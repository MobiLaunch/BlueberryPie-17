"""App info for the application menu: where an app came from, what is running, force stop, uninstall.

Reads use `pacman -Qo/-Qi`, Flatpak's own metadata and the open-window list. The
two actions are deliberately narrow:

* Force stop only signals processes that own a window of this app, belong to the
  current user and are not the shell, the compositor or this bridge.
* Uninstall only removes a *user* Flatpak. System packages are never removed from
  here (that needs root); the page shows the command to copy instead.

Every command is a fixed argv; the desktop ID is looked up in the installed
entries and Flatpak/pacman names must match strict patterns first.
"""
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

from . import apps, windows
from .system import CommandError, run

PACKAGE = re.compile(r"[a-z0-9@._+-]{1,100}\Z")
FLATPAK_ID = re.compile(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+){2,}\Z")
PROTECTED = frozenset({"hyprland", "quickshell", "qs", "prismctl", "systemd", "dbus-daemon", "dbus-broker",
                       "greetd", "sddm", "login", "init", "pipewire", "wireplumber", "networkmanager"})
GRACE_SECONDS = 2.0


def find(desktop_id):
    entry = next((item for item in apps.entries() if item["id"] == desktop_id), None)
    if entry is None:
        raise ValueError("Application is no longer installed or visible")
    return entry


def flatpak_id(entry):
    """The Flatpak application ID when the entry is exported by Flatpak, else empty."""
    path = entry["path"]
    if "/flatpak/" not in path:  # exports are symlinks, so the resolved path lives under flatpak/app/
        return ""
    stem = Path(path).stem
    return stem if FLATPAK_ID.fullmatch(stem) else ""


def flatpak_scope(app_id):
    """'user', 'system' or '' for an installed Flatpak."""
    for scope in ("user", "system"):
        try:
            run(["flatpak", "info", f"--{scope}", app_id], timeout=6)
            return scope
        except CommandError:
            continue
    return ""


def pacman_package(path):
    try:
        text = run(["pacman", "-Qo", "-q", path], timeout=6)
    except CommandError:
        return ""
    name = text.splitlines()[0].strip() if text else ""
    return name if PACKAGE.fullmatch(name) else ""


def pacman_details(name):
    try:
        text = run(["pacman", "-Qi", name], timeout=6)
    except CommandError:
        return {}
    wanted = {"Version": "version", "Installed Size": "size", "Description": "description", "URL": "url"}
    found = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() in wanted and wanted[key.strip()] not in found:
            found[wanted[key.strip()]] = value.strip()[:300]
    return found


def flatpak_details(app_id, scope):
    try:
        text = run(["flatpak", "info", f"--{scope}", app_id], timeout=6)
    except CommandError:
        return {}
    found = {}
    for line in text.splitlines():
        key, sep, value = line.strip().partition(":")
        if sep and key in ("Version", "Installed", "Origin") and key.lower() not in found:
            found[key.lower()] = value.strip()[:300]
    return found


def app_windows(entry, clients):
    wanted = set(_classes(entry))
    return [window for window in clients if window["class"].strip().lower() in wanted]


def _classes(entry):
    ident = entry["id"].strip().lower()
    ident = ident[:-8] if ident.endswith(".desktop") else ident
    classes = [entry.get("startupClass", "").strip().lower(), ident]
    if "." in ident:
        classes.append(ident.rsplit(".", 1)[-1])
    return [value for value in classes if value]


def info(desktop_id):
    entry = find(desktop_id)
    try:
        open_windows = app_windows(entry, windows.clients())
    except CommandError:
        open_windows = []
    pids = sorted({window["pid"] for window in open_windows if window["pid"] > 0})
    result = {"ok": True, "id": entry["id"], "name": entry["name"], "icon": entry["icon"],
              "description": entry["description"], "category": entry["category"],
              "running": bool(open_windows), "windows": len(open_windows), "processes": len(pids),
              "source": "other", "package": "", "version": "", "size": "", "origin": "",
              "removable": False, "remove_command": ""}
    app_id = flatpak_id(entry)
    if app_id:
        scope = flatpak_scope(app_id)
        details = flatpak_details(app_id, scope) if scope else {}
        result.update(source="flatpak", package=app_id, version=details.get("version", ""),
                      origin=details.get("origin", ""), size=details.get("installed", ""))
        if scope == "user":
            result["removable"] = True
        elif scope == "system":
            result["remove_command"] = f"flatpak uninstall {app_id}"
        return result
    package = pacman_package(entry["path"])
    if package:
        details = pacman_details(package)
        result.update(source="pacman", package=package, version=details.get("version", ""),
                      size=details.get("size", ""),
                      remove_command=f"sudo pacman -Rns {package}")
    return result


def _comm(pid):
    try:
        return Path(f"/proc/{pid}/comm").read_text().strip().lower()
    except OSError:
        return ""


def _mine(pid):
    try:
        return os.stat(f"/proc/{pid}").st_uid == os.getuid()
    except OSError:
        return False


def stoppable(pid):
    return (pid > 1 and pid != os.getpid() and pid != os.getppid() and _mine(pid)
            and _comm(pid) not in PROTECTED)


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # A zombie that was not reaped yet is already gone for our purposes.
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return False


def force_stop(desktop_id, grace=GRACE_SECONDS):
    entry = find(desktop_id)
    pids = sorted({window["pid"] for window in app_windows(entry, windows.clients()) if window["pid"] > 0})
    targets = [pid for pid in pids if stoppable(pid)]
    if not pids:
        raise ValueError(f"{entry['name']} is not running")
    if not targets:
        raise CommandError(f"{entry['name']} cannot be stopped from here")
    for pid in targets:
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and any(alive(pid) for pid in targets):
        time.sleep(0.05)
    forced = 0
    for pid in targets:
        if alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
                forced += 1
            except (ProcessLookupError, PermissionError):
                pass
    return {"ok": True, "id": entry["id"], "stopped": len(targets), "forced": forced}


def uninstall(desktop_id):
    entry = find(desktop_id)
    app_id = flatpak_id(entry)
    if not app_id or flatpak_scope(app_id) != "user":
        raise CommandError("Only apps installed for your user can be removed here")
    run(["flatpak", "uninstall", "--user", "-y", "--noninteractive", app_id], timeout=180)
    return {"ok": True, "id": entry["id"], "name": entry["name"]}


def copy_command(desktop_id):
    """Put the remove command for a package-managed app on the clipboard (never run it)."""
    command = info(desktop_id)["remove_command"]
    if not command:
        raise CommandError("There is no command to copy for this app")
    if not shutil.which("wl-copy"):
        raise CommandError("wl-copy is not installed")
    outcome = subprocess.run(["wl-copy"], input=command.encode(), timeout=8, check=False,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if outcome.returncode:
        raise CommandError("Could not copy to the clipboard")
    return {"ok": True, "copied": command}
