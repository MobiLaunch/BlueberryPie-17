"""Opt-in Android lifecycle; no automatic image downloads or privileged QML."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import settings
from .system import CommandError, run

HELPER = "/usr/libexec/prism-android-helper"
FDROID_URL = "https://f-droid.org/F-Droid.apk"
MAX_APK = 64 * 1024 * 1024


def emit(phase, label, **details):
    print(json.dumps({"ok": True, "phase": phase, "label": label, **details}), flush=True)


def status():
    enabled = settings.load()["android_enabled"]
    available = bool(shutil.which("waydroid"))
    result = {"ok": True, "enabled": enabled, "available": available,
              "initialized": Path("/var/lib/waydroid/waydroid.cfg").is_file(),
              "ready": False, "phase": "off" if not enabled else "not-ready"}
    if not available:
        result["error"] = "Waydroid is not installed"
        return result
    try:
        output = run(["waydroid", "status"], timeout=8)
        result["status"] = output
        result["ready"] = (enabled and "Session: RUNNING" in output
                           and "Container: RUNNING" in output)
        if result["ready"]:
            result["phase"] = "ready"
    except CommandError as error:
        result["status"] = str(error)
    return result


def privileged_setup():
    if not shutil.which("pkexec"):
        raise CommandError("polkit is not installed")
    if not Path(HELPER).is_file():
        raise CommandError("PrismOS Android helper is missing; reinstall prism-shell")
    process = subprocess.Popen(["pkexec", HELPER, "enable"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, bufsize=1)
    for line in process.stdout:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("phase") and event.get("label"):
            emit(event["phase"], event["label"])
    error = process.stderr.read()[-700:]
    if process.wait() != 0:
        raise CommandError(error.strip() or "Administrator approval was cancelled")


def enable():
    if not shutil.which("waydroid"):
        raise CommandError("Waydroid is missing; install the waydroid package")
    settings.update(android_enabled=True)
    emit("preparing", "Checking your Android environment")
    if not status()["ready"]:
        emit("authorization", "Preparing Android services; administrator approval may be required")
        privileged_setup()
        emit("starting", "Starting the Android user session")
        subprocess.Popen(["waydroid", "session", "start"], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            if status()["ready"]:
                try:
                    run(["waydroid", "app", "list"], timeout=7)
                    break
                except CommandError:
                    pass
            time.sleep(2)
        else:
            raise CommandError("Android did not become ready; check Waydroid logs and kernel binder support")
    emit("ready", "Android is ready to use", ready=True)
    return 0


def disable():
    settings.update(android_enabled=False)
    if shutil.which("waydroid"):
        try:
            run(["waydroid", "session", "stop"], timeout=20)
        except CommandError:
            pass
    return status()


def open_android():
    if not status()["ready"]:
        raise ValueError("Enable Android in Settings first")
    subprocess.Popen(["waydroid", "show-full-ui"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return {"ok": True, "message": "Requested Android window"}


def install_apk(path):
    if not path:
        raise ValueError("An APK filename is required")
    if not status()["ready"]:
        raise ValueError("Android is not ready")
    apk = Path(path).expanduser().resolve()
    if not apk.is_file() or apk.suffix.lower() != ".apk":
        raise ValueError("Select an existing .apk file")
    run(["waydroid", "app", "install", str(apk)], timeout=180)
    return {"ok": True, "file": apk.name}


def download_fdroid(destination):
    """Fetch F-Droid from its fixed official HTTPS host with a strict size cap."""
    with urlopen(Request(FDROID_URL, headers={"User-Agent": "PrismOS/0.5"}),
                 timeout=35) as response:
        url = urlparse(response.geturl())
        hostname = (url.hostname or "").lower()
        if url.scheme != "https" or not (hostname == "f-droid.org" or hostname.endswith(".f-droid.org")):
            raise CommandError("F-Droid redirected outside its official domain")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_APK:
            raise CommandError("F-Droid download was too large")
        size = 0
        with open(destination, "wb") as handle:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_APK:
                    raise CommandError("F-Droid download was too large")
                handle.write(chunk)
    with open(destination, "rb") as check:
        if size < 1024 or check.read(2) != b"PK":
            raise CommandError("The download was not an Android APK")


def install_fdroid():
    if not status()["ready"]:
        raise ValueError("Android setup must finish before installing F-Droid")
    emit("downloading", "Downloading F-Droid from its official website")
    with tempfile.TemporaryDirectory(prefix="prism-fdroid-") as temporary:
        apk = Path(temporary) / "F-Droid.apk"
        download_fdroid(apk)
        emit("installing", "Installing F-Droid inside Android")
        run(["waydroid", "app", "install", str(apk)], timeout=180)
    emit("ready", "F-Droid is installed", ready=True)
    return 0


def resume():
    """Quiet login resume; never triggers downloads or polkit elevation."""
    if not settings.load()["android_enabled"]:
        return {"ok": True, "skipped": True}
    if not shutil.which("waydroid"):
        return {"ok": False, "error": "Waydroid is not installed"}
    if status()["ready"]:
        return {"ok": True, "already_running": True}
    if not Path("/var/lib/waydroid/waydroid.cfg").is_file():
        return {"ok": False, "error": "Android needs one-time setup in Settings"}
    subprocess.Popen(["waydroid", "session", "start"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return {"ok": True, "starting": True}
