"""Load the real shell QML under Qt Quick with stub Quickshell modules.

Needs PySide6 (>= 6.8) and EGL libraries; skipped otherwise. This catches QML
reference/binding errors and layout regressions without a compositor. It does
not qualify Quickshell, layer-shell focus, Hyprland or hardware.
"""
import json
import re
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

SURFACES = ("shade", "launcher", "settings", "files", "store", "power", "recents", "calculator", "clock", "alarms", "converter", "clipboard", "worldclock")
SECTIONS = ("network", "bluetooth", "display", "sound", "notifications", "style", "widgets", "datetime", "input", "shortcuts", "apps", "power", "storage", "about")
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

    def test_largest_text_size_keeps_every_surface_and_section_readable(self):
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, font_scale=1.3)
        harness.load()
        harness.pump(1500)
        for surface in SURFACES:
            harness.ipc(surface)
            harness.pump(500)
            self.assertEqual(harness.problems(), [], surface)
            self.assertEqual(harness.truncated_texts(), [], surface)
            harness.ipc("close")
            harness.pump(250)
        harness.ipc("settings")
        harness.pump(700)
        for section in SECTIONS:
            with self.subTest(section=section):
                row = harness.find("section-" + section)
                harness.reveal(row)
                harness.click(*harness.scene_pos(row))
                harness.pump(500)
                self.assertEqual(harness.problems(), [], section)
                self.assertEqual(harness.truncated_texts(), [], section)

    def test_color_scheme_and_text_size_change_through_the_bridge(self):
        from prismos import settings
        harness = self.boot()
        before = harness.eval_value("Theme.primary.toString() + '|' + Theme.type.bodyMedium.size")
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-style")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(600)
        pick = next(item for item in harness.visible_items()
                    if item.metaObject().className().startswith("ListRow") and item.property("title") == "Monochrome")
        harness.reveal(pick)
        harness.click(*harness.scene_pos(pick))
        self.assertTrue(harness.wait_for(lambda: settings.load()["scheme"] == "monochrome", 6000))
        chip = next(item for item in harness.visible_items()
                    if item.metaObject().className().startswith("FilterChip") and item.property("text") == "Largest")
        harness.reveal(chip)
        harness.click(*harness.scene_pos(chip))
        self.assertTrue(harness.wait_for(lambda: settings.load()["font_scale"] == 1.3, 6000))
        harness.pump(900)
        after = harness.eval_value("Theme.primary.toString() + '|' + Theme.type.bodyMedium.size")
        self.assertNotEqual(before.split("|")[0], after.split("|")[0])
        self.assertEqual(after.split("|")[1], "18")
        self.assertEqual(harness.problems(), [])

    def test_quick_settings_tiles_can_be_added_reordered_and_used(self):
        from prismos import settings
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("shade")
        harness.pump(600)
        edit = next(item for item in harness.visible_items() if item.property("symbol") == "edit")
        harness.click(*harness.scene_pos(edit))
        harness.pump(500)
        self.assertEqual(harness.problems(), [])
        self.assertEqual(harness.truncated_texts(), [])

        def toggle_for(title):
            return next(row for row in harness.visible_items()
                        if row.metaObject().className().startswith("ListRow") and row.property("title") == title)

        def chevron(symbol):
            return next((item for item in harness.visible_items(toggle_for("Screenshot")) if item.property("symbol") == symbol), None)
        row = toggle_for("Screenshot")
        harness.reveal(row)
        switch = next(item for item in harness.visible_items(row) if item.metaObject().className().startswith("AndroidToggle"))
        harness.click(*harness.scene_pos(switch))
        self.assertTrue(harness.wait_for(lambda: "screenshot" in (settings.load()["tiles"] or []), 6000))
        self.assertTrue(harness.wait_for(lambda: chevron("chevron_up") is not None, 6000))
        settled = lambda: harness.eval_value("!SystemBridge.busy && SystemBridge.pending.length === 0 && !SystemBridge.staleRead") == "true"
        self.assertTrue(harness.wait_for(settled, 8000))  # the editor has finished re-laying out
        harness.reveal(chevron("chevron_up"))
        harness.click(*harness.scene_pos(chevron("chevron_up")))
        self.assertTrue(harness.wait_for(lambda: settings.load()["tiles"][-2:] == ["screenshot", "audio_devices"], 6000))
        self.assertTrue(harness.wait_for(settled, 8000))
        done = next(item for item in harness.visible_items()
                    if item.metaObject().className().startswith("PillButton") and item.property("text") == "Done")
        harness.reveal(done)
        harness.click(*harness.scene_pos(done))
        find_tile = lambda: next((item for item in harness.visible_items()
                                  if item.metaObject().className().startswith("QuickTile") and item.property("title") == "Screenshot"), None)
        self.assertTrue(harness.wait_for(lambda: find_tile() is not None, 8000))
        shot = find_tile()
        Process.log.clear()
        harness.click(*harness.scene_pos(shot))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "screenshot", "area"] in Process.log, 4000))
        self.assertEqual(harness.problems(), [])

    def test_muted_apps_are_dropped_but_critical_alerts_get_through(self):
        from qml_runtime import stubs
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, muted_apps=["Chat"])
        harness.load()
        harness.pump(1800)
        server = stubs.NotificationServer.instances[0]
        server.post(appName="Chat", summary="Muted hello")
        server.post(appName="Mail", summary="Visible hello")
        harness.pump(400)
        texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
        self.assertNotIn("Muted hello", texts)
        self.assertIn("Visible hello", texts)
        server.post(appName="Chat", summary="Chat fire alarm", urgency=2)
        harness.pump(500)
        texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
        self.assertIn("Chat fire alarm", texts)

    def test_notification_settings_list_apps_and_mute_through_the_bridge(self):
        from prismos import settings
        from qml_runtime import stubs
        harness = self.boot()
        server = stubs.NotificationServer.instances[0]
        server.post(appName="Chat", summary="hello")
        harness.pump(300)
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-notifications")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(600)
        app = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ToggleRow") and item.property("title") == "Chat")
        harness.reveal(app)
        harness.click(*harness.scene_pos(app))
        self.assertTrue(harness.wait_for(lambda: settings.load()["muted_apps"] == ["Chat"], 6000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_notification_history_is_opt_in_in_memory_and_clearable(self):
        from prismos import settings
        from qml_runtime import stubs
        harness = self.boot()
        server = stubs.NotificationServer.instances[0]
        history = lambda: json.loads(harness.eval_value("JSON.stringify(Notifications.history.map(e => [e.app, e.summary, e.critical]))"))
        server.post(appName="Chat", summary="before opting in")
        harness.pump(200)
        self.assertEqual(history(), [])
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-notifications")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(600)
        toggle = harness.find("history-toggle")
        harness.reveal(toggle)
        harness.click(*harness.scene_pos(toggle))
        self.assertTrue(harness.wait_for(lambda: settings.load()["notification_history"] is True, 6000))
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("Notifications.historyEnabled") == "true", 6000))
        server.post(appName="Chat", summary="hello", body="line one\nline two")
        server.post(appName="Alarm", summary="Wake up", urgency=2)
        harness.pump(300)
        self.assertEqual(history(), [["Alarm", "Wake up", True], ["Chat", "hello", False]])
        self.assertTrue(harness.wait_for(lambda: len([i for i in harness.visible_items() if i.objectName() == "history-item"]) == 2, 4000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])
        # Muted apps are dropped before they reach the history.
        settings.update(muted_apps=["Spam"])
        harness.eval("SystemBridge.refresh()")
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("Notifications.isMuted('Spam')") == "true", 6000))
        server.post(appName="Spam", summary="buy now")
        harness.pump(200)
        self.assertEqual(len(history()), 2)
        # Long text is bounded and the list never grows past its limit.
        server.post(appName="Chat", summary="x" * 500, body="y" * 900)
        for index in range(110):
            server.post(appName="Bulk", summary=f"n{index}")
        harness.pump(500)
        self.assertEqual(harness.eval_value("Notifications.history.length"), "100")
        self.assertEqual(harness.eval_value("Notifications.history[0].summary"), "n109")
        # Clear history, then turn it off: nothing is kept.
        clear = harness.find("history-clear")
        harness.reveal(clear)
        harness.click(*harness.scene_pos(clear))
        harness.pump(300)
        self.assertEqual(harness.eval_value("Notifications.history.length"), "0")
        server.post(appName="Chat", summary="again")
        harness.pump(200)
        self.assertEqual(harness.eval_value("Notifications.history.length"), "1")
        toggle = harness.find("history-toggle")
        harness.reveal(toggle)
        harness.click(*harness.scene_pos(toggle))
        self.assertTrue(harness.wait_for(lambda: settings.load()["notification_history"] is False, 6000))
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("Notifications.history.length") == "0", 6000))

    def test_calculator_types_evaluates_and_rejects_bad_input(self):
        from PySide6.QtTest import QTest
        harness = self.boot()
        harness.ipc("calculator")
        harness.pump(500)
        field = next(item for item in harness.visible_items()
                     if "TextField" in item.metaObject().className() and item.property("placeholderText") == "0")
        self.assertTrue(field.property("activeFocus"), "the expression field takes focus")
        for character in "2+3*4":
            QTest.keyClick(harness.view, character)
        harness.pump(150)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertIn("= 14", texts())

        def key(label):
            button = next(item for item in harness.visible_items()
                          if item.metaObject().className().startswith(("PillButton", "FilterChip")) and item.property("text") == label)
            harness.click(*harness.scene_pos(button))
            harness.pump(120)
        key("=")
        self.assertEqual(field.property("text"), "14")
        key("÷"); key("0"); key("=")
        self.assertIn("Can't divide by zero", texts())
        key("C")
        for character in "process.exit()":
            QTest.keyClick(harness.view, character)
        key("=")
        self.assertTrue(any(word in text for text in texts() for word in ("Unknown", "Unexpected", "Check the number")))
        key("C")
        key("Scientific")
        key("√"); key("9"); key("( )")
        harness.pump(150)
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_timer_counts_down_and_announces_and_stopwatch_laps(self):
        harness = self.boot()
        harness.ipc("clock")
        harness.pump(500)
        harness.eval("ClockState.setTimer(1)")
        start = next(item for item in harness.visible_items()
                     if item.metaObject().className().startswith("PillButton") and item.property("text") == "Start")
        harness.click(*harness.scene_pos(start))
        harness.pump(300)
        self.assertEqual(harness.eval_value("ClockState.timerRunning"), "true")
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("ClockState.timerFinished") == "true", 4000))
        self.assertEqual(harness.eval_value("ClockState.ringing.kind"), "timer")
        harness.eval("ClockState.startWatch(); ClockState.lap(); ClockState.lap()")
        harness.pump(200)
        self.assertEqual(harness.eval_value("ClockState.laps.length"), "2")
        harness.eval("ClockState.stopWatch()")
        elapsed = float(harness.eval_value("ClockState.watchElapsed"))
        harness.pump(200)
        self.assertEqual(float(harness.eval_value("ClockState.watchElapsed")), elapsed)
        self.assertEqual(harness.eval_value("ClockState.clock(61000, false)"), "1:01")
        self.assertEqual(harness.eval_value("ClockState.clock(3725120, true)"), "1:02:05.12")
        self.assertEqual(harness.problems(), [])

    def test_alarm_rings_once_with_sound_and_can_be_added_in_the_panel(self):
        import datetime
        from prismos import settings
        from qml_runtime.stubs import Process
        import time
        if datetime.datetime.now().second > 52:  # never straddle a minute boundary
            time.sleep(9)
        now = datetime.datetime.now()
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, alarms=[
            {"id": 1, "time": now.strftime("%H:%M"), "days": [], "label": "Test", "enabled": True}])
        Process.log.clear()
        harness.load()
        harness.pump(1800)
        self.assertEqual(harness.eval_value("ClockState.ringing.title"), "Test")
        self.assertIn(["prismctl", "sound", "alarm"], Process.log)
        self.assertTrue(harness.wait_for(lambda: settings.load()["alarms"][0]["enabled"] is False, 6000),
                        "a one-time alarm switches itself off")
        harness.ipc("alarms")
        harness.pump(500)
        add = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("PillButton") and item.property("text") == "Add alarm")
        harness.click(*harness.scene_pos(add))
        self.assertTrue(harness.wait_for(lambda: len(settings.load()["alarms"]) == 2, 6000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_quiet_hours_silence_banners_until_the_window_ends(self):
        import datetime
        from qml_runtime import stubs
        now = datetime.datetime.now()
        around = lambda hours: (now + datetime.timedelta(hours=hours)).strftime("%H:%M")
        for label, schedule, expect_banner in (
                ("inside", {"enabled": True, "start": around(-1), "end": around(1)}, False),
                ("outside", {"enabled": True, "start": around(1), "end": around(2)}, True),
                ("disabled", {"enabled": False, "start": around(-1), "end": around(1)}, True)):
            with self.subTest(label):
                harness = Harness()
                self.addCleanup(harness.close)
                harness.write_settings(onboarding_complete=True, dnd_schedule=schedule)
                harness.load()
                harness.pump(1800)
                server = stubs.NotificationServer.instances[-1]
                server.post(appName="Chat", summary="Hello " + label)
                harness.pump(400)
                texts = {item.property("text") for item in harness.visible_items() if item.property("text")}
                self.assertEqual("Hello " + label in texts, expect_banner)
                self.assertEqual(harness.eval_value("Notifications.quiet"), "false" if expect_banner else "true")
                self.assertEqual(harness.problems(), [])

    def test_quiet_hours_settings_edit_through_the_bridge(self):
        from prismos import settings
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-notifications")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(600)
        toggle = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("ToggleRow") and item.property("title") == "Turn on automatically")
        harness.reveal(toggle)
        harness.click(*harness.scene_pos(toggle))
        self.assertTrue(harness.wait_for(lambda: settings.load()["dnd_schedule"]["enabled"] is True, 6000))
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("Notifications.schedule.enabled") == "true", 6000))
        harness.pump(500)
        up = min((item for item in harness.visible_items() if item.property("symbol") == "chevron_up"),
                 key=lambda item: harness.scene_pos(item)[0])  # the From hour stepper
        harness.reveal(up)
        harness.click(*harness.scene_pos(up))
        self.assertTrue(harness.wait_for(lambda: settings.load()["dnd_schedule"]["start"] == "23:00", 6000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_converter_converts_and_swaps(self):
        harness = self.boot()
        harness.ipc("converter")
        harness.pump(500)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertIn("3.2808399 ft", texts())
        chip = next(item for item in harness.visible_items()
                    if item.metaObject().className().startswith("FilterChip") and item.property("text") == "Temperature")
        harness.click(*harness.scene_pos(chip))
        harness.pump(300)
        self.assertIn("33.8 °F", texts())
        swap = next(item for item in harness.visible_items() if item.property("symbol") == "arrow" and item.rotation() == 90)
        harness.click(*harness.scene_pos(swap))
        harness.pump(300)
        self.assertEqual(harness.eval_value("1"), "1")  # layout settled
        self.assertIn("1 °C", texts())
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_clipboard_history_is_opt_in_and_copies_by_numeric_id(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("clipboard")
        harness.pump(700)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertTrue(any("cliphist" in text for text in texts()), "explains the missing tool instead of failing")
        harness.eval('ClipboardState.available = true; ClipboardState.enabled = true; ClipboardState.items = ['
                     '{id:"12", kind:"text", preview:"hello world"}, {id:"11", kind:"image", preview:"Image"}]')
        harness.pump(300)
        row = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ListRow") and item.property("title") == "hello world")
        Process.log.clear()
        harness.click(*harness.scene_pos(row))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "clipboard", "copy", "12"] in Process.log, 3000))
        self.assertEqual(harness.truncated_texts(), [])

    def test_twelve_hour_clock_setting_changes_every_clock(self):
        import re
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, clock_24h=False)
        harness.load()
        harness.pump(1600)
        texts = [str(item.property("text")) for item in harness.visible_items() if item.property("text")]
        times = [text for text in texts if re.fullmatch(r"\d{1,2}:\d{2}( [AP]M)?", text)]
        self.assertTrue(times and all(text.endswith(("AM", "PM")) for text in times), times)
        self.assertEqual(harness.truncated_texts(), [])

    def test_date_time_page_toggles_clock_format_through_the_bridge(self):
        from prismos import settings
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-datetime")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(800)
        toggle = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("ToggleRow") and item.property("title") == "24-hour clock")
        harness.reveal(toggle)
        harness.click(*harness.scene_pos(toggle))
        self.assertTrue(harness.wait_for(lambda: settings.load()["clock_24h"] is False, 6000))
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("Theme.clock24") == "false", 6000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_keyboard_layout_choice_goes_to_the_bridge(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-input")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        self.assertTrue(harness.wait_for(lambda: any(
            item.metaObject().className().startswith("ListRow") and item.property("title") == "German"
            for item in harness.visible_items()), 6000))
        german = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("ListRow") and item.property("title") == "German")
        harness.reveal(german)
        Process.log.clear()
        harness.click(*harness.scene_pos(german))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "input", "set", "keyboard", "de"] in Process.log, 4000))
        self.assertEqual(harness.truncated_texts(), [])

    def test_ringing_banner_can_snooze_and_ring_again_then_dismiss(self):
        harness = self.boot()
        harness.eval('ClockState.ring({id: 7, time: "07:30", days: [0], label: "Gym", enabled: true}, true)')
        harness.pump(400)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertTrue({"Gym", "07:30", "Snooze 10 min", "Dismiss"} <= texts())

        def press(label):
            button = next(item for item in harness.visible_items()
                          if item.metaObject().className().startswith("PillButton") and item.property("text") == label)
            harness.click(*harness.scene_pos(button))
            harness.pump(300)
        press("Snooze 10 min")
        self.assertEqual(harness.eval_value("ClockState.ringing === null"), "true")
        self.assertEqual(harness.eval_value("ClockState.snoozed.length"), "1")
        harness.eval("ClockState.checkSnoozed(Date.now() + 11 * 60000)")
        harness.pump(300)
        self.assertEqual(harness.eval_value("ClockState.ringing.title"), "Gym")
        self.assertEqual(harness.eval_value("ClockState.snoozed.length"), "0")
        press("Dismiss")
        self.assertEqual(harness.eval_value("ClockState.ringing === null"), "true")
        self.assertEqual(harness.problems(), [])

    def test_timer_banner_has_no_snooze(self):
        harness = self.boot()
        harness.eval('ClockState.startRinging({title: "Timer", detail: "Time\'s up", kind: "timer", alarm: null})')
        harness.pump(400)
        labels = [str(item.property("text")) for item in harness.visible_items()
                  if item.metaObject().className().startswith("PillButton")]
        self.assertIn("Dismiss", labels)
        self.assertNotIn("Snooze 10 min", labels)
        self.assertEqual(harness.truncated_texts(), [])

    def test_world_clock_adds_a_zone_through_the_bridge(self):
        from prismos import regional, settings
        if "Asia/Tokyo" not in regional.timezones():
            self.skipTest("tz database missing")
        harness = self.boot()
        harness.ipc("worldclock")
        harness.pump(500)
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("InstallerState.timezones.length") != "0", 8000))
        harness.pump(400)
        self.type_into(harness, "Search", "Tokyo")
        row = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("ListRow") and item.property("title") == "Asia/Tokyo")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(200)
        add = next(item for item in harness.visible_items()
                   if item.metaObject().className().startswith("PillButton") and item.property("text") == "Add")
        harness.click(*harness.scene_pos(add))
        self.assertTrue(harness.wait_for(lambda: settings.load()["world_clocks"] == ["Asia/Tokyo"], 6000))
        self.assertTrue(harness.wait_for(lambda: harness.eval_value("WorldClockState.clocks.length") == "1", 6000))
        harness.pump(500)
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_recents_shows_window_previews_and_falls_back_to_icons(self):
        import tempfile
        from PIL import Image
        folder = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        shot = Path(folder) / "0xaa01-1.png"
        Image.new("RGB", (96, 60), (200, 40, 40)).save(shot)
        harness = self.boot()
        harness.ipc("recents")
        harness.pump(900)
        self.assertEqual(harness.eval_value("ShellState.recentsOpen"), "true", "opens even when no preview can be taken")
        harness.eval(WINDOWS + 'Windows.thumbs = {"0xaa01": "%s"};' % shot)

        def previews():
            return [item for item in harness.visible_items()
                    if item.metaObject().className().startswith("QQuickImage") and "0xaa01-1.png" in str(item.property("source"))]
        self.assertTrue(harness.wait_for(lambda: len(previews()) == 1, 3000))
        previews = previews()
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_preview_toggle_goes_to_the_bridge(self):
        from prismos import settings
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-style")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(700)
        toggle = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("ToggleRow") and item.property("title") == "Window previews in Recents")
        harness.reveal(toggle)
        harness.click(*harness.scene_pos(toggle))
        self.assertTrue(harness.wait_for(lambda: settings.load()["recents_previews"] is False, 6000))

    def test_glance_shows_the_next_alarm_and_a_running_timer(self):
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, alarms=[
            {"id": 1, "time": "23:59", "days": [], "label": "", "enabled": True}])
        harness.load()
        harness.pump(1800)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertTrue(any(text.startswith("Alarm ") and "23:59" in text for text in texts()), texts())
        harness.eval("ClockState.setTimer(90); ClockState.startTimer()")
        harness.pump(300)
        self.assertTrue(any(text.startswith("Timer ") for text in texts()))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_notes_widget_saves_what_you_type(self):
        from prismos import notes
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, widgets=["glance", "notes"])
        harness.load()
        harness.pump(1500)
        area = next(item for item in harness.visible_items()
                    if "TextArea" in item.metaObject().className() and item.property("placeholderText") == "Jot something down…")
        self.assertTrue(harness.wait_for(lambda: area.property("enabled") is True, 4000))
        area.forceActiveFocus()
        from PySide6.QtTest import QTest
        for character in "buy milk":
            QTest.keyClick(harness.view, character)
        self.assertTrue(harness.wait_for(lambda: notes.get()["text"] == "buy milk", 6000))
        self.assertTrue(harness.wait_for(lambda: "Saved" in {str(i.property("text")) for i in harness.visible_items() if i.property("text")}, 3000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_power_mode_and_night_light_settings_reach_the_bridge(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-display")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(700)
        texts = {str(item.property("text")) for item in harness.visible_items() if item.property("text")}
        self.assertIn("Night Light", texts)
        self.assertIn("Needs the hyprsunset package", texts)
        self.assertEqual(harness.truncated_texts(), [])
        row = harness.find("section-power")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.eval('const snap = JSON.parse(JSON.stringify(SystemBridge.snapshot)); snap.profile = {available: true, profile: "balanced", saver: false}; SystemBridge.snapshot = snap;')
        find = lambda: next((item for item in harness.visible_items()
                             if item.metaObject().className().startswith("ListRow") and item.property("title") == "Power saver"), None)
        self.assertTrue(harness.wait_for(lambda: find() is not None, 1500))
        saver = find()
        harness.reveal(saver)
        Process.log.clear()
        harness.click(*harness.scene_pos(saver))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "action", "power-saver"] in Process.log, 4000))
        self.assertEqual(harness.truncated_texts(), [])

    def test_clipboard_history_can_be_searched(self):
        from PySide6.QtTest import QTest
        harness = self.boot()
        harness.ipc("clipboard")
        harness.pump(600)
        harness.eval('ClipboardState.available = true; ClipboardState.enabled = true; ClipboardState.items = ['
                     '{id:"12", kind:"text", preview:"hello world"}, {id:"11", kind:"text", preview:"grocery list"}]')
        harness.pump(300)
        titles = lambda: sorted(str(item.property("title")) for item in harness.visible_items()
                                if item.metaObject().className().startswith("ListRow") and item.property("title") in ("hello world", "grocery list"))
        self.assertEqual(titles(), ["grocery list", "hello world"])
        self.type_into(harness, "Search history", "gro")
        self.assertEqual(titles(), ["grocery list"])
        self.type_into(harness, "Search history", "zzz")
        self.assertEqual(titles(), [])
        self.assertTrue(any(str(item.property("text")) == "No matches" for item in harness.visible_items()))

    def test_clipboard_pins_show_copy_and_unpin_through_the_bridge(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("clipboard")
        harness.pump(600)
        harness.eval('ClipboardState.available = true; ClipboardState.enabled = true; ClipboardState.pins = ['
                     '{id: 3, preview: "my address"}]; ClipboardState.items = [{id:"12", kind:"text", preview:"hello world"}, '
                     '{id:"11", kind:"image", preview:"Image"}]')
        harness.pump(300)
        row = lambda title: next(item for item in harness.visible_items()
                                 if item.metaObject().className().startswith("ListRow") and item.property("title") == title)
        Process.log.clear()
        harness.click(*harness.scene_pos(row("my address")))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "clipboard", "copy-pin", "3"] in Process.log, 3000))
        pin_buttons = [item for item in harness.visible_items(row("hello world")) if item.property("symbol") == "pin"]
        self.assertEqual(len(pin_buttons), 1)
        self.assertEqual([item for item in harness.visible_items(row("Image")) if item.property("symbol") == "pin"], [],
                         "images cannot be pinned")
        harness.click(*harness.scene_pos(pin_buttons[0]))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "clipboard", "pin", "12"] in Process.log, 3000))
        self.assertEqual(harness.truncated_texts(), [])
        self.assertEqual(harness.problems(), [])

    def test_tile_detail_panels_open_on_right_click_and_act(self):
        from PySide6.QtCore import Qt
        from prismos import settings
        from qml_runtime.stubs import Process
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, tiles=["dark", "battery_saver", "screenshot", "night_light", "dnd"])
        harness.load()
        harness.pump(1500)
        harness.ipc("shade")
        harness.pump(600)
        texts = lambda: {str(item.property("text")) for item in harness.visible_items() if item.property("text")}

        def tile(title):
            return next(item for item in harness.visible_items()
                        if item.metaObject().className().startswith("QuickTile") and item.property("title") == title)

        def chip(label):
            return next(item for item in harness.visible_items()
                        if item.metaObject().className().startswith("FilterChip") and item.property("text") == label)
        harness.click(*harness.scene_pos(tile("Night Light")), button=Qt.RightButton)
        harness.pump(400)
        self.assertIn("Night Light needs the hyprsunset package.", texts())
        harness.click(*harness.scene_pos(tile("Battery Saver")), button=Qt.RightButton)
        harness.pump(300)
        harness.eval('const snap = JSON.parse(JSON.stringify(SystemBridge.snapshot)); snap.profile = {available: true, profile: "balanced", saver: false}; SystemBridge.snapshot = snap;')
        self.assertTrue(harness.wait_for(lambda: chip("Performance").property("enabled"), 2000))
        Process.log.clear()
        harness.click(*harness.scene_pos(chip("Performance")))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "action", "power-performance"] in Process.log, 3000))
        harness.click(*harness.scene_pos(tile("Dark theme")), button=Qt.RightButton)
        harness.pump(300)
        harness.click(*harness.scene_pos(chip("Vibrant")))
        self.assertTrue(harness.wait_for(lambda: settings.load()["scheme"] == "vibrant", 6000))
        harness.click(*harness.scene_pos(tile("Screenshot")), button=Qt.RightButton)
        harness.pump(300)
        Process.log.clear()
        harness.click(*harness.scene_pos(chip("Full screen")))
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "screenshot", "full"] in Process.log, 4000))
        self.assertEqual(harness.problems(), [])

    def test_widget_size_changes_the_card_and_keeps_text_readable(self):
        from prismos import settings
        sizes = {}
        for label, saved in (("small", "small"), ("large", "large")):
            harness = Harness(width=1600, height=1000)
            self.addCleanup(harness.close)
            harness.write_settings(onboarding_complete=True, widgets=["glance", "system", "calendar", "notes"],
                                   widget_sizes={"system": saved, "calendar": saved, "notes": saved})
            harness.load()
            harness.pump(1600)
            card = next(item for item in harness.visible_items()
                        if item.metaObject().className().startswith("SystemWidget"))
            sizes[label] = card.width()
            self.assertEqual(harness.truncated_texts(), [], label)
            self.assertEqual(harness.problems(), [], label)
        self.assertLess(sizes["small"], 292)
        self.assertGreater(sizes["large"], 292)

    def test_widgets_page_size_chips_reach_the_bridge(self):
        from prismos import settings
        harness = Harness()
        self.addCleanup(harness.close)
        harness.write_settings(onboarding_complete=True, widgets=["glance", "notes"])
        harness.load()
        harness.pump(1500)
        harness.ipc("settings")
        harness.pump(500)
        row = harness.find("section-widgets")
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        harness.pump(700)
        chip = next(item for item in harness.visible_items()
                    if item.metaObject().className().startswith("FilterChip") and item.property("text") == "Large")
        harness.reveal(chip)
        harness.click(*harness.scene_pos(chip))
        self.assertTrue(harness.wait_for(lambda: settings.load()["widget_sizes"].get("notes") == "large", 6000))
        self.assertEqual(harness.truncated_texts(), [])

    def test_recents_uses_live_window_contents_when_the_compositor_offers_them(self):
        from qml_runtime import stubs
        harness = self.boot()
        harness.pump(300)
        ipc = stubs.Services().hyprland
        ipc.add_toplevel("aa01")            # no 0x prefix, as Quickshell may report it
        ipc.add_toplevel("0xaa02", with_handle=False)   # window without a toplevel handle
        harness.ipc("recents")
        harness.pump(900)
        harness.eval(WINDOWS)
        harness.pump(400)
        self.assertGreaterEqual(ipc.refreshes, 1, "refreshes the toplevel list when it opens")
        live = [item for item in harness.visible_items() if item.metaObject().className().startswith("LivePreview")]
        self.assertEqual(len(live), 1, "only the window with a handle shows live contents")
        harness.ipc("close")
        harness.pump(500)
        self.assertEqual([item for item in harness.visible_items() if item.metaObject().className().startswith("LivePreview")], [])
        self.assertEqual(harness.problems(), [])

    def test_close_all_closes_every_window_one_request_at_a_time(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.ipc("recents")
        harness.pump(900)
        harness.eval(WINDOWS)
        harness.pump(300)
        button = next(item for item in harness.visible_items()
                      if item.metaObject().className().startswith("PillButton") and item.property("text") == "Close all")
        Process.log.clear()
        harness.click(*harness.scene_pos(button))
        wanted = [["prismctl", "windows", "close", "0xaa01"], ["prismctl", "windows", "close", "0xaa02"]]
        self.assertTrue(harness.wait_for(lambda: all(command in Process.log for command in wanted), 8000), Process.log)
        self.assertEqual(harness.eval_value("Windows.closing.length"), "0")

    def test_storage_page_reports_folders_and_clears_previews(self):
        import os
        from pathlib import Path
        harness = self.boot()
        home = Path(os.environ["HOME"])
        (home / "Documents").mkdir()
        (home / "Documents" / "notes.txt").write_bytes(b"x" * 50000)
        (home / "Downloads").mkdir()
        (home / "Downloads" / "big.iso").write_bytes(b"x" * 90000)
        previews = Path(os.environ["XDG_RUNTIME_DIR"]) / "prismos-previews"
        previews.mkdir()
        (previews / "0xaa01-1.png").write_bytes(b"x" * 20000)
        harness.ipc("settings")
        harness.pump(600)
        row = harness.find("section-storage")
        self.assertIsNotNone(row)
        harness.reveal(row)
        harness.click(*harness.scene_pos(row))
        self.assertTrue(harness.wait_for(lambda: harness.find("storage-documents") is not None, 8000))
        self.assertIsNotNone(harness.find("storage-downloads"))
        self.assertFalse(harness.find("storage-music").isVisible())
        for value, text in (("0", "0 B"), ("999", "999 B"), ("1500", "1.5 KB"), ("20000", "20 KB"),
                            ("123456789", "123 MB"), ("2000000000", "2 GB"), ("undefined", "Unknown")):
            self.assertEqual(harness.eval_value(f"StorageState.size({value})"), text, value)
        self.assertTrue(harness.find("storage-downloads").isVisible())
        self.assertEqual(harness.problems(), [])
        self.assertEqual(harness.truncated_texts(), [])
        button = harness.find("storage-clear-previews")
        harness.reveal(button)
        harness.click(*harness.scene_pos(button))
        self.assertTrue(harness.wait_for(lambda: not previews.exists(), 8000))
        self.assertTrue(harness.wait_for(lambda: not harness.find("storage-clear-previews").isEnabled(), 8000))

    def test_apps_the_theme_has_no_icon_for_get_a_letter_tile_not_a_generic_icon(self):
        harness = Harness()
        self.addCleanup(harness.close)
        harness.add_desktop_entry("noicon.desktop", "Zebra Notes", icon="no-such-icon-anywhere")
        harness.add_desktop_entry("bare.desktop", "Quill", icon="")
        harness.write_settings(onboarding_complete=True)
        harness.load()
        harness.pump(1500)
        harness.ipc("launcher")
        harness.pump(700)
        tiles = [item for item in harness.visible_items() if item.metaObject().className().startswith("AppIcon")]
        self.assertGreaterEqual(len(tiles), 2)
        for tile in tiles:
            self.assertFalse(tile.property("found"), tile.property("label"))
        initials = {tile.property("label"): tile.property("initial") for tile in tiles}
        self.assertEqual(initials["Zebra Notes"], "Z")
        self.assertEqual(initials["Quill"], "Q")
        self.assertEqual(harness.problems(), [])
        self.assertEqual(harness.truncated_texts(), [])

    def test_toggles_answer_the_click_at_once_and_the_real_state_confirms_it(self):
        from prismos import settings
        harness = self.boot()
        harness.pump(1500)  # first status read lands
        now = harness.eval_value
        # Hardware the sandbox does not have is put in place inside each evaluation, because
        # the real status reads that follow every click would otherwise replace it.
        fake = ("SystemBridge.snapshot = SystemBridge.patched({wifi: {available: true, enabled: true}, "
                "volume: {available: true, value: 40, muted: false}, brightness: {available: true, value: 50}}); ")

        def clicked(call, field):
            return now("(function () { " + fake + call + "; return " + field + "; })()")
        # The value is already there when the call returns: nothing waited on a command.
        self.assertEqual(clicked("SystemBridge.action('dnd')", "SystemBridge.snapshot.settings.dnd"), "true")
        self.assertEqual(clicked("SystemBridge.action('wifi')", "SystemBridge.snapshot.wifi.enabled"), "false")
        self.assertEqual(clicked("SystemBridge.action('mute')", "SystemBridge.snapshot.volume.muted"), "true")
        self.assertEqual(clicked("SystemBridge.action('volume', 72)", "SystemBridge.snapshot.volume.value"), "72")
        self.assertEqual(clicked("SystemBridge.action('brightness-down')", "SystemBridge.snapshot.brightness.value"), "45")
        self.assertEqual(clicked("SystemBridge.action('volume-up')", "SystemBridge.snapshot.volume.value"), "45")
        # Sliders stay inside their range.
        self.assertEqual(clicked("SystemBridge.action('volume', 400)", "SystemBridge.snapshot.volume.value"), "100")
        self.assertEqual(clicked("SystemBridge.action('brightness', 0)", "SystemBridge.snapshot.brightness.value"), "1")
        # Editing the tile list answers at once as well.
        self.assertEqual(clicked("SystemBridge.setTiles(['dnd', 'wifi'])", "JSON.stringify(SystemBridge.snapshot.settings.tiles)"), '["dnd","wifi"]')
        # Unavailable hardware is left alone, and unknown actions predict nothing.
        self.assertEqual(clicked("SystemBridge.action('microphone-mute')", "SystemBridge.snapshot.microphone.muted"), "false")
        self.assertEqual(now("SystemBridge.predict('lock') === null"), "true")
        # The command really ran, and the status read that follows settles on the real value.
        self.assertTrue(harness.wait_for(lambda: settings.load()["dnd"] is True, 8000))
        self.assertTrue(harness.wait_for(lambda: now("SystemBridge.pending.length === 0 && !SystemBridge.busy") == "true", 20000))
        harness.pump(1500)
        self.assertEqual(now("SystemBridge.snapshot.settings.dnd"), "true")
        self.assertEqual(harness.problems(), [])

    def test_a_status_read_that_started_before_a_click_cannot_flip_the_tile_back(self):
        harness = self.boot()
        harness.pump(1500)
        now = harness.eval_value
        self.assertEqual(now("(function () { SystemBridge.action('dnd'); return SystemBridge.staleRead; })()"), "false",
                         "nothing was reading, so nothing is stale")
        harness.wait_for(lambda: now("!SystemBridge.busy && SystemBridge.pending.length === 0") == "true", 8000)
        harness.pump(1500)
        self.assertEqual(now("(function () { SystemBridge.refresh(); SystemBridge.action('dnd'); return SystemBridge.staleRead; })()"), "true")
        self.assertTrue(harness.wait_for(lambda: now("SystemBridge.staleRead") == "false", 8000))
        harness.pump(1500)
        self.assertEqual(now("SystemBridge.snapshot.settings.dnd"), "false", "two toggles are back to the start")

    def test_a_wrong_guess_is_replaced_by_the_real_state_even_when_nothing_else_changed(self):
        harness = self.boot()
        harness.pump(2500)
        now = harness.eval_value
        self.assertEqual(now("SystemBridge.lastStatus.length > 10"), "true", "the first real reading is remembered")
        # A guess the system will not confirm (the real value stays false): the tile must go back.
        self.assertEqual(now("(function () { SystemBridge.snapshot = SystemBridge.patched({settings: {dnd: true}}); "
                             "SystemBridge.lastStatus = ''; SystemBridge.refresh(); return SystemBridge.snapshot.settings.dnd; })()"), "true")
        self.assertTrue(harness.wait_for(lambda: now("SystemBridge.snapshot.settings.dnd") == "false", 8000))

    def test_slider_rows_show_their_value_once_in_their_own_units(self):
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(600)
        for section, expect_percent in (("input", False), ("sound", True)):
            row = harness.find("section-" + section)
            harness.reveal(row)
            harness.click(*harness.scene_pos(row))
            harness.pump(700)
            texts = [str(item.property("text")) for item in harness.visible_items() if item.property("text") is not None]
            percents = [text for text in texts if re.fullmatch(r"-?\d+(\.\d+)?%", text)]
            if expect_percent:
                self.assertEqual(len(percents), 1, f"{section}: the same value must not appear twice: {percents}")
            else:
                self.assertEqual(percents, [], f"{section}: speeds and rates are not percentages")
            self.assertEqual(harness.truncated_texts(), [], section)
        self.assertEqual(harness.problems(), [])

    def test_hardware_keys_show_an_indicator_that_follows_the_level(self):
        harness = self.boot()
        harness.pump(2500)
        now = harness.eval_value

        def setup(volume=40, muted=False, mic_muted=False, brightness=3):
            # Real hardware answers the key; here a status read would replace the pretend values, so
            # each key press starts from known values (once the previous press has fully settled)
            # and is checked before the next read can land.
            harness.wait_for(lambda: now("!SystemBridge.busy && SystemBridge.pending.length === 0 && !SystemBridge.reader.running") == "true", 8000)
            harness.eval("SystemBridge.snapshot = SystemBridge.patched({"
                         f"volume: {{available: true, value: {volume}, muted: {str(muted).lower()}}}, "
                         f"microphone: {{available: true, value: 70, muted: {str(mic_muted).lower()}}}, "
                         f"brightness: {{available: true, value: {brightness}}}}}); ")

        def pill():
            return harness.find("osd-pill")
        self.assertEqual(now("ShellState.osdKind"), "")
        # Bindings update synchronously, so each result is read straight after the key press.
        text = lambda: harness.find("osd-value").property("text")
        setup()
        harness.ipc("volumeUp")
        self.assertTrue(pill().isVisible())
        self.assertEqual(text(), "45%")
        setup(volume=45)
        harness.ipc("volumeDown")
        harness.ipc("volumeDown")
        self.assertEqual(text(), "35%")
        setup(volume=35)
        harness.ipc("volumeMute")
        self.assertEqual(text(), "Muted")
        setup(mic_muted=False)
        harness.ipc("micMute")
        self.assertEqual(text(), "Muted")
        self.assertEqual(harness.eval_value("ShellState.osdKind"), "microphone")
        setup(brightness=3)
        harness.ipc("brightnessDown")
        self.assertEqual(text(), "1%", "never steps to a black screen")
        self.assertEqual(harness.truncated_texts(), [])
        # It goes away by itself.
        self.assertTrue(harness.wait_for(lambda: now("ShellState.osdKind") == "", 4000))
        self.assertTrue(harness.wait_for(lambda: not pill().isVisible(), 3000))
        # Without a volume control there is nothing to show (the command reports the problem instead).
        harness.eval("SystemBridge.snapshot = SystemBridge.patched({volume: {available: false}});")
        harness.ipc("volumeUp")
        harness.pump(60)
        self.assertEqual(now("ShellState.osdKind"), "")
        self.assertEqual(harness.problems(), [])

    def test_stepping_keys_are_never_merged_but_slider_values_are(self):
        from qml_runtime.stubs import Process
        harness = self.boot()
        harness.pump(2500)
        Process.log.clear()
        harness.eval("SystemBridge.action('mute'); SystemBridge.action('mute'); SystemBridge.action('mute');")
        self.assertTrue(harness.wait_for(lambda: Process.log.count(["prismctl", "action", "mute"]) == 3, 8000), Process.log)
        harness.wait_for(lambda: harness.eval_value("!SystemBridge.busy && SystemBridge.pending.length === 0") == "true", 8000)
        Process.log.clear()
        harness.eval("SystemBridge.action('volume', 10); SystemBridge.action('volume', 20); SystemBridge.action('volume', 30);")
        self.assertTrue(harness.wait_for(lambda: ["prismctl", "action", "volume", "30"] in Process.log, 8000), Process.log)
        harness.wait_for(lambda: harness.eval_value("!SystemBridge.busy && SystemBridge.pending.length === 0") == "true", 8000)
        volumes = [entry for entry in Process.log if entry[:3] == ["prismctl", "action", "volume"]]
        self.assertEqual(volumes[0], ["prismctl", "action", "volume", "10"])
        self.assertEqual(volumes[-1], ["prismctl", "action", "volume", "30"])
        self.assertNotIn(["prismctl", "action", "volume", "20"], volumes, "the middle value was superseded")

    def test_settings_search_filters_sections(self):
        harness = self.boot()
        harness.ipc("settings")
        harness.pump(600)
        self.assertIsNotNone(harness.find("section-network"))
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
