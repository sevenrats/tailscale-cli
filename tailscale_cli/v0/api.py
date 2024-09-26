import requests

from tailscale_cli.v0.model import *
from tailscale_cli._util.sock import SockAdapter
from tailscale_cli._util.error import TailscaleException


class API_V0:

    """Handle to Tailscale's local API"""

    _client: requests.Session = requests.Session()
    _socket_path: str

    def __init__(self, *, socket_path: str = "/run/tailscale/tailscaled.sock"):
        """
        Creates a handle to Tailscale's local API, through the path to
        `tailscaled` UNIX socket.
        """

        self._client.mount("http://ts/", SockAdapter())
        self._socket_path = socket_path

    def up(self):
        #       Connect to Tailscale, logging in if needed
        raise NotImplementedError("not implemented")

    def down(self):
        #       Disconnect from Tailscale
        raise NotImplementedError("not implemented")

    def setpref(self):
        #        Change specified preferences
        raise NotImplementedError("not implemented")
    def login(self):
        #       Log in to a Tailscale account
        raise NotImplementedError("not implemented")
    def logout(self):
        #      Disconnect from Tailscale and expire current node key
        raise NotImplementedError("not implemented")
    def switch(self):
        #      Switches to a different Tailscale account
        raise NotImplementedError("not implemented")
    def configure(self):
        #   [ALPHA] Configure the host to enable more Tailscale features
        raise NotImplementedError("not implemented")
    def netcheck(self):
        #   Print an analysis of local network conditions
        raise NotImplementedError("not implemented")
    def ip(self):
        #          Show Tailscale IP addresses
        raise NotImplementedError("not implemented")
    def dns(self):
        #         Diagnose the internal DNS forwarder
        raise NotImplementedError("not implemented")
    def status(self):
        #      Show state of tailscaled and its connections
        response = self._client.get("http://ts/localapi/v0/status")

        if response.status_code != 200:
            raise TailscaleException.from_status_code(response.status_code, response.text)

        return Status.deserialize(response.content.decode())

    def ping(self):
        #        Ping a host at the Tailscale layer, see how it routed
        raise NotImplementedError("not implemented")
    def nc(self):
        #          Connect to a port on a host, connected to stdin/stdout
        raise NotImplementedError("not implemented")
    def ssh(self):
        #         SSH to a Tailscale machine
        raise NotImplementedError("not implemented")
    def funnel(self):
        #      Serve content and local servers on the internet
        raise NotImplementedError("not implemented")
    def serve(self):
        #       Serve content and local servers on your tailnet
        raise NotImplementedError("not implemented")
    def version(self):
        #     Print Tailscale version
        raise NotImplementedError("not implemented")
    def web(self):
        #         Run a web server for controlling Tailscale
        raise NotImplementedError("not implemented")
    def file(self):
        #        Send or receive files
        raise NotImplementedError("not implemented")
    def bugreport(self):
        #   Print a shareable identifier to help diagnose issues
        raise NotImplementedError("not implemented")
    def cert(self):
        #        Get TLS certs
        raise NotImplementedError("not implemented")
    def lock(self):
        #        Manage tailnet lock
        raise NotImplementedError("not implemented")
    def licenses(self):
        #    Get open source license information
        raise NotImplementedError("not implemented")
    def exit_node(self):
        #   Show machines on your tailnet configured as exit nodes
        raise NotImplementedError("not implemented")
    def update(self):
        #      Update Tailscale to the latest/different version
        raise NotImplementedError("not implemented")
    def whois(self):
        #       Show the machine and user associated with a Tailscale IP (v4 or v6)
        raise NotImplementedError("not implemented")
    def drive(self):
        #       Share a directory with your tailnet
        raise NotImplementedError("not implemented")
    def completion(self):
        #  Shell tab-completion scripts
        raise NotImplementedError("not implemented")
    
