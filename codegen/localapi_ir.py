"""
Intermediate representation for the parsed LocalAPI surface.

The localapi parser emits these dataclasses; the localapi generator
consumes them to produce a versioned ``localapi.py`` module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class APIQueryParam:
    """A query parameter extracted from ``r.FormValue`` / ``r.URL.Query().Get``."""

    name: str  # Go-side name (e.g. "ip", "type", "addr")
    go_type: str = "string"  # inferred type hint (string by default)


@dataclass
class APIEndpoint:
    """One route in the local API."""

    route: str  # e.g. "status", "ping", "profiles/"
    handler_name: str  # e.g. "serveStatus", "servePing"
    http_methods: List[str] = field(default_factory=list)  # e.g. ["GET"]
    permission: str = "none"  # "read", "write", "cert", or "none"
    is_prefix: bool = False  # True if route ends with '/'  (prefix match)
    query_params: List[APIQueryParam] = field(default_factory=list)
    has_request_body: bool = False  # json.NewDecoder(r.Body).Decode(…)
    has_json_response: bool = False  # json.NewEncoder(w).Encode(…) or json.Marshal(…)
    is_streaming: bool = False  # long-lived connections (watch-ipn-bus, logtap, dial)
    comment: str = ""
    # Registration type: "static" (from handler map) or "dynamic" (from Register/init)
    registration: str = "static"


@dataclass
class LocalAPIFile:
    """The parsed local API surface for a single Tailscale version."""

    endpoints: List[APIEndpoint] = field(default_factory=list)
