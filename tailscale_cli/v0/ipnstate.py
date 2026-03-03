from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, NewType, Optional

from tailscale_cli._util.serde import SerdeMixin

# --- External / opaque Go types (modeled as light Python aliases) ---

NodePublic = NewType("NodePublic", str)  # key.NodePublic
NLPublic = NewType("NLPublic", str)  # key.NLPublic
NodeCapability = NewType("NodeCapability", str)  # tailcfg.NodeCapability

UserID = NewType("UserID", int)  # tailcfg.UserID
NodeID = NewType("NodeID", int)  # tailcfg.NodeID
StableNodeID = NewType("StableNodeID", str)  # tailcfg.StableNodeID

UserProfile = Dict[str, Any]  # tailcfg.UserProfile (opaque)
ClientVersion = Dict[str, Any]  # tailcfg.ClientVersion (opaque)
Location = Dict[str, Any]  # tailcfg.Location (opaque)

NodeKeySignature = NewType("NodeKeySignature", str)  # tka.NodeKeySignature

# --- netip equivalents (keep as strings unless you already have wrappers) ---

NetipAddr = NewType("NetipAddr", str)  # netip.Addr
NetipPrefix = NewType("NetipPrefix", str)  # netip.Prefix


# --- Enums (must be defined before use in type annotations/defaults) ---


class TaildropTargetStatus(IntEnum):
    UNKNOWN = 0
    AVAILABLE = 1
    NO_NETMAP_AVAILABLE = 2
    IPN_STATE_NOT_RUNNING = 3
    MISSING_CAP = 4
    OFFLINE = 5
    NO_PEER_INFO = 6
    UNSUPPORTED_OS = 7
    NO_PEER_API = 8
    OWNED_BY_OTHER_USER = 9


class SelfUpdateStatus(str, Enum):
    UPDATE_FINISHED = "UpdateFinished"
    UPDATE_IN_PROGRESS = "UpdateInProgress"
    UPDATE_FAILED = "UpdateFailed"


# --- Dataclasses ---


@dataclass
class TKAKey(SerdeMixin):
    kind: str = ""
    key: NLPublic = NLPublic("")
    metadata: Dict[str, str] = field(default_factory=dict)
    votes: int = 0


@dataclass
class TKAPeer(SerdeMixin):
    name: str = ""
    id: NodeID = NodeID(0)
    stable_id: StableNodeID = StableNodeID("")
    tailscale_ips: List[NetipAddr] = field(default_factory=list)
    node_key: NodePublic = NodePublic("")
    node_key_signature: NodeKeySignature = NodeKeySignature("")


@dataclass
class NetworkLockStatus(SerdeMixin):
    enabled: bool = False
    head: Optional[bytes] = None  # Go: *[32]byte; store 32 bytes or None
    public_key: NLPublic = NLPublic("")
    node_key: Optional[NodePublic] = None
    node_key_signed: bool = False
    node_key_signature: Optional[NodeKeySignature] = None
    trusted_keys: List[TKAKey] = field(default_factory=list)
    visible_peers: List[TKAPeer] = field(default_factory=list)
    filtered_peers: List[TKAPeer] = field(default_factory=list)
    state_id: int = 0  # uint64


@dataclass
class NetworkLockUpdate(SerdeMixin):
    hash: bytes = b""  # Go: [32]byte; store 32 bytes
    change: str = ""
    raw: bytes = b""


@dataclass
class TailnetStatus(SerdeMixin):
    name: str = ""
    magic_dns_suffix: str = ""
    magic_dns_enabled: bool = False


@dataclass
class ExitNodeStatus(SerdeMixin):
    id: StableNodeID = StableNodeID("")
    online: bool = False
    tailscale_ips: List[NetipPrefix] = field(default_factory=list)


@dataclass
class PeerStatusLite(SerdeMixin):
    node_key: NodePublic = NodePublic("")
    tx_bytes: int = 0
    rx_bytes: int = 0
    last_handshake: Optional[datetime] = None


@dataclass
class PeerStatus(SerdeMixin):
    id: StableNodeID = StableNodeID("")
    public_key: NodePublic = NodePublic("")
    host_name: str = ""

    dns_name: str = ""
    os: str = ""
    user_id: UserID = UserID(0)
    alt_sharer_user_id: UserID = UserID(0)

    tailscale_ips: List[NetipAddr] = field(default_factory=list)
    allowed_ips: Optional[List[NetipPrefix]] = None
    tags: Optional[List[str]] = None
    primary_routes: Optional[List[NetipPrefix]] = None

    addrs: List[str] = field(default_factory=list)
    cur_addr: str = ""
    relay: str = ""
    peer_relay: str = ""

    rx_bytes: int = 0
    tx_bytes: int = 0
    created: Optional[datetime] = None
    last_write: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_handshake: Optional[datetime] = None

    online: bool = False
    exit_node: bool = False
    exit_node_option: bool = False
    active: bool = False

    peer_api_url: List[str] = field(default_factory=list)

    taildrop_target: TaildropTargetStatus = TaildropTargetStatus.UNKNOWN
    no_file_sharing_reason: str = ""

    capabilities: List[NodeCapability] = field(default_factory=list)
    cap_map: Dict[str, Any] = field(default_factory=dict)

    ssh_host_keys: List[str] = field(default_factory=list)

    sharee_node: bool = False
    in_network_map: bool = False
    in_magic_sock: bool = False
    in_engine: bool = False

    expired: bool = False
    key_expiry: Optional[datetime] = None
    location: Optional[Location] = None

    def has_cap(self, cap: NodeCapability) -> bool:
        # Best-effort with our opaque cap_map representation
        return str(cap) in self.cap_map or str(cap) in {
            str(c) for c in self.capabilities
        }

    def is_tagged(self) -> bool:
        return bool(self.tags)


@dataclass
class Status(SerdeMixin):
    version: str = ""
    tun: bool = False
    backend_state: str = ""

    have_node_key: bool = False
    auth_url: str = ""
    tailscale_ips: List[NetipAddr] = field(default_factory=list)
    _self: Optional[PeerStatus] = None

    exit_node_status: Optional[ExitNodeStatus] = None
    health: List[str] = field(default_factory=list)

    magic_dns_suffix: str = ""
    current_tailnet: Optional[TailnetStatus] = None

    cert_domains: List[str] = field(default_factory=list)

    # NOTE: JSON from tailscaled often uses string keys here; our SerdeMixin will
    # keep them as-is unless you add custom coercion in SerdeMixin.
    peer: Dict[NodePublic, PeerStatus] = field(default_factory=dict)
    user: Dict[UserID, UserProfile] = field(default_factory=dict)

    client_version: Optional[ClientVersion] = None


@dataclass
class PingResult(SerdeMixin):
    ip: str = ""
    node_ip: str = ""
    node_name: str = ""

    err: str = ""
    latency_seconds: float = 0.0

    endpoint: str = ""
    peer_relay: str = ""

    derp_region_id: int = 0
    derp_region_code: str = ""

    peer_api_port: int = 0
    peer_api_url: str = ""

    is_local_ip: bool = False


@dataclass
class DebugDERPRegionReport(SerdeMixin):
    info: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class UpdateProgress(SerdeMixin):
    status: Optional[SelfUpdateStatus] = None
    message: str = ""
    version: str = ""
