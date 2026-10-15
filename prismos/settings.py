import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .regional import KEYBOARD_IDS
from .theme import SCHEME_SPECS

FONT_SCALES = (0.9, 1.0, 1.15, 1.3)
TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")
MAX_ALARMS = 10
RESIZABLE_WIDGETS = ("calendar", "weather", "system", "notes")
WIDGET_SIZES = ("small", "medium", "large")
NIGHT_TEMPS = (2500, 5500)
MAX_WORLD_CLOCKS = 6


def clean_alarms(items):
    """Keep only well-formed alarms: unique id, HH:MM, days 0-6 (Monday first), short label."""
    result, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        identity, when, days, label = item.get("id"), item.get("time"), item.get("days"), item.get("label", "")
        if (type(identity) is not int or not 1 <= identity <= 9999 or identity in seen
                or not isinstance(when, str) or not TIME.fullmatch(when)
                or not isinstance(days, list) or not all(type(day) is int and 0 <= day <= 6 for day in days)
                or not isinstance(label, str) or len(label) > 40 or re.search(r"[\x00-\x1f\x7f]", label)
                or type(item.get("enabled")) is not bool):
            continue
        seen.add(identity)
        result.append({"id": identity, "time": when, "days": sorted(set(days)), "label": label.strip(),
                       "enabled": item["enabled"]})
    return result[:MAX_ALARMS]

TILE_IDS = ("wifi", "bluetooth", "sound", "microphone", "dnd", "dark", "reduced_motion", "audio_devices",
            "airplane", "battery_saver", "night_light", "screenshot", "lock", "hotspot", "vpn", "screen_record")
WIDGET_IDS = ("glance", "clock", "search", "calendar", "media", "weather", "system", "analog", "notes")
DEFAULTS = {"seed": "#8469cf", "dark": False, "reduced_motion": False, "dnd": False,
            "favorites": None, "recent_apps": [], "wallpaper": "", "widgets": None, "weather": {}, "keyboard": "us", "widget_sizes": {}, "night_temp": 3800, "recents_previews": True, "clock_24h": True, "world_clocks": [], "tiles": None, "alarms": [], "dnd_schedule": {"enabled": False, "start": "22:00", "end": "07:00"}, "clipboard_history": False, "notification_history": False, "lock_notifications": True, "record_audio": False, "vpn_profile": "", "muted_apps": [], "night_light": False, "scheme": "tonal_spot", "font_scale": 1.0, "android_enabled": False, "onboarding_complete": False,
            "natural_scroll": True, "tap_to_click": True,
            "pointer_speed": 0.0, "repeat_rate": 25, "display_scales": {}, "display_positions": {}}


def directory():
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "prismos"


