"""Screen recording with wf-recorder. Files go to ~/Videos/Screen recordings.

One recording at a time. The recorder runs detached; a small state file in the login's runtime
directory remembers its process id, file and start time so the shell can show a timer and stop it
later, even after the shell restarts. Only fixed argv lists are run: the area comes from slurp and
must match a strict `x,y wxh` pattern, the output name from hyprctl must match a strict pattern, and
the file name is built here. Stopping sends SIGINT, which makes wf-recorder finish the file."""
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

from . import settings
from .system import CommandError, run

MODES = ("full", "area", "window")
REGION = re.compile(r"-?\d{1,6},-?\d{1,6} \d{1,6}x\d{1,6}\Z")
OUTPUT = re.compile(r"[A-Za-z0-9_.:-]{1,32}\Z")


def folder():
    return Path.home() / "Videos" / "Screen recordings"


def state_path():
    base = os.environ.get("XDG_RUNTIME_DIR")
    return Path(base) / "prismos-recording.json" if base else Path(settings.directory()) / "recording.json"


def available():
    return bool(shutil.which("wf-recorder"))


def alive(pid):
    try:
        argv = Path(f"/proc/{int(pid)}/cmdline").read_bytes().split(b"\0")
    except (OSError, ValueError, TypeError):
        return False
    return bool(argv) and os.path.basename(argv[0].decode(errors="replace")) == "wf-recorder"


def read_state():
    try:
        data = json.loads(state_path().read_text())
        pid, started, path = int(data["pid"]), float(data["started"]), str(data["path"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not alive(pid):
        state_path().unlink(missing_ok=True)
        return None
    return {"pid": pid, "started": started, "path": path}


def write_state(pid, path, started):
    target = state_path()
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=target.parent, prefix=".recording-")
    try:
        with os.fdopen(handle, "w") as stream:
            json.dump({"pid": pid, "path": path, "started": started}, stream)
        os.chmod(temp, 0o600)
        os.replace(temp, target)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def status(now=None):
    if not available():
        return {"available": False, "recording": False, "seconds": 0, "label": "Needs the wf-recorder package",
                "audio": settings.load()["record_audio"]}
    state = read_state()
    seconds = max(0, int((now if now is not None else time.time()) - state["started"])) if state else 0
    return {"available": True, "recording": state is not None, "seconds": seconds,
            "started": state["started"] if state else 0, "audio": settings.load()["record_audio"]}


def focused_output():
    try:
        monitors = json.loads(run(["hyprctl", "-j", "monitors"], timeout=4))
        name = next(m["name"] for m in monitors if m.get("focused")) if monitors else None
    except (ValueError, KeyError, TypeError, StopIteration, CommandError):
        name = None  # no compositor query: let the recorder use its default screen
    if name is not None and not OUTPUT.fullmatch(str(name)):
        raise ValueError("The screen name is not usable")
    return name


def window_region():
    try:
        window = json.loads(run(["hyprctl", "-j", "activewindow"], timeout=4))
        x, y = (int(v) for v in window["at"])
        width, height = (int(v) for v in window["size"])
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("No window is focused") from error
    if width < 1 or height < 1:
        raise ValueError("No window is focused")
    return f"{x},{y} {width}x{height}"


def choose_region(mode):
    if mode == "window":
        return window_region()
    try:
        chosen = run(["slurp", "-d"], timeout=90)
    except CommandError as error:
        raise ValueError("Recording cancelled") from error
    if not REGION.fullmatch(chosen):
        raise ValueError("Recording cancelled")
    return chosen


def new_path(now=None):
    directory = folder()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    stem = (now or datetime.now()).strftime("Recording-%Y-%m-%d-%H%M%S")
    path, counter = directory / f"{stem}.mp4", 1
    while path.exists():
        counter += 1
        path = directory / f"{stem}-{counter}.mp4"
    return path


def start(mode="full", now=None):
    if mode not in MODES:
        raise ValueError("Unknown recording mode")
    if not available():
        raise CommandError("Screen recording needs the wf-recorder package")
    if mode == "area" and not shutil.which("slurp"):
        raise CommandError("Recording an area needs the slurp package")
    if read_state() is not None:
        raise CommandError("A recording is already running")
    region = None if mode == "full" else choose_region(mode)
    output = focused_output() if mode == "full" else None
    path = new_path(now)
    argv = ["wf-recorder", "-f", str(path)]
    if region:
        argv += ["-g", region]
    elif output:
        argv += ["-o", output]
    if settings.load()["record_audio"]:
        argv += ["--audio"]
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        raise CommandError("The recorder could not start") from None
    time.sleep(0.4)
    if process.poll() is not None:
        raise CommandError("The recorder could not start. Check that this screen can be recorded.")
    write_state(process.pid, str(path), time.time() if now is None else now.timestamp())
    return {"ok": True, "recording": True, "path": str(path)}


def stop(wait=8.0):
    state = read_state()
    if state is None:
        raise CommandError("No recording is running")
    try:
        os.kill(state["pid"], signal.SIGINT)
    except OSError:
        pass
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline and alive(state["pid"]):
        time.sleep(0.1)
    if alive(state["pid"]):
        try:
            os.kill(state["pid"], signal.SIGTERM)
        except OSError:
            pass
    state_path().unlink(missing_ok=True)
    path = Path(state["path"])
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    if size == 0:
        raise CommandError("The recording was not saved")
    return {"ok": True, "recording": False, "path": str(path), "name": path.name, "size": size}


def toggle(mode="full"):
    return stop() if read_state() is not None else start(mode)


def set_audio(value):
    if value not in ("yes", "no"):
        raise ValueError("Audio must be yes or no")
    settings.update(record_audio=value == "yes")
    return status()
