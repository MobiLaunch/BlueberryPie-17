"""Safe, user-scoped file browsing and basic file actions for Prism Files.

Operations use pathlib/GIO with argument arrays; no shell interpolation, root,
arbitrary code execution, privilege changes or raw file contents are exposed.
"""
import mimetypes
import os
from pathlib import Path
import shutil
import subprocess

from .system import CommandError

MAX_ITEMS = 700
MAX_PATH = 4096


def location(raw):
    if not isinstance(raw, str) or not raw or len(raw) > MAX_PATH or "\0" in raw:
        raise ValueError("Select a valid location")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("A location must be an absolute path")
    # Keep symlinks as file entries. Resolving symlinks before rename/trash
    # would target the destination rather than the selected symlink itself.
    return Path(os.path.abspath(path))


def filename(raw):
    if (not isinstance(raw, str) or not (1 <= len(raw) <= 150)
            or raw in (".", "..") or "/" in raw or "\x00" in raw
            or "\\" in raw or raw.rstrip(" .") != raw):
        raise ValueError("Enter a valid filename without path separators")
    return raw


def format_size(size):
    if size < 1024:
        return str(size) + " B"
    for unit in ("KB", "MB", "GB", "TB"):
        size /= 1024
        if size < 1024 or unit == "TB":
            return "%.1f %s" % (size, unit)


def home():
    return str(Path.home())


def bookmarks():
    root = Path.home()
    defaults = [
        ("Home", root, "⌂"), ("Desktop", root / "Desktop", "▣"),
        ("Documents", root / "Documents", "▤"),
        ("Downloads", root / "Downloads", "↓"),
        ("Pictures", root / "Pictures", "◈"),
        ("Music", root / "Music", "♫"),
        ("Videos", root / "Videos", "▷"),
    ]
    # Optional mounts are discovered by the portal/file-manager stack.
    return {"ok": True, "items": [
        {"name": name, "path": str(path), "symbol": symbol}
        for name, path, symbol in defaults if path.is_dir()
    ]}


def browse(raw=None, hidden=False):
    path = location(raw or home())
    if not path.is_dir():
        raise ValueError("That folder is no longer available")
    items = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
        for entry in entries:
            if len(items) == MAX_ITEMS:
                break
            if not hidden and entry.name.startswith("."):
                continue
            try:
                info = entry.stat()
                folder = entry.is_dir()
            except (OSError, ValueError):
                continue
            mimetype = "inode/directory" if folder else (
                mimetypes.guess_type(entry.name)[0] or "application/octet-stream")
            items.append({
                "name": entry.name,
                "path": str(entry),
                "directory": folder,
                "hidden": entry.name.startswith("."),
                "symbol": "▣" if folder else "◈" if mimetype.startswith("image/") else
                          "♫" if mimetype.startswith("audio/") else
                          "▷" if mimetype.startswith("video/") else "▤",
                "type": mimetype,
                "size": "" if folder else format_size(info.st_size),
            })
    except (PermissionError, OSError) as error:
        raise CommandError("Cannot read folder: " + str(error)) from error
    return {"ok": True, "path": str(path),
            "parent": str(path.parent), "items": items,
            "more": len(entries) > MAX_ITEMS, "hidden": bool(hidden)}


def open_item(raw):
    path = location(raw)
    if not path.exists():
        raise ValueError("The selected file no longer exists")
    # xdg-open defers to the user's file/mime associations.
    subprocess.Popen(["xdg-open", str(path)], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return {"ok": True, "message": "Opening " + path.name}


def create_folder(raw, name):
    parent = location(raw)
    if not parent.is_dir():
        raise ValueError("Choose an existing parent folder")
    destination = parent / filename(name)
    destination.mkdir(mode=0o755, exist_ok=False)
    return {"ok": True, "path": str(destination), "message": "Folder created"}


def rename(raw, name):
    source = location(raw)
    destination = source.with_name(filename(name))
    if not source.exists():
        raise ValueError("The selected item no longer exists")
    if destination.exists():
        raise ValueError("A file or folder with that name already exists")
    if source == destination:
        return {"ok": True, "path": str(source)}
    source.rename(destination)
    return {"ok": True, "path": str(destination), "message": "Item renamed"}


def trash(raw):
    path = location(raw)
    if not path.exists():
        raise ValueError("The selected item no longer exists")
    if path == Path.home() or path.parent == path:
        raise ValueError("Cannot trash this special folder")
    if not shutil.which("gio"):
        raise CommandError("GIO trash support is not installed")
    result = subprocess.run(["gio", "trash", "--", str(path)],
                            capture_output=True, text=True, timeout=40, check=False)
    if result.returncode:
        raise CommandError((result.stderr or "Failed to move to Trash").strip()[:500])
    return {"ok": True, "message": "Moved to Trash"}
