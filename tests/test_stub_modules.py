import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class StubModuleTests(unittest.TestCase):
    """The runtime harness must shadow every Quickshell module the shell imports.

    On a machine with the real Quickshell installed (CI), a module without a stub
    qmldir resolves to the system copy, whose plugin cannot load under the test's Qt."""

    def imports(self):
        found = set()
        for path in (ROOT / "shell").rglob("*.qml"):
            found.update(re.findall(r"^import (Quickshell[\w.]*)", path.read_text(), re.M))
        return found

    def test_every_imported_quickshell_module_has_a_pluginless_stub(self):
        modules = self.imports()
        self.assertIn("Quickshell.Io", modules)
        for module in sorted(modules):
            qmldir = ROOT / "tests/qmlstubs" / module.replace(".", "/") / "qmldir"
            self.assertTrue(qmldir.is_file(), f"missing stub qmldir for {module}")
            text = qmldir.read_text()
            self.assertIn(f"module {module}", text)
            self.assertNotRegex(text, r"(?m)^(optional )?plugin\b", f"{module} stub must not name a plugin")


if __name__ == "__main__":
    unittest.main()
