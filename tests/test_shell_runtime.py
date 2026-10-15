"""Load the real shell QML under Qt Quick with stub Quickshell modules.

Needs PySide6 (>= 6.8) and EGL libraries; skipped otherwise. This catches QML
reference/binding errors and layout regressions without a compositor. It does
not qualify Quickshell, layer-shell focus, Hyprland or hardware.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

    def test_theme_ink_roles_resolve_to_scheme_values(self):
        """Regression: properties named `onX` next to `x` silently stayed black."""
        harness = self.boot()
        harness.pump(1500)
        harness.eval('console.log("INK", [Theme.primaryInk, Theme.surfaceInk, Theme.surfaceVariantInk, '
                     'Theme.errorInk, Theme.inverseSurfaceInk].join(" "))')
        from prismos import theme
        scheme = theme.palette("#8469cf", False)
        expected = " ".join(scheme[name] for name in ("onPrimary", "onSurface", "onSurfaceVariant", "onError", "inverseOnSurface"))
        self.assertIn("INK " + expected, harness.messages)

    def test_no_text_is_elided_on_any_surface(self):
        harness = self.boot()
        self.assertEqual(harness.truncated_texts(), [], "desktop")
        for surface in SURFACES:
            with self.subTest(surface=surface):
                harness.ipc(surface)
                harness.pump(600)
                self.assertEqual(harness.truncated_texts(), [], surface)
                harness.ipc("close")
                harness.pump(200)

    def test_dock_is_sized_to_its_content(self):
        harness = self.boot()
        dock = next(w for w in harness.visible_items() if w.metaObject().className().startswith("QQuickFlickable")
                    and w.property("contentWidth") and w.parentItem().height() == 76)
        self.assertLessEqual(dock.property("contentWidth"), dock.width() + 0.5,
                             "dock buttons would be clipped")

    def test_notifications_are_grouped_and_dismissible(self):
        from qml_runtime import stubs
        harness = self.boot()
        server = stubs.NotificationServer.instances[0]
        first = server.post(appName="Messages", summary="Ava", body="Lunch?")
        server.post(appName="Messages", summary="Noah", body="Photo")
        server.post(appName="Calendar", summary="Review")
        harness.ipc("shade")
        harness.pump(600)
        self.assertEqual(len(server.tracked.values), 3)
        texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
        self.assertIn("Messages · 2", texts)
        self.assertIn("Review", texts)
        first.dismiss()
        harness.pump(300)
        self.assertEqual(len(server.tracked.values), 2)
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
