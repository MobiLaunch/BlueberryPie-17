import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("generate_design", ROOT / "scripts/generate-design.py")
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)

IDENT = re.compile(r'"([a-z][a-z0-9_]*)"')


def generated():
    text = (ROOT / "shell/components/IconData.js").read_text()
    tables = {}
    for name in ("outline", "filled"):
        body = re.search(rf"var {name} = (\{{.*?\n\}});", text, re.S).group(1)
        tables[name] = json.loads(body)
    return tables


def symbol_blocks(source):
    """The text of every `Symbol { ... }` block, found by matching braces."""
    for match in re.finditer(r"\bSymbol\s*\{", source):
        depth, index = 1, match.end()
        while depth and index < len(source):
            depth += {"{": 1, "}": -1}.get(source[index], 0)
            index += 1
        yield source[match.end():index]


def used_names():
    names = {}
    for path in sorted((ROOT / "shell").rglob("*.qml")):
        source = path.read_text()
        lines = [(m.group(1), "symbol") for m in re.finditer(r"\b(?:symbol|iconName)\s*:\s*([^\n]+)", source)]
        for block in symbol_blocks(source):
            lines += [(m.group(1), "name") for m in re.finditer(r"\bname\s*:\s*([^\n]+)", block)]
        for expression, _ in lines:
            # Strings compared with === are conditions, not icon names.
            expression = re.sub(r'[=!]==?\s*"[^"]*"', "", expression)
            for token in IDENT.findall(expression):
                names.setdefault(token, set()).add(path.name)
    return names


class IconSetTests(unittest.TestCase):
    def test_generated_data_matches_the_vendored_svgs(self):
        outline, filled = generator.load_icons()
        tables = generated()
        self.assertEqual(tables["outline"], outline)
        self.assertEqual(tables["filled"], filled)

    def test_every_symbol_used_by_the_shell_exists(self):
        known = set(generated()["outline"])
        missing = {name: sorted(files) for name, files in used_names().items() if name not in known}
        # Words that only look like icon names (modes, roles) are not Symbols.
        ignored = {"filled", "tonal", "neutral", "text", "outlined", "yes", "no"}
        missing = {name: files for name, files in missing.items() if name not in ignored}
        self.assertEqual(missing, {}, "icon names used in QML but not in design/icons/material-map.json")

    def test_a_good_share_of_the_icon_set_is_used(self):
        used = set(used_names())
        unused = set(generated()["outline"]) - used
        self.assertLess(len(unused), 40, sorted(unused))

    def test_vendored_icons_are_single_path_and_licensed(self):
        material = ROOT / "design/icons/material"
        self.assertIn("Apache License", (material / "LICENSE").read_text())
        notice = (ROOT / "design/icons/NOTICE.md").read_text()
        self.assertIn("Apache License, Version 2.0", notice)
        files = list(material.glob("*.svg"))
        self.assertGreater(len(files), 100)
        for path in files:
            self.assertEqual(len(generator.PATH.findall(path.read_text())), 1, path.name)

    def test_every_mapped_symbol_has_an_outlined_and_a_filled_variant(self):
        material = ROOT / "design/icons/material"
        mapping = json.loads((ROOT / "design/icons/material-map.json").read_text())
        for name, symbol in mapping.items():
            for suffix in ("", "-fill"):
                self.assertTrue((material / f"{symbol}{suffix}.svg").exists(), f"{name}: {symbol}{suffix}.svg")

    def test_battery_has_a_glyph_for_every_charge_level(self):
        names = set(generated()["outline"])
        for level in range(7):
            self.assertIn(f"battery_level_{level}", names)
        for name in ("battery", "battery_charging"):
            self.assertIn(name, names)


class AppIconThemeTests(unittest.TestCase):
    def run_wrapper(self, with_theme, **extra):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "bin").mkdir()
            fake = root / "bin/qs"
            fake.write_text('#!/bin/sh\necho "theme=${QS_ICON_THEME-unset}"\n')
            fake.chmod(0o755)
            icons = root / "icons"
            (icons / ("Papirus" if with_theme else "Adwaita")).mkdir(parents=True)
            env = {**os.environ, "PATH": f"{root / 'bin'}:{os.environ['PATH']}", "PRISM_ICON_ROOT": str(icons), **extra}
            env.pop("QS_ICON_THEME", None)
            env.update(extra)
            return subprocess.run(["bash", str(ROOT / "bin/prism-shell")], env=env, capture_output=True, text=True, timeout=10)

    def test_papirus_is_used_when_installed(self):
        self.assertEqual(self.run_wrapper(True).stdout.strip(), "theme=Papirus")

    def test_the_system_theme_is_left_alone_without_papirus(self):
        self.assertEqual(self.run_wrapper(False).stdout.strip(), "theme=unset")

    def test_an_explicit_theme_wins(self):
        self.assertEqual(self.run_wrapper(True, QS_ICON_THEME="Adwaita").stdout.strip(), "theme=Adwaita")

    def test_the_icon_theme_is_a_package_dependency(self):
        self.assertIn("'papirus-icon-theme'", (ROOT / "packaging/arch/PKGBUILD").read_text())
        packages = (ROOT / "archiso/packages.x86_64").read_text().split()
        self.assertIn("papirus-icon-theme", packages)

    def test_no_app_icon_falls_back_to_the_generic_executable_art(self):
        for path in (ROOT / "shell").rglob("*.qml"):
            self.assertNotIn("application-x-executable", path.read_text(), path.name)


if __name__ == "__main__":
    unittest.main()
