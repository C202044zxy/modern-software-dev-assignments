# Assignment: Build a Custom MCP Server

> "Anything an LLM can usefully *do* needs to live behind a tool. The
> Model Context Protocol is the contract for what 'a tool' means." — folk
> wisdom

## Overview

In this assignment you will implement an **MCP server** that wraps a real
external API — the [Open-Meteo](https://open-meteo.com) weather service —
and exposes it to an MCP client (Claude Desktop, the MCP Inspector, or
any agent runtime that speaks MCP). By the end you will have:

* an **HTTP client** that talks to two Open-Meteo endpoints and converts
  every upstream failure mode into a clean, user-readable error;
* a **tool registry** of three MCP tools — `geocode_location`,
  `get_current_weather`, `get_forecast` — each with a JSON-Schema input
  contract;
* a **dispatcher** that validates tool arguments and runs the right
  handler;
* an **MCP server wiring layer** that bridges the protocol's
  `list_tools` / `call_tool` requests to your dispatcher;
* a runnable **STDIO entrypoint** you can hook into Claude Desktop.

Most of the code is yours to write. The skeleton supplies the data
classes, the registry, JSON-Schema descriptions, the entrypoint script,
and a comprehensive test suite. Every function with substantive logic is
left as `NotImplementedError("...")` waiting for your code.

A complete pytest suite ships alongside the skeleton. **At the start of
the assignment 45 of 49 tests are failing.** As you implement each part
the corresponding tests turn green, and at the end the whole suite
passes.

### Logistics

| Part | Module | What you build | Tests |
| ---- | ------ | -------------- | ----- |
| 1 | — | Background reading & setup | — |
| 2 | `server/client.py` | Open-Meteo HTTP wrapper + response parsers | `tests/test_client.py` |
| 3 | `server/tools.py` | Tool handlers, validation, dispatch | `tests/test_tools.py` |
| 4 | `server/server.py` | MCP `Server` wiring | `tests/test_server.py` |
| 5 | — | Run it against Claude Desktop / MCP Inspector | — |
| 6 | — | Stretch goals (optional) | — |

### How to run the tests

From `week3/`:

```bash
# Run everything
pytest

# Run a single part
pytest tests/test_client.py -v

# Stop on first failure (useful while iterating)
pytest -x
```

If `pytest` is not on your path, run it through Poetry: `poetry run pytest`.

---

## Part 1 — Background

### Why MCP?

LLMs do two things very well: **draft text** and **decide what to do
next**. They are terrible at everything else — fetching live data,
running deterministic code, talking to your services. So we wire them up
to **tools**, and the LLM's job becomes "look at the situation, pick a
tool, fill in its arguments."

The hard part is the *plumbing*. Every assistant, every IDE, every agent
framework rolled its own tool-calling convention, which meant every API
integration had to be reimplemented N times. The **Model Context
Protocol (MCP)** is the standard that ends that duplication. An MCP
*server* exposes tools, resources, and prompts; an MCP *client* (Claude
Desktop, Cursor, an agent runtime) connects to the server and presents
its capabilities to the LLM. One server, many clients.

### What an MCP server actually serves

MCP defines three kinds of capabilities. We focus on **tools** in this
assignment because they are the load-bearing one; the other two are
shown for context.

| Capability | What it is | Triggered by |
| ---------- | ---------- | ------------ |
| **Tools** | Named functions the LLM may invoke | The model decides to call one |
| **Resources** | Read-only blobs the client may fetch (files, DB rows, …) | The user or app attaches one |
| **Prompts** | Server-authored prompt templates | The user picks one from a menu |

A *tool definition* is just three fields:

```
name:        "get_current_weather"
description: "Get the current weather at a latitude/longitude."
inputSchema: { "type": "object", "properties": {...}, "required": [...] }
```

The description and schema are how the LLM decides *whether* and *how*
to call the tool. We'll spend a lot of Part 3 writing good ones.

### Transports: STDIO vs HTTP

MCP is **transport-agnostic** — the same JSON-RPC messages can flow over
several physical channels. The two common ones:

* **STDIO.** The client launches the server as a subprocess and pipes
  JSON-RPC over stdin/stdout. Simple, secure (no network surface), and
  the right choice for local tools. Claude Desktop uses STDIO.
* **Streamable HTTP.** The server is a long-running HTTP service. Right
  for tools that need to be shared across users or machines, hosted in
  the cloud, etc.

We use **STDIO** in this assignment. The MCP Python SDK abstracts the
transport — `Server.run(read, write, ...)` takes generic streams, and
`stdio_server()` is the one-liner that gives you the right pair for
STDIO. Swapping to HTTP later means swapping that one context manager.

### Pipeline of an MCP request

A single tool call from the user's point of view:

```
┌──────────────┐    1. list_tools       ┌──────────────┐
│              │  ──────────────────▶   │              │
│ MCP client   │    [{name,desc,...}]   │  Your MCP    │
│ (Claude      │  ◀──────────────────   │  server      │
│  Desktop)    │                        │              │
│              │    2. call_tool        │              │
│   ◀── LLM ──▶│  ──────────────────▶   │              │
│              │  (name, arguments)     │   ┌────────┐ │
│              │                        │   │  tool  │ │
│              │                        │   │ handler│ │
│              │                        │   └───┬────┘ │
│              │    3. result content   │       ▼      │
│              │  ◀──────────────────   │  upstream API│
└──────────────┘                        └──────────────┘
```

Roughly:

1. On connect, the client asks `list_tools` and the server returns its
   advertisable surface area.
2. When the LLM picks a tool, the client sends `call_tool(name, args)`.
3. The server runs the handler, calls upstream APIs as needed, and
   returns a list of `Content` blocks (text, image, embedded resource).
   On failure it returns the same shape with `isError=True`, so the
   LLM can see the message and try again.

You implement the boxes on the right.

### Setup

This assignment lives at `week3/`. Layout:

```
week3/
├── tutorial.md               <- this file
├── README.md                 <- short reference
├── server/                   <- the package you implement
│   ├── __init__.py
│   ├── types.py              <- dataclasses + ToolError (provided)
│   ├── client.py             <- Part 2
│   ├── tools.py              <- Part 3
│   ├── server.py             <- Part 4
│   └── main.py               <- STDIO entrypoint (provided)
└── tests/                    <- pytest suite (provided)
    ├── conftest.py
    ├── test_client.py
    ├── test_tools.py
    └── test_server.py
```

Install the MCP Python SDK and confirm everything is wired up:

```bash
pip install mcp httpx
cd week3
pytest -q
```

You should see **45 failures and 4 passes**. The four passes come from
the registry data the skeleton ships with; everything else is a
`NotImplementedError` waiting for your code.

---

## Part 2 — Talking to Open-Meteo (`server/client.py`)

### Why this layer exists

The fundamental rule of building tools on top of a third-party API:
**isolate the third party behind one class** and never reach for `httpx`
directly from anywhere else. Two reasons:

1. **Errors.** Real APIs fail in dozens of shaped ways — timeouts, 4xx
   bodies that *do* parse as JSON, 5xx bodies that don't, 429 rate
   limits, network blips. Centralising all of those in one place lets
   you decide *once* how each maps to a `ToolError`, instead of doing
   it in every handler.
2. **Testing.** Once everything goes through `OpenMeteoClient`, your
   handler tests don't need to mock the network — they mock the client.
   And your client tests don't need to know what a "tool" is — they
   just check the HTTP wiring. Each layer is testable in isolation.

### The endpoints

Open-Meteo is free, requires no API key, and has two endpoints we care
about. Try them in your browser before you write the code:

* Geocoding: <https://geocoding-api.open-meteo.com/v1/search?name=Berlin&count=1>
* Current weather: <https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m,weather_code>
* Daily forecast: <https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&forecast_days=3>

The third URL exposes one of Open-Meteo's quirks: the `daily` block is
**column-oriented**. You get parallel arrays like
`time = [d1, d2, d3]`, `temperature_2m_max = [9.1, 8.4, 5.0]`, …, and
you have to `zip` them into per-day rows yourself.

### Your task

Open `server/client.py` and implement:

1. **`OpenMeteoClient._get_json(url, params)`** — the workhorse HTTP
   call. Convert every `httpx` exception and every non-2xx status into a
   `ToolError`. Handle `httpx.TimeoutException`, `httpx.HTTPError`
   (covers connection errors), and 429 separately from other 4xx/5xx so
   you can give a clearer rate-limit message.
2. **`OpenMeteoClient.geocode`**, **`get_current_weather`**,
   **`get_forecast`** — thin wrappers that build the right query params
   and call `_get_json`, then hand the payload to the matching parser.
3. **`parse_geocode_response`**, **`parse_current_weather`**,
   **`parse_forecast`** — pure functions that turn an Open-Meteo
   response dict into our `GeocodeResult` / `CurrentWeather` /
   `Forecast` types. Each raises `ToolError` if the expected block is
   missing or empty.

The docstrings spell out the contract; the tests pin it down precisely.
A few things to watch for:

* **Empty geocode results are an error.** `{"results": []}` is a 200 OK,
  but from the user's point of view "place not found" is a failure
  worth reporting — not a silent `None`.
* **`forecast_days` is one query param.** Don't try to call the API
  once per day.
* **Validate `days` *before* the network call.** Tests don't even mock
  the network for the invalid-`days` case, so if you skip the check
  you'll see a confusing 404 from the mock router.
* **The daily arrays must all be the same length.** Open-Meteo always
  returns aligned arrays, but defensive parsing is a one-liner and
  catches an entire class of bugs early.

### Run the tests

```bash
pytest tests/test_client.py -v
```

All 21 tests should pass before you continue.

### Quick design discussion

Why is `_get_json` a method and the parsers free functions? Because the
*HTTP call* is stateful (connection pool, URL, timeout) and benefits
from `self`, while the parsers are **pure** — input dict in, dataclass
out — and so are simpler to test, simpler to reason about, and trivially
reusable. The same split shows up in production codebases; favour it
unless you have a specific reason not to.

---

## Part 3 — Tool definitions and dispatch (`server/tools.py`)

### The problem

We have a client. Now we need to package its calls so the LLM can pick
them out of a list and invoke them with the right arguments. That
means:

1. An **advertisable description** for each tool (name + sentence +
   JSON-Schema input).
2. A **handler** that takes the validated arguments and runs the
   right client call.
3. A **dispatcher** that looks up a handler by name, validates the
   arguments, and runs it.

### The registry

The skeleton ships a list of three `ToolSpec` objects in `TOOLS`. Read
it once before you write any code — the `name`, `description`,
`input_schema`, and `handler` fields are the entire vocabulary of what
your server exposes to the LLM. In particular:

* **Descriptions matter.** The LLM reads them while choosing what to do
  next. A vague description leads the model to either ignore the tool
  or use it for the wrong job. (The skeleton's descriptions are good
  enough to start; feel free to refine them in Part 5 after you've seen
  the model use them.)
* **`additionalProperties: false`.** This is what stops the model from
  inventing fields. Always set it.
* **Keep schemas flat.** Nested objects are legal but the LLM is more
  reliable with a single-level argument record.

### Your task

In `server/tools.py`, implement:

1. **`handle_geocode_location`**, **`handle_get_current_weather`**,
   **`handle_get_forecast`** — three handlers. Each takes
   `(client, args)`, makes one client call, and returns a *plain
   string* the user would want to read in a chat. Tests check for
   specific substrings (location name, country, temperature, …),
   so render generously rather than tersely.
2. **`get_tool(name)`** — lookup, raises `ToolError` on unknown name.
3. **`validate_arguments(schema, args)`** — hand-rolled mini-validator
   covering `required`, `additionalProperties: false`, and the four
   types we use (`string`, `integer`, `number`, plus implicit booleans
   that you must reject for the integer / number types).
4. **`call_tool(client, name, args)`** — wires the above together:
   look up the spec, validate the arguments, run the handler, and
   translate any `KeyError` / `TypeError` / `ValueError` from the
   handler into a `ToolError`. Let `ToolError` propagate as-is.

A subtle thing: Python's `bool` is a subclass of `int`. So
`isinstance(True, int) == True`. You almost certainly want to reject
`True`/`False` for `"type": "integer"` and `"type": "number"` — the
test `test_rejects_wrong_type` checks this with the literal value
`"three"`, but the principle generalises.

### Run the tests

```bash
pytest tests/test_tools.py -v
```

All 18 tests should pass.

### Why a separate dispatcher?

You might be tempted to write the per-tool logic directly inside the
MCP `call_tool` handler in Part 4 — it would be shorter. Don't. The
dispatcher is the seam where you can:

* unit-test tools without an MCP server in the loop (you've already
  seen this);
* expose the same tools through a *different* transport (HTTP, a CLI,
  a Slack bot) by reusing the dispatcher;
* add cross-cutting concerns (rate limiting, logging, metrics, auth)
  in one place.

A four-line saving in `call_tool` is not worth losing that.

---

## Part 4 — MCP server wiring (`server/server.py`)

### The problem

`mcp.server.Server` is the SDK's low-level server class. It speaks
JSON-RPC over a transport you supply, and dispatches to handlers you
register with decorators. To wire it up you need exactly two handlers:

```python
srv = Server("weather")

@srv.list_tools()
async def list_tools() -> list[Tool]:
    return [...]

@srv.call_tool()
async def call_tool(name: str, arguments: dict):
    return ...   # see below for the return-shape options
```

That's it. Everything else (the protocol framing, the initialization
handshake, capability negotiation) is handled by the SDK.

