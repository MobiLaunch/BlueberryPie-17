"""Load the real shell QML under Qt Quick with stub Quickshell modules.

Needs PySide6 (>= 6.8) and EGL libraries; skipped otherwise. This catches QML
reference/binding errors and layout regressions without a compositor. It does
not qualify Quickshell, layer-shell focus, Hyprland or hardware.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from qml_runtime.harness import Harness
except ImportError as error:  # PySide6 or its system libraries are absent
    Harness = None
    SKIP_REASON = f"PySide6 runtime unavailable: {error}"
else:
    SKIP_REASON = ""

SURFACES = ("shade", "launcher", "settings", "files", "store", "power")


@unittest.skipIf(Harness is None, SKIP_REASON)
class ShellRuntimeTests(unittest.TestCase):
    def boot(self, onboarded=True):
        harness = Harness()
        self.addCleanup(harness.close)
        for name, title in (("firefox", "Firefox"), ("thunar", "Files"), ("foot", "Foot")):
            harness.add_desktop_entry(f"{name}.desktop", title, icon=name)
        if onboarded:
            harness.write_settings(onboarding_complete=True,
                                   favorites=["firefox.desktop", "thunar.desktop", "foot.desktop"])
        harness.load()
        harness.pump(1500)
        return harness

    def test_shell_loads_without_qml_errors(self):
        harness = self.boot()
        self.assertEqual(harness.problems(), [])

    def test_first_run_opens_and_loads_cleanly(self):
        harness = self.boot(onboarded=False)
        self.assertEqual(harness.problems(), [])

    def test_every_surface_opens_without_qml_errors(self):
        harness = self.boot()
        for surface in SURFACES:
            with self.subTest(surface=surface):
                harness.ipc(surface)
                harness.pump(500)
                harness.ipc("close")
                harness.pump(200)
        self.assertEqual(harness.problems(), [])


if __name__ == "__main__":
    unittest.main()
