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
local log = {}
local function noop() end
local function descriptor(kind) return function(arg) return { kind = kind, arg = arg } end end
local curves = {}
-- Mirrors the checks Hyprland 0.56 makes on animation curves: a spring needs numeric
-- mass, stiffness and `dampening`; an animation can only name a curve that exists.
local function curve(name, opts)
  if type(name) ~= "string" or type(opts) ~= "table" then error("hl.curve expects a name and a table") end
  if opts.type == "spring" then
    for _, field in ipairs({ "mass", "stiffness", "dampening" }) do
      if type(opts[field]) ~= "number" then error(field .. " expects a number") end
    end
  elseif opts.type == "bezier" then
    if type(opts.points) ~= "table" or #opts.points < 2 then error("points expects two control points") end
  else
    error("unknown curve type")
  end
  curves[name] = opts.type
  log[#log + 1] = "curve\t" .. name .. "\t" .. opts.type
end
local function animation(opts)
  if type(opts.leaf) ~= "string" then error("leaf expects a string") end
  if opts.spring and curves[opts.spring] ~= "spring" then error("no such spring " .. tostring(opts.spring)) end
  if opts.bezier and curves[opts.bezier] ~= "bezier" then error("no such bezier " .. tostring(opts.bezier)) end
  log[#log + 1] = "animation\t" .. opts.leaf .. "\t" .. tostring(opts.spring or opts.bezier or "-")
end
local DIRECTIONS = { up = true, down = true, left = true, right = true, horizontal = true, vertical = true, pinch = true }
local function gesture(opts)
  if type(opts.fingers) ~= "number" or opts.fingers < 2 or opts.fingers > 5 then error("fingers expects 2-5") end
  if not DIRECTIONS[opts.direction] then error("unknown direction " .. tostring(opts.direction)) end
  if type(opts.action) ~= "string" and type(opts.action) ~= "function" then error("action expects a string or function") end
  local commands = {}
  if type(opts.action) == "function" then
    local real = hl.exec_cmd
    hl.exec_cmd = function(cmd) commands[#commands + 1] = cmd end
    opts.action()
    hl.exec_cmd = real
  end
  log[#log + 1] = "gesture\t" .. opts.fingers .. "\t" .. opts.direction .. "\t" .. (commands[1] or tostring(opts.action))
end
hl = {
  monitor = noop, env = noop, config = noop, curve = curve, animation = animation, gesture = gesture,
  on = function(event) log[#log + 1] = "on\t" .. event end,
  exec_cmd = noop,
  bind = function(keys, action, options)
    binds[#binds + 1] = keys .. "\t" .. tostring(action and (action.arg or action.kind) or "?")
  end,
  dsp = { exec_cmd = descriptor("exec"),
          window = { drag = descriptor("drag"), resize = descriptor("resize"), close = descriptor("close") } },
}
if arg[2] then dofile(arg[2]) end  -- optional sabotage: make some API calls fail
dofile(arg[1])
for _, line in ipairs(binds) do print(line) end
for _, line in ipairs(log) do print("@" .. line) end
'''


def run_config(path, sabotage=None):
    """Run the config against the mock; `sabotage` is Lua that runs first (to make API calls fail)."""
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        extra = []
        if sabotage:
            script = Path(folder) / "sabotage.lua"
            script.write_text(sabotage)
            extra = [str(script)]
        return subprocess.run([LUA, "-", str(path), *extra], input=PRELUDE, capture_output=True, text=True, timeout=10)


@unittest.skipIf(LUA is None, "lua interpreter not installed")
class HyprlandConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = run_config(ROOT / "config/hypr/hyprland.lua")
        cls.stderr = result.stderr
        cls.returncode = result.returncode
        cls.binds = dict(line.split("\t", 1) for line in result.stdout.splitlines()
                         if "\t" in line and not line.startswith("@"))
        cls.log = [line[1:].split("\t") for line in result.stdout.splitlines() if line.startswith("@")]

    def test_config_executes_cleanly(self):
        self.assertEqual(self.returncode, 0, self.stderr)

    def test_window_open_animation_uses_a_spring_that_exists(self):
        self.assertIn(["curve", "prismSpring", "spring"], self.log)
        self.assertIn(["animation", "windowsIn", "prismSpring"], self.log)

    def test_spring_uses_the_field_name_hyprland_expects(self):
        source = (ROOT / "config/hypr/hyprland.lua").read_text()
        self.assertIn("dampening =", source)
        self.assertNotRegex(source, r"\bdamping\s*=")

    def test_a_refused_spring_falls_back_to_a_bezier_without_breaking_the_session(self):
        import tempfile
        source = (ROOT / "config/hypr/hyprland.lua").read_text().replace("dampening =", "damping =")
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / "broken.lua"
            broken.write_text(source)
            result = run_config(broken)
        self.assertEqual(result.returncode, 0, result.stderr)
        log = [line[1:].split("\t") for line in result.stdout.splitlines() if line.startswith("@")]
        self.assertNotIn(["curve", "prismSpring", "spring"], log)
        self.assertIn(["animation", "windowsIn", "prismFade"], log)
        self.assertIn("SUPER + SPACE", result.stdout, "binds after the animations still run")

    def test_autostart_and_binds_survive_every_new_api_being_refused(self):
        sabotage = """
            local real_curve = hl.curve
            hl.curve = function() error("curves are not supported here") end
            hl.animation = function() error("animations are not supported here") end
            hl.gesture = function() error("gestures are not supported here") end
        """
        result = run_config(ROOT / "config/hypr/hyprland.lua", sabotage)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("@on\thyprland.start", result.stdout, "the shell must still be started")
        self.assertIn("SUPER + SPACE", result.stdout)
        self.assertIn("XF86AudioRaiseVolume", result.stdout)

    def test_hardware_keys_drive_fixed_prismctl_actions(self):
        # Through the shell (which shows the indicator), falling back to the bridge when it is not running.
        expected = {
            "XF86AudioRaiseVolume": "prism-shell ipc volumeUp || prismctl action volume-up",
            "XF86AudioLowerVolume": "prism-shell ipc volumeDown || prismctl action volume-down",
            "XF86AudioMute": "prism-shell ipc volumeMute || prismctl action mute",
            "XF86AudioMicMute": "prism-shell ipc micMute || prismctl action microphone-mute",
            "XF86MonBrightnessUp": "prism-shell ipc brightnessUp || prismctl action brightness-up",
            "XF86MonBrightnessDown": "prism-shell ipc brightnessDown || prismctl action brightness-down",
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

    def test_touchpad_gestures_are_valid_and_reach_the_shell(self):
        gestures = {(fingers, direction): command for kind, fingers, direction, command in
                    (row for row in self.log if row[0] == "gesture")}
        self.assertEqual(gestures[("3", "horizontal")], "workspace")
        self.assertEqual(gestures[("3", "up")], "prism-shell ipc recents")
        self.assertEqual(gestures[("3", "down")], "prism-shell ipc home || prismctl windows show-desktop")
        self.assertEqual(gestures[("4", "up")], "prism-shell ipc launcher")
        self.assertEqual(gestures[("4", "down")], "prism-shell ipc shade")

    def test_home_key_shows_the_desktop_even_without_the_shell(self):
        self.assertEqual(self.binds.get("SUPER + D"), "prism-shell ipc home || prismctl windows show-desktop")

    def test_screenshot_keys_and_night_light_autostart(self):
        self.assertEqual(self.binds.get("SUPER + C"), "prism-shell ipc calculator")
        self.assertEqual(self.binds.get("SUPER + V"), "prism-shell ipc clipboard")
        self.assertIn("prismctl clipboard resume", (ROOT / "config/hypr/hyprland.lua").read_text())
        self.assertEqual(self.binds.get("Print"), "prism-shell ipc screenshot")
        self.assertEqual(self.binds.get("SHIFT + Print"), "prism-shell ipc screenshotFull")
        self.assertEqual(self.binds.get("SUPER + SHIFT + R"), "prism-shell ipc record")
        source = (ROOT / "config/hypr/hyprland.lua").read_text()
        self.assertIn("prismctl action night-light-apply", source)

    def test_every_ipc_target_exists_in_wrapper_and_shell(self):
        targets = {match.split()[-1] for command in self.binds.values()
                   for match in re.findall(r"prism-shell ipc \w+", command)}
        self.assertTrue({"volumeUp", "volumeDown", "volumeMute", "micMute", "brightnessUp", "brightnessDown"} <= targets)
        self.assertTrue(targets)
        wrapper = (ROOT / "bin/prism-shell").read_text()
        shell = (ROOT / "shell/shell.qml").read_text()
        for target in targets:
            self.assertRegex(wrapper, rf"\b{target}\b", f"{target} missing from prism-shell")
            self.assertRegex(shell, rf"function {target}\(\)", f"{target} missing from shell IPC")


if __name__ == "__main__":
    unittest.main()
