"""Shared fixtures.

Two responsibilities:

* Make ``import server.*`` work when pytest is invoked from the repo root.
* Provide an :class:`httpx.MockTransport` based fixture so client tests
  don't touch the real network. The handler is registered per-test by
  setting ``mock_router[(method, path)] = response``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, Tuple

import httpx
import pytest

# Make ``import server.*`` work when pytest is invoked from the repo root.
_ASSIGNMENT_ROOT = Path(__file__).resolve().parent.parent
if str(_ASSIGNMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_ASSIGNMENT_ROOT))


# Imported AFTER sys.path is set up.
from server.client import OpenMeteoClient  # noqa: E402


RouterKey = Tuple[str, str]  # (method, path)
RouterFn = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def mock_router() -> Dict[RouterKey, RouterFn]:
    """A test-controlled dict mapping (method, path) -> handler.

    Tests register handlers like so::

        mock_router[("GET", "/v1/search")] = lambda req: httpx.Response(
            200, json={"results": [...]}
        )
    """
    return {}


@pytest.fixture
def mock_client(monkeypatch: pytest.MonkeyPatch, mock_router) -> OpenMeteoClient:
    """An :class:`OpenMeteoClient` whose HTTP transport is in-process.

    Internally we patch the ``httpx.Client`` instance attribute to use an
    :class:`httpx.MockTransport`. Tests get a real, fully-formed client —
    they just never reach the public internet.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        fn = mock_router.get(key)
        if fn is None:
            return httpx.Response(404, text=f"no mock for {key!r}")
        return fn(request)

    client = OpenMeteoClient(
        geocode_url="https://mock-geocode/v1/search",
        forecast_url="https://mock-forecast/v1/forecast",
    )
    # Replace the internal httpx.Client with one wired to MockTransport.
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler), timeout=5.0)
    yield client
    client.close()


# ---------- canned payloads ------------------------------------------------

@pytest.fixture
def berlin_geocode_payload() -> dict:
    return {
        "results": [
            {
                "id": 1,
                "name": "Berlin",
                "country": "Germany",
                "latitude": 52.52,
                "longitude": 13.41,
                "admin1": "Berlin",
                "feature_code": "PPLC",
            },
            {
                "id": 2,
                "name": "Berlin",
                "country": "United States",
                "latitude": 44.47,
                "longitude": -71.18,
            },
        ],
        "generationtime_ms": 0.7,
    }


@pytest.fixture
def berlin_current_payload() -> dict:
    return {
        "latitude": 52.52,
        "longitude": 13.41,
        "current": {
            "time": "2025-01-01T12:00",
            "temperature_2m": 7.3,
            "wind_speed_10m": 12.5,
            "weather_code": 3,
        },
    }


@pytest.fixture
def berlin_forecast_payload() -> dict:
    return {
        "latitude": 52.52,
        "longitude": 13.41,
        "daily": {
            "time": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "temperature_2m_max": [9.1, 8.4, 5.0],
            "temperature_2m_min": [2.0, 1.2, -1.5],
            "precipitation_sum": [0.0, 1.3, 4.4],
            "weather_code": [3, 61, 71],
        },
    }
