import re
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config/hypr/hyprlock.conf"
BLOCKS = {"general", "background", "label", "input-field"}


class LockScreenConfigTests(unittest.TestCase):
    def blocks(self):
        found, current = [], None
        for number, raw in enumerate(CONFIG.read_text().splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("{"):
                self.assertIsNone(current, f"nested block at line {number}")
                current = {"name": line[:-1].strip(), "values": {}}
            elif line == "}":
                self.assertIsNotNone(current, f"stray brace at line {number}")
                found.append(current)
                current = None
            else:
                self.assertIsNotNone(current, f"setting outside a block at line {number}")
                key, _, value = line.partition("=")
                self.assertTrue(value.strip() or key.strip() == "monitor", f"empty value at line {number}")
                current["values"][key.strip()] = value.strip()
        self.assertIsNone(current, "unterminated block")
        return found

    def test_structure_uses_only_documented_blocks(self):
        names = [block["name"] for block in self.blocks()]
        self.assertTrue(set(names) <= BLOCKS, names)
        for needed in ("general", "background", "input-field"):
            self.assertIn(needed, names)
        self.assertGreaterEqual(names.count("label"), 4)

    def test_colors_are_material_dark_roles(self):
        for block in self.blocks():
            for key, value in block["values"].items():
                if key.endswith("color"):
                    self.assertRegex(value, r"rgb\([0-9a-f]{6}\)", key)

    def test_label_commands_never_read_untrusted_input(self):
        for block in self.blocks():
            text = block["values"].get("text", "")
            if text.startswith("cmd["):
                self.assertNotRegex(text, r"\$\{?(?!USER)[A-Z_]+\}?|`|eval|curl|wget|\|\s*sh", text)

    def test_password_field_is_centered_and_visible_on_empty(self):
        field = next(block for block in self.blocks() if block["name"] == "input-field")["values"]
        self.assertEqual(field["fade_on_empty"], "false")
        self.assertEqual((field["halign"], field["valign"]), ("center", "center"))


if __name__ == "__main__":
    unittest.main()
