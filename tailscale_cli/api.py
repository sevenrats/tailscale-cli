"""
Main entrypoint for Tailscale's local API.

This is the class that should be used as a starting point to access a handle to
use this library.  By default the factory queries the running daemon for its
version and loads the matching generated models automatically.

Example usage::

    from tailscale_cli import TailscaleCLI

    # Auto-detect the daemon version and load matching models:
    api = TailscaleCLI.connect()
    status = api.status()   # returns a typed model if models exist

    # Or pin to a specific model version explicitly:
    api = TailscaleCLI.connect("v1.94.2")
    status = api.status()   # → tailscale_cli.v1_94_2.ipnstate.Status
"""

from __future__ import annotations

import importlib
import logging
from typing import Optional

from tailscale_cli.v0.api import LocalAPI

log = logging.getLogger(__name__)


# Lazy helper: read the pinned ref from codegen.toml without pulling in tomllib
# at import time.  Falls back to None if the config isn't found.
def _default_ref() -> Optional[str]:
    try:
        from pathlib import Path

        cfg_path = Path(__file__).resolve().parent.parent / "codegen.toml"
        if not cfg_path.exists():
            return None
        for line in cfg_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("ref"):
                # ref = "v1.82.0"
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def _ref_to_package_name(ref: str) -> str:
    """Inline copy of codegen.type_map.ref_to_package_name (avoid import cycle)."""
    import re

    name = ref.strip()
    if re.fullmatch(r"[0-9a-f]{40}", name):
        name = name[:12]
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if name and name[0].isdigit():
        name = "v" + name
    return name.lower()


def _query_daemon_version(api: LocalAPI) -> Optional[str]:
    """Ask the running tailscaled for its version.

    Returns a semver-style ref string (e.g. ``"v1.94.2"``) or ``None`` if the
    daemon is unreachable or the response is missing the expected field.
    """
    try:
        info = api.version()
        # The JSON payload normally contains "majorMinorPatch" (e.g. "1.94.2")
        # as well as "short" (e.g. "1.94.2") and "long".
        mmp = info.get("majorMinorPatch") or info.get("short")
        if mmp:
            mmp = mmp.strip()
            if not mmp.startswith("v"):
                mmp = "v" + mmp
            return mmp
    except Exception:
        log.debug("Could not query tailscaled version", exc_info=True)
    return None


class TailscaleCLI:
    """Factory for Tailscale local-API handles."""

    @classmethod
    def connect(
        cls,
        version: Optional[str] = None,
        *,
        socket_path: str = "/run/tailscale/tailscaled.sock",
    ) -> LocalAPI:
        """
        Create a :class:`LocalAPI` handle bound to models generated from the
        given upstream *version* (tag, branch, or commit hash).

        The *version* string is resolved to a Python sub-package under
        ``tailscale_cli``.  For example ``"v1.82.0"`` → ``tailscale_cli.v1_82_0``.

        Version resolution order:

        1. Explicit *version* argument (if provided).
        2. Live query of the running ``tailscaled`` daemon via
           ``GET /localapi/v0/version`` (uses the ``majorMinorPatch`` field).
        3. Static ref pinned in ``codegen.toml``.

        If none of the above yields a version, the API handle is returned
        without typed models (responses will be raw dicts).

        Args:
            version:     Upstream ref string (e.g. ``"v1.94.2"``).  When
                         ``None`` the daemon is queried automatically.
            socket_path: Path to the tailscaled UNIX socket.

        Returns:
            A :class:`LocalAPI` instance with version-matched model classes.

        Raises:
            ImportError: If an explicit *version* was given but models for
                that version haven't been generated yet.
        """
        # --- 1. Build a bare API handle (no models yet) ----------------------
        api = LocalAPI(socket_path=socket_path, models=None)

        # --- 2. Determine the target ref -------------------------------------
        ref = version  # explicit always wins
        detected_from_daemon = False

        if ref is None:
            ref = _query_daemon_version(api)
            if ref:
                detected_from_daemon = True
                log.debug("Detected tailscaled version: %s", ref)

        if ref is None:
            ref = _default_ref()
            if ref:
                log.debug("Falling back to codegen.toml ref: %s", ref)

        # --- 3. Try to load matching generated models ------------------------
        models = None
        if ref:
            pkg = _ref_to_package_name(ref)
            try:
                models = importlib.import_module(f"tailscale_cli.{pkg}")
            except ModuleNotFoundError:
                if detected_from_daemon:
                    # Auto-detected version — not fatal, just warn.
                    log.warning(
                        "No generated models for daemon version %s "
                        "(expected package tailscale_cli.%s). "
                        "Responses will be raw dicts. "
                        "Run: python -m codegen --pin %s",
                        ref,
                        pkg,
                        ref,
                    )
                else:
                    # Caller explicitly asked for this version — fail hard.
                    raise ImportError(
                        f"No generated models for version {ref!r} "
                        f"(expected package tailscale_cli.{pkg}).\n"
                        f"Run: python -m codegen --pin {ref}"
                    ) from None

        # --- 4. Bind models onto the existing handle -------------------------
        api._models = models
        return api

    # Backwards compatibility alias
    @classmethod
    def v0(cls, *, socket_path: str = "/run/tailscale/tailscaled.sock") -> LocalAPI:
        """Deprecated — use :meth:`connect` instead."""
        return cls.connect(socket_path=socket_path)
