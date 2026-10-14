"""NetworkManager/BlueZ device operations. All inputs are revalidated at use."""
import os
import pwd
import re
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import system
from .system import CommandError, run

MAC = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")
IFACE = re.compile(r"[A-Za-z0-9_.-]{1,15}")
UUID = re.compile(r"[0-9a-fA-F-]{36}")


def fields(line):
    """Decode nmcli terse fields, including escaped colons and backslashes."""
    result, word, escaped = [], "", False
    for char in line:
        if escaped:
            word += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            result.append(word)
            word = ""
        else:
            word += char
    if escaped:
        word += "\\"
    return result + [word]


def profiles():
    raw = run(["nmcli", "-t", "-f", "UUID,TYPE", "connection", "show"])
    ids = [row[0] for row in map(fields, raw.splitlines())
           if len(row) == 2 and UUID.fullmatch(row[0]) and row[1] in ("wifi", "802-11-wireless")][:64]

    def read(identifier):
        raw = run(["nmcli", "--escape", "no", "-g", "802-11-wireless.ssid,802-11-wireless-security.key-mgmt",
                   "connection", "show", "uuid", identifier])
        parts = raw.splitlines()
        return {"uuid": identifier, "ssid": parts[0] if parts else "",
                "key": parts[1] if len(parts) > 1 else ""}

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(read, ids))


def security_key(security):
    words = set(security.split())
    if not words or words == {"--"}:
        return ""
    if words.intersection({"802.1X", "WEP", "OWE", "EAP"}):
        return None
    if words <= {"WPA1", "WPA2", "WPA3"}:
        return "sae" if words == {"WPA3"} else "wpa-psk"
    return None


def wifi_list(rescan=False):
    state = system.wifi()
    result = {**state, "networks": []}
    if not state["available"] or not state["enabled"]:
        return result
    raw = run(["nmcli", "-t", "--escape", "yes", "-f", "BSSID,SSID,SIGNAL,SECURITY,IN-USE,DEVICE",
               "device", "wifi", "list", "--rescan", "yes" if rescan else "no"], timeout=15)
    saved = profiles()
    networks = []
    for row in map(fields, raw.splitlines()):
        if len(row) != 6:
            continue
        bssid, ssid, signal, security, active, interface = row
        if not MAC.fullmatch(bssid) or not IFACE.fullmatch(interface) or not ssid or any(c in ssid for c in "\r\n\x00"):
            continue
        key = security_key(security)
        profile = next((p for p in saved if p["ssid"] == ssid and
                        (p["key"] == key or (key is None and p["key"] == "wpa-eap"))), None)
        try:
            strength = max(0, min(100, int(signal)))
        except ValueError:
            continue
        networks.append({"bssid": bssid.upper(), "ssid": ssid, "signal": strength,
                         "security": security, "interface": interface, "connected": active == "*",
                         "profile": profile["uuid"] if profile else None,
                         "supported": key is not None or profile is not None,
                         "secured": bool(security and security != "--"), "key": key})
    # Keep the strongest AP per SSID/security/radio, preferring the active AP.
    for network in sorted(networks, key=lambda n: (not n["connected"], -n["signal"])):
        if not any((n["ssid"], n["security"], n["interface"]) ==
                   (network["ssid"], network["security"], network["interface"]) for n in result["networks"]):
            result["networks"].append(network)
    return result


