"""VPN connections kept in NetworkManager (OpenVPN, WireGuard, and other `vpn` profiles).

Only profiles that already exist are used: PrismOS does not create VPNs or handle their
credentials. A profile that needs a password or token is connected once in Network settings;
after that the Quick Settings tile can switch it on and off."""
import re

from . import settings
from .system import CommandError, run

UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
KINDS = ("vpn", "wireguard")
LIMIT = 32


def rows_from(raw):
    """Profiles from `nmcli -t --escape no -f NAME,UUID,TYPE,ACTIVE connection show`."""
    result = []
    for line in raw.splitlines():
        parts = line.rsplit(":", 3)
        if len(parts) != 4:
            continue
        name, identifier, kind, active = parts
        # NAME may itself contain colons, so the three trailing fields are split from the right.
        if identifier and UUID.fullmatch(identifier) and kind in KINDS:
            result.append({"name": re.sub(r"[\x00-\x1f\x7f]", "", name)[:64], "uuid": identifier.lower(),
                           "type": kind, "active": active == "yes"})
    return result[:LIMIT]


def profiles():
    return rows_from(run(["nmcli", "-t", "--escape", "no", "-f", "NAME,UUID,TYPE,ACTIVE", "connection", "show"]))


def preferred(found):
    wanted = settings.load()["vpn_profile"]
    return next((p for p in found if p["uuid"] == wanted), found[0] if found else None)


def status(found=None):
    try:
        found = profiles() if found is None else found
    except CommandError as error:
        return {"available": False, "enabled": False, "label": str(error), "count": 0}
    active = [p for p in found if p["active"]]
    choice = preferred(found)
    return {"available": bool(found), "enabled": bool(active), "count": len(found),
            "label": active[0]["name"] if active else (choice["name"] if choice else "No VPN set up")}


def listing():
    found = profiles()
    choice = preferred(found)
    return {"ok": True, "profiles": found, "preferred": choice["uuid"] if choice else ""}


def find(identifier):
    if not isinstance(identifier, str) or not UUID.fullmatch(identifier):
        raise ValueError("Choose a VPN")
    found = next((p for p in profiles() if p["uuid"] == identifier.lower()), None)
    if found is None:
        raise ValueError("That VPN is no longer available")
    return found


def connect(identifier):
    profile = find(identifier)
    if profile["active"]:
        return {"ok": True}
    try:
        run(["nmcli", "--wait", "30", "connection", "up", "uuid", profile["uuid"]], timeout=35)
    except CommandError as error:
        if "secret" in str(error).lower() or "password" in str(error).lower():
            raise CommandError("This VPN needs a password or token. Connect it once in Network settings first.") from None
        raise CommandError("The VPN could not connect. Check it in Network settings.") from None
    settings.update(vpn_profile=profile["uuid"])
    return {"ok": True}


def disconnect(identifier):
    profile = find(identifier)
    if profile["active"]:
        run(["nmcli", "--wait", "10", "connection", "down", "uuid", profile["uuid"]], timeout=15)
    return {"ok": True}


def choose(identifier):
    settings.update(vpn_profile=find(identifier)["uuid"])
    return listing()


def toggle():
    found = profiles()
    active = [p for p in found if p["active"]]
    if active:
        for profile in active:
            run(["nmcli", "--wait", "10", "connection", "down", "uuid", profile["uuid"]], timeout=15)
        return {"ok": True}
    choice = preferred(found)
    if choice is None:
        raise CommandError("No VPN is set up. Add one in Network settings.")
    return connect(choice["uuid"])
