"""Unit tests for tailscale_cli — version resolution, TailscaleCLI.connect,
LocalAPIBase transport, versioned LocalAPI endpoints, and SerdeMixin models.

These tests match the refactored architecture where:
  - TailscaleCLI.connect() is the public factory
  - LocalAPIBase provides the raw HTTP transport (socket → httpx)
  - Versioned LocalAPI classes (v1_XX_Y.localapi.LocalAPI) extend LocalAPIBase
  - Models live inside versioned packages (e.g. v1_94_2.ipnstate.Status)
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from tailscale_cli.api import (
    TailscaleCLI,
    _find_latest_version_package,
    _load_versioned_api,
    _parse_version_tuple,
    _query_daemon_version,
    _ref_to_package_name,
)
from tailscale_cli._util.error import TailscaleError, TailscaleException
from tailscale_cli._util.localapi_base import LocalAPIBase


# =========================================================================
# _ref_to_package_name
# =========================================================================


class TestRefToPackageName:
    def test_semver_tag(self):
        assert _ref_to_package_name("v1.94.2") == "v1_94_2"

    def test_semver_tag_no_v(self):
        assert _ref_to_package_name("1.94.2") == "v1_94_2"

    def test_commit_sha_truncated(self):
        sha = "2de4d317a8c2595904f1563ebd98fdcf843da275"
        result = _ref_to_package_name(sha)
        # 12-char prefix, starts with digit → v prefix
        assert result == "v2de4d317a8c2"

    def test_branch_name(self):
        assert _ref_to_package_name("main") == "main"

    def test_whitespace_stripped(self):
        assert _ref_to_package_name("  v1.94.2  ") == "v1_94_2"

    def test_double_dots_collapsed(self):
        assert _ref_to_package_name("v1..94..2") == "v1_94_2"

    def test_special_chars_replaced(self):
        assert _ref_to_package_name("release/v1.94.2") == "release_v1_94_2"


# =========================================================================
# _parse_version_tuple
# =========================================================================


class TestParseVersionTuple:
    def test_valid_version(self):
        assert _parse_version_tuple("v1_94_2") == (1, 94, 2)

    def test_invalid_name(self):
        assert _parse_version_tuple("main") is None

    def test_non_numeric(self):
        assert _parse_version_tuple("v1_abc_2") is None

    def test_two_parts_only(self):
        assert _parse_version_tuple("v1_94") is None


# =========================================================================
# _find_latest_version_package
# =========================================================================


class TestFindLatestVersionPackage:
    def test_returns_a_valid_package_name(self):
        """Should find at least one versioned package in the repo."""
        result = _find_latest_version_package()
        assert result is not None
        assert result.startswith("v")

    def test_returns_highest_version(self):
        """The result should be the lexicographically highest semver."""
        result = _find_latest_version_package()
        ver = _parse_version_tuple(result)
        assert ver is not None
        # v1.94.2 is known to exist
        assert ver >= (1, 94, 2)


# =========================================================================
# _load_versioned_api
# =========================================================================


class TestLoadVersionedApi:
    def test_loads_known_version(self):
        cls = _load_versioned_api("v1_94_2")
        assert cls is not None
        assert issubclass(cls, LocalAPIBase)

    def test_returns_none_for_unknown(self):
        cls = _load_versioned_api("v99_99_99")
        assert cls is None

    def test_returns_none_for_garbage(self):
        cls = _load_versioned_api("not_a_real_package")
        assert cls is None


# =========================================================================
# _query_daemon_version
# =========================================================================


class TestQueryDaemonVersion:
    """_query_daemon_version talks to the socket via LocalAPIBase.version()."""

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_returns_version_from_major_minor_patch(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"majorMinorPatch": "1.94.2", "short": "1.94.2"}
        assert _query_daemon_version("/fake.sock") == "v1.94.2"

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_prepends_v_prefix(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"majorMinorPatch": "1.94.2"}
        assert _query_daemon_version("/fake.sock") == "v1.94.2"

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_preserves_existing_v_prefix(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"majorMinorPatch": "v1.94.2"}
        assert _query_daemon_version("/fake.sock") == "v1.94.2"

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_falls_back_to_short(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"short": "1.94.2"}
        assert _query_daemon_version("/fake.sock") == "v1.94.2"

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_returns_none_on_missing_fields(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"long": "some-long-hash"}
        assert _query_daemon_version("/fake.sock") is None

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_returns_none_on_empty_response(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {}
        assert _query_daemon_version("/fake.sock") is None

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_raises_on_connection_error(self, MockBase):
        instance = MockBase.return_value
        instance.version.side_effect = ConnectionError("no socket")
        with pytest.raises(TailscaleException) as exc_info:
            _query_daemon_version("/fake.sock")
        assert exc_info.value.error == TailscaleError.CONNECTION_ERROR

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_raises_on_any_exception(self, MockBase):
        instance = MockBase.return_value
        instance.version.side_effect = RuntimeError("boom")
        with pytest.raises(TailscaleException) as exc_info:
            _query_daemon_version("/fake.sock")
        assert exc_info.value.error == TailscaleError.CONNECTION_ERROR

    @patch("tailscale_cli.api.LocalAPIBase")
    def test_strips_whitespace_from_version(self, MockBase):
        instance = MockBase.return_value
        instance.version.return_value = {"majorMinorPatch": "  1.94.2  "}
        assert _query_daemon_version("/fake.sock") == "v1.94.2"


# =========================================================================
# TailscaleCLI.connect — version resolution
# =========================================================================


class TestConnect:
    """Tests for TailscaleCLI.connect() — the main factory.

    LocalAPI creation via httpx.HTTPTransport(uds=...) is lazy, so we can
    exercise the full resolution logic without actually having a socket.
    """

    @patch("tailscale_cli.api._query_daemon_version", return_value="v1.94.2")
    def test_explicit_version_loads_matching_api(self, mock_query):
        """Explicit version probes daemon, then loads a versioned LocalAPI."""
        result = TailscaleCLI.connect("v1.94.2")

        mock_query.assert_called_once()
        # Should be an instance of the versioned LocalAPI, not bare base
        assert type(result).__name__ == "LocalAPI"
        assert isinstance(result, LocalAPIBase)

    @patch("tailscale_cli.api._query_daemon_version", return_value="v1.94.2")
    def test_auto_detect_from_daemon(self, mock_query):
        """When no version is given, query the daemon and load matching API."""
        result = TailscaleCLI.connect()

        mock_query.assert_called_once()
        assert type(result).__name__ == "LocalAPI"
        assert isinstance(result, LocalAPIBase)

    @patch("tailscale_cli.api._query_daemon_version",
           side_effect=TailscaleException.connection_error())
    def test_raises_on_unreachable_daemon(self, mock_query):
        """When daemon is unreachable, connect() raises."""
        with pytest.raises(TailscaleException) as exc_info:
            TailscaleCLI.connect()
        assert exc_info.value.error == TailscaleError.CONNECTION_ERROR

    @patch("tailscale_cli.api._find_latest_version_package", return_value=None)
    @patch("tailscale_cli.api._query_daemon_version", return_value=None)
    def test_no_version_returns_bare_base(self, mock_query, mock_latest):
        """When no version packages exist at all, get a bare LocalAPIBase."""
        result = TailscaleCLI.connect()

        assert type(result) is LocalAPIBase

    @patch("tailscale_cli.api._find_latest_version_package", return_value=None)
    @patch("tailscale_cli.api._query_daemon_version", return_value="v99.99.99")
    def test_unknown_detected_version_falls_back_gracefully(self, mock_query, mock_latest):
        """Detected version with no matching package → bare LocalAPIBase."""
        result = TailscaleCLI.connect()
        assert type(result) is LocalAPIBase

    @patch("tailscale_cli.api._query_daemon_version", return_value="v1.94.2")
    def test_custom_socket_path_forwarded(self, mock_query):
        """The socket_path argument is propagated to the returned handle."""
        result = TailscaleCLI.connect("v1.94.2", socket_path="/tmp/custom.sock")
        assert result._socket_path == "/tmp/custom.sock"

    @patch("tailscale_cli.api._query_daemon_version", return_value="v1.94.2")
    def test_default_socket_path(self, mock_query):
        """Default socket path is the standard tailscaled location."""
        result = TailscaleCLI.connect("v1.94.2")
        assert result._socket_path == "/run/tailscale/tailscaled.sock"


# =========================================================================
# TailscaleCLI.v0 — backwards compat alias
# =========================================================================


class TestV0Alias:
    @patch.object(TailscaleCLI, "connect")
    def test_v0_delegates_to_connect(self, mock_connect):
        TailscaleCLI.v0(socket_path="/tmp/ts.sock")
        mock_connect.assert_called_once_with(socket_path="/tmp/ts.sock")


# =========================================================================
# LocalAPIBase — transport layer
# =========================================================================


def _mock_base(socket_path: str = "/fake.sock") -> tuple[LocalAPIBase, MagicMock]:
    """Create a LocalAPIBase with a mocked httpx client."""
    with patch("tailscale_cli._util.localapi_base.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
        base = LocalAPIBase(socket_path=socket_path)
    return base, mock_client


def _make_response(
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text: str = "",
    content: Optional[bytes] = None,
) -> MagicMock:
    """Build a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    if content is not None:
        resp.content = content
    return resp


