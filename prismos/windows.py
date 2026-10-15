"""Open-window state and window management for the dock, Recents and caption controls.

Reads use `hyprctl -j`. Every action sends fixed dispatcher names; the only
variable parts are a window address that matched `ADDRESS` *and* a window that
is currently open, plus integers computed here. No caller-provided text reaches
a command line.

Dispatcher compatibility with a Lua-configured Hyprland is unverified (see
docs/VALIDATION.md); a rejected request is reported and changes nothing.
"""
import json
import os
import re
import tempfile
from pathlib import Path

from .system import CommandError, run

ADDRESS = re.compile(r"0x[0-9a-fA-F]{1,16}\Z")
CLASS = re.compile(r"[^\x00-\x1f]{1,120}\Z")
MINIMIZED = "special:minimized"
GAP = 12  # breathing room around snapped windows, matching the session's gaps
from .windowops import OPERATIONS, SCREEN_OPERATIONS  # noqa: E402,F401  (re-exported)


def _json(command):
    try:
        return json.loads(run(command, timeout=5))
    except (ValueError, TypeError) as error:
        raise CommandError("Could not read window information") from error


def clients():
    payload = _json(["hyprctl", "-j", "clients"])
    active = _json(["hyprctl", "-j", "activewindow"])
    if not isinstance(payload, list):
        raise CommandError("Unexpected window information")
    focused = active.get("address") if isinstance(active, dict) else None
    result = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("mapped", True):
            continue
        address, app_class = item.get("address"), item.get("class")
        if not isinstance(address, str) or not ADDRESS.fullmatch(address):
            continue
        if not isinstance(app_class, str) or not CLASS.fullmatch(app_class):
            continue  # Windows without an app ID cannot be matched to an application.
        workspace = item.get("workspace") if isinstance(item.get("workspace"), dict) else {}
        try:
            workspace_id = int(workspace.get("id", 0))
            pid = int(item.get("pid", 0))
            recency = int(item.get("focusHistoryID", 999))  # 0 is the most recently focused
            monitor = int(item.get("monitor", 0))
            fullscreen = int(item.get("fullscreen", 0) or 0)
            x, y = (int(v) for v in item.get("at", (0, 0)))
            width, height = (int(v) for v in item.get("size", (0, 0)))
        except (TypeError, ValueError):
            workspace_id, pid, recency, monitor, fullscreen = 0, 0, 999, 0, 0
            x = y = width = height = 0
        result.append({"address": address.lower(), "class": app_class,
                       "title": str(item.get("title") or "")[:200],
                       "workspace": workspace_id, "pid": pid, "recency": recency,
                       "monitor": monitor, "x": x, "y": y, "width": width, "height": height,
                       "focused": address == focused,
                       "floating": bool(item.get("floating", False)),
                       "maximized": fullscreen != 0,
                       "minimized": workspace.get("name") == MINIMIZED,
                       "hidden": bool(item.get("hidden", False))})
    result.sort(key=lambda window: (window["workspace"], window["class"].casefold(), window["address"]))
    return result


def status():
    try:
        return {"ok": True, "windows": clients()}
    except CommandError as error:
        return {"ok": False, "windows": [], "error": str(error)}


def hypr(name, argument):
    """Send one fixed dispatcher; the compositor must answer `ok`."""
    reply = run(["hyprctl", "dispatch", name, argument], timeout=5)
    if reply.strip().lower() != "ok":
        raise CommandError("The compositor did not accept the request")


def work_area(window):
    """Usable rectangle (x, y, w, h) of the window's monitor in layout pixels."""
    monitors = _json(["hyprctl", "-j", "monitors"])
    if not isinstance(monitors, list) or not monitors:
        raise CommandError("Could not read displays")
    chosen = next((m for m in monitors if isinstance(m, dict) and m.get("id") == window["monitor"]), monitors[0])
    try:
        scale = float(chosen.get("scale", 1)) or 1.0
        x, y = int(chosen["x"]), int(chosen["y"])
        width, height = int(int(chosen["width"]) / scale), int(int(chosen["height"]) / scale)
        reserved = [int(v) for v in (chosen.get("reserved") or [0, 0, 0, 0])][:4]
    except (KeyError, TypeError, ValueError) as error:
        raise CommandError("Unexpected display information") from error
    left, top, right, bottom = (reserved + [0, 0, 0, 0])[:4]
    return x + left, y + top, width - left - right, height - top - bottom


def snap_rect(area, side):
    x, y, width, height = area
    half = (width - 3 * GAP) // 2
    top, tall = y + GAP, height - 2 * GAP
    if half < 200 or tall < 200:
        raise CommandError("There is not enough room to snap this window")
    return (x + GAP if side == "left" else x + 2 * GAP + half, top, half, tall)


