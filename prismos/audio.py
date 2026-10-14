"""PipeWire device discovery and WirePlumber controls, without parsing UI trees."""
import json
import math
import re
from concurrent.futures import ThreadPoolExecutor

from .system import CommandError, percentage, run

KINDS = {"output": "Audio/Sink", "input": "Audio/Source"}


def level(target):
    try:
        text = run(["wpctl", "get-volume", str(target)])
        match = re.fullmatch(r"Volume:\s+([0-9]+(?:\.[0-9]+)?)(\s+\[MUTED\])?", text)
        if not match or not math.isfinite(float(match[1])):
            raise CommandError("The audio device did not report a valid volume")
        return {"available": True, "value": min(100, round(float(match[1]) * 100)), "muted": bool(match[2])}
    except CommandError as error:
        return {"available": False, "value": 0, "muted": False, "error": str(error)}


def default_level(kind):
    return level("@DEFAULT_AUDIO_SINK@" if kind == "output" else "@DEFAULT_AUDIO_SOURCE@")


def unsigned(value, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, str)) or not re.fullmatch(r"[0-9]+", str(value)):
        return None
    number = int(value)
    return number if 0 < number <= maximum else None


def properties(item):
    info = item.get("info")
    props = info.get("props") if isinstance(info, dict) else item.get("props")
    return props if isinstance(props, dict) else {}


def graph():
    try:
        data = json.loads(run(["pw-dump", "--no-colors"], timeout=5))
    except (ValueError, TypeError):
        raise CommandError("PipeWire returned invalid device data") from None
    if not isinstance(data, list):
        raise CommandError("PipeWire returned invalid device data")
    devices, defaults, seen = [], {}, set()
    for item in data:
        if not isinstance(item, dict):
            continue
        props = properties(item)
        if item.get("type") == "PipeWire:Interface:Metadata" and props.get("metadata.name") == "default":
            metadata = item.get("metadata")
            for entry in metadata if isinstance(metadata, list) else []:
                if (not isinstance(entry, dict) or entry.get("subject") != 0 or
                        entry.get("key") not in ("default.audio.sink", "default.audio.source")):
                    continue
                value = entry.get("value")
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        continue
                if isinstance(value, dict) and isinstance(value.get("name"), str):
                    defaults[entry.get("key")] = value["name"]
        if item.get("type") != "PipeWire:Interface:Node":
            continue
        media = props.get("media.class")
        kind = next((name for name, value in KINDS.items() if value == media), None)
        identifier = unsigned(item.get("id"), 2**32 - 1)
        serial = unsigned(props.get("object.serial"), 2**64 - 1)
        name = props.get("node.name")
        if (not kind or identifier is None or serial is None or serial in seen or
                not isinstance(name, str) or not name):
            continue
        if kind == "input" and (props.get("device.class") == "monitor" or name.endswith(".monitor")):
            continue
        seen.add(serial)
        label = next((props[key] for key in ("node.description", "node.nick", "node.name")
                      if isinstance(props.get(key), str) and props[key].strip()), name)
        devices.append({"id": identifier, "serial": str(serial), "name": name,
                        "label": " ".join(label.split())[:180], "kind": kind})
    for device in devices:
        key = "default.audio.sink" if device["kind"] == "output" else "default.audio.source"
        device["selected"] = device["name"] == defaults.get(key)
    return sorted(devices, key=lambda device: (not device["selected"], device["label"].casefold(), device["serial"]))


def snapshot():
    try:
        devices = graph()
    except CommandError as error:
        return {"available": False, "outputs": [], "inputs": [], "output": None, "input": None, "error": str(error)}
    current = {kind: next((d for d in devices if d["kind"] == kind and d["selected"]), None) for kind in KINDS}

    def read(kind):
        device = current[kind]
        return {**device, **level(device["id"])} if device else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = dict(zip(KINDS, pool.map(read, KINDS)))
    return {"available": True, "outputs": [d for d in devices if d["kind"] == "output"],
            "inputs": [d for d in devices if d["kind"] == "input"], **values}


def action(operation, kind, serial, name, value=None):
    if kind not in KINDS or operation not in ("select", "volume", "mute"):
        raise ValueError("Choose a supported audio device and action")
    number = unsigned(serial, 2**64 - 1)
    if number is None or not isinstance(name, str) or not name or len(name) > 1024:
        raise ValueError("Choose an available audio device")
    if operation == "volume":
        value = f"{percentage(value)}%"
    elif operation == "mute" and value not in ("0", "1"):
        raise ValueError("Mute must be 0 or 1")
    # Resolve a lifetime serial against a fresh graph. Cached/reused node IDs
    # from a previous selection are never accepted as a mutation target.
    device = next((d for d in graph() if d["serial"] == str(number) and d["kind"] == kind and d["name"] == name), None)
    if not device:
        raise CommandError("That device is no longer available. Refresh and choose another.")
    identifier = str(device["id"])
    if operation == "select":
        run(["wpctl", "set-default", identifier])
    elif operation == "volume":
        run(["wpctl", "set-volume", identifier, value, "--limit", "1.0"])
    else:
        run(["wpctl", "set-mute", identifier, value])
    return {"ok": True, "action": operation}
