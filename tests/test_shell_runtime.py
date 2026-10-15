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
SECTIONS = ("network", "bluetooth", "display", "sound", "notifications", "style", "widgets", "input", "shortcuts", "apps", "power", "about")
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

    def test_caption_controls_act_on_the_focused_window(self):
        from qml_runtime.stubs import Process
        harness = Harness(width=1440, height=900)
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True)
        harness.load()
        harness.pump(1200)
        state = ('Windows.available = true; Windows.list = ['
                 '{address:"0xaa01", class:"firefox", title:"Docs", workspace:1, pid:1, recency:0, focused:true, '
                 'floating:false, maximized:false, minimized:false, monitor:0},'
                 '{address:"0xaa02", class:"foot", title:"~", workspace:1, pid:2, recency:1, focused:false, '
                 'floating:true, maximized:false, minimized:true, monitor:0}];')
        for symbol in ("minimize", "maximize", "close"):
            # The sandbox has no hyprctl, so the bridge's refresh empties the list; restore it each time.
            harness.eval(state)
            harness.wait_for(lambda: all(i.property("enabled") for i in harness.visible_items()
                                         if i.property("symbol") == "minimize"), 3000)
            button = next(i for i in harness.visible_items()
                          if i.property("symbol") == symbol and i.property("implicitWidth") == 32)
            Process.log.clear()
            harness.click(*harness.scene_pos(button))
            self.assertTrue(harness.wait_for(lambda: ["prismctl", "windows", symbol, "0xaa01"] in Process.log, 3000), symbol)
            harness.pump(600)
        self.assertEqual(harness.problems(), [])

    def test_default_widgets_show_and_search_hands_off_to_the_launcher(self):
        harness = self.boot()
        harness.pump(500)
        texts = [item.property("text") for item in harness.visible_items() if item.property("text")]
        import datetime
        self.assertTrue(any(str(datetime.date.today().year) in str(t) and len(str(t)) < 20 for t in texts), "calendar heading")
        field = next(item for item in harness.visible_items()
                     if "TextField" in item.metaObject().className() and item.property("placeholderText") == "Search apps, then the web")
        field.forceActiveFocus()
        field.setProperty("text", "firef")
        harness.pump(100)
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        QTest.keyClick(harness.view, Qt.Key_Return)
        harness.pump(900)
        launcher_field = next(item for item in harness.visible_items()
                              if "TextField" in item.metaObject().className() and item.property("placeholderText") == "Search apps")
        self.assertEqual(launcher_field.property("text"), "firef")
        labels = [item.property("text") for item in harness.visible_items() if item.property("text")]
        self.assertTrue(any("Search the web for" in str(label) for label in labels))
        self.assertEqual(harness.problems(), [])

    def test_widget_toggles_persist_and_hide_the_widget(self):
        from prismos import settings
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-widgets")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(800)
        self.assertEqual(harness.problems(), [])
        self.assertEqual(harness.truncated_texts(), [])
        row = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ToggleRow") and item.property("title") == "System")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        self.assertTrue(harness.wait_for(lambda: "system" in (settings.load()["widgets"] or []), 6000))
        harness.ipc("close")
        harness.pump(400)
        titles = [item.property("text") for item in harness.visible_items() if item.property("text")]
        self.assertIn("Processor", titles)

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

    # -- installer wizard ----------------------------------------------------
    def installer_session(self, runner_script, stdin_file):
        """Open the installer with the bridge calls replaced by canned, argv-only scripts."""
        import json
        harness = self.boot()
        py = sys.executable
        status = json.dumps({"ok": True, "live": True, "firmware": "uefi", "connectivity": "full", "online": True,
                             "battery": {"available": False}, "min_disk_label": "16 GB"})
        disks = json.dumps({"ok": True, "disks": [
            {"path": "/dev/nvme0n1", "name": "nvme0n1", "size": 5 * 10**11, "size_label": "500 GB", "model": "Test NVMe",
             "transport": "NVME", "removable": False, "eligible": True, "reason": "",
             "partitions": [{"path": "/dev/nvme0n1p1", "size_label": "100 MB", "fstype": "vfat", "label": "EFI"},
                            {"path": "/dev/nvme0n1p2", "size_label": "499 GB", "fstype": "ntfs", "label": "Windows"}]},
            {"path": "/dev/sda", "name": "sda", "size": 3 * 10**10, "size_label": "30 GB", "model": "Live USB", "transport": "USB",
             "removable": True, "eligible": False, "reason": "This is the USB you started from", "partitions": []}]})
        plan = json.dumps({"ok": True, "partitions": [{"name": "EFI system partition", "detail": "1 GB"},
                                                       {"name": "PrismOS", "detail": "rest"}]})
        for target, script in (("statusReader", "print(%r)" % status), ("diskReader", "print(%r)" % disks),
                               ("planner", "import sys; sys.stdin.read(); print(%r)" % plan),
                               ("runner", runner_script)):
            harness.eval("InstallerState.%s.command = %s" % (target, json.dumps([py, "-c", script.replace("STDIN_FILE", str(stdin_file))])))
        harness.eval("InstallerState.live = true")
        harness.ipc("installer")
        harness.pump(900)
        return harness

    def press(self, harness, label):
        button = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("PillButton") and item.property("text") == label)
        self.assertTrue(button.property("enabled"), f"{label} should be enabled")
        harness.click(*harness.scene_pos(button))
        harness.pump(500)

    def type_into(self, harness, placeholder, text):
        from PySide6.QtTest import QTest
        field = next(item for item in harness.visible_items()
                     if "TextField" in item.metaObject().className() and item.property("placeholderText") == placeholder)
        field.forceActiveFocus()
        for character in text:
            QTest.keyClick(harness.view, character)
        harness.pump(150)

    def click_row(self, harness, title):
        row = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ListRow") and str(item.property("title")).startswith(title))
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(300)

    def test_installer_wizard_collects_choices_and_sends_the_password_privately(self):
        import json
        import tempfile
        from qml_runtime import stubs
        record = Path(tempfile.mkdtemp()) / "request.json"
        self.addCleanup(lambda: record.parent.exists() and __import__("shutil").rmtree(record.parent))
        script = ("import sys, json\nraw = sys.stdin.read()\nopen('STDIN_FILE', 'w').write(raw)\n"
                  "for percent, phase, label in ((5, 'partition', 'Creating partitions'), (60, 'packages', 'Installing PrismOS')):\n"
                  "    print(json.dumps({'ok': True, 'phase': phase, 'label': label, 'percent': percent, 'detail': 'installing foo'}), flush=True)\n"
                  "print(json.dumps({'ok': True, 'phase': 'done', 'label': 'PrismOS is installed', 'percent': 100, 'done': True}), flush=True)\n")
        harness = self.installer_session(script, record)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertIn("Install PrismOS", texts())
        self.assertEqual(harness.problems(), [])
        self.press(harness, "Get started")
        self.assertIn("Language and region", texts())
        self.click_row(harness, "Português (Portugal)")
        self.click_row(harness, "Portuguese")
        self.assertEqual(harness.truncated_texts(), [])
        self.press(harness, "Continue")
        self.assertIn("You're online", texts())
        self.press(harness, "Continue")
        self.assertIn("Choose a disk", texts())
        sda = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ListRow") and str(item.property("title")).startswith("Live USB"))
        self.assertFalse(sda.property("enabled"))
        harness.click(*harness.scene_pos(sda))
        continue_button = next(item for item in harness.visible_items()
                               if item.metaObject().className().startswith("PillButton") and item.property("text") == "Continue")
        self.assertFalse(continue_button.property("enabled"), "an unusable disk can't be selected")
        self.click_row(harness, "Test NVMe")
        self.assertEqual(harness.truncated_texts(), [])
        self.press(harness, "Continue")
        self.assertIn("Create your account", texts())
        self.type_into(harness, "Alex Doe", "Alex Doe")
        username = next(item for item in harness.visible_items()
                        if "TextField" in item.metaObject().className() and item.property("placeholderText") == "alex")
        self.assertEqual(username.property("text"), "alexdoe")
        self.type_into(harness, "At least 8 characters", "tr0ub4dor&3")
        self.type_into(harness, "Type it again", "mismatch")
        self.assertIn("The passwords don't match", texts())
        continue_button = next(item for item in harness.visible_items()
                               if item.metaObject().className().startswith("PillButton") and item.property("text") == "Continue")
        self.assertFalse(continue_button.property("enabled"))
        repeat = next(item for item in harness.visible_items()
                      if "TextField" in item.metaObject().className() and item.property("placeholderText") == "Type it again")
        repeat.setProperty("text", "")
        self.type_into(harness, "Type it again", "tr0ub4dor&3")
        self.assertEqual(harness.truncated_texts(), [])
        self.press(harness, "Continue")
        self.assertIn("Ready to install", texts())
        self.assertTrue(harness.wait_for(lambda: "EFI system partition + PrismOS" in texts(), 4000))
        self.assertTrue(any("will be erased" in text for text in texts()))
        install = next(item for item in harness.visible_items()
                       if item.metaObject().className().startswith("PillButton") and item.property("text") == "Erase and install")
        self.assertFalse(install.property("enabled"), "typed confirmation is required")
        self.type_into(harness, "Type nvme0n1 to confirm", "wrong")
        self.assertFalse(install.property("enabled"))
        field = next(item for item in harness.visible_items()
                     if "TextField" in item.metaObject().className() and str(item.property("placeholderText")).startswith("Type nvme0n1"))
        field.setProperty("text", "")
        self.type_into(harness, "Type nvme0n1 to confirm", "nvme0n1")
        self.assertEqual(harness.truncated_texts(), [])
        self.press(harness, "Erase and install")
        self.assertTrue(harness.wait_for(lambda: "PrismOS is installed" in texts(), 8000))
        sent = json.loads(record.read_text())
        self.assertEqual((sent["disk"], sent["confirm"], sent["username"], sent["fullname"]), ("/dev/nvme0n1", "nvme0n1", "alexdoe", "Alex Doe"))
        self.assertEqual((sent["locale"], sent["keyboard"], sent["password"]), ("pt_PT.UTF-8", "pt", "tr0ub4dor&3"))
        self.assertFalse(any("tr0ub4dor" in " ".join(command) for command in stubs.Process.log), "the password must never be in argv")
        self.assertEqual(harness.problems(), [])

    def test_installer_failure_returns_to_the_review_without_losing_choices(self):
        import tempfile
        record = Path(tempfile.mkdtemp()) / "request.json"
        self.addCleanup(lambda: record.parent.exists() and __import__("shutil").rmtree(record.parent))
        script = ("import sys, json\nsys.stdin.read()\n"
                  "print(json.dumps({'ok': True, 'phase': 'partition', 'label': 'Creating partitions', 'percent': 4}), flush=True)\n"
                  "print(json.dumps({'ok': False, 'error': 'Formatting failed: no space'}), flush=True)\nsys.exit(1)\n")
        harness = self.installer_session(script, record)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        for label in ("Get started", "Continue", "Continue"):
            self.press(harness, label)
        self.click_row(harness, "Test NVMe")
        self.press(harness, "Continue")
        self.type_into(harness, "Alex Doe", "Sam")
        self.type_into(harness, "At least 8 characters", "longenough1")
        self.type_into(harness, "Type it again", "longenough1")
        self.press(harness, "Continue")
        harness.wait_for(lambda: "EFI system partition + PrismOS" in texts(), 4000)
        self.type_into(harness, "Type nvme0n1 to confirm", "nvme0n1")
        self.press(harness, "Erase and install")
        self.assertTrue(harness.wait_for(lambda: "The installation didn't finish" in texts(), 8000))
        self.assertIn("Formatting failed: no space", texts())
        self.assertEqual(harness.truncated_texts(), [])
        self.press(harness, "Back")
        self.assertIn("Ready to install", texts())
        field = next(item for item in harness.visible_items()
                     if "TextField" in item.metaObject().className() and str(item.property("placeholderText")).startswith("Type nvme0n1"))
        self.assertEqual(field.property("text"), "", "the confirmation must be typed again")
        self.assertEqual(harness.problems(), [])

    def test_installer_is_refused_off_the_live_usb(self):
        harness = self.boot()
        harness.ipc("installer")
        harness.pump(400)
        texts = {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertIn("Installing is only available from the PrismOS live USB", texts)
        self.assertNotIn("Install PrismOS", texts)

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
