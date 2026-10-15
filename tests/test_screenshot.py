import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from prismos import cli, screenshot
from prismos.system import CommandError


class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        which = patch("prismos.screenshot.shutil.which", side_effect=lambda name: "/usr/bin/" + name)
        which.start()
        self.addCleanup(which.stop)
        self.when = datetime(2026, 10, 15, 9, 8, 7)

    @patch("prismos.screenshot.subprocess.run", return_value=MagicMock(returncode=0))
    @patch("prismos.screenshot.run")
    def test_full_screen_capture_is_saved_and_copied(self, run, copier):
        run.side_effect = lambda argv, timeout=4: Path(argv[-1]).write_bytes(b"png") and ""
        result = screenshot.capture("full", self.when)
        path = Path(self.temp.name) / "Pictures/Screenshots/Screenshot-2026-10-15-090807.png"
        run.assert_called_once_with(["grim", str(path)], timeout=20)
        self.assertEqual((result["name"], result["copied"]), (path.name, True))
        self.assertEqual(copier.call_args.args[0], ["wl-copy", "--type", "image/png"])

    @patch("prismos.screenshot.subprocess.run", return_value=MagicMock(returncode=1))
    @patch("prismos.screenshot.run")
    def test_area_uses_slurp_output_only_when_it_is_a_region(self, run, copier):
        path = Path(self.temp.name) / "Pictures/Screenshots/Screenshot-2026-10-15-090807.png"
        run.side_effect = ["10,20 300x200", ""]
        screenshot.capture("area", self.when)
        self.assertEqual(run.call_args_list[1].args[0], ["grim", "-g", "10,20 300x200", str(path)])
        run.reset_mock(side_effect=True)
        for bad in ("10,20 300x200; reboot", "", "1,2 3x4 extra", "$(id)"):
            run.side_effect = [bad]
            with self.assertRaisesRegex(ValueError, "cancelled"):
                screenshot.capture("area", self.when)
        run.side_effect = CommandError("selection cancelled")
        with self.assertRaisesRegex(ValueError, "cancelled"):
            screenshot.capture("area", self.when)

    @patch("prismos.screenshot.subprocess.run")
    @patch("prismos.screenshot.run")
    def test_window_uses_the_focused_window_box(self, run, copier):
        run.side_effect = [json.dumps({"at": [100, 40], "size": [800, 600]}), ""]
        copier.return_value = MagicMock(returncode=0)
        screenshot.capture("window", self.when)
        self.assertEqual(run.call_args_list[1].args[0][1:3], ["-g", "100,40 800x600"])
        run.side_effect = ["{}"]
        with self.assertRaisesRegex(ValueError, "No window"):
            screenshot.capture("window", self.when)

    def test_unknown_mode_and_missing_tools_are_clear_errors(self):
        with self.assertRaises(ValueError):
            screenshot.capture("everything")
        with patch("prismos.screenshot.shutil.which", return_value=None):
            with self.assertRaisesRegex(CommandError, "grim"):
                screenshot.capture("full")

    @patch("prismos.screenshot.run")
    def test_cli_returns_json(self, run):
        run.return_value = ""
        with patch("prismos.screenshot.subprocess.run", return_value=MagicMock(returncode=0)):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli.main(["screenshot", "full"]), 0)
        self.assertTrue(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
