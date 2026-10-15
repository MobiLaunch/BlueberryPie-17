import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from prismos import cli, settings, wallpaper


class WallpaperTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.home = Path(temp.name).resolve() / "home"; self.home.mkdir()
        env = patch.dict(os.environ, {"HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home / ".config"),
                                      "XDG_CACHE_HOME": str(self.home / ".cache")})
        env.start(); self.addCleanup(env.stop)
        (self.home / "Pictures/Wallpapers").mkdir(parents=True)
        Image.new("RGB", (64, 40), (71, 132, 106)).save(self.home / "Pictures/Wallpapers/mint.png")
        Image.new("RGB", (64, 40), (200, 90, 60)).save(self.home / "Pictures/orange.jpg")
        (self.home / "Pictures/notes.txt").write_text("not a picture")
        self.outside = Path(temp.name) / "outside.png"
        Image.new("RGB", (8, 8), (1, 2, 3)).save(self.outside)

    def test_lists_only_supported_pictures_with_cached_previews(self):
        names = [item["name"] for item in wallpaper.candidates()]
        self.assertEqual(sorted(names), ["mint", "orange"])
        self.assertTrue(all(item["thumbnail"].startswith("file://") for item in wallpaper.candidates()))

    def test_choosing_sets_wallpaper_and_derives_the_accent(self):
        result = wallpaper.choose(str(self.home / "Pictures/Wallpapers/mint.png"))
        self.assertEqual(result["seed"], "#47846a")
        saved = settings.load()
        self.assertEqual(saved["wallpaper"], str(self.home / "Pictures/Wallpapers/mint.png"))
        self.assertEqual(saved["seed"], "#47846a")

    def test_rejects_outside_home_traversal_wrong_type_and_symlink_escape(self):
        link = self.home / "Pictures/escape.png"
        link.symlink_to(self.outside)
        for raw in (str(self.outside), str(self.home / "Pictures/notes.txt"), "relative.png", "", None,
                    str(link), str(self.home / "Pictures/../../outside.png"), "/etc/passwd\0.png"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                wallpaper.choose(raw)
        self.assertEqual(settings.load()["wallpaper"], "")

    def test_oversized_pictures_are_refused(self):
        big = self.home / "Pictures/huge.png"
        Image.new("RGB", (4, 4)).save(big)
        with patch.object(wallpaper, "MAX_BYTES", 10), self.assertRaises(ValueError):
            wallpaper.choose(str(big))

    def test_clear_returns_to_the_theme_wallpaper(self):
        wallpaper.choose(str(self.home / "Pictures/orange.jpg"))
        wallpaper.clear()
        self.assertEqual(settings.load()["wallpaper"], "")

    def test_hostile_saved_values_are_ignored(self):
        for value in ("relative.png", "/tmp/x.sh", "/tmp/a\0.png", 5, ["/a.png"]):
            settings.directory().mkdir(parents=True, exist_ok=True)
            (settings.directory() / "settings.json").write_text(json.dumps({"wallpaper": value}))
            self.assertEqual(settings.load()["wallpaper"], "", value)

    def test_cli_round_trip(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["wallpaper", "set", str(self.home / "Pictures/orange.jpg")]), 0)
        self.assertTrue(json.loads(out.getvalue())["ok"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["wallpaper", "set", str(self.outside)]), 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
