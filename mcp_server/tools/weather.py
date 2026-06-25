"""
Weather tools for the Lawn Concierge MCP server.

Fetches current conditions and forecasts from OpenWeatherMap to support
watering schedule and lawn care recommendations.
"""

import os
import httpx
from typing import Any

# OpenWeatherMap free-tier API base URL
OWM_BASE = "https://api.openweathermap.org/data/2.5"


def _api_key() -> str:
    """Read the OpenWeatherMap API key from the environment."""
    key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not set. "
            "Get a free key at https://openweathermap.org/api"
        )
    return key


def _location_candidates(location: str) -> list[str]:
    """Build a list of OpenWeatherMap `q` query strings to try in order.

    OpenWeatherMap's geocoding only accepts 'City', 'City,CountryCode', or
    'City,StateCode,CountryCode' (US) — it does NOT accept 'City, ST' (state
    abbreviation without a country code), which is the natural way callers
    (including the LLM) phrase a US location. Try the literal input first,
    then fall back to US-qualified forms.
    """
    parts = [p.strip() for p in location.split(",") if p.strip()]
    candidates = [",".join(parts)] if parts else [location]

    if len(parts) == 2 and len(parts[1]) == 2:
        # Looks like "City, ST" — assume a US state abbreviation.
        candidates.append(f"{parts[0]},{parts[1]},US")
    if len(parts) >= 1:
        candidates.append(f"{parts[0]},US")

    seen: set[str] = set()
    deduped = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped


async def _get_with_location_fallback(
    client: httpx.AsyncClient, path: str, location: str, extra_params: dict
) -> dict:
    """GET an OWM endpoint, retrying with US-qualified location forms on 404."""
    last_error: httpx.HTTPStatusError | None = None
    for candidate in _location_candidates(location):
        resp = await client.get(path, params={"q": candidate, **extra_params})
        if resp.status_code == 404:
            last_error = httpx.HTTPStatusError(
                f"404 for location '{candidate}'", request=resp.request, response=resp
            )
            continue
        resp.raise_for_status()
        return resp.json()
    raise last_error or RuntimeError(f"No location candidates for '{location}'")


async def get_weather_forecast(location: str, days: int = 7) -> dict[str, Any]:
    """
    Fetch a multi-day weather forecast for a given location.

    Args:
        location: City name, optionally with state/country, e.g. 'Austin',
            'Austin, TX', or 'Austin,US'. US state abbreviations are handled
            automatically.
        days: Number of forecast days to return (1–7).

    Returns:
        dict with keys:
          - location: resolved city name and country
          - current: today's temperature (°F), humidity (%), rain_mm, description
          - forecast: list of daily summaries (date, high_f, low_f, rain_mm, description)
          - watering_advice: plain-language watering recommendation based on forecast
    """
    days = max(1, min(days, 7))

    async with httpx.AsyncClient(timeout=10) as client:
        current_data = await _get_with_location_fallback(
            client,
            f"{OWM_BASE}/weather",
            location,
            {"appid": _api_key(), "units": "imperial"},
        )
        forecast_data = await _get_with_location_fallback(
            client,
            f"{OWM_BASE}/forecast",
            location,
            {"appid": _api_key(), "units": "imperial", "cnt": days * 8},
        )

    # --- Parse current conditions ---
    current = {
        "temp_f": current_data["main"]["temp"],
        "humidity_pct": current_data["main"]["humidity"],
        "rain_mm": current_data.get("rain", {}).get("1h", 0.0),
        "description": current_data["weather"][0]["description"],
    }

    # --- Aggregate 3-hour slots into daily summaries ---
    from collections import defaultdict

    daily: dict[str, dict] = defaultdict(lambda: {"highs": [], "lows": [], "rain_mm": 0.0, "descriptions": []})
    for slot in forecast_data["list"]:
        date = slot["dt_txt"][:10]
        daily[date]["highs"].append(slot["main"]["temp_max"])
        daily[date]["lows"].append(slot["main"]["temp_min"])
        daily[date]["rain_mm"] += slot.get("rain", {}).get("3h", 0.0)
        daily[date]["descriptions"].append(slot["weather"][0]["description"])

    forecast = []
    for date, vals in list(daily.items())[:days]:
        forecast.append(
            {
                "date": date,
                "high_f": round(max(vals["highs"]), 1),
                "low_f": round(min(vals["lows"]), 1),
                "rain_mm": round(vals["rain_mm"], 2),
                "description": vals["descriptions"][len(vals["descriptions"]) // 2],
            }
        )

    # --- Generate plain-language watering advice ---
    total_rain = sum(d["rain_mm"] for d in forecast)
    if total_rain > 25:
        watering_advice = (
            f"Significant rain expected ({total_rain:.0f}mm over {days} days). "
            "Skip supplemental watering — natural rainfall should be sufficient."
        )
    elif total_rain > 10:
        watering_advice = (
            f"Moderate rain expected ({total_rain:.0f}mm over {days} days). "
            "Reduce watering frequency by half."
        )
    else:
        watering_advice = (
            f"Little to no rain expected ({total_rain:.0f}mm over {days} days). "
            "Maintain regular watering schedule."
        )

    return {
        "location": f"{current_data['name']}, {current_data['sys']['country']}",
        "current": current,
        "forecast": forecast,
        "watering_advice": watering_advice,
    }


async def get_current_conditions(location: str) -> dict[str, Any]:
    """
    Fetch current weather conditions for a location.

    Args:
        location: City name, optionally with state/country, e.g. 'Austin',
            'Austin, TX', or 'Austin,US'. US state abbreviations are handled
            automatically.

    Returns:
        dict with temp_f, humidity_pct, wind_mph, rain_mm, description.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        data = await _get_with_location_fallback(
            client,
            f"{OWM_BASE}/weather",
            location,
            {"appid": _api_key(), "units": "imperial"},
        )

    return {
        "location": f"{data['name']}, {data['sys']['country']}",
        "temp_f": data["main"]["temp"],
        "feels_like_f": data["main"]["feels_like"],
        "humidity_pct": data["main"]["humidity"],
        "wind_mph": round(data["wind"]["speed"], 1),
        "rain_mm": data.get("rain", {}).get("1h", 0.0),
        "description": data["weather"][0]["description"],
    }
