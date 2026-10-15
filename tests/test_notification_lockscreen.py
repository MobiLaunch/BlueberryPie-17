import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, notifyprefs, settings

ROOT = Path(__file__).resolve().parent.parent


class LockScreenNotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        runtime = Path(self.temp.name) / "run"
        runtime.mkdir(mode=0o700)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name + "/config", "XDG_RUNTIME_DIR": str(runtime)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, out.getvalue()

    def test_nothing_to_say_by_default(self):
        self.assertEqual(notifyprefs.summary(), "")
        self.assertEqual(self.run_cli(["lock-summary"]), (0, "\n"))

    def test_the_count_is_stored_privately_and_summarised_in_plain_text(self):
        code, out = self.run_cli(["notifications", "count", "3"])
        self.assertEqual((code, json.loads(out)), (0, {"ok": True, "count": 3, "stored": True}))
        path = notifyprefs.count_path()
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertEqual(path.read_text(), "3", "only the number is stored, no text")
        self.assertEqual(self.run_cli(["lock-summary"]), (0, "3 notifications\n"))
        notifyprefs.set_count(1)
        self.assertEqual(notifyprefs.summary(), "1 notification")
        notifyprefs.set_count(0)
        self.assertEqual(notifyprefs.summary(), "")
        self.assertEqual([p.name for p in path.parent.iterdir()], ["notification-count"], "no temp files left behind")

    def test_the_user_can_turn_it_off(self):
        notifyprefs.set_count(5)
        self.assertEqual(self.run_cli(["notifications", "lock-count", "no"])[0], 0)
        self.assertIs(settings.load()["lock_notifications"], False)
        self.assertEqual(notifyprefs.summary(), "")
        notifyprefs.set_lock_count("yes")
        self.assertEqual(notifyprefs.summary(), "5 notifications")

    def test_bad_values_are_refused(self):
        for value in ("-1", "1000", "abc", "", "1.5", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                notifyprefs.set_count(value)
        for value in ("true", "", None):
            with self.subTest(toggle=value), self.assertRaises(ValueError):
                notifyprefs.set_lock_count(value)
        self.assertFalse(notifyprefs.count_path().exists())

    def test_a_damaged_or_missing_file_reads_as_zero(self):
        path = notifyprefs.count_path()
        self.assertEqual(notifyprefs.read_count(), 0)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        for text in ("lots", "-4", "99999", ""):
            path.write_text(text)
            self.assertEqual(notifyprefs.read_count(), 0, text)

    def test_without_a_runtime_directory_nothing_is_written(self):
        with patch.dict(os.environ):
            os.environ.pop("XDG_RUNTIME_DIR")
            self.assertEqual(notifyprefs.set_count(2), {"ok": True, "count": 2, "stored": False})
            self.assertEqual(notifyprefs.summary(), "")

    def test_the_lock_screen_prints_only_the_summary(self):
        config = (ROOT / "config/hypr/hyprlock.conf").read_text()
        self.assertIn("cmd[update:3000] prismctl lock-summary", config)
        self.assertNotIn("summary", config.replace("lock-summary", ""), "no notification text is ever requested")


if __name__ == "__main__":
    unittest.main()
