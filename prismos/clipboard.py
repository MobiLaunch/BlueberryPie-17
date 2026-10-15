"""Opt-in clipboard history with cliphist and wl-clipboard.

History is off until the user turns it on, because a clipboard can hold passwords.
Entries are addressed by the numeric id cliphist assigns; no other text from the
history reaches a command line. Copying streams `cliphist decode ID` into `wl-copy`
through a pipe, so bytes (including images) are never re-interpreted."""
import json
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path

from . import settings
from .system import CommandError, run

ID = re.compile(r"\d{1,18}\Z")
LIMIT = 40
WATCHERS = (["wl-paste", "--type", "text", "--watch", "cliphist", "store"],
            ["wl-paste", "--type", "image", "--watch", "cliphist", "store"])


def available():
    return bool(shutil.which("cliphist") and shutil.which("wl-copy") and shutil.which("wl-paste"))


def state_file():
    base = Path(os.environ.get("XDG_RUNTIME_DIR") or settings.directory())
    return base / "prismos-clipboard.json"


def _alive(pid):
    try:
        argv = Path(f"/proc/{int(pid)}/cmdline").read_bytes().split(b"\0")
    except (OSError, ValueError):
        return False
    return bool(argv) and argv[0].endswith(b"wl-paste") and b"cliphist" in argv


def running():
    try:
        pids = json.loads(state_file().read_text())
    except (OSError, ValueError):
        return False
    return isinstance(pids, list) and any(type(pid) is int and _alive(pid) for pid in pids)


def check(identity):
    if not isinstance(identity, str) or not ID.fullmatch(identity):
        raise ValueError("Invalid clipboard entry")
    return identity


def entries():
    lines = run(["cliphist", "list"], timeout=6).splitlines()
    found = []
    for line in lines[:LIMIT]:
        identity, _, preview = line.partition("\t")
        if not ID.fullmatch(identity):
            continue
        clean = re.sub(r"[\x00-\x1f\x7f]", " ", preview).strip()
        image = clean.startswith("[[ binary data")
        found.append({"id": identity, "kind": "image" if image else "text",
                      "preview": "Image" if image else clean[:120]})
    return found


def status(items=True):
    enabled = settings.load()["clipboard_history"]
    ready = available()
    result = {"ok": True, "enabled": enabled, "available": ready, "running": running() if ready else False, "items": []}
    if items and ready and enabled:
        result["items"] = entries()
    return result


def start():
    if not available():
        raise CommandError("Clipboard history needs cliphist and wl-clipboard")
    if running():
        return
    pids = []
    for argv in WATCHERS:
        pids.append(subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True).pid)
    state_file().parent.mkdir(parents=True, exist_ok=True)
    state_file().write_text(json.dumps(pids))


def stop():
    try:
        pids = json.loads(state_file().read_text())
    except (OSError, ValueError):
        return
    for pid in pids if isinstance(pids, list) else []:
        if type(pid) is int and _alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    try:
        state_file().unlink()
    except OSError:
        pass


def enable(on):
    if on:
        start()
        settings.update(clipboard_history=True)
    else:
        settings.update(clipboard_history=False)
        stop()
    return status()


def resume():
    """Session start: begin watching again only if the user turned history on."""
    if settings.load()["clipboard_history"] and available():
        start()
    return status(items=False)


def copy(identity):
    identity = check(identity)
    if not available():
        raise CommandError("Clipboard history needs cliphist and wl-clipboard")
    decoder = subprocess.Popen(["cliphist", "decode", identity], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        copier = subprocess.run(["wl-copy"], stdin=decoder.stdout, timeout=8, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, check=False)
    except subprocess.TimeoutExpired as error:
        decoder.kill()
        raise CommandError("Copying took too long") from error
    finally:
        decoder.stdout.close()
        decoder.wait()
    if decoder.returncode or copier.returncode:
        raise CommandError("That entry could not be copied")
    return {"ok": True, "id": identity}


def delete(identity):
    identity = check(identity)
    line = next((raw for raw in run(["cliphist", "list"], timeout=6).splitlines() if raw.partition("\t")[0] == identity), None)
    if line is None:
        raise ValueError("That entry is already gone")
    subprocess.run(["cliphist", "delete"], input=line.encode(), timeout=6, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return status()


def clear():
    if shutil.which("cliphist"):
        run(["cliphist", "wipe"], timeout=6)
    return status()
