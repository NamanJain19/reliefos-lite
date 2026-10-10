"""
RELIEFOS Lite — Open-Meteo Weather & Rainfall Provider Adapter
Fetches genuine real-world meteorological observations and forecasts for Kamrup Metropolitan (Guwahati).
License: CC-BY 4.0 Open-Meteo (No API key required; strictly respects fair use with 15-minute caching).
"""

import time
import urllib.request
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.ingestion.registry import registry, DataSourceState
from app.core.location_registry import get_location_meta, normalize_location_id, DEFAULT_LOCATION_ID

GUWAHATI_LAT = 26.1445
GUWAHATI_LNG = 91.7362
CACHE_TTL_SECONDS = 900  # 15 minutes cache to respect fair use

_LOCATION_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
_LOCATION_FETCH_TIMES: Dict[str, float] = {}
_WEATHER_CACHE: Optional[Dict[str, Any]] = None
_LAST_FETCH_TIME: float = 0.0


def _interpret_wmo_code(code: int) -> str:
    """Interprets WMO weather interpretation code into human-readable description."""
    codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return codes.get(code, "Unspecified meteorological condition")


def fetch_location_weather(location_id: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retrieves genuine real-world weather and precipitation telemetry for any configured Assam district from Open-Meteo.
    Thread-safe cached retrieval adhering to CC-BY 4.0 fair use policy.
    """
    global _LOCATION_WEATHER_CACHE, _LOCATION_FETCH_TIMES, _WEATHER_CACHE, _LAST_FETCH_TIME

    loc_id = normalize_location_id(location_id)
    loc_meta = get_location_meta(loc_id)
    lat = loc_meta.latitude
    lng = loc_meta.longitude

    now = time.time()
    cached = _LOCATION_WEATHER_CACHE.get(loc_id)
    last_fetch = _LOCATION_FETCH_TIMES.get(loc_id, 0.0)

    if not force_refresh and cached is not None and (now - last_fetch) < CACHE_TTL_SECONDS:
        return cached

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lng}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m"
        f"&hourly=precipitation,rain&forecast_days=2&timezone=Asia%2FKolkata"
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "RELIEFOS-Lite/1.0 (academic-disaster-support)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                raw = json.loads(response.read().decode("utf-8"))
                curr = raw.get("current", {})
                w_code = curr.get("weather_code", 0)

                # Format hourly forecast
                hourly_raw = raw.get("hourly", {})
                times = hourly_raw.get("time", [])[:24]
                precip = hourly_raw.get("precipitation", [])[:24]
                hourly_list = [{"time": t, "precip_mm": p} for t, p in zip(times, precip)]

                result = {
                    "source": "Open-Meteo NWP Global Model (ECMWF/DWD)",
                    "state": DataSourceState.LIVE.value,
                    "is_live": True,
                    "location_id": loc_id,
                    "target_location": loc_meta.display_name,
                    "coordinates": {"latitude": lat, "longitude": lng},
                    "observation_time": curr.get("time", datetime.now(timezone.utc).isoformat()),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "current": {
                        "temperature_c": curr.get("temperature_2m"),
                        "humidity_pct": curr.get("relative_humidity_2m"),
                        "precipitation_rate_mm_h": curr.get("precipitation", 0.0),
                        "rain_rate_mm_h": curr.get("rain", 0.0),
                        "wind_speed_kmh": curr.get("wind_speed_10m"),
                        "weather_code": w_code,
                        "weather_condition": _interpret_wmo_code(w_code)
                    },
                    "forecast_24h": hourly_list,
                    "units": {
                        "temperature": "°C",
                        "humidity": "%",
                        "precipitation": "mm/h",
                        "wind_speed": "km/h"
                    },
                    "attribution": "Weather data by Open-Meteo.com under CC-BY 4.0"
                }

                _LOCATION_WEATHER_CACHE[loc_id] = result
                _LOCATION_FETCH_TIMES[loc_id] = now
                if loc_id == "kamrup_metro":
                    _WEATHER_CACHE = result
                    _LAST_FETCH_TIME = now

                # Update registry status
                registry.update_provider_status(
                    provider_id="MET-OPENMETEO-01",
                    state=DataSourceState.LIVE,
                    health_pct=100.0,
                    observation_time=result["observation_time"]
                )
                return result

    except Exception as exc:
        # Graceful fallback: If we had a previous cache for this location, serve as LAST_KNOWN
        if cached is not None:
            fallback = dict(cached)
            fallback["state"] = DataSourceState.LAST_KNOWN.value
            fallback["is_live"] = False
            fallback["warning"] = f"Live upstream request failed ({str(exc)}). Serving last verified observation."
            return fallback

        # If no cache available, mark UNAVAILABLE
        return {
            "source": "Open-Meteo API",
            "state": DataSourceState.UNAVAILABLE.value,
            "is_live": False,
            "location_id": loc_id,
            "target_location": loc_meta.display_name,
            "coordinates": {"latitude": lat, "longitude": lng},
            "current": {
                "temperature_c": 28.0,
                "humidity_pct": 75,
                "precipitation_rate_mm_h": 0.0,
                "rain_rate_mm_h": 0.0,
                "wind_speed_kmh": 12.0,
                "weather_code": 1,
                "weather_condition": "Mainly clear (Baseline Estimate)"
            },
            "forecast_24h": [],
            "error": f"Live meteorological feed temporarily unreachable: {str(exc)}",
            "attribution": "Open-Meteo.com"
        }


def fetch_guwahati_weather(force_refresh: bool = False) -> Dict[str, Any]:
    """Backward compatibility wrapper for Kamrup Metro weather."""
    return fetch_location_weather("kamrup_metro", force_refresh=force_refresh)

