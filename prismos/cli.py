import argparse
import json
import sys

from . import apps, favorites, settings, system, theme, wireless


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prismctl", description="PrismOS native system bridge (JSON output)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("apps")
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
