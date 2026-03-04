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
