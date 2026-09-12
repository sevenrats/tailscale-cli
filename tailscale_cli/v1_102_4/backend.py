"""
Auto-generated from upstream Go source — DO NOT EDIT.

Source : https://github.com/tailscale/tailscale/blob/bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8/ipn/backend.go
Commit : bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8
Generated: 2026-09-12T10:09:30Z
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, ClassVar, Dict, List, NewType, Optional

from tailscale_cli._util.serde import SerdeMixin

# --- External / opaque Go types ---

NodePublic = NewType("NodePublic", str)  # key.NodePublic
NodeID = NewType("NodeID", int)  # tailcfg.NodeID
StableNodeID = NewType("StableNodeID", str)  # tailcfg.StableNodeID
UserID = NewType("UserID", int)  # tailcfg.UserID


class State(IntEnum):
    NO_STATE = 0
    IN_USE_OTHER_USER = 1
    NEEDS_LOGIN = 2
    NEEDS_MACHINE_AUTH = 3
    STOPPED = 4
    STARTING = 5
    RUNNING = 6


class NotifyWatchOpt(IntEnum):
    NOTIFY_WATCH_ENGINE_UPDATES = 0
    NOTIFY_INITIAL_STATE = 1  # if set, the first Notify message (sent immediately) will contain the current State + BrowseToURL + SessionID
    NOTIFY_INITIAL_PREFS = 2  # if set, the first Notify message (sent immediately) will contain the current Prefs
    NOTIFY_INITIAL_NET_MAP = 3  # if set, the first Notify message (sent immediately) will contain the current NetMap
    NOTIFY_NO_PRIVATE_KEYS = 4  # (no-op) it used to redact private keys; now they always are and this does nothing
    NOTIFY_INITIAL_DRIVE_SHARES = 5  # if set, the first Notify message (sent immediately) will contain the current Taildrive Shares
    NOTIFY_INITIAL_OUTGOING_FILES = 6  # if set, the first Notify message (sent immediately) will contain the current Taildrop OutgoingFiles
    NOTIFY_INITIAL_HEALTH_STATE = 7  # if set, the first Notify message (sent immediately) will contain the current health.State of the client
    NOTIFY_RATE_LIMIT = 8  # if set, rate limit spammy netmap updates to every few seconds
    NOTIFY_HEALTH_ACTIONS = 9  # if set, include PrimaryActions in health.State. Otherwise append the action URL to the text
    NOTIFY_INITIAL_SUGGESTED_EXIT_NODE = 10  # if set, the first Notify message (sent immediately) will contain the current SuggestedExitNode if available
    NOTIFY_INITIAL_CLIENT_VERSION = 11  # if set, the first Notify message (sent immediately) will contain the current ClientVersion if available and if update checks are enabled
    NOTIFY_PEER_CHANGES = 12
    NOTIFY_NO_NET_MAP = 13
    NOTIFY_INITIAL_STATUS = 14
    NOTIFY_PEER_PATCHES = 15
    NOTIFY_IN_PROCESS_NO_DISCONNECT = 16
    NOTIFY_SYS_POLICY_CHANGES = 17
    NOTIFY_PEER_WIRE_GUARD_STATE = 18


class PeerWireGuardState(IntEnum):
    NONE = 0
    HANDSHAKE = 1
    ESTABLISHED = 2
    EXPIRED = 3


# EngineStatus contains WireGuard engine stats.
@dataclass
class EngineStatus(SerdeMixin):
    r_bytes: int = 0  # json="RBytes"
    w_bytes: int = 0  # json="WBytes"
    num_live: int = 0  # json="NumLive"
    live_derps: int = 0  # json="LiveDERPs"; number of active DERP connections
    live_peers: Dict[NodePublic, Dict[str, Any]] = field(default_factory=dict)  # json="LivePeers"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "LiveDERPs": "live_derps",
        "LivePeers": "live_peers",
        "NumLive": "num_live",
        "RBytes": "r_bytes",
        "WBytes": "w_bytes",
    }


# Notify is a communication from a backend (e.g. tailscaled) to a frontend
# (cmd/tailscale, iOS, macOS, Win Tasktray).
# In any given notification, any or all of these may be nil, meaning
# that they have not changed.
# They are JSON-encoded on the wire, despite the lack of struct tags.
# 
# API maturity: this type is not considered a stable API and is
# subject to change between releases.
@dataclass
class Notify(SerdeMixin):
    version: str = ""  # json="Version"; version number of IPN backend
    session_id: str = ""  # json="SessionID"
    err_message: Optional[str] = None  # json="ErrMessage"
    login_finished: Optional[Dict[str, Any]] = None  # json="LoginFinished"; non-nil when/if the login process succeeded
    state: Optional[State] = None  # json="State"; if non-nil, the new or current IPN state
    prefs: Optional[Dict[str, Any]] = None  # json="Prefs"; if non-nil && Valid, the new or current preferences
    self_change: Optional[Dict[str, Any]] = None  # json="SelfChange"
    initial_status: Optional[Dict[str, Any]] = None  # json="InitialStatus"
    net_map: Optional[Dict[str, Any]] = None  # json="NetMap"
    peer_changed_patch: List[Optional[Dict[str, Any]]] = field(default_factory=list)  # json="PeerChangedPatch"
    peers_changed: List[Optional[Dict[str, Any]]] = field(default_factory=list)  # json="PeersChanged"
    peers_removed: List[NodeID] = field(default_factory=list)  # json="PeersRemoved"
    user_profiles: Dict[UserID, Dict[str, Any]] = field(default_factory=dict)  # json="UserProfiles"
    peer_state: Dict[StableNodeID, PeerState] = field(default_factory=dict)  # json="PeerState"
    engine: Optional[EngineStatus] = None  # json="Engine"; if non-nil, the new or current wireguard stats
    browse_to_url: Optional[str] = None  # json="BrowseToURL"; if non-nil, UI should open a browser right now
    files_waiting: Optional[Dict[str, Any]] = None  # json="FilesWaiting"
    incoming_files: List[PartialFile] = field(default_factory=list)  # json="IncomingFiles"
    outgoing_files: List[Optional[OutgoingFile]] = field(default_factory=list)  # json="OutgoingFiles"
    local_tcp_port: Optional[int] = None  # json="LocalTCPPort"
    client_version: Optional[Dict[str, Any]] = None  # json="ClientVersion"
    drive_shares: Dict[str, Any] = field(default_factory=dict)  # json="DriveShares"
    health: Optional[State] = None  # json="Health"
    suggested_exit_node: Optional[StableNodeID] = None  # json="SuggestedExitNode"
    policy: Optional[Dict[str, Any]] = None  # json="Policy"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "BrowseToURL": "browse_to_url",
        "ClientVersion": "client_version",
        "DriveShares": "drive_shares",
        "Engine": "engine",
        "ErrMessage": "err_message",
        "FilesWaiting": "files_waiting",
        "Health": "health",
        "IncomingFiles": "incoming_files",
        "InitialStatus": "initial_status",
        "LocalTCPPort": "local_tcp_port",
        "LoginFinished": "login_finished",
        "NetMap": "net_map",
        "OutgoingFiles": "outgoing_files",
        "PeerChangedPatch": "peer_changed_patch",
        "PeerState": "peer_state",
        "PeersChanged": "peers_changed",
        "PeersRemoved": "peers_removed",
        "Policy": "policy",
        "Prefs": "prefs",
        "SelfChange": "self_change",
        "SessionID": "session_id",
        "State": "state",
        "SuggestedExitNode": "suggested_exit_node",
        "UserProfiles": "user_profiles",
        "Version": "version",
    }


# PeerState is the per-peer WireGuard session state delivered in
# [Notify.PeerState].
@dataclass
class PeerState(SerdeMixin):
    peer_wire_guard_state: PeerWireGuardState = None  # json="PeerWireGuardState"
    peer_wire_guard_state_at: datetime = None  # json="PeerWireGuardStateAt"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "PeerWireGuardState": "peer_wire_guard_state",
        "PeerWireGuardStateAt": "peer_wire_guard_state_at",
    }


# PartialFile represents an in-progress incoming file transfer.
@dataclass
class PartialFile(SerdeMixin):
    name: str = ""  # json="Name"; e.g. "foo.jpg"
    started: datetime = None  # json="Started"; time transfer started
    declared_size: int = 0  # json="DeclaredSize"; or -1 if unknown
    received: int = 0  # json="Received"; bytes copied thus far
    partial_path: str = ""  # json="PartialPath"
    final_path: str = ""  # json="FinalPath"
    done: bool = False  # json="Done"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "DeclaredSize": "declared_size",
        "Done": "done",
        "FinalPath": "final_path",
        "Name": "name",
        "PartialPath": "partial_path",
        "Received": "received",
        "Started": "started",
    }


# OutgoingFile represents an in-progress outgoing file transfer.
@dataclass
class OutgoingFile(SerdeMixin):
    id: str = ""  # json="ID"; unique identifier for this transfer (a type 4 UUID)
    peer_id: StableNodeID = StableNodeID("")  # json="PeerID"; identifier for the peer to which this is being transferred
    name: str = ""  # json="Name"; e.g. "foo.jpg"
    started: datetime = None  # json="Started"; time transfer started
    declared_size: int = 0  # json="DeclaredSize"; or -1 if unknown
    sent: int = 0  # json="Sent"; bytes copied thus far
    finished: bool = False  # json="Finished"; indicates whether or not the transfer finished
    succeeded: bool = False  # json="Succeeded"; for a finished transfer, indicates whether or not it was successful

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "DeclaredSize": "declared_size",
        "Finished": "finished",
        "ID": "id",
        "Name": "name",
        "PeerID": "peer_id",
        "Sent": "sent",
        "Started": "started",
        "Succeeded": "succeeded",
    }


@dataclass
class Options(SerdeMixin):
    frontend_log_id: str = ""  # json="FrontendLogID"
    update_prefs: Optional[Dict[str, Any]] = None  # json="UpdatePrefs"
    auth_key: str = ""  # json="AuthKey"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "AuthKey": "auth_key",
        "FrontendLogID": "frontend_log_id",
        "UpdatePrefs": "update_prefs",
    }


# StateKey is an opaque identifier for a set of LocalBackend state
# (preferences, private keys, etc.). It is also used as a key for
# the various LoginProfiles that the instance may be signed into.
# 
# Additionally, the StateKey can be debug setting name:
# 
# - "_debug_magicsock_until" with value being a unix timestamp stringified
# - "_debug_<component>_until" with value being a unix timestamp stringified
StateKey = NewType("StateKey", str)

