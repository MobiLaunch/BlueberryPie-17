import os
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