class TestLocalAPIBase:
    def test_url_prefixes_localapi_v0(self):
        base, _ = _mock_base()
        assert base._url("status") == "/localapi/v0/status"
        assert base._url("/status") == "/localapi/v0/status"
        assert base._url("localapi/v0/status") == "/localapi/v0/status"

    def test_version_returns_json(self):
        base, mock_client = _mock_base()
        mock_client.request.return_value = _make_response(
            json_data={
                "majorMinorPatch": "1.94.2",
                "short": "1.94.2",
                "long": "1.94.2-t1abc...",
                "gitCommit": "2de4d317a8c2",
                "cap": 106,
            }
        )

        result = base.version()

        mock_client.request.assert_called_once()
        assert result["majorMinorPatch"] == "1.94.2"
        assert result["cap"] == 106

    def test_request_raises_on_4xx(self):
        base, mock_client = _mock_base()
        mock_client.request.return_value = _make_response(
            status_code=401, text="unauthorized"
        )

        with pytest.raises(TailscaleException) as exc_info:
            base._request("GET", "status")
        assert exc_info.value.error == TailscaleError.UNAUTHORIZED

    def test_request_raises_on_5xx(self):
        base, mock_client = _mock_base()
        mock_client.request.return_value = _make_response(
            status_code=500, text="internal server error"
        )

        with pytest.raises(TailscaleException) as exc_info:
            base._request("GET", "status")
        assert exc_info.value.error == TailscaleError.HTTP_ERROR

    def test_request_passes_json_body(self):
        base, mock_client = _mock_base()
        mock_client.request.return_value = _make_response()

        base._request("PATCH", "prefs", json_body={"WantRunning": True})

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["json"] == {"WantRunning": True}
        assert "application/json" in call_kwargs["headers"].get("Content-Type", "")

    def test_request_passes_params(self):
        base, mock_client = _mock_base()
        mock_client.request.return_value = _make_response()

        base._request("GET", "status", params={"peers": "true"})

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"] == {"peers": "true"}


