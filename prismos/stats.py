"""CPU, memory and storage readings for the System widget. Reads /proc only."""
import os
import shutil
import time
from pathlib import Path


def _cpu_times(path):
    for line in Path(path).read_text().splitlines():
        if line.startswith("cpu "):
            values = [int(v) for v in line.split()[1:9]]
            idle = values[3] + values[4]  # idle + iowait
            return idle, sum(values)
    raise ValueError("No CPU line")


def cpu_percent(interval=0.25, path="/proc/stat"):
    try:
        idle_a, total_a = _cpu_times(path)
        time.sleep(interval)
        idle_b, total_b = _cpu_times(path)
    except (OSError, ValueError, IndexError):
        return None
    span = total_b - total_a
    return None if span <= 0 else max(0, min(100, round(100 * (1 - (idle_b - idle_a) / span))))


def memory(path="/proc/meminfo"):
    try:
        fields = {}
        for line in Path(path).read_text().splitlines():
            key, _, rest = line.partition(":")
            fields[key] = int(rest.split()[0])
        total, available = fields["MemTotal"], fields["MemAvailable"]
    except (OSError, ValueError, KeyError, IndexError):
        return None
    used = total - available
    return {"used_gib": round(used / 1048576, 1), "total_gib": round(total / 1048576, 1),
            "percent": round(100 * used / total) if total else 0}


def storage(path=None):
    try:
        usage = shutil.disk_usage(path or Path.home())
    except OSError:
        return None
    return {"used_gib": round((usage.total - usage.free) / 2**30, 1), "total_gib": round(usage.total / 2**30, 1),
            "percent": round(100 * (usage.total - usage.free) / usage.total) if usage.total else 0}


def snapshot(stat_path="/proc/stat", meminfo_path="/proc/meminfo", interval=0.25):
    try:
        load = round(os.getloadavg()[0], 2)
    except OSError:
        load = None
    return {"ok": True, "cpu": cpu_percent(interval, stat_path), "memory": memory(meminfo_path),
            "storage": storage(), "load": load}
