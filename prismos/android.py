"""Optional Waydroid entry points; never silently download Android images."""
from pathlib import Path
import shutil
import subprocess
from .system import CommandError, run


def status():
    if not shutil.which("waydroid"):
        return {"ok": True, "available": False, "error": "Waydroid is not installed"}
    try:
        output = run(["waydroid", "status"], timeout=8)
    except CommandError as error:
        return {"ok": True, "available": True, "ready": False, "status": str(error)}
    return {"ok": True, "available": True,
            "ready": "Session: RUNNING" in output, "status": output}


def open_android():
    if not shutil.which("waydroid"):
        raise CommandError("Waydroid is not installed")
    subprocess.Popen(["waydroid", "show-full-ui"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return {"ok": True, "message": "Requested Waydroid window"}


def install_apk(path):
    apk = Path(path).expanduser().resolve()
    if not apk.is_file() or apk.suffix.lower() != ".apk":
        raise ValueError("Select an existing .apk file")
    run(["waydroid", "app", "install", str(apk)], timeout=180)
    return {"ok": True, "file": apk.name}
