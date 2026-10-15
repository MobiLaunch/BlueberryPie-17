"""Read-only system facts for Settings > About. No commands are executed."""
import os
import platform
import shutil
from pathlib import Path

from . import __version__


def os_release(path="/etc/os-release"):
    values = {}
    try:
        for line in Path(path).read_text(errors="replace").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"')
    except OSError:
        pass
    return values


def cpu_model(path="/proc/cpuinfo"):
    try:
        for line in Path(path).read_text(errors="replace").splitlines():
            if line.lower().startswith(("model name", "hardware", "cpu model")):
                return " ".join(line.split(":", 1)[1].split())[:100]
    except (OSError, IndexError):
        pass
    return ""


def memory_gib(path="/proc/meminfo"):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 / 1024, 1)
    except (OSError, ValueError, IndexError):
        pass
    return None


def uptime_seconds(path="/proc/uptime"):
    try:
        return int(float(Path(path).read_text().split()[0]))
    except (OSError, ValueError, IndexError):
        return None


def info(release_path="/etc/os-release", cpuinfo="/proc/cpuinfo", meminfo="/proc/meminfo", uptime="/proc/uptime"):
    release = os_release(release_path)
    try:
        disk = shutil.disk_usage(Path.home())
        storage = {"total_gib": round(disk.total / 2**30, 1), "free_gib": round(disk.free / 2**30, 1)}
    except OSError:
        storage = None
    return {"ok": True, "prismos": __version__,
            "base": release.get("PRETTY_NAME") or release.get("NAME") or platform.system(),
            "kernel": platform.release(), "hostname": platform.node(), "architecture": platform.machine(),
            "cpu": cpu_model(cpuinfo), "memory_gib": memory_gib(meminfo), "uptime_seconds": uptime_seconds(uptime),
            "storage": storage,
            "session": os.environ.get("XDG_SESSION_TYPE", ""),
            "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "")}
