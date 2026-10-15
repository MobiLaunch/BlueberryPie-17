"""Wallpaper choices from the user's pictures, with Material You color extraction.

Only still images inside the user's home directory are accepted. The shell shows
the chosen file directly; PrismOS never copies, uploads or modifies it.
"""
import os
from hashlib import sha256
from pathlib import Path

from . import settings, theme

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 80_000_000
MAX_CHOICES = 36


def folders():
    pictures = Path.home() / "Pictures"
    return [pictures / "Wallpapers", pictures]


def _inside_home(path):
    try:
        path.relative_to(Path.home().resolve())
        return True
    except ValueError:
        return False


def validate(raw):
    """Return a resolved image path inside the home directory, or raise ValueError."""
    if not isinstance(raw, str) or not raw or len(raw) > 4096 or "\0" in raw:
        raise ValueError("Choose a picture")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ValueError("A wallpaper must be an absolute path")
    path = path.resolve()
    if path.suffix.lower() not in EXTENSIONS:
        raise ValueError("Wallpapers must be PNG, JPEG or WebP pictures")
    if not _inside_home(path) or not path.is_file():
        raise ValueError("Choose a picture from your home folder")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("That picture is too large to use as a wallpaper")
    return path


def thumbnail(path):
    """Cached 320 px preview, or an empty string if the picture cannot be decoded."""
    try:
        from PIL import Image, ImageOps
        info = path.stat()
        key = sha256(f"{path}:{info.st_mtime_ns}:{info.st_size}".encode("utf-8", "surrogateescape")).hexdigest()[:40]
        cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "prismos/wallpapers"
        cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        output = cache / (key + ".png")
        if not output.is_file():
            Image.MAX_IMAGE_PIXELS = MAX_PIXELS
            with Image.open(path) as opened:
                opened.draft("RGB", (640, 640))
                image = ImageOps.exif_transpose(opened)
                image.thumbnail((320, 320))
                image.convert("RGB").save(output, "PNG")
        return output.as_uri()
    except Exception:  # decoders raise many types; a bad picture just has no preview
        return ""


def candidates():
    seen, items = set(), []
    for folder in folders():
        if not folder.is_dir():
            continue
        for entry in sorted(folder.iterdir(), key=lambda p: p.name.casefold()):
            try:
                path = validate(str(entry))
            except (ValueError, OSError):
                continue
            if path in seen:
                continue
            seen.add(path)
            items.append({"name": entry.stem, "path": str(path), "thumbnail": thumbnail(path)})
            if len(items) >= MAX_CHOICES:
                return items
    return items


def status():
    return {"ok": True, "current": settings.load()["wallpaper"], "items": candidates()}


def choose(raw):
    path = validate(raw)
    seed = theme.wallpaper_seed(path)
    settings.update(wallpaper=str(path), seed=seed)
    return {"ok": True, "current": str(path), "seed": seed}


def clear():
    settings.update(wallpaper="")
    return {"ok": True, "current": ""}
