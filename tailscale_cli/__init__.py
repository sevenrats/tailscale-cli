"""
Control Tailscale's local API.
"""

from ._util.error import TailscaleException as TailscaleException
from ._util.localapi_base import LocalAPIBase as LocalAPIBase
from .api import TailscaleCLI as TailscaleCLI

# ---------------------------------------------------------------------------
# Canonical type re-exports (from the latest generated version).
#
# These are the dataclass models returned by LocalAPI methods such as
# ``status()``, ``ping()``, etc.  They are re-exported here so that
# consumers can write::
#
#     from tailscale_cli import Status, PeerStatus
#
# instead of reaching into a version-specific sub-package.  At runtime
# the object returned by ``connect()`` will use its own version's
# model classes, but these are structurally compatible for type-checking.
# ---------------------------------------------------------------------------

from .v1_94_2.ipnstate import (  # noqa: E402 — re-exports for convenience
    DebugDERPRegionReport as DebugDERPRegionReport,
    ExitNodeStatus as ExitNodeStatus,
    NetworkLockStatus as NetworkLockStatus,
    NetworkLockUpdate as NetworkLockUpdate,
    PeerStatus as PeerStatus,
    PeerStatusLite as PeerStatusLite,
    PingResult as PingResult,
    SelfUpdateStatus as SelfUpdateStatus,
    Status as Status,
    StatusBuilder as StatusBuilder,
    TailnetStatus as TailnetStatus,
    TaildropTargetStatus as TaildropTargetStatus,
    TKAKey as TKAKey,
    TKAPeer as TKAPeer,
    UpdateProgress as UpdateProgress,
)
