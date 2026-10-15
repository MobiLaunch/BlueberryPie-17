import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, notes, settings, system, widgets
from prismos.system import CommandError


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name, "XDG_DATA_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, argv, stdin=""):
        with patch("sys.stdin", io.StringIO(stdin)), contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class NotesTests(Isolated):
    def test_round_trip_is_private_and_atomic(self):
        self.assertEqual(self.call(["notes", "get"])[1]["text"], "")
        code, result = self.call(["notes", "set"], json.dumps({"text": "milk\n\teggs"}))
        self.assertEqual((code, result["length"]), (0, 10))
        self.assertEqual(self.call(["notes", "get"])[1]["text"], "milk\n\teggs")
        self.assertEqual(stat.S_IMODE(notes.path().stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(notes.path().parent.stat().st_mode), 0o700)
        self.assertEqual([p.name for p in notes.path().parent.iterdir()], ["notes.txt"])

    def test_control_characters_are_stripped_and_length_is_bounded(self):
        self.call(["notes", "set"], json.dumps({"text": "a\x00b\x1b[31mc\r\nd"}))
        self.assertEqual(notes.get()["text"], "ab[31mc\nd")
        code, result = self.call(["notes", "set"], json.dumps({"text": "x" * (notes.MAX + 1)}))
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(self.call(["notes", "set"], json.dumps({"text": "x" * notes.MAX}))[0], 0)

    def test_malformed_input_is_a_json_error_and_keeps_the_old_note(self):
        self.call(["notes", "set"], json.dumps({"text": "keep"}))
        for bad in ("not json", json.dumps({"txt": "x"}), json.dumps({"text": 5}), json.dumps([1])):
            self.assertEqual(self.call(["notes", "set"], bad)[0], 1, bad)
        self.assertEqual(notes.get()["text"], "keep")

    def test_notes_is_a_catalog_widget_off_by_default(self):
        item = next(entry for entry in widgets.CATALOG if entry["id"] == "notes")
        self.assertFalse(item["default"])
        self.assertIn("notes", widgets.enabled() + ["notes"])
        self.call(["widgets", "set", "notes", "clock"])
        self.assertEqual(settings.load()["widgets"], ["clock", "notes"])


class PowerAndWarmthTests(Isolated):
    @patch("prismos.system.run")
    @patch("prismos.system.power_profile", return_value={"available": True, "profile": "balanced", "saver": False})
    def test_profiles_map_to_fixed_powerprofilesctl_values(self, profile, run):
        for action, expected in (("power-saver", "power-saver"), ("power-balanced", "balanced"), ("power-performance", "performance")):
            system.action(action)
            run.assert_called_with(["powerprofilesctl", "set", expected])
        profile.return_value = {"available": False, "profile": "", "saver": False}
        with self.assertRaises(CommandError):
            system.action("power-saver")

    @patch("prismos.system.run")
    @patch("prismos.system.shutil.which", return_value="/usr/bin/hyprsunset")
    def test_warmth_applies_live_only_while_night_light_is_on(self, which, run):
        system.action("night-temp", "3200")
        run.assert_not_called()
        self.assertEqual(settings.load()["night_temp"], 3200)
        settings.update(night_light=True)
        system.action("night-temp", "4100")
        run.assert_called_with(["hyprctl", "hyprsunset", "temperature", "4100"], timeout=5)
        system.action("night-light")  # turn off
        system.action("night-light")  # on again uses the saved warmth
        run.assert_called_with(["hyprctl", "hyprsunset", "temperature", "4100"], timeout=5)

    @patch("prismos.system.run")
    def test_warmth_is_bounded_and_numeric(self, run):
        for bad in ("1000", "9000", "warm", None, "3800; x"):
            with self.assertRaises(ValueError):
                system.action("night-temp", bad)
        run.assert_not_called()
        self.assertEqual(settings.load()["night_temp"], 3800)

    def test_corrupt_warmth_falls_back(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text('{"night_temp": "hot"}')
        self.assertEqual(settings.load()["night_temp"], 3800)


if __name__ == "__main__":
    unittest.main()
