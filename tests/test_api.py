"""Unit tests for tailscale_cli.api — version resolution & TailscaleCLI.connect."""

from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from tailscale_cli.api import (
    TailscaleCLI,
    _query_daemon_version,
    _ref_to_package_name,
)
from tailscale_cli.v0.api import LocalAPI


# ---------------------------------------------------------------------------
# _ref_to_package_name
# ---------------------------------------------------------------------------


class TestRefToPackageName:
    def test_semver_tag(self):
        assert _ref_to_package_name("v1.94.2") == "v1_94_2"

    def test_semver_tag_no_v(self):
        assert _ref_to_package_name("1.94.2") == "v1_94_2"

    def test_commit_sha_truncated(self):
        sha = "2de4d317a8c2595904f1563ebd98fdcf843da275"
        result = _ref_to_package_name(sha)
        assert result == "v2de4d317a8c2"  # 12-char prefix, starts with digit → v prefix

    def test_branch_name(self):
        assert _ref_to_package_name("main") == "main"

    def test_whitespace_stripped(self):
        assert _ref_to_package_name("  v1.94.2  ") == "v1_94_2"


# ---------------------------------------------------------------------------
# _query_daemon_version
# ---------------------------------------------------------------------------


class TestQueryDaemonVersion:
    def _make_api(
        self,
        version_response: Optional[Dict[str, Any]] = None,
        raises: Optional[Exception] = None,
    ) -> LocalAPI:
        """Build a LocalAPI with a mocked version() method."""
        api = MagicMock(spec=LocalAPI)
        if raises:
            api.version.side_effect = raises
        else:
            api.version.return_value = version_response or {}
        return api

    def test_returns_version_from_major_minor_patch(self):
        api = self._make_api({"majorMinorPatch": "1.94.2", "short": "1.94.2"})
        assert _query_daemon_version(api) == "v1.94.2"

    def test_prepends_v_prefix(self):
        api = self._make_api({"majorMinorPatch": "1.94.2"})
        assert _query_daemon_version(api) == "v1.94.2"

    def test_preserves_existing_v_prefix(self):
        api = self._make_api({"majorMinorPatch": "v1.94.2"})
        assert _query_daemon_version(api) == "v1.94.2"

    def test_falls_back_to_short(self):
        api = self._make_api({"short": "1.94.2"})
        assert _query_daemon_version(api) == "v1.94.2"

    def test_returns_none_on_missing_fields(self):
        api = self._make_api({"long": "some-long-hash"})
        assert _query_daemon_version(api) is None

    def test_returns_none_on_empty_response(self):
        api = self._make_api({})
        assert _query_daemon_version(api) is None

    def test_returns_none_on_connection_error(self):
        api = self._make_api(raises=ConnectionError("no socket"))
        assert _query_daemon_version(api) is None

    def test_returns_none_on_any_exception(self):
        api = self._make_api(raises=RuntimeError("boom"))
        assert _query_daemon_version(api) is None

    def test_strips_whitespace_from_version(self):
        api = self._make_api({"majorMinorPatch": "  1.94.2  "})
        assert _query_daemon_version(api) == "v1.94.2"


# ---------------------------------------------------------------------------
# TailscaleCLI.connect — version resolution
#
# Note: LocalAPI is NOT mocked — httpx.HTTPTransport(uds=...) is lazy and
# won't fail at creation time even if the socket doesn't exist.  This lets
# us test the full resolution logic without any transport-level mocks.
# ---------------------------------------------------------------------------


class TestConnect:
    """Tests for TailscaleCLI.connect() with mocked daemon version probe."""

    @patch("tailscale_cli.api._query_daemon_version")
    def test_explicit_version_loads_matching_models(self, mock_query):
        result = TailscaleCLI.connect("v1.94.2")

        # Should NOT query the daemon when an explicit version is given.
        mock_query.assert_not_called()
        # Should have loaded the real v1_94_2 models package.
        assert result._models is not None
        assert hasattr(result._models, "Status")

    @patch("tailscale_cli.api._query_daemon_version", return_value="v1.94.2")
    def test_auto_detect_from_daemon(self, mock_query):
        result = TailscaleCLI.connect()

        mock_query.assert_called_once()
        assert result._models is not None
        assert hasattr(result._models, "Status")

    @patch("tailscale_cli.api._default_ref", return_value="v1.94.2")
    @patch("tailscale_cli.api._query_daemon_version", return_value=None)
    def test_falls_back_to_codegen_toml(self, mock_query, mock_default):
        result = TailscaleCLI.connect()

        mock_query.assert_called_once()
        mock_default.assert_called_once()
        assert result._models is not None
        assert hasattr(result._models, "Status")

    @patch("tailscale_cli.api._default_ref", return_value=None)
    @patch("tailscale_cli.api._query_daemon_version", return_value=None)
    def test_no_version_returns_handle_without_models(self, mock_query, mock_default):
        result = TailscaleCLI.connect()
        assert result._models is None

    @patch("tailscale_cli.api._query_daemon_version")
    def test_explicit_version_missing_models_raises(self, mock_query):
        with pytest.raises(ImportError, match="No generated models"):
            TailscaleCLI.connect("v99.99.99")

    @patch("tailscale_cli.api._default_ref", return_value=None)
    @patch("tailscale_cli.api._query_daemon_version", return_value="v99.99.99")
    def test_auto_detected_version_missing_models_warns_not_raises(
        self,
        mock_query,
        mock_default,
    ):
        # Should NOT raise — just warn and return handle without models.
        result = TailscaleCLI.connect()
        assert result._models is None

    @patch("tailscale_cli.api._query_daemon_version")
    def test_custom_socket_path_forwarded(self, mock_query):
        result = TailscaleCLI.connect("v1.94.2", socket_path="/tmp/custom.sock")
        assert result._socket_path == "/tmp/custom.sock"


# ---------------------------------------------------------------------------
# TailscaleCLI.v0 — backwards compat alias
# ---------------------------------------------------------------------------


class TestV0Alias:
    @patch.object(TailscaleCLI, "connect")
    def test_v0_delegates_to_connect(self, mock_connect):
        TailscaleCLI.v0(socket_path="/tmp/ts.sock")
        mock_connect.assert_called_once_with(socket_path="/tmp/ts.sock")


# ---------------------------------------------------------------------------
# LocalAPI.version (integration-level with mocked HTTP)
# ---------------------------------------------------------------------------


class TestLocalAPIVersion:
    @patch("tailscale_cli.v0.api.make_client")
    def test_version_returns_json(self, mock_make_client):
        mock_client = MagicMock()
        mock_make_client.return_value = mock_client

        resp = MagicMock()
        resp.json.return_value = {
            "majorMinorPatch": "1.94.2",
            "short": "1.94.2",
            "long": "1.94.2-t1abc...",
            "gitCommit": "2de4d317a8c2",
            "cap": 106,
        }
        resp.status_code = 200
        mock_client.request.return_value = resp

        api = LocalAPI(models=None)
        result = api.version()

        mock_client.request.assert_called_once()
        assert result["majorMinorPatch"] == "1.94.2"
        assert result["cap"] == 106
