"""Weather fetcher — uses Open-Meteo API (free, no key needed).

Returns current conditions + today's high/low for dashboard display.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass

from src.config import settings

logger = logging.getLogger(__name__)

# WMO Weather Code → short description + icon
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear", "☀"),
    1: ("Mostly Clear", "🌤"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁"),
    45: ("Foggy", "🌫"),
    48: ("Fog", "🌫"),
    51: ("Light Drizzle", "🌦"),
    53: ("Drizzle", "🌦"),
    55: ("Heavy Drizzle", "🌧"),
    61: ("Light Rain", "🌦"),
    63: ("Rain", "🌧"),
    65: ("Heavy Rain", "🌧"),
    71: ("Light Snow", "🌨"),
    73: ("Snow", "❄"),
    75: ("Heavy Snow", "❄"),
    77: ("Snow Grains", "❄"),
    80: ("Light Showers", "🌦"),
    81: ("Showers", "🌧"),
    82: ("Heavy Showers", "🌧"),
    85: ("Snow Showers", "🌨"),
    86: ("Heavy Snow Showers", "🌨"),
    95: ("Thunderstorm", "⛈"),
    96: ("Thunderstorm + Hail", "⛈"),
    99: ("Thunderstorm + Hail", "⛈"),
}

# For e-ink (no emoji), use text-only descriptions
WMO_EINK: dict[int, str] = {
    0: "CLEAR",
    1: "MOSTLY CLEAR",
    2: "PARTLY CLOUDY",
    3: "OVERCAST",
    45: "FOG",
    48: "FOG",
    51: "DRIZZLE",
    53: "DRIZZLE",
    55: "HEAVY DRIZZLE",
    61: "LIGHT RAIN",
    63: "RAIN",
    65: "HEAVY RAIN",
    71: "LIGHT SNOW",
    73: "SNOW",
    75: "HEAVY SNOW",
    77: "SNOW",
    80: "SHOWERS",
    81: "SHOWERS",
    82: "HEAVY SHOWERS",
    85: "SNOW SHOWERS",
    86: "SNOW SHOWERS",
    95: "THUNDERSTORM",
    96: "THUNDERSTORM",
    99: "THUNDERSTORM",
}


@dataclass
class Weather:
    temp_current: int          # °F
    temp_high: int             # °F today
    temp_low: int              # °F today
    description: str           # "Partly Cloudy"
    description_short: str     # "PARTLY CLOUDY" (for e-ink label)
    wind_mph: int              # wind speed
    humidity: int              # %
    weather_code: int


def fetch_weather() -> Weather | None:
    """Fetch current weather from Open-Meteo API.

    Uses Seattle coordinates by default. Configure via WEATHER_LAT/WEATHER_LON env vars.
    """
    lat = getattr(settings, 'weather_lat', 47.61)   # Seattle default
    lon = getattr(settings, 'weather_lon', -122.33)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&temperature_unit=fahrenheit"
        f"&wind_speed_unit=mph"
        f"&timezone=auto"
        f"&forecast_days=1"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kindle-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        logger.error(f"Weather fetch failed: {e}")
        return None

    try:
        current = data["current"]
        daily = data["daily"]
        code = current.get("weather_code", 0)

        return Weather(
            temp_current=round(current["temperature_2m"]),
            temp_high=round(daily["temperature_2m_max"][0]),
            temp_low=round(daily["temperature_2m_min"][0]),
            description=WMO_CODES.get(code, ("Unknown", "?"))[0],
            description_short=WMO_EINK.get(code, "UNKNOWN"),
            wind_mph=round(current.get("wind_speed_10m", 0)),
            humidity=round(current.get("relative_humidity_2m", 0)),
            weather_code=code,
        )
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Weather parse failed: {e}")
        return None
