import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, settings, theme

SEEDS = ("#8469cf", "#47846a", "#c27443", "#b85c80", "#000000", "#ffffff", "#808080", "#3a7bd5")
PAIRS = (("primary", "onPrimary"), ("primaryContainer", "onPrimaryContainer"), ("secondaryContainer", "onSecondaryContainer"),
         ("tertiaryContainer", "onTertiaryContainer"), ("surface", "onSurface"), ("surfaceContainerHigh", "onSurface"),
         ("surfaceVariant", "onSurfaceVariant"), ("errorContainer", "onErrorContainer"), ("inverseSurface", "inverseOnSurface"))


class SchemeTests(unittest.TestCase):
    def test_every_scheme_holds_contrast_for_every_pair(self):
        for scheme in theme.SCHEMES:
            for seed in SEEDS:
                for dark in (False, True):
                    colors = theme.palette(seed, dark, scheme)
                    for background, content in PAIRS:
                        self.assertGreaterEqual(theme.contrast(colors[background], colors[content]), 4.5,
                                                (scheme, seed, dark, background))

    def test_schemes_are_distinct_and_monochrome_is_gray(self):
        seen = {scheme: theme.palette("#8469cf", False, scheme)["primary"] for scheme in theme.SCHEMES}
        self.assertEqual(len(set(seen.values())), len(seen))
        gray = theme.palette("#8469cf", True, "monochrome")
        for role in ("primary", "secondary", "tertiary", "surface", "surfaceContainer"):
            red, green, blue = (int(gray[role][i:i + 2], 16) for i in (1, 3, 5))
            self.assertLessEqual(max(red, green, blue) - min(red, green, blue), 2, role)
        self.assertEqual(theme.palette("#8469cf")["scheme"], "tonal_spot")

    def test_default_matches_the_published_tonal_spot_reference(self):
        self.assertEqual(theme.palette("#6750a4"), theme.palette("#6750a4", False, "tonal_spot"))

    def test_unknown_scheme_is_refused(self):
        for value in ("rainbow", "", None, "tonal_spot; rm"):
            with self.assertRaises(ValueError):
                theme.palette("#8469cf", False, value)


class PreferenceTests(unittest.TestCase):
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

    def test_cli_saves_scheme_and_text_size(self):
        code, roles = self.call(["theme", "--scheme", "vibrant", "--font-scale", "1.15"])
        self.assertEqual((code, roles["scheme"]), (0, "vibrant"))
        self.assertEqual((settings.load()["scheme"], settings.load()["font_scale"]), ("vibrant", 1.15))
        self.assertEqual(self.call(["theme"])[1]["scheme"], "vibrant")

    def test_invalid_text_size_is_a_json_error_and_changes_nothing(self):
        code, result = self.call(["theme", "--font-scale", "5"])
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(settings.load()["font_scale"], 1.0)

    def test_corrupt_values_fall_back(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text('{"scheme": "../x", "font_scale": 9, "seed": "#112233"}')
        loaded = settings.load()
        self.assertEqual((loaded["scheme"], loaded["font_scale"], loaded["seed"]), ("tonal_spot", 1.0, "#112233"))


if __name__ == "__main__":
    unittest.main()
