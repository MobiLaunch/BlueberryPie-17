import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from prismos import cli, clockset, inputs, regional, settings, worldclock
from prismos.system import CommandError

ZONES = regional.timezones()
HAS_ZONES = "Europe/Lisbon" in ZONES and "Asia/Tokyo" in ZONES


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


class DateTimeTests(Isolated):
    @patch("prismos.clockset.run", return_value="Timezone=Europe/Lisbon\nNTP=yes\nNTPSynchronized=no\n")
    @patch("prismos.clockset.shutil.which", return_value="/usr/bin/timedatectl")
    def test_status_reads_timedated_facts(self, which, run):
        result = self.call(["datetime", "get"])[1]
        self.assertEqual((result["timezone"], result["ntp"], result["synchronized"], result["clock_24h"]),
                         ("Europe/Lisbon", True, False, True))

    @patch("prismos.clockset.shutil.which", return_value=None)
    def test_missing_timedatectl_is_reported_not_fatal(self, which):
        self.assertFalse(self.call(["datetime", "get"])[1]["available"])

    @unittest.skipUnless(HAS_ZONES, "tz database missing")
    @patch("prismos.clockset.status", return_value={"ok": True})
    @patch("prismos.clockset.run")
    def test_only_listed_zones_and_booleans_reach_timedatectl(self, run, status):
        clockset.set_timezone("Europe/Lisbon")
        run.assert_called_with(["timedatectl", "set-timezone", "Europe/Lisbon"], timeout=60)
        for bad in ("../etc/passwd", "Mars/Base", "Europe/Lisbon; reboot", ""):
            with self.assertRaises(ValueError):
                clockset.set_timezone(bad)
        clockset.set_ntp("yes")
        run.assert_called_with(["timedatectl", "set-ntp", "true"], timeout=60)
        with self.assertRaises(ValueError):
            clockset.set_ntp("maybe")
        self.assertEqual(run.call_count, 2)

    def test_twenty_four_hour_preference_persists(self):
        with patch("prismos.clockset.shutil.which", return_value=None):
            self.assertFalse(self.call(["datetime", "24h", "no"])[1]["clock_24h"])
        self.assertFalse(settings.load()["clock_24h"])
        self.assertEqual(self.call(["datetime", "24h", "x"])[0], 1)


@unittest.skipUnless(HAS_ZONES, "tz database missing")
class WorldClockTests(Isolated):
    def test_entries_show_local_time_day_and_offset(self):
        now = datetime(2026, 1, 15, 23, 30, tzinfo=timezone.utc)
        with patch.dict(os.environ, {"TZ": "UTC"}):
            import time
            time.tzset()
            tokyo = worldclock.entry("Asia/Tokyo", now)
        self.assertEqual((tokyo["hour"], tokyo["minute"], tokyo["day"], tokyo["offset"], tokyo["label"]), (8, 30, 1, 540, "Tokyo"))

    def test_add_remove_limit_and_validation(self):
        self.assertEqual([c["zone"] for c in self.call(["worldclock", "add", "Asia/Tokyo"])[1]["clocks"]], ["Asia/Tokyo"])
        self.call(["worldclock", "add", "Asia/Tokyo"])
        self.assertEqual(len(settings.load()["world_clocks"]), 1)
        for bad in ("Mars/Base", "../x", ""):
            self.assertEqual(self.call(["worldclock", "add", bad])[0], 1, bad)
        for zone in [z for z in ZONES if z != "Asia/Tokyo"][: settings.MAX_WORLD_CLOCKS - 1]:
            worldclock.add(zone)
        self.assertEqual(self.call(["worldclock", "add", "Europe/Lisbon"])[0], 1 if "Europe/Lisbon" not in settings.load()["world_clocks"] else 0)
        self.assertEqual(self.call(["worldclock", "remove", "Asia/Tokyo"])[1]["clocks"][0]["zone"] != "Asia/Tokyo", True)

    def test_corrupt_saved_zones_are_filtered(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text(json.dumps({"world_clocks": ["Asia/Tokyo", "Asia/Tokyo", "nope", 5, "../x"]}))
        self.assertEqual(settings.load()["world_clocks"], ["Asia/Tokyo"])


class KeyboardLayoutTests(Isolated):
    @patch("prismos.inputs.run")
    def test_layout_applies_then_persists(self, run):
        result = self.call(["input", "set", "keyboard", "de"])[1]
        self.assertEqual(result["settings"]["keyboard"], "de")
        calls = [call.args[0] for call in run.call_args_list]
        self.assertIn(["hyprctl", "keyword", "input:kb_layout", "de"], calls)
        self.assertIn(["hyprctl", "keyword", "input:kb_variant", ""], calls)
        self.assertEqual(settings.load()["keyboard"], "de")

    @patch("prismos.inputs.run", side_effect=CommandError("no compositor"))
    def test_failed_apply_is_not_saved(self, run):
        self.assertEqual(self.call(["input", "set", "keyboard", "fr"])[0], 1)
        self.assertEqual(settings.load()["keyboard"], "us")

    @patch("prismos.inputs.run")
    def test_unknown_layouts_are_refused(self, run):
        for bad in ("qwertz", "../x", "us; reboot", ""):
            self.assertEqual(self.call(["input", "set", "keyboard", bad])[0], 1, bad)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
