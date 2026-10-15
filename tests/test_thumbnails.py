import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, settings, thumbnails, windows
from prismos.system import CommandError


def window(address, workspace=1, x=0, y=0, width=800, height=600, **extra):
    return {"address": address, "class": "app", "title": "t", "workspace": workspace, "pid": 1, "recency": 0,
            "monitor": 0, "x": x, "y": y, "width": width, "height": height, "focused": False, "floating": False,
            "maximized": False, "minimized": False, "hidden": False, **extra}


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name, "XDG_RUNTIME_DIR": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        which = patch("prismos.thumbnails.shutil.which", return_value="/usr/bin/grim")
        which.start()
        self.addCleanup(which.stop)
        self.calls = []

    def fake_run(self, args, timeout=4):
        if args[:3] == ["hyprctl", "-j", "activeworkspace"]:
            return json.dumps({"id": 1})
        if args[0] == "grim":
            self.calls.append(args)
            Path(args[-1]).write_bytes(b"png")
            return ""
        raise AssertionError(args)

    def call(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class CaptureTests(Isolated):
    def capture(self, clients, now=100):
        with patch("prismos.thumbnails.windows.clients", return_value=clients), \
                patch("prismos.thumbnails.run", side_effect=self.fake_run):
            return thumbnails.capture(now)

    def test_only_visible_windows_on_the_current_workspace_are_captured(self):
        result = self.capture([window("0xaa", 1), window("0xbb", 2), window("0xcc", 1, minimized=True),
                               window("0xdd", 1, hidden=True), window("0xee", 1, width=4)])
        self.assertEqual(result["captured"], 1)
        self.assertEqual(self.calls, [["grim", "-s", "0.3", "-g", "0,0 800x600", str(thumbnails.directory() / "0xaa-100.png")]])
        self.assertEqual(list(result["thumbs"]), ["0xaa"])

    def test_old_previews_are_replaced_and_closed_windows_are_deleted(self):
        self.capture([window("0xaa"), window("0xbb")], now=100)
        result = self.capture([window("0xaa")], now=200)
        names = sorted(path.name for path in thumbnails.directory().iterdir())
        self.assertEqual(names, ["0xaa-200.png"])
        self.assertEqual(list(result["thumbs"]), ["0xaa"])

    def test_previews_of_windows_on_other_workspaces_are_kept_from_earlier(self):
        self.capture([window("0xaa", 1), window("0xbb", 1)], now=100)
        result = self.capture([window("0xaa", 2), window("0xbb", 1)], now=200)
        self.assertEqual(sorted(result["thumbs"]), ["0xaa", "0xbb"])
        self.assertTrue(result["thumbs"]["0xaa"].endswith("0xaa-100.png"))
        self.assertTrue(result["thumbs"]["0xbb"].endswith("0xbb-200.png"))

    def test_regions_are_integers_only_and_bounded(self):
        self.assertEqual(thumbnails.region(window("0x1", x=-20, y=5, width=300, height=200)), "-20,5 300x200")
        self.assertIsNone(thumbnails.region(window("0x1", width=20000)))
        self.assertIsNone(thumbnails.region(window("0x1", x=10**7)))

    def test_one_failed_capture_does_not_lose_the_rest(self):
        def flaky(args, timeout=4):
            if args[0] == "grim" and "0xaa" in args[-1]:
                raise CommandError("compositor said no")
            return self.fake_run(args, timeout)
        with patch("prismos.thumbnails.windows.clients", return_value=[window("0xaa"), window("0xbb")]), \
                patch("prismos.thumbnails.run", side_effect=flaky):
            result = thumbnails.capture(5)
        self.assertEqual((result["captured"], list(result["thumbs"])), (1, ["0xbb"]))

    def test_foreign_files_are_ignored_and_removed(self):
        folder = thumbnails.directory()
        folder.mkdir(parents=True)
        (folder / "notes.png").write_bytes(b"x")
        (folder / "0xaa-1.png").write_bytes(b"x")
        (folder / "0xaa-notanumber.png").write_bytes(b"x")
        self.assertEqual(list(thumbnails.existing()), ["0xaa"])
        self.capture([window("0xaa", 2)], now=9)
        self.assertEqual(sorted(path.name for path in folder.iterdir()), ["0xaa-1.png"])

    def test_missing_grim_is_a_clear_error(self):
        with patch("prismos.thumbnails.shutil.which", return_value=None):
            with self.assertRaisesRegex(CommandError, "grim"):
                thumbnails.capture()


class PrivacyTests(Isolated):
    def test_turning_previews_off_deletes_them_and_stops_capture(self):
        with patch("prismos.thumbnails.windows.clients", return_value=[window("0xaa")]), \
                patch("prismos.thumbnails.run", side_effect=self.fake_run):
            thumbnails.capture(1)
            self.assertTrue(thumbnails.directory().exists())
            self.call(["thumbnails", "enable", "no"])
            self.assertFalse(thumbnails.directory().exists())
            self.assertEqual(thumbnails.capture(2)["captured"], 0)
        self.assertEqual(self.calls.__len__(), 1)
        self.assertFalse(settings.load()["recents_previews"])

    def test_directory_is_private(self):
        with patch("prismos.thumbnails.windows.clients", return_value=[window("0xaa")]), \
                patch("prismos.thumbnails.run", side_effect=self.fake_run):
            thumbnails.capture(1)
        self.assertEqual(thumbnails.directory().stat().st_mode & 0o777, 0o700)

    def test_bad_enable_values_are_refused(self):
        self.assertEqual(self.call(["thumbnails", "enable", "maybe"])[0], 1)

    def test_window_geometry_comes_from_hyprctl(self):
        raw = [{"address": "0xaa", "mapped": True, "class": "foot", "title": "t", "workspace": {"id": 1}, "pid": 1,
                "focusHistoryID": 0, "at": [10, 20], "size": [300, 200]}]
        with patch("prismos.windows.run", side_effect=lambda args, timeout=4: json.dumps(raw if "clients" in args else {})):
            entry = windows.clients()[0]
        self.assertEqual((entry["x"], entry["y"], entry["width"], entry["height"]), (10, 20, 300, 200))


if __name__ == "__main__":
    unittest.main()
