import argparse
import json
import sys

from . import about, android, apps, audio, displays, drives, favorites, fdroid, files, inputs, settings, store, system, theme, windows, wireless


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prismctl", description="PrismOS native system bridge (JSON output)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("apps")
    sub.add_parser("about")
    win = sub.add_parser("windows")
    win.add_argument("operation", choices=("list", "focus", "close"))
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
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            result = system.status()
        elif args.command == "apps":
            result = apps.entries()
        elif args.command == "about":
            result = about.info()
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
            prefs = settings.update(**changes) if changes else settings.load()
            result = theme.palette(prefs["seed"], prefs["dark"])
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, system.CommandError, ImportError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