def wifi_connect(bssid, interface, password=""):
    if not isinstance(bssid, str) or not MAC.fullmatch(bssid) or not isinstance(interface, str) or not IFACE.fullmatch(interface):
        raise ValueError("Choose an available Wi-Fi network")
    if not isinstance(password, str) or any(c in password for c in "\r\n\x00") or len(password) > 64:
        raise ValueError("Invalid Wi-Fi password")
    network = next((n for n in wifi_list()["networks"]
                    if n["bssid"] == bssid.upper() and n["interface"] == interface), None)
    if not network:
        raise CommandError("That network is no longer available. Refresh and try again.")
    if network["connected"]:
        return {"ok": True}
    if not network["supported"]:
        raise CommandError("Use advanced network settings for this security type")
    if password and not network["key"]:
        raise ValueError("Use advanced settings to change this network's credentials")
    if network["key"] == "wpa-psk" and password and not (8 <= len(password) <= 63 or re.fullmatch(r"[0-9a-fA-F]{64}", password)):
        raise ValueError("Use 8–63 characters or a 64-digit hexadecimal key")
    if network["key"] == "sae" and password and len(password) > 63:
        raise ValueError("Use a password of at most 63 characters")
    if network["secured"] and not network["profile"] and not password:
        raise ValueError("Enter the network password")
    identifier = network["profile"] or str(uuid.uuid4())
    created = not network["profile"]
    try:
        if created:
            args = ["nmcli", "connection", "add", "type", "wifi", "con-name", network["ssid"],
                    "connection.uuid", identifier, "ssid", network["ssid"], "ifname", interface,
                    "connection.permissions", "user:" + pwd.getpwuid(os.getuid()).pw_name,
                    "connection.autoconnect", "no"]
            if network["key"]:
                args += ["802-11-wireless-security.key-mgmt", network["key"]]
            run(args)
        # The password never appears in argv, settings.json, stdout, or logs.
        with tempfile.TemporaryDirectory(prefix="prism-wifi-") as folder:
            args = ["nmcli", "--wait", "30", "connection", "up", "uuid", identifier,
                    "ifname", interface, "ap", network["bssid"]]
            if password:
                secret = Path(folder)/"password"
                descriptor = os.open(secret, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w") as stream:
                    stream.write("802-11-wireless-security.psk:" + password + "\n")
                args += ["passwd-file", str(secret)]
            run(args, timeout=35)
    except CommandError:
        if created:
            try:
                run(["nmcli", "connection", "delete", "uuid", identifier])
            except CommandError:
                pass
        # nmcli diagnostics can contain user-supplied data; do not echo secrets.
        raise CommandError("Could not connect. Check the password, signal and network permissions, then try again.") from None
    if created:
        try:
            run(["nmcli", "connection", "modify", "uuid", identifier, "connection.autoconnect", "yes"])
        except CommandError:
            # Activation succeeded; never tear down that connection because a
            # later preference update was denied by policy.
            return {"ok": True, "warning": "Connected. Automatic reconnect could not be enabled."}
    return {"ok": True}


def wifi_disconnect(interface):
    if not isinstance(interface, str) or not IFACE.fullmatch(interface):
        raise ValueError("Invalid Wi-Fi interface")
    if not any(n["interface"] == interface and n["connected"] for n in wifi_list()["networks"]):
        raise CommandError("No active Wi-Fi network on that interface")
    run(["nmcli", "--wait", "10", "device", "disconnect", interface], timeout=15)
    return {"ok": True}


def bluetooth_list(scan=False):
    state = system.bluetooth()
    result = {**state, "devices": []}
    if not state["available"] or not state["enabled"]:
        return result
    if scan:
        run(["bluetoothctl", "--timeout", "6", "scan", "on"], timeout=10)
    raw = run(["bluetoothctl", "devices"])
    known = [(match[1], match[2]) for line in raw.splitlines()
             if (match := re.fullmatch(r"Device ((?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}) (.+)", line))][:64]

    def read(item):
        address, name = item
        try:
            info = run(["bluetoothctl", "info", address])
        except CommandError:
            return None  # A discovered device can disappear during the scan.
        return {"address": address.upper(), "name": name,
                "paired": bool(re.search(r"(?:Paired|Bonded):\s+yes", info)),
                "connected": bool(re.search(r"Connected:\s+yes", info))}

    with ThreadPoolExecutor(max_workers=6) as pool:
        result["devices"] = sorted(filter(None, pool.map(read, known)),
                                   key=lambda d: (not d["connected"], not d["paired"], d["name"].casefold()))
    return result


def bluetooth_action(operation, address):
    if operation not in ("connect", "disconnect") or not isinstance(address, str) or not MAC.fullmatch(address):
        raise ValueError("Choose a known Bluetooth device and action")
    device = next((d for d in bluetooth_list()["devices"] if d["address"] == address.upper()), None)
    if not device or not device["paired"]:
        raise CommandError("Pair this device in Bluetooth settings first")
    output = run(["bluetoothctl", "--timeout", "15", operation, device["address"]], timeout=20)
    # bluetoothctl may report a D-Bus error while returning zero.
    if re.search(r"Failed|org\.bluez\.Error|not available", output, re.I):
        raise CommandError("The Bluetooth device could not complete that action. Check that it is in range.")
    return {"ok": True}
