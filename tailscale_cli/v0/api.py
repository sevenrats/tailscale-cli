from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING, Union

import httpx

from tailscale_cli._util.error import TailscaleException
from tailscale_cli._util.sock import make_client

if TYPE_CHECKING:
    pass


class LocalAPI:
    """Handle to Tailscale's local API.

    The *models* parameter is a module (or any object) that exposes the
    model classes ``Status`` and ``PingResult``.  This is typically one of
    the auto-generated version packages, e.g.::

        from tailscale_cli.v1_82_0 import ipnstate
        api = LocalAPI(models=ipnstate)

    If *models* is not supplied, the API still works but returns raw dicts
    for structured responses.
    """

    _client: httpx.Client
    _socket_path: str
    _models: Any  # version-specific models module (has Status, PingResult, …)

    def __init__(
        self,
        *,
        socket_path: str = "/run/tailscale/tailscaled.sock",
        models: Any = None,
    ):
        """
        Creates a handle to Tailscale's local API, through the path to
        `tailscaled` UNIX socket.

        Args:
            socket_path: Path to the tailscaled UNIX socket.
            models: A module exposing model classes (Status, PingResult, …).
                    Typically an auto-generated version package.
        """
        self._client = make_client(socket_path)
        self._models = models
        self._socket_path = socket_path

    # -------------------------
    # internals
    # -------------------------

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        # All of these CLI-like actions live under /localapi/v0/...
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
    # public API
    # -------------------------

    def status(self) -> Any:
        """Show state of tailscaled and its connections.

        Returns a ``Status`` model instance if *models* was provided,
        otherwise the raw JSON dict.
        """
        resp = self._request("GET", "status")
        if self._models and hasattr(self._models, "Status"):
            return self._models.Status.loads(resp.content.decode())
        return resp.json()

    def ip(self) -> list[str]:
        # Show Tailscale IP addresses (convenience wrapper around status)
        st = self.status()
        return [str(ip) for ip in (st.tailscale_ips or [])]

    def ping(
        self,
        ip_or_host: str,
        *,
        ping_type: str = "disco",
        size: int = 0,
    ) -> Any:
        """
        Ping at the Tailscale layer.

        Returns a ``PingResult`` model instance if *models* was provided,
        otherwise the raw JSON dict.

        LocalAPI shape (as used by tailscale CLI) is:
          POST /localapi/v0/ping?ip=...&size=0&type=disco
        """
        resp = self._request(
            "POST",
            "ping",
            params={"ip": ip_or_host, "size": str(int(size)), "type": ping_type},
        )
        if self._models and hasattr(self._models, "PingResult"):
            return self._models.PingResult.loads(resp.content.decode())
        return resp.json()

    def whois(self, addr: str) -> Dict[str, Any]:
        """
        Look up the node/user associated with a Tailscale IP.
        Returns raw JSON (tailcfg.WhoIsResponse-like).
        """
        resp = self._request("GET", "whois", params={"addr": addr})
        return resp.json()

    def login(self) -> Any:
        """
        Kick off interactive login (populates AuthURL in status if needed).
        LocalAPI route: /localapi/v0/login-interactive
        """
        self._request("POST", "login-interactive")
        return self.status()

    def logout(self) -> None:
        """Disconnect from Tailscale and expire current node key."""
        self._request("POST", "logout")
        return None

    def up(self, *, prefs: Optional[Dict[str, Any]] = None) -> None:
        """
        Connect to Tailscale, logging in if needed.

        Implementation note: LocalAPI uses /localapi/v0/prefs for preference updates.
        At minimum we set WantRunning=true. You can pass additional prefs as a dict.
        """
        body: Dict[str, Any] = {"WantRunning": True}
        if prefs:
            body.update(prefs)
        self._request("POST", "prefs", json_body=body)
        return None

    def down(self) -> None:
        """Disconnect from Tailscale."""
        self._request("POST", "prefs", json_body={"WantRunning": False})
        return None

    def setpref(self, **prefs: Any) -> None:
        """
        Change specified preferences (thin wrapper over POST /localapi/v0/prefs).

        Example:
          api.setpref(AcceptRoutes=True, AdvertiseRoutes=["10.0.0.0/24"])
        """
        if not prefs:
            return None
        self._request("POST", "prefs", json_body=prefs)
        return None

    # The rest are CLI surface area; keep stubs until you decide which localapi
    # endpoints you want to bind.

    def switch(self):
        # Switches to a different Tailscale account
        raise NotImplementedError("not implemented")

    def configure(self):
        # [ALPHA] Configure the host to enable more Tailscale features
        raise NotImplementedError("not implemented")

    def netcheck(self):
        # Print an analysis of local network conditions
        raise NotImplementedError("not implemented")

    def dns(self):
        # Diagnose the internal DNS forwarder
        raise NotImplementedError("not implemented")

    def nc(self):
        # Connect to a port on a host, connected to stdin/stdout
        raise NotImplementedError("not implemented")

    def ssh(self):
        # SSH to a Tailscale machine
        raise NotImplementedError("not implemented")

    def funnel(self):
        # Serve content and local servers on the internet
        raise NotImplementedError("not implemented")

    def serve(self):
        # Serve content and local servers on your tailnet
        raise NotImplementedError("not implemented")

    def version(self) -> Dict[str, Any]:
        """Return the Tailscale daemon version information.

        Queries ``GET /localapi/v0/version`` and returns the JSON response
        which typically includes keys such as ``majorMinorPatch``, ``short``,
        ``long``, ``gitCommit``, and ``cap``.
        """
        resp = self._request("GET", "version")
        return resp.json()

    def web(self):
        # Run a web server for controlling Tailscale
        raise NotImplementedError("not implemented")

    def file(self):
        # Send or receive files
        raise NotImplementedError("not implemented")

    def bugreport(self):
        # Print a shareable identifier to help diagnose issues
        raise NotImplementedError("not implemented")

    def cert(self):
        # Get TLS certs
        raise NotImplementedError("not implemented")

    def lock(self):
        # Manage tailnet lock
        raise NotImplementedError("not implemented")

    def licenses(self):
        # Get open source license information
        raise NotImplementedError("not implemented")

    def exit_node(self):
        # Show machines configured as exit nodes
        raise NotImplementedError("not implemented")

    def update(self):
        # Update Tailscale to the latest/different version
        raise NotImplementedError("not implemented")

    def drive(self):
        # Share a directory with your tailnet
        raise NotImplementedError("not implemented")

    def completion(self):
        # Shell tab-completion scripts
        raise NotImplementedError("not implemented")
