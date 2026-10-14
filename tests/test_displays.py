import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prismos import displays, settings


class DisplaySafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.tmp.name,
                                       "XDG_RUNTIME_DIR": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        self.display = {
            "name": "eDP-1", "width": 1920, "height": 1080,
            "scale": 1.0, "refresh": 60.0, "x": 0, "y": 0,
            "choices": [1.0, 1.25, 1.5, 2.0]
        }

    @patch("prismos.displays.run")
    def test_connected_monitors_and_supported_scales(self, run):
        run.return_value = json.dumps([dict(self.display,
            refreshRate=60.0, description="Internal LCD")])
        monitors = displays.monitors()
        self.assertEqual(monitors[0]["name"], "eDP-1")
        self.assertIn(1.5, monitors[0]["choices"])
        self.assertNotIn(1.75, monitors[0]["choices"])
        run.assert_called_once_with(["hyprctl", "-j", "monitors"], timeout=7)

    @patch("prismos.displays.run")
    def test_lua_mode_uses_fixed_values_without_shell(self, run):
        displays.apply_rule(self.display, 1.5)
        self.assertEqual(run.call_args.args[0],
            ["hyprctl", "eval",
             'hl.monitor({ output = "eDP-1", mode = "1920x1080@60", position = "0x0", scale = 1.5 })'])

    @patch("prismos.displays.apply_rule")
    @patch("prismos.displays.monitors")
    @patch("prismos.displays.time.monotonic", side_effect=[0, 21])
    def test_trial_rolls_back_when_not_confirmed(self, monotonic, monitors, apply):
        monitors.return_value = [self.display]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(displays.preview("eDP-1", "1.5"), 0)
        self.assertEqual(apply.call_count, 2)
        self.assertEqual(apply.call_args_list[0].args[1], 1.5)
        self.assertEqual(apply.call_args_list[1].args[1], 1.0)
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["phase"], "reverted")
        self.assertFalse(settings.load()["display_scales"])

    @patch("prismos.displays.apply_rule")
    @patch("prismos.displays.monitors")
    def test_confirmed_trial_persists_only_after_explicit_confirmation(self, monitors, apply):
        monitors.return_value = [self.display]
        def confirm_instead_of_wait(delay):
            data = json.loads((displays.runtime_dir() / "display-pending.json").read_text())
            displays.confirm(data["token"])
        with patch("prismos.displays.time.sleep", side_effect=confirm_instead_of_wait):
            with contextlib.redirect_stdout(io.StringIO()):
                displays.preview("eDP-1", "1.5")
        self.assertEqual(settings.load()["display_scales"], {"eDP-1": 1.5})
        apply.assert_called_once()

    def test_invalid_monitor_and_scale_are_refused(self):
        for name, scale in (("DP-1; reboot", "1.5"), ("eDP-1", "999"),
                            ("eDP-1", "nan")):
            with self.subTest(name=name, scale=scale), self.assertRaises(ValueError):
                displays.preview(name, scale)

    def test_expired_and_unknown_confirmation_token_is_refused(self):
        with self.assertRaises(ValueError):
            displays.confirm("x" * 32)
        with self.assertRaises(ValueError):
            displays.confirm("0" * 32)


    def test_relative_positions_and_overlap_validation(self):
        selected = dict(self.display, name="HDMI-A-1", x=1920)
        self.assertEqual(displays.proposed_position(selected,self.display,"below"), (0,1080))
        self.assertEqual(displays.proposed_position(selected,self.display,"right"), (1920,0))
        self.assertFalse(displays.overlaps(self.display,selected))
        self.assertTrue(displays.overlaps(self.display,{**selected,"x":100}))

    @patch("prismos.displays.apply_rule")
    @patch("prismos.displays.monitors")
    @patch("prismos.displays.time.monotonic", side_effect=[0, 21])
    def test_unconfirmed_rearrangement_rolls_back(self, monotonic, monitors, apply):
        selected = {**self.display, "name":"HDMI-A-1","x":1920}
        monitors.return_value = [self.display,selected]
        with contextlib.redirect_stdout(io.StringIO()):
            displays.preview_position("HDMI-A-1","below","eDP-1")
        self.assertEqual(apply.call_count,2)
        self.assertEqual(apply.call_args_list[0].args[0]["y"],1080)
        self.assertEqual(apply.call_args_list[1].args[0]["x"],1920)
        self.assertFalse(settings.load()["display_positions"])

    @patch("prismos.displays.apply_rule")
    @patch("prismos.displays.monitors")
    def test_confirmed_arrangement_persists_and_reapplies(self, monitors, apply):
        second={**self.display,"name":"HDMI-A-1","x":1920}
        monitors.return_value = [self.display,second]
        def accept(delay):
            pending=json.loads((displays.runtime_dir()/"display-pending.json").read_text())
            displays.confirm(pending["token"])
        with patch("prismos.displays.time.sleep", side_effect=accept):
            with contextlib.redirect_stdout(io.StringIO()):
                displays.preview_position("HDMI-A-1","below","eDP-1")
        self.assertEqual(settings.load()["display_positions"],{"HDMI-A-1":[0,1080]})
        apply.reset_mock()
        self.assertEqual(displays.apply_saved()["applied"],1)
        self.assertEqual(apply.call_args.args[0]["y"],1080)

    @patch("prismos.displays.apply_rule")
    @patch("prismos.displays.monitors")
    def test_arrangement_rejects_overlap_with_third_monitor(self, monitors, apply):
        second = {**self.display,"name":"HDMI-A-1","x":1920}
        third = {**self.display,"name":"DP-2","x":0,"y":1080}
        monitors.return_value = [self.display,second,third]
        with self.assertRaises(ValueError):
            displays.preview_position("HDMI-A-1","below","eDP-1")
        apply.assert_not_called()

    @patch("prismos.displays.monitors")
    @patch("prismos.displays.apply_rule")
    def test_reapply_only_supported_connected_monitors(self, apply, monitors):
        settings.update(display_scales={"eDP-1": 1.5, "DP-5": 2.0})
        monitors.return_value = [self.display]
        self.assertEqual(displays.apply_saved()["applied"], 1)
        apply.assert_called_once_with(self.display, 1.5)


if __name__ == "__main__":
    unittest.main()