# =========================================================================
# Versioned LocalAPI endpoints (v1_94_2)
# =========================================================================


def _mock_versioned_api(version: str = "v1_94_2"):
    """Create a versioned LocalAPI with a mocked httpx transport."""
    cls = _load_versioned_api(version)
    assert cls is not None, f"Could not load {version}"
    with patch("tailscale_cli._util.localapi_base.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
        api = cls(socket_path="/fake.sock")
    return api, mock_client


class TestVersionedLocalAPI:
    """Tests for the auto-generated v1_94_2.LocalAPI endpoint methods."""

    def test_status_returns_typed_model(self):
        from tailscale_cli.v1_94_2 import ipnstate

        api, mock_client = _mock_versioned_api()
        status_json = {
            "Version": "1.94.2",
            "BackendState": "Running",
            "TUN": True,
            "HaveNodeKey": True,
            "AuthURL": "",
            "TailscaleIPs": ["100.64.0.1"],
            "Health": [],
        }
        mock_client.request.return_value = _make_response(
            content=json.dumps(status_json).encode()
        )

        result = api.status()

        assert isinstance(result, ipnstate.Status)
        assert result.backend_state == "Running"
        assert result.tun is True
        assert result.version == "1.94.2"

    def test_ping_returns_typed_model(self):
        from tailscale_cli.v1_94_2 import ipnstate

        api, mock_client = _mock_versioned_api()
        ping_json = {
            "IP": "100.64.0.2",
            "NodeIP": "100.64.0.2",
            "NodeName": "my-node",
            "LatencySeconds": 0.012,
            "Endpoint": "1.2.3.4:41641",
        }
        mock_client.request.return_value = _make_response(
            content=json.dumps(ping_json).encode()
        )

        result = api.ping("100.64.0.2")

        assert isinstance(result, ipnstate.PingResult)
        assert result.ip == "100.64.0.2"
        assert result.latency_seconds == pytest.approx(0.012)
        # Check query params were sent
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["ip"] == "100.64.0.2"

    def test_profiles_returns_list(self):
        api, mock_client = _mock_versioned_api()
        profiles_json = [
            {"ID": "prof-1", "Name": "work"},
            {"ID": "prof-2", "Name": "personal"},
        ]
        mock_client.request.return_value = _make_response(json_data=profiles_json)

        result = api.profiles()

        assert len(result) == 2
        assert result[0]["ID"] == "prof-1"
        assert result[1]["Name"] == "personal"

    def test_profiles_switch_posts_with_encoded_id(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        api.profiles_switch("user@example.com")

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert "user%40example.com" in call_kwargs["url"]

    def test_profiles_delete_sends_delete(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        api.profiles_delete("prof-abc123")

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "DELETE"
        assert "prof-abc123" in call_kwargs["url"]

    def test_login_interactive(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        result = api.login_interactive()

        assert result is None
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert "login-interactive" in call_kwargs["url"]

    def test_logout(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        result = api.logout()

        assert result is None
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert "logout" in call_kwargs["url"]

    def test_start_with_json_body(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        api.start(json_body={"AuthKey": "tskey-abc123"})

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["json"] == {"AuthKey": "tskey-abc123"}

    def test_prefs_get(self):
        api, mock_client = _mock_versioned_api()
        prefs_json = {"WantRunning": True, "Hostname": "my-host"}
        mock_client.request.return_value = _make_response(json_data=prefs_json)

        result = api.prefs()

        assert result["WantRunning"] is True
        assert result["Hostname"] == "my-host"

    def test_check_prefs_post(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response(json_data={})

        api.check_prefs(json_body={"Hostname": "new-host", "HostnameSet": True})

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["json"]["Hostname"] == "new-host"

    def test_bugreport_returns_text(self):
        api, mock_client = _mock_versioned_api()
        resp = _make_response()
        resp.text = "BUG-abc123"
        mock_client.request.return_value = resp

        result = api.bugreport(note="test bug")

        assert result == "BUG-abc123"
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["note"] == "test bug"

    def test_goroutines_returns_text(self):
        api, mock_client = _mock_versioned_api()
        resp = _make_response()
        resp.text = "goroutine 1 [running]:\nmain.main()"
        mock_client.request.return_value = resp

        result = api.goroutines()

        assert "goroutine 1" in result

    def test_metrics_returns_text(self):
        api, mock_client = _mock_versioned_api()
        resp = _make_response()
        resp.text = "# HELP tailscaled_inbound_bytes_total\ntailscaled_inbound_bytes_total 42"
        mock_client.request.return_value = resp

        result = api.metrics()

        assert "tailscaled_inbound_bytes_total" in result

    def test_whois_returns_json(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response(
            json_data={"Node": {"ID": 123}, "UserProfile": {"LoginName": "user@example.com"}}
        )

        result = api.whois("100.64.0.2")

        assert result["UserProfile"]["LoginName"] == "user@example.com"
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["addr"] == "100.64.0.2"

    def test_id_token(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response(
            json_data={"id_token": "eyJ..."}
        )

        result = api.id_token("my-audience")

        assert result["id_token"] == "eyJ..."
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["aud"] == "my-audience"

    def test_streaming_endpoints_raise(self):
        api, _ = _mock_versioned_api()

        with pytest.raises(NotImplementedError):
            api.shutdown()
        with pytest.raises(NotImplementedError):
            api.watch_ipn_bus()
        with pytest.raises(NotImplementedError):
            api.dial()
        with pytest.raises(NotImplementedError):
            api.logtap()

    def test_derpmap_returns_json(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response(
            json_data={"Regions": {"1": {"RegionID": 1, "RegionCode": "nyc"}}}
        )

        result = api.derpmap()

        assert result["Regions"]["1"]["RegionCode"] == "nyc"

    def test_set_dns(self):
        api, mock_client = _mock_versioned_api()
        mock_client.request.return_value = _make_response()

        api.set_dns(name="_acme-challenge.example.com", value="abc123")

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"]["name"] == "_acme-challenge.example.com"
        assert call_kwargs["params"]["value"] == "abc123"


# =========================================================================
# SerdeMixin — from_dict / to_dict round-tripping
# =========================================================================


class TestSerdeMixin:
    """Test the serde layer used by all generated model dataclasses."""

    def test_status_from_dict_basic(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        data = {
            "Version": "1.94.2",
            "BackendState": "Running",
            "TUN": True,
            "HaveNodeKey": True,
            "AuthURL": "",
            "TailscaleIPs": ["100.64.0.1"],
            "Health": [],
            "MagicDNSSuffix": "ts.net",
        }
        s = Status.from_dict(data)
        assert s.version == "1.94.2"
        assert s.backend_state == "Running"
        assert s.tun is True
        assert s.magic_dns_suffix == "ts.net"
        assert s.tailscale_i_ps == ["100.64.0.1"]

    def test_status_to_dict_uses_json_keys(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status(version="1.94.2", backend_state="Running", tun=True)
        d = s.to_dict()
        assert d["Version"] == "1.94.2"
        assert d["BackendState"] == "Running"
        assert d["TUN"] is True

    def test_status_loads_from_json_string(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        raw = json.dumps({"Version": "1.94.2", "BackendState": "Stopped"})
        s = Status.loads(raw)
        assert s.backend_state == "Stopped"

    def test_status_dumps_to_json_string(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status(version="1.94.2", backend_state="Running")
        raw = s.dumps()
        parsed = json.loads(raw)
        assert parsed["Version"] == "1.94.2"

    def test_ping_result_from_dict(self):
        from tailscale_cli.v1_94_2.ipnstate import PingResult

        data = {
            "IP": "100.64.0.2",
            "NodeIP": "100.64.0.2",
            "NodeName": "peer-1",
            "LatencySeconds": 0.005,
            "Endpoint": "1.2.3.4:41641",
            "DERPRegionID": 1,
            "DERPRegionCode": "nyc",
        }
        p = PingResult.from_dict(data)
        assert p.ip == "100.64.0.2"
        assert p.node_name == "peer-1"
        assert p.latency_seconds == pytest.approx(0.005)
        assert p.derp_region_code == "nyc"

    def test_ping_result_round_trip(self):
        from tailscale_cli.v1_94_2.ipnstate import PingResult

        data = {"IP": "100.64.0.2", "NodeName": "peer-1", "LatencySeconds": 0.01}
        p = PingResult.from_dict(data)
        out = p.to_dict()
        assert out["IP"] == "100.64.0.2"
        assert out["NodeName"] == "peer-1"

    def test_peer_status_from_dict(self):
        from tailscale_cli.v1_94_2.ipnstate import PeerStatus

        data = {
            "ID": "stable-123",
            "PublicKey": "nodekey:abc",
            "HostName": "my-laptop",
            "DNSName": "my-laptop.ts.net.",
            "OS": "linux",
            "Online": True,
            "TailscaleIPs": ["100.64.0.5"],
            "ExitNode": False,
            "Active": True,
        }
        ps = PeerStatus.from_dict(data)
        assert ps.id == "stable-123"
        assert ps.host_name == "my-laptop"
        assert ps.dns_name == "my-laptop.ts.net."
        assert ps.online is True
        assert ps.tailscale_i_ps == ["100.64.0.5"]

    def test_from_dict_empty(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status.from_dict({})
        assert s.version == ""
        assert s.backend_state == ""

    def test_from_dict_none_returns_defaults(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status.from_dict(None)
        assert s.version == ""

    def test_to_dict_omit_none(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status(version="1.94.2")
        d = s.to_dict(omit_none=True)
        # Fields that are None should be omitted
        assert "ExitNodeStatus" not in d

    def test_to_dict_keep_none(self):
        from tailscale_cli.v1_94_2.ipnstate import Status

        s = Status(version="1.94.2")
        d = s.to_dict(omit_none=False)
        assert "ExitNodeStatus" in d
        assert d["ExitNodeStatus"] is None

    def test_nested_model_deserialization(self):
        from tailscale_cli.v1_94_2.ipnstate import Status, TailnetStatus

        data = {
            "Version": "1.94.2",
            "CurrentTailnet": {
                "Name": "my-tailnet",
                "MagicDNSSuffix": "ts.net",
                "MagicDNSEnabled": True,
            },
        }
        s = Status.from_dict(data)
        assert s.current_tailnet is not None
        assert isinstance(s.current_tailnet, TailnetStatus)
        assert s.current_tailnet.name == "my-tailnet"
        assert s.current_tailnet.magic_dns_enabled is True


# =========================================================================
# TailscaleException
# =========================================================================


class TestTailscaleException:
    def test_connection_error(self):
        exc = TailscaleException.connection_error()
        assert exc.error == TailscaleError.CONNECTION_ERROR
        assert "socket" in exc.message

    def test_from_status_code_401(self):
        exc = TailscaleException.from_status_code(401)
        assert exc.error == TailscaleError.UNAUTHORIZED

    def test_from_status_code_500(self):
        exc = TailscaleException.from_status_code(500, "internal error")
        assert exc.error == TailscaleError.HTTP_ERROR
        assert "500" in exc.message

    def test_other(self):
        exc = TailscaleException.other("custom message")
        assert exc.error == TailscaleError.OTHER
        assert exc.message == "custom message"


# =========================================================================
# Package-level imports
# =========================================================================


class TestPackageInit:
    def test_top_level_exports(self):
        """Verify the public names exported from tailscale_cli."""
        import tailscale_cli

        assert hasattr(tailscale_cli, "TailscaleCLI")
        assert hasattr(tailscale_cli, "LocalAPIBase")
        assert hasattr(tailscale_cli, "TailscaleException")

    def test_versioned_package_exports(self):
        """Versioned packages export LocalAPI and model classes."""
        from tailscale_cli.v1_94_2 import LocalAPI
        from tailscale_cli.v1_94_2.ipnstate import Status, PeerStatus, PingResult

        assert issubclass(LocalAPI, LocalAPIBase)
        assert hasattr(Status, "from_dict")
        assert hasattr(PeerStatus, "from_dict")
        assert hasattr(PingResult, "from_dict")
