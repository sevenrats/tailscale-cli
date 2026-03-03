"""
Lightweight Go source parser.

Extracts struct definitions, const groups (iota enums), and type aliases
from a single Go source file.  Handles the subset of syntax that appears
in tailscale's ipnstate.go and similar model-definition files.

This is *not* a complete Go parser—it deliberately ignores functions,
imports, and interface declarations.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from .ir import (
    GoConstGroup,
    GoConstValue,
    GoField,
    GoFile,
    GoStruct,
    GoType,
    GoTypeAlias,
    GoTypeKind,
)

# ---------------------------------------------------------------------------
# Regex building blocks
# ---------------------------------------------------------------------------

_IDENT = r"[A-Za-z_]\w*"
_QUALIFIED = rf"(?:{_IDENT}\.)?{_IDENT}"  # pkg.Type or Type
_WS = r"[ \t]*"

# Matches `json:"name,omitempty"`, also handles `-` (skip)
_JSON_TAG_RE = re.compile(r'json:"([^"]*)"')

# ---------------------------------------------------------------------------
# Type expression parser (recursive-descent, from a string)
# ---------------------------------------------------------------------------


def _parse_type(s: str) -> Tuple[GoType, str]:
    """Parse a Go type expression from the front of *s* and return (GoType, rest)."""
    s = s.lstrip()

    # interface{}
    if s.startswith("interface{}"):
        return GoType(kind=GoTypeKind.INTERFACE), s[len("interface{}") :]

    # any (Go 1.18+)
    m = re.match(r"any\b", s)
    if m:
        return GoType(kind=GoTypeKind.INTERFACE), s[m.end() :]

    # Pointer: *T
    if s.startswith("*"):
        inner, rest = _parse_type(s[1:])
        return GoType(kind=GoTypeKind.POINTER, elem=inner), rest

    # Slice: []T
    if s.startswith("[]"):
        inner, rest = _parse_type(s[2:])
        return GoType(kind=GoTypeKind.SLICE, elem=inner), rest

    # Array: [N]T
    m = re.match(r"\[(\d+)\]", s)
    if m:
        length = int(m.group(1))
        inner, rest = _parse_type(s[m.end() :])
        return GoType(kind=GoTypeKind.ARRAY, elem=inner, array_len=length), rest

    # Map: map[K]V
    if s.startswith("map["):
        s = s[4:]  # skip "map["
        key_type, s = _parse_type(s)
        s = s.lstrip()
        if s.startswith("]"):
            s = s[1:]
        val_type, rest = _parse_type(s)
        return GoType(kind=GoTypeKind.MAP, key=key_type, value=val_type), rest

    # Named type: pkg.Type or Type
    m = re.match(rf"({_QUALIFIED})", s)
    if m:
        return GoType(kind=GoTypeKind.IDENT, name=m.group(1)), s[m.end() :]

    # Fallback
    return GoType(kind=GoTypeKind.IDENT, name="UNKNOWN"), s


def parse_type_expr(s: str) -> GoType:
    """Convenience: parse a complete Go type expression."""
    t, _ = _parse_type(s.strip())
    return t


# ---------------------------------------------------------------------------
# Struct body parser
# ---------------------------------------------------------------------------


def _parse_json_tag(tag_str: str) -> Tuple[str, bool]:
    """Return (json_name, omitempty) from a struct tag string."""
    m = _JSON_TAG_RE.search(tag_str)
    if not m:
        return "", False
    parts = m.group(1).split(",")
    name = parts[0]
    omit = "omitempty" in parts[1:]
    return name, omit


def _parse_struct_body(body: str) -> List[GoField]:
    """Parse fields from the text between outer { … } of a struct."""
    fields: List[GoField] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//") or line == "{" or line == "}":
            continue

        # Capture inline comment
        comment = ""
        cm = re.search(r"//\s*(.*)", line)
        if cm:
            comment = cm.group(1).strip()
            line = line[: cm.start()].rstrip()

        # Remove struct tags (backtick-delimited)
        tag = ""
        tm = re.search(r"`([^`]+)`", line)
        if tm:
            tag = tm.group(1)
            line = line[: tm.start()].rstrip()

        if not line.strip():
            continue

        # Now line should be:  FieldName  TypeExpr
        parts = line.split(None, 1)
        if len(parts) < 2:
            # Embedded (anonymous) field — skip for now
            continue

        field_name = parts[0]
        if not field_name[0].isupper():
            # unexported — skip
            continue

        type_expr = parts[1].strip()
        go_type = parse_type_expr(type_expr)

        json_name, omit = _parse_json_tag(tag)

        fields.append(
            GoField(
                name=field_name,
                go_type=go_type,
                json_name=json_name,
                json_omitempty=omit,
                comment=comment,
            )
        )

    return fields


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------

# Match:  type FooBar struct {
_STRUCT_HEAD_RE = re.compile(rf"^type\s+({_IDENT})\s+struct\s*\{{", re.MULTILINE)

# Match:  type FooBar underlying
_TYPE_ALIAS_RE = re.compile(rf"^type\s+({_IDENT})\s+({_QUALIFIED})\s*$", re.MULTILINE)

# Match the opening of a const block:  const (
_CONST_BLOCK_RE = re.compile(r"^const\s*\(", re.MULTILINE)


def _find_matching_brace(src: str, open_pos: int) -> int:
    """Return the index of the closing '}' that matches the '{' at open_pos."""
    depth = 0
    i = open_pos
    while i < len(src):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(src)


def _find_matching_paren(src: str, open_pos: int) -> int:
    """Return the index of the closing ')' that matches the '(' at open_pos."""
    depth = 0
    i = open_pos
    while i < len(src):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(src)


def _collect_preceding_comment(src: str, pos: int) -> str:
    """Gather consecutive // comment lines immediately above *pos*."""
    lines = src[:pos].rstrip().rsplit("\n", 10)
    comments: list[str] = []
    for raw in reversed(lines):
        stripped = raw.strip()
        if stripped.startswith("//"):
            comments.append(stripped.lstrip("/").strip())
        elif stripped == "":
            continue
        else:
            break
    comments.reverse()
    return "\n".join(comments)


