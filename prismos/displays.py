"""Display scaling with live, reversible Hyprland Lua monitor configuration.

Never disables a monitor. Changes revert after twenty seconds unless confirmed.
All output names and numeric scales come from validated compositor state.
"""
import fcntl
import json
import os
import re
import secrets
import time
from pathlib import Path

from . import settings
from .system import CommandError, run

SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)
MONITOR = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,39}\Z")
TIMEOUT = 20


def emit(phase, **fields):
    print(json.dumps({"ok": True, "phase": phase, **fields}), flush=True)


def monitors():
    try:
        payload = json.loads(run(["hyprctl", "-j", "monitors"], timeout=7))
    except (ValueError, TypeError) as error:
        raise CommandError("Could not read displays") from error
    if not isinstance(payload, list):
        raise CommandError("Unexpected display information")
    result = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not MONITOR.fullmatch(name):
            continue
        try:
            width = int(item["width"])
            height = int(item["height"])
            scale = float(item["scale"])
            hz = round(float(item.get("refreshRate") or 60), 2)
            x = int(item.get("x", 0))
            y = int(item.get("y", 0))
        except (TypeError, ValueError, KeyError):
            continue
        if not (width > 0 and height > 0 and 0.5 <= scale <= 4 and hz > 0):
            continue
        supported = [v for v in SCALES
                     if abs(width / v - round(width / v)) < .001
                     and abs(height / v - round(height / v)) < .001]
        result.append({"name": name, "description": str(item.get("description") or name)[:140],
                       "width": width, "height": height, "refresh": hz,
                       "scale": scale, "x": x, "y": y,
                       "choices": supported})
    return result


def status():
    return {"ok": True, "monitors": monitors()}


def apply_rule(display, scale):
    """Generate a fixed Lua API call: no execution of user-provided Lua code."""
    name = display["name"]
    if not MONITOR.fullmatch(name) or scale not in display["choices"] and scale != display["scale"]:
        raise ValueError("Unsupported monitor or scale")
    mode = f'{display["width"]}x{display["height"]}@{display["refresh"]:g}'
    position = f'{display["x"]}x{display["y"]}'
    # The name/mode/position are fully validated before interpolation.
    lua = (f'hl.monitor({{ output = "{name}", mode = "{mode}", '
           f'position = "{position}", scale = {scale:g} }})')
    run(["hyprctl", "eval", lua], timeout=10)


def runtime_dir():
    base = os.environ.get("XDG_RUNTIME_DIR")
    if base:
        root = Path(base) / "prismos"
    else:
        root = settings.directory()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    return root


def confirm(token):
    if not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{32}", token):
        raise ValueError("Invalid display confirmation token")
    directory = runtime_dir()
    pending = directory / "display-pending.json"
    try:
        data = json.loads(pending.read_text())
    except (OSError, ValueError):
        raise ValueError("No display change is awaiting confirmation") from None
    if data.get("token") != token or data.get("expires", 0) < time.time():
        raise ValueError("The display confirmation has expired")
    marker = directory / ("display-confirm-" + token)
    with marker.open("x") as file:
        file.write("confirm")
    return {"ok": True, "message": "Display configuration confirmed"}


def preview(name, raw_scale):
    if not isinstance(name, str) or not MONITOR.fullmatch(name):
        raise ValueError("Select a connected display")
    try:
        target_scale = float(raw_scale)
    except (ValueError, TypeError):
        raise ValueError("Select a supported scale") from None
    if target_scale not in SCALES:
        raise ValueError("Select a supported scale")
    directory = runtime_dir()
    lock_path = directory / "display.lock"
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another display preview is already running") from None
        display = next((d for d in monitors() if d["name"] == name), None)
        if not display or target_scale not in display["choices"]:
            raise ValueError("The requested display scaling is unavailable")
        previous = display["scale"]
        if abs(previous - target_scale) < .0001:
            emit("confirmed", name=name, scale=target_scale)
            return 0
        token = secrets.token_hex(16)
        pending = directory / "display-pending.json"
        marker = directory / ("display-confirm-" + token)
        deadline = time.time() + TIMEOUT
        pending.write_text(json.dumps({"token": token, "expires": deadline}))
        pending.chmod(0o600)
        try:
            apply_rule(display, target_scale)
            emit("trial", token=token, name=name, scale=target_scale, seconds=TIMEOUT)
            until = time.monotonic() + TIMEOUT
            while time.monotonic() < until:
                if marker.exists():
                    saved = dict(settings.load().get("display_scales") or {})
                    saved[name] = target_scale
                    settings.update(display_scales=saved)
                    emit("confirmed", name=name, scale=target_scale)
                    return 0
                time.sleep(.25)
            apply_rule(display, previous)
            emit("reverted", name=name, scale=previous)
            return 0
        finally:
            pending.unlink(missing_ok=True)
            marker.unlink(missing_ok=True)


def apply_saved():
    stored = settings.load().get("display_scales") or {}
    active = {m["name"]: m for m in monitors()}
    count = 0
    for name, target in stored.items():
        display = active.get(name)
        if display and target in display["choices"]:
            apply_rule(display, target)
            count += 1
    return {"ok": True, "applied": count}