### Return-shape options

The SDK's `call_tool` accepts several return shapes:

| Returned object | Meaning |
| --------------- | ------- |
| `list[ContentBlock]` | success, unstructured content |
| `dict` | success, structured content (serialised to JSON) |
| `(list[ContentBlock], dict)` | both |
| `CallToolResult` | full control — including `isError=True` |

We use the **`CallToolResult`** form because we want to set
`isError=True` on `ToolError`s. The MCP client passes the content
through to the LLM in both cases; the difference is that with
`isError=True` the LLM is told "this call failed, try something else
or apologise."

### Your task

In `server/server.py`, implement three functions:

1. **`tools_for_protocol()`** — convert each `ToolSpec` in `TOOLS` to
   an `mcp.types.Tool`. Note the field name: `inputSchema` (camelCase)
   on `Tool`, vs `input_schema` (snake_case) on `ToolSpec`. That tiny
   asymmetry trips people up.
2. **`run_tool_as_content(client, name, arguments)`** — calls
   `server.tools.call_tool` and packages the result as
   `(content, is_error)`. On a `ToolError`, return a single
   `TextContent` whose text starts with `"Error: "` and contains the
   error message, plus `is_error=True`. This is the function the unit
   tests target directly.
3. **`build_server(client)`** — construct the `Server`, register both
   handlers, and return it. The `list_tools` handler returns
   `tools_for_protocol()`. The `call_tool` handler delegates to
   `run_tool_as_content` and wraps the pair in a `CallToolResult`.

