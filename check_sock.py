#!/usr/bin/env python3
"""Quick check: is tailscaled listening on a UNIX socket?"""
import os, socket, sys, json

PATHS = [
    "/run/tailscale/tailscaled.sock",
    "/var/run/tailscale/tailscaled.sock",
    "/tmp/tailscaled.sock",
]

sock_path = sys.argv[1] if len(sys.argv) > 1 else None

if sock_path:
    paths = [sock_path]
else:
    paths = PATHS

for p in paths:
    exists = os.path.exists(p)
    if not exists:
        print(f"  {p}  MISSING")
        continue

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.settimeout(3)
        s.connect(p)
        # Send a minimal HTTP request to the local API
        req = (
            b"GET /localapi/v0/status?peers=false HTTP/1.0\r\n"
            b"Host: local-tailscaled.sock\r\n"
            b"\r\n"
        )
        s.sendall(req)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        text = data.decode(errors="replace")
        status_line = text.split("\r\n", 1)[0]

        if "200" in status_line:
            body = text.split("\r\n\r\n", 1)[-1]
            info = json.loads(body)
            ver = info.get("Version", "?")
            state = info.get("BackendState", "?")
            self_name = info.get("Self", {}).get("HostName", "?")
            print(f"  {p}  OK  tailscaled={ver}  state={state}  host={self_name}")
        else:
            print(f"  {p}  CONNECT_OK  but HTTP {status_line}")
    except socket.timeout:
        print(f"  {p}  EXISTS  but timed out (not responding)")
    except ConnectionRefusedError:
        print(f"  {p}  EXISTS  but connection refused (not listening)")
    except Exception as e:
        print(f"  {p}  EXISTS  but error: {e}")
    finally:
        s.close()
