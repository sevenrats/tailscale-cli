"""
Generate a versioned ``localapi.py`` from the parsed API surface IR.

Produces a Python class that inherits from ``LocalAPIBase`` and exposes
one method per endpoint, with:
- Correct HTTP method
- Query parameters as keyword arguments
- Typed return values for well-known endpoints (via model imports)
- Raw ``Dict[str, Any]`` for unknown endpoints
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from .localapi_ir import APIEndpoint, APIQueryParam, LocalAPIFile
from .type_map import go_name_to_snake


# ---------------------------------------------------------------------------
# Curated endpoint metadata
#
# The parser extracts routes, HTTP methods, permissions, and query params
# automatically.  But mapping Go function internals to typed Python
# return values requires semantic knowledge.  This dict supplies that
# for well-known endpoints.  Endpoints not listed here get generic
# Dict[str, Any] return types and auto-generated signatures.
# ---------------------------------------------------------------------------

# py_name: Python method name override (otherwise derived from route)
# response_type: Python return annotation (as a string)
# response_model: module.Class for deserialization (None → .json())
# positional_params: list of (py_name, query_key, py_type, default|REQUIRED)
# doc: docstring override
_REQUIRED = object()


class _EP:
    """Descriptor for a curated endpoint."""
    __slots__ = (
        "py_name", "response_type", "response_model",
        "positional_params", "doc",
    )

    def __init__(
        self,
        py_name: str = "",
        response_type: str = "Dict[str, Any]",
        response_model: str = "",
        positional_params: Optional[List[Tuple[str, str, str, Any]]] = None,
        doc: str = "",
    ):
        self.py_name = py_name
        self.response_type = response_type
        self.response_model = response_model
        self.positional_params = positional_params or []
        self.doc = doc


CURATED: Dict[str, _EP] = {
    # ---- Core status / connectivity ----
    "status": _EP(
        py_name="status",
        response_type="ipnstate.Status",
        response_model="ipnstate.Status",
        doc="Show state of tailscaled and its connections.",
    ),
    "ping": _EP(
        py_name="ping",
        response_type="ipnstate.PingResult",
        response_model="ipnstate.PingResult",
        positional_params=[
            ("ip_or_host", "ip", "str", _REQUIRED),
            ("ping_type", "type", "str", '"disco"'),
            ("size", "size", "int", "0"),
        ],
        doc="Ping a Tailscale node at the Tailscale layer.",
    ),
    "whois": _EP(
        py_name="whois",
        response_type="Dict[str, Any]",
        doc="Look up the node/user associated with a Tailscale IP.",
        positional_params=[
            ("addr", "addr", "str", _REQUIRED),
        ],
    ),

    # ---- Prefs / config ----
    "prefs": _EP(
        py_name="prefs",
        response_type="Dict[str, Any]",
        doc="Get or update daemon preferences.",
    ),
    "check-prefs": _EP(
        py_name="check_prefs",
        response_type="Dict[str, Any]",
        doc="Validate a prefs change without applying it.",
    ),

    # ---- Lifecycle ----
    "login-interactive": _EP(
        py_name="login_interactive",
        response_type="None",
        doc="Start an interactive (browser-based) login flow.",
    ),
    "start": _EP(
        py_name="start",
        response_type="None",
        doc="Start the Tailscale backend with the given options.",
    ),
    "logout": _EP(
        py_name="logout",
        response_type="None",
        doc="Disconnect from Tailscale and expire current node key.",
    ),
    "shutdown": _EP(
        py_name="shutdown",
        response_type="None",
        doc="Shut down the tailscaled daemon.",
    ),
    "reset-auth": _EP(
        py_name="reset_auth",
        response_type="None",
        doc="Reset authentication state, forcing re-login.",
    ),
    "set-expiry-sooner": _EP(
        py_name="set_expiry_sooner",
        response_type="None",
        doc="Set the key expiry to a sooner time.",
    ),
    "reload-config": _EP(
        py_name="reload_config",
        response_type="None",
        doc="Reload configuration from disk.",
    ),

    # ---- Profiles ----
    "profiles/": _EP(
        py_name="profiles",
        response_type="List[Dict[str, Any]]",
        doc="List or manage Tailscale account profiles.",
    ),

    # ---- Network diagnostics ----
    "derpmap": _EP(
        py_name="derpmap",
        response_type="Dict[str, Any]",
        doc="Return the current DERP map.",
    ),
    "suggest-exit-node": _EP(
        py_name="suggest_exit_node",
        response_type="Dict[str, Any]",
        doc="Suggest an exit node based on current conditions.",
    ),
    "check-ip-forwarding": _EP(
        py_name="check_ip_forwarding",
        response_type="Dict[str, Any]",
        doc="Check whether IP forwarding is enabled on this host.",
    ),

    # ---- DNS ----
    "set-dns": _EP(
        py_name="set_dns",
        response_type="None",
        doc="Set a DNS record for an ACME challenge.",
    ),
    "dns-osconfig": _EP(
        py_name="dns_osconfig",
        response_type="Dict[str, Any]",
        doc="Return the OS DNS configuration.",
    ),
    "dns-query": _EP(
        py_name="dns_query",
        response_type="Dict[str, Any]",
        doc="Perform a DNS query through the Tailscale DNS forwarder.",
    ),

    # ---- Debugging ----
    "bugreport": _EP(
        py_name="bugreport",
        response_type="str",
        doc="Generate a bug report identifier.",
    ),
    "goroutines": _EP(
        py_name="goroutines",
        response_type="str",
        doc="Return a goroutine dump from tailscaled.",
    ),
    "metrics": _EP(
        py_name="metrics",
        response_type="str",
        doc="Return Prometheus-style metrics from tailscaled.",
    ),

    # ---- Updates ----
    "update/check": _EP(
        py_name="update_check",
        response_type="Dict[str, Any]",
        doc="Check for available Tailscale updates.",
    ),

    # ---- Exit node ----
    "set-use-exit-node-enabled": _EP(
        py_name="set_use_exit_node_enabled",
        response_type="None",
        doc="Enable or disable using the configured exit node.",
    ),

    # ---- Misc ----
    "id-token": _EP(
        py_name="id_token",
        response_type="Dict[str, Any]",
        doc="Request an OIDC ID token for the given audience.",
        positional_params=[
            ("aud", "aud", "str", _REQUIRED),
        ],
    ),
    "query-feature": _EP(
        py_name="query_feature",
        response_type="Dict[str, Any]",
        doc="Query whether a feature is available.",
    ),
    "set-gui-visible": _EP(
        py_name="set_gui_visible",
        response_type="None",
        doc="Tell tailscaled whether a GUI is visible.",
    ),
    "usermetrics": _EP(
        py_name="usermetrics",
        response_type="None",
        doc="Upload user-facing metrics.",
    ),
    "upload-client-metrics": _EP(
        py_name="upload_client_metrics",
        response_type="None",
        doc="Upload client metrics to the control server.",
    ),
    "disconnect-control": _EP(
        py_name="disconnect_control",
        response_type="None",
        doc="Disconnect from the control server (debug).",
    ),
    "appc-route-info": _EP(
        py_name="appc_route_info",
        response_type="Dict[str, Any]",
        doc="Get app connector route information.",
    ),
    "check-so-mark-in-use": _EP(
        py_name="check_so_mark_in_use",
        response_type="Dict[str, Any]",
        doc="Check if the SO_MARK value is in use.",
    ),
    "check-udp-gro-forwarding": _EP(
        py_name="check_udp_gro_forwarding",
        response_type="Dict[str, Any]",
        doc="Check whether UDP GRO forwarding is supported.",
    ),
    "set-udp-gro-forwarding": _EP(
        py_name="set_udp_gro_forwarding",
        response_type="None",
        doc="Enable or disable UDP GRO forwarding.",
    ),
    "check-reverse-path-filtering": _EP(
        py_name="check_reverse_path_filtering",
        response_type="Dict[str, Any]",
        doc="Check reverse-path filtering status.",
    ),
    "set-push-device-token": _EP(
        py_name="set_push_device_token",
        response_type="None",
        doc="Register a push notification device token.",
    ),
    "handle-push-message": _EP(
        py_name="handle_push_message",
        response_type="None",
        doc="Handle an incoming push notification message.",
    ),
    "alpha-set-device-attrs": _EP(
        py_name="set_device_attrs",
        response_type="None",
        doc="Set device attributes (alpha/experimental).",
    ),
}

# Streaming endpoints — generated as stubs, not full methods.
STREAMING_ROUTES = {"watch-ipn-bus", "logtap", "dial", "pprof"}


# ---------------------------------------------------------------------------
# Name derivation helpers
# ---------------------------------------------------------------------------

def _route_to_method_name(route: str) -> str:
    """Derive a Python method name from a route string."""
    name = route.rstrip("/")
    # Replace non-alphanum with underscore
    name = name.replace("-", "_").replace("/", "_")
    # Collapse double underscores
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def generate_localapi_module(
    api_file: LocalAPIFile,
    *,
    upstream_url: str = "",
    upstream_commit: str = "",
    base_import: str = "tailscale_cli._util.localapi_base",
    serde_import: str = "tailscale_cli._util.serde",
    available_models: Optional[Set[str]] = None,
) -> str:
    """Generate a Python module containing a versioned ``LocalAPI`` class."""

    lines: List[str] = []

    # --- Header ---
    lines.append('"""')
    lines.append("Auto-generated LocalAPI client — DO NOT EDIT.")
    lines.append("")
    lines.append("This module is produced by codegen from upstream Go source.")
    lines.append("It exposes one method per LocalAPI endpoint, with the correct")
    lines.append("HTTP method, query parameters, and (where known) typed returns.")
    if upstream_url:
        lines.append(f"")
        lines.append(f"Source : {upstream_url}")
    if upstream_commit:
        lines.append(f"Commit : {upstream_commit}")
    lines.append(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any, Dict, List, Optional")
    lines.append("")
    lines.append(f"from {base_import} import LocalAPIBase")
    lines.append("")

    # Determine which model modules are referenced by curated endpoints
    model_refs: Set[str] = set()
    for ep in api_file.endpoints:
        cur = CURATED.get(ep.route)
        if cur and cur.response_model:
            mod = cur.response_model.split(".")[0]
            model_refs.add(mod)

    # Emit relative model imports (from . import ipnstate, prefs, …)
    if model_refs:
        imports = ", ".join(sorted(model_refs))
        lines.append(f"from . import {imports}")
        lines.append("")

    lines.append("")

    # --- Endpoint list as a class variable (for introspection) ---
    lines.append("# Route table extracted from upstream localapi.go")
    lines.append("ENDPOINTS = [")
    for ep in api_file.endpoints:
        methods = ", ".join(f'"{m}"' for m in ep.http_methods)
        params = ", ".join(f'"{p.name}"' for p in ep.query_params)
        lines.append(
            f'    {{"route": "{ep.route}", "methods": [{methods}], '
            f'"permission": "{ep.permission}", "params": [{params}]}},')
    lines.append("]")
    lines.append("")
    lines.append("")

    # --- Class ---
    lines.append("class LocalAPI(LocalAPIBase):")
    lines.append('    """Version-specific LocalAPI client.')
    lines.append("")
    lines.append(f"    Auto-generated from ``localapi.go``.")
    if upstream_commit:
        lines.append(f"    Commit: {upstream_commit[:12]}")
    lines.append("")
    lines.append(f"    {len(api_file.endpoints)} endpoints available.")
    lines.append('    """')
    lines.append("")

    # --- Methods ---
    for ep in api_file.endpoints:
        _generate_endpoint_method(ep, lines, available_models)

    return "\n".join(lines) + "\n"


def _generate_endpoint_method(
    ep: APIEndpoint,
    lines: List[str],
    available_models: Optional[Set[str]],
) -> None:
    """Append a method definition for one endpoint."""

    cur = CURATED.get(ep.route)
    py_name = (cur.py_name if cur else "") or _route_to_method_name(ep.route)

    # Streaming endpoints → stub only
    if ep.route in STREAMING_ROUTES or ep.is_streaming:
        _emit_streaming_stub(ep, py_name, cur, lines)
        return

    # Prefix-match routes (like profiles/) need special handling
    if ep.is_prefix:
        _emit_prefix_route(ep, py_name, cur, lines)
        return

    http_method = ep.http_methods[0] if ep.http_methods else "GET"
    return_type = (cur.response_type if cur else None) or "Dict[str, Any]"

    # Build method signature
    positional: List[Tuple[str, str, str, Any]] = []
    keyword_params: List[APIQueryParam] = []

    if cur and cur.positional_params:
        positional = cur.positional_params
    else:
        keyword_params = ep.query_params

    sig_parts = ["self"]
    # Positional (required first, then optional)
    req_params = [p for p in positional if p[3] is _REQUIRED]
    opt_params = [p for p in positional if p[3] is not _REQUIRED]

    for py_p, _qk, py_t, _default in req_params:
        sig_parts.append(f"{py_p}: {py_t}")

    if opt_params or keyword_params or ep.has_request_body:
        sig_parts.append("*")

    for py_p, _qk, py_t, default in opt_params:
        sig_parts.append(f"{py_p}: {py_t} = {default}")

    for qp in keyword_params:
        safe_name = qp.name.replace("-", "_")
        sig_parts.append(f"{safe_name}: Optional[str] = None")

    if ep.has_request_body:
        sig_parts.append("json_body: Optional[Dict[str, Any]] = None")

    sig_parts.append("timeout: float = 30.0")

    sig = ", ".join(sig_parts)

    # Determine actual return annotation
    ret_ann = return_type
    if ret_ann == "None":
        ret_ann = "None"

    # Docstring
    doc = (cur.doc if cur else "") or f"{http_method} /localapi/v0/{ep.route}"
    perm_note = f"Requires ``{ep.permission}`` permission." if ep.permission != "none" else ""

    lines.append(f"    def {py_name}({sig}) -> {ret_ann}:")
    lines.append(f'        """{doc}')
    lines.append(f"")
    lines.append(f"        {http_method} /localapi/v0/{ep.route}")
    if perm_note:
        lines.append(f"        {perm_note}")
    lines.append(f'        """')

    # Build params dict
    if positional or keyword_params:
        lines.append("        params: Dict[str, str] = {}")
        for py_p, qk, py_t, default in positional:
            if default is _REQUIRED:
                if py_t == "int":
                    lines.append(f'        params["{qk}"] = str({py_p})')
                else:
                    lines.append(f'        params["{qk}"] = {py_p}')
            else:
                lines.append(f'        if {py_p} is not None:')
                if py_t == "int":
                    lines.append(f'            params["{qk}"] = str({py_p})')
                else:
                    lines.append(f'            params["{qk}"] = str({py_p})')
        for qp in keyword_params:
            safe = qp.name.replace("-", "_")
            lines.append(f'        if {safe} is not None:')
            lines.append(f'            params["{qp.name}"] = {safe}')

    # Make the request
    params_arg = "params=params, " if (positional or keyword_params) else ""
    body_arg = "json_body=json_body, " if ep.has_request_body else ""

    lines.append(
        f'        resp = self._request("{http_method}", "{ep.route}", '
        f'{params_arg}{body_arg}timeout=timeout)'
    )

    # Return
    if return_type == "None":
        lines.append("        return None")
    elif return_type == "str":
        lines.append("        return resp.text")
    elif cur and cur.response_model:
        mod_class = cur.response_model
        lines.append(f"        return {mod_class}.loads(resp.content.decode())")
    elif return_type.startswith("List["):
        lines.append("        return resp.json()")
    else:
        lines.append("        return resp.json()")

    lines.append("")


def _emit_streaming_stub(
    ep: APIEndpoint,
    py_name: str,
    cur: Optional[_EP],
    lines: List[str],
) -> None:
    """Emit a stub for a streaming or special endpoint."""
    doc = (cur.doc if cur else "") or f"Streaming: {ep.route}"
    lines.append(f"    def {py_name}(self) -> None:")
    lines.append(f'        """{doc}')
    lines.append(f"")
    lines.append(f"        This endpoint uses long-lived streaming and is not")
    lines.append(f"        supported through the standard request/response flow.")
    lines.append(f'        """')
    lines.append(f'        raise NotImplementedError("{ep.route} is a streaming endpoint")')
    lines.append("")


def _emit_prefix_route(
    ep: APIEndpoint,
    py_name: str,
    cur: Optional[_EP],
    lines: List[str],
) -> None:
    """Emit method(s) for a prefix-match route like ``profiles/``."""
    route_base = ep.route.rstrip("/")
    doc = (cur.doc if cur else "") or f"Prefix route: {ep.route}"

    # List (GET /<route>/)
    lines.append(f"    def {py_name}(self, *, timeout: float = 30.0) -> List[Dict[str, Any]]:")
    lines.append(f'        """{doc}')
    lines.append(f"")
    lines.append(f"        GET /localapi/v0/{ep.route}")
    lines.append(f'        """')
    lines.append(f'        resp = self._request("GET", "{ep.route}", timeout=timeout)')
    lines.append(f"        return resp.json()")
    lines.append("")

    # Get single (GET /<route>/<id>)
    lines.append(f"    def {py_name}_get(self, item_id: str, *, timeout: float = 30.0) -> Dict[str, Any]:")
    lines.append(f'        """Get a single item from {ep.route}<id>."""')
    lines.append(f"        import urllib.parse")
    lines.append(f'        encoded = urllib.parse.quote(item_id, safe="")')
    lines.append(f'        resp = self._request("GET", f"{route_base}/{{encoded}}", timeout=timeout)')
    lines.append(f"        return resp.json()")
    lines.append("")

    # Switch / POST (POST /<route>/<id>)
    lines.append(f"    def {py_name}_switch(self, item_id: str, *, timeout: float = 30.0) -> None:")
    lines.append(f'        """POST to {ep.route}<id> (e.g. switch profile)."""')
    lines.append(f"        import urllib.parse")
    lines.append(f'        encoded = urllib.parse.quote(item_id, safe="")')
    lines.append(f'        self._request("POST", f"{route_base}/{{encoded}}", timeout=timeout)')
    lines.append(f"        return None")
    lines.append("")

    # Delete (DELETE /<route>/<id>)
    lines.append(f"    def {py_name}_delete(self, item_id: str, *, timeout: float = 30.0) -> None:")
    lines.append(f'        """DELETE {ep.route}<id>."""')
    lines.append(f"        import urllib.parse")
    lines.append(f'        encoded = urllib.parse.quote(item_id, safe="")')
    lines.append(f'        self._request("DELETE", f"{route_base}/{{encoded}}", timeout=timeout)')
    lines.append(f"        return None")
    lines.append("")
