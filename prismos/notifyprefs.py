"""Per-app notification muting. App names come from notification senders, so they
are only stored as data (never run) and are bounded and stripped of control characters."""
import re

from . import settings

NAME = re.compile(r"[^\x00-\x1f\x7f]{1,64}\Z")
LIMIT = 50


def clean(name):
    if not isinstance(name, str) or not NAME.fullmatch(name.strip()):
        raise ValueError("Invalid application name")
    return name.strip()


def status():
    return {"ok": True, "muted": settings.load()["muted_apps"]}


def mute(name):
    name = clean(name)
    muted = settings.load()["muted_apps"]
    if name not in muted and len(muted) >= LIMIT:
        raise ValueError("Too many muted applications")
    settings.modify(lambda data: {**data, "muted_apps": list(dict.fromkeys([*data["muted_apps"], name]))})
    return status()


def unmute(name):
    name = clean(name)
    settings.modify(lambda data: {**data, "muted_apps": [item for item in data["muted_apps"] if item != name]})
    return status()
