"""MCP tool definitions and dispatch.

An MCP tool has three parts:

1. A **name** (``"get_current_weather"``).
2. A **description** the LLM reads to decide *whether to call it*.
3. An **input schema** — a JSON Schema object describing the arguments.

The runtime needs to know the set of available tools (so it can advertise
them in ``list_tools``) and how to actually run them (so it can answer
``call_tool``). This module is where we expose both.

Design:

* :class:`ToolSpec` bundles a tool's advertised metadata with the Python
  function that implements it.
* ``TOOLS`` is the module-level registry — a single source of truth that
  both ``list_tools`` and ``call_tool`` read from.
* :func:`call_tool` looks up the handler by name and runs it. It also
  performs basic input validation so handlers don't have to re-check the
  same things over and over.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from server.client import OpenMeteoClient
from server.types import ToolError


# ---------- registry types --------------------------------------------------

# Handlers take an ``OpenMeteoClient`` and the already-validated arguments
# dict, and return a *plain string* — the user-facing rendering of the tool
# result. (We let the MCP transport layer wrap that string in the protocol's
# content envelope; see ``server/server.py``.)
ToolHandler = Callable[[OpenMeteoClient, Dict[str, Any]], str]


@dataclass(frozen=True)
class ToolSpec:
    """A self-contained description of one MCP tool.

    Attributes:
        name: Stable identifier the LLM uses to invoke the tool.
        description: Plain-English explanation of what the tool does. The LLM
            reads this during tool selection, so write it as if briefing a
            colleague who has never seen the API.
        input_schema: A JSON Schema object describing the arguments. Use
            ``"type": "object"``, name each property, and list the required
            keys. Keep it strict (``"additionalProperties": false``) so the
            model can't sneak free-form fields in.
        handler: The Python function that actually runs the tool.
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: ToolHandler


# ---------- tool handlers ---------------------------------------------------
#
# Each handler implements one tool. Conventions:
#
# * Trust the keys in ``args`` to exist — :func:`call_tool` validates them
#   against the schema before calling you.
# * Raise :class:`~server.types.ToolError` for user-facing failures (bad
#   inputs that schema validation didn't catch, upstream errors bubbling
#   up from the client, ...). The dispatcher converts these into MCP error
#   results.
# * Return a *string*. Format it the way you'd want to read it in a chat:
#   short, human-friendly, no JSON.


def handle_geocode_location(client: OpenMeteoClient, args: Dict[str, Any]) -> str:
    """Run the ``geocode_location`` tool.

    Expected ``args``::

        {"name": "Berlin"}

    A reasonable rendering::

        Berlin, Germany — 52.52°N, 13.41°E
    """
    result = client.geocode(args["name"])
    return f"{result.name}, {result.country} — {result.latitude}°N, {result.longitude}°E"


def handle_get_current_weather(client: OpenMeteoClient, args: Dict[str, Any]) -> str:
    """Run the ``get_current_weather`` tool.

    Expected ``args``::

        {"latitude": 52.52, "longitude": 13.41}

    A reasonable rendering::

        Current weather at 52.52, 13.41 (as of 2025-01-01T12:00):
          Temperature: 7.3 °C
          Wind:        12.5 km/h
          Conditions:  Overcast (weather code 3)
    """
    latitude = args["latitude"]
    longitude = args["longitude"]
    result = client.get_current_weather(latitude, longitude)

    weather_str = describe_weather_code(result.weather_code)
    return (
        f"Current weather at {latitude}, {longitude} (as of {result.observed_at}):\n"
        f"  Temperature: {result.temperature_c} °C\n"
        f"  Wind: {result.wind_kph} km/h\n"
        f"  Conditions: {weather_str}"
    )


def handle_get_forecast(client: OpenMeteoClient, args: Dict[str, Any]) -> str:
    """Run the ``get_forecast`` tool.

    Expected ``args``::

        {"latitude": 52.52, "longitude": 13.41, "days": 3}

    A reasonable rendering::

        3-day forecast at 52.52, 13.41:
          2025-01-01: 2.0–9.1 °C, 0.0 mm precip, code 3
          2025-01-02: 1.2–8.4 °C, 1.3 mm precip, code 61
          ...
    """
    latitude = args["latitude"]
    longitude = args["longitude"]
    days = args["days"]

    result = client.get_forecast(latitude, longitude, days)
    forecast_str = "\n".join(
        (
            f"  {day.date}: {day.temp_min_c}-{day.temp_max_c} °C, "
            f"{day.precipitation_mm} mm precip, code {day.weather_code}"
        )
        for day in result.days
    )
    return f"{days}-day forecast at {latitude}, {longitude}:\n{forecast_str}"


