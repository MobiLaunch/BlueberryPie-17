import argparse
import json
import sys

from . import apps, settings, system, theme


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prismctl", description="PrismOS native system bridge (JSON output)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("apps")
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
