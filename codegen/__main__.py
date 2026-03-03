"""
CLI entry point for model codegen.

Usage:
    python -m codegen                  # regenerate all models
    python -m codegen --check          # fail if models are stale (for CI)
    python -m codegen --diff           # show what would change
    python -m codegen --pin <ref>      # update the pinned upstream ref & regenerate
    python -m codegen --dry-run        # print generated code to stdout
    python -m codegen --sync-tags      # generate all missing upstream release tags
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Any, Dict, List

from .fetch import fetch_go_source, fetch_release_tags, resolve_commit_sha
from .go_parser import parse_go_file
from .generator import generate_module
from .type_map import ref_to_package_name

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "codegen.toml"


def _load_config(path: Path | None = None) -> Dict[str, Any]:
    p = path or CONFIG_PATH
    text = p.read_text()
    if tomllib is not None:
        return tomllib.loads(text)
    raise SystemExit(
        "tomllib not available (Python <3.11). Install `tomli`:\n  pip install tomli"
    )


# ---------------------------------------------------------------------------
# Path derivation
# ---------------------------------------------------------------------------


def _version_package_dir(base_package: str, ref: str) -> Path:
    """Return the filesystem path to the versioned sub-package.

    e.g. base_package="tailscale_cli", ref="v1.82.0"
         → REPO_ROOT / "tailscale_cli" / "v1_82_0"
    """
    pkg_name = ref_to_package_name(ref)
    return REPO_ROOT / base_package / pkg_name


def _version_import_path(base_package: str, ref: str) -> str:
    """Return the Python dotted-import prefix for the version package.

    e.g. "tailscale_cli.v1_82_0"
    """
    return f"{base_package}.{ref_to_package_name(ref)}"


# ---------------------------------------------------------------------------
# __init__.py generation for the version package
# ---------------------------------------------------------------------------


def _generate_version_init(
    base_package: str,
    ref: str,
    commit_sha: str,
    module_names: List[str],
) -> str:
    """Generate the __init__.py for a versioned sub-package."""
    pkg_name = ref_to_package_name(ref)
    lines = [
        '"""',
        f"Tailscale models pinned to upstream ref: {ref}",
        f"Commit : {commit_sha}",
        f"Package: {base_package}.{pkg_name}",
        "",
        "Auto-generated — DO NOT EDIT.",
        '"""',
        "",
    ]
    # Re-export all public names from each module for convenience
    for mod in sorted(module_names):
        lines.append(f"from .{mod} import *  # noqa: F401,F403")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _generate_one(
    cfg_source: Dict[str, Any],
    upstream_repo: str,
    upstream_ref: str,
    commit_sha: str,
    serde_import: str,
) -> str:
    """Fetch + parse + generate for a single source mapping. Returns generated code."""
    go_path: str = cfg_source["go_path"]

    url = f"https://github.com/{upstream_repo}/blob/{commit_sha}/{go_path}"

    print(f"  Fetching {go_path} @ {commit_sha[:12]}…")
    go_src = fetch_go_source(upstream_repo, commit_sha, go_path)

    print("  Parsing Go types…")
    ir = parse_go_file(go_src)

    struct_names = [s.name for s in ir.structs]
    enum_names = [c.type_name for c in ir.const_groups]
    alias_names = [a.name for a in ir.type_aliases]
    print(f"    {len(struct_names)} structs: {', '.join(struct_names)}")
    print(f"    {len(enum_names)} enums:   {', '.join(enum_names)}")
    print(f"    {len(alias_names)} aliases: {', '.join(alias_names)}")

    print("  Generating Python module…")
    code = generate_module(
        ir,
        upstream_url=url,
        upstream_commit=commit_sha,
        serde_import=serde_import,
    )
    return code


