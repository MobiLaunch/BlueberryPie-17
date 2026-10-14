import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import settings


class CommandError(RuntimeError):
    pass


def run(args, timeout=4):
    if not shutil.which(args[0]):
        raise CommandError(f"{args[0]} is not installed")
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "LC_ALL": "C"}, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CommandError(f"{args[0]} did not respond") from error
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[:220]
        raise CommandError(detail or f"{args[0]} failed ({result.returncode})")
    return result.stdout.strip()


def wifi():
    try:
        enabled = run(["nmcli", "radio", "wifi"]) == "enabled"
        active = run(["nmcli", "-t", "--escape", "no", "-f", "NAME,TYPE", "connection", "show", "--active"])
        name = next((line.rsplit(":", 1)[0] for line in active.splitlines()
                     if line.rsplit(":", 1)[-1] in ("802-11-wireless", "wifi")), "Not connected")
        return {"available": True, "enabled": enabled, "label": name if enabled else "Off"}
    except CommandError as error:
        return {"available": False, "enabled": False, "label": str(error)}


def bluetooth():
    try:
        text = run(["bluetoothctl", "show"])
        if "Controller " not in text:
            raise CommandError("No Bluetooth controller")
        return {"available": True, "enabled": bool(re.search(r"Powered:\s+yes", text)), "label": "Bluetooth"}
    except CommandError as error:
        return {"available": False, "enabled": False, "label": str(error)}


def volume():
    try:
        text = run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
        match = re.search(r"Volume:\s+([0-9.]+)", text)
        if not match:
            raise CommandError("No audio output")
        return {"available": True, "value": min(100, round(float(match[1])*100)), "muted": "[MUTED]" in text}
    except CommandError as error:
        return {"available": False, "value": 0, "muted": False, "error": str(error)}


def brightness():
    try:
        current = int(run(["brightnessctl", "-c", "backlight", "get"]))
        maximum = int(run(["brightnessctl", "-c", "backlight", "max"]))
        if maximum <= 0:
            raise CommandError("No supported backlight")
        return {"available": True, "value": round(current*100/maximum)}
    except (CommandError, ValueError) as error:
        return {"available": False, "value": 0, "error": str(error)}


def battery():
    for path in sorted(Path("/sys/class/power_supply").glob("*")):
        try:
            if (path/"type").read_text().strip() == "Battery":
                return {"available": True, "value": int((path/"capacity").read_text()),
                        "charging": (path/"status").read_text().strip() == "Charging"}
        except (OSError, ValueError):
            continue
    return {"available": False, "value": None, "charging": False}


def status():
    readers = {"wifi": wifi, "bluetooth": bluetooth, "volume": volume, "brightness": brightness, "battery": battery}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {key: pool.submit(reader) for key, reader in readers.items()}
        result = {key: future.result() for key, future in futures.items()}
    result["settings"] = settings.load()
    return result


def percentage(value, minimum=0):
    if value is None:
        raise ValueError("A percentage value is required")
    number = float(value)
    if not minimum <= number <= 100:
        raise ValueError(f"Value must be between {minimum} and 100")
    return round(number)


def action(name, value=None):
    if name == "wifi":
        state = wifi()
        if not state["available"]:
            raise CommandError(state["label"])
        run(["nmcli", "radio", "wifi", "off" if state["enabled"] else "on"])
    elif name == "bluetooth":
        state = bluetooth()
        if not state["available"]:
            raise CommandError(state["label"])
        run(["bluetoothctl", "power", "off" if state["enabled"] else "on"])
    elif name == "volume":
        run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{percentage(value)}%"])
    elif name == "brightness":
        run(["brightnessctl", "-c", "backlight", "set", f"{percentage(value, 1)}%"])
    elif name == "mute":
        run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    elif name in ("dark", "reduced_motion", "dnd"):
        settings.toggle(name)
    elif name == "lock":
        config = os.environ.get("PRISM_HYPRLOCK_CONFIG", "/usr/share/prismos/config/hypr/hyprlock.conf")
        if not Path(config).is_file():
            config = str(Path(__file__).resolve().parent.parent/"config/hypr/hyprlock.conf")
        subprocess.Popen(["hyprlock", "--config", config], stdin=subprocess.DEVNULL, start_new_session=True)
    elif name == "network-settings":
        subprocess.Popen(["nm-connection-editor"], stdin=subprocess.DEVNULL, start_new_session=True)
    elif name == "bluetooth-settings":
        subprocess.Popen(["blueman-manager"], stdin=subprocess.DEVNULL, start_new_session=True)
    else:
        raise ValueError("Unknown system action")
    return {"ok": True, "action": name}
