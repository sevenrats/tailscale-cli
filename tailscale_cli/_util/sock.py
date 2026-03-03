"""Helpers for building an httpx client that talks to tailscaled over a UNIX socket."""

from __future__ import annotations

import httpx


# Base URL used as a placeholder — httpx routes the actual traffic over UDS.
BASE_URL = "http://local-tailscaled.sock"


def make_client(socket_path: str) -> httpx.Client:
    """Return an :class:`httpx.Client` connected via the given UNIX socket."""
    transport = httpx.HTTPTransport(uds=socket_path)
    return httpx.Client(base_url=BASE_URL, transport=transport)
