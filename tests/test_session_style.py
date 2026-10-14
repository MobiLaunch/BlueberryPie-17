import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "bin/prism-style-env"
THEMES = ROOT / "packaging/themes"


class SessionStyleTests(unittest.TestCase):
    def resolve(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "prismos"
            d.mkdir()
            (d / "settings.json").write_text(data)
            env = dict(os.environ)
            env["XDG_CONFIG_HOME"] = tmp
            proc = subprocess.run([sys.executable, str(STYLE)], cwd=ROOT,
                                  env=env, capture_output=True, text=True,
                                  check=True, timeout=8)
            return proc.stdout.splitlines()

    def test_four_palettes_and_dark_variants_ship_gtk3_and_gtk4(self):
        for name in ("Lilac", "Mint", "Tangerine", "Rose"):
            for suffix in ("", "-Dark"):
                theme = THEMES / ("PrismOS-" + name + suffix)
                with self.subTest(theme=theme):
                    for toolkit in ("gtk-3.0", "gtk-4.0"):
                        css = theme / toolkit / "gtk.css"
                        self.assertTrue(css.is_file(), css)
                        text = css.read_text()
                        self.assertIn("entry", text)
                        self.assertIn("menu", text)
                        self.assertIn("switch", text)

    def test_saved_palettes_choose_correct_toolkit_style(self):
        for seed, name, accent in (
            ("#8469cf", "Lilac", "DeepPurple"),
            ("#47846a", "Mint", "Teal"),
            ("#c27443", "Tangerine", "DeepOrange"),
            ("#b85c80", "Rose", "Pink"),
        ):
            self.assertEqual(self.resolve(
                '{"seed":"' + seed + '","dark":true}'),
                ["PrismOS-" + name + "-Dark", "Dark", accent])

    def test_unrecognized_custom_seed_falls_back_without_unsafe_text(self):
        self.assertEqual(self.resolve('{"seed":"#ffffff","dark":false}'),
                         ["PrismOS-Lilac", "Light", "DeepPurple"])


if __name__ == "__main__":
    unittest.main()
