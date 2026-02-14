import socket

from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
from urllib3.connection import HTTPConnection
from urllib3.connectionpool import HTTPConnectionPool

from tailscale_cli._util.error import TailscaleException

SOCK = "%2Frun%2Ftailscale%2Ftailscaled.sock"


class SockConnection(HTTPConnection):
    def __init__(self):
        super().__init__("local-tailscaled.sock")

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect("/run/tailscale/tailscaled.sock")
        except ConnectionError:
            raise TailscaleException.connection_error()


class SockConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super().__init__("local-tailscaled.sock")

    def _new_conn(self):
        return SockConnection()


class SockAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return SockConnectionPool()