def _parse_const_block(body: str) -> List[GoConstGroup]:
    """
    Parse a const ( … ) block.

    Handles iota-style int enums and string-constant enums.
    Returns one GoConstGroup per distinct type found.
    """
    groups: dict[str, GoConstGroup] = {}
    current_type = ""
    current_base = "int"
    iota_val = 0

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line == "(" or line == ")":
            continue

        # Capture comment
        comment = ""
        cm = re.search(r"//\s*(.*)", line)
        if cm:
            comment = cm.group(1).strip()
            line = line[: cm.start()].rstrip()

        if not line:
            continue

        # Pattern: Name Type = iota  OR  Name Type = "value"  OR  Name (continuing iota)
        # Full declaration:  Name Type = Value
        m = re.match(rf"({_IDENT})\s+({_QUALIFIED})\s*=\s*(.*)", line)
        if m:
            name, typ, val_str = m.group(1), m.group(2), m.group(3).strip()
            if typ != current_type:
                current_type = typ
                iota_val = 0
                # Determine base type
                if "iota" in val_str:
                    current_base = "int"
                elif val_str.startswith('"'):
                    current_base = "string"
                else:
                    current_base = "int"

            if current_type not in groups:
                groups[current_type] = GoConstGroup(
                    type_name=current_type.rsplit(".", 1)[-1],
                    base_type=current_base,
                )

            if current_base == "string":
                # Extract the string literal
                sm = re.match(r'"([^"]*)"', val_str)
                value = sm.group(1) if sm else val_str
            else:
                value = iota_val

            groups[current_type].values.append(
                GoConstValue(name=name, value=value, comment=comment)
            )
            iota_val += 1
            continue

        # Continuation line (name only, inherits type and increments iota)
        m = re.match(rf"({_IDENT})\s*$", line)
        if m and current_type:
            name = m.group(1)
            if current_type not in groups:
                groups[current_type] = GoConstGroup(
                    type_name=current_type.rsplit(".", 1)[-1],
                    base_type=current_base,
                )
            groups[current_type].values.append(
                GoConstValue(name=name, value=iota_val, comment=comment)
            )
            iota_val += 1
            continue

        # Explicit value continuation:  Name = "value"  (no type, reuses current)
        m = re.match(rf'({_IDENT})\s*=\s*"([^"]*)"', line)
        if m and current_type:
            name, val = m.group(1), m.group(2)
            if current_type not in groups:
                groups[current_type] = GoConstGroup(
                    type_name=current_type.rsplit(".", 1)[-1],
                    base_type=current_base,
                )
            groups[current_type].values.append(
                GoConstValue(name=name, value=val, comment=comment)
            )
            continue

    return list(groups.values())


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def parse_go_file(src: str) -> GoFile:
    """Parse a Go source file and return its IR."""
    result = GoFile()

    # Package
    m = re.search(r"^package\s+(\w+)", src, re.MULTILINE)
    if m:
        result.package = m.group(1)

    # --- Structs ---
    for m in _STRUCT_HEAD_RE.finditer(src):
        name = m.group(1)
        open_brace = m.end() - 1
        close_brace = _find_matching_brace(src, open_brace)
        body = src[open_brace + 1 : close_brace]
        comment = _collect_preceding_comment(src, m.start())
        result.structs.append(
            GoStruct(name=name, fields=_parse_struct_body(body), comment=comment)
        )

    # --- Const blocks ---
    for m in _CONST_BLOCK_RE.finditer(src):
        open_paren = m.end() - 1
        close_paren = _find_matching_paren(src, open_paren)
        body = src[open_paren + 1 : close_paren]
        result.const_groups.extend(_parse_const_block(body))

    # --- Type aliases ---
    # Collect all struct names so we don't re-emit them as aliases
    struct_names = {s.name for s in result.structs}
    for m in _TYPE_ALIAS_RE.finditer(src):
        name = m.group(1)
        if name in struct_names:
            continue
        underlying_str = m.group(2)
        comment = _collect_preceding_comment(src, m.start())
        result.type_aliases.append(
            GoTypeAlias(
                name=name,
                underlying=parse_type_expr(underlying_str),
                comment=comment,
            )
        )

    return result
