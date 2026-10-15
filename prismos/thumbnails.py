"""Window previews for the Recents overview.

Only windows that are on screen right now can be captured, so the previews of
windows on other workspaces are the ones taken the last time they were visible.
Previews are small screenshots, so they live in the per-login runtime directory
(tmpfs, removed at logout) and are deleted when their window closes or the user
turns previews off. Only validated integers and window addresses reach a command."""
import os
import re
import shutil
import time
from pathlib import Path

from . import settings, windows
from .system import CommandError, run

SCALE = "0.3"
MAX_FILES = 40
NAME = re.compile(r"(0x[0-9a-f]{1,16})-(\d{1,12})\.png\Z")


def directory():
    base = os.environ.get("XDG_RUNTIME_DIR")
    root = Path(base) if base else Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "prismos-previews"


def existing():
    """address -> newest preview path for files that look like ours."""
    found = {}
    try:
        entries = list(directory().iterdir())
    except OSError:
        return found
    for path in entries:
        match = NAME.fullmatch(path.name)
        if not match or path.is_symlink():
            continue
        address, stamp = match.group(1), int(match.group(2))
        if address not in found or stamp > found[address][0]:
            found[address] = (stamp, path)
    return found


def region(window):
    x, y, width, height = (window[key] for key in ("x", "y", "width", "height"))
    if not (16 <= width <= 16384 and 16 <= height <= 16384 and abs(x) <= 100000 and abs(y) <= 100000):
        return None
    return f"{x},{y} {width}x{height}"


def current_workspace():
    import json
    try:
        data = json.loads(run(["hyprctl", "-j", "activeworkspace"], timeout=4))
        return int(data["id"])
    except (ValueError, KeyError, TypeError, CommandError):
        return None


def prune(open_addresses):
    for address, (_, path) in list(existing().items()):
        if address not in open_addresses:
            path.unlink(missing_ok=True)
    for path in directory().glob("*.png") if directory().is_dir() else []:
        match = NAME.fullmatch(path.name)
        if not match or match.group(1) not in open_addresses:
            path.unlink(missing_ok=True)


def listing():
    open_windows = {window["address"] for window in windows.clients()}
    return {address: str(path) for address, (_, path) in existing().items() if address in open_windows}


def status():
    return {"ok": True, "enabled": settings.load()["recents_previews"], "thumbs": listing() if settings.load()["recents_previews"] else {}}


def capture(now=None):
    if not settings.load()["recents_previews"]:
        return {"ok": True, "enabled": False, "captured": 0, "thumbs": {}}
    if not shutil.which("grim"):
        raise CommandError("Window previews need the grim package")
    clients = windows.clients()
    prune({window["address"] for window in clients})
    workspace = current_workspace()
    folder = directory()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = int(now if now is not None else time.time())
    captured = 0
    for window in clients:
        box = region(window)
        if box is None or window["minimized"] or window["hidden"] or workspace is None or window["workspace"] != workspace:
            continue
        target = folder / f"{window['address']}-{stamp}.png"
        try:
            run(["grim", "-s", SCALE, "-g", box, str(target)], timeout=8)
        except CommandError:
            continue  # one window failing must not lose the others
        for old in folder.glob(f"{window['address']}-*.png"):
            if old != target and NAME.fullmatch(old.name):
                old.unlink(missing_ok=True)
        captured += 1
    found = existing()
    if len(found) > MAX_FILES:
        for address, (_, path) in sorted(found.items(), key=lambda item: item[1][0])[: len(found) - MAX_FILES]:
            path.unlink(missing_ok=True)
    return {"ok": True, "enabled": True, "captured": captured, "thumbs": listing()}


def clear():
    shutil.rmtree(directory(), ignore_errors=True)
    return {"ok": True, "thumbs": {}}


def set_enabled(value):
    if value not in ("yes", "no"):
        raise ValueError("Enabled must be yes or no")
    settings.update(recents_previews=value == "yes")
    if value == "no":
        clear()
    return status()
