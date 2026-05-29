"""Unit tests for server.server (Part 4).

These tests check the MCP wiring without actually starting a transport.
We exercise the two pure helpers (``tools_for_protocol`` and
``run_tool_as_content``) directly; ``build_server`` is checked via a
lightweight smoke test.
"""

from __future__ import annotations

import pytest

# Skip the whole file if the user has not installed the MCP Python SDK yet.
# The other test files don't depend on it, so they continue to run.
pytest.importorskip("mcp")

from mcp.types import TextContent  # noqa: E402
from server.server import build_server, run_tool_as_content, tools_for_protocol  # noqa: E402
from server.types import ToolError  # noqa: E402

from tests.test_tools import FakeClient, _fake_geocode  # noqa: E402


class TestToolsForProtocol:
    def test_returns_one_tool_per_registry_entry(self):
        from server.tools import TOOLS

        tools = tools_for_protocol()
        assert len(tools) == len(TOOLS)

    def test_preserves_name_and_schema(self):
        tools = tools_for_protocol()
        names = {t.name for t in tools}
        assert names == {"geocode_location", "get_current_weather", "get_forecast"}

        by_name = {t.name: t for t in tools}
        # The MCP Tool type spells the field ``inputSchema`` (camelCase).
        assert by_name["geocode_location"].inputSchema["type"] == "object"

    def test_descriptions_non_empty(self):
        for t in tools_for_protocol():
            assert t.description and len(t.description) > 10


class TestRunToolAsContent:
    def test_success_returns_text_content_no_error(self):
        client = FakeClient(geocode=_fake_geocode())
        content, is_error = run_tool_as_content(client, "geocode_location", {"name": "Berlin"})
        assert is_error is False
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        assert "Berlin" in content[0].text

    def test_tool_error_returns_is_error_true(self):
        client = FakeClient(geocode=ToolError("no such place"))
        content, is_error = run_tool_as_content(client, "geocode_location", {"name": "Atlantis"})
        assert is_error is True
        assert len(content) == 1
        assert isinstance(content[0], TextContent)
        # The message should make it through to the user.
        assert "no such place" in content[0].text

    def test_unknown_tool_returns_is_error_true(self):
        client = FakeClient()
        content, is_error = run_tool_as_content(client, "does_not_exist", {})
        assert is_error is True
        assert "does_not_exist" in content[0].text or "unknown" in content[0].text.lower()


class TestBuildServer:
    def test_returns_server_instance(self):
        from mcp.server import Server

        srv = build_server()
        assert isinstance(srv, Server)

    def test_server_has_a_name(self):
        srv = build_server()
        # The MCP SDK exposes the server name; the exact attribute differs
        # by version, so we accept either of two common spellings.
        name = getattr(srv, "name", None) or getattr(srv, "_name", None)
        assert name is not None
