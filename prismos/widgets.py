"""Which desktop widgets are shown. The catalog is fixed; users pick from it."""
from . import settings

CATALOG = [
    {"id": "glance", "title": "At a glance", "description": "Today's date with battery or weather", "default": True},
    {"id": "clock", "title": "Clock", "description": "Large digital clock", "default": True},
    {"id": "search", "title": "Search", "description": "Search apps, then the web", "default": True},
    {"id": "calendar", "title": "Calendar", "description": "This month at a glance", "default": True},
    {"id": "media", "title": "Now playing", "description": "Appears while a player is active", "default": True},
    {"id": "weather", "title": "Weather", "description": "Temperature and conditions (set up in Settings)", "default": False},
    {"id": "system", "title": "System", "description": "Processor, memory and storage", "default": False},
    {"id": "notes", "title": "Notes", "description": "A scratchpad that stays on your desktop", "default": False},
    {"id": "analog", "title": "Analog clock", "description": "A Material cookie-shaped clock", "default": False},
]
IDS = tuple(item["id"] for item in CATALOG)


def enabled():
    saved = settings.load()["widgets"]
    return saved if saved is not None else [item["id"] for item in CATALOG if item["default"]]


def status():
    return {"ok": True, "catalog": CATALOG, "enabled": enabled(), "sizes": settings.load()["widget_sizes"],
            "resizable": list(settings.RESIZABLE_WIDGETS)}


def resize(identifier, size):
    if identifier not in settings.RESIZABLE_WIDGETS:
        raise ValueError("That widget cannot be resized")
    if size not in settings.WIDGET_SIZES:
        raise ValueError("Size must be small, medium or large")
    settings.modify(lambda data: {**data, "widget_sizes": {**data["widget_sizes"], identifier: size}})
    return status()


def change(ids):
    clean = list(dict.fromkeys(ids or []))
    if any(item not in IDS for item in clean):
        raise ValueError("Unknown widget")
    ordered = [item for item in IDS if item in clean]  # catalog order keeps the layout stable
    settings.update(widgets=ordered)
    return {"ok": True, "enabled": ordered}
