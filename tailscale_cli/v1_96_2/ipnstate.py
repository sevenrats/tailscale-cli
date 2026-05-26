"""
Auto-generated from upstream Go source — DO NOT EDIT.

Source : https://github.com/tailscale/tailscale/blob/17a4f58b5c457d350b1e357c8b1e3a9e7188416b/ipn/ipnstate/ipnstate.go
Commit : 17a4f58b5c457d350b1e357c8b1e3a9e7188416b
Generated: 2026-05-26T00:54:15Z
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, ClassVar, Dict, List, NewType, Optional

from tailscale_cli._util.serde import SerdeMixin

# --- External / opaque Go types ---

NLPublic = NewType("NLPublic", str)  # key.NLPublic
NodePublic = NewType("NodePublic", str)  # key.NodePublic
Addr = NewType("Addr", str)  # netip.Addr
Prefix = NewType("Prefix", str)  # netip.Prefix
NodeCapability = NewType("NodeCapability", str)  # tailcfg.NodeCapability
NodeID = NewType("NodeID", int)  # tailcfg.NodeID
StableNodeID = NewType("StableNodeID", str)  # tailcfg.StableNodeID
UserID = NewType("UserID", int)  # tailcfg.UserID
NodeKeySignature = NewType("NodeKeySignature", str)  # tka.NodeKeySignature


class TaildropTargetStatus(IntEnum):
    TAILDROP_TARGET_UNKNOWN = 0
    TAILDROP_TARGET_AVAILABLE = 1
    TAILDROP_TARGET_NO_NETMAP_AVAILABLE = 2
    TAILDROP_TARGET_IPN_STATE_NOT_RUNNING = 3
    TAILDROP_TARGET_MISSING_CAP = 4
    TAILDROP_TARGET_OFFLINE = 5
    TAILDROP_TARGET_NO_PEER_INFO = 6
    TAILDROP_TARGET_UNSUPPORTED_OS = 7
    TAILDROP_TARGET_NO_PEER_API = 8
    TAILDROP_TARGET_OWNED_BY_OTHER_USER = 9


class SelfUpdateStatus(str, Enum):
    UPDATE_FINISHED = 'UpdateFinished'
    UPDATE_IN_PROGRESS = 'UpdateInProgress'
    UPDATE_FAILED = 'UpdateFailed'


# go:generate go run tailscale.com/cmd/cloner  -clonefunc=false -type=TKAPeer
# Status represents the entire state of the IPN network.
@dataclass
class Status(SerdeMixin):
    version: str = ""  # json="Version"
    tun: bool = False  # json="TUN"
    backend_state: str = ""  # json="BackendState"
    have_node_key: bool = False  # json="HaveNodeKey"
    auth_url: str = ""  # json="AuthURL"; current URL provided by control to authorize client
    tailscale_ips: List[Addr] = field(default_factory=list)  # json="TailscaleIPs"; Tailscale IP(s) assigned to this node
    _self: Optional[PeerStatus] = None  # json="Self"
    exit_node_status: Optional[ExitNodeStatus] = None  # json="ExitNodeStatus"
    health: List[str] = field(default_factory=list)  # json="Health"
    magic_dns_suffix: str = ""  # json="MagicDNSSuffix"
    current_tailnet: Optional[TailnetStatus] = None  # json="CurrentTailnet"
    cert_domains: List[str] = field(default_factory=list)  # json="CertDomains"
    peer: Dict[NodePublic, Optional[PeerStatus]] = field(default_factory=dict)  # json="Peer"
    user: Dict[UserID, Dict[str, Any]] = field(default_factory=dict)  # json="User"
    client_version: Optional[Dict[str, Any]] = None  # json="ClientVersion"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "AuthURL": "auth_url",
        "BackendState": "backend_state",
        "CertDomains": "cert_domains",
        "ClientVersion": "client_version",
        "CurrentTailnet": "current_tailnet",
        "ExitNodeStatus": "exit_node_status",
        "HaveNodeKey": "have_node_key",
        "Health": "health",
        "MagicDNSSuffix": "magic_dns_suffix",
        "Peer": "peer",
        "Self": "_self",
        "TUN": "tun",
        "TailscaleIPs": "tailscale_ips",
        "User": "user",
        "Version": "version",
    }


# TKAKey describes a key trusted by network lock.
@dataclass
class TKAKey(SerdeMixin):
    kind: str = ""  # json="Kind"
    key: NLPublic = NLPublic("")  # json="Key"
    metadata: Dict[str, str] = field(default_factory=dict)  # json="Metadata"
    votes: int = 0  # json="Votes"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Key": "key",
        "Kind": "kind",
        "Metadata": "metadata",
        "Votes": "votes",
    }


# TKAPeer describes a peer and its network lock details.
@dataclass
class TKAPeer(SerdeMixin):
    name: str = ""  # json="Name"; DNS
    id: NodeID = NodeID(0)  # json="ID"
    stable_id: StableNodeID = StableNodeID("")  # json="StableID"
    tailscale_ips: List[Addr] = field(default_factory=list)  # json="TailscaleIPs"; Tailscale IP(s) assigned to this node
    node_key: NodePublic = NodePublic("")  # json="NodeKey"
    node_key_signature: NodeKeySignature = NodeKeySignature("")  # json="NodeKeySignature"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "ID": "id",
        "Name": "name",
        "NodeKey": "node_key",
        "NodeKeySignature": "node_key_signature",
        "StableID": "stable_id",
        "TailscaleIPs": "tailscale_ips",
    }


# NetworkLockStatus represents whether network-lock is enabled,
# along with details about the locally-known state of the tailnet
# key authority.
@dataclass
class NetworkLockStatus(SerdeMixin):
    enabled: bool = False  # json="Enabled"
    head: Optional[Optional[bytes]] = None  # json="Head"
    public_key: NLPublic = NLPublic("")  # json="PublicKey"
    node_key: Optional[NodePublic] = None  # json="NodeKey"
    node_key_signed: bool = False  # json="NodeKeySigned"
    node_key_signature: Optional[NodeKeySignature] = None  # json="NodeKeySignature"
    trusted_keys: List[TKAKey] = field(default_factory=list)  # json="TrustedKeys"
    visible_peers: List[Optional[TKAPeer]] = field(default_factory=list)  # json="VisiblePeers"
    filtered_peers: List[Optional[TKAPeer]] = field(default_factory=list)  # json="FilteredPeers"
    state_id: int = 0  # json="StateID"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Enabled": "enabled",
        "FilteredPeers": "filtered_peers",
        "Head": "head",
        "NodeKey": "node_key",
        "NodeKeySignature": "node_key_signature",
        "NodeKeySigned": "node_key_signed",
        "PublicKey": "public_key",
        "StateID": "state_id",
        "TrustedKeys": "trusted_keys",
        "VisiblePeers": "visible_peers",
    }


# NetworkLockUpdate describes a change to network-lock state.
@dataclass
class NetworkLockUpdate(SerdeMixin):
    hash: Optional[bytes] = None  # json="Hash"
    change: str = ""  # json="Change"; values of tka.AUMKind.String()
    raw: List[int] = field(default_factory=list)  # json="Raw"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Change": "change",
        "Hash": "hash",
        "Raw": "raw",
    }


# TailnetStatus is information about a Tailscale network ("tailnet").
@dataclass
class TailnetStatus(SerdeMixin):
    name: str = ""  # json="Name"
    magic_dns_suffix: str = ""  # json="MagicDNSSuffix"
    magic_dns_enabled: bool = False  # json="MagicDNSEnabled"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "MagicDNSEnabled": "magic_dns_enabled",
        "MagicDNSSuffix": "magic_dns_suffix",
        "Name": "name",
    }


# ExitNodeStatus describes the current exit node.
@dataclass
class ExitNodeStatus(SerdeMixin):
    id: StableNodeID = StableNodeID("")  # json="ID"
    online: bool = False  # json="Online"
    tailscale_ips: List[Prefix] = field(default_factory=list)  # json="TailscaleIPs"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "ID": "id",
        "Online": "online",
        "TailscaleIPs": "tailscale_ips",
    }


@dataclass
class PeerStatusLite(SerdeMixin):
    node_key: NodePublic = NodePublic("")  # json="NodeKey"
    tx_bytes: int = 0  # json="TxBytes"
    rx_bytes: int = 0  # json="RxBytes"
    last_handshake: datetime = None  # json="LastHandshake"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "LastHandshake": "last_handshake",
        "NodeKey": "node_key",
        "RxBytes": "rx_bytes",
        "TxBytes": "tx_bytes",
    }


# PeerStatus describes a peer node and its current state.
# WARNING: The fields in PeerStatus are merged by the AddPeer method in the StatusBuilder.
# When adding a new field to PeerStatus, you must update AddPeer to handle merging
# the new field. The AddPeer function is responsible for combining multiple updates
# to the same peer, and any new field that is not merged properly may lead to
# inconsistencies or lost data in the peer status.
@dataclass
class PeerStatus(SerdeMixin):
    id: StableNodeID = StableNodeID("")  # json="ID"
    public_key: NodePublic = NodePublic("")  # json="PublicKey"
    host_name: str = ""  # json="HostName"; HostInfo's Hostname (not a DNS name or necessarily unique)
    dns_name: str = ""  # json="DNSName"
    os: str = ""  # json="OS"; HostInfo.OS
    user_id: UserID = UserID(0)  # json="UserID"
    alt_sharer_user_id: UserID = UserID(0)  # json="AltSharerUserID"
    tailscale_ips: List[Addr] = field(default_factory=list)  # json="TailscaleIPs"
    allowed_ips: Optional[Dict[str, Any]] = None  # json="AllowedIPs"
    tags: Optional[Dict[str, Any]] = None  # json="Tags"
    primary_routes: Optional[Dict[str, Any]] = None  # json="PrimaryRoutes"
    addrs: List[str] = field(default_factory=list)  # json="Addrs"
    cur_addr: str = ""  # json="CurAddr"; one of Addrs, or unique if roaming
    relay: str = ""  # json="Relay"; DERP region
    peer_relay: str = ""  # json="PeerRelay"; peer relay address (ip:port:vni)
    rx_bytes: int = 0  # json="RxBytes"
    tx_bytes: int = 0  # json="TxBytes"
    created: datetime = None  # json="Created"; time registered with tailcontrol
    last_write: datetime = None  # json="LastWrite"; time last packet sent
    last_seen: datetime = None  # json="LastSeen"; last seen to tailcontrol; only present if offline
    last_handshake: datetime = None  # json="LastHandshake"; with local wireguard
    online: bool = False  # json="Online"; whether node is connected to the control plane
    exit_node: bool = False  # json="ExitNode"; true if this is the currently selected exit node.
    exit_node_option: bool = False  # json="ExitNodeOption"; true if this node can be an exit node (offered && approved)
    active: bool = False  # json="Active"
    peer_apiurl: List[str] = field(default_factory=list)  # json="PeerAPIURL"
    taildrop_target: TaildropTargetStatus = None  # json="TaildropTarget"
    no_file_sharing_reason: str = ""  # json="NoFileSharingReason"
    capabilities: List[NodeCapability] = field(default_factory=list)  # json="Capabilities"
    cap_map: Dict[str, Any] = field(default_factory=dict)  # json="CapMap"
    ssh_host_keys: List[str] = field(default_factory=list)  # json="sshHostKeys"
    sharee_node: bool = False  # json="ShareeNode"
    in_network_map: bool = False  # json="InNetworkMap"
    in_magic_sock: bool = False  # json="InMagicSock"
    in_engine: bool = False  # json="InEngine"
    expired: bool = False  # json="Expired"
    key_expiry: Optional[datetime] = None  # json="KeyExpiry"
    location: Optional[Dict[str, Any]] = None  # json="Location"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Active": "active",
        "Addrs": "addrs",
        "AllowedIPs": "allowed_ips",
        "AltSharerUserID": "alt_sharer_user_id",
        "CapMap": "cap_map",
        "Capabilities": "capabilities",
        "Created": "created",
        "CurAddr": "cur_addr",
        "DNSName": "dns_name",
        "ExitNode": "exit_node",
        "ExitNodeOption": "exit_node_option",
        "Expired": "expired",
        "HostName": "host_name",
        "ID": "id",
        "InEngine": "in_engine",
        "InMagicSock": "in_magic_sock",
        "InNetworkMap": "in_network_map",
        "KeyExpiry": "key_expiry",
        "LastHandshake": "last_handshake",
        "LastSeen": "last_seen",
        "LastWrite": "last_write",
        "Location": "location",
        "NoFileSharingReason": "no_file_sharing_reason",
        "OS": "os",
        "Online": "online",
        "PeerAPIURL": "peer_apiurl",
        "PeerRelay": "peer_relay",
        "PrimaryRoutes": "primary_routes",
        "PublicKey": "public_key",
        "Relay": "relay",
        "RxBytes": "rx_bytes",
        "ShareeNode": "sharee_node",
        "Tags": "tags",
        "TaildropTarget": "taildrop_target",
        "TailscaleIPs": "tailscale_ips",
        "TxBytes": "tx_bytes",
        "UserID": "user_id",
        "sshHostKeys": "ssh_host_keys",
    }


# StatusBuilder is a request to construct a Status. A new StatusBuilder is
# passed to various subsystems which then call methods on it to populate state.
# Call its Status method to return the final constructed Status.
@dataclass
class StatusBuilder(SerdeMixin):
    want_peers: bool = False  # json="WantPeers"; whether caller wants peers

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "WantPeers": "want_peers",
    }


# PingResult contains response information for the "tailscale ping" subcommand,
# saying how Tailscale can reach a Tailscale IP or subnet-routed IP.
# See tailcfg.PingResponse for a related response that is sent back to control
# for remote diagnostic pings.
@dataclass
class PingResult(SerdeMixin):
    ip: str = ""  # json="IP"; ping destination
    node_ip: str = ""  # json="NodeIP"; Tailscale IP of node handling IP (different for subnet routers)
    node_name: str = ""  # json="NodeName"; DNS name base or (possibly not unique) hostname
    err: str = ""  # json="Err"
    latency_seconds: float = 0.0  # json="LatencySeconds"
    endpoint: str = ""  # json="Endpoint"
    peer_relay: str = ""  # json="PeerRelay"
    derp_region_id: int = 0  # json="DERPRegionID"
    derp_region_code: str = ""  # json="DERPRegionCode"
    peer_api_port: int = 0  # json="PeerAPIPort"
    peer_apiurl: str = ""  # json="PeerAPIURL"
    is_local_ip: bool = False  # json="IsLocalIP"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "DERPRegionCode": "derp_region_code",
        "DERPRegionID": "derp_region_id",
        "Endpoint": "endpoint",
        "Err": "err",
        "IP": "ip",
        "IsLocalIP": "is_local_ip",
        "LatencySeconds": "latency_seconds",
        "NodeIP": "node_ip",
        "NodeName": "node_name",
        "PeerAPIPort": "peer_api_port",
        "PeerAPIURL": "peer_apiurl",
        "PeerRelay": "peer_relay",
    }


# DebugDERPRegionReport is the result of a "tailscale debug derp" command,
# to let people debug a custom DERP setup.
@dataclass
class DebugDERPRegionReport(SerdeMixin):
    info: List[str] = field(default_factory=list)  # json="Info"
    warnings: List[str] = field(default_factory=list)  # json="Warnings"
    errors: List[str] = field(default_factory=list)  # json="Errors"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Errors": "errors",
        "Info": "info",
        "Warnings": "warnings",
    }


@dataclass
class UpdateProgress(SerdeMixin):
    status: SelfUpdateStatus = None
    message: str = ""
    version: str = ""


