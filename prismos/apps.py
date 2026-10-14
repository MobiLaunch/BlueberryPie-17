import configparser
import os
import shutil
import subprocess
from pathlib import Path

from . import settings
from .system import CommandError, run

# First matching group wins, so order expresses priority for multi-category apps.
CATEGORY_GROUPS = (
    ("Games", {"Game"}),
    ("Internet", {"Network", "WebBrowser", "Email", "Chat", "InstantMessaging", "News", "FileTransfer", "P2P"}),
    ("Develop", {"Development", "IDE", "Debugger", "WebDevelopment"}),
    ("Media", {"AudioVideo", "Audio", "Video", "Music", "Player", "Recorder", "Graphics", "Photography",
               "2DGraphics", "3DGraphics", "RasterGraphics", "VectorGraphics", "Viewer"}),
    ("Office", {"Office", "WordProcessor", "Spreadsheet", "Presentation", "Calendar", "ContactManagement", "Finance"}),
    ("Education", {"Education", "Science", "Math", "Languages"}),
    ("System", {"System", "Settings", "Monitor", "PackageManager", "Security", "TerminalEmulator", "HardwareSettings"}),
    ("Utilities", {"Utility", "Accessibility", "Archiving", "Calculator", "FileManager", "TextEditor", "Clock"}),
)


def categorize(raw):
    found = set(filter(None, (raw or "").split(";")))
    return next((name for name, members in CATEGORY_GROUPS if found & members), "Other")


def roots():
    home = Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    # Flatpak --user exports desktop entries beneath the XDG data home, not
    # directly within its applications/ directory. Also include system exports
    # if a minimal greetd session has not set the Flatpak XDG_DATA_DIRS yet.
    paths = [home/"applications", home/"flatpak/exports/share/applications",
             Path("/var/lib/flatpak/exports/share/applications")]
    paths += [Path(p)/"applications" for p in os.environ.get(
        "XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if p]
    return list(dict.fromkeys(paths))


def entries():
    seen = set()
    result = []
    for root in roots():
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.desktop")):
            desktop_id = "-".join(path.relative_to(root).parts)
            if desktop_id in seen:
                continue
            seen.add(desktop_id)  # Hidden user overrides still hide system entries.
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
                data = parser["Desktop Entry"]
                if data.get("Type") != "Application" or data.getboolean("Hidden", fallback=False) or data.getboolean("NoDisplay", fallback=False):
                    continue
                desktops = set(os.environ.get("XDG_CURRENT_DESKTOP", "Hyprland:PrismOS").split(":"))
                only = set(filter(None, data.get("OnlyShowIn", "").split(";")))
                excluded = set(filter(None, data.get("NotShowIn", "").split(";")))
                if (only and not desktops.intersection(only)) or desktops.intersection(excluded):
                    continue
                try_exec = data.get("TryExec")
                if try_exec and not shutil.which(try_exec):
                    continue
                if not data.get("Name") or not (data.get("Exec") or data.getboolean("DBusActivatable", fallback=False)):
                    continue
                result.append({"id": desktop_id, "name": data["Name"], "icon": data.get("Icon", "application-x-executable"),
                               "startupClass": data.get("StartupWMClass", ""),
                               "description": data.get("Comment", ""), "path": str(path.resolve()),
                               "category": categorize(data.get("Categories", "")),
                               "keywords": " ".join(filter(None, data.get("Keywords", "").split(";")))[:200]})
            except (configparser.Error, OSError, UnicodeError, ValueError, KeyError):
                continue
    return sorted(result, key=lambda item: item["name"].casefold())


def launch(desktop_id):
    entry = next((item for item in entries() if item["id"] == desktop_id), None)
    if entry is None:
        raise ValueError("Application is no longer installed or visible")
    # gio implements Desktop Entry field codes and terminal/DBus semantics.
    # Never pass the Exec line through sh, eval, or string interpolation.
    run(["gio", "launch", entry["path"]], timeout=8)
    try:
        # Recents are a convenience; never let bookkeeping fail a launch.
        settings.modify(lambda data: {**data, "recent_apps": [desktop_id] + [
            item for item in data.get("recent_apps") or [] if item != desktop_id]})
    except OSError:
        pass
    return {"ok": True, "id": desktop_id, "name": entry["name"]}
