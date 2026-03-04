"""
Go → Python type mapping rules.

Centralises all decisions about how Go types translate to Python types.
The generator imports this and delegates all type-resolution here.
"""

from __future__ import annotations

from typing import Dict, Set

# ---------------------------------------------------------------------------
# Primitive Go → Python mappings
# ---------------------------------------------------------------------------

PRIMITIVE_MAP: Dict[str, str] = {
    "string": "str",
    "bool": "bool",
    "int": "int",
    "int8": "int",
    "int16": "int",
    "int32": "int",
    "int64": "int",
    "uint": "int",
    "uint8": "int",
    "uint16": "int",
    "uint32": "int",
    "uint64": "int",
    "float32": "float",
    "float64": "float",
    "byte": "int",
    "rune": "int",
}

# Go types that become ``datetime`` in Python.
DATETIME_TYPES: Set[str] = {
    "time.Time",
}

# External / opaque Go types that we model as ``NewType("X", str|int)``
# rather than generating a full dataclass.  Maps  qualified Go name → Python
# base type.  This list is intentionally explicit so that adding a new opaque
# type requires a conscious decision.
OPAQUE_NEWTYPES: Dict[str, str] = {
    # key.*
    "key.NodePublic": "str",
    "key.NLPublic": "str",
    "key.DiscoPublic": "str",
    "key.MachinePublic": "str",
    # tailcfg.*
    "tailcfg.NodeCapability": "str",
    "tailcfg.UserID": "int",
    "tailcfg.NodeID": "int",
    "tailcfg.StableNodeID": "str",
    "tailcfg.CapabilityVersion": "int",
    # tka.*
    "tka.NodeKeySignature": "str",
    # netip.*
    "netip.Addr": "str",
    "netip.Prefix": "str",
    "netip.AddrPort": "str",
    # ipn.* — unqualified same-package types referenced across files
    "StateKey": "str",
    "WindowsUserID": "str",
    "ProfileID": "str",
    "ExitNodeExpression": "str",
    # persist.*
    "persist.PersistView": "str",
}

# External Go types that we keep as opaque ``Dict[str, Any]`` because they are
# large / polymorphic and we don't want to fully model them yet.
OPAQUE_DICTS: Set[str] = {
    "tailcfg.UserProfile",
    "tailcfg.ClientVersion",
    "tailcfg.Location",
    "tailcfg.Hostinfo",
    "tailcfg.NetInfo",
    "tailcfg.DERPRegion",
    "views.Slice",
    # persist / control types
    "persist.Persist",
    "persist.PersistView",
    "controlclient.NetmapUpdater",
    "wgcfg.Config",
    "filter.Match",
    "router.Config",
    "dns.OSConfig",
    "dns.Config",
    "tailcfg.Debug",
    "url.URL",
    # ipn cross-file struct refs (not yet codegen'd together)
    "ServeConfig",
    "ConfigVAlpha",
}

# ---------------------------------------------------------------------------
# Ref → Python package name
# ---------------------------------------------------------------------------


def ref_to_package_name(ref: str) -> str:
    """Convert an upstream Git ref to a valid Python package directory name.

    Examples:
        v1.82.0      → v1_82_0
        v1.84.0-rc1  → v1_84_0_rc1
        main         → main
        abc123…      → abc123… (first 12 hex chars)
    """
    import re

    name = ref.strip()
    # If it looks like a full SHA, truncate to 12 chars
    if re.fullmatch(r"[0-9a-f]{40}", name):
        name = name[:12]
    # Replace any character that isn't alphanumeric or underscore
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    # Must not start with a digit (prefix with 'v' if needed)
    if name and name[0].isdigit():
        name = "v" + name
    return name.lower()


# ---------------------------------------------------------------------------
# Name helpers
# ---------------------------------------------------------------------------


def go_name_to_snake(name: str) -> str:
    """Convert GoCamelCase to python_snake_case.

    Handles common acronyms (IP, DNS, ID, URL, SSH, TLS, API, OS, …).
    """
    import re

    # Insert underscore between: UPPER run followed by Upper+lower
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    # Insert underscore between: lower/digit followed by Upper
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def json_key_to_snake(key: str) -> str:
    """Convert a JSON key (usually PascalCase) to snake_case."""
    return go_name_to_snake(key)
