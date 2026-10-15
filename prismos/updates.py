"""Software updates for Settings > Software update.

Checking only reads: ``checkupdates`` (pacman-contrib) works on a private copy of the
package database, so it needs no root and never changes the system, and Flatpak is asked
which installed apps have a newer version. Installing is deliberately *not* done in the
background: the page opens the session terminal on a fixed command so the password prompt,
package conflicts and news are seen by the person updating. The last result is cached in
the user's cache folder (names and versions only)."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .system import CommandError

PACKAGE = re.compile(r"[a-z0-9@._+-]{1,100}\Z")
VERSION = re.compile(r"[A-Za-z0-9:.+_~-]{1,80}\Z")
FLATPAK_ID = re.compile(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}\Z")
MAX_ITEMS = 500
KINDS = {
    "pacman": "sudo pacman -Syu",
    "flatpak": "flatpak update",
    "all": "sudo pacman -Syu; flatpak update",
}


def cache_path():
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "prismos" / "updates.json"


def parse_pacman(text):
    items = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[2] == "->" and PACKAGE.fullmatch(parts[0]) \
                and VERSION.fullmatch(parts[1]) and VERSION.fullmatch(parts[3]):
            items.append({"name": parts[0], "old": parts[1], "new": parts[3]})
    return sorted(items, key=lambda item: item["name"])[:MAX_ITEMS]


def parse_flatpak(text):
    items = []
    for line in text.splitlines():
        identity = line.split("\t", 1)[0].strip()
        if FLATPAK_ID.fullmatch(identity):
            items.append({"name": identity, "old": "", "new": ""})
    return sorted(items, key=lambda item: item["name"])[:MAX_ITEMS]


def _group(items=(), available=True, error=""):
    return {"available": available, "count": len(items), "items": list(items), "error": error}


def pacman_updates():
    if not shutil.which("checkupdates"):
        return _group(available=False, error="Checking needs the pacman-contrib package")
    try:
        result = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=90, check=False,
                                env={**os.environ, "LC_ALL": "C"})
    except (OSError, subprocess.TimeoutExpired):
        return _group(error="The package check did not finish")
    if result.returncode == 2:  # checkupdates' way of saying there is nothing to update
        return _group()
    if result.returncode:
        return _group(error=(result.stderr.strip() or "The package check failed")[:200])
    return _group(parse_pacman(result.stdout))


def flatpak_updates():
    if not shutil.which("flatpak"):
        return _group(available=False)
    try:
        result = subprocess.run(["flatpak", "remote-ls", "--updates", "--columns=application"],
                                capture_output=True, text=True, timeout=60, check=False,
                                env={**os.environ, "LC_ALL": "C"})
    except (OSError, subprocess.TimeoutExpired):
        return _group(error="The Flatpak check did not finish")
    if result.returncode:
        return _group(error=(result.stderr.strip() or "The Flatpak check failed")[:200])
    return _group(parse_flatpak(result.stdout))


def save(result):
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, name = tempfile.mkstemp(prefix=".updates-", dir=path.parent)  # 0600
    with os.fdopen(descriptor, "w") as stream:
        json.dump(result, stream)
    os.replace(name, path)


def cached():
    """The last result, or an empty one that says nothing has been checked."""
    try:
        data = json.loads(cache_path().read_text())
        if isinstance(data, dict) and isinstance(data.get("checked"), (int, float)):
            pacman = data.get("pacman") if isinstance(data.get("pacman"), dict) else {}
            flatpak = data.get("flatpak") if isinstance(data.get("flatpak"), dict) else {}
            return _summary(float(data["checked"]), _clean(pacman), _clean(flatpak))
    except (OSError, ValueError):
        pass
    return _summary(0, _group(), _group())


def _clean(group):
    items = [{"name": str(item["name"]), "old": str(item.get("old", "")), "new": str(item.get("new", ""))}
             for item in group.get("items", []) if isinstance(item, dict) and isinstance(item.get("name"), str)
             and (PACKAGE.fullmatch(item["name"]) or FLATPAK_ID.fullmatch(item["name"]))][:MAX_ITEMS]
    return _group(items, group.get("available") is not False, str(group.get("error", ""))[:200])


def _summary(checked, pacman, flatpak):
    return {"ok": True, "checked": checked, "pacman": pacman, "flatpak": flatpak,
            "total": pacman["count"] + flatpak["count"]}


def check():
    result = _summary(time.time(), pacman_updates(), flatpak_updates())
    if not result["pacman"]["available"] and not result["flatpak"]["available"]:
        raise CommandError("Neither pacman-contrib nor Flatpak is available to check for updates")
    save(result)
    return result


def apply(kind):
    """Open the session terminal on one fixed update command."""
    if kind not in KINDS:
        raise ValueError("Choose pacman, flatpak or all")
    if not shutil.which("foot"):
        raise CommandError("The foot terminal is not installed")
    script = f"{KINDS[kind]}; echo; read -r -p 'Done. Press Enter to close.' _"
    subprocess.Popen(["foot", "--title", "PrismOS update", "bash", "-c", script],
                     stdin=subprocess.DEVNULL, start_new_session=True)
    return {"ok": True, "kind": kind}
