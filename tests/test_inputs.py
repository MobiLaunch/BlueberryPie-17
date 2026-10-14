import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import inputs, settings, cli


class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        p = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        p.start()
        self.addCleanup(p.stop)

    def test_strict_types(self):
        for key, value in (("natural_scroll","yes"),("tap_to_click","1"),
                           ("pointer_speed","nan"),("pointer_speed","2.0"),
                           ("pointer_speed","1; reboot"),("repeat_rate","500"),
                           ("repeat_rate","false"),("missing","true")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                inputs.value(key, value)

    @patch("prismos.inputs.run")
    def test_changed_input_uses_fixed_hyprctl_argv(self, run):
        result = inputs.change("natural_scroll","false")
        self.assertFalse(result["settings"]["natural_scroll"])
        run.assert_called_once_with(
            ["hyprctl","keyword","input:touchpad:natural_scroll","false"],timeout=5)

    @patch("prismos.inputs.run", side_effect=OSError("Hyprland not available"))
    def test_failed_live_change_does_not_persist(self, run):
        with self.assertRaises(OSError):
            inputs.change("pointer_speed","0.7")
        self.assertEqual(settings.load()["pointer_speed"], 0.0)

    @patch("prismos.inputs.run")
    def test_apply_respects_saved_scoped_prefs(self, run):
        settings.update(tap_to_click=False, pointer_speed=0.5)
        inputs.apply()
        calls = [entry.args[0] for entry in run.call_args_list]
        self.assertIn(["hyprctl","keyword","input:touchpad:tap_to_click","false"],calls)
        self.assertIn(["hyprctl","keyword","input:sensitivity","0.5"],calls)

    def test_preference_validation_prevents_injection(self):
        settings.directory().mkdir()
        (settings.directory()/"settings.json").write_text(
            '{"pointer_speed": "oops", "repeat_rate": 900, "tap_to_click": "no"}')
        current = settings.load()
        self.assertEqual(current["pointer_speed"], 0.0)
        self.assertEqual(current["repeat_rate"],25)
        self.assertTrue(current["tap_to_click"])

    @patch("prismos.inputs.run")
    def test_cli_is_json(self, run):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(["input","set","repeat_rate","40"])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(output.getvalue())["settings"]["repeat_rate"],40)


if __name__ == "__main__":
    unittest.main()
