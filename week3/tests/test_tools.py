"""Unit tests for server.tools (Part 3)."""

from __future__ import annotations

from typing import Any, Dict

import httpx
import pytest

from server.client import OpenMeteoClient
from server.tools import (
    TOOLS,
    call_tool,
    describe_weather_code,
    get_tool,
    validate_arguments,
)
from server.types import ToolError


# ---------- registry ---------------------------------------------------------

class TestToolRegistry:
    def test_three_tools_registered(self):
        names = {t.name for t in TOOLS}
        assert names == {"geocode_location", "get_current_weather", "get_forecast"}

    def test_each_tool_has_object_schema(self):
        for spec in TOOLS:
            assert spec.input_schema["type"] == "object"
            assert "properties" in spec.input_schema
            # Schemas should be strict so the LLM can't add stray fields.
            assert spec.input_schema.get("additionalProperties") is False

    def test_get_tool_returns_spec(self):
        spec = get_tool("geocode_location")
        assert spec.name == "geocode_location"

    def test_get_tool_unknown_raises(self):
        with pytest.raises(ToolError):
            get_tool("does_not_exist")


# ---------- validate_arguments ------------------------------------------------

class TestValidateArguments:
    SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer"},
            "factor": {"type": "number"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def test_accepts_valid(self):
        validate_arguments(self.SCHEMA, {"name": "x", "count": 3, "factor": 1.5})

    def test_rejects_missing_required(self):
        with pytest.raises(ToolError):
            validate_arguments(self.SCHEMA, {"count": 1})

    def test_rejects_unknown_field(self):
        with pytest.raises(ToolError):
            validate_arguments(self.SCHEMA, {"name": "x", "extra": 1})

    def test_rejects_wrong_type(self):
        with pytest.raises(ToolError):
            validate_arguments(self.SCHEMA, {"name": 123})
        with pytest.raises(ToolError):
            validate_arguments(self.SCHEMA, {"name": "x", "count": "three"})

    def test_number_accepts_int_or_float(self):
        validate_arguments(self.SCHEMA, {"name": "x", "factor": 1})
        validate_arguments(self.SCHEMA, {"name": "x", "factor": 1.5})


# ---------- describe_weather_code -------------------------------------------

class TestDescribeWeatherCode:
    def test_known_code(self):
        s = describe_weather_code(3)
        assert "Overcast" in s
        assert "3" in s

    def test_unknown_code_falls_back_to_number(self):
        s = describe_weather_code(999)
        assert "999" in s


# ---------- handlers ---------------------------------------------------------
#
# We drive these through call_tool() so we also exercise the dispatcher.

class FakeClient:
    """Stand-in for OpenMeteoClient that records the calls it received."""

    def __init__(self, **canned: Any) -> None:
        self.canned = canned
        self.calls: list[tuple[str, tuple, dict]] = []

    def _record(self, name: str, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        if name in self.canned:
            value = self.canned[name]
            if isinstance(value, Exception):
                raise value
            return value
        raise AssertionError(f"FakeClient got unexpected call: {name}")

    def geocode(self, name):
        return self._record("geocode", name)

    def get_current_weather(self, lat, lon):
        return self._record("get_current_weather", lat, lon)

    def get_forecast(self, lat, lon, days):
        return self._record("get_forecast", lat, lon, days)


def _fake_geocode():
    from server.types import GeocodeResult

    return GeocodeResult(name="Berlin", country="Germany", latitude=52.52, longitude=13.41)


def _fake_current():
    from server.types import CurrentWeather

    return CurrentWeather(
        temperature_c=7.3,
        wind_kph=12.5,
        weather_code=3,
        observed_at="2025-01-01T12:00",
    )


def _fake_forecast():
    from server.types import Forecast, ForecastDay

    return Forecast(
        days=[
            ForecastDay("2025-01-01", 9.1, 2.0, 0.0, 3),
            ForecastDay("2025-01-02", 8.4, 1.2, 1.3, 61),
        ]
    )


class TestCallToolGeocode:
    def test_renders_name_country_and_coords(self):
        client = FakeClient(geocode=_fake_geocode())
        out = call_tool(client, "geocode_location", {"name": "Berlin"})
        assert "Berlin" in out
        assert "Germany" in out
        assert "52.52" in out
        assert "13.41" in out

    def test_forwards_name_to_client(self):
        client = FakeClient(geocode=_fake_geocode())
        call_tool(client, "geocode_location", {"name": "Berlin"})
        assert client.calls == [("geocode", ("Berlin",), {})]

    def test_missing_arg_raises(self):
        client = FakeClient()
        with pytest.raises(ToolError):
            call_tool(client, "geocode_location", {})

    def test_extra_arg_raises(self):
        client = FakeClient()
        with pytest.raises(ToolError):
            call_tool(client, "geocode_location", {"name": "x", "extra": 1})


class TestCallToolCurrentWeather:
    def test_renders_temperature_and_conditions(self):
        client = FakeClient(get_current_weather=_fake_current())
        out = call_tool(
            client,
            "get_current_weather",
            {"latitude": 52.52, "longitude": 13.41},
        )
        assert "7.3" in out
        assert "12.5" in out
        assert "Overcast" in out  # via describe_weather_code(3)

    def test_forwards_coords_to_client(self):
        client = FakeClient(get_current_weather=_fake_current())
        call_tool(
            client,
            "get_current_weather",
            {"latitude": 52.52, "longitude": 13.41},
        )
        assert client.calls == [("get_current_weather", (52.52, 13.41), {})]


class TestCallToolForecast:
    def test_renders_every_day(self):
        client = FakeClient(get_forecast=_fake_forecast())
        out = call_tool(
            client,
            "get_forecast",
            {"latitude": 52.52, "longitude": 13.41, "days": 2},
        )
        assert "2025-01-01" in out
        assert "2025-01-02" in out
        assert "9.1" in out  # max temp day 1
        assert "1.2" in out  # min temp day 2

    def test_propagates_upstream_tool_error(self):
        client = FakeClient(get_forecast=ToolError("upstream is down"))
        with pytest.raises(ToolError) as exc_info:
            call_tool(
                client,
                "get_forecast",
                {"latitude": 0.0, "longitude": 0.0, "days": 3},
            )
        assert "upstream is down" in str(exc_info.value)


class TestCallToolUnknownName:
    def test_unknown_tool_raises(self):
        client = FakeClient()
        with pytest.raises(ToolError):
            call_tool(client, "not_a_real_tool", {})
