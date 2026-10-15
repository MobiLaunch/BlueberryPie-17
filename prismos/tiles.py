"""Which Quick Settings tiles are shown, and in what order. The catalog is fixed."""
from . import settings

# id -> large tile (shows a title and state) rather than a compact icon tile.
CATALOG = [
    {"id": "wifi", "title": "Wi-Fi", "large": True, "default": True},
    {"id": "bluetooth", "title": "Bluetooth", "large": True, "default": True},
    {"id": "sound", "title": "Sound", "large": True, "default": True},
    {"id": "microphone", "title": "Microphone", "large": True, "default": True},
    {"id": "dnd", "title": "Do Not Disturb", "large": False, "default": True},
    {"id": "dark", "title": "Dark theme", "large": False, "default": True},
    {"id": "reduced_motion", "title": "Reduced motion", "large": False, "default": True},
    {"id": "audio_devices", "title": "Audio devices", "large": False, "default": True},
    {"id": "airplane", "title": "Airplane mode", "large": False, "default": False},
    {"id": "battery_saver", "title": "Battery Saver", "large": False, "default": False},
    {"id": "night_light", "title": "Night Light", "large": False, "default": False},
    {"id": "screenshot", "title": "Screenshot", "large": False, "default": False},
    {"id": "lock", "title": "Lock screen", "large": False, "default": False},
    {"id": "hotspot", "title": "Hotspot", "large": False, "default": False},
    {"id": "vpn", "title": "VPN", "large": False, "default": False},
]
IDS = tuple(item["id"] for item in CATALOG)
assert IDS == settings.TILE_IDS


def enabled():
    saved = settings.load()["tiles"]
    return saved if saved is not None else [item["id"] for item in CATALOG if item["default"]]


def status():
    return {"ok": True, "catalog": CATALOG, "enabled": enabled()}


def change(ids):
    clean = list(dict.fromkeys(ids or []))
    if any(item not in IDS for item in clean):
        raise ValueError("Unknown tile")
    if not clean:
        raise ValueError("Keep at least one tile")
    settings.update(tiles=clean)
    return {"ok": True, "enabled": clean}


def reset():
    settings.update(tiles=None)
    return status()