A few practical notes:

* **Inject the client.** Production calls `build_server()` and lets you
  construct a default `OpenMeteoClient`. Tests can call
  `build_server(client=...)` with a fake — though the tests in this
  part don't bother, because `run_tool_as_content` takes the client
  directly and is more pleasant to test.
* **Never `print()` from a STDIO server.** Stdout is reserved for
  JSON-RPC frames. The `main.py` we ship configures `logging` to write
  to stderr — stick to `logger.info(...)`.
* **Don't catch `BaseException`.** Catching everything inside
  `run_tool_as_content` would swallow `KeyboardInterrupt` and make
  debugging miserable. Catch `ToolError` only; let the rest propagate
  so the SDK can produce a proper protocol-level error.

### Run the tests

```bash
pytest tests/test_server.py -v
```

All 8 tests should pass.

### Run the whole suite

```bash
pytest
```

You should now see:

```
tests/test_client.py     .....................  [ 42%]
tests/test_server.py     ........               [ 59%]
tests/test_tools.py      ....................   [100%]
======== 49 passed in 0.7s ========
```

---

## Part 5 — Run it against a real client

### Try it with the MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
is a small web UI that connects to a local MCP server and lets you
poke at it manually. It's by far the fastest way to verify your
server works end-to-end without dragging the LLM into the loop.

