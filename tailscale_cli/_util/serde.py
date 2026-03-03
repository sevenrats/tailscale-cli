from __future__ import annotations

import json
from dataclasses import fields
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

T = TypeVar("T", bound="SerdeMixin")


def _dt_from_any(v: Any) -> Any:
    if v is None or isinstance(v, datetime):
        return v
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(v, tz=timezone.utc)
        except Exception:
            return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except Exception:
            return v
    return v


def _dt_to_str(dt: datetime) -> str:
    # Keep timezone info if present. If naive, assume UTC for stability.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin is None:
        return False
    if origin is Union:
        args = get_args(tp)
        return any(a is type(None) for a in args)
    return False


def _unwrap_optional(tp: Any) -> Any:
    if not _is_optional(tp):
        return tp
    args = get_args(tp)
    non_none = [a for a in args if a is not type(None)]
    return non_none[0] if non_none else Any


@lru_cache(maxsize=None)
def _field_specs(cls: Type[Any]) -> Tuple[Tuple[str, Any], ...]:
    """
    Cached field (name, type) pairs for a dataclass.
    """
    return tuple((f.name, f.type) for f in fields(cls))


def _coerce_value(tp: Any, v: Any) -> Any:
    """
    Coerce v into tp (best-effort), handling:
      - Optional
      - datetime
      - Enum
      - dataclasses with from_dict
      - List[T]
      - Dict[K,V] (coerce values)
    """
    if v is None:
        return None

    tp = _unwrap_optional(tp)
    origin = get_origin(tp)
    args = get_args(tp)

    # datetime
    if tp is datetime:
        return _dt_from_any(v)

    # Enums
    if isinstance(tp, type) and issubclass(tp, Enum):
        try:
            return tp(v)
        except Exception:
            return v

    # Nested dataclass-like
    if isinstance(tp, type) and hasattr(tp, "from_dict") and isinstance(v, dict):
        return tp.from_dict(v)

    # List[T]
    if origin in (list, List):
        elem_t = args[0] if args else Any
        if not isinstance(v, list):
            return v
        return [_coerce_value(elem_t, x) for x in v]

    # Dict[K,V]
    if origin in (dict, Dict, Mapping):
        if not isinstance(v, dict):
            return v
        if len(args) == 2:
            _, val_t = args
            return {k: _coerce_value(val_t, vv) for k, vv in v.items()}
        return v

    return v


def _encode_value(v: Any) -> Any:
    """
    Encode python objects into JSON-safe primitives.
    """
    if v is None:
        return None
    if isinstance(v, datetime):
        return _dt_to_str(v)
    if isinstance(v, Enum):
        return v.value
    if hasattr(v, "to_dict") and callable(v.to_dict):
        return v.to_dict()
    if isinstance(v, list):
        return [_encode_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _encode_value(val) for k, val in v.items()}
    return v


class SerdeMixin:
    """
    Fast serde for dataclasses:
      - from_dict / to_dict
      - from_json / to_json

    Subclasses may define a ``__json_map__`` class variable — a
    ``Dict[str, str]`` mapping JSON key names to Python field names.
    This lets generated models handle CamelCase ↔ snake_case automatically.
    """

    # Override in subclasses to remap JSON keys → Python field names.
    # Example:  __json_map__: ClassVar[Dict[str, str]] = {"HostName": "host_name"}
    __json_map__: Dict[str, str] = {}

    @classmethod
    @lru_cache(maxsize=None)
    def _reverse_json_map(cls) -> Dict[str, str]:
        """Python field name → JSON key name (inverse of __json_map__)."""
        return {v: k for k, v in cls.__json_map__.items()}

    @classmethod
    def from_dict(cls: Type[T], d: Dict[str, Any]) -> T:
        if d is None:
            return cls()
        d = dict(d)  # shallow copy

        # Remap JSON keys → Python field names if __json_map__ is defined
        jmap = getattr(cls, "__json_map__", {})
        if jmap:
            for json_key, py_name in jmap.items():
                if json_key in d and py_name not in d:
                    d[py_name] = d.pop(json_key)

        kwargs: Dict[str, Any] = {}
        for name, tp in _field_specs(cls):
            if name in d:
                kwargs[name] = _coerce_value(tp, d[name])
        return cls(**kwargs)

    def to_dict(self, *, omit_none: bool = True) -> Dict[str, Any]:
        rev = self._reverse_json_map()
        out: Dict[str, Any] = {}
        for name, _tp in _field_specs(type(self)):
            v = getattr(self, name, None)
            if omit_none and v is None:
                continue
            # Use the original JSON key name if mapped
            key = rev.get(name, name)
            out[key] = _encode_value(v)
        return out

    @classmethod
    def loads(cls: Type[T], s: str) -> T:
        return cls.from_dict(json.loads(s))

    def dumps(self, *, omit_none: bool = True, **json_kwargs: Any) -> str:
        # json_kwargs: separators=(',', ':'), ensure_ascii=False, etc.
        return json.dumps(self.to_dict(omit_none=omit_none), **json_kwargs)
