"""
Auto-generated LocalAPI client — DO NOT EDIT.

This module is produced by codegen from upstream Go source.
It exposes one method per LocalAPI endpoint, with the correct
HTTP method, query parameters, and (where known) typed returns.

Source : https://github.com/tailscale/tailscale/blob/3fb8edada1715925e592493ae77016952866a202/ipn/localapi/localapi.go
Commit : 3fb8edada1715925e592493ae77016952866a202
Generated: 2026-09-12T10:09:28Z
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tailscale_cli._util.localapi_base import LocalAPIBase

from . import ipnstate


# Route table extracted from upstream localapi.go
ENDPOINTS = [
    {"route": "profiles/", "methods": ["DELETE", "GET", "POST", "PUT"], "permission": "write", "params": []},
    {"route": "cert-domains", "methods": ["GET"], "permission": "read", "params": []},
    {"route": "check-prefs", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "check-so-mark-in-use", "methods": ["GET"], "permission": "read", "params": []},
    {"route": "derpmap", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "dns-config", "methods": ["GET"], "permission": "read", "params": []},
    {"route": "goroutines", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "login-interactive", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "logout", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "peer-by-id", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "ping", "methods": ["POST"], "permission": "none", "params": ["ip", "type", "size"]},
    {"route": "prefs", "methods": ["GET", "PATCH"], "permission": "read", "params": []},
    {"route": "reload-config", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "reset-auth", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "services", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "set-expiry-sooner", "methods": ["POST"], "permission": "write", "params": ["expiry"]},
    {"route": "shutdown", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "start", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "status", "methods": ["GET"], "permission": "read", "params": ["peers"]},
    {"route": "user-profile", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "whois", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "appc-route-info", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "check-ip-forwarding", "methods": ["GET"], "permission": "read", "params": []},
    {"route": "check-udp-gro-forwarding", "methods": ["GET"], "permission": "read", "params": []},
    {"route": "set-udp-gro-forwarding", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "upload-client-metrics", "methods": ["POST"], "permission": "none", "params": []},
    {"route": "update/check", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "suggest-exit-node", "methods": ["GET", "POST"], "permission": "none", "params": ["probe", "timeout"]},
    {"route": "set-use-exit-node-enabled", "methods": ["POST"], "permission": "write", "params": ["enabled"]},
    {"route": "set-dns", "methods": ["POST"], "permission": "write", "params": ["name", "value"]},
    {"route": "bugreport", "methods": ["POST"], "permission": "read", "params": ["note", "diagnose", "record"]},
    {"route": "pprof", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "watch-ipn-bus", "methods": ["GET"], "permission": "read", "params": ["mask"]},
    {"route": "dns-osconfig", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "dns-query", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "usermetrics", "methods": ["GET"], "permission": "none", "params": []},
    {"route": "query-feature", "methods": ["POST"], "permission": "read", "params": ["feature"]},
    {"route": "dial", "methods": ["POST"], "permission": "none", "params": []},
    {"route": "metrics", "methods": ["GET"], "permission": "write", "params": []},
    {"route": "disconnect-control", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "id-token", "methods": ["GET"], "permission": "write", "params": ["aud"]},
    {"route": "alpha-set-device-attrs", "methods": ["PATCH"], "permission": "write", "params": []},
    {"route": "handle-push-message", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "set-push-device-token", "methods": ["POST"], "permission": "write", "params": []},
    {"route": "set-gui-visible", "methods": ["POST"], "permission": "none", "params": []},
    {"route": "logtap", "methods": ["GET"], "permission": "write", "params": []},
]


class LocalAPI(LocalAPIBase):
    """Version-specific LocalAPI client.

    Auto-generated from ``localapi.go``.
    Commit: 3fb8edada171

    46 endpoints available.
    """

    def profiles(self, *, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """List or manage Tailscale account profiles.

        GET /localapi/v0/profiles/
        """
        resp = self._request("GET", "profiles/", timeout=timeout)
        return resp.json()

    def profiles_get(self, item_id: str, *, timeout: float = 30.0) -> Dict[str, Any]:
        """Get a single item from profiles/<id>."""
        import urllib.parse
        encoded = urllib.parse.quote(item_id, safe="")
        resp = self._request("GET", f"profiles/{encoded}", timeout=timeout)
        return resp.json()

    def profiles_switch(self, item_id: str, *, timeout: float = 30.0) -> None:
        """POST to profiles/<id> (e.g. switch profile)."""
        import urllib.parse
        encoded = urllib.parse.quote(item_id, safe="")
        self._request("POST", f"profiles/{encoded}", timeout=timeout)
        return None

    def profiles_delete(self, item_id: str, *, timeout: float = 30.0) -> None:
        """DELETE profiles/<id>."""
        import urllib.parse
        encoded = urllib.parse.quote(item_id, safe="")
        self._request("DELETE", f"profiles/{encoded}", timeout=timeout)
        return None

    def cert_domains(self, timeout: float = 30.0) -> Dict[str, Any]:
        """GET /localapi/v0/cert-domains

        GET /localapi/v0/cert-domains
        Requires ``read`` permission.
        """
        resp = self._request("GET", "cert-domains", timeout=timeout)
        return resp.json()

    def check_prefs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Validate a prefs change without applying it.

        POST /localapi/v0/check-prefs
        Requires ``write`` permission.
        """
        resp = self._request("POST", "check-prefs", json_body=json_body, timeout=timeout)
        return resp.json()

    def check_so_mark_in_use(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Check if the SO_MARK value is in use.

        GET /localapi/v0/check-so-mark-in-use
        Requires ``read`` permission.
        """
        resp = self._request("GET", "check-so-mark-in-use", timeout=timeout)
        return resp.json()

    def derpmap(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Return the current DERP map.

        GET /localapi/v0/derpmap
        """
        resp = self._request("GET", "derpmap", timeout=timeout)
        return resp.json()

    def dns_config(self, timeout: float = 30.0) -> Dict[str, Any]:
        """GET /localapi/v0/dns-config

        GET /localapi/v0/dns-config
        Requires ``read`` permission.
        """
        resp = self._request("GET", "dns-config", timeout=timeout)
        return resp.json()

    def goroutines(self, timeout: float = 30.0) -> str:
        """Return a goroutine dump from tailscaled.

        GET /localapi/v0/goroutines
        Requires ``write`` permission.
        """
        resp = self._request("GET", "goroutines", timeout=timeout)
        return resp.text

    def login_interactive(self, timeout: float = 30.0) -> None:
        """Start an interactive (browser-based) login flow.

        POST /localapi/v0/login-interactive
        Requires ``write`` permission.
        """
        resp = self._request("POST", "login-interactive", timeout=timeout)
        return None

    def logout(self, timeout: float = 30.0) -> None:
        """Disconnect from Tailscale and expire current node key.

        POST /localapi/v0/logout
        Requires ``write`` permission.
        """
        resp = self._request("POST", "logout", timeout=timeout)
        return None

    def peer_by_id(self, timeout: float = 30.0) -> Dict[str, Any]:
        """GET /localapi/v0/peer-by-id

        GET /localapi/v0/peer-by-id
        """
        resp = self._request("GET", "peer-by-id", timeout=timeout)
        return resp.json()

    def ping(self, ip_or_host: str, *, ping_type: str = "disco", size: int = 0, timeout: float = 30.0) -> ipnstate.PingResult:
        """Ping a Tailscale node at the Tailscale layer.

        POST /localapi/v0/ping
        """
        params: Dict[str, str] = {}
        params["ip"] = ip_or_host
        if ping_type is not None:
            params["type"] = str(ping_type)
        if size is not None:
            params["size"] = str(size)
        resp = self._request("POST", "ping", params=params, timeout=timeout)
        return ipnstate.PingResult.loads(resp.content.decode())

    def prefs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Get or update daemon preferences.

        GET /localapi/v0/prefs
        Requires ``read`` permission.
        """
        resp = self._request("GET", "prefs", json_body=json_body, timeout=timeout)
        return resp.json()

    def reload_config(self, timeout: float = 30.0) -> None:
        """Reload configuration from disk.

        POST /localapi/v0/reload-config
        Requires ``write`` permission.
        """
        resp = self._request("POST", "reload-config", timeout=timeout)
        return None

    def reset_auth(self, timeout: float = 30.0) -> None:
        """Reset authentication state, forcing re-login.

        POST /localapi/v0/reset-auth
        Requires ``write`` permission.
        """
        resp = self._request("POST", "reset-auth", timeout=timeout)
        return None

    def services(self, timeout: float = 30.0) -> Dict[str, Any]:
        """GET /localapi/v0/services

        GET /localapi/v0/services
        """
        resp = self._request("GET", "services", timeout=timeout)
        return resp.json()

    def set_expiry_sooner(self, *, expiry: Optional[str] = None, timeout: float = 30.0) -> None:
        """Set the key expiry to a sooner time.

        POST /localapi/v0/set-expiry-sooner
        Requires ``write`` permission.
        """
        params: Dict[str, str] = {}
        if expiry is not None:
            params["expiry"] = expiry
        resp = self._request("POST", "set-expiry-sooner", params=params, timeout=timeout)
        return None

    def shutdown(self) -> None:
        """Shut down the tailscaled daemon.

        This endpoint uses long-lived streaming and is not
        supported through the standard request/response flow.
        """
        raise NotImplementedError("shutdown is a streaming endpoint")

    def start(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Start the Tailscale backend with the given options.

        POST /localapi/v0/start
        Requires ``write`` permission.
        """
        resp = self._request("POST", "start", json_body=json_body, timeout=timeout)
        return None

    def status(self, *, peers: Optional[str] = None, timeout: float = 30.0) -> ipnstate.Status:
        """Show state of tailscaled and its connections.

        GET /localapi/v0/status
        Requires ``read`` permission.
        """
        params: Dict[str, str] = {}
        if peers is not None:
            params["peers"] = peers
        resp = self._request("GET", "status", params=params, timeout=timeout)
        return ipnstate.Status.loads(resp.content.decode())

    def user_profile(self, timeout: float = 30.0) -> Dict[str, Any]:
        """GET /localapi/v0/user-profile

        GET /localapi/v0/user-profile
        """
        resp = self._request("GET", "user-profile", timeout=timeout)
        return resp.json()

    def whois(self, addr: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Look up the node/user associated with a Tailscale IP.

        GET /localapi/v0/whois
        """
        params: Dict[str, str] = {}
        params["addr"] = addr
        resp = self._request("GET", "whois", params=params, timeout=timeout)
        return resp.json()

    def appc_route_info(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Get app connector route information.

        GET /localapi/v0/appc-route-info
        """
        resp = self._request("GET", "appc-route-info", timeout=timeout)
        return resp.json()

    def check_ip_forwarding(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Check whether IP forwarding is enabled on this host.

        GET /localapi/v0/check-ip-forwarding
        Requires ``read`` permission.
        """
        resp = self._request("GET", "check-ip-forwarding", timeout=timeout)
        return resp.json()

    def check_udp_gro_forwarding(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Check whether UDP GRO forwarding is supported.

        GET /localapi/v0/check-udp-gro-forwarding
        Requires ``read`` permission.
        """
        resp = self._request("GET", "check-udp-gro-forwarding", timeout=timeout)
        return resp.json()

    def set_udp_gro_forwarding(self, timeout: float = 30.0) -> None:
        """Enable or disable UDP GRO forwarding.

        GET /localapi/v0/set-udp-gro-forwarding
        Requires ``write`` permission.
        """
        resp = self._request("GET", "set-udp-gro-forwarding", timeout=timeout)
        return None

    def upload_client_metrics(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Upload client metrics to the control server.

        POST /localapi/v0/upload-client-metrics
        """
        resp = self._request("POST", "upload-client-metrics", json_body=json_body, timeout=timeout)
        return None

    def update_check(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Check for available Tailscale updates.

        GET /localapi/v0/update/check
        """
        resp = self._request("GET", "update/check", timeout=timeout)
        return resp.json()

    def suggest_exit_node(self, *, probe: Optional[str] = None, timeout: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Suggest an exit node based on current conditions.

        GET /localapi/v0/suggest-exit-node
        """
        params: Dict[str, str] = {}
        if probe is not None:
            params["probe"] = probe
        if timeout is not None:
            params["timeout"] = timeout
        resp = self._request("GET", "suggest-exit-node", params=params, timeout=timeout)
        return resp.json()

    def set_use_exit_node_enabled(self, *, enabled: Optional[str] = None, timeout: float = 30.0) -> None:
        """Enable or disable using the configured exit node.

        POST /localapi/v0/set-use-exit-node-enabled
        Requires ``write`` permission.
        """
        params: Dict[str, str] = {}
        if enabled is not None:
            params["enabled"] = enabled
        resp = self._request("POST", "set-use-exit-node-enabled", params=params, timeout=timeout)
        return None

    def set_dns(self, *, name: Optional[str] = None, value: Optional[str] = None, timeout: float = 30.0) -> None:
        """Set a DNS record for an ACME challenge.

        POST /localapi/v0/set-dns
        Requires ``write`` permission.
        """
        params: Dict[str, str] = {}
        if name is not None:
            params["name"] = name
        if value is not None:
            params["value"] = value
        resp = self._request("POST", "set-dns", params=params, timeout=timeout)
        return None

    def bugreport(self, *, note: Optional[str] = None, diagnose: Optional[str] = None, record: Optional[str] = None, timeout: float = 30.0) -> str:
        """Generate a bug report identifier.

        POST /localapi/v0/bugreport
        Requires ``read`` permission.
        """
        params: Dict[str, str] = {}
        if note is not None:
            params["note"] = note
        if diagnose is not None:
            params["diagnose"] = diagnose
        if record is not None:
            params["record"] = record
        resp = self._request("POST", "bugreport", params=params, timeout=timeout)
        return resp.text

    def pprof(self) -> None:
        """Streaming: pprof

        This endpoint uses long-lived streaming and is not
        supported through the standard request/response flow.
        """
        raise NotImplementedError("pprof is a streaming endpoint")

    def watch_ipn_bus(self) -> None:
        """Streaming: watch-ipn-bus

        This endpoint uses long-lived streaming and is not
        supported through the standard request/response flow.
        """
        raise NotImplementedError("watch-ipn-bus is a streaming endpoint")

    def dns_osconfig(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Return the OS DNS configuration.

        GET /localapi/v0/dns-osconfig
        Requires ``write`` permission.
        """
        resp = self._request("GET", "dns-osconfig", timeout=timeout)
        return resp.json()

    def dns_query(self, timeout: float = 30.0) -> Dict[str, Any]:
        """Perform a DNS query through the Tailscale DNS forwarder.

        GET /localapi/v0/dns-query
        Requires ``write`` permission.
        """
        resp = self._request("GET", "dns-query", timeout=timeout)
        return resp.json()

    def usermetrics(self, timeout: float = 30.0) -> None:
        """Upload user-facing metrics.

        GET /localapi/v0/usermetrics
        """
        resp = self._request("GET", "usermetrics", timeout=timeout)
        return None

    def query_feature(self, *, feature: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Query whether a feature is available.

        POST /localapi/v0/query-feature
        Requires ``read`` permission.
        """
        params: Dict[str, str] = {}
        if feature is not None:
            params["feature"] = feature
        resp = self._request("POST", "query-feature", params=params, timeout=timeout)
        return resp.json()

    def dial(self) -> None:
        """Streaming: dial

        This endpoint uses long-lived streaming and is not
        supported through the standard request/response flow.
        """
        raise NotImplementedError("dial is a streaming endpoint")

    def metrics(self, timeout: float = 30.0) -> str:
        """Return Prometheus-style metrics from tailscaled.

        GET /localapi/v0/metrics
        Requires ``write`` permission.
        """
        resp = self._request("GET", "metrics", timeout=timeout)
        return resp.text

    def disconnect_control(self, timeout: float = 30.0) -> None:
        """Disconnect from the control server (debug).

        POST /localapi/v0/disconnect-control
        Requires ``write`` permission.
        """
        resp = self._request("POST", "disconnect-control", timeout=timeout)
        return None

    def id_token(self, aud: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Request an OIDC ID token for the given audience.

        GET /localapi/v0/id-token
        Requires ``write`` permission.
        """
        params: Dict[str, str] = {}
        params["aud"] = aud
        resp = self._request("GET", "id-token", params=params, timeout=timeout)
        return resp.json()

    def set_device_attrs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Set device attributes (alpha/experimental).

        PATCH /localapi/v0/alpha-set-device-attrs
        Requires ``write`` permission.
        """
        resp = self._request("PATCH", "alpha-set-device-attrs", json_body=json_body, timeout=timeout)
        return None

    def handle_push_message(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Handle an incoming push notification message.

        POST /localapi/v0/handle-push-message
        Requires ``write`` permission.
        """
        resp = self._request("POST", "handle-push-message", json_body=json_body, timeout=timeout)
        return None

    def set_push_device_token(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Register a push notification device token.

        POST /localapi/v0/set-push-device-token
        Requires ``write`` permission.
        """
        resp = self._request("POST", "set-push-device-token", json_body=json_body, timeout=timeout)
        return None

    def set_gui_visible(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Tell tailscaled whether a GUI is visible.

        POST /localapi/v0/set-gui-visible
        """
        resp = self._request("POST", "set-gui-visible", json_body=json_body, timeout=timeout)
        return None

    def logtap(self) -> None:
        """Streaming: logtap

        This endpoint uses long-lived streaming and is not
        supported through the standard request/response flow.
        """
        raise NotImplementedError("logtap is a streaming endpoint")

