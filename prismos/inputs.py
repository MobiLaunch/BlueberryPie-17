"""Validated, user-scoped Hyprland input preferences for PrismOS.

Only fixed Hyprland keys and typed numeric/boolean values may be applied.
Never edits the user's personal Hyprland config or executes arbitrary commands.
"""
from . import regional, settings
from .system import run

KEYS = {
    "natural_scroll": "input:touchpad:natural_scroll",
    "tap_to_click": "input:touchpad:tap_to_click",
    "pointer_speed": "input:sensitivity",
    "repeat_rate": "input:repeat_rate",
}


def value(name, raw):
    if name in ("tap_to_click", "natural_scroll"):
        if raw not in ("true", "false"):
            raise ValueError("Expected true or false")
        return raw == "true"
    if name == "pointer_speed":
        if raw is None:
            raise ValueError("Pointer speed is required")
        try:
            speed = float(raw)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid pointer speed") from error
        if not -1 <= speed <= 1:
            raise ValueError("Pointer speed must be between -1 and 1")
        return round(speed, 2)
    if name == "repeat_rate":
        if raw is None or not str(raw).isdigit():
            raise ValueError("Invalid repeat rate")
        rate = int(raw)
        if not 10 <= rate <= 60:
            raise ValueError("Repeat rate must be between 10 and 60")
        return rate
    raise ValueError("Unknown input setting")


def serialized(item):
    if isinstance(item, bool):
        return "true" if item else "false"
    return str(item)


def apply_one(name, selected):
    run(["hyprctl", "keyword", KEYS[name], serialized(selected)], timeout=5)


def list_settings():
    current = settings.load()
    return {"ok": True, "settings": {**{name: current[name] for name in KEYS}, "keyboard": current["keyboard"]},
            "layouts": [{"id": item[0], "label": item[1]} for item in regional.KEYBOARDS]}


def apply_keyboard(identifier):
    layout = regional.keyboard(identifier)
    run(["hyprctl", "keyword", "input:kb_layout", layout["layout"]], timeout=5)
    run(["hyprctl", "keyword", "input:kb_variant", layout["variant"]], timeout=5)


def change(name, raw):
    if name == "keyboard":
        if raw not in regional.KEYBOARD_IDS:
            raise ValueError("Unknown keyboard layout")
        apply_keyboard(raw)  # an error here must not persist a layout that did not apply
        settings.update(keyboard=raw)
        return list_settings()
    new_value = value(name, raw)
    # An error should be visible rather than falsely persisting a failed change.
    apply_one(name, new_value)
    settings.update(**{name: new_value})
    return list_settings()


def apply():
    # Called from PrismOS session autostart. Does not modify global user files.
    current = settings.load()
    for name in KEYS:
        apply_one(name, current[name])
    apply_keyboard(current["keyboard"])
    return {"ok": True, "applied": True}
