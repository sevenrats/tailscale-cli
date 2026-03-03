#!/usr/bin/env python3
"""
Offline unit test for the Go parser + generator.
Uses a snippet of Go source rather than fetching from GitHub.

Run:  python3 codegen/_test_offline.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen.go_parser import parse_go_file, parse_type_expr
from codegen.generator import generate_module
from codegen.ir import GoTypeKind


# ---- Test type expression parser ----
def test_type_parser():
    cases = [
        ("string", GoTypeKind.IDENT, "string"),
        ("*string", GoTypeKind.POINTER, None),
        ("[]string", GoTypeKind.SLICE, None),
        ("[32]byte", GoTypeKind.ARRAY, None),
        ("map[string]int", GoTypeKind.MAP, None),
        ("key.NodePublic", GoTypeKind.IDENT, "key.NodePublic"),
        ("interface{}", GoTypeKind.INTERFACE, ""),
    ]
    for expr, expected_kind, expected_name in cases:
        t = parse_type_expr(expr)
        assert t.kind == expected_kind, (
            f"{expr}: got {t.kind}, expected {expected_kind}"
        )
        if expected_name is not None:
            assert t.name == expected_name, (
                f"{expr}: got name={t.name!r}, expected {expected_name!r}"
            )
    print("  type parser: OK")


# ---- Test Go file parser ----
GO_SNIPPET = """
package ipnstate

import "time"

type TaildropTargetStatus int

const (
    TaildropTargetUnknown          TaildropTargetStatus = iota
    TaildropTargetAvailable
    TaildropTargetNoNetmapAvailable
)

type SelfUpdateStatus string

const (
    UpdateFinished   SelfUpdateStatus = "UpdateFinished"
    UpdateInProgress SelfUpdateStatus = "UpdateInProgress"
    UpdateFailed     SelfUpdateStatus = "UpdateFailed"
)

// PeerStatus describes a peer node.
type PeerStatus struct {
    ID        tailcfg.StableNodeID `json:"ID"`
    PublicKey key.NodePublic       `json:"PublicKey"`
    HostName  string               `json:"HostName"`

    DNSName     string `json:"DNSName"`
    OS          string `json:"OS,omitempty"`
    Online      bool   `json:"Online,omitempty"`
    ExitNode    bool   `json:"ExitNode"`

    TailscaleIPs []netip.Addr   `json:"TailscaleIPs"`
    AllowedIPs   *[]netip.Prefix `json:"AllowedIPs,omitempty"`

    RxBytes    int64      `json:"RxBytes"`
    LastSeen   *time.Time `json:"LastSeen,omitempty"`
    KeyExpiry  *time.Time `json:"KeyExpiry,omitempty"`

    Expired bool `json:"Expired"`
    Location *tailcfg.Location `json:"Location,omitempty"`
}

// Status represents the overall status of the Tailscale daemon.
type Status struct {
    Version      string         `json:"Version"`
    TUN          bool           `json:"TUN"`
    BackendState string         `json:"BackendState"`
    Self         *PeerStatus    `json:"Self"`
    Peer         map[key.NodePublic]*PeerStatus `json:"Peer"`
    Health       []string       `json:"Health,omitempty"`
}

type PingResult struct {
    IP       string  `json:"IP"`
    NodeIP   string  `json:"NodeIP"`
    Err      string  `json:"Err,omitempty"`
    LatencySeconds float64 `json:"LatencySeconds"`
}
"""


def test_go_parser():
    ir = parse_go_file(GO_SNIPPET)
    assert ir.package == "ipnstate", f"package: {ir.package}"

    # Structs
    struct_names = [s.name for s in ir.structs]
    assert "PeerStatus" in struct_names, f"structs: {struct_names}"
    assert "Status" in struct_names
    assert "PingResult" in struct_names
    assert len(ir.structs) == 3, f"expected 3 structs, got {len(ir.structs)}"

    # Check PeerStatus fields
    ps = [s for s in ir.structs if s.name == "PeerStatus"][0]
    field_names = [f.name for f in ps.fields]
    assert "ID" in field_names
    assert "PublicKey" in field_names
    assert "TailscaleIPs" in field_names
    assert "LastSeen" in field_names

    # Check JSON tags
    id_field = [f for f in ps.fields if f.name == "ID"][0]
    assert id_field.json_name == "ID"
    os_field = [f for f in ps.fields if f.name == "OS"][0]
    assert os_field.json_omitempty

    # Const groups
    assert len(ir.const_groups) == 2, (
        f"expected 2 const groups, got {len(ir.const_groups)}"
    )
    tdts = [c for c in ir.const_groups if c.type_name == "TaildropTargetStatus"][0]
    assert tdts.base_type == "int"
    assert len(tdts.values) == 3

    sus = [c for c in ir.const_groups if c.type_name == "SelfUpdateStatus"][0]
    assert sus.base_type == "string"
    assert sus.values[0].value == "UpdateFinished"

    # Type aliases
    alias_names = [a.name for a in ir.type_aliases]
    assert "TaildropTargetStatus" in alias_names
    assert "SelfUpdateStatus" in alias_names

    print("  Go parser: OK")


# ---- Test Python generator ----
def test_generator():
    ir = parse_go_file(GO_SNIPPET)
    code = generate_module(ir, upstream_url="test://url", upstream_commit="abc123")

    # Verify it's valid Python
    compile(code, "<generated>", "exec")

    # Check key elements are present
    assert "class PeerStatus(SerdeMixin):" in code
    assert "class Status(SerdeMixin):" in code
    assert "class TaildropTargetStatus(IntEnum):" in code
    assert "class SelfUpdateStatus(str, Enum):" in code
    assert "__json_map__" in code
    assert "DO NOT EDIT" in code
    assert "abc123" in code

    print("  Generator: OK")
    return code


# ---- Run all ----
if __name__ == "__main__":
    print("Running codegen tests...")
    test_type_parser()
    test_go_parser()
    code = test_generator()
    print("\nAll tests passed!\n")
    print("=== Generated code (first 3000 chars) ===")
    print(code[:3000])
