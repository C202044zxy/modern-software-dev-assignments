"""Unit tests for server.client (Part 2)."""

from __future__ import annotations

import httpx
import pytest
from server.client import (
    parse_current_weather,
    parse_forecast,
    parse_geocode_response,
)
from server.types import CurrentWeather, ForecastDay, ToolError

# ---------- response parsers --------------------------------------------------


class TestParseGeocodeResponse:
    def test_returns_first_match(self, berlin_geocode_payload):
        result = parse_geocode_response(berlin_geocode_payload)
        assert result.name == "Berlin"
        assert result.country == "Germany"
        assert result.latitude == pytest.approx(52.52)
        assert result.longitude == pytest.approx(13.41)

    def test_raises_when_no_results_key(self):
        with pytest.raises(ToolError):
            parse_geocode_response({"generationtime_ms": 0.7})

    def test_raises_when_results_empty(self):
        with pytest.raises(ToolError):
            parse_geocode_response({"results": []})


class TestParseCurrentWeather:
    def test_returns_current_block(self, berlin_current_payload):
        cw = parse_current_weather(berlin_current_payload)
        assert isinstance(cw, CurrentWeather)
        assert cw.temperature_c == pytest.approx(7.3)
        assert cw.wind_kph == pytest.approx(12.5)
        assert cw.weather_code == 3
        assert cw.observed_at == "2025-01-01T12:00"

    def test_raises_when_current_missing(self):
        with pytest.raises(ToolError):
            parse_current_weather({"latitude": 0.0, "longitude": 0.0})


class TestParseForecast:
    def test_zips_parallel_arrays(self, berlin_forecast_payload):
        fc = parse_forecast(berlin_forecast_payload)
        assert len(fc.days) == 3
        first = fc.days[0]
        assert isinstance(first, ForecastDay)
        assert first.date == "2025-01-01"
        assert first.temp_max_c == pytest.approx(9.1)
        assert first.temp_min_c == pytest.approx(2.0)
        assert first.precipitation_mm == pytest.approx(0.0)
        assert first.weather_code == 3
        assert fc.days[-1].date == "2025-01-03"

    def test_raises_when_daily_missing(self):
        with pytest.raises(ToolError):
            parse_forecast({"latitude": 0.0, "longitude": 0.0})

    def test_raises_when_arrays_unaligned(self):
        bad = {
            "daily": {
                "time": ["2025-01-01", "2025-01-02"],
                "temperature_2m_max": [9.1],
                "temperature_2m_min": [2.0, 1.2],
                "precipitation_sum": [0.0, 1.3],
                "weather_code": [3, 61],
            }
        }
        with pytest.raises(ToolError):
            parse_forecast(bad)


# ---------- OpenMeteoClient.geocode ------------------------------------------


class TestClientGeocode:
    def test_returns_first_match(self, mock_client, mock_router, berlin_geocode_payload):
        mock_router[("GET", "/v1/search")] = lambda req: httpx.Response(
            200, json=berlin_geocode_payload
        )
        result = mock_client.geocode("Berlin")
        assert result.country == "Germany"

    def test_sends_name_as_query_param(self, mock_client, mock_router, berlin_geocode_payload):
        seen = {}

        def handler(req):
            seen["name"] = req.url.params.get("name")
            return httpx.Response(200, json=berlin_geocode_payload)

        mock_router[("GET", "/v1/search")] = handler
        mock_client.geocode("Berlin")
        assert seen["name"] == "Berlin"

    def test_empty_name_raises(self, mock_client):
        with pytest.raises(ToolError):
            mock_client.geocode("")
        with pytest.raises(ToolError):
            mock_client.geocode("   ")

    def test_no_results_raises(self, mock_client, mock_router):
        mock_router[("GET", "/v1/search")] = lambda req: httpx.Response(200, json={"results": []})
        with pytest.raises(ToolError):
            mock_client.geocode("Nowhereville")

    def test_http_error_raises_tool_error(self, mock_client, mock_router):
        mock_router[("GET", "/v1/search")] = lambda req: httpx.Response(500, text="boom")
        with pytest.raises(ToolError):
            mock_client.geocode("Berlin")

    def test_timeout_raises_tool_error(self, mock_client, mock_router):
        def handler(req):
            raise httpx.ReadTimeout("timed out", request=req)

        mock_router[("GET", "/v1/search")] = handler
        with pytest.raises(ToolError):
            mock_client.geocode("Berlin")

    def test_rate_limit_raises_tool_error(self, mock_client, mock_router):
        mock_router[("GET", "/v1/search")] = lambda req: httpx.Response(429, text="slow down")
        with pytest.raises(ToolError):
            mock_client.geocode("Berlin")


# ---------- OpenMeteoClient.get_current_weather ------------------------------


class TestClientCurrentWeather:
    def test_happy_path(self, mock_client, mock_router, berlin_current_payload):
        mock_router[("GET", "/v1/forecast")] = lambda req: httpx.Response(
            200, json=berlin_current_payload
        )
        cw = mock_client.get_current_weather(52.52, 13.41)
        assert cw.temperature_c == pytest.approx(7.3)

    def test_sends_coordinates_as_query_params(
        self, mock_client, mock_router, berlin_current_payload
    ):
        seen = {}

        def handler(req):
            seen["lat"] = req.url.params.get("latitude")
            seen["lon"] = req.url.params.get("longitude")
            seen["current"] = req.url.params.get("current")
            return httpx.Response(200, json=berlin_current_payload)

        mock_router[("GET", "/v1/forecast")] = handler
        mock_client.get_current_weather(52.52, 13.41)
        assert seen["lat"] == "52.52"
        assert seen["lon"] == "13.41"
        # The request must ask for at least the three current-weather fields.
        assert "temperature_2m" in seen["current"]
        assert "wind_speed_10m" in seen["current"]
        assert "weather_code" in seen["current"]

    def test_http_error_raises_tool_error(self, mock_client, mock_router):
        mock_router[("GET", "/v1/forecast")] = lambda req: httpx.Response(500)
        with pytest.raises(ToolError):
            mock_client.get_current_weather(0.0, 0.0)


# ---------- OpenMeteoClient.get_forecast -------------------------------------


class TestClientForecast:
    def test_happy_path(self, mock_client, mock_router, berlin_forecast_payload):
        mock_router[("GET", "/v1/forecast")] = lambda req: httpx.Response(
            200, json=berlin_forecast_payload
        )
        fc = mock_client.get_forecast(52.52, 13.41, days=3)
        assert len(fc.days) == 3
        assert fc.days[1].date == "2025-01-02"

    def test_sends_days_param(self, mock_client, mock_router, berlin_forecast_payload):
        seen = {}

        def handler(req):
            seen["days"] = req.url.params.get("forecast_days")
            seen["daily"] = req.url.params.get("daily")
            return httpx.Response(200, json=berlin_forecast_payload)

        mock_router[("GET", "/v1/forecast")] = handler
        mock_client.get_forecast(0.0, 0.0, days=3)
        assert seen["days"] == "3"
        assert "temperature_2m_max" in seen["daily"]

    def test_invalid_days_raises(self, mock_client):
        with pytest.raises(ToolError):
            mock_client.get_forecast(0.0, 0.0, days=0)
        with pytest.raises(ToolError):
            mock_client.get_forecast(0.0, 0.0, days=100)
