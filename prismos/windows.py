"""Open-window state for the dock and Recents, read from Hyprland.

Reads use `hyprctl -j clients`. Focus and close send fixed dispatcher names with
a validated window address; no caller-provided text reaches a command line.
"""
import json
import re

from .system import CommandError, run

ADDRESS = re.compile(r"0x[0-9a-fA-F]{1,16}\Z")
CLASS = re.compile(r"[^\x00-\x1f]{1,120}\Z")


def clients():
    try:
        payload = json.loads(run(["hyprctl", "-j", "clients"], timeout=5))
        active = json.loads(run(["hyprctl", "-j", "activewindow"], timeout=5))
    except (ValueError, TypeError) as error:
        raise CommandError("Could not read open windows") from error
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
        except (TypeError, ValueError):
            workspace_id, pid = 0, 0
        result.append({"address": address.lower(), "class": app_class,
                       "title": str(item.get("title") or "")[:200],
                       "workspace": workspace_id, "pid": pid,
                       "focused": address == focused,
                       "hidden": bool(item.get("hidden", False))})
    result.sort(key=lambda window: (window["workspace"], window["class"].casefold(), window["address"]))
    return result


def status():
    try:
        return {"ok": True, "windows": clients()}
    except CommandError as error:
        return {"ok": False, "windows": [], "error": str(error)}


def dispatch(operation, address):
    names = {"focus": "focuswindow", "close": "closewindow"}
    if operation not in names:
        raise ValueError("Unknown window action")
    if not isinstance(address, str) or not ADDRESS.fullmatch(address):
        raise ValueError("Invalid window")
    known = {window["address"] for window in clients()}
    if address.lower() not in known:
        raise ValueError("That window is no longer open")
    reply = run(["hyprctl", "dispatch", names[operation], "address:" + address.lower()], timeout=5)
    if reply.strip().lower() != "ok":
        raise CommandError("The compositor did not accept the request")
    return {"ok": True, "action": operation, "address": address.lower()}
