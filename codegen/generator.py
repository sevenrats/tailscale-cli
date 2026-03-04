"""
Python code generator.

Consumes the Go IR and produces a self-contained Python module containing
dataclass definitions, enums, and NewType aliases — all wired to SerdeMixin.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

from .ir import (
    GoField,
    GoFile,
    GoType,
    GoTypeKind,
)
from .type_map import (
    DATETIME_TYPES,
    OPAQUE_DICTS,
    OPAQUE_NEWTYPES,
    PRIMITIVE_MAP,
    go_name_to_snake,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _py_type_for(
    gt: GoType, local_structs: Set[str], local_enums: Set[str], local_aliases: Set[str]
) -> str:
    """Resolve a GoType to a Python type annotation string."""

    if gt.kind == GoTypeKind.INTERFACE:
        return "Any"

    if gt.kind == GoTypeKind.POINTER:
        inner = _py_type_for(gt.elem, local_structs, local_enums, local_aliases)  # type: ignore[arg-type]
        return f"Optional[{inner}]"

    if gt.kind == GoTypeKind.SLICE:
        inner = _py_type_for(gt.elem, local_structs, local_enums, local_aliases)  # type: ignore[arg-type]
        return f"List[{inner}]"

    if gt.kind == GoTypeKind.ARRAY:
        inner = _py_type_for(gt.elem, local_structs, local_enums, local_aliases)  # type: ignore[arg-type]
        # Model fixed-size byte arrays as `bytes`
        if gt.elem and gt.elem.name == "byte":
            return "Optional[bytes]"
        return f"List[{inner}]"

    if gt.kind == GoTypeKind.MAP:
        k = _py_type_for(gt.key, local_structs, local_enums, local_aliases)  # type: ignore[arg-type]
        v = _py_type_for(gt.value, local_structs, local_enums, local_aliases)  # type: ignore[arg-type]
        return f"Dict[{k}, {v}]"

    # IDENT
    name = gt.name

    # Primitives
    if name in PRIMITIVE_MAP:
        return PRIMITIVE_MAP[name]

    # datetime
    if name in DATETIME_TYPES:
        return "datetime"

    # Opaque NewType
    if name in OPAQUE_NEWTYPES:
        short = name.rsplit(".", 1)[-1]
        return short

    # Opaque dict
    if name in OPAQUE_DICTS:
        return "Dict[str, Any]"

    # Local struct/enum/alias (strip package qualifier if present)
    short = name.rsplit(".", 1)[-1]
    if short in local_structs or short in local_enums or short in local_aliases:
        return short

    # Unknown external type → Dict[str, Any] with a comment
    return "Dict[str, Any]"


def _py_default(py_type: str, field: GoField) -> str:
    """Return the default-value expression for a field."""
    if py_type.startswith("Optional["):
        return "None"
    if py_type.startswith("List["):
        return "field(default_factory=list)"
    if py_type.startswith("Dict["):
        return "field(default_factory=dict)"
    if py_type == "str":
        return '""'
    if py_type == "int":
        return "0"
    if py_type == "float":
        return "0.0"
    if py_type == "bool":
        return "False"
    if py_type == "bytes":
        return 'b""'
    if py_type == "datetime":
        return "None"  # will be Optional in practice (Go zero-value is meaningless)
    if py_type == "Any":
        return "None"

    # NewType — use its constructor with a zero-value
    # Check if it's one of our opaque newtypes
    for go_name, base in OPAQUE_NEWTYPES.items():
        short = go_name.rsplit(".", 1)[-1]
        if short == py_type:
            if base == "str":
                return f'{py_type}("")'
            elif base == "int":
                return f"{py_type}(0)"
            return "None"

    # Enum type — default to first variant? No, use 0
    return "None"


def _field_line(
    py_name: str, py_type: str, default: str, json_name: str, comment: str
) -> str:
    """Generate a single field line, including metadata for JSON name mapping."""
    parts = [f"    {py_name}: {py_type} = {default}"]
    inline_comments = []
    if json_name and json_name != py_name:
        inline_comments.append(f'json="{json_name}"')
    if comment:
        inline_comments.append(comment)
    if inline_comments:
        parts.append(f"  # {'; '.join(inline_comments)}")
    return "".join(parts)


# ---------------------------------------------------------------------------
# JSON name-mapping generation
# ---------------------------------------------------------------------------


def _build_json_map(fields: List[Tuple[str, str]]) -> Dict[str, str]:
    """Return {json_key: python_name} for fields where they differ."""
    return {jn: pn for pn, jn in fields if jn and jn != pn}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_module(
    go_file: GoFile,
    *,
    upstream_url: str = "",
    upstream_commit: str = "",
    serde_import: str = "tailscale_cli._util.serde",
) -> str:
    """Generate a complete Python module from a parsed Go file."""

    lines: List[str] = []

    # --- Header ---
    lines.append('"""')
    lines.append("Auto-generated from upstream Go source — DO NOT EDIT.")
    lines.append("")
    if upstream_url:
        lines.append(f"Source : {upstream_url}")
    if upstream_commit:
        lines.append(f"Commit : {upstream_commit}")
    lines.append(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from dataclasses import dataclass, field")
    lines.append("from datetime import datetime")
    lines.append("from enum import Enum, IntEnum")
    lines.append("from typing import Any, ClassVar, Dict, List, NewType, Optional")
    lines.append("")
    lines.append(f"from {serde_import} import SerdeMixin")
    lines.append("")

    # Collect names for forward-reference resolution
    local_structs: Set[str] = {s.name for s in go_file.structs}
    local_enums: Set[str] = {cg.type_name for cg in go_file.const_groups}
    local_aliases: Set[str] = {a.name for a in go_file.type_aliases}

    # --- NewType declarations for opaque external types actually used ---
    used_newtypes: Set[str] = set()
    _collect_used_newtypes(go_file, used_newtypes)

    if used_newtypes:
        lines.append("# --- External / opaque Go types ---")
        lines.append("")
        for go_name in sorted(used_newtypes):
            short = go_name.rsplit(".", 1)[-1]
            base = OPAQUE_NEWTYPES[go_name]
            lines.append(f'{short} = NewType("{short}", {base})  # {go_name}')
        lines.append("")
        lines.append("")

    # --- Enums ---
    for cg in go_file.const_groups:
        if cg.comment:
            for cl in cg.comment.splitlines():
                lines.append(f"# {cl}")
        base_cls = "IntEnum" if cg.base_type == "int" else "str, Enum"
        lines.append(f"class {cg.type_name}({base_cls}):")
        for cv in cg.values:
            val_repr = repr(cv.value)
            cmt = f"  # {cv.comment}" if cv.comment else ""
            member_name = _enum_member_name(cv.name, cg.type_name)
            lines.append(f"    {member_name} = {val_repr}{cmt}")
        lines.append("")
        lines.append("")

    # --- Structs (as dataclasses) ---
    for struct in go_file.structs:
        if struct.comment:
            for cl in struct.comment.splitlines():
                lines.append(f"# {cl}")
        lines.append("@dataclass")
        lines.append(f"class {struct.name}(SerdeMixin):")

        # Build JSON↔Python mapping
        json_pairs: List[Tuple[str, str]] = []  # (py_name, json_name)

        if not struct.fields:
            lines.append("    pass")
        else:
            for f in struct.fields:
                # Skip fields tagged json:"-"
                if f.json_name == "-":
                    continue

                py_name = go_name_to_snake(f.name)
                # Avoid collision with Python builtins
                if py_name in ("self", "type", "class"):
                    py_name = f"_{py_name}"

                py_type = _py_type_for(
                    f.go_type, local_structs, local_enums, local_aliases
                )

                # Pointer fields → Optional
                if f.go_type.kind == GoTypeKind.POINTER:
                    pass  # already Optional from _py_type_for
                elif f.json_omitempty and not py_type.startswith("Optional["):
                    # omitempty with a non-pointer type that could still be None in practice
                    pass

                default = _py_default(py_type, f)

                # JSON name (from tag, or Go field name if no tag)
                json_name = f.json_name if f.json_name else f.name
                json_pairs.append((py_name, json_name))

                lines.append(
                    _field_line(py_name, py_type, default, json_name, f.comment)
                )

        # Add __json_map__ class-var for SerdeMixin to use
        jmap = _build_json_map(json_pairs)
        if jmap:
            lines.append("")
            lines.append("    # JSON key name → Python field name")
            lines.append("    __json_map__: ClassVar[Dict[str, str]] = {")
            for jk, pk in sorted(jmap.items()):
                lines.append(f'        "{jk}": "{pk}",')
            lines.append("    }")

        lines.append("")
        lines.append("")

    # --- Type aliases ---
    # Skip aliases already emitted as opaque NewTypes or enum classes.
    _emitted_newtypes = {go_name.rsplit(".", 1)[-1] for go_name in used_newtypes}
    for alias in go_file.type_aliases:
        short = alias.name
        if short in _emitted_newtypes:
            continue
        if short in local_enums:
            continue  # already emitted as an IntEnum/Enum class
        py_underlying = _py_type_for(
            alias.underlying, local_structs, local_enums, local_aliases
        )
        if alias.comment:
            for cl in alias.comment.splitlines():
                lines.append(f"# {cl}")
        # If the underlying type is a primitive, use NewType for type-safety
        if py_underlying in ("str", "int", "float", "bool"):
            lines.append(f'{short} = NewType("{short}", {py_underlying})')
        else:
            lines.append(f"{short} = {py_underlying}")
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _collect_used_newtypes(go_file: GoFile, out: Set[str]) -> None:
    """Walk all types in the file and collect referenced opaque NewTypes."""

    def _walk(gt: GoType) -> None:
        if gt.kind == GoTypeKind.IDENT and gt.name in OPAQUE_NEWTYPES:
            out.add(gt.name)
        for child in (gt.elem, gt.key, gt.value):
            if child is not None:
                _walk(child)

    for s in go_file.structs:
        for f in s.fields:
            _walk(f.go_type)
    for a in go_file.type_aliases:
        _walk(a.underlying)


def _enum_member_name(const_name: str, type_name: str) -> str:
    """
    Derive a clean UPPER_SNAKE enum member name.

    Go enums conventionally prefix the type name, e.g.
    ``TaildropTargetStatusUnknown`` → ``UNKNOWN``.
    """
    name = const_name
    # Strip the type-name prefix (case-insensitive start)
    if name.lower().startswith(type_name.lower()):
        name = name[len(type_name) :]
    # Convert to UPPER_SNAKE
    name = go_name_to_snake(name).upper().lstrip("_")
    if not name:
        name = const_name.upper()
    return name
