"""Material 3 dynamic color for PrismOS.

`palette()` builds the Tonal Spot scheme (the Android default) from a seed color
using the CAM16/HCT engine in `hct.py`. Roles use the Material 3 names and
tone mapping, so contrast follows from tone differences rather than guesses.
"""
import re

from .hct import TonalPalette, hct_from_hex

PALETTES = {"Lilac": "#8469cf", "Mint": "#47846a", "Tangerine": "#c27443", "Rose": "#b85c80"}

# Role -> (palette, light tone, dark tone). Tones follow the Material 3 baseline.
ROLES = {
    "primary": ("primary", 40, 80), "onPrimary": ("primary", 100, 20),
    "primaryContainer": ("primary", 90, 30), "onPrimaryContainer": ("primary", 10, 90),
    "inversePrimary": ("primary", 80, 40),
    "secondary": ("secondary", 40, 80), "onSecondary": ("secondary", 100, 20),
    "secondaryContainer": ("secondary", 90, 30), "onSecondaryContainer": ("secondary", 10, 90),
    "tertiary": ("tertiary", 40, 80), "onTertiary": ("tertiary", 100, 20),
    "tertiaryContainer": ("tertiary", 90, 30), "onTertiaryContainer": ("tertiary", 10, 90),
    "error": ("error", 40, 80), "onError": ("error", 100, 20),
    "errorContainer": ("error", 90, 30), "onErrorContainer": ("error", 10, 90),
    "surface": ("neutral", 98, 6), "onSurface": ("neutral", 10, 90),
    "surfaceDim": ("neutral", 87, 6), "surfaceBright": ("neutral", 98, 24),
    "surfaceContainerLowest": ("neutral", 100, 4), "surfaceContainerLow": ("neutral", 96, 10),
    "surfaceContainer": ("neutral", 94, 12), "surfaceContainerHigh": ("neutral", 92, 17),
    "surfaceContainerHighest": ("neutral", 90, 22),
    "surfaceVariant": ("neutralVariant", 90, 30), "onSurfaceVariant": ("neutralVariant", 30, 80),
    "outline": ("neutralVariant", 50, 60), "outlineVariant": ("neutralVariant", 80, 30),
    "inverseSurface": ("neutral", 20, 90), "inverseOnSurface": ("neutral", 95, 20),
    "scrim": ("neutral", 0, 0), "shadow": ("neutral", 0, 0),
}


def rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Use a six-digit hex color, for example #8469cf")
    return tuple(int(value[i:i+2], 16) / 255 for i in (1, 3, 5))


def luminance(value):
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb(value)]
    return sum(c*w for c, w in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)


def tonal_spot(seed):
    """Tonal Spot core palettes: fixed chroma per role, hue taken from the seed."""
    hue, _, _ = hct_from_hex(seed)
    return {"primary": TonalPalette(hue, 36), "secondary": TonalPalette(hue, 16),
            "tertiary": TonalPalette(hue + 60, 24), "neutral": TonalPalette(hue, 6),
            "neutralVariant": TonalPalette(hue, 8), "error": TonalPalette(25, 84)}


def palette(seed="#8469cf", dark=False):
    rgb(seed)  # validates; raises ValueError on anything but #rrggbb
    seed = seed.lower()
    tones = tonal_spot(seed)
    roles = {name: tones[source].tone(dark_tone if dark else light_tone)
             for name, (source, light_tone, dark_tone) in ROLES.items()}
    roles["surfaceTint"] = roles["primary"]
    roles["seed"] = seed
    roles["dark"] = bool(dark)
    return roles


def legacy_tokens(roles):
    """Pre-Material-3 role names, used by the offline HTML preview.

    The preview's CSS predates the M3 role set: its "primary" was a tonal
    container, "primaryStrong" the saturated accent. Mapping is explicit here
    so preview and native shell stay derived from the same scheme.
    """
    mapped = {
        "primary": roles["primaryContainer"], "onPrimary": roles["onPrimaryContainer"],
        "primaryStrong": roles["primary"], "onPrimaryStrong": roles["onPrimary"],
        "secondary": roles["secondaryContainer"], "onSecondary": roles["onSecondaryContainer"],
        "tertiary": roles["tertiaryContainer"], "onTertiary": roles["onTertiaryContainer"],
        "surface": roles["surface"], "onSurface": roles["onSurface"],
        "surfaceContainer": roles["surfaceContainer"], "onSurfaceContainer": roles["onSurface"],
        "surfaceHigh": roles["surfaceContainerHigh"], "onSurfaceHigh": roles["onSurface"],
        "outline": roles["outline"], "error": roles["error"], "onError": roles["onError"],
    }
    mapped["seed"], mapped["dark"] = roles["seed"], roles["dark"]
    return mapped


def wallpaper_seed(path):
    """Pick the most representative accent in an image, as Material scoring does:
    favor populous colors, require some chroma, and prefer moderately vivid ones."""
    from PIL import Image
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((96, 96))
        colors = image.quantize(colors=12).convert("RGB").getcolors(96*96) or []
        total = sum(count for count, _ in colors) or 1

        def score(item):
            count, color = item
            hex_color = "#%02x%02x%02x" % color
            _, chroma, tone = hct_from_hex(hex_color)
            if chroma < 5 or not 15 < tone < 90:
                return 0
            proportion = count / total
            return proportion * 100 * 0.7 + (chroma - 48) * (0.1 if chroma > 48 else 0.3)
        candidates = [item for item in colors if score(item) > 0]
        if not candidates:
            return "#8469cf"
        color = max(candidates, key=score)[1]
        return "#%02x%02x%02x" % color

