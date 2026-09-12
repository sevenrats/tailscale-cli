"""
Auto-generated from upstream Go source — DO NOT EDIT.

Source : https://github.com/tailscale/tailscale/blob/bbcd7d1fc2054b9189ebc1531acf74bd880ca0c8/ipn/prefs.go
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

ExitNodeExpression = NewType("ExitNodeExpression", str)  # ExitNodeExpression
ProfileID = NewType("ProfileID", str)  # ProfileID
StateKey = NewType("StateKey", str)  # StateKey
WindowsUserID = NewType("WindowsUserID", str)  # WindowsUserID
Addr = NewType("Addr", str)  # netip.Addr
AddrPort = NewType("AddrPort", str)  # netip.AddrPort
Prefix = NewType("Prefix", str)  # netip.Prefix
StableNodeID = NewType("StableNodeID", str)  # tailcfg.StableNodeID


# Prefs are the user modifiable settings of the Tailscale node agent.
# When you add a Pref to this struct, remember to add a corresponding
# field in MaskedPrefs, and check your field for equality in Prefs.Equals().
@dataclass
class Prefs(SerdeMixin):
    control_url: str = ""  # json="ControlURL"
    route_all: bool = False  # json="RouteAll"
    exit_node_id: StableNodeID = StableNodeID("")  # json="ExitNodeID"
    exit_node_ip: Addr = Addr("")  # json="ExitNodeIP"
    auto_exit_node: ExitNodeExpression = ExitNodeExpression("")  # json="AutoExitNode"
    internal_exit_node_prior: StableNodeID = StableNodeID("")  # json="InternalExitNodePrior"
    exit_node_allow_lan_access: bool = False  # json="ExitNodeAllowLANAccess"
    corp_dns: bool = False  # json="CorpDNS"
    run_ssh: bool = False  # json="RunSSH"
    run_web_client: bool = False  # json="RunWebClient"
    want_running: bool = False  # json="WantRunning"
    logged_out: bool = False  # json="LoggedOut"
    shields_up: bool = False  # json="ShieldsUp"
    advertise_tags: List[str] = field(default_factory=list)  # json="AdvertiseTags"
    hostname: str = ""  # json="Hostname"
    notepad_urls: bool = False  # json="NotepadURLs"
    force_daemon: bool = False  # json="ForceDaemon"
    egg: bool = False  # json="Egg"
    advertise_routes: List[Prefix] = field(default_factory=list)  # json="AdvertiseRoutes"
    advertise_services: List[str] = field(default_factory=list)  # json="AdvertiseServices"
    sync: Dict[str, Any] = field(default_factory=dict)  # json="Sync"
    no_snat: bool = False  # json="NoSNAT"
    no_stateful_filtering: Dict[str, Any] = field(default_factory=dict)  # json="NoStatefulFiltering"
    netfilter_mode: Dict[str, Any] = field(default_factory=dict)  # json="NetfilterMode"
    operator_user: str = ""  # json="OperatorUser"
    profile_name: str = ""  # json="ProfileName"
    auto_update: AutoUpdatePrefs = None  # json="AutoUpdate"
    app_connector: AppConnectorPrefs = None  # json="AppConnector"
    posture_checking: bool = False  # json="PostureChecking"
    netfilter_kind: str = ""  # json="NetfilterKind"
    remote_config: bool = False  # json="RemoteConfig"
    drive_shares: List[Optional[Dict[str, Any]]] = field(default_factory=list)  # json="DriveShares"
    relay_server_port: Optional[int] = None  # json="RelayServerPort"
    relay_server_static_endpoints: List[AddrPort] = field(default_factory=list)  # json="RelayServerStaticEndpoints"
    persist: Optional[Dict[str, Any]] = None  # json="Config"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "AdvertiseRoutes": "advertise_routes",
        "AdvertiseServices": "advertise_services",
        "AdvertiseTags": "advertise_tags",
        "AppConnector": "app_connector",
        "AutoExitNode": "auto_exit_node",
        "AutoUpdate": "auto_update",
        "Config": "persist",
        "ControlURL": "control_url",
        "CorpDNS": "corp_dns",
        "DriveShares": "drive_shares",
        "Egg": "egg",
        "ExitNodeAllowLANAccess": "exit_node_allow_lan_access",
        "ExitNodeID": "exit_node_id",
        "ExitNodeIP": "exit_node_ip",
        "ForceDaemon": "force_daemon",
        "Hostname": "hostname",
        "InternalExitNodePrior": "internal_exit_node_prior",
        "LoggedOut": "logged_out",
        "NetfilterKind": "netfilter_kind",
        "NetfilterMode": "netfilter_mode",
        "NoSNAT": "no_snat",
        "NoStatefulFiltering": "no_stateful_filtering",
        "NotepadURLs": "notepad_urls",
        "OperatorUser": "operator_user",
        "PostureChecking": "posture_checking",
        "ProfileName": "profile_name",
        "RelayServerPort": "relay_server_port",
        "RelayServerStaticEndpoints": "relay_server_static_endpoints",
        "RemoteConfig": "remote_config",
        "RouteAll": "route_all",
        "RunSSH": "run_ssh",
        "RunWebClient": "run_web_client",
        "ShieldsUp": "shields_up",
        "Sync": "sync",
        "WantRunning": "want_running",
    }


# AutoUpdatePrefs are the auto update settings for the node agent.
@dataclass
class AutoUpdatePrefs(SerdeMixin):
    check: bool = False  # json="Check"
    apply: Dict[str, Any] = field(default_factory=dict)  # json="Apply"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Apply": "apply",
        "Check": "check",
    }


# AppConnectorPrefs are the app connector settings for the node agent.
@dataclass
class AppConnectorPrefs(SerdeMixin):
    advertise: bool = False  # json="Advertise"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Advertise": "advertise",
    }


# MaskedPrefs is a Prefs with an associated bitmask of which fields are set.
# 
# Each FooSet field maps to a corresponding Foo field in Prefs. FooSet can be
# a struct, in which case inner fields of FooSet map to inner fields of Foo in
# Prefs (see AutoUpdateSet for example).
@dataclass
class MaskedPrefs(SerdeMixin):
    control_url_set: bool = False  # json="ControlURLSet"
    route_all_set: bool = False  # json="RouteAllSet"
    exit_node_id_set: bool = False  # json="ExitNodeIDSet"
    exit_node_ip_set: bool = False  # json="ExitNodeIPSet"
    auto_exit_node_set: bool = False  # json="AutoExitNodeSet"
    internal_exit_node_prior_set: bool = False  # json="InternalExitNodePriorSet"; Internal; can't be set by LocalAPI clients
    exit_node_allow_lan_access_set: bool = False  # json="ExitNodeAllowLANAccessSet"
    corp_dns_set: bool = False  # json="CorpDNSSet"
    run_ssh_set: bool = False  # json="RunSSHSet"
    run_web_client_set: bool = False  # json="RunWebClientSet"
    want_running_set: bool = False  # json="WantRunningSet"
    logged_out_set: bool = False  # json="LoggedOutSet"
    shields_up_set: bool = False  # json="ShieldsUpSet"
    advertise_tags_set: bool = False  # json="AdvertiseTagsSet"
    hostname_set: bool = False  # json="HostnameSet"
    notepad_urls_set: bool = False  # json="NotepadURLsSet"
    force_daemon_set: bool = False  # json="ForceDaemonSet"
    egg_set: bool = False  # json="EggSet"
    advertise_routes_set: bool = False  # json="AdvertiseRoutesSet"
    advertise_services_set: bool = False  # json="AdvertiseServicesSet"
    sync_set: bool = False  # json="SyncSet"
    no_snat_set: bool = False  # json="NoSNATSet"
    no_stateful_filtering_set: bool = False  # json="NoStatefulFilteringSet"
    netfilter_mode_set: bool = False  # json="NetfilterModeSet"
    operator_user_set: bool = False  # json="OperatorUserSet"
    profile_name_set: bool = False  # json="ProfileNameSet"
    auto_update_set: AutoUpdatePrefsMask = None  # json="AutoUpdateSet"
    app_connector_set: bool = False  # json="AppConnectorSet"
    posture_checking_set: bool = False  # json="PostureCheckingSet"
    netfilter_kind_set: bool = False  # json="NetfilterKindSet"
    remote_config_set: bool = False  # json="RemoteConfigSet"
    drive_shares_set: bool = False  # json="DriveSharesSet"
    relay_server_port_set: bool = False  # json="RelayServerPortSet"
    relay_server_static_endpoints_set: bool = False  # json="RelayServerStaticEndpointsSet"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "AdvertiseRoutesSet": "advertise_routes_set",
        "AdvertiseServicesSet": "advertise_services_set",
        "AdvertiseTagsSet": "advertise_tags_set",
        "AppConnectorSet": "app_connector_set",
        "AutoExitNodeSet": "auto_exit_node_set",
        "AutoUpdateSet": "auto_update_set",
        "ControlURLSet": "control_url_set",
        "CorpDNSSet": "corp_dns_set",
        "DriveSharesSet": "drive_shares_set",
        "EggSet": "egg_set",
        "ExitNodeAllowLANAccessSet": "exit_node_allow_lan_access_set",
        "ExitNodeIDSet": "exit_node_id_set",
        "ExitNodeIPSet": "exit_node_ip_set",
        "ForceDaemonSet": "force_daemon_set",
        "HostnameSet": "hostname_set",
        "InternalExitNodePriorSet": "internal_exit_node_prior_set",
        "LoggedOutSet": "logged_out_set",
        "NetfilterKindSet": "netfilter_kind_set",
        "NetfilterModeSet": "netfilter_mode_set",
        "NoSNATSet": "no_snat_set",
        "NoStatefulFilteringSet": "no_stateful_filtering_set",
        "NotepadURLsSet": "notepad_urls_set",
        "OperatorUserSet": "operator_user_set",
        "PostureCheckingSet": "posture_checking_set",
        "ProfileNameSet": "profile_name_set",
        "RelayServerPortSet": "relay_server_port_set",
        "RelayServerStaticEndpointsSet": "relay_server_static_endpoints_set",
        "RemoteConfigSet": "remote_config_set",
        "RouteAllSet": "route_all_set",
        "RunSSHSet": "run_ssh_set",
        "RunWebClientSet": "run_web_client_set",
        "ShieldsUpSet": "shields_up_set",
        "SyncSet": "sync_set",
        "WantRunningSet": "want_running_set",
    }


@dataclass
class AutoUpdatePrefsMask(SerdeMixin):
    check_set: bool = False  # json="CheckSet"
    apply_set: bool = False  # json="ApplySet"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "ApplySet": "apply_set",
        "CheckSet": "check_set",
    }


# ExitNodeLocalIPError is returned when the requested IP address for an exit
# node belongs to the local machine.
@dataclass
class ExitNodeLocalIPError(SerdeMixin):
    pass


# NetworkProfile is a subset of netmap.NetworkMap
# that should be saved with each user profile.
@dataclass
class NetworkProfile(SerdeMixin):
    magic_dns_name: str = ""  # json="MagicDNSName"
    domain_name: str = ""  # json="DomainName"
    display_name: str = ""  # json="DisplayName"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "DisplayName": "display_name",
        "DomainName": "domain_name",
        "MagicDNSName": "magic_dns_name",
    }


# LoginProfile represents a single login profile as managed
# by the ProfileManager.
@dataclass
class LoginProfile(SerdeMixin):
    id: ProfileID = ProfileID("")  # json="ID"
    name: str = ""  # json="Name"
    network_profile: NetworkProfile = None  # json="NetworkProfile"
    key: StateKey = StateKey("")  # json="Key"
    user_profile: Dict[str, Any] = field(default_factory=dict)  # json="UserProfile"
    node_id: StableNodeID = StableNodeID("")  # json="NodeID"
    local_user_id: WindowsUserID = WindowsUserID("")  # json="LocalUserID"
    control_url: str = ""  # json="ControlURL"
    created: datetime = None  # json="Created"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "ControlURL": "control_url",
        "Created": "created",
        "ID": "id",
        "Key": "key",
        "LocalUserID": "local_user_id",
        "Name": "name",
        "NetworkProfile": "network_profile",
        "NodeID": "node_id",
        "UserProfile": "user_profile",
    }