From `week3/`:

```bash
npx @modelcontextprotocol/inspector python -m server.main
```

Open the URL it prints, click **List Tools**, and you should see your
three tools. Pick `geocode_location`, fill in `{"name": "Berlin"}`,
and hit **Call Tool**. You should get back the rendered text result.

If you see *nothing* in the tool list, your `list_tools` handler isn't
registered. If the tool call hangs, your handler is probably blocking
the event loop (Open-Meteo down, network firewalled, etc.).

### Hook it into Claude Desktop

Edit (or create) `~/Library/Application Support/Claude/claude_desktop_config.json`
on macOS, or `%APPDATA%\Claude\claude_desktop_config.json` on Windows:

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

Restart Claude Desktop. The tools menu (paperclip icon) should now
list your three tools. Try the prompts below.

### Things to try

* **Ask a question your server answers.** "What's the weather in
  Berlin right now?" The model should call `geocode_location("Berlin")`,
  then `get_current_weather(52.52, 13.41)`, then summarise the result.
  Notice the multi-tool chain — that's the LLM stitching your tools
  together.
* **Ask a question your server can't answer.** "What's the weather on
  Mars?" The geocoder will return no matches; your `ToolError` should
  surface as `"Error: No matching location found."` and the model
  should apologise rather than hallucinate.
