import os
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from prismos import favorites, settings, system


class FavoriteTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        env=patch.dict(os.environ,{"XDG_CONFIG_HOME":temp.name});env.start();self.addCleanup(env.stop)
        self.installed=[{"id":f"app{i}.desktop","name":f"App {i}"} for i in range(10)]
        source=patch("prismos.favorites.apps.entries",return_value=self.installed);source.start();self.addCleanup(source.stop)

    def test_pin_persists_order_and_no_duplicates(self):
        for entry in ("app2.desktop","app1.desktop","app2.desktop"):favorites.change("pin",entry)
        self.assertEqual(settings.load()["favorites"],["app2.desktop","app1.desktop"])

    def test_empty_dock_is_preserved(self):
        favorites.change("pin","app2.desktop");favorites.change("unpin","app2.desktop")
        self.assertEqual(favorites.change("list")["favorites"],[])

    def test_unknown_app_cannot_be_pinned(self):
        with self.assertRaises(ValueError):favorites.change("pin","untrusted.desktop")
        self.assertIsNone(settings.load()["favorites"])

    def test_capacity_preserves_existing_choices(self):
        for i in range(8):favorites.change("pin",f"app{i}.desktop")
        with self.assertRaises(ValueError):favorites.change("pin","app8.desktop")
        self.assertEqual(len(settings.load()["favorites"]),8)

    def test_concurrent_pins_do_not_lose_changes(self):
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda i:favorites.change("pin",f"app{i}.desktop"),range(4)))
        self.assertEqual(set(settings.load()["favorites"]),{f"app{i}.desktop" for i in range(4)})

    def test_default_categories_handle_namespaced_ids(self):
        installed=[{"id":"org.mozilla.firefox.desktop","name":"Firefox Web Browser"},{"id":"org.xfce.Thunar.desktop","name":"File Manager"},{"id":"foot.desktop","name":"Foot"}]
        self.assertEqual(favorites.defaults(installed),[item["id"] for item in installed])


class PowerTests(unittest.TestCase):
    @patch("prismos.system.power",return_value={"restart":True})
    @patch("prismos.system.run",return_value="")
    def test_restart_maps_only_to_known_command(self, run, power):
        system.action("restart")
        run.assert_called_once_with(["systemctl","--no-block","reboot"])

    @patch("prismos.system.power",return_value={"shutdown":False})
    @patch("prismos.system.run")
    def test_denied_capability_does_not_execute(self, run, power):
        with self.assertRaises(system.CommandError):system.action("shutdown")
        run.assert_not_called()

    @patch.dict(os.environ,{"XDG_SESSION_ID":"self; reboot"})
    @patch("prismos.system.run")
    def test_invalid_session_id_cannot_terminate(self, run):
        with self.assertRaises(system.CommandError):system.action("logout")
        run.assert_not_called()

    @patch.dict(os.environ,{"XDG_SESSION_ID":"c4"})
    @patch("prismos.system.run",return_value="")
    def test_logout_only_uses_current_session(self, run):
        system.action("logout")
        run.assert_called_once_with(["loginctl","terminate-session","c4"])


class LauncherDataTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"XDG_CONFIG_HOME": temp.name + "/config", "XDG_DATA_HOME": temp.name + "/data",
                                      "XDG_DATA_DIRS": temp.name + "/none", "XDG_CURRENT_DESKTOP": "PrismOS:Hyprland"})
        env.start(); self.addCleanup(env.stop)
        apps_dir = Path(temp.name) / "data/applications"; apps_dir.mkdir(parents=True)
        for name, categories, extra in (("web", "Network;WebBrowser;", "Keywords=internet;surf;"), ("tux", "Game;ArcadeGame;", ""),
                                        ("calc", "Utility;Calculator;", ""), ("plain", "", "")):
            (apps_dir / f"{name}.desktop").write_text(
                f"[Desktop Entry]\nType=Application\nName={name.title()}\nExec=true\nCategories={categories}\n{extra}\n")

    def test_entries_have_groups_and_keywords(self):
        from prismos import apps
        by_name = {item["name"]: item for item in apps.entries()}
        self.assertEqual(by_name["Web"]["category"], "Internet")
        self.assertEqual(by_name["Tux"]["category"], "Games")
        self.assertEqual(by_name["Calc"]["category"], "Utilities")
        self.assertEqual(by_name["Plain"]["category"], "Other")
        self.assertEqual(by_name["Web"]["keywords"], "internet surf")

    def test_an_app_without_an_icon_key_has_an_empty_icon_so_the_shell_draws_a_letter_tile(self):
        from prismos import apps
        self.assertEqual({item["icon"] for item in apps.entries()}, {""})

    def test_launch_records_most_recent_first_without_duplicates(self):
        from prismos import apps
        with patch("prismos.apps.run"):
            for name in ("web", "tux", "web"):
                apps.launch(f"{name}.desktop")
        self.assertEqual(settings.load()["recent_apps"], ["web.desktop", "tux.desktop"])

    def test_recents_ignore_hostile_values_and_cap_at_eight(self):
        settings.update(recent_apps=["../etc/passwd", 7, "ok.desktop", "ok.desktop"] + [f"a{i}.desktop" for i in range(12)])
        recents = settings.load()["recent_apps"]
        self.assertEqual(recents[0], "ok.desktop")
        self.assertEqual(len(recents), 8)
        self.assertNotIn("../etc/passwd", recents)


class AboutTests(unittest.TestCase):
    def test_reads_system_files_without_running_commands(self):
        from prismos import about
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "os-release").write_text('NAME="Arch Linux"\nPRETTY_NAME="Arch Linux"\n# comment\nBROKEN\n')
            (root / "cpuinfo").write_text("processor\t: 0\nmodel name\t: Fake   CPU @ 3GHz\n")
            (root / "meminfo").write_text("MemTotal:       16384000 kB\n")
            (root / "uptime").write_text("3600.55 100.0\n")
            with patch("subprocess.run") as run, patch("subprocess.Popen") as popen:
                result = about.info(root / "os-release", root / "cpuinfo", root / "meminfo", root / "uptime")
            run.assert_not_called(); popen.assert_not_called()
        self.assertEqual(result["base"], "Arch Linux")
        self.assertEqual(result["cpu"], "Fake CPU @ 3GHz")
        self.assertEqual(result["memory_gib"], 15.6)
        self.assertEqual(result["uptime_seconds"], 3600)

    def test_missing_files_degrade_to_empty_values(self):
        from prismos import about
        missing = "/nonexistent/prism"
        result = about.info(missing, missing, missing, missing)
        self.assertTrue(result["ok"])
        self.assertEqual(result["cpu"], "")
        self.assertIsNone(result["memory_gib"])
        self.assertIsNone(result["uptime_seconds"])


class HardwareKeyTests(unittest.TestCase):
    @patch("prismos.system.run", return_value="")
    def test_media_key_actions_map_to_fixed_commands(self, run):
        expected = {
            "volume-up": ["wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "5%+"],
            "volume-down": ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"],
            "brightness-up": ["brightnessctl", "-c", "backlight", "set", "5%+"],
            "brightness-down": ["brightnessctl", "-c", "backlight", "--min-value=1", "set", "5%-"],
        }
        for name, command in expected.items():
            with self.subTest(action=name):
                run.reset_mock()
                self.assertEqual(system.action(name), {"ok": True, "action": name})
                run.assert_called_once_with(command)

    @patch("prismos.system.run")
    def test_step_actions_take_no_caller_value(self, run):
        system.action("volume-up", "999; reboot")
        self.assertNotIn("999; reboot", " ".join(run.call_args.args[0]))
