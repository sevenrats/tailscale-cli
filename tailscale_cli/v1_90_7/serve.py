"""
Auto-generated from upstream Go source — DO NOT EDIT.

Source : https://github.com/tailscale/tailscale/blob/90d3cb3c9573958386061cccefbf8708e870220a/ipn/serve.go
Commit : 90d3cb3c9573958386061cccefbf8708e870220a
Generated: 2026-05-26T00:53:57Z
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, ClassVar, Dict, List, NewType, Optional

from tailscale_cli._util.serde import SerdeMixin

# --- External / opaque Go types ---

AddrPort = NewType("AddrPort", str)  # netip.AddrPort


# ServiceConfig contains the config information for a single service.
# it contains a bool to indicate if the service is in Tun mode (L3 forwarding).
# If the service is not in Tun mode, the service is configured by the L4 forwarding
# (TCP ports) and/or the L7 forwarding (http handlers) information.
@dataclass
class ServiceConfig(SerdeMixin):
    tcp: Dict[int, Optional[TCPPortHandler]] = field(default_factory=dict)  # json="TCP"
    web: Dict[HostPort, Optional[WebServerConfig]] = field(default_factory=dict)  # json="Web"
    tun: bool = False  # json="Tun"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "TCP": "tcp",
        "Tun": "tun",
        "Web": "web",
    }


# ServeConfig is the JSON type stored in the StateStore for
# StateKey "_serve/$PROFILE_ID" as returned by ServeConfigKey.
@dataclass
class ServeConfig(SerdeMixin):
    tcp: Dict[int, Optional[TCPPortHandler]] = field(default_factory=dict)  # json="TCP"
    web: Dict[HostPort, Optional[WebServerConfig]] = field(default_factory=dict)  # json="Web"
    services: Dict[Dict[str, Any], Optional[ServiceConfig]] = field(default_factory=dict)  # json="Services"
    allow_funnel: Dict[HostPort, bool] = field(default_factory=dict)  # json="AllowFunnel"
    foreground: Dict[str, Optional[Dict[str, Any]]] = field(default_factory=dict)  # json="Foreground"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "AllowFunnel": "allow_funnel",
        "Foreground": "foreground",
        "Services": "services",
        "TCP": "tcp",
        "Web": "web",
    }


# A FunnelConn wraps a net.Conn that is coming over a
# Funnel connection. It can be used to determine further
# information about the connection, like the source address
# and the target SNI name.
@dataclass
class FunnelConn(SerdeMixin):
    target: HostPort = None  # json="Target"
    src: AddrPort = AddrPort("")  # json="Src"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Src": "src",
        "Target": "target",
    }


# WebServerConfig describes a web server's configuration.
@dataclass
class WebServerConfig(SerdeMixin):
    handlers: Dict[str, Optional[HTTPHandler]] = field(default_factory=dict)  # json="Handlers"; mountPoint => handler

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Handlers": "handlers",
    }


# TCPPortHandler describes what to do when handling a TCP
# connection.
@dataclass
class TCPPortHandler(SerdeMixin):
    https: bool = False  # json="HTTPS"
    http: bool = False  # json="HTTP"
    tcp_forward: str = ""  # json="TCPForward"
    terminate_tls: str = ""  # json="TerminateTLS"

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "HTTP": "http",
        "HTTPS": "https",
        "TCPForward": "tcp_forward",
        "TerminateTLS": "terminate_tls",
    }


# HTTPHandler is either a path or a proxy to serve.
@dataclass
class HTTPHandler(SerdeMixin):
    path: str = ""  # json="Path"; absolute path to directory or file to serve
    proxy: str = ""  # json="Proxy"; http://localhost:3000/, localhost:3030, 3030
    text: str = ""  # json="Text"; plaintext to serve (primarily for testing)

    # JSON key name → Python field name
    __json_map__: ClassVar[Dict[str, str]] = {
        "Path": "path",
        "Proxy": "proxy",
        "Text": "text",
    }


# HostPort is an SNI name and port number, joined by a colon.
# There is no implicit port 443. It must contain a colon.
HostPort = NewType("HostPort", str)

