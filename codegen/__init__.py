"""
Go → Python model codegen for tailscale-cli.

Parses Go struct/const definitions from the upstream tailscale/tailscale repo
and generates deterministic Python dataclass modules pinned to a specific
commit or tag.

Usage:
    python -m codegen            # regenerate all configured sources
    python -m codegen --check    # exit non-zero if generated files are stale
"""
