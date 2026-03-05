"""Base transport for the Tailscale local API.

This module provides :class:`LocalAPIBase`, the low-level HTTP transport
that communicates with the ``tailscaled`` daemon over its UNIX-domain socket.
The versioned, auto-generated ``LocalAPI`` classes inherit from this.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import httpx

from tailscale_cli._util.error import TailscaleException
from tailscale_cli._util.sock import make_client


class LocalAPIBase:
    """Reusable HTTP transport for Tailscale's local API.

    Subclasses (the generated ``LocalAPI`` per version) add typed
    endpoint methods on top of this base.
    """

    _client: httpx.Client
    _socket_path: str

    def __init__(
        self,
        *,
        socket_path: str = "/run/tailscale/tailscaled.sock",
    ):
        """
        Create a handle to Tailscale's local API.

        Args:
            socket_path: Path to the tailscaled UNIX socket.
        """
        self._client = make_client(socket_path)
        self._socket_path = socket_path

    # -------------------------
    # internals
    # -------------------------

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        if not path.startswith("localapi/v0/"):
            path = "localapi/v0/" + path
        return "/" + path

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        hdrs: Dict[str, str] = {}
        if headers:
            hdrs.update(headers)

        if json_body is not None:
            hdrs.setdefault("Content-Type", "application/json")

        resp = self._client.request(
            method=method.upper(),
            url=self._url(path),
            params=params,
            json=json_body,
            content=data,
            headers=hdrs,
            timeout=timeout,
        )

        if resp.status_code >= 400:
            raise TailscaleException.from_status_code(resp.status_code, resp.text)

        return resp

    # -------------------------
    # convenience (always available regardless of version)
    # -------------------------

    def login(
        self,
        *,
        auth_key: Optional[str] = None,
        control_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Log in to Tailscale.

        When *auth_key* is supplied the daemon authenticates headlessly
        using that key (``POST /localapi/v0/start`` with an ``AuthKey``
        body).  Without an auth key the daemon starts an interactive
        browser-based login flow (``POST /localapi/v0/login-interactive``).

        Use *control_url* to point the daemon at a custom control server
        (e.g. Headscale) before logging in.

        Args:
            auth_key:    A Tailscale auth key (``tskey-…``).  If provided
                         the login is non-interactive.
            control_url: Optional control-plane URL.  When set together
                         with *auth_key* it is sent as ``UpdatePrefs``
                         inside the ``start`` body.  When set without an
                         auth key the prefs are patched first via
                         ``PATCH /localapi/v0/prefs``.
            timeout:     HTTP request timeout in seconds.

        Example::

            # Headless auth-key login
            api.login(auth_key="tskey-auth-abc123")

            # Interactive browser login
            api.login()

            # Login to a Headscale instance with an auth key
            api.login(
                auth_key="tskey-auth-abc123",
                control_url="https://headscale.example.com",
            )
        """
        if auth_key is not None:
            body: Dict[str, Any] = {"AuthKey": auth_key}
            if control_url is not None:
                body["UpdatePrefs"] = {"ControlURL": control_url}
            self._request("POST", "start", json_body=body, timeout=timeout)
        else:
            if control_url is not None:
                self._request(
                    "PATCH",
                    "prefs",
                    json_body={
                        "ControlURL": control_url,
                        "ControlURLSet": True,
                    },
                    timeout=timeout,
                )
            self._request("POST", "login-interactive", timeout=timeout)

    def logout(self, *, timeout: float = 30.0) -> None:
        """Log out of Tailscale.

        Expires the current node key and disconnects from the network.

        POST /localapi/v0/logout
        """
        self._request("POST", "logout", timeout=timeout)

    # ------------------------------------------------------------------
    # Stubs for endpoints present in every generated version.
    #
    # These raise ``NotImplementedError`` at the base level so that
    # callers always get IDE autocomplete / type-checking.  The
    # generated ``LocalAPI`` subclasses override every one of these
    # with proper implementations.
    # ------------------------------------------------------------------

    def profiles(self, *, timeout: float = 30.0) -> Any:
        """List or manage Tailscale account profiles."""
        raise NotImplementedError("use a versioned LocalAPI")

    def profiles_get(self, item_id: str, *, timeout: float = 30.0) -> Any:
        """Get a single profile by ID."""
        raise NotImplementedError("use a versioned LocalAPI")

    def profiles_switch(self, item_id: str, *, timeout: float = 30.0) -> None:
        """Switch to a profile."""
        raise NotImplementedError("use a versioned LocalAPI")

    def profiles_delete(self, item_id: str, *, timeout: float = 30.0) -> None:
        """Delete a profile."""
        raise NotImplementedError("use a versioned LocalAPI")

    def check_prefs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Any:
        """Validate a prefs change without applying it."""
        raise NotImplementedError("use a versioned LocalAPI")

    def derpmap(self, timeout: float = 30.0) -> Any:
        """Return the current DERP map."""
        raise NotImplementedError("use a versioned LocalAPI")

    def goroutines(self, timeout: float = 30.0) -> str:
        """Return a goroutine dump from tailscaled."""
        raise NotImplementedError("use a versioned LocalAPI")

    def login_interactive(self, timeout: float = 30.0) -> None:
        """Start an interactive (browser-based) login flow."""
        raise NotImplementedError("use a versioned LocalAPI")

    def ping(self, ip_or_host: str, *, ping_type: str = "disco", size: int = 0, timeout: float = 30.0) -> Any:
        """Ping a Tailscale node at the Tailscale layer."""
        raise NotImplementedError("use a versioned LocalAPI")

    def prefs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Any:
        """Get or update daemon preferences."""
        raise NotImplementedError("use a versioned LocalAPI")

    def reload_config(self, timeout: float = 30.0) -> None:
        """Reload configuration from disk."""
        raise NotImplementedError("use a versioned LocalAPI")

    def reset_auth(self, timeout: float = 30.0) -> None:
        """Reset authentication state, forcing re-login."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_expiry_sooner(self, *, expiry: Optional[str] = None, timeout: float = 30.0) -> None:
        """Set the key expiry to a sooner time."""
        raise NotImplementedError("use a versioned LocalAPI")

    def shutdown(self) -> None:
        """Shut down the tailscaled daemon."""
        raise NotImplementedError("use a versioned LocalAPI")

    def start(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Start the Tailscale backend with the given options."""
        raise NotImplementedError("use a versioned LocalAPI")

    def status(self, *, peers: Optional[str] = None, timeout: float = 30.0) -> Any:
        """Show state of tailscaled and its connections."""
        raise NotImplementedError("use a versioned LocalAPI")

    def whois(self, addr: str, timeout: float = 30.0) -> Any:
        """Look up the node/user associated with a Tailscale IP."""
        raise NotImplementedError("use a versioned LocalAPI")

    def appc_route_info(self, timeout: float = 30.0) -> Any:
        """Get app connector route information."""
        raise NotImplementedError("use a versioned LocalAPI")

    def check_ip_forwarding(self, timeout: float = 30.0) -> Any:
        """Check whether IP forwarding is enabled on this host."""
        raise NotImplementedError("use a versioned LocalAPI")

    def check_udp_gro_forwarding(self, timeout: float = 30.0) -> Any:
        """Check whether UDP GRO forwarding is supported."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_udp_gro_forwarding(self, timeout: float = 30.0) -> None:
        """Enable or disable UDP GRO forwarding."""
        raise NotImplementedError("use a versioned LocalAPI")

    def check_reverse_path_filtering(self, timeout: float = 30.0) -> Any:
        """Check reverse-path filtering status."""
        raise NotImplementedError("use a versioned LocalAPI")

    def upload_client_metrics(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Upload client metrics to the control server."""
        raise NotImplementedError("use a versioned LocalAPI")

    def update_check(self, timeout: float = 30.0) -> Any:
        """Check for available Tailscale updates."""
        raise NotImplementedError("use a versioned LocalAPI")

    def suggest_exit_node(self, timeout: float = 30.0) -> Any:
        """Suggest an exit node based on current conditions."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_use_exit_node_enabled(self, *, enabled: Optional[str] = None, timeout: float = 30.0) -> None:
        """Enable or disable using the configured exit node."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_dns(self, *, name: Optional[str] = None, value: Optional[str] = None, timeout: float = 30.0) -> None:
        """Set a DNS record for an ACME challenge."""
        raise NotImplementedError("use a versioned LocalAPI")

    def bugreport(self, *, note: Optional[str] = None, diagnose: Optional[str] = None, record: Optional[str] = None, timeout: float = 30.0) -> str:
        """Generate a bug report identifier."""
        raise NotImplementedError("use a versioned LocalAPI")

    def pprof(self) -> None:
        """Streaming: pprof."""
        raise NotImplementedError("use a versioned LocalAPI")

    def watch_ipn_bus(self) -> None:
        """Streaming: watch-ipn-bus."""
        raise NotImplementedError("use a versioned LocalAPI")

    def dns_osconfig(self, timeout: float = 30.0) -> Any:
        """Return the OS DNS configuration."""
        raise NotImplementedError("use a versioned LocalAPI")

    def dns_query(self, timeout: float = 30.0) -> Any:
        """Perform a DNS query through the Tailscale DNS forwarder."""
        raise NotImplementedError("use a versioned LocalAPI")

    def usermetrics(self, timeout: float = 30.0) -> None:
        """Upload user-facing metrics."""
        raise NotImplementedError("use a versioned LocalAPI")

    def query_feature(self, *, feature: Optional[str] = None, timeout: float = 30.0) -> Any:
        """Query whether a feature is available."""
        raise NotImplementedError("use a versioned LocalAPI")

    def dial(self) -> None:
        """Streaming: dial."""
        raise NotImplementedError("use a versioned LocalAPI")

    def metrics(self, timeout: float = 30.0) -> str:
        """Return Prometheus-style metrics from tailscaled."""
        raise NotImplementedError("use a versioned LocalAPI")

    def disconnect_control(self, timeout: float = 30.0) -> None:
        """Disconnect from the control server (debug)."""
        raise NotImplementedError("use a versioned LocalAPI")

    def id_token(self, aud: str, timeout: float = 30.0) -> Any:
        """Request an OIDC ID token for the given audience."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_device_attrs(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Set device attributes (alpha/experimental)."""
        raise NotImplementedError("use a versioned LocalAPI")

    def handle_push_message(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Handle an incoming push notification message."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_push_device_token(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Register a push notification device token."""
        raise NotImplementedError("use a versioned LocalAPI")

    def set_gui_visible(self, *, json_body: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> None:
        """Tell tailscaled whether a GUI is visible."""
        raise NotImplementedError("use a versioned LocalAPI")

    def logtap(self) -> None:
        """Streaming: logtap."""
        raise NotImplementedError("use a versioned LocalAPI")

    def daemon_version(self) -> Optional[str]:
        """Return the running ``tailscaled`` version string.

        The daemon sets a ``Tailscale-Version`` header on every HTTP
        response (see ``localapi.go``'s ``ServeHTTP``).  We issue a
        lightweight ``GET /localapi/v0/status?peers=false`` and read
        that header — the same approach the official Go CLI uses.

        Returns the version string (e.g. ``"1.94.2"``) or ``None``
        if the header is missing.
        """
        resp = self._request("GET", "status", params={"peers": "false"})
        return resp.headers.get("Tailscale-Version")
