"""Unprivileged Flatpak/Flathub software catalog for Prism Store."""
import re
import shutil
import subprocess
from .system import CommandError, run

REMOTE = "flathub"
REMOTE_URL = "https://flathub.org/repo/flathub.flatpakrepo"
APP_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+){2,}\Z")


def app_id(value):
    if not isinstance(value, str) or not APP_ID.fullmatch(value) or len(value) > 200:
        raise ValueError("Invalid Flatpak application ID")
    return value


def status():
    if not shutil.which("flatpak"):
        return {"ok": True, "available": False, "configured": False,
                "error": "Flatpak is missing. Install it with: sudo pacman -S flatpak"}
    remotes = run(["flatpak", "remotes", "--user", "--columns=name"], timeout=8)
    return {"ok": True, "available": True, "configured":
            REMOTE in {line.strip() for line in remotes.splitlines()}}


def enable():
    if not shutil.which("flatpak"):
        raise CommandError("Install Flatpak first")
    run(["flatpak", "remote-add", "--user", "--if-not-exists",
         REMOTE, REMOTE_URL], timeout=90)
    return status()


def installed_ids():
    output = run(["flatpak", "list", "--user", "--app", "--columns=application"], timeout=20)
    return {line.strip() for line in output.splitlines() if APP_ID.fullmatch(line.strip())}


def search(term):
    if not isinstance(term, str) or not 1 <= len(term.strip()) <= 80 or "\n" in term or "\r" in term:
        raise ValueError("Search must contain 1 to 80 characters")
    state = status()
    if not state["available"] or not state["configured"]:
        return {**state, "items": []}
    try:
        output = run(["flatpak", "search", "--user",
                      "--columns=application,name,description,remotes", term.strip()], timeout=35)
    except CommandError as error:
        if "No matches" in str(error) or "No results" in str(error):
            output = ""
        else:
            raise
    installed = installed_ids()
    items, seen = [], set()
    for line in output.splitlines():
        columns = line.split("\t", 3)
        if len(columns) != 4:
            continue
        identifier, name, description, remotes = columns
        if identifier in seen or not APP_ID.fullmatch(identifier):
            continue
        if REMOTE not in {value.strip() for value in remotes.split(",")}:
            continue
        seen.add(identifier)
        items.append({"id": identifier, "name": name or identifier,
                      "description": description, "installed": identifier in installed})
        if len(items) == 48:
            break
    return {**state, "items": items}


def change(operation, identifier):
    app_id(identifier)
    state = status()
    if not state["available"] or not state["configured"]:
        raise ValueError("Enable Flathub in Prism Store first")
    if operation == "install":
        if identifier not in installed_ids():
            run(["flatpak", "install", "--user", "--noninteractive", "--assumeyes",
                 REMOTE, identifier], timeout=900)
    elif operation == "remove":
        if identifier in installed_ids():
            run(["flatpak", "uninstall", "--user", "--noninteractive", "--assumeyes",
                 identifier], timeout=900)
    elif operation == "open":
        if identifier not in installed_ids():
            raise ValueError("Install the application before opening it")
        subprocess.Popen(["flatpak", "run", "--user", identifier],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    else:
        raise ValueError("Unknown store operation")
    return {"ok": True, "operation": operation, "id": identifier}
