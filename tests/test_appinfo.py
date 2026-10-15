import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import appinfo, cli
from prismos.system import CommandError

DESKTOP = "[Desktop Entry]\nType=Application\nName={name}\nExec=true\nIcon=x\nStartupWMClass={wm}\n"


class AppInfoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.pacman_desktop = root / "applications" / "foot.desktop"
        self.flatpak_desktop = root / "flatpak" / "app" / "org.gnome.Calculator" / "export" / "org.gnome.Calculator.desktop"
        for path, name, wm in ((self.pacman_desktop, "Foot", "foot"),
                               (self.flatpak_desktop, "Calculator", "")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(DESKTOP.format(name=name, wm=wm))
        self.entries = [
            {"id": "foot.desktop", "name": "Foot", "icon": "foot", "startupClass": "foot", "description": "Terminal",
             "path": str(self.pacman_desktop), "category": "System", "keywords": ""},
            {"id": "org.gnome.Calculator.desktop", "name": "Calculator", "icon": "calc", "startupClass": "",
             "description": "", "path": str(self.flatpak_desktop), "category": "Utilities", "keywords": ""},
        ]
        self.clients = []
        self.scopes = {"user"}
        self.commands = []
        for target, value in (("prismos.appinfo.apps.entries", lambda: self.entries),
                              ("prismos.appinfo.windows.clients", lambda: self.clients),
                              ("prismos.appinfo.run", self.fake_run)):
            patcher = patch(target, side_effect=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_run(self, args, timeout=4):
        self.commands.append(args)
        if args[:3] == ["pacman", "-Qo", "-q"]:
            return "foot" if args[3] == str(self.pacman_desktop) else self.fail_with("error: no package owns")
        if args[:2] == ["pacman", "-Qi"]:
            return "Name : foot\nVersion         : 1.20.0-1\nDescription     : Fast terminal\nURL             : https://x\nInstalled Size  : 1.2 MiB"
        if args[:2] == ["flatpak", "info"]:
            scope = args[2].lstrip("-")
            if scope not in self.scopes:
                self.fail_with("not installed")
            return "Version: 8.0\nOrigin: flathub\nInstalled: 4.0 MB"
        if args[:2] == ["flatpak", "uninstall"]:
            return ""
        raise AssertionError(args)

    @staticmethod
    def fail_with(message):
        raise CommandError(message)

    @staticmethod
    def reap(*processes):
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait()
            if process.stdout:
                process.stdout.close()

    def window(self, wm_class, pid):
        return {"address": "0x1", "class": wm_class, "pid": pid}

    def test_pacman_app_shows_package_details_and_a_copyable_command_but_is_not_removable(self):
        result = appinfo.info("foot.desktop")
        self.assertEqual((result["source"], result["package"], result["version"]), ("pacman", "foot", "1.20.0-1"))
        self.assertEqual(result["remove_command"], "sudo pacman -Rns foot")
        self.assertFalse(result["removable"])
        with self.assertRaises(CommandError):
            appinfo.uninstall("foot.desktop")
        self.assertFalse(any(cmd[:2] == ["flatpak", "uninstall"] for cmd in self.commands))

    def test_user_flatpak_is_removable_and_system_flatpak_only_shows_a_command(self):
        result = appinfo.info("org.gnome.Calculator.desktop")
        self.assertEqual((result["source"], result["package"], result["removable"]), ("flatpak", "org.gnome.Calculator", True))
        self.scopes = {"system"}
        result = appinfo.info("org.gnome.Calculator.desktop")
        self.assertFalse(result["removable"])
        self.assertEqual(result["remove_command"], "flatpak uninstall org.gnome.Calculator")
        with self.assertRaises(CommandError):
            appinfo.uninstall("org.gnome.Calculator.desktop")

    def test_uninstall_uses_a_fixed_user_only_command(self):
        appinfo.uninstall("org.gnome.Calculator.desktop")
        self.assertIn(["flatpak", "uninstall", "--user", "-y", "--noninteractive", "org.gnome.Calculator"], self.commands)

    def test_unknown_apps_are_rejected_before_any_command_runs(self):
        for bad in ("nope.desktop", "../../etc/passwd", "foot.desktop; rm -rf /"):
            with self.assertRaises(ValueError):
                appinfo.info(bad)
            with self.assertRaises(ValueError):
                appinfo.force_stop(bad)
            with self.assertRaises(ValueError):
                appinfo.uninstall(bad)
        self.assertEqual(self.commands, [])

    def test_running_state_matches_windows_by_class(self):
        self.clients = [self.window("Foot", 4242), self.window("foot", 4242), self.window("other", 1)]
        result = appinfo.info("foot.desktop")
        self.assertEqual((result["running"], result["windows"], result["processes"]), (True, 2, 1))
        self.clients = []
        self.assertFalse(appinfo.info("foot.desktop")["running"])

    def test_force_stop_terminates_a_real_process_then_kills_a_stubborn_one(self):
        polite = subprocess.Popen(["sleep", "60"])
        stubborn = subprocess.Popen([sys.executable, "-c",
            "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); print('ready', flush=True); time.sleep(60)"],
            stdout=subprocess.PIPE, text=True)
        stubborn.stdout.readline()
        self.addCleanup(self.reap, polite, stubborn)
        self.clients = [self.window("foot", polite.pid), self.window("foot", stubborn.pid)]
        result = appinfo.force_stop("foot.desktop", grace=0.5)
        self.assertEqual((result["stopped"], result["forced"]), (2, 1))
        self.assertEqual(polite.wait(timeout=5), -signal.SIGTERM)
        self.assertEqual(stubborn.wait(timeout=5), -signal.SIGKILL)

    def test_force_stop_refuses_protected_foreign_and_own_processes(self):
        self.assertFalse(appinfo.stoppable(os.getpid()))
        self.assertFalse(appinfo.stoppable(1))
        self.assertFalse(appinfo.stoppable(2 ** 22 + 12345))
        with patch("prismos.appinfo._comm", return_value="hyprland"):
            sleeper = subprocess.Popen(["sleep", "30"])
            self.addCleanup(self.reap, sleeper)
            self.assertFalse(appinfo.stoppable(sleeper.pid))
            self.clients = [self.window("foot", sleeper.pid)]
            with self.assertRaises(CommandError):
                appinfo.force_stop("foot.desktop")
        self.assertIsNone(sleeper.poll())

    def test_force_stop_of_an_app_that_is_not_running_is_an_error(self):
        with self.assertRaises(ValueError):
            appinfo.force_stop("foot.desktop")

    def test_copy_command_sends_only_the_generated_command_to_wl_copy(self):
        with patch("prismos.appinfo.shutil.which", return_value="/usr/bin/wl-copy"), \
                patch("prismos.appinfo.subprocess.run") as run:
            run.return_value.returncode = 0
            result = appinfo.copy_command("foot.desktop")
        self.assertEqual(result["copied"], "sudo pacman -Rns foot")
        self.assertEqual(run.call_args.args[0], ["wl-copy"])
        self.assertEqual(run.call_args.kwargs["input"], b"sudo pacman -Rns foot")
        with self.assertRaises(CommandError):  # user Flatpaks are removed in the UI, nothing to copy
            appinfo.copy_command("org.gnome.Calculator.desktop")

    def test_cli_reports_errors_as_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["appinfo", "info", "nope.desktop"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["appinfo", "info", "foot.desktop"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["name"], "Foot")


if __name__ == "__main__":
    unittest.main()
