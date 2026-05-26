# Tailscale Local API

This library can be used to control and get information from Tailscaled's local socket API.

It is not a Tailscale SaaS API library.

## Usage

```python
from tailscale_cli import TailscaleCLI

# Auto-detect the daemon version and load matching models:
api = TailscaleCLI.connect()
status = api.status()   # returns a typed model if models exist

# Or pin to a specific model version explicitly:
api = TailscaleCLI.connect("v1.94.2")
status = api.status()   # → tailscale_cli.v1_94_2.ipnstate.Status
```
