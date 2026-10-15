"""Execute the packaged Hyprland Lua config against a mock `hl` API.

Needs a `lua` interpreter (lua5.4 / lua); skipped otherwise. This verifies the
config runs top to bottom and that its binds line up with the shell's IPC, not
that Hyprland accepts them (that needs a real compositor)."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LUA = shutil.which("lua5.4") or shutil.which("lua")

PRELUDE = r'''
local binds = {}
local function noop() end
local function descriptor(kind) return function(arg) return { kind = kind, arg = arg } end end
hl = {
  monitor = noop, env = noop, config = noop, curve = noop, animation = noop, gesture = noop, on = noop,
  exec_cmd = noop,
  bind = function(keys, action, options)
    binds[#binds + 1] = keys .. "\t" .. tostring(action and (action.arg or action.kind) or "?")
  end,
  dsp = { exec_cmd = descriptor("exec"),
          window = { drag = descriptor("drag"), resize = descriptor("resize"), close = descriptor("close") } },
}
dofile(arg[1])
for _, line in ipairs(binds) do print(line) end
'''


@unittest.skipIf(LUA is None, "lua interpreter not installed")
class HyprlandConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run([LUA, "-", str(ROOT / "config/hypr/hyprland.lua")],
                                input=PRELUDE, capture_output=True, text=True, timeout=10)
        cls.stderr = result.stderr
        cls.returncode = result.returncode
        cls.binds = dict(line.split("\t", 1) for line in result.stdout.splitlines() if "\t" in line)

    def test_config_executes_cleanly(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_hardware_keys_drive_fixed_prismctl_actions(self):
        expected = {
            "XF86AudioRaiseVolume": "prismctl action volume-up",
            "XF86AudioLowerVolume": "prismctl action volume-down",
            "XF86AudioMute": "prismctl action mute",
            "XF86AudioMicMute": "prismctl action microphone-mute",
            "XF86MonBrightnessUp": "prismctl action brightness-up",
            "XF86MonBrightnessDown": "prismctl action brightness-down",
        }
        for key, command in expected.items():
            self.assertEqual(self.binds.get(key), command, key)

    def test_window_management_binds_target_the_focused_window(self):
        expected = {
            "SUPER + UP": "prismctl windows maximize active",
            "SUPER + DOWN": "prismctl windows minimize active",
            "SUPER + LEFT": "prismctl windows snap-left active",
            "SUPER + RIGHT": "prismctl windows snap-right active",
            "SUPER + F": "prismctl windows float active",
        }
        for keys, command in expected.items():
            self.assertEqual(self.binds.get(keys), command, keys)

    def test_screenshot_keys_and_night_light_autostart(self):
        self.assertEqual(self.binds.get("SUPER + C"), "prism-shell ipc calculator")
        self.assertEqual(self.binds.get("SUPER + V"), "prism-shell ipc clipboard")
        self.assertIn("prismctl clipboard resume", (ROOT / "config/hypr/hyprland.lua").read_text())
        self.assertEqual(self.binds.get("Print"), "prism-shell ipc screenshot")
        self.assertEqual(self.binds.get("SHIFT + Print"), "prism-shell ipc screenshotFull")
        source = (ROOT / "config/hypr/hyprland.lua").read_text()
        self.assertIn("prismctl action night-light-apply", source)

    def test_every_ipc_target_exists_in_wrapper_and_shell(self):
        targets = {match.split()[-1] for command in self.binds.values()
                   for match in re.findall(r"prism-shell ipc \w+", command)}
        self.assertTrue(targets)
        wrapper = (ROOT / "bin/prism-shell").read_text()
        shell = (ROOT / "shell/shell.qml").read_text()
        for target in targets:
            self.assertRegex(wrapper, rf"\b{target}\b", f"{target} missing from prism-shell")
            self.assertRegex(shell, rf"function {target}\(\)", f"{target} missing from shell IPC")


if __name__ == "__main__":
    unittest.main()
