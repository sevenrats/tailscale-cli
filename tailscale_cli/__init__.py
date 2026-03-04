"""
Control Tailscale's local API.
"""

from ._util.error import TailscaleException as TailscaleException
from ._util.localapi_base import LocalAPIBase as LocalAPIBase
from .api import TailscaleCLI as TailscaleCLI
