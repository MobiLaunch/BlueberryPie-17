import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

DEFAULTS = {"seed": "#8469cf", "dark": False, "reduced_motion": False, "dnd": False,
            "favorites": None, "android_enabled": False, "onboarding_complete": False,
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
        for key in ("dark", "reduced_motion", "dnd", "android_enabled", "onboarding_complete",
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
    if key not in ("dark", "reduced_motion", "dnd"):
        raise ValueError("Unknown preference")
    return modify(lambda data: {**data, key: not bool(data[key])})
