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

    def version(self) -> Dict[str, Any]:
        """Return the Tailscale daemon version information.

        Queries ``GET /localapi/v0/version`` and returns the JSON response
        which typically includes keys such as ``majorMinorPatch``, ``short``,
        ``long``, ``gitCommit``, and ``cap``.
        """
        resp = self._request("GET", "version")
        return resp.json()
