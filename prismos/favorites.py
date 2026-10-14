from . import apps, settings


def defaults(installed):
    selected = []
    for names in (("firefox", "chromium"), ("thunar", "files", "dolphin"), ("foot", "terminal", "konsole")):
        match = next((entry for name in names for entry in installed
                      if entry["name"].casefold() == name or entry["name"].casefold().startswith(name+" ")
                      or entry["id"].casefold() == name+".desktop" or entry["id"].casefold().endswith("."+name+".desktop")), None)
        if match and match["id"] not in selected:
            selected.append(match["id"])
    return selected


def change(operation, desktop_id=None):
    installed = apps.entries()
    if operation == "list":
        current = settings.load()["favorites"]
        return {"favorites": defaults(installed) if current is None else current}
    if operation not in ("pin", "unpin") or not desktop_id:
        raise ValueError("Choose pin or unpin and an application ID")
    if operation == "pin" and not any(entry["id"] == desktop_id for entry in installed):
        raise ValueError("Application is no longer installed")

    def update(data):
        current = data["favorites"]
        items = list(defaults(installed) if current is None else current)
        if operation == "pin" and desktop_id not in items:
            if len(items) >= 8:
                raise ValueError("The dock supports eight favorites; unpin one first")
            items.append(desktop_id)
        elif operation == "unpin":
            items = [item for item in items if item != desktop_id]
        return {**data, "favorites": items}

    result = settings.modify(update)
    return {"ok": True, "favorites": result["favorites"]}