def resolve(address, windows):
    if address == "active":
        found = next((w for w in windows if w["focused"]), None)
        if found is None:
            raise ValueError("No window is focused")
        return found
    if not isinstance(address, str) or not ADDRESS.fullmatch(address):
        raise ValueError("Invalid window")
    found = next((w for w in windows if w["address"] == address.lower()), None)
    if found is None:
        raise ValueError("That window is no longer open")
    return found


def dispatch(operation, address):
    if operation not in OPERATIONS:
        raise ValueError("Unknown window action")
    window = resolve(address, clients())
    target = "address:" + window["address"]
    if operation == "focus":
        hypr("focuswindow", target)
    elif operation == "close":
        hypr("closewindow", target)
    elif operation == "minimize":
        hypr("movetoworkspacesilent", f"{MINIMIZED},{target}")
    elif operation == "restore":
        if window["minimized"]:
            workspace = _json(["hyprctl", "-j", "activeworkspace"])
            current = workspace.get("id") if isinstance(workspace, dict) else None
            if not isinstance(current, int) or current < 1:
                raise CommandError("Could not find the current workspace")
            hypr("movetoworkspace", f"{current},{target}")
        hypr("focuswindow", target)
        if window["maximized"]:
            hypr("fullscreen", "1")
    elif operation == "maximize":
        if window["minimized"]:
            raise ValueError("Restore the window first")
        hypr("focuswindow", target)
        hypr("fullscreen", "1")  # toggles maximized on the focused window
    elif operation == "float":
        hypr("togglefloating", target)
    else:  # snap-left / snap-right
        if window["minimized"]:
            raise ValueError("Restore the window first")
        snap(window, operation.split("-")[1])
    return {"ok": True, "action": operation, "address": window["address"]}


def snap(window, side):
    target = "address:" + window["address"]
    x, y, width, height = snap_rect(work_area(window), side)
    if window["maximized"]:
        hypr("focuswindow", target)
        hypr("fullscreen", "1")
    if not window["floating"]:
        hypr("togglefloating", target)
    hypr("resizewindowpixel", f"exact {width} {height},{target}")
    hypr("movewindowpixel", f"exact {x} {y},{target}")


def bring_here(window):
    """Move a minimized window, or one on another workspace, to the current workspace without following it."""
    workspace = _json(["hyprctl", "-j", "activeworkspace"])
    current = workspace.get("id") if isinstance(workspace, dict) else None
    if not isinstance(current, int) or current < 1:
        raise CommandError("Could not find the current workspace")
    if window["minimized"] or window["workspace"] != current:
        hypr("movetoworkspacesilent", f"{current},address:{window['address']}")


def split(first, second):
    """Put two windows side by side: ``first`` on the left, ``second`` on the right."""
    all_windows = clients()
    left, right = resolve(first, all_windows), resolve(second, all_windows)
    if left["address"] == right["address"]:
        raise ValueError("Choose two different windows")
    for window in (left, right):
        bring_here(window)
    # Snap against the current layout: both are no longer minimized once brought back.
    for window, side in ((left, "left"), (right, "right")):
        snap(dict(window, minimized=False), side)
    hypr("focuswindow", "address:" + right["address"])
    return {"ok": True, "action": "split", "left": left["address"], "right": right["address"]}


def desktop_state():
    return Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()) / "prismos-desktop.json"


def remembered():
    try:
        value = json.loads(desktop_state().read_text())
    except (OSError, ValueError):
        return []
    return [a for a in value if isinstance(a, str) and ADDRESS.fullmatch(a)] if isinstance(value, list) else []


def remember(addresses):
    path = desktop_state()
    if not addresses:
        path.unlink(missing_ok=True)
        return
    descriptor, name = tempfile.mkstemp(prefix=".desktop-", dir=path.parent)
    with os.fdopen(descriptor, "w") as stream:  # mkstemp creates the file private (0600)
        json.dump(addresses, stream)
    os.replace(name, path)


def show_desktop():
    """Android's Home: tuck every window on the current workspace away; do it again to bring them back."""
    all_windows = clients()
    workspace = _json(["hyprctl", "-j", "activeworkspace"])
    current = workspace.get("id") if isinstance(workspace, dict) else None
    if not isinstance(current, int) or current < 1:
        raise CommandError("Could not find the current workspace")
    visible = [w for w in all_windows if w["workspace"] == current and not w["minimized"]]
    if visible:
        for window in visible:
            hypr("movetoworkspacesilent", f"{MINIMIZED},address:{window['address']}")
        remember([w["address"] for w in visible])
        return {"ok": True, "action": "show-desktop", "hidden": len(visible), "restored": 0}
    open_now = {w["address"]: w for w in all_windows if w["minimized"]}
    back = [open_now[a] for a in remembered() if a in open_now]
    remember([])
    for window in back:
        hypr("movetoworkspacesilent", f"{current},address:{window['address']}")
    if back:
        hypr("focuswindow", "address:" + back[0]["address"])
    return {"ok": True, "action": "show-desktop", "hidden": 0, "restored": len(back)}
