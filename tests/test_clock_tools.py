import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import alarms, cli, notifyprefs, settings, sound
from prismos.system import CommandError


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class AlarmTests(Isolated):
    def test_add_toggle_remove_through_the_cli(self):
        code, result = self.call(["alarms", "add", "--time", "07:30", "--days", "4,0,0,2", "--label", " Work "])
        self.assertEqual(code, 0)
        self.assertEqual(result["alarms"], [{"id": 1, "time": "07:30", "days": [0, 2, 4], "label": "Work", "enabled": True}])
        self.assertFalse(self.call(["alarms", "toggle", "1"])[1]["alarms"][0]["enabled"])
        self.assertTrue(self.call(["alarms", "toggle", "1"])[1]["alarms"][0]["enabled"])
        self.assertEqual(self.call(["alarms", "remove", "1"])[1]["alarms"], [])

    def test_ids_are_reused_and_unique(self):
        for hour in ("06:00", "07:00", "08:00"):
            alarms.add(hour)
        alarms.remove(2)
        self.assertEqual([item["id"] for item in alarms.add("09:00")["alarms"]], [1, 3, 2])

    def test_bad_input_is_refused_and_changes_nothing(self):
        bad = [["--time", "7:30"], ["--time", "24:00"], ["--time", "07:60"], ["--time", "07:30", "--days", "7"],
               ["--time", "07:30", "--days", "a"], ["--time", "07:30", "--label", "x" * 41],
               ["--time", "07:30", "--label", "a\nb"], []]
        for extra in bad:
            code, result = self.call(["alarms", "add", *extra])
            self.assertEqual(code, 1, extra)
            self.assertFalse(result["ok"])
        self.assertEqual(settings.load()["alarms"], [])
        self.assertEqual(self.call(["alarms", "toggle", "9"])[0], 1)
        self.assertEqual(self.call(["alarms", "remove", "x"])[0], 1)

    def test_limit(self):
        for index in range(settings.MAX_ALARMS):
            alarms.add("%02d:00" % index)
        self.assertEqual(self.call(["alarms", "add", "--time", "23:00"])[0], 1)

    def test_corrupt_saved_alarms_are_filtered(self):
        settings.directory().mkdir()
        good = {"id": 2, "time": "06:15", "days": [1], "label": "ok", "enabled": True}
        (settings.directory() / "settings.json").write_text(json.dumps({"alarms": [
            good, {**good, "id": 2}, {**good, "id": 3, "time": "6:15"}, {**good, "id": 4, "days": [9]},
            {**good, "id": 5, "label": "a\x01"}, {**good, "id": 6, "enabled": "yes"}, "junk", {**good, "id": "7"}]}))
        self.assertEqual(settings.load()["alarms"], [good])


class QuietHoursTests(Isolated):
    def test_schedule_round_trips(self):
        self.assertFalse(settings.load()["dnd_schedule"]["enabled"])
        code, result = self.call(["quiet-hours", "set", "--enabled", "yes", "--start", "21:30", "--end", "06:45"])
        self.assertEqual((code, result["schedule"]), (0, {"enabled": True, "start": "21:30", "end": "06:45"}))
        self.assertEqual(self.call(["quiet-hours", "get"])[1]["schedule"]["start"], "21:30")

    def test_bad_times_are_refused(self):
        for start in ("9:00", "25:00", "", "22:00; x"):
            self.assertEqual(self.call(["quiet-hours", "set", "--enabled", "yes", "--start", start, "--end", "07:00"])[0], 1)
        self.assertEqual(self.call(["quiet-hours", "set", "--start", "21:00", "--end", "07:00"])[0], 1)

    def test_corrupt_schedule_falls_back(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text('{"dnd_schedule": {"enabled": "yes", "start": "1", "end": "2"}}')
        self.assertEqual(settings.load()["dnd_schedule"], {"enabled": False, "start": "22:00", "end": "07:00"})


class SoundTests(Isolated):
    @patch("prismos.sound.subprocess.Popen")
    @patch("prismos.sound.shutil.which", side_effect=lambda name: "/usr/bin/" + name if name == "paplay" else None)
    @patch("prismos.sound.Path.is_file", return_value=True)
    def test_plays_only_known_files_with_an_argv_list(self, is_file, which, popen):
        sound.play("alarm")
        self.assertEqual(popen.call_args.args[0], ["paplay", sound.SOUNDS["alarm"]])

    def test_unknown_names_and_missing_pieces_are_errors(self):
        with self.assertRaises(ValueError):
            sound.play("../../etc/passwd")
        with patch("prismos.sound.Path.is_file", return_value=False):
            with self.assertRaises(CommandError):
                sound.play("ding")
        with patch("prismos.sound.Path.is_file", return_value=True), patch("prismos.sound.shutil.which", return_value=None):
            with self.assertRaises(CommandError):
                sound.play("ding")


if __name__ == "__main__":
    unittest.main()
