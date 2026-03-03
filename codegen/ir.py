"""
Intermediate representation for parsed Go types.

Everything the Go parser emits is one of these dataclasses;
the Python generator consumes them to produce .py files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional


# ---------------------------------------------------------------------------
# Go type IR
# ---------------------------------------------------------------------------


class GoTypeKind(Enum):
    IDENT = auto()  # simple named type: "string", "bool", "MyStruct"
    POINTER = auto()  # *T
    SLICE = auto()  # []T
    ARRAY = auto()  # [N]T
    MAP = auto()  # map[K]V
    INTERFACE = auto()  # interface{}


@dataclass
class GoType:
    kind: GoTypeKind
    name: str = ""  # for IDENT: the type name
    elem: Optional["GoType"] = None  # for POINTER / SLICE / ARRAY
    key: Optional["GoType"] = None  # for MAP
    value: Optional["GoType"] = None  # for MAP
    array_len: int = 0  # for ARRAY


# ---------------------------------------------------------------------------
# Struct field
# ---------------------------------------------------------------------------


@dataclass
class GoField:
    name: str
    go_type: GoType
    json_name: str = ""  # from `json:"…"` tag, empty → use name
    json_omitempty: bool = False
    comment: str = ""


# ---------------------------------------------------------------------------
# Struct
# ---------------------------------------------------------------------------


@dataclass
class GoStruct:
    name: str
    fields: List[GoField] = field(default_factory=list)
    comment: str = ""


# ---------------------------------------------------------------------------
# Const block → becomes an enum
# ---------------------------------------------------------------------------


@dataclass
class GoConstValue:
    name: str
    value: Any = None  # int for iota, str for string consts
    comment: str = ""


@dataclass
class GoConstGroup:
    """A group of constants that share a type (e.g. iota enums)."""

    type_name: str
    base_type: str  # "int" or "string"
    values: List[GoConstValue] = field(default_factory=list)
    comment: str = ""


# ---------------------------------------------------------------------------
# Type alias / named type  (e.g. `type StableNodeID string`)
# ---------------------------------------------------------------------------


@dataclass
class GoTypeAlias:
    name: str
    underlying: GoType
    comment: str = ""


# ---------------------------------------------------------------------------
# Entire parsed file
# ---------------------------------------------------------------------------


@dataclass
class GoFile:
    package: str = ""
    structs: List[GoStruct] = field(default_factory=list)
    const_groups: List[GoConstGroup] = field(default_factory=list)
    type_aliases: List[GoTypeAlias] = field(default_factory=list)
