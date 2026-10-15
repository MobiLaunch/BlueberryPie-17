"""Wi-Fi hotspot through NetworkManager's shared mode.

The profile is named "PrismOS Hotspot" and marked so NetworkManager does not keep its
password (`psk-flags 2`). PrismOS keeps the network name and password in a private file in the
user's data directory and hands the password to nmcli through a private password file when the
hotspot is turned on, so it never appears in a command line. The password is only returned
when the user opens the hotspot details."""
import json
import os
import pwd
import re
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

from .system import CommandError, run

NAME = "PrismOS Hotspot"
IFACE = re.compile(r"[A-Za-z0-9_.-]{1,15}")
ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # no look-alike characters
PASSWORD_LENGTH = 12


def config_path():
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "prismos" / "hotspot.json"


def clean_ssid(value):
    if not isinstance(value, str):
        raise ValueError("The network name must be text")
    value = value.strip()
    if not value or len(value.encode("utf-8")) > 32 or re.search(r"[\x00-\x1f\x7f]", value):
        raise ValueError("Use a network name of 1 to 32 characters")
    return value


def clean_password(value):
    if not isinstance(value, str) or not 8 <= len(value) <= 63 or not all(32 <= ord(c) <= 126 for c in value):
        raise ValueError("Use a password of 8 to 63 letters, digits or symbols")
    return value


def default_ssid():
    host = re.sub(r"[^A-Za-z0-9-]", "", os.uname().nodename)[:20] or "PC"
    return f"PrismOS-{host}"


def make_password():
    return "".join(secrets.choice(ALPHABET) for _ in range(PASSWORD_LENGTH))


def load():
    """The saved network name and password. The first use (or a damaged file) creates and saves
    them, so the password shown, copied and used to start the hotspot is always the same one."""
    try:
        data = json.loads(config_path().read_text())
        return {"ssid": clean_ssid(data["ssid"]), "password": clean_password(data["password"])}
    except (OSError, ValueError, KeyError, TypeError):
        config = {"ssid": default_ssid(), "password": make_password()}
        save(config)
        return config


def save(config):
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=".hotspot-")
    try:
        with os.fdopen(handle, "w") as stream:
            json.dump(config, stream)
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def stored():
    return config_path().exists()


def wifi_interface():
    """The first Wi-Fi adapter, if it can host an access point."""
    rows = run(["nmcli", "-t", "--escape", "no", "-f", "DEVICE,TYPE", "device"]).splitlines()
    device = next((row.rsplit(":", 1)[0] for row in rows if row.rsplit(":", 1)[-1] == "wifi"
                   and IFACE.fullmatch(row.rsplit(":", 1)[0])), None)
    if device is None:
        raise CommandError("No Wi-Fi adapter was found")
    if run(["nmcli", "-g", "WIFI-PROPERTIES.AP", "device", "show", device]).strip().lower() != "yes":
        raise CommandError("This Wi-Fi adapter cannot host a hotspot")
    return device


def profile_rows():
    raw = run(["nmcli", "-t", "--escape", "no", "-f", "NAME,TYPE,ACTIVE", "connection", "show"])
    return [row.rsplit(":", 2) for row in raw.splitlines() if row.count(":") >= 2]


def state():
    """(profile exists, hotspot active) from one nmcli call."""
    exists = active = False
    for name, _kind, running in profile_rows():
        if name == NAME:
            exists, active = True, running == "yes"
    return exists, active


def status(rows=None):
    """Cheap status for the Quick Settings tile."""
    try:
        exists, active = state() if rows is None else (
            any(r[0] == NAME for r in rows), any(r[0] == NAME and r[2] == "yes" for r in rows))
    except CommandError as error:
        return {"available": False, "enabled": False, "label": str(error)}
    return {"available": True, "enabled": active, "configured": exists,
            "ssid": load()["ssid"] if stored() else ""}


def info():
    config = load()
    exists, active = state()
    return {"ok": True, "ssid": config["ssid"], "password": config["password"], "enabled": active,
            "configured": exists}


def secret_file(folder, password):
    path = Path(folder) / "psk"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("802-11-wireless-security.psk:" + password + "\n")
    return str(path)


def enable():
    if not shutil.which("dnsmasq"):
        raise CommandError("The hotspot needs the dnsmasq package")
    interface = wifi_interface()
    config = load()
    exists, active = state()
    if active:
        return {"ok": True, "enabled": True}
    run(["nmcli", "radio", "wifi", "on"])
    if not exists:
        run(["nmcli", "connection", "add", "type", "wifi", "con-name", NAME, "ifname", interface,
             "ssid", config["ssid"], "mode", "ap", "ipv4.method", "shared",
             "802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk-flags", "2",
             "connection.autoconnect", "no", "connection.permissions", "user:" + pwd.getpwuid(os.getuid()).pw_name])
    else:
        run(["nmcli", "connection", "modify", "id", NAME, "802-11-wireless.ssid", config["ssid"],
             "connection.interface-name", interface])
    try:
        with tempfile.TemporaryDirectory(prefix="prism-hotspot-") as folder:
            run(["nmcli", "--wait", "30", "connection", "up", "id", NAME, "ifname", interface,
                 "passwd-file", secret_file(folder, config["password"])], timeout=35)
    except CommandError:
        # nmcli's message can echo settings; give a fixed, useful one instead.
        raise CommandError("The hotspot could not start. Check that Wi-Fi is on and not busy, then try again.") from None
    return {"ok": True, "enabled": True}


def disable():
    exists, active = state()
    if active:
        run(["nmcli", "--wait", "10", "connection", "down", "id", NAME], timeout=15)
    return {"ok": True, "enabled": False}


def toggle():
    return disable() if state()[1] else enable()


def configure(ssid=None, password=None, regenerate=False):
    config = load()
    if ssid is not None:
        config["ssid"] = clean_ssid(ssid)
    if regenerate:
        config["password"] = make_password()
    if password is not None:
        config["password"] = clean_password(password)
    save(config)
    exists, active = state()
    if exists and not active:
        run(["nmcli", "connection", "modify", "id", NAME, "802-11-wireless.ssid", config["ssid"]])
    return {**info(), "restart_needed": active}


def copy_password():
    """Put the password on the clipboard through a pipe, never a command line."""
    if not shutil.which("wl-copy"):
        raise CommandError("wl-copy is not installed")
    try:
        subprocess.run(["wl-copy"], input=load()["password"], text=True, timeout=5, check=True, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        raise CommandError("Could not copy the password") from None
    return {"ok": True}
