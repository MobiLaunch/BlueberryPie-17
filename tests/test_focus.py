import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, notifyprefs, settings, system, tiles


class FocusModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())

    def test_off_with_no_apps_by_default_and_toggles_through_the_bridge(self):
        self.assertEqual((settings.load()["focus"], settings.load()["focus_apps"]), (False, []))
        system.action("focus")
        self.assertTrue(settings.load()["focus"])
        self.assertTrue(system.status()["settings"]["focus"])
        system.action("focus")
        self.assertFalse(settings.load()["focus"])

    def test_apps_are_added_and_removed_without_touching_the_muted_list(self):
        code, result = self.run_cli(["notifications", "focus-app", "Chat", "yes"])
        self.assertEqual((code, result["focus_apps"], result["muted"]), (0, ["Chat"], []))
        self.run_cli(["notifications", "focus-app", "Mail", "yes"])
        self.run_cli(["notifications", "focus-app", "Chat", "yes"])  # no duplicates
        self.assertEqual(settings.load()["focus_apps"], ["Chat", "Mail"])
        self.run_cli(["notifications", "mute", "Games"])
        _, result = self.run_cli(["notifications", "focus-app", "Chat", "no"])
        self.assertEqual((result["focus_apps"], result["muted"]), (["Mail"], ["Games"]))

    def test_bad_names_flags_and_overflow_are_refused(self):
        for argv in (["notifications", "focus-app", "", "yes"], ["notifications", "focus-app", "x\ny", "yes"],
                     ["notifications", "focus-app", "A" * 65, "yes"], ["notifications", "focus-app", "Chat", "maybe"],
                     ["notifications", "focus-app", "Chat"]):
            with self.subTest(argv=argv):
                code, result = self.run_cli(argv)
                self.assertEqual((code, result["ok"]), (1, False))
        for index in range(notifyprefs.LIMIT):
            notifyprefs.focus_app(f"App {index}", "yes")
        with self.assertRaises(ValueError):
            notifyprefs.focus_app("One too many", "yes")
        notifyprefs.focus_app("App 0", "yes")  # an app already in the list is fine
        self.assertEqual(settings.load()["focus_apps"][0], "App 0")

    def test_saved_settings_are_validated_on_load(self):
        settings.directory().mkdir(parents=True)
        (settings.directory() / "settings.json").write_text(json.dumps(
            {"focus": "yes", "focus_apps": ["Good", 7, "bad\u0000name", "Good", "x" * 80]}))
        loaded = settings.load()
        self.assertEqual((loaded["focus"], loaded["focus_apps"]), (False, ["Good"]))

    def test_the_tile_is_in_the_catalog_and_can_be_chosen(self):
        self.assertIn("focus", tiles.IDS)
        self.assertEqual(self.run_cli(["tiles", "set", "focus", "dnd"])[1]["enabled"], ["focus", "dnd"])


if __name__ == "__main__":
    unittest.main()
