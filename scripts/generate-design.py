#!/usr/bin/env python3
"""Generate shared preview tokens and original vector assets; no network."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from prismos.theme import PALETTES, palette

icons = {
    "wifi": '<path d="M3 8.5a15 15 0 0 1 18 0M6.5 12a9.3 9.3 0 0 1 11 0M10 15.5a3.8 3.8 0 0 1 4 0"/><circle cx="12" cy="19" r=".8" fill="#19151e"/>',
    "bluetooth": '<path d="m7 7 10 10-5 4V3l5 4L7 17"/>',
    "brightness": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/>',
    "volume": '<path d="M3 9h4l5-4v14l-5-4H3zM16 8a6 6 0 0 1 0 8M19 5a10 10 0 0 1 0 14"/>',
    "microphone": '<rect x="8" y="2" width="8" height="13" rx="4"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8"/>',
    "headphones": '<path d="M4 13v-2a8 8 0 0 1 16 0v2"/><rect x="2" y="11" width="5" height="10" rx="2.5"/><rect x="17" y="11" width="5" height="10" rx="2.5"/>',
    "moon": '<path d="M20 14.2A8.6 8.6 0 0 1 9.8 4 8.5 8.5 0 1 0 20 14.2Z"/>',
    "dnd": '<circle cx="12" cy="12" r="9"/><path d="M7 12h10"/>',
    "motion": '<path d="M3 6h7M2 11h5M3 16h7m5-12a8 8 0 1 1 0 16m-2-12 5 4-5 4"/>',
    "spark": '<path d="m12 2 2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6Z"/>',
    "apps": ''.join(f'<rect x="{x}" y="{y}" width="4" height="4" rx="1.4"/>' for x in (3,10,17) for y in (3,10,17)),
    "settings": '<path d="m9 3 1-1h4l1 3 3 1 2-1 2 4-2 2v3l2 2-2 4-3-1-2 1-1 2h-4l-1-2-3-1-2 1-2-4 2-2v-3L2 9l2-4 3 1 2-1Z"/><circle cx="12" cy="12" r="3"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "browser": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Z"/>',
    "terminal": '<rect x="2" y="4" width="20" height="16" rx="4"/><path d="m6 9 4 3-4 3m7 0h4"/>',
    "music": '<path d="M9 18V5l11-2v13M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2.5"/><ellipse cx="17" cy="16" rx="3" ry="2.5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="4"/><path d="M7 3v4m10-4v4M3 11h18m-14 5h3m4 0h3"/>',
    "photo": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="8" cy="8" r="2"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="4"/><path d="m4 7 8 6 8-6"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "arrow": '<path d="m8 4 8 8-8 8"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
    "power": '<path d="M12 2v10M6 5a9 9 0 1 0 12 0"/>',
}


def generate():
    target = ROOT/"design/icons"
    target.mkdir(exist_ok=True)
    for name, paths in icons.items():
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#19151e" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>\n'
        (target/f"{name}.svg").write_text(svg)
    preview_icons = {name:(target/f"{name}.svg").read_text().replace("#19151e", "currentColor") for name in icons}
    (ROOT/"preview/icons.js").write_text("window.PRISM_ICONS = "+json.dumps(preview_icons)+";\n")
    data = {"version": 1, "motion": {"fast":160, "standard":320, "slow":500},
            "shape": {"tileInactive":36, "tileActive":26, "panel":36, "app":24},
            "palettes": {name:{"seed":seed, "light":palette(seed), "dark":palette(seed, True)} for name, seed in PALETTES.items()}}
    (ROOT/"design/tokens.json").write_text(json.dumps(data, indent=2)+"\n")
    # Keep the review preview usable when opened directly through file://.
    (ROOT/"preview/tokens.js").write_text("window.PRISM_TOKENS = "+json.dumps(data)+";\n")
    flower = " ".join(f'{680+math.cos(a)*r:.1f},{350+math.sin(a)*r:.1f}' for i in range(241) for a in [i*math.pi/120] for r in [255+30*math.cos(a*8)])
    wallpaper = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">
<rect width="1920" height="1080" fill="#e9dff4"/>
<path d="M0 670Q400 450 760 810T1600 770V1080H0Z" fill="#d2bbe9"/>
<path d="M800 1080Q760 520 1200 500T1920 190V1080Z" fill="#cbe6d7"/>
<ellipse cx="1580" cy="180" rx="330" ry="310" fill="#f7d8ba"/>
<ellipse cx="1580" cy="180" rx="190" ry="180" fill="#e9dff4"/>
<polygon points="{flower}" fill="#bba0dd" transform="translate(270 70) rotate(-12 680 350)"/>
<circle cx="950" cy="420" r="140" fill="#e9dff4"/>
<path d="M1550 820q75-170 175-115t140 180" fill="none" stroke="#8fb9a3" stroke-width="60" stroke-linecap="round"/>
<circle cx="410" cy="950" r="82" fill="#f2cbaa"/>
</svg>\n'''
    (ROOT/"design/wallpaper.svg").write_text(wallpaper)
    (ROOT/"preview/assets/wallpaper.svg").write_text(wallpaper)
    print(f"Generated {len(icons)} original SVG symbols, wallpaper and shared tokens")


if __name__ == "__main__":
    generate()
