import json
import unittest
from unittest.mock import patch

from prismos import cli, windows
from prismos.system import CommandError

CLIENTS = [
    {"address": "0xAB12", "mapped": True, "hidden": False, "class": "firefox", "title": "Docs, drafts",
     "workspace": {"id": 2}, "pid": 10, "focusHistoryID": 0},
    {"address": "0xcd34", "mapped": True, "class": "foot", "title": "~", "workspace": {"id": 1}, "pid": 11, "focusHistoryID": 3},
    {"address": "0xdead", "mapped": False, "class": "ghost", "title": "unmapped", "workspace": {"id": 1}},
    {"address": "not-hex", "mapped": True, "class": "evil", "workspace": {"id": 1}},
    {"address": "0xbeef", "mapped": True, "class": "", "title": "no app id", "workspace": {"id": 1}},
]


def fake_run(args, timeout=4):
    if args[:3] == ["hyprctl", "-j", "clients"]:
        return json.dumps(CLIENTS)
    if args[:3] == ["hyprctl", "-j", "activewindow"]:
        return json.dumps({"address": "0xAB12"})
    if args[:2] == ["hyprctl", "dispatch"]:
        return fake_run.reply
    raise AssertionError(args)


fake_run.reply = "ok"


class WindowTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("prismos.windows.run", side_effect=fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)
        fake_run.reply = "ok"

    def test_only_mapped_valid_windows_with_app_ids_are_listed_in_order(self):
        result = windows.clients()
        self.assertEqual([w["class"] for w in result], ["foot", "firefox"])
        self.assertTrue(result[1]["focused"])
        self.assertEqual(result[1]["title"], "Docs, drafts")

    def test_recency_comes_from_focus_history(self):
        by_class = {w["class"]: w["recency"] for w in windows.clients()}
        self.assertEqual(by_class, {"firefox": 0, "foot": 3})

    def test_focus_sends_fixed_arguments_for_known_window(self):
        with patch("prismos.windows.run", side_effect=fake_run) as run:
            windows.dispatch("focus", "0xAB12")
        run.assert_called_with(["hyprctl", "dispatch", "focuswindow", "address:0xab12"], timeout=5)

    def test_unknown_or_malformed_windows_never_reach_the_compositor(self):
        for address in ("0x9999", "x; reboot", "", None, "0xAB12 --batch"):
            with self.subTest(address=address), patch("prismos.windows.run", side_effect=fake_run) as run:
                with self.assertRaises(ValueError):
                    windows.dispatch("close", address)
                self.assertNotIn("dispatch", [call.args[0][1] for call in run.call_args_list])

    def test_unknown_operation_rejected(self):
        with self.assertRaises(ValueError):
            windows.dispatch("kill", "0xAB12")

    def test_rejected_dispatch_is_reported(self):
        fake_run.reply = "Invalid dispatcher"
        with self.assertRaises(CommandError):
            windows.dispatch("focus", "0xcd34")

    def test_missing_hyprctl_returns_structured_error(self):
        with patch("prismos.windows.run", side_effect=CommandError("hyprctl is not installed")):
            self.assertEqual(windows.status()["ok"], False)

    def test_cli_lists_windows_as_json(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["windows", "list"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out.getvalue())["windows"]), 2)



MONITORS = [{"id": 0, "x": 0, "y": 0, "width": 2560, "height": 1600, "scale": 2.0, "reserved": [0, 44, 0, 92]}]
CLIENTS_STATE = [
    {"address": "0xaa01", "mapped": True, "class": "firefox", "title": "Docs", "workspace": {"id": 1, "name": "1"},
     "pid": 1, "floating": False, "fullscreen": 0, "monitor": 0, "focusHistoryID": 0},
    {"address": "0xaa02", "mapped": True, "class": "foot", "title": "~", "workspace": {"id": -98, "name": "special:minimized"},
     "pid": 2, "floating": True, "fullscreen": 0, "monitor": 0, "focusHistoryID": 2},
    {"address": "0xaa03", "mapped": True, "class": "thunar", "title": "Files", "workspace": {"id": 1, "name": "1"},
     "pid": 3, "floating": True, "fullscreen": 1, "monitor": 0, "focusHistoryID": 1},
]