* **Force a timeout.** Block Open-Meteo at the firewall (or unplug
  your network) and try a query. Confirm the message you see is
  *your* timeout message and not a generic "tool failed" string —
  this is the payoff for centralising errors in `_get_json`.
* **Edit a tool description.** Change `get_current_weather`'s
  description to something tiny and unhelpful ("get weather"). Ask
  some questions and see how the model's tool-selection behaviour
  changes. Then put the original back.

---

## Part 6 — Stretch goals (optional)

These are not graded but make for good follow-up exploration:

* **Add a fourth tool.** Open-Meteo also exposes air quality at
  <https://air-quality-api.open-meteo.com/v1/air-quality>. Add an
  `OpenAirQualityClient` (or extend the existing one) and a
  `get_air_quality(latitude, longitude)` tool. Keep the error
  handling consistent.
* **Expose a resource.** Add an MCP **resource** that serves the
  WMO weather-code reference table at a URI like
  `weather://codes`. The MCP SDK has `@srv.list_resources()` and
  `@srv.read_resource()` decorators that mirror the tool ones.
* **Author a prompt template.** Add an MCP **prompt** called
  `travel_brief` that renders a fixed template (current weather +
  3-day forecast for a given city) given a `city` argument. Users
  pick it from the prompt menu in their MCP client.
* **Switch to HTTP transport.** Replace `stdio_server()` in
  `main.py` with the SDK's streamable-HTTP transport, expose the
  server on a port, and call it from `curl` and from an MCP-aware
  agent runtime. Mind the security: HTTP servers should validate
  the `Origin` header and bind to `127.0.0.1` unless you genuinely
  want network access.
* **Add API-key auth.** Wrap incoming requests with a check against
  an environment variable; reject unauthorised calls before they
  reach the handler. Only meaningful once you're on HTTP.

---

## Submission

* Make sure every test passes: `pytest` from `week3/`.
* Commit your filled-in versions of `client.py`, `tools.py`, and
  `server.py`.
* Run the server against Claude Desktop or the MCP Inspector and
  paste a screenshot (or transcript) of a successful tool call into
  `week3/README.md` under a "Demo" heading.
* Add a short note at the top of `server/server.py` summarising one
  observation from Part 5 (e.g. "the model chained geocode →
  current_weather automatically even though I never told it to —
  the schema was enough").

That is it — you have built a working MCP server from first
principles.
