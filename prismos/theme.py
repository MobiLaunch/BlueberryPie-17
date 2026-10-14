"""Seed-derived, contrast-checked tonal colors for the initial shell.

This is an HSL tonal generator, not Google's HCT/Monet algorithm. The adapter
boundary is deliberate so HCT can replace it without changing any component.
"""
import colorsys
import re

PALETTES = {"Lilac": "#8469cf", "Mint": "#47846a", "Tangerine": "#c27443", "Rose": "#b85c80"}


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


def ink(background):
    selected = max(("#19151e", "#ffffff"), key=lambda c: contrast(c, background))
    if contrast(selected, background) >= 4.5:
        return selected
    return max(("#000000", "#ffffff"), key=lambda c: contrast(c, background))


def palette(seed="#8469cf", dark=False):
    hue, _, saturation = colorsys.rgb_to_hls(*rgb(seed))
    saturation = max(0.3, min(0.65, saturation))

    def tone(lightness, sat=None, offset=0):
        values = colorsys.hls_to_rgb((hue+offset) % 1, lightness, saturation if sat is None else sat)
        return "#" + "".join(f"{round(c*255):02x}" for c in values)

    roles = {
        "primary": tone(.79 if dark else .84),
        "primaryStrong": tone(.74 if dark else .34),
        "secondary": tone(.76 if dark else .84, .35, .38),
        "tertiary": tone(.77 if dark else .86, .65, -.22),
        "surface": tone(.09 if dark else .98, .12),
        "surfaceContainer": tone(.15 if dark else .94, .14),
        "surfaceHigh": tone(.22 if dark else .88, .13),
        "outline": tone(.65 if dark else .48, .1),
        "error": "#ffb4ab" if dark else "#a8332a",
    }
    for suffix, role in (("Primary", "primary"), ("PrimaryStrong", "primaryStrong"),
                         ("Secondary", "secondary"), ("Tertiary", "tertiary"),
                         ("Surface", "surface"), ("SurfaceContainer", "surfaceContainer"),
                         ("SurfaceHigh", "surfaceHigh"), ("Error", "error")):
        roles["on"+suffix] = ink(roles[role])
    roles["seed"] = seed.lower()
    roles["dark"] = bool(dark)
    return roles


def wallpaper_seed(path):
    from PIL import Image
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((96, 96))
        colors = image.quantize(colors=12).convert("RGB").getcolors(96*96) or []
        def score(item):
            count, color = item
            _, lightness, sat = colorsys.rgb_to_hls(*(c/255 for c in color))
            return count * (sat+.05) if .18 < lightness < .88 else 0
        candidates = [item for item in colors if score(item) > 0]
        if not candidates:
            return "#8469cf"
        color = max(candidates, key=score)[1]
        return "#"+"".join(f"{c:02x}" for c in color)