class WindowManagementTests(unittest.TestCase):
    def setUp(self):
        self.sent = []

        def fake(args, timeout=4):
            if args[:3] == ["hyprctl", "-j", "clients"]:
                return json.dumps(CLIENTS_STATE)
            if args[:3] == ["hyprctl", "-j", "activewindow"]:
                return json.dumps({"address": "0xaa01"})
            if args[:3] == ["hyprctl", "-j", "monitors"]:
                return json.dumps(MONITORS)
            if args[:3] == ["hyprctl", "-j", "activeworkspace"]:
                return json.dumps({"id": 3})
            if args[:2] == ["hyprctl", "dispatch"]:
                self.sent.append(args[2:])
                return "ok"
            raise AssertionError(args)
        patcher = patch("prismos.windows.run", side_effect=fake)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_state_reports_floating_maximized_and_minimized(self):
        state = {w["class"]: w for w in windows.clients()}
        self.assertTrue(state["foot"]["minimized"])
        self.assertFalse(state["firefox"]["minimized"])
        self.assertTrue(state["thunar"]["maximized"] and state["thunar"]["floating"])

    def test_minimize_moves_to_the_special_workspace_silently(self):
        windows.dispatch("minimize", "0xaa01")
        self.assertEqual(self.sent, [["movetoworkspacesilent", "special:minimized,address:0xaa01"]])

    def test_restore_returns_to_current_workspace_and_focuses(self):
        windows.dispatch("restore", "0xaa02")
        self.assertEqual(self.sent, [["movetoworkspace", "3,address:0xaa02"], ["focuswindow", "address:0xaa02"]])

    def test_maximize_focuses_then_toggles(self):
        windows.dispatch("maximize", "0xaa01")
        self.assertEqual(self.sent, [["focuswindow", "address:0xaa01"], ["fullscreen", "1"]])

    def test_active_alias_targets_the_focused_window_only(self):
        windows.dispatch("close", "active")
        self.assertEqual(self.sent, [["closewindow", "address:0xaa01"]])

    def test_snap_left_floats_then_sizes_to_half_the_usable_area(self):
        windows.dispatch("snap-left", "0xaa01")
        # 2560x1600 at 2x is 1280x800; usable 1280x664; half = (1280-36)//2 = 622
        self.assertEqual(self.sent, [["togglefloating", "address:0xaa01"],
                                     ["resizewindowpixel", "exact 622 640,address:0xaa01"],
                                     ["movewindowpixel", "exact 12 56,address:0xaa01"]])

    def test_snap_right_and_leaving_maximized_state(self):
        windows.dispatch("snap-right", "0xaa03")
        self.assertEqual(self.sent[:2], [["focuswindow", "address:0xaa03"], ["fullscreen", "1"]])
        self.assertEqual(self.sent[-1], ["movewindowpixel", "exact 646 56,address:0xaa03"])
        self.assertNotIn(["togglefloating", "address:0xaa03"], self.sent)  # already floating

    def test_minimized_windows_cannot_be_snapped_or_maximized(self):
        for operation in ("snap-left", "maximize"):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                windows.dispatch(operation, "0xaa02")
        self.assertEqual(self.sent, [])

    def test_tiny_screens_refuse_to_snap(self):
        tiny = [dict(MONITORS[0], width=420, height=600, scale=1.0, reserved=[0, 44, 0, 92])]
        with patch.object(windows, "_json", side_effect=lambda c: tiny if c[2] == "monitors" else
                          json.loads(windows.run(c))):
            with self.assertRaises(CommandError):
                windows.dispatch("snap-left", "0xaa01")

    def test_hostile_addresses_and_operations_never_dispatch(self):
        for operation, address in (("close", "0xaa01; reboot"), ("snap-up", "0xaa01"), ("float", "active\n"), ("focus", "0xAA99")):
            with self.subTest(operation=operation, address=address), self.assertRaises(ValueError):
                windows.dispatch(operation, address)
        self.assertEqual(self.sent, [])


SPLIT_CLIENTS = [
    {"address": "0xaa01", "mapped": True, "class": "firefox", "title": "Docs", "workspace": {"id": 1, "name": "1"},
     "pid": 1, "floating": False, "fullscreen": 0, "monitor": 0, "focusHistoryID": 0},
    {"address": "0xaa02", "mapped": True, "class": "foot", "title": "~", "workspace": {"id": -98, "name": "special:minimized"},
     "pid": 2, "floating": True, "fullscreen": 0, "monitor": 0, "focusHistoryID": 2},
    {"address": "0xaa03", "mapped": True, "class": "thunar", "title": "Files", "workspace": {"id": 4, "name": "4"},
     "pid": 3, "floating": False, "fullscreen": 0, "monitor": 0, "focusHistoryID": 1},
]


