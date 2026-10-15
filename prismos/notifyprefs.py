"""Per-app notification muting. App names come from notification senders, so they
are only stored as data (never run) and are bounded and stripped of control characters."""
import os
import re
import tempfile
from pathlib import Path

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


def history_status():
    return {"ok": True, "enabled": settings.load()["notification_history"]}


def set_history(value):
    """Opt in to remembering recent notifications. The shell keeps them in memory only."""
    if value not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    settings.update(notification_history=value == "yes")
    return history_status()


def schedule_status():
    return {"ok": True, "schedule": settings.load()["dnd_schedule"]}


def set_schedule(enabled, start, end):
    """Quiet hours: Do Not Disturb applies automatically between start and end (may span midnight)."""
    if enabled not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    for value in (start, end):
        if not isinstance(value, str) or not settings.TIME.fullmatch(value):
            raise ValueError("Use times like 22:00")
    settings.update(dnd_schedule={"enabled": enabled == "yes", "start": start, "end": end})
    return schedule_status()


# --- Lock screen -----------------------------------------------------------------------------
# hyprlock cannot show shell state, so the shell leaves a number in the login's runtime
# directory (tmpfs, 0700, gone at logout) and the lock screen prints a one-line summary from it.
# Only a count is stored, never any notification text.
MAX_COUNT = 999


def count_path():
    base = os.environ.get("XDG_RUNTIME_DIR")
    return Path(base) / "prismos" / "notification-count" if base else None


def set_count(value):
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise ValueError("The count must be a whole number") from None
    if not 0 <= count <= MAX_COUNT:
        raise ValueError(f"The count must be between 0 and {MAX_COUNT}")
    path = count_path()
    if path is None:
        return {"ok": True, "count": count, "stored": False}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=".count-")
    try:
        with os.fdopen(handle, "w") as stream:
            stream.write(str(count))
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise
    return {"ok": True, "count": count, "stored": True}


def read_count():
    path = count_path()
    try:
        value = int(path.read_text().strip()) if path else 0
    except (OSError, ValueError):
        return 0
    return value if 0 <= value <= MAX_COUNT else 0


def summary():
    """The line the lock screen shows: empty when there is nothing to say or the user turned it off."""
    if not settings.load()["lock_notifications"]:
        return ""
    count = read_count()
    if count == 0:
        return ""
    return f"{count} notification" + ("" if count == 1 else "s")


def lock_status():
    return {"ok": True, "enabled": settings.load()["lock_notifications"]}


def set_lock_count(value):
    if value not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    settings.update(lock_notifications=value == "yes")
    return lock_status()
