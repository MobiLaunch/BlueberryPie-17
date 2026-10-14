"""F-Droid catalog discovery for Prism Store.

F-Droid's public search API is *display metadata only*. The actual install
approval, signature checking, downloads and updates remain in the F-Droid Android
client; PrismOS never installs unverified APKs from search API results.
"""
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

from . import android
from .system import CommandError, run

SEARCH_URL = "https://search.f-droid.org/api/search_apps"
ID = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,}\Z")
MAX_RESPONSE = 2 * 1024 * 1024


def package_id(value):
    if not isinstance(value, str) or len(value) > 220 or not ID.fullmatch(value):
        raise ValueError("Invalid Android application identifier")
    return value


def normalized_results(payload):
    """The search endpoint has changed its envelope over time; keep it strict."""
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = next((payload[key] for key in ("apps", "results", "packages")
                        if isinstance(payload.get(key), list)), [])
    else:
        raise ValueError("F-Droid returned an invalid catalog")
    items, seen = [], set()
    for item in records[:120]:
        if not isinstance(item, dict):
            continue
        identifier = next((item[k] for k in ("packageName", "package_name", "package", "id")
                           if isinstance(item.get(k), str)), None)
        try:
            package_id(identifier)
        except ValueError:
            continue
        if identifier in seen:
            continue
        seen.add(identifier)
        name = item.get("name") or item.get("title") or identifier
        summary = item.get("summary") or item.get("description") or ""
        categories = item.get("categories") or []
        if isinstance(name, dict):
            name = name.get("en-US") or next(iter(name.values()), identifier)
        if isinstance(summary, dict):
            summary = summary.get("en-US") or next(iter(summary.values()), "")
        if not isinstance(categories, list):
            categories = []
        items.append({"id": identifier, "name": str(name)[:100],
                      "description": str(summary)[:320],
                      "categories": [str(x)[:40] for x in categories[:8]],
                      "source": "F-Droid", "kind": "android",
                      "installed": False})
        if len(items) >= 40:
            break
    return items


def search(term):
    if not isinstance(term, str) or not 1 <= len(term.strip()) <= 80 or "\r" in term or "\n" in term:
        raise ValueError("Enter 1–80 characters to search F-Droid")
    if not android.status()["enabled"]:
        return {"ok": True, "enabled": False, "items": [],
                "message": "Enable Android apps in Settings to explore F-Droid"}
    query = urlencode({"q": term.strip()})
    request = Request(SEARCH_URL + "?" + query, headers={"Accept": "application/json",
                                                       "User-Agent": "PrismOS/0.6"})
    try:
        with urlopen(request, timeout=15) as response:
            if response.geturl().split("?")[0] != SEARCH_URL:
                raise CommandError("F-Droid search redirected to an unexpected source")
            data = response.read(MAX_RESPONSE + 1)
            if len(data) > MAX_RESPONSE:
                raise CommandError("F-Droid catalog response is too large")
    except (OSError, URLError, TimeoutError) as error:
        raise CommandError("F-Droid search is unavailable: " + str(error)) from error
    try:
        items = normalized_results(json.loads(data))
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise CommandError("Could not decode F-Droid search results") from error
    return {"ok": True, "enabled": True, "items": items,
            "message": "Installations are confirmed inside F-Droid"}


def details(identifier):
    """Open the official listing in Android; F-Droid handles installation."""
    package_id(identifier)
    state = android.status()
    if not state["enabled"] or not state["ready"]:
        raise ValueError("Finish enabling Android in Settings to install this application")
    if not state.get("fdroid_installed"):
        raise ValueError("Install F-Droid from Settings before opening Android listings")
    uri = "https://f-droid.org/packages/" + identifier + "/"
    # Waydroid forwards ACTION_VIEW intents to Android, including F-Droid's
    # registered official package URL handler. Never run a shell.
    run(["waydroid", "app", "intent", "android.intent.action.VIEW", uri], timeout=18)
    return {"ok": True, "id": identifier, "handoff": "fdroid",
            "message": "Choose Install in F-Droid to verify and install"}