# ---------- weather-code helper --------------------------------------------

# Friendly labels for a handful of common WMO weather codes. You don't need
# to cover them all — fall back to the bare code for anything missing.
WEATHER_CODE_LABELS: Dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


def describe_weather_code(code: int) -> str:
    """Return ``"<label> (weather code <n>)"`` if known, else just the code."""
    label = WEATHER_CODE_LABELS.get(code)
    if label is None:
        return f"weather code {code}"
    return f"{label} (weather code {code})"


# ---------- the registry ----------------------------------------------------

TOOLS: List[ToolSpec] = [
    ToolSpec(
        name="geocode_location",
        description=(
            "Resolve a free-form place name (e.g. 'Berlin', 'San Francisco') to "
            "its canonical name, country, and latitude/longitude. Use this first "
            "if the user gives a place name and you need coordinates for the "
            "weather tools."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Free-form place name. Must be non-empty.",
                    "minLength": 1,
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=handle_geocode_location,
    ),
    ToolSpec(
        name="get_current_weather",
        description=(
            "Get the current weather (temperature, wind, conditions) at a "
            "latitude/longitude. Coordinates can be obtained from "
            "geocode_location."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
            },
            "required": ["latitude", "longitude"],
            "additionalProperties": False,
        },
        handler=handle_get_current_weather,
    ),
    ToolSpec(
        name="get_forecast",
        description=(
            "Get a daily weather forecast for the next ``days`` days at a "
            "latitude/longitude. Each day reports high/low temperature, total "
            "precipitation, and a weather condition code."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                "days": {"type": "integer", "minimum": 1, "maximum": 16},
            },
            "required": ["latitude", "longitude", "days"],
            "additionalProperties": False,
        },
        handler=handle_get_forecast,
    ),
]


def get_tool(name: str) -> ToolSpec:
    """Look up a tool by name, or raise :class:`ToolError` if unknown."""
    for tool in TOOLS:
        if tool.name == name:
            return tool
    raise ToolError(f"tool {name} not found")


def call_tool(client: OpenMeteoClient, name: str, arguments: Dict[str, Any]) -> str:
    """Invoke a registered tool by name.

    The dispatcher is responsible for:

    1. Looking the tool up by name (delegating to :func:`get_tool`).
    2. Validating ``arguments`` against the tool's ``input_schema``
       (delegating to :func:`validate_arguments`).
    3. Calling the tool's handler with ``client`` and ``arguments``.
    4. Translating bare ``KeyError``/``TypeError``/``ValueError`` from the
       handler into :class:`ToolError` — those almost always mean "bad
       input" and we want them reported to the caller, not crashed on.
       Let :class:`ToolError` and anything else propagate as-is.

    Returns the handler's string result.
    """
    tool = get_tool(name)
    validate_arguments(tool.input_schema, arguments)
    return tool.handler(client, arguments)


def validate_arguments(schema: Dict[str, Any], arguments: Dict[str, Any]) -> None:
    """Light-weight schema validator.

    We don't pull in ``jsonschema`` — instead we hand-check the subset of
    JSON Schema features our tool schemas actually use:

    * Every key in ``schema["required"]`` is present in ``arguments``.
    * No key in ``arguments`` is missing from ``schema["properties"]``
      (because every schema we ship has ``"additionalProperties": false``).
    * Every value's Python type matches the declared JSON-Schema ``"type"``
      (``"string"`` -> ``str``, ``"integer"`` -> ``int``, ``"number"`` ->
      ``int`` or ``float``).

    On any violation raise :class:`ToolError` with a message that names the
    offending field.

    You can ignore ``minimum``/``maximum``/``minLength`` — those are advisory
    for the LLM, and the handlers (or the upstream API) will reject truly
    invalid values.
    """
    required_keys = schema["required"]
    for required_key in required_keys:
        if required_key not in arguments:
            raise ToolError(f"{required_key} is required")

    properties = schema["properties"]
    for key, value in arguments.items():
        if key not in properties:
            raise ToolError(f"{key} should not be prompted")

        type = properties[key]["type"]
        match type:
            case "string":
                if not isinstance(value, str):
                    raise ToolError(f"{key} should be string, but {value} prompted")
            case "integer":
                if not isinstance(value, int):
                    raise ToolError(f"{key} should be int, but {value} prompted")
            case "number":
                if not isinstance(value, int) and not isinstance(value, float):
                    raise ToolError(f"{key} should be int or float, but {value} prompted")


__all__ = [
    "ToolSpec",
    "TOOLS",
    "get_tool",
    "call_tool",
    "validate_arguments",
    "describe_weather_code",
]
