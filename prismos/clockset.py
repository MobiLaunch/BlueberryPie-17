"""Date and time settings: time zone and automatic time through timedated, 12/24-hour display locally.

timedatectl asks polkit for approval, so changes may show an authentication prompt.
Only a zone that exists in the system tz database, or a fixed boolean word, is ever passed."""
import shutil

from . import regional, settings
from .system import CommandError, run


def parse(text):
    values = {}
    for line in text.splitlines():
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def status():
    result = {"ok": True, "available": bool(shutil.which("timedatectl")), "timezone": "", "ntp": False,
              "synchronized": False, "clock_24h": settings.load()["clock_24h"]}
    if not result["available"]:
        return result
    try:
        facts = parse(run(["timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized"], timeout=5))
    except CommandError as error:
        result["error"] = str(error)
        return result
    result.update(timezone=facts.get("Timezone", ""), ntp=facts.get("NTP") == "yes",
                  synchronized=facts.get("NTPSynchronized") == "yes")
    return result


def set_timezone(name):
    if name not in regional.timezones():
        raise ValueError("Choose a time zone from the list")
    run(["timedatectl", "set-timezone", name], timeout=60)
    return status()


def set_ntp(enabled):
    if enabled not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    run(["timedatectl", "set-ntp", "true" if enabled == "yes" else "false"], timeout=60)
    return status()


def set_24h(enabled):
    if enabled not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    settings.update(clock_24h=enabled == "yes")
    return status()
