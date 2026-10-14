import random
import unittest

from prismos import hct, theme


def close(a, b, tolerance=2):
    return all(abs(x - y) <= tolerance for x, y in zip(hct.rgb_from_hex(a), hct.rgb_from_hex(b)))


class HctTests(unittest.TestCase):
    def test_tone_is_luminance_and_round_trips(self):
        generator = random.Random(17)
        for _ in range(250):
            hue, chroma, tone = generator.uniform(0, 360), generator.uniform(4, 60), generator.uniform(5, 95)
            self.assertLess(abs(hct.lstar_from_rgb(hct.hct_to_rgb(hue, chroma, tone)) - tone), 0.6)

    def test_hue_and_chroma_survive_in_gamut_round_trip(self):
        generator = random.Random(23)
        for _ in range(150):
            hue, tone = generator.uniform(0, 360), generator.uniform(30, 80)
            h2, c2, _ = hct.cam_from_rgb(hct.hct_to_rgb(hue, 20, tone))
            self.assertLess(min(abs(h2 - hue), 360 - abs(h2 - hue)), 3)
            self.assertLess(abs(c2 - 20), 2.5)

    def test_matches_published_material_tonal_spot_scheme(self):
        # Material Theme Builder, source #6750A4, Tonal Spot, contrast 0.
        light, dark = theme.palette("#6750a4"), theme.palette("#6750a4", True)
        expected_light = {"primary": "#65558f", "primaryContainer": "#e9ddff", "onPrimaryContainer": "#201047",
                          "secondary": "#625b71", "secondaryContainer": "#e8def8", "tertiary": "#7e5260",
                          "tertiaryContainer": "#ffd9e3", "onSurface": "#1d1b20", "outline": "#7a757f",
                          "outlineVariant": "#cac4cf"}
        for role, value in expected_light.items():
            with self.subTest(role=role):
                self.assertTrue(close(light[role], value), (role, light[role], value))
        self.assertTrue(close(dark["primary"], "#cfbdfe"))
        self.assertTrue(close(dark["surface"], "#141218"))

    def test_out_of_gamut_request_lowers_chroma_instead_of_failing(self):
        rgb = hct.hct_to_rgb(110, 120, 90)
        self.assertEqual(len(rgb), 3)
        self.assertLess(abs(hct.lstar_from_rgb(rgb) - 90), 1)

    def test_greys_and_extremes_do_not_break(self):
        for seed in ("#000000", "#ffffff", "#808080"):
            for dark in (False, True):
                colors = theme.palette(seed, dark)
                self.assertGreaterEqual(theme.contrast(colors["surface"], colors["onSurface"]), 7)


if __name__ == "__main__":
    unittest.main()
