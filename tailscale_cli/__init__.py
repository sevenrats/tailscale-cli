"""
Control Tailscale's local API.
"""

from ._util.error import TailscaleException as TailscaleException
from .api import TailscaleCLI as TailscaleCLI
from .v0.api import LocalAPI as LocalAPI
