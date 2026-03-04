"""
Main entrypoint for Tailscale's local API.

This is the class that should be used as a starting point to access a handle to
use this library.  By default the factory queries the running daemon for its
version and loads the matching generated ``LocalAPI`` automatically.

Example usage::

    from tailscale_cli import TailscaleCLI

    # Auto-detect the daemon version and load matching LocalAPI:
    api = TailscaleCLI.connect()
    status = api.status()   # returns a typed ipnstate.Status

    # Or pin to a specific version explicitly:
    api = TailscaleCLI.connect("v1.94.2")
    status = api.status()
"""

from __future__ import annotations

import importlib
import logging
import re
from pathlib import Path
from typing import Optional, Tuple, Type

from tailscale_cli._util.error import TailscaleException
from tailscale_cli._util.localapi_base import LocalAPIBase

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"^v(\d+)_(\d+)_(\d+)$")


def _ref_to_package_name(ref: str) -> str:
    """Convert a git ref like ``v1.94.2`` to a Python package name ``v1_94_2``."""
    name = ref.strip()
    if re.fullmatch(r"[0-9a-f]{40}", name):
        name = name[:12]
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if name and name[0].isdigit():
        name = "v" + name
    return name.lower()


def _parse_version_tuple(pkg_name: str) -> Optional[Tuple[int, ...]]:
    """Extract ``(major, minor, patch)`` from a package dir name like ``v1_94_2``."""
    m = _VERSION_RE.match(pkg_name)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _find_latest_version_package() -> Optional[str]:
    """Scan ``tailscale_cli/v*`` directories and return the newest package name.

    Only considers directories that contain a ``localapi.py``.
    """
    pkg_root = Path(__file__).resolve().parent
    best: Optional[Tuple[Tuple[int, ...], str]] = None

    for d in pkg_root.iterdir():
        if not d.is_dir() or not d.name.startswith("v"):
            continue
        if not (d / "localapi.py").exists():
            continue
        ver = _parse_version_tuple(d.name)
        if ver is None:
            continue
        if best is None or ver > best[0]:
            best = (ver, d.name)

    return best[1] if best else None


def _load_versioned_api(pkg_name: str) -> Optional[Type[LocalAPIBase]]:
    """Try to import ``tailscale_cli.<pkg_name>.localapi.LocalAPI``."""
    try:
        mod = importlib.import_module(f"tailscale_cli.{pkg_name}.localapi")
        cls = getattr(mod, "LocalAPI", None)
        if cls is not None and issubclass(cls, LocalAPIBase):
            return cls
    except (ModuleNotFoundError, AttributeError):
        pass
    return None


def _query_daemon_version(socket_path: str) -> Optional[str]:
    """Ask the running tailscaled for its version.

    The daemon sets a ``Tailscale-Version`` header on *every* HTTP
    response, so we issue a lightweight ``GET /localapi/v0/status``
    (without peers) and read that header — exactly like the official
    Go ``tailscale`` CLI does.

    Returns a semver-style ref string (e.g. ``"v1.94.2"``) or ``None``
    if the header is absent.

    Raises:
        TailscaleException: If the daemon is unreachable.
    """
    try:
        probe = LocalAPIBase(socket_path=socket_path)
        ver = probe.daemon_version()
        if ver:
            ver = ver.strip()
            if not ver.startswith("v"):
                ver = "v" + ver
            return ver
    except Exception as exc:
        raise TailscaleException.connection_error() from exc
    return None


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


class TailscaleCLI:
    """Factory for Tailscale local-API handles."""

    @classmethod
    def connect(
        cls,
        version: Optional[str] = None,
        *,
        socket_path: str = "/run/tailscale/tailscaled.sock",
    ) -> LocalAPIBase:
        """Create a version-matched :class:`LocalAPI` handle.

        Resolution order:

        1. Explicit *version* argument (e.g. ``"v1.94.2"``).
        2. Live query of the running ``tailscaled`` daemon via
           ``GET /localapi/v0/version``.
        3. **Fallback** — the newest generated version package found
           locally under ``tailscale_cli/``.

        If none of the above produces a usable versioned ``LocalAPI``,
        a bare :class:`LocalAPIBase` (transport-only, no typed methods)
        is returned.

        Args:
            version:     Pin to a specific upstream version.
            socket_path: Path to the ``tailscaled`` UNIX socket.

        Returns:
            A :class:`LocalAPIBase` subclass with version-specific endpoint
            methods and typed model returns.
        """
        # --- 0. Verify the daemon is reachable -----------------------------
        daemon_version = _query_daemon_version(socket_path)

        # --- 1. Determine the target ref -----------------------------------
        ref = version

        if ref is None:
            ref = daemon_version
            if ref:
                log.debug("Detected tailscaled version: %s", ref)

        # --- 2. Try exact-match import for that version --------------------
        if ref:
            pkg = _ref_to_package_name(ref)
            VersionedAPI = _load_versioned_api(pkg)
            if VersionedAPI is not None:
                log.debug("Loaded versioned LocalAPI from tailscale_cli.%s", pkg)
                return VersionedAPI(socket_path=socket_path)
            else:
                log.debug("No generated package for %s (tailscale_cli.%s)", ref, pkg)

        # --- 3. Fallback to latest local version ---------------------------
        latest_pkg = _find_latest_version_package()
        if latest_pkg:
            VersionedAPI = _load_versioned_api(latest_pkg)
            if VersionedAPI is not None:
                if ref:
                    log.info(
                        "Exact version %s not available; falling back to %s",
                        ref, latest_pkg,
                    )
                else:
                    log.debug("Using latest local version: %s", latest_pkg)
                return VersionedAPI(socket_path=socket_path)

        # --- 4. Nothing available — bare transport -------------------------
        log.warning(
            "No generated LocalAPI packages found. "
            "Run: python -m codegen --sync-tags"
        )
        return LocalAPIBase(socket_path=socket_path)

    # Backwards compatibility alias
    @classmethod
    def v0(cls, *, socket_path: str = "/run/tailscale/tailscaled.sock") -> LocalAPIBase:
        """Deprecated — use :meth:`connect` instead."""
        return cls.connect(socket_path=socket_path)
