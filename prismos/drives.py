"""Removable volume browser/mount actions, backed by lsblk and UDisks2.

Never mounts a supplied arbitrary path or modifies a root/internal device.
UDisks2 handles polkit authorization and encryption prompts.
"""
import json
import re
import shutil
import subprocess

from .system import CommandError, run

DEVICE_RE = re.compile(r"/dev/[A-Za-z0-9_.-]{1,100}\Z")


def _bool(value):
    return value is True or str(value).lower() in ("1", "true")


def volumes():
    data = json.loads(run(["lsblk", "--json", "--paths", "--output",
                           "PATH,NAME,LABEL,FSTYPE,MOUNTPOINT,RM,TRAN,TYPE"], timeout=8))
    result = []
    def scan(records, removable=False):
        for item in records or []:
            if not isinstance(item, dict):
                continue
            rm = removable or _bool(item.get("rm")) or item.get("tran") == "usb"
            kind = item.get("type")
            if rm and kind in ("part", "disk") and item.get("fstype"):
                path = item.get("path")
                if isinstance(path, str) and DEVICE_RE.fullmatch(path):
                    result.append({
                        "device": path,
                        "label": str(item.get("label") or item.get("name") or path)[:100],
                        "mountpoint": item.get("mountpoint") or "",
                        "filesystem": str(item.get("fstype"))[:40],
                        "mounted": bool(item.get("mountpoint")),
                    })
            scan(item.get("children"), rm)
    if not isinstance(data, dict) or not isinstance(data.get("blockdevices"), list):
        raise CommandError("Could not read removable devices")
    scan(data["blockdevices"])
    return {"ok": True, "items": result[:32], "available": bool(shutil.which("udisksctl"))}


def change(operation, device):
    if operation not in ("mount", "unmount"):
        raise ValueError("Unsupported drive operation")
    if not isinstance(device, str) or not DEVICE_RE.fullmatch(device):
        raise ValueError("Select a removable drive")
    active = next((entry for entry in volumes()["items"] if entry["device"] == device), None)
    if not active:
        raise ValueError("The removable drive is no longer available")
    if operation == "mount" and active["mounted"]:
        return {"ok": True, "message": "Drive is already mounted"}
    if operation == "unmount" and not active["mounted"]:
        return {"ok": True, "message": "Drive is already unmounted"}
    if not shutil.which("udisksctl"):
        raise CommandError("UDisks2 is not installed")
    args = ["udisksctl", operation, "--block-device", device]
    output = run(args, timeout=90)
    return {"ok": True, "message": output.strip() or
            ("Drive mounted" if operation == "mount" else "Drive safely unmounted")}
