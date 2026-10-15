"""World clock: a few saved time zones with their current local time."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import regional, settings


def label(name):
    return name.rsplit("/", 1)[-1].replace("_", " ")


def entry(name, now=None):
    now = now or datetime.now(timezone.utc)
    here = now.astimezone()
    there = now.astimezone(ZoneInfo(name))
    offset = there.utcoffset().total_seconds() / 60
    local_offset = here.utcoffset().total_seconds() / 60
    return {"zone": name, "label": label(name), "hour": there.hour, "minute": there.minute,
            "day": (there.date() - here.date()).days, "offset": int(offset - local_offset)}


def status(now=None):
    return {"ok": True, "clocks": [entry(name, now) for name in settings.load()["world_clocks"]]}


def add(name):
    if name not in regional.timezones():
        raise ValueError("Choose a time zone from the list")

    def change(data):
        zones = data["world_clocks"]
        if name in zones:
            return data
        if len(zones) >= settings.MAX_WORLD_CLOCKS:
            raise ValueError("You can keep up to %d clocks" % settings.MAX_WORLD_CLOCKS)
        return {**data, "world_clocks": zones + [name]}
    settings.modify(change)
    return status()


def remove(name):
    settings.modify(lambda data: {**data, "world_clocks": [zone for zone in data["world_clocks"] if zone != name]})
    return status()
