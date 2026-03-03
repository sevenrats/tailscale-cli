#!/usr/bin/env python3
"""Quick smoke test for the codegen pipeline."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen.go_parser import parse_go_file
from codegen.fetch import fetch_go_source
from codegen.generator import generate_module

src = fetch_go_source("tailscale/tailscale", "v1.82.0", "ipn/ipnstate/ipnstate.go")
ir = parse_go_file(src)
code = generate_module(ir, upstream_url="test", upstream_commit="v1.82.0")
# Write to a temp file so we can read it
out = "/tmp/codegen_test_output.py"
with open(out, "w") as f:
    f.write(code)
print(f"Generated {len(code)} bytes -> {out}")
print(f"Structs: {[s.name for s in ir.structs]}")
print(f"Enums: {[c.type_name for c in ir.const_groups]}")
# Check syntax validity
compile(code, out, "exec")
print("Syntax check: OK")
