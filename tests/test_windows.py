import json
import unittest
from unittest.mock import patch

from prismos import cli, windows
from prismos.system import CommandError

CLIENTS = [
    {"address": "0xAB12", "mapped": True, "hidden": False, "class": "firefox", "title": "Docs, drafts",
     "workspace": {"id": 2}, "pid": 10},
    {"address": "0xcd34", "mapped": True, "class": "foot", "title": "~", "workspace": {"id": 1}, "pid": 11},
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


if __name__ == "__main__":
    unittest.main()
