"""Shared data classes and the ToolError exception.

These are intentionally simple containers — no behaviour, just data. Every
other module in the package consumes or produces one of these types, so they
form the "vocabulary" of the server.

You do not need to modify this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class GeocodeResult:
    """The single best match returned by the Open-Meteo geocoding API.

    Attributes:
        name: The canonical place name (e.g. ``"Berlin"``).
        country: The country name (e.g. ``"Germany"``).
        latitude: Decimal degrees, north-positive.
        longitude: Decimal degrees, east-positive.
    """

    name: str
    country: str
    latitude: float
    longitude: float


@dataclass
class CurrentWeather:
    """A snapshot of the current weather at a coordinate.

    Attributes:
        temperature_c: Air temperature at 2 m, in degrees Celsius.
        wind_kph: Wind speed at 10 m, in kilometres per hour.
        weather_code: WMO weather interpretation code (0 = clear, 95 = thunder, ...).
        observed_at: ISO-8601 timestamp of the observation, as reported by the API.
    """

    temperature_c: float
    wind_kph: float
    weather_code: int
    observed_at: str


@dataclass
class ForecastDay:
    """One day in a multi-day forecast.

    Attributes:
        date: ISO date ``"YYYY-MM-DD"``.
        temp_max_c: Daily maximum temperature at 2 m, in degrees Celsius.
        temp_min_c: Daily minimum temperature at 2 m, in degrees Celsius.
        precipitation_mm: Total precipitation, in millimetres.
        weather_code: WMO weather interpretation code for the day.
    """

    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    weather_code: int


@dataclass
class Forecast:
    """A list of forecast days for one location."""

    days: List[ForecastDay]


class ToolError(Exception):
    """Raised by client / tool code to signal a user-facing failure.

    The MCP server catches this and translates it into a tool-result with
    ``isError=True`` so the LLM (and the user) can see *why* a call failed —
    rather than the whole server crashing.

    Use this for upstream errors that we *expect* and want to surface cleanly:
    timeouts, 4xx/5xx responses, empty results, rate limits. Do **not** use it
    to mask programmer bugs — let those raise normal Python exceptions so the
    test suite catches them.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
