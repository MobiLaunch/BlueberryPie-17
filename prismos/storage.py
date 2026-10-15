"""Storage usage for Settings > Storage.

Reads sizes only. One bounded walk of the home directory attributes every
top-level entry to a category; symbolic links are never followed, other
filesystems are skipped and the walk stops at a fixed entry count or time so a
huge home directory cannot stall the shell. The one action, clearing window
previews, only touches PrismOS's own preview folder."""
import os
import shutil
import time
from pathlib import Path

from . import thumbnails

MAX_ENTRIES = 300_000
MAX_SECONDS = 6.0
CATEGORIES = (
    ("documents", "Documents"),
    ("downloads", "Downloads"),
    ("pictures", "Pictures"),
    ("music", "Music"),
    ("videos", "Videos"),
    ("apps", "App data"),
    ("cache", "Cache"),
    ("other", "Other files"),
)
FOLDERS = {"Documents": "documents", "Downloads": "downloads", "Pictures": "pictures",
           "Music": "music", "Videos": "videos", ".cache": "cache",
           ".local": "apps", ".config": "apps", ".var": "apps", ".mozilla": "apps"}


def category_of(name):
    return FOLDERS.get(name, "other")


def walk(top, device, budget):
    """Bytes on disk below ``top`` (files counted by allocated blocks)."""
    total = 0
    pending = [top]
    while pending and not budget["truncated"]:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if budget["entries"] >= MAX_ENTRIES or budget["clock"]() > budget["deadline"]:
                        budget["truncated"] = True
                        break
                    budget["entries"] += 1
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if info.st_dev != device:
                        continue
                    total += info.st_blocks * 512
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(entry.path)
        except OSError:
            continue
    return total


def usage(home=None, clock=time.monotonic):
    base = Path(home) if home else Path.home()
    disk = shutil.disk_usage(base)
    budget = {"entries": 0, "truncated": False, "clock": clock, "deadline": clock() + MAX_SECONDS}
    sizes = {key: 0 for key, _ in CATEGORIES}
    try:
        device = base.stat().st_dev
        with os.scandir(base) as entries:
            for entry in entries:
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if info.st_dev != device:
                    continue
                key = category_of(entry.name)
                sizes[key] += info.st_blocks * 512
                if entry.is_dir(follow_symlinks=False):
                    sizes[key] += walk(entry.path, device, budget)
    except OSError:
        pass
    items = [{"id": key, "label": label, "bytes": sizes[key]} for key, label in CATEGORIES]
    return {"ok": True, "total": disk.total, "used": disk.used, "free": disk.free,
            "items": items, "yours": sum(sizes.values()), "truncated": budget["truncated"],
            "previews": preview_bytes()}


def preview_bytes():
    total = 0
    try:
        for path in thumbnails.directory().iterdir():
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
    except OSError:
        pass
    return total


def clear_previews():
    thumbnails.clear()
    return {"ok": True, "previews": preview_bytes(), "message": "Window previews cleared"}
