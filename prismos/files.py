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


# Per-user Files clipboard persists between short-lived prismctl commands. Entries
# hold paths, not file bytes; moving happens only when the user requests Paste.
import json
import tempfile
import time


def _exists(path):
    return path.exists() or path.is_symlink()


def _clipboard_file():
    root = Path(os.environ.get("XDG_RUNTIME_DIR", "")) if os.environ.get("XDG_RUNTIME_DIR") else (
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")))
    root = root / "prismos"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root / "file-clipboard.json"


def clipboard_status():
    try:
        path = _clipboard_file()
        info = json.loads(path.read_text())
        if info.get("action") not in ("copy", "cut") or not isinstance(info.get("path"), str):
            raise ValueError("Invalid clipboard state")
        source = location(info["path"])
        if time.time() - float(info.get("created", 0)) > 4 * 3600 or not _exists(source):
            raise ValueError("Clipboard item expired")
        return {"ok": True, "has_item": True, "action": info["action"],
                "name": source.name, "path": str(source)}
    except (OSError, ValueError, TypeError):
        return {"ok": True, "has_item": False}


def stage(raw, action):
    if action not in ("copy", "cut"):
        raise ValueError("Choose Copy or Cut")
    source = location(raw)
    if not _exists(source) or source == source.parent:
        raise ValueError("Select a file or folder")
    state = _clipboard_file()
    data = json.dumps({"action": action, "path": str(source), "created": time.time()})
    fd, temporary = tempfile.mkstemp(dir=state.parent, prefix=".clipboard-")
    try:
        with os.fdopen(fd, "w") as output:
            output.write(data)
        os.chmod(temporary, 0o600)
        os.replace(temporary, state)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"ok": True, "message": ("Ready to move " if action == "cut"
                                     else "Ready to copy ") + source.name}


def transfer(source, folder, move=False):
    source = location(source)
    folder = location(folder)
    if not _exists(source) or source == source.parent:
        raise ValueError("The selected file or folder is unavailable")
    if not folder.is_dir():
        raise ValueError("Choose a destination folder")
    destination = folder / source.name
    if _exists(destination):
        raise ValueError("An item with this name already exists in the destination")
    # Compare actual directories to prevent recursively copying/moving a parent
    # into itself, including through aliases and symbolic links.
    if source.is_dir() and not source.is_symlink():
        actual_source = source.resolve()
        actual_folder = folder.resolve()
        if actual_folder == actual_source or actual_source in actual_folder.parents:
            raise ValueError("A folder cannot be placed inside itself")
    if move:
        # Cross-device moves are handled by GIO with no shell interpolation.
        # GIO reports failures instead of silently replacing existing names.
        if not shutil.which("gio"):
            raise CommandError("GIO is required to move files")
        result = subprocess.run(["gio", "move", "--no-target-directory", "--",
                                 str(source), str(destination)], timeout=180,
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise CommandError((result.stderr or "Move failed").strip()[:500])
    elif source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        # Exclusive-create means a race cannot overwrite an existing file.
        with source.open("rb") as original, destination.open("xb") as output:
            shutil.copyfileobj(original, output, length=1024 * 1024)
        shutil.copystat(source, destination)
    return {"ok": True, "path": str(destination),
            "message": ("Moved " if move else "Copied ") + source.name}


def paste(folder):
    state = clipboard_status()
    if not state["has_item"]:
        raise ValueError("Copy or cut an item before pasting")
    result = transfer(state["path"], folder, move=state["action"] == "cut")
    if state["action"] == "cut":
        _clipboard_file().unlink(missing_ok=True)
    return result
