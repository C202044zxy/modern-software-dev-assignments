"""MCP server wiring.

This is the smallest layer in the stack: it just bridges the MCP protocol
(``list_tools`` / ``call_tool`` requests) to our :mod:`server.tools` registry.

Why is it so thin? Because :mod:`server.tools` already knows everything
about *what* the tools are; the server's only job is to expose that to the
MCP client over the wire. If you wanted to swap the SDK for a different one
(or wrap the tools in a CLI, or a Slack bot, or anything else) you'd
replace *this* file and reuse the rest.

We use the lower-level ``mcp.server.Server`` API (not ``FastMCP``) on
purpose: the explicit ``list_tools`` / ``call_tool`` handlers make the
shape of the protocol concrete instead of hiding it behind decorators on
your handler functions.
"""

from __future__ import annotations

import logging
from typing import List

from mcp.server import Server
from mcp.types import CallToolResult, TextContent, Tool

from server.client import OpenMeteoClient
from server.tools import TOOLS, call_tool
from server.types import ToolError

logger = logging.getLogger(__name__)


def build_server(client: OpenMeteoClient | None = None) -> Server:
    """Construct an MCP :class:`Server` wired up to our tool registry.

    Args:
        client: Optional injected :class:`OpenMeteoClient`. Tests pass a
            client pointed at a mock HTTP server; production code calls
            ``build_server()`` and lets us construct a default one.

    The returned server has exactly two handlers registered:

    * ``list_tools`` returns one ``Tool`` per entry in ``TOOLS``.
    * ``call_tool`` dispatches to :func:`server.tools.call_tool` and wraps
      the result in a list of :class:`TextContent`. On
      :class:`~server.types.ToolError` it returns an MCP error result
      (``[TextContent("Error: ...")]`` plus ``isError=True``) rather than
      raising — that way the client sees the error message instead of a
      generic transport failure.

    Returns:
        A fully configured :class:`Server`, ready to be passed to a
        transport (e.g. ``stdio_server``).
    """
    srv = Server("weather")

    if client is None:
        client = OpenMeteoClient()

    @srv.list_tools()
    async def list_tools() -> list[Tool]:
        return tools_for_protocol()

    @srv.call_tool()
    async def call_tool(name: str, arguments: dict):
        content, is_error = run_tool_as_content(client, name, arguments)
        return CallToolResult(content=content, isError=is_error)

    return srv


def tools_for_protocol() -> List[Tool]:
    """Convert our :data:`server.tools.TOOLS` registry to a list of
    :class:`mcp.types.Tool` objects, ready to return from ``list_tools``.

    The MCP ``Tool`` type wants ``name``, ``description``, and
    ``inputSchema`` — which matches our :class:`~server.tools.ToolSpec`
    exactly, modulo the casing of ``inputSchema``.
    """
    return [
        Tool(name=tool.name, description=tool.description, inputSchema=tool.input_schema)
        for tool in TOOLS
    ]


def run_tool_as_content(
    client: OpenMeteoClient, name: str, arguments: dict
) -> tuple[List[TextContent], bool]:
    """Invoke a tool and package the result for MCP transport.

    This is the function ``call_tool`` should delegate to. Splitting it out
    makes the unit tests in :mod:`tests.test_server` an order of magnitude
    simpler — they can drive this directly without spinning up a transport.

    Returns:
        A pair ``(content, is_error)`` where ``content`` is a one-element
        list of :class:`TextContent` and ``is_error`` is ``True`` iff a
        :class:`ToolError` was caught.
    """
    try:
        response = call_tool(client, name, arguments)
        text_content = TextContent(type="text", text=response)
        return ([text_content], False)
    except ToolError as e:
        text_content = TextContent(type="text", text=str(e.message))
        return ([text_content], True)


__all__ = ["build_server", "tools_for_protocol", "run_tool_as_content"]


# A note on logging:
#
# For STDIO servers, stdout is **reserved for the protocol** — anything you
# print there will be parsed as a JSON-RPC message and corrupt the stream.
# Always log to stderr. The ``logging`` module defaults to stderr, so as
# long as you stick to ``logger.info(...)`` and never ``print(...)``, you
# are fine. ``main.py`` configures the root logger for you.
_ = ToolError  # re-export marker for static analysers; ignore.
