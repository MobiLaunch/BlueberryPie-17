import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

DEFAULTS = {"seed": "#8469cf", "dark": False, "reduced_motion": False, "dnd": False, "favorites": None}


def directory():
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "prismos"


def load():
    try:
        data = json.loads((directory() / "settings.json").read_text())
        if not isinstance(data, dict):
            return dict(DEFAULTS)
        valid = {}
        for key in ("dark", "reduced_motion", "dnd"):
            if isinstance(data.get(key), bool):
                valid[key] = data[key]
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
