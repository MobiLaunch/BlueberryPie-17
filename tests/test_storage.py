import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, storage


def put(path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


class StorageUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def sizes(self, **kwargs):
        return {item["id"]: item["bytes"] for item in storage.usage(self.home, **kwargs)["items"]}

    def test_top_level_folders_map_to_categories(self):
        put(self.home / "Documents" / "a" / "deep" / "report.txt", 40000)
        put(self.home / "Downloads" / "installer.bin", 40000)
        put(self.home / ".cache" / "thumbs" / "x.png", 40000)
        put(self.home / ".config" / "app" / "conf", 8000)
        put(self.home / "stray.txt", 8000)
        sizes = self.sizes()
        self.assertGreaterEqual(sizes["documents"], 40000)
        self.assertGreaterEqual(sizes["downloads"], 40000)
        self.assertGreaterEqual(sizes["cache"], 40000)
        self.assertGreaterEqual(sizes["apps"], 8000)
        self.assertGreaterEqual(sizes["other"], 8000)
        self.assertEqual(sizes["music"], 0)

    def test_total_matches_the_category_sum(self):
        put(self.home / "Pictures" / "p.jpg", 20000)
        put(self.home / "Videos" / "v.mp4", 20000)
        result = storage.usage(self.home)
        self.assertEqual(result["yours"], sum(item["bytes"] for item in result["items"]))
        self.assertGreater(result["total"], 0)
        self.assertEqual([item["id"] for item in result["items"]],
                         [key for key, _ in storage.CATEGORIES])

    def test_symlinks_are_not_followed(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        put(Path(outside.name) / "big.bin", 400000)
        (self.home / "Documents").mkdir()
        os.symlink(outside.name, self.home / "Documents" / "link")
        self.assertLess(self.sizes()["documents"], 100000)

    def test_walk_stops_at_the_entry_cap_and_says_so(self):
        for index in range(30):
            put(self.home / "Documents" / f"f{index}.txt", 10)
        with patch.object(storage, "MAX_ENTRIES", 10):
            result = storage.usage(self.home)
        self.assertTrue(result["truncated"])

    def test_walk_stops_at_the_deadline_and_says_so(self):
        put(self.home / "Documents" / "a" / "b.txt", 10)
        ticks = iter(range(0, 1000, 100))
        result = storage.usage(self.home, clock=lambda: next(ticks))
        self.assertTrue(result["truncated"])

    def test_unreadable_home_reports_zero_instead_of_failing(self):
        with patch("prismos.storage.os.scandir", side_effect=PermissionError):
            result = storage.usage(self.home)
        self.assertEqual(result["yours"], 0)
        self.assertFalse(result["truncated"])


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_RUNTIME_DIR": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_clear_removes_only_the_preview_folder(self):
        folder = Path(self.temp.name) / "prismos-previews"
        put(folder / "0xabc-1.png", 1234)
        keep = Path(self.temp.name) / "keep.txt"
        keep.write_text("keep")
        self.assertEqual(storage.preview_bytes(), 1234)
        result = storage.clear_previews()
        self.assertEqual(result["previews"], 0)
        self.assertFalse(folder.exists())
        self.assertTrue(keep.exists())

    def test_symlinked_preview_is_not_counted(self):
        folder = Path(self.temp.name) / "prismos-previews"
        folder.mkdir()
        target = Path(self.temp.name) / "secret.bin"
        target.write_bytes(b"x" * 5000)
        os.symlink(target, folder / "0xabc-1.png")
        self.assertEqual(storage.preview_bytes(), 0)

    def test_cli_round_trip(self):
        for argv, key in ((["storage", "usage"], "items"), (["storage", "clear-previews"], "previews")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = cli.main(argv)
            self.assertEqual(code, 0)
            self.assertIn(key, json.loads(out.getvalue()))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.main(["storage", "format"])


if __name__ == "__main__":
    unittest.main()