def run(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="codegen",
        description="Generate Python models from upstream Go source.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any generated file is out of date (CI mode).",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show a unified diff of what would change.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated code to stdout instead of writing files.",
    )
    parser.add_argument(
        "--pin",
        metavar="REF",
        help="Update codegen.toml to pin to a new ref (tag/SHA) before generating.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to codegen.toml (default: repo root).",
    )
    parser.add_argument(
        "--sync-tags",
        action="store_true",
        help="Discover all upstream release tags, generate any that are missing locally.",
    )
    parser.add_argument(
        "--include-pre-release",
        action="store_true",
        help="When used with --sync-tags, also include pre-release tags (-rc, -beta, etc.).",
    )
    parser.add_argument(
        "--min-version",
        default=None,
        help="Minimum version to consider with --sync-tags (e.g. '1.50.0'). "
        "Defaults to the lowest version already present locally.",
    )
    args = parser.parse_args(argv)

    cfg = _load_config(args.config)
    upstream_repo: str = cfg["upstream"]["repo"]
    upstream_ref: str = args.pin or cfg["upstream"]["ref"]
    base_package: str = cfg["upstream"].get("base_package", "tailscale_cli")

    # --sync-tags: discover upstream tags, generate any that are missing
    if args.sync_tags:
        return _sync_tags(cfg, args)

    # If --pin, update the config file first
    if args.pin:
        _update_pin(args.config or CONFIG_PATH, args.pin)

    # Derive the version package name from the ref
    pkg_name = ref_to_package_name(upstream_ref)
    _version_package_dir(base_package, upstream_ref)
    version_import = _version_import_path(base_package, upstream_ref)
    serde_import = f"{base_package}._util.serde"

    print(f"Upstream ref : {upstream_ref}")
    print(f"Python pkg   : {version_import}")

    # Resolve to full SHA for reproducibility
    print(f"Resolving {upstream_ref}…")
    commit_sha = resolve_commit_sha(upstream_repo, upstream_ref)
    print(f"  → {commit_sha}")

    stale = False
    module_names: List[str] = []

    for src_cfg in cfg["source"]:
        module_name: str = src_cfg["module_name"]
        module_names.append(module_name)
        py_rel = f"{base_package}/{pkg_name}/{module_name}.py"
        py_path = REPO_ROOT / py_rel

        code = _generate_one(
            src_cfg, upstream_repo, upstream_ref, commit_sha, serde_import
        )

        if args.dry_run:
            print(f"\n# ═══ {py_rel} ═══")
            print(code)
            continue

        existing = py_path.read_text() if py_path.exists() else ""
        if args.check or args.diff:
            if _content_changed(existing, code):
                stale = True
                if args.diff:
                    _print_diff(existing, code, py_rel)
                elif args.check:
                    print(f"  ✗ {py_rel} is stale")
        else:
            py_path.parent.mkdir(parents=True, exist_ok=True)
            py_path.write_text(code)
            print(f"  ✓ Wrote {py_rel}")

    # --- Generate __init__.py for the version package ---
    init_code = _generate_version_init(
        base_package, upstream_ref, commit_sha, module_names
    )
    init_rel = f"{base_package}/{pkg_name}/__init__.py"
    init_path = REPO_ROOT / init_rel

    if args.dry_run:
        print(f"\n# ═══ {init_rel} ═══")
        print(init_code)
    elif args.check or args.diff:
        existing_init = init_path.read_text() if init_path.exists() else ""
        if _content_changed(existing_init, init_code):
            stale = True
            if args.diff:
                _print_diff(existing_init, init_code, init_rel)
            elif args.check:
                print(f"  ✗ {init_rel} is stale")
    else:
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text(init_code)
        print(f"  ✓ Wrote {init_rel}")

    if args.check and stale:
        print("\nGenerated models are out of date. Run `python -m codegen` to update.")
        return 1

    if not args.check and not args.diff and not args.dry_run:
        print("\nImport with:")
        for mod in module_names:
            print(f"  from {version_import}.{mod} import *")

    return 0


# ---------------------------------------------------------------------------
# Sync-tags: discover & generate all missing upstream releases
# ---------------------------------------------------------------------------


def _existing_version_dirs(base_package: str) -> set[str]:
    """Return the set of version package directory names that already exist.

    e.g. {"v1_92_5", "v1_94_2"}
    """
    pkg_dir = REPO_ROOT / base_package
    if not pkg_dir.is_dir():
        return set()
    return {
        d.name
        for d in pkg_dir.iterdir()
        if d.is_dir()
        and d.name.startswith("v")
        and (d / "__init__.py").exists()
    }


def _detect_min_version(existing: set[str]) -> tuple[int, ...]:
    """Detect the minimum version from already-generated packages.

    Falls back to (1, 50, 0) if nothing exists yet.
    """
    import re as _re

    versions: list[tuple[int, ...]] = []
    for name in existing:
        m = _re.match(r"v(\d+)_(\d+)_(\d+)", name)
        if m:
            versions.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    if versions:
        return min(versions)
    return (1, 50, 0)


