import argparse
import json
import sys

from . import sound as alert_sound
from . import about, alarms, android, apps, audio, clipboard, clockset, notes, thumbnails, worldclock, displays, drives, favorites, fdroid, files, inputs, installer, notifyprefs, screenshot, settings, stats, storage, store, system, theme, tiles, wallpaper, weather, websearch, widgets, windows, wireless


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prismctl", description="PrismOS native system bridge (JSON output)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("apps")
    sub.add_parser("about")
    space = sub.add_parser("storage")
    space.add_argument("operation", choices=("usage", "clear-previews"))
    sub.add_parser("stats")
    web = sub.add_parser("websearch")
    web.add_argument("query")
    setup = sub.add_parser("installer")
    setup.add_argument("operation", choices=("status", "options", "disks", "plan", "install"))
    clock = sub.add_parser("alarms")
    clock.add_argument("operation", choices=("list", "add", "toggle", "remove"))
    clock.add_argument("id", nargs="?")
    clock.add_argument("--time")
    clock.add_argument("--days", default="")
    clock.add_argument("--label", default="")
    jot = sub.add_parser("notes")
    jot.add_argument("operation", choices=("get", "set"))
    thumbs = sub.add_parser("thumbnails")
    thumbs.add_argument("operation", choices=("capture", "list", "clear", "enable"))
    thumbs.add_argument("value", nargs="?")
    when = sub.add_parser("datetime")
    when.add_argument("operation", choices=("get", "timezone", "ntp", "24h"))
    when.add_argument("value", nargs="?")
    world = sub.add_parser("worldclock")
    world.add_argument("operation", choices=("list", "add", "remove"))
    world.add_argument("zone", nargs="?")
    clip = sub.add_parser("clipboard")
    clip.add_argument("operation", choices=("list", "copy", "delete", "clear", "enable", "disable", "resume", "pin", "unpin", "copy-pin"))
    clip.add_argument("id", nargs="?")
    quiet = sub.add_parser("quiet-hours")
    quiet.add_argument("operation", choices=("get", "set"))
    quiet.add_argument("--enabled", choices=("yes", "no"))
    quiet.add_argument("--start")
    quiet.add_argument("--end")
    tone = sub.add_parser("sound")
    tone.add_argument("name", choices=tuple(alert_sound.SOUNDS))
    shot = sub.add_parser("screenshot")
    shot.add_argument("mode", choices=screenshot.MODES)
    tile = sub.add_parser("tiles")
    tile.add_argument("operation", choices=("list", "set", "reset"))
    tile.add_argument("ids", nargs="*")
    alerts = sub.add_parser("notifications")
    alerts.add_argument("operation", choices=("list", "mute", "unmute", "history"))
    alerts.add_argument("app", nargs="?")
    gadget = sub.add_parser("widgets")
    gadget.add_argument("operation", choices=("list", "set", "size"))
    gadget.add_argument("ids", nargs="*")
    forecast = sub.add_parser("weather")
    forecast.add_argument("operation", choices=("get", "search", "set", "disable"))
    forecast.add_argument("--query")
    forecast.add_argument("--lat")
    forecast.add_argument("--lon")
    forecast.add_argument("--label")
    forecast.add_argument("--units", default="metric")
    paper = sub.add_parser("wallpaper")
    paper.add_argument("operation", choices=("list", "set", "clear"))
    paper.add_argument("path", nargs="?")
    win = sub.add_parser("windows")
    win.add_argument("operation", choices=("list",) + windows.OPERATIONS)
    win.add_argument("address", nargs="?")
    inp = sub.add_parser("input")
    inp.add_argument("operation", choices=("list", "set", "apply"))
    inp.add_argument("key", nargs="?")
    inp.add_argument("value", nargs="?")
    volume = sub.add_parser("drives")
    volume.add_argument("operation", choices=("list", "mount", "unmount"))
    volume.add_argument("device", nargs="?")
    disp = sub.add_parser("display")
    disp.add_argument("operation", choices=("list", "preview", "arrange", "confirm", "apply"))
    disp.add_argument("name", nargs="?")
    disp.add_argument("value", nargs="?")
    disp.add_argument("anchor", nargs="?")
    fileargs = sub.add_parser("files")
    fileargs.add_argument("operation", choices=("list", "bookmarks", "open", "mkdir", "rename", "trash", "stage", "paste", "clipboard", "transfer"))
    fileargs.add_argument("path", nargs="?")
    fileargs.add_argument("--name")
    fileargs.add_argument("--action", choices=("copy", "cut"))
    fileargs.add_argument("--dest")
    fileargs.add_argument("--hidden", action="store_true")
    software = sub.add_parser("store")
    software.add_argument("operation", choices=("status", "enable", "search", "install", "remove", "open"))
    software.add_argument("value", nargs="?")
    catalog = sub.add_parser("fdroid")
    catalog.add_argument("operation", choices=("search", "details"))
    catalog.add_argument("value")
    droid = sub.add_parser("android")
    droid.add_argument("operation", choices=("status", "enable", "disable", "resume", "open", "install", "fdroid", "fdroid-open"))
    droid.add_argument("value", nargs="?")
    welcome = sub.add_parser("welcome")
    welcome.add_argument("operation", choices=("status", "finish"))
    welcome.add_argument("--android", choices=("yes", "no"))
    sound = sub.add_parser("audio")
    sound.add_argument("operation", choices=("list", "select", "volume", "mute"))
    sound.add_argument("--kind", choices=("output", "input"))
    sound.add_argument("--serial")
    sound.add_argument("--node-name")
    sound.add_argument("--value")
    wifi = sub.add_parser("wifi")
    wifi.add_argument("operation", choices=("list", "scan", "connect", "disconnect"))
    wifi.add_argument("--bssid")
    wifi.add_argument("--interface")
    wifi.add_argument("--password-stdin", action="store_true")
    bluetooth = sub.add_parser("bluetooth")
    bluetooth.add_argument("operation", choices=("list", "scan", "connect", "disconnect"))
    bluetooth.add_argument("address", nargs="?")
    favorite = sub.add_parser("favorites")
    favorite.add_argument("operation", choices=("list", "pin", "unpin"))
    favorite.add_argument("desktop_id", nargs="?")
    act = sub.add_parser("action")
    act.add_argument("name")
    act.add_argument("value", nargs="?")
    launch = sub.add_parser("launch")
    launch.add_argument("desktop_id")
    color = sub.add_parser("theme")
    color.add_argument("--seed")
    color.add_argument("--wallpaper")
    color.add_argument("--dark", action="store_true", default=None)
    color.add_argument("--scheme", choices=tuple(theme.SCHEMES))
    color.add_argument("--font-scale", type=float)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = system.status()
        elif args.command == "apps":
            result = apps.entries()
        elif args.command == "wallpaper":
            result = (wallpaper.status() if args.operation == "list" else
                      wallpaper.clear() if args.operation == "clear" else wallpaper.choose(args.path))
        elif args.command == "installer":
            if args.operation == "install":
                return installer.install(sys.stdin.read(65536))
            if args.operation == "plan":
                try:
                    result = installer.preview(json.loads(sys.stdin.read(65536)))
                except (TypeError, json.JSONDecodeError):
                    raise ValueError("The installation request is not valid") from None
            else:
                result = {"status": installer.status, "options": installer.options,
                          "disks": installer.disk_listing}[args.operation]()
        elif args.command == "alarms":
            if args.operation == "list":
                result = alarms.status()
            elif args.operation == "add":
                result = alarms.add(args.time, args.days, args.label)
            else:
                if args.id is None or not args.id.isdigit():
                    raise ValueError("An alarm number is required")
                result = alarms.toggle(args.id) if args.operation == "toggle" else alarms.remove(args.id)
        elif args.command == "notes":
            if args.operation == "get":
                result = notes.get()
            else:
                try:
                    result = notes.save(json.loads(sys.stdin.read(32768))["text"])
                except (KeyError, TypeError, json.JSONDecodeError):
                    raise ValueError("The note was not valid") from None
        elif args.command == "thumbnails":
            op = args.operation
            result = (thumbnails.capture() if op == "capture" else thumbnails.status() if op == "list"
                      else thumbnails.clear() if op == "clear" else thumbnails.set_enabled(args.value))
        elif args.command == "datetime":
            op = args.operation
            result = (clockset.status() if op == "get" else clockset.set_timezone(args.value) if op == "timezone"
                      else clockset.set_ntp(args.value) if op == "ntp" else clockset.set_24h(args.value))
        elif args.command == "worldclock":
            result = (worldclock.status() if args.operation == "list"
                      else worldclock.add(args.zone) if args.operation == "add" else worldclock.remove(args.zone))
        elif args.command == "clipboard":
            op = args.operation
            result = (clipboard.status() if op == "list" else clipboard.copy(args.id) if op == "copy"
                      else clipboard.delete(args.id) if op == "delete" else clipboard.clear() if op == "clear"
                      else clipboard.pin(args.id) if op == "pin" else clipboard.unpin(args.id) if op == "unpin"
                      else clipboard.copy_pin(args.id) if op == "copy-pin"
                      else clipboard.resume() if op == "resume" else clipboard.enable(op == "enable"))
        elif args.command == "quiet-hours":
            result = (notifyprefs.schedule_status() if args.operation == "get"
                      else notifyprefs.set_schedule(args.enabled, args.start, args.end))
        elif args.command == "sound":
            result = alert_sound.play(args.name)
        elif args.command == "screenshot":
            result = screenshot.capture(args.mode)
        elif args.command == "tiles":
            result = (tiles.status() if args.operation == "list" else
                      tiles.reset() if args.operation == "reset" else tiles.change(args.ids))
        elif args.command == "notifications":
            result = (notifyprefs.status() if args.operation == "list" else
                      notifyprefs.mute(args.app) if args.operation == "mute" else
                      notifyprefs.set_history(args.app) if args.operation == "history" else notifyprefs.unmute(args.app))
        elif args.command == "websearch":
            result = websearch.search(args.query)
        elif args.command == "stats":
            result = stats.snapshot()
        elif args.command == "widgets":
            if args.operation == "size":
                if len(args.ids) != 2:
                    raise ValueError("Usage: widgets size WIDGET small|medium|large")
                result = widgets.resize(*args.ids)
            else:
                result = widgets.status() if args.operation == "list" else widgets.change(args.ids)
        elif args.command == "weather":
            if args.operation == "search":
                result = weather.search(args.query)
            elif args.operation == "set":
                result = weather.choose(args.lat, args.lon, args.label, args.units)
            elif args.operation == "disable":
                result = weather.disable()
            else:
                result = weather.current()
        elif args.command == "about":
            result = about.info()
        elif args.command == "storage":
            result = storage.usage() if args.operation == "usage" else storage.clear_previews()
        elif args.command == "windows":
            result = (windows.status() if args.operation == "list"
                      else windows.dispatch(args.operation, args.address))
        elif args.command == "input":
            if args.operation == "list":
                result = inputs.list_settings()
            elif args.operation == "set":
                result = inputs.change(args.key, args.value)
            else:
                result = inputs.apply()
        elif args.command == "drives":
            result = (drives.volumes() if args.operation == "list"
                      else drives.change(args.operation, args.device))
        elif args.command == "display":
            if args.operation == "list":
                result = displays.status()
            elif args.operation == "preview":
                return displays.preview(args.name, args.value)
            elif args.operation == "arrange":
                return displays.preview_position(args.name, args.value, args.anchor)
            elif args.operation == "confirm":
                result = displays.confirm(args.name)
            else:
                result = displays.apply_saved()
        elif args.command == "files":
            if args.operation == "list":
                result = files.browse(args.path, args.hidden)
            elif args.operation == "bookmarks":
                result = files.bookmarks()
            elif args.operation == "open":
                result = files.open_item(args.path)
            elif args.operation == "mkdir":
                result = files.create_folder(args.path, args.name)
            elif args.operation == "rename":
                result = files.rename(args.path, args.name)
            elif args.operation == "trash":
                result = files.trash(args.path)
            elif args.operation == "stage":
                result = files.stage(args.path, args.action)
            elif args.operation == "paste":
                result = files.paste(args.path)
            elif args.operation == "transfer":
                result = files.transfer(args.path, args.dest)
            else:
                result = files.clipboard_status()
        elif args.command == "store":
            if args.operation == "status":
                result = store.status()
            elif args.operation == "enable":
                result = store.enable()
            elif args.operation == "search":
                result = store.search(args.value)
            else:
                result = store.change(args.operation, args.value)
        elif args.command == "fdroid":
            result = (fdroid.search(args.value) if args.operation == "search"
                      else fdroid.details(args.value))
        elif args.command == "android":
            if args.operation == "status":
                result = android.status()
            elif args.operation == "enable":
                return android.enable()
            elif args.operation == "disable":
                result = android.disable()
            elif args.operation == "resume":
                result = android.resume()
            elif args.operation == "fdroid":
                return android.install_fdroid()
            elif args.operation == "fdroid-open":
                result = android.open_fdroid()
            elif args.operation == "open":
                result = android.open_android()
            else:
                result = android.install_apk(args.value)
        elif args.command == "welcome":
            if args.operation == "finish":
                result = settings.update(onboarding_complete=True,
                                         android_enabled=(args.android == "yes"))
            else:
                prefs = settings.load()
                result = {"ok": True, "complete": prefs["onboarding_complete"],
                          "android_enabled": prefs["android_enabled"]}
        elif args.command == "audio":
            result = audio.snapshot() if args.operation == "list" else audio.action(args.operation, args.kind, args.serial, args.node_name, args.value)
        elif args.command == "wifi":
            if args.operation in ("list", "scan"):
                result = wireless.wifi_list(args.operation == "scan")
            elif args.operation == "disconnect":
                result = wireless.wifi_disconnect(args.interface)
            else:
                password = ""
                if args.password_stdin:
                    # One bounded JSON line over a private pipe, never an argv secret.
                    try:
                        value = json.loads(sys.stdin.readline(1024))
                        password = value["password"]
                    except (ValueError, KeyError, TypeError):
                        raise ValueError("Invalid password input") from None
                result = wireless.wifi_connect(args.bssid, args.interface, password)
        elif args.command == "bluetooth":
            result = (wireless.bluetooth_list(args.operation == "scan") if args.operation in ("list", "scan")
                      else wireless.bluetooth_action(args.operation, args.address))
        elif args.command == "favorites":
            result = favorites.change(args.operation, args.desktop_id)
        elif args.command == "action":
            result = system.action(args.name, args.value)
        elif args.command == "launch":
            result = apps.launch(args.desktop_id)
        else:
            changes = {}
            seed = theme.wallpaper_seed(args.wallpaper) if args.wallpaper else args.seed
            if seed:
                theme.rgb(seed)
                changes["seed"] = seed
            if args.dark is not None:
                changes["dark"] = args.dark
            if args.scheme:
                changes["scheme"] = args.scheme
            if args.font_scale is not None:
                if args.font_scale not in settings.FONT_SCALES:
                    raise ValueError("Text size must be one of " + ", ".join(str(v) for v in settings.FONT_SCALES))
                changes["font_scale"] = args.font_scale
            prefs = settings.update(**changes) if changes else settings.load()
            result = theme.palette(prefs["seed"], prefs["dark"], prefs["scheme"])
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, system.CommandError, ImportError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
