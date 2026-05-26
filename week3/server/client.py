"""HTTP client for the Open-Meteo weather API.

Open-Meteo is a free, no-key weather API. We use two of its endpoints:

* Geocoding: ``https://geocoding-api.open-meteo.com/v1/search``
* Forecast:  ``https://api.open-meteo.com/v1/forecast``

This module is the **upstream-facing seam** of the server. Every other module
should go through :class:`OpenMeteoClient` and never call ``httpx`` directly.
That way, when we want to test the higher layers, we only have to fake out
*this* class instead of patching the network globally.

Implementation rules:

* Use :class:`httpx.Client` (synchronous). Construct it once and keep it as
  an attribute so connection pooling works across calls.
* On a non-2xx response, on a timeout, or on a connection failure, raise
  :class:`~server.types.ToolError` with a short, user-readable message.
  **Do not** let raw ``httpx`` exceptions bubble up to callers.
* On an empty result (e.g. the geocoder returns no matches), raise
  :class:`ToolError` — empty is a *semantic* error from the user's point of
  view, even though it's a perfectly valid 200 OK from the server.
* The default request timeout is 10 seconds. The base URLs are class
  constants so tests can override them.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from server.types import (
    CurrentWeather,
    Forecast,
    ForecastDay,
    GeocodeResult,
    ToolError,
)


class OpenMeteoClient:
    """Wraps the two Open-Meteo endpoints we need.

    The base URLs are exposed as instance attributes so tests can point the
    client at an in-process mock server (see ``tests/conftest.py``).
    """

    DEFAULT_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    DEFAULT_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(
        self,
        *,
        geocode_url: str | None = None,
        forecast_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.geocode_url = geocode_url or self.DEFAULT_GEOCODE_URL
        self.forecast_url = forecast_url or self.DEFAULT_FORECAST_URL
        self._client = httpx.Client(timeout=timeout)

    # ----- public API ----------------------------------------------------

    def geocode(self, name: str) -> GeocodeResult:
        """Resolve a place name to a single best lat/lon match.

        Args:
            name: A free-form place name (e.g. ``"Tokyo"``, ``"São Paulo"``).
                Must be non-empty after stripping whitespace.

        Returns:
            The first (highest-confidence) match returned by Open-Meteo.

        Raises:
            ToolError: If ``name`` is empty/whitespace, if the API call fails,
                or if no matches are found.
        """
        raise NotImplementedError("Part 2: implement OpenMeteoClient.geocode")

    def get_current_weather(self, latitude: float, longitude: float) -> CurrentWeather:
        """Fetch the current weather at the given coordinate.

        Hit the forecast endpoint with::

            current=temperature_2m,wind_speed_10m,weather_code

        Args:
            latitude: -90 .. 90.
            longitude: -180 .. 180.

        Returns:
            A :class:`CurrentWeather` filled in from the ``current`` block of
            the response.

        Raises:
            ToolError: On any HTTP/transport error, or if the ``current`` block
                is missing from the response.
        """
        raise NotImplementedError("Part 2: implement OpenMeteoClient.get_current_weather")

    def get_forecast(self, latitude: float, longitude: float, days: int) -> Forecast:
        """Fetch a ``days``-day daily forecast.

        Hit the forecast endpoint with::

            daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code
            forecast_days=<days>

        Args:
            latitude: -90 .. 90.
            longitude: -180 .. 180.
            days: 1 .. 16 (Open-Meteo's cap).

        Returns:
            A :class:`Forecast` with one :class:`ForecastDay` per requested day.

        Raises:
            ToolError: On any HTTP/transport error, on ``days`` out of range,
                or if the ``daily`` block is missing from the response.
        """
        raise NotImplementedError("Part 2: implement OpenMeteoClient.get_forecast")

    # ----- helpers you may find useful -----------------------------------

    def _get_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET ``url`` with ``params`` and return the parsed JSON body.

        Converts every ``httpx`` failure mode and every non-2xx status into a
        :class:`ToolError` with a short message. You should use this from
        each of the three public methods above so error handling stays in
        one place.
        """
        raise NotImplementedError("Part 2: implement OpenMeteoClient._get_json")

    def close(self) -> None:
        """Close the underlying HTTP connection pool. Safe to call twice."""
        self._client.close()

    def __enter__(self) -> "OpenMeteoClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


# ---------- response parsers ------------------------------------------------
#
# We expose these as module-level functions (not methods) so the test suite
# can poke at them with synthetic dicts without instantiating the client.

def parse_geocode_response(payload: Dict[str, Any]) -> GeocodeResult:
    """Turn a geocoding response payload into a :class:`GeocodeResult`.

    Open-Meteo returns ``{"results": [{...}, ...]}`` on a hit, and
    ``{"generationtime_ms": ...}`` (no ``results`` key) on a miss.

    Raises:
        ToolError: If the payload contains no results.
    """
    raise NotImplementedError("Part 2: implement parse_geocode_response")


def parse_current_weather(payload: Dict[str, Any]) -> CurrentWeather:
    """Turn a forecast response with a ``current`` block into a :class:`CurrentWeather`.

    The ``current`` block looks like::

        {
            "time": "2025-01-01T12:00",
            "temperature_2m": 7.3,
            "wind_speed_10m": 12.5,
            "weather_code": 3
        }

    Raises:
        ToolError: If the payload has no ``current`` block.
    """
    raise NotImplementedError("Part 2: implement parse_current_weather")


def parse_forecast(payload: Dict[str, Any]) -> Forecast:
    """Turn a forecast response with a ``daily`` block into a :class:`Forecast`.

    The ``daily`` block is *column-oriented* — parallel arrays keyed by field
    name::

        "daily": {
            "time": ["2025-01-01", "2025-01-02"],
            "temperature_2m_max": [9.1, 8.4],
            "temperature_2m_min": [2.0, 1.2],
            "precipitation_sum": [0.0, 1.3],
            "weather_code": [3, 61]
        }

    You'll need to ``zip`` them into per-day rows.

    Raises:
        ToolError: If the payload has no ``daily`` block, or if the arrays
            are not all the same length.
    """
    raise NotImplementedError("Part 2: implement parse_forecast")


# Public re-exports so the rest of the package can `from server.client import X`.
__all__ = [
    "OpenMeteoClient",
    "parse_geocode_response",
    "parse_current_weather",
    "parse_forecast",
]


# A sentinel used by the tests; you can ignore it.
_UNUSED: List[str] = []