def _sync_tags(cfg: Dict[str, Any], args: argparse.Namespace) -> int:
    """Sync all missing upstream release tags."""
    upstream_repo: str = cfg["upstream"]["repo"]
    base_package: str = cfg["upstream"].get("base_package", "tailscale_cli")
    serde_import = f"{base_package}._util.serde"

    # Determine minimum version
    existing = _existing_version_dirs(base_package)
    if args.min_version:
        parts = args.min_version.replace("v", "").split(".")
        min_ver = tuple(int(p) for p in parts)
    else:
        min_ver = _detect_min_version(existing)

    print(f"Fetching upstream tags from {upstream_repo}…")
    all_tags = fetch_release_tags(
        upstream_repo,
        stable_only=not args.include_pre_release,
        min_version=min_ver,
    )
    print(f"  Found {len(all_tags)} upstream release tags (>= {'.'.join(str(v) for v in min_ver)})")

    # Find which tags are missing locally
    missing: List[str] = []
    for tag in all_tags:
        pkg_name = ref_to_package_name(tag)
        if pkg_name not in existing:
            missing.append(tag)

    if not missing:
        print("  All tags are up to date — nothing to generate.")
        return 0

    print(f"  {len(missing)} missing tag(s) to generate: {', '.join(missing)}")

    errors: List[str] = []
    generated_tags: List[str] = []

    for tag in missing:
        pkg_name = ref_to_package_name(tag)
        version_import = _version_import_path(base_package, tag)

        print(f"\n{'='*60}")
        print(f"Generating {tag} → {version_import}")
        print(f"{'='*60}")

        try:
            commit_sha = resolve_commit_sha(upstream_repo, tag)
            print(f"  Resolved to {commit_sha[:12]}")
        except Exception as e:
            print(f"  ✗ Failed to resolve {tag}: {e}")
            errors.append(f"{tag}: resolve failed: {e}")
            continue

        module_names: List[str] = []
        tag_ok = True

        for src_cfg in cfg["source"]:
            module_name: str = src_cfg["module_name"]
            module_names.append(module_name)
            py_rel = f"{base_package}/{pkg_name}/{module_name}.py"
            py_path = REPO_ROOT / py_rel

            try:
                code = _generate_one(
                    src_cfg, upstream_repo, tag, commit_sha, serde_import
                )
            except Exception as e:
                print(f"  ✗ Failed to generate {module_name} for {tag}: {e}")
                errors.append(f"{tag}/{module_name}: {e}")
                tag_ok = False
                break

            if args.dry_run:
                print(f"\n# ═══ {py_rel} ═══")
                print(code)
            else:
                py_path.parent.mkdir(parents=True, exist_ok=True)
                py_path.write_text(code)
                print(f"  ✓ Wrote {py_rel}")

        if not tag_ok:
            continue

        # Write __init__.py for this version
        init_code = _generate_version_init(
            base_package, tag, commit_sha, module_names
        )
        init_rel = f"{base_package}/{pkg_name}/__init__.py"
        init_path = REPO_ROOT / init_rel

        if args.dry_run:
            print(f"\n# ═══ {init_rel} ═══")
            print(init_code)
        else:
            init_path.parent.mkdir(parents=True, exist_ok=True)
            init_path.write_text(init_code)
            print(f"  ✓ Wrote {init_rel}")

        generated_tags.append(tag)

    # Summary
    print(f"\n{'='*60}")
    print(f"Sync complete: {len(generated_tags)} generated, {len(errors)} errors")
    if generated_tags:
        print(f"  Generated: {', '.join(generated_tags)}")
    if errors:
        print(f"  Errors:")
        for err in errors:
            print(f"    - {err}")
        return 1

    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _content_changed(existing: str, generated: str) -> bool:
    """Check if the meaningful content changed (ignoring the Generated: timestamp line)."""

    def _strip_timestamp(s: str) -> str:
        return "\n".join(
            line for line in s.splitlines() if not line.startswith("Generated:")
        )

    return _strip_timestamp(existing) != _strip_timestamp(generated)


def _print_diff(existing: str, generated: str, rel_path: str) -> None:
    diff = difflib.unified_diff(
        existing.splitlines(keepends=True),
        generated.splitlines(keepends=True),
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
    )
    sys.stdout.writelines(diff)


def _update_pin(config_path: Path, new_ref: str) -> None:
    """Rewrite the ref = "…" line in codegen.toml."""
    text = config_path.read_text()
    import re

    new_text = re.sub(
        r'^(ref\s*=\s*)"[^"]*"', f'\\1"{new_ref}"', text, flags=re.MULTILINE
    )
    config_path.write_text(new_text)
    print(f'  Updated {config_path.name}: ref = "{new_ref}"')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(run())
