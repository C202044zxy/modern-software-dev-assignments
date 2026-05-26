"""STDIO entrypoint for the weather MCP server.

Run with ``python -m server.main`` from ``week3/``. This is what Claude
Desktop (and the MCP Inspector) will spawn under the hood once you point
them at this server.

This file is provided — you do not need to modify it.

Two non-obvious bits:

1. **Logging goes to stderr.** Anything written to stdout would be
   interpreted as a JSON-RPC message by the client and would corrupt the
   protocol stream.
2. **The transport is async.** ``stdio_server()`` is an async context
   manager that yields ``(read_stream, write_stream)`` pairs; we hand them
   to ``server.run(...)`` which is also async. ``asyncio.run`` ties the
   knot.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from mcp.server.stdio import stdio_server

from server.server import build_server


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    )


async def _serve() -> None:
    server = build_server()
    init_options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


def main() -> None:
    _configure_logging()
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
