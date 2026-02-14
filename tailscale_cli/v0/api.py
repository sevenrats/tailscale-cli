from typing import Any, Dict, Optional, Union

import requests

from tailscale_cli._util.error import TailscaleException
from tailscale_cli._util.sock import SockAdapter
from tailscale_cli.v0.ipnstate import (
    PingResult,
    Status,
)


class API_V0:
    """Handle to Tailscale's local API"""

    _client: requests.Session = requests.Session()
    _socket_path: str

    def __init__(self, *, socket_path: str = "/run/tailscale/tailscaled.sock"):
        """
        Creates a handle to Tailscale's local API, through the path to
        `tailscaled` UNIX socket.
        """
        adapter = SockAdapter()
        self._client.mount("http://ts/", adapter)
        self._socket_path = socket_path

        # Best-effort: teach the adapter the socket path (different adapters do this differently)
        for attr in ("socket_path", "sock_path", "path"):
            if hasattr(adapter, attr):
                try:
                    setattr(adapter, attr, socket_path)
                except Exception:
                    pass
        if hasattr(adapter, "set_socket_path"):
            try:
                adapter.set_socket_path(socket_path)
            except Exception:
                pass

    # -------------------------
    # internals
    # -------------------------

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        # All of these CLI-like actions live under /localapi/v0/...
        if not path.startswith("localapi/v0/"):
            path = "localapi/v0/" + path
        return "http://ts/" + path

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
    ) -> requests.Response:
        hdrs: Dict[str, str] = {}
        if headers:
            hdrs.update(headers)

        # Best-effort: some SockAdapter implementations look for a header like this.
        # If yours doesn't, it will be ignored.
        hdrs.setdefault("X-TS-Socket-Path", self._socket_path)

        if json_body is not None:
            hdrs.setdefault("Content-Type", "application/json")

        resp = self._client.request(
            method=method.upper(),
            url=self._url(path),
            params=params,
            json=json_body,
            data=data,
            headers=hdrs,
            timeout=timeout,
        )

        if resp.status_code >= 400:
            raise TailscaleException.from_status_code(resp.status_code, resp.text)

        return resp

    # -------------------------
    # public API
    # -------------------------

    def status(self) -> Status:
        # Show state of tailscaled and its connections
        resp = self._request("GET", "status")
        return Status.loads(resp.content.decode())

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
    ) -> PingResult:
        """
        Ping at the Tailscale layer.

        LocalAPI shape (as used by tailscale CLI) is:
          POST /localapi/v0/ping?ip=...&size=0&type=disco
        """
        resp = self._request(
            "POST",
            "ping",
            params={"ip": ip_or_host, "size": str(int(size)), "type": ping_type},
        )
        return PingResult.deserialize(resp.content.decode())

    def whois(self, addr: str) -> Dict[str, Any]:
        """
        Look up the node/user associated with a Tailscale IP.
        Returns raw JSON (tailcfg.WhoIsResponse-like).
        """
        resp = self._request("GET", "whois", params={"addr": addr})
        return resp.json()

    def login(self) -> Status:
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

    def version(self):
        # Print Tailscale version
        raise NotImplementedError("not implemented")

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
