"""Alarms: a short list of time-of-day alarms kept in the user's settings."""
from . import settings

MAX = settings.MAX_ALARMS


def status():
    return {"ok": True, "alarms": settings.load()["alarms"]}


def parse_days(text):
    if not text:
        return []
    try:
        days = [int(part) for part in str(text).split(",")]
    except ValueError as error:
        raise ValueError("Days must be numbers from 0 (Monday) to 6 (Sunday)") from error
    if not all(0 <= day <= 6 for day in days):
        raise ValueError("Days must be numbers from 0 (Monday) to 6 (Sunday)")
    return sorted(set(days))


def add(when, days="", label=""):
    if not isinstance(when, str) or not settings.TIME.fullmatch(when):
        raise ValueError("Use a time like 07:30")
    label = (label or "").strip()
    if len(label) > 40 or any(ord(char) < 32 or ord(char) == 127 for char in label):
        raise ValueError("The label is too long or has control characters")
    chosen = parse_days(days)

    def change(data):
        existing = data["alarms"]
        if len(existing) >= MAX:
            raise ValueError("You can keep up to %d alarms" % MAX)
        identity = next(number for number in range(1, 10000) if number not in {item["id"] for item in existing})
        return {**data, "alarms": existing + [{"id": identity, "time": when, "days": chosen, "label": label, "enabled": True}]}
    settings.modify(change)
    return status()


def _find(data, identity):
    if not any(item["id"] == identity for item in data["alarms"]):
        raise ValueError("That alarm no longer exists")


def toggle(identity, enabled=None):
    identity = int(identity)

    def change(data):
        _find(data, identity)
        return {**data, "alarms": [{**item, "enabled": (not item["enabled"] if enabled is None else enabled)}
                                   if item["id"] == identity else item for item in data["alarms"]]}
    settings.modify(change)
    return status()


def remove(identity):
    identity = int(identity)

    def change(data):
        _find(data, identity)
        return {**data, "alarms": [item for item in data["alarms"] if item["id"] != identity]}
    settings.modify(change)
    return status()