class DesktopAndSplitTests(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.sent = []
        self.clients = [dict(c, workspace=dict(c["workspace"])) for c in SPLIT_CLIENTS]
        self.current = 1
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        runtime = patch.dict(os.environ, {"XDG_RUNTIME_DIR": folder.name})
        runtime.start(); self.addCleanup(runtime.stop)
        self.folder = folder.name

        def fake(args, timeout=4):
            if args[:3] == ["hyprctl", "-j", "clients"]:
                return json.dumps(self.clients)
            if args[:3] == ["hyprctl", "-j", "activewindow"]:
                return json.dumps({"address": "0xaa01"})
            if args[:3] == ["hyprctl", "-j", "monitors"]:
                return json.dumps(MONITORS)
            if args[:3] == ["hyprctl", "-j", "activeworkspace"]:
                return json.dumps({"id": self.current})
            if args[:2] == ["hyprctl", "dispatch"]:
                self.sent.append(args[2:])
                self.apply(args[2], args[3])
                return "ok"
            raise AssertionError(args)
        patcher = patch("prismos.windows.run", side_effect=fake)
        patcher.start(); self.addCleanup(patcher.stop)

    def apply(self, name, argument):
        """Just enough of the compositor to follow a window between workspaces."""
        if name == "movetoworkspacesilent":
            where, target = argument.split(",address:")
            for client in self.clients:
                if client["address"] == target:
                    client["workspace"] = {"id": -98 if where == windows.MINIMIZED else int(where), "name": where}

    def test_show_desktop_tucks_away_the_current_workspace_and_a_second_press_brings_it_back(self):
        result = windows.show_desktop()
        self.assertEqual((result["hidden"], result["restored"]), (1, 0))
        self.assertEqual(self.sent, [["movetoworkspacesilent", "special:minimized,address:0xaa01"]])
        self.assertTrue((__import__("pathlib").Path(self.folder) / "prismos-desktop.json").exists())
        self.sent.clear()
        result = windows.show_desktop()
        self.assertEqual((result["hidden"], result["restored"]), (0, 1))
        self.assertEqual(self.sent, [["movetoworkspacesilent", "1,address:0xaa01"], ["focuswindow", "address:0xaa01"]],
                         "only what the first press hid comes back, not the window minimized earlier")
        self.assertFalse((__import__("pathlib").Path(self.folder) / "prismos-desktop.json").exists())

    def test_show_desktop_with_nothing_to_hide_or_restore_does_nothing(self):
        self.clients = [c for c in self.clients if c["address"] != "0xaa01"]
        self.assertEqual(windows.show_desktop()["restored"], 0)
        self.assertEqual(self.sent, [])

    def test_a_remembered_window_that_has_since_closed_is_skipped(self):
        windows.show_desktop()
        self.clients = [c for c in self.clients if c["address"] != "0xaa01"]
        self.sent.clear()
        self.assertEqual(windows.show_desktop()["restored"], 0)
        self.assertEqual(self.sent, [])

    def test_a_corrupt_state_file_is_ignored(self):
        (__import__("pathlib").Path(self.folder) / "prismos-desktop.json").write_text('["0xaa01; reboot", 7]')
        self.clients[0]["workspace"] = {"id": -98, "name": windows.MINIMIZED}
        self.assertEqual(windows.show_desktop()["restored"], 0)
        self.assertEqual(self.sent, [])

    def test_split_brings_both_windows_here_and_snaps_left_and_right(self):
        result = windows.split("0xaa03", "0xaa02")
        self.assertEqual((result["left"], result["right"]), ("0xaa03", "0xaa02"))
        self.assertEqual(self.sent[:2], [["movetoworkspacesilent", "1,address:0xaa03"],
                                         ["movetoworkspacesilent", "1,address:0xaa02"]])
        left = [c for c in self.sent if c[0] in ("resizewindowpixel", "movewindowpixel") and c[1].endswith("0xaa03")]
        right = [c for c in self.sent if c[0] in ("resizewindowpixel", "movewindowpixel") and c[1].endswith("0xaa02")]
        self.assertEqual(left[-1], ["movewindowpixel", "exact 12 56,address:0xaa03"])
        self.assertEqual(right[-1], ["movewindowpixel", "exact 646 56,address:0xaa02"])
        self.assertEqual(self.sent[-1], ["focuswindow", "address:0xaa02"])

    def test_split_rejects_the_same_window_and_unknown_or_hostile_addresses(self):
        for first, second in (("0xaa01", "0xaa01"), ("0xaa01", "0xdead"), ("0xaa01", "0xaa02; reboot"), ("nope", "0xaa02")):
            with self.subTest(first=first, second=second), self.assertRaises(ValueError):
                windows.split(first, second)
        self.assertEqual(self.sent, [])

    def test_cli_runs_both_screen_operations(self):
        import contextlib
        import io
        for argv, key in ((["windows", "show-desktop"], "hidden"), (["windows", "split", "0xaa01", "0xaa03"], "left")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(argv), 0)
            self.assertIn(key, json.loads(out.getvalue()))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["windows", "split", "0xaa01"]), 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
