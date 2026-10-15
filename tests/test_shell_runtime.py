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

SURFACES = ("shade", "launcher", "settings", "files", "store", "power", "recents")
SECTIONS = ("network", "bluetooth", "display", "sound", "notifications", "style", "input", "shortcuts", "apps", "power", "about")
WINDOWS = ('Windows.available = true; Windows.list = ['
           '{address:"0xaa01", class:"firefox", title:"Docs", workspace:1, pid:1, recency:0, focused:true, hidden:false},'
           '{address:"0xaa02", class:"foot", title:"~/code", workspace:2, pid:2, recency:1, focused:false, hidden:false}];')


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

    def test_every_settings_page_loads_and_fits(self):
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(700)
        for section in SECTIONS:
            with self.subTest(section=section):
                row = harness.find("section-" + section)
                self.assertIsNotNone(row, f"no row for {section}")
                harness.reveal(row)
                harness.click(*harness.scene_pos(row))
                harness.pump(500)
                self.assertEqual(harness.problems(), [], section)
                self.assertEqual(harness.truncated_texts(), [], section)
        harness.ipc("close")

    def test_settings_search_filters_sections(self):
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(600)
        self.assertIsNotNone(harness.find("section-about"))
        field = next(item for item in harness.visible_items() if item.property("placeholderText") == "Search settings")
        field.setProperty("text", "bluetooth")
        harness.pump(300)
        self.assertIsNotNone(harness.find("section-bluetooth"))
        self.assertTrue(harness.find("section-about") is None or not harness.find("section-about").isVisible())

    def test_recents_lists_open_windows_most_recent_first(self):
        harness = self.boot()
        harness.eval(WINDOWS)
        harness.ipc("recents")
        harness.pump(500)
        harness.eval(WINDOWS)
        texts = [item.property("text") for item in harness.visible_items() if item.property("text")]
        self.assertIn("Workspace 1", texts)
        self.assertIn("Workspace 2", texts)
        self.assertIn("Close all", texts)
        self.assertLess(texts.index("Docs"), texts.index("~/code"))

    def test_heads_up_respects_do_not_disturb_but_not_critical(self):
        from qml_runtime import stubs
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, dnd=True)
        harness.load()
        harness.pump(1800)
        server = stubs.NotificationServer.instances[0]
        server.post(appName="Chat", summary="Quiet one")
        harness.pump(300)
        texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
        self.assertNotIn("Quiet one", texts)
        server.post(appName="System", summary="Disk almost full", urgency=2)
        harness.pump(500)
        texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
        self.assertIn("Disk almost full", texts)

    def test_first_run_wizard_completes_through_the_bridge(self):
        harness = self.boot(onboarded=False)

        def press(label):
            button = next(item for item in harness.visible_items()
                          if item.metaObject().className().startswith("PillButton") and item.property("text") == label)
            harness.click(*harness.scene_pos(button))
            harness.pump(300)
        press("Continue")
        press("Continue")
        press("Enter PrismOS")
        self.assertTrue(harness.wait_for(lambda: harness.truncated_texts() is not None and not any(
            item.property("text") == "Welcome to PrismOS" for item in harness.visible_items()), 6000))
        from prismos import settings
        self.assertTrue(settings.load()["onboarding_complete"])
        self.assertEqual(harness.problems(), [])

    def test_dark_theme_text_stays_legible(self):
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, dark=True)
        harness.load()
        harness.pump(2500)
        harness.eval('console.log("LUMA", Theme.surface.hslLightness, Theme.surfaceInk.hslLightness)')
        line = next(m for m in harness.messages if m.startswith("LUMA"))
        surface, ink = (float(v) for v in line.split()[1:])
        self.assertLess(surface, 0.2)
        self.assertGreater(ink, 0.7)

    def test_native_smoke_fixture_passes_under_stub_modules(self):
        """The same fixture CI runs against real Quickshell: drag-safe sound refresh,
        private stdin pipe, launch readiness, favorites, media and notifications."""
        harness = Harness()
        self.addCleanup(harness.close)
        harness.add_desktop_entry("fixture.desktop", "Fixture")
        harness.write_settings(favorites=["fixture.desktop"], reduced_motion=True, onboarding_complete=True)
        fixture = harness.shell_dir / "smoke_stub.qml"
        source = (Path(__file__).resolve().parent / "native-smoke.qml").read_text()
        fixture.write_text(source.replace('"../shell/components"', '"components"').replace('"../shell/services"', '"services"'))
        self.addCleanup(fixture.unlink)
        harness.load("smoke_stub.qml")
        harness.wait_for(lambda: any("PRISM_NATIVE_SMOKE" in m for m in harness.messages), 20000)
        verdicts = [m for m in harness.messages if "PRISM_NATIVE_SMOKE" in m]
        self.assertEqual(verdicts, ["PRISM_NATIVE_SMOKE_OK"])

    def test_choosing_a_wallpaper_sets_the_picture_and_recolors_the_shell(self):
        import tempfile
        from PIL import Image
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        folder = Path(home.name) / "Pictures" / "Wallpapers"
        folder.mkdir(parents=True)
        Image.new("RGB", (320, 180), (71, 132, 106)).save(folder / "Forest.png")
        harness = Harness(files_home=home.name)
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True)
        harness.load()
        harness.pump(1500)
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-style")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        self.assertTrue(harness.wait_for(lambda: any(
            i.metaObject().className().startswith("PaperTile") and i.property("title") == "Forest"
            for i in harness.visible_items()), 6000))
        tile = next(i for i in harness.visible_items()
                    if i.metaObject().className().startswith("PaperTile") and i.property("title") == "Forest")
        harness.click(*harness.scene_pos(tile))
        from prismos import settings
        self.assertTrue(harness.wait_for(lambda: settings.load()["wallpaper"].endswith("Forest.png"), 6000))
        self.assertEqual(settings.load()["seed"], "#47846a")
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
