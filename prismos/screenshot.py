"""Screenshots with grim (and slurp for an area). Files go to ~/Pictures/Screenshots;
the image is also copied to the clipboard when wl-copy is installed.

Only fixed argv lists are run. The area comes from slurp and must match a strict
`x,y wxh` pattern before it reaches grim; the window box comes from hyprctl integers."""
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .system import CommandError, run

MODES = ("full", "area", "window")
REGION = re.compile(r"-?\d{1,6},-?\d{1,6} \d{1,6}x\d{1,6}\Z")


def folder():
    return Path.home() / "Pictures" / "Screenshots"


def window_region():
    import json
    try:
        window = json.loads(run(["hyprctl", "-j", "activewindow"], timeout=4))
        x, y = (int(v) for v in window["at"])
        width, height = (int(v) for v in window["size"])
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("No window is focused") from error
    if width < 1 or height < 1:
        raise ValueError("No window is focused")
    return f"{x},{y} {width}x{height}"


def region_for(mode):
    if mode == "full":
        return None
    if mode == "window":
        return window_region()
    try:
        chosen = run(["slurp", "-d"], timeout=90)
    except CommandError as error:
        raise ValueError("Screenshot cancelled") from error
    if not REGION.fullmatch(chosen):
        raise ValueError("Screenshot cancelled")
    return chosen


def capture(mode, now=None):
    if mode not in MODES:
        raise ValueError("Unknown screenshot mode")
    if not shutil.which("grim"):
        raise CommandError("Screenshots need the grim package")
    if mode == "area" and not shutil.which("slurp"):
        raise CommandError("Area screenshots need the slurp package")
    region = region_for(mode)
    directory = folder()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / (now or datetime.now()).strftime("Screenshot-%Y-%m-%d-%H%M%S.png")
    run(["grim", *(["-g", region] if region else []), str(path)], timeout=20)
    copied = False
    if shutil.which("wl-copy"):
        try:
            with path.open("rb") as image:
                copied = subprocess.run(["wl-copy", "--type", "image/png"], stdin=image, timeout=8,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            copied = False
    return {"ok": True, "path": str(path), "name": path.name, "copied": copied}
