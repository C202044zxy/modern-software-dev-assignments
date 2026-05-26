# Week 3 — Custom MCP Server (Open-Meteo)

A small Model Context Protocol server that wraps the free
[Open-Meteo](https://open-meteo.com) weather API and exposes it as
three tools to any MCP client.

> The walk-through is in [`tutorial.md`](./tutorial.md). This file is
> the short reference: how to install, run, and configure.

## Prerequisites

* Python 3.10+
* The MCP Python SDK and `httpx`:
  ```bash
  pip install mcp httpx
  ```
  (Or, from the repo root: `poetry install` — `httpx` is already a
  dev dependency. `mcp` is not yet pinned in `pyproject.toml`; add it
  there if you want a reproducible env.)

## Run the tests

From `week3/`:

```bash
pytest -q
```

At the start of the assignment 45 of 49 tests fail (every
`NotImplementedError`). When you finish Parts 2–4, all 49 should pass.

## Run the server locally

The server uses **STDIO transport** — it expects to be launched as a
subprocess by an MCP client and to speak JSON-RPC over stdin/stdout.
You can also drive it manually with the MCP Inspector.

### With the MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m server.main
```

Open the URL it prints, click **List Tools**, pick one, fill in the
arguments, **Call Tool**.

### With Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["-m", "server.main"],
      "cwd": "/absolute/path/to/week3"
    }
  }
}
```

Restart Claude Desktop, open the tools menu, and your three tools
should appear.

## Tool reference

| Tool | Arguments | Returns |
| ---- | --------- | ------- |
| `geocode_location` | `name: string` | The single best lat/lon match for the place name. |
| `get_current_weather` | `latitude: number`, `longitude: number` | Temperature, wind speed, conditions at the coordinate. |
| `get_forecast` | `latitude: number`, `longitude: number`, `days: integer (1–16)` | Daily high/low, precipitation, conditions for the next *days* days. |

Each tool returns a plain text rendering of the result. On any
upstream failure (HTTP error, timeout, rate limit, empty result) the
tool returns `Error: <message>` with `isError=True`, so the LLM can
recover gracefully instead of hallucinating.

### Example flow

> User: "What's the weather like in Tokyo right now?"
>
> 1. Model calls `geocode_location({"name": "Tokyo"})` →
>    `"Tokyo, Japan — 35.69°N, 139.69°E"`.
> 2. Model calls `get_current_weather({"latitude": 35.69, "longitude": 139.69})`
>    → `"Current weather at 35.69, 139.69 (as of …): Temperature: 18.2 °C; Wind: 9.4 km/h; Conditions: Mainly clear (weather code 1)"`.
> 3. Model summarises both for the user.

## Layout

```
week3/
├── tutorial.md
├── README.md             <- this file
├── server/
│   ├── __init__.py
│   ├── types.py          <- dataclasses + ToolError (provided)
│   ├── client.py         <- Open-Meteo HTTP wrapper (Part 2)
│   ├── tools.py          <- tool registry + dispatch (Part 3)
│   ├── server.py         <- MCP Server wiring (Part 4)
│   └── main.py           <- STDIO entrypoint (provided)
└── tests/
    ├── conftest.py
    ├── test_client.py
    ├── test_tools.py
    └── test_server.py
```

## Troubleshooting

* **`ModuleNotFoundError: mcp`** — install the SDK:
  `pip install mcp`. The `test_server.py` file uses
  `pytest.importorskip("mcp")`, so the other test files still run
  if it isn't installed.
* **`stdio_server` produces garbled output** — you are `print`ing to
  stdout somewhere. Use `logger.info(...)` instead; stdout is
  reserved for the protocol stream.
* **Claude Desktop doesn't see the server** — check the desktop log
  (Help → Show MCP Logs). The most common causes are an absolute
  path with a typo, or `python` not being on `PATH` from the
  subprocess shell.
* **Tool calls work in the Inspector but not in Claude Desktop** —
  Claude Desktop caches tool definitions. Restart it after any
  schema change.
