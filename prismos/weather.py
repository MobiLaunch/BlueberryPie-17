"""Optional weather for the Weather widget, from Open-Meteo (no account or key).

Nothing is requested until the user picks a place in Settings. Only the chosen
coordinates (and a city name when searching) leave the machine, over HTTPS to two
fixed hosts. Results are cached for 15 minutes to keep requests rare.
"""
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import settings

FORECAST = "https://api.open-meteo.com/v1/forecast"
GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
CACHE_SECONDS = 900
MAX_BYTES = 128 * 1024
# WMO weather interpretation codes -> (summary, icon)
CODES = {0: ("Clear", "sun"), 1: ("Mostly clear", "sun"), 2: ("Partly cloudy", "partly_cloudy"), 3: ("Overcast", "cloud"),
         45: ("Fog", "fog"), 48: ("Freezing fog", "fog"), 51: ("Light drizzle", "rain"), 53: ("Drizzle", "rain"),
         55: ("Heavy drizzle", "rain"), 56: ("Freezing drizzle", "rain"), 57: ("Freezing drizzle", "rain"),
         61: ("Light rain", "rain"), 63: ("Rain", "rain"), 65: ("Heavy rain", "rain"), 66: ("Freezing rain", "rain"),
         67: ("Freezing rain", "rain"), 71: ("Light snow", "snow"), 73: ("Snow", "snow"), 75: ("Heavy snow", "snow"),
         77: ("Snow grains", "snow"), 80: ("Rain showers", "rain"), 81: ("Rain showers", "rain"),
         82: ("Violent showers", "rain"), 85: ("Snow showers", "snow"), 86: ("Snow showers", "snow"),
         95: ("Thunderstorm", "bolt"), 96: ("Thunderstorm with hail", "bolt"), 99: ("Thunderstorm with hail", "bolt")}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(url):
    """HTTPS GET of a fixed host, size-bounded, redirects refused."""
    if not url.startswith(("https://api.open-meteo.com/", "https://geocoding-api.open-meteo.com/")):
        raise ValueError("Unexpected weather host")
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "PrismOS-weather/0.9"})
    with opener.open(request, timeout=6) as reply:
        data = reply.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Weather reply was too large")
    return data


def _number(value, low, high, name):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name}") from None
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"Invalid {name}")
    return round(number, 4)


def _label(value):
    text = " ".join(str(value or "").split())[:60]
    if not text or any(ord(ch) < 32 for ch in text):
        raise ValueError("Choose a place name")
    return text


def search(name):
    text = " ".join(str(name or "").split())[:80]
    if len(text) < 2:
        raise ValueError("Type at least two letters")
    query = urllib.parse.urlencode({"name": text, "count": 6, "language": "en", "format": "json"})
    try:
        payload = json.loads(fetch(f"{GEOCODING}?{query}"))
    except (OSError, ValueError, urllib.error.URLError) as error:
        return {"ok": False, "error": "Could not search for places. Check your connection."}
    places = []
    for item in payload.get("results") or []:
        try:
            label = ", ".join(part for part in (item.get("name"), item.get("admin1"), item.get("country")) if part)
            places.append({"label": _label(label), "lat": _number(item["latitude"], -90, 90, "latitude"),
                           "lon": _number(item["longitude"], -180, 180, "longitude")})
        except (KeyError, ValueError):
            continue
    return {"ok": True, "places": places}


def configuration():
    saved = settings.load()["weather"]
    return saved if saved else None


def choose(lat, lon, label, units="metric"):
    if units not in ("metric", "imperial"):
        raise ValueError("Unknown units")
    value = {"lat": _number(lat, -90, 90, "latitude"), "lon": _number(lon, -180, 180, "longitude"),
             "label": _label(label), "units": units}
    settings.update(weather=value)
    _cache_path().unlink(missing_ok=True)
    return {"ok": True, "weather": value}


def disable():
    settings.update(weather={})
    _cache_path().unlink(missing_ok=True)
    return {"ok": True, "weather": None}


def _cache_path():
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "prismos/weather.json"


def current(now=None):
    config = configuration()
    if config is None:
        return {"ok": True, "configured": False}
    now = time.time() if now is None else now
    path = _cache_path()
    try:
        cached = json.loads(path.read_text())
        if cached.get("config") == config and now - cached["at"] < CACHE_SECONDS:
            return {**cached["result"], "cached": True}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    unit = "fahrenheit" if config["units"] == "imperial" else "celsius"
    query = urllib.parse.urlencode({
        "latitude": config["lat"], "longitude": config["lon"], "timezone": "auto", "temperature_unit": unit,
        "current": "temperature_2m,apparent_temperature,weather_code,is_day",
        "daily": "temperature_2m_max,temperature_2m_min", "forecast_days": 1})
    try:
        payload = json.loads(fetch(f"{FORECAST}?{query}"))
        now_data, daily = payload["current"], payload["daily"]
        code = int(now_data["weather_code"])
        summary, icon = CODES.get(code, ("Unknown", "cloud"))
        if icon == "sun" and not now_data.get("is_day", 1):
            icon = "moon"
        result = {"ok": True, "configured": True, "label": config["label"], "units": config["units"],
                  "temperature": round(float(now_data["temperature_2m"])),
                  "feels_like": round(float(now_data["apparent_temperature"])),
                  "high": round(float(daily["temperature_2m_max"][0])), "low": round(float(daily["temperature_2m_min"][0])),
                  "summary": summary, "icon": icon}
    except (OSError, ValueError, KeyError, IndexError, TypeError, urllib.error.URLError):
        return {"ok": False, "configured": True, "label": config["label"],
                "error": "Weather is unavailable right now"}
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_text(json.dumps({"at": now, "config": config, "result": result}))
    except OSError:
        pass
    return result