def load():
    try:
        data = json.loads((directory() / "settings.json").read_text())
        if not isinstance(data, dict):
            return dict(DEFAULTS)
        valid = {}
        for key in ("dark", "reduced_motion", "dnd", "night_light", "clipboard_history", "notification_history", "lock_notifications", "record_audio", "clock_24h", "recents_previews", "android_enabled", "onboarding_complete",
                    "natural_scroll", "tap_to_click"):
            if isinstance(data.get(key), bool):
                valid[key] = data[key]
        speed = data.get("pointer_speed")
        if type(speed) in (int, float) and -1.0 <= speed <= 1.0:
            valid["pointer_speed"] = float(speed)
        rate = data.get("repeat_rate")
        if type(rate) is int and 10 <= rate <= 60:
            valid["repeat_rate"] = rate
        monitors = data.get("display_scales")
        if isinstance(monitors, dict):
            valid["display_scales"] = {
                name: float(scale) for name, scale in list(monitors.items())[:8]
                if isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,39}", name)
                and type(scale) in (float, int) and scale in (1, 1.25, 1.5, 1.75, 2)
            }
        positions = data.get("display_positions")
        if isinstance(positions, dict):
            valid["display_positions"] = {
                name: [int(coords[0]), int(coords[1])]
                for name, coords in list(positions.items())[:8]
                if isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,39}", name)
                and isinstance(coords, list) and len(coords) == 2
                and all(type(c) is int and abs(c) <= 40000 for c in coords)
            }
        seed = data.get("seed")
        if isinstance(seed, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", seed):
            valid["seed"] = seed.lower()
        favorites = data.get("favorites")
        if isinstance(favorites, list):
            valid["favorites"] = list(dict.fromkeys(value for value in favorites
                if isinstance(value, str) and value.endswith(".desktop") and len(value) <= 256
                and not any(char in value for char in ("/", "\\", "\x00"))))[:8]
        widgets = data.get("widgets")
        if isinstance(widgets, list):
            valid["widgets"] = [item for item in WIDGET_IDS if item in widgets]
        tiles = data.get("tiles")
        if isinstance(tiles, list):
            valid["tiles"] = [item for item in dict.fromkeys(tiles) if item in TILE_IDS]
        sizes = data.get("widget_sizes")
        if isinstance(sizes, dict):
            valid["widget_sizes"] = {key: value for key, value in sizes.items()
                                     if key in RESIZABLE_WIDGETS and value in WIDGET_SIZES}
        zones = data.get("world_clocks")
        if isinstance(zones, list):
            # The time zone database is only read (it is slow to scan) when there is something to check.
            candidates = [z for z in zones if isinstance(z, str)]
            if candidates:
                from .regional import timezones
                known = set(timezones())
                candidates = [z for z in candidates if z in known]
            valid["world_clocks"] = list(dict.fromkeys(candidates))[:MAX_WORLD_CLOCKS]
        alarms = data.get("alarms")
        if isinstance(alarms, list):
            valid["alarms"] = clean_alarms(alarms)
        quiet = data.get("dnd_schedule")
        if isinstance(quiet, dict) and type(quiet.get("enabled")) is bool \
                and TIME.fullmatch(str(quiet.get("start"))) and TIME.fullmatch(str(quiet.get("end"))):
            valid["dnd_schedule"] = {"enabled": quiet["enabled"], "start": quiet["start"], "end": quiet["end"]}
        profile = data.get("vpn_profile")
        if isinstance(profile, str) and re.fullmatch(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", profile):
            valid["vpn_profile"] = profile.lower()
        muted = data.get("muted_apps")
        if isinstance(muted, list):
            valid["muted_apps"] = list(dict.fromkeys(
                name for name in muted if isinstance(name, str) and 1 <= len(name) <= 64
                and not re.search(r"[\x00-\x1f\x7f]", name)))[:50]
        place = data.get("weather")
        if isinstance(place, dict) and place:
            try:
                lat, lon, label, units = float(place["lat"]), float(place["lon"]), str(place["label"])[:60], place["units"]
                if -90 <= lat <= 90 and -180 <= lon <= 180 and label.strip() and units in ("metric", "imperial"):
                    valid["weather"] = {"lat": lat, "lon": lon, "label": label, "units": units}
            except (KeyError, TypeError, ValueError):
                pass
        warmth = data.get("night_temp")
        if type(warmth) is int and NIGHT_TEMPS[0] <= warmth <= NIGHT_TEMPS[1]:
            valid["night_temp"] = warmth
        if data.get("scheme") in SCHEME_SPECS:
            valid["scheme"] = data["scheme"]
        scale = data.get("font_scale")
        if type(scale) in (int, float) and float(scale) in FONT_SCALES:
            valid["font_scale"] = float(scale)
        layout = data.get("keyboard")
        if isinstance(layout, str) and layout in KEYBOARD_IDS:
            valid["keyboard"] = layout
        wallpaper = data.get("wallpaper")
        if (isinstance(wallpaper, str) and wallpaper.startswith("/") and len(wallpaper) <= 4096
                and "\x00" not in wallpaper
                and wallpaper.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))):
            valid["wallpaper"] = wallpaper
        recents = data.get("recent_apps")
        if isinstance(recents, list):
            valid["recent_apps"] = list(dict.fromkeys(value for value in recents
                if isinstance(value, str) and value.endswith(".desktop") and len(value) <= 256
                and not any(char in value for char in ("/", "\\", "\x00"))))[:8]
        return {**DEFAULTS, **valid}
    except (OSError, ValueError):
        return dict(DEFAULTS)


@contextmanager
def locked():
    root = directory()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / "settings.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def update(**changes):
    return modify(lambda data: {**data, **changes})


def modify(transform):
    """Apply one read/modify/write under the same lock."""
    with locked():
        data = transform(load())
        fd, name = tempfile.mkstemp(prefix=".settings-", dir=directory())
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(data, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, directory() / "settings.json")
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return data


def toggle(key):
    if key not in ("dark", "reduced_motion", "dnd", "night_light"):
        raise ValueError("Unknown preference")
    return modify(lambda data: {**data, key: not bool(data[key])})
