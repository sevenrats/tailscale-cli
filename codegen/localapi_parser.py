"""
Parse ``ipn/localapi/localapi.go`` to extract the API surface.

Extracts:
- Route registrations (static handler map + dynamic ``Register()`` calls)
- HTTP method constraints per handler
- Permission requirements (PermitRead / PermitWrite / PermitCert)
- Query parameters (from ``r.FormValue`` / ``r.URL.Query().Get``)
- Whether the handler reads a JSON request body
- Whether the handler writes a JSON response
- Whether the handler is a streaming endpoint
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .localapi_ir import APIEndpoint, APIQueryParam, LocalAPIFile

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Static handler map entry:  "route": (*Handler).serveXxx,
_STATIC_HANDLER_RE = re.compile(
    r'"([^"]+)":\s+\(\*Handler\)\.(\w+)'
)

# Dynamic Register() call:  Register("route", (*Handler).serveXxx)
_REGISTER_RE = re.compile(
    r'Register\(\s*"([^"]+)"\s*,\s*\(\*Handler\)\.(\w+)\s*\)'
)

# Handler function signature
_HANDLER_FUNC_RE = re.compile(
    r'func\s+\(h\s+\*Handler\)\s+(\w+)\(w\s+http\.ResponseWriter,\s*r\s+\*http\.Request\)'
)

# HTTP method checks
_METHOD_NEQ_RE = re.compile(r'r\.Method\s*!=\s*(?:httpm\.)?["\']?(\w+)')
_METHOD_EQ_RE = re.compile(r'r\.Method\s*==\s*(?:httpm\.)?["\']?(\w+)')
_METHOD_SWITCH_CASE_RE = re.compile(r'case\s+httpm\.(\w+)')

# Permission checks  (the Go code uses  if !h.PermitXxx { ... return })
_PERMIT_RE = re.compile(r'h\.Permit(\w+)')

# Query parameters
_FORM_VALUE_RE = re.compile(r'r\.FormValue\(\s*"([^"]+)"\s*\)')
_QUERY_GET_RE = re.compile(r'r\.URL\.Query\(\)\.Get\(\s*"([^"]+)"\s*\)')
_QUERY_HAS_RE = re.compile(r'r\.URL\.Query\(\)\.Has\(\s*"([^"]+)"\s*\)')

# JSON request body
_JSON_DECODE_RE = re.compile(r'json\.NewDecoder\(r\.Body\)\.Decode')

# JSON response
_JSON_ENCODE_RE = re.compile(r'json\.NewEncoder\(w\)\.Encode|json\.Marshal')

# Streaming indicators
_STREAMING_INDICATORS = {"watch-ipn-bus", "logtap", "dial"}
_FLUSHER_RE = re.compile(r'http\.Flusher')


# ---------------------------------------------------------------------------
# Handler body extraction
# ---------------------------------------------------------------------------

def _extract_handler_bodies(src: str) -> Dict[str, str]:
    """Map handler_name → function body text for all handler functions."""
    bodies: Dict[str, str] = {}

    for m in _HANDLER_FUNC_RE.finditer(src):
        handler_name = m.group(1)
        # Find the opening brace of the function
        rest = src[m.end():]
        brace_pos = rest.find("{")
        if brace_pos == -1:
            continue

        abs_start = m.end() + brace_pos
        # Walk forward to find the matching close brace
        depth = 0
        i = abs_start
        while i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1

        body = src[abs_start + 1 : i]
        bodies[handler_name] = body

    return bodies


# ---------------------------------------------------------------------------
# Per-handler analysis
# ---------------------------------------------------------------------------

def _detect_http_methods(body: str) -> List[str]:
    """Detect which HTTP methods a handler accepts."""
    methods: List[str] = []

    # Case 1: switch on r.Method with case httpm.XXX
    switch_cases = _METHOD_SWITCH_CASE_RE.findall(body)
    if switch_cases:
        return sorted(set(m.upper() for m in switch_cases))

    # Case 2: r.Method != httpm.XXX (means method MUST be XXX)
    neq = _METHOD_NEQ_RE.findall(body)
    if neq:
        # If there's a single != check, the required method is that one
        # (the handler rejects everything else)
        return sorted(set(m.upper().strip('"').strip("'") for m in neq))

    # Case 3: r.Method == httpm.XXX
    eq = _METHOD_EQ_RE.findall(body)
    if eq:
        return sorted(set(m.upper().strip('"').strip("'") for m in eq))

    return ["GET"]  # default assumption


def _detect_permission(body: str) -> str:
    """Detect the permission level from the first PermitXxx gate."""
    # Look for the first !h.PermitXxx check — that's the gate.
    # Order matters: check within the first ~500 chars (the preamble).
    preamble = body[:800]
    m = _PERMIT_RE.search(preamble)
    if m:
        perm = m.group(1).lower()
        if perm in ("read", "write", "cert"):
            return perm
    return "none"


def _extract_query_params(body: str) -> List[APIQueryParam]:
    """Extract query parameter names from the handler body."""
    seen: Dict[str, APIQueryParam] = {}

    for pat in (_FORM_VALUE_RE, _QUERY_GET_RE, _QUERY_HAS_RE):
        for m in pat.finditer(body):
            name = m.group(1)
            if name not in seen:
                seen[name] = APIQueryParam(name=name)

    return list(seen.values())


def _has_json_request_body(body: str) -> bool:
    return bool(_JSON_DECODE_RE.search(body))


def _has_json_response(body: str) -> bool:
    return bool(_JSON_ENCODE_RE.search(body))


def _is_streaming(route: str, body: str) -> bool:
    if route in _STREAMING_INDICATORS:
        return True
    return bool(_FLUSHER_RE.search(body))


# ---------------------------------------------------------------------------
# Route extraction
# ---------------------------------------------------------------------------

def _extract_routes(src: str) -> List[Tuple[str, str, str]]:
    """Extract (route, handler_name, registration_type) triples."""
    routes: List[Tuple[str, str, str]] = []

    for m in _STATIC_HANDLER_RE.finditer(src):
        routes.append((m.group(1), m.group(2), "static"))

    for m in _REGISTER_RE.finditer(src):
        routes.append((m.group(1), m.group(2), "dynamic"))

    return routes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_localapi(src: str) -> LocalAPIFile:
    """Parse a ``localapi.go`` source file and return its API surface IR."""
    routes = _extract_routes(src)
    bodies = _extract_handler_bodies(src)

    endpoints: List[APIEndpoint] = []

    for route, handler_name, reg_type in routes:
        body = bodies.get(handler_name, "")

        ep = APIEndpoint(
            route=route,
            handler_name=handler_name,
            http_methods=_detect_http_methods(body) if body else ["GET"],
            permission=_detect_permission(body) if body else "none",
            is_prefix=route.endswith("/"),
            query_params=_extract_query_params(body) if body else [],
            has_request_body=_has_json_request_body(body) if body else False,
            has_json_response=_has_json_response(body) if body else False,
            is_streaming=_is_streaming(route, body),
            registration=reg_type,
        )
        endpoints.append(ep)

    return LocalAPIFile(endpoints=endpoints)
