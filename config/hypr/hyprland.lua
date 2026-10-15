-- PrismOS session for Hyprland 0.56+. Keep this separate from personal configs.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
hl.env("XDG_CURRENT_DESKTOP", "PrismOS:Hyprland")
hl.env("XCURSOR_SIZE", "24")
hl.env("QT_QPA_PLATFORM", "wayland")
hl.config({
    general = {
        gaps_in = 8, gaps_out = 14, border_size = 2, layout = "dwindle",
        col = { active_border = "rgba(8469cfff)", inactive_border = "rgba(d6cddfff)" },
        resize_on_border = true,
    },
    decoration = {
        rounding = 24,
        shadow = { enabled = true, range = 18, render_power = 3, color = 0x221b1425 },
        blur = { enabled = true, size = 6, passes = 3, vibrancy = 0.12 },
    },
    animations = { enabled = true },
    input = { kb_layout = "us", follow_mouse = 1, touchpad = { natural_scroll = true } },
})
hl.curve("prismSpring", { type = "spring", mass = 1, stiffness = 340, damping = 29 })
hl.curve("prismFade", { type = "bezier", points = {{0.2, 0}, {0, 1}} })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 3.2, spring = "prismSpring", style = "popin 90%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.6, bezier = "prismFade", style = "popin 95%" })
hl.animation({ leaf = "fade", enabled = true, speed = 1.6, bezier = "prismFade" })
hl.animation({ leaf = "layers", enabled = false }) -- The shell animates its own panels.
-- Hyprland 0.56 native trackpad gestures: continuous workspace movement
-- plus Android-like 4-finger launcher / Quick Settings reveals.
-- These do not intercept ordinary two-finger app scrolling.
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 4, direction = "up",
    action = function() hl.exec_cmd("prism-shell ipc launcher") end })
hl.gesture({ fingers = 4, direction = "down",
    action = function() hl.exec_cmd("prism-shell ipc shade") end })
hl.bind("SUPER + SPACE", hl.dsp.exec_cmd("prism-shell ipc launcher"))
hl.bind("SUPER + A", hl.dsp.exec_cmd("prism-shell ipc launcher"))
hl.bind("SUPER + Q", hl.dsp.exec_cmd("prism-shell ipc shade"))
hl.bind("SUPER + S", hl.dsp.exec_cmd("prism-shell ipc store"))
-- Window interactions remain available across native and Android windows.
hl.bind("ALT + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("ALT + mouse:273", hl.dsp.window.resize(), { mouse = true })
hl.bind("SUPER + COMMA", hl.dsp.exec_cmd("prism-shell ipc settings"))
hl.bind("SUPER + RETURN", hl.dsp.exec_cmd("foot"))
hl.bind("SUPER + E", hl.dsp.exec_cmd("prism-shell ipc files"))
hl.bind("SUPER + L", hl.dsp.exec_cmd("prismctl action lock"))
hl.bind("SUPER + SHIFT + Q", hl.dsp.window.close())
hl.bind("SUPER + TAB", hl.dsp.exec_cmd("prism-shell ipc recents"))
-- Hardware keys. Wrapped in pcall so a bind option this Hyprland build does not
-- understand can never abort the rest of the session configuration.
local function key_bind(keys, command, options)
    pcall(hl.bind, keys, hl.dsp.exec_cmd(command), options)
end
local held = { locked = true, repeating = true }
-- Window management (acts on the focused window). Super + arrows, Android desktop style.
key_bind("SUPER + UP", "prismctl windows maximize active")
key_bind("SUPER + DOWN", "prismctl windows minimize active")
key_bind("SUPER + LEFT", "prismctl windows snap-left active")
key_bind("SUPER + RIGHT", "prismctl windows snap-right active")
key_bind("SUPER + F", "prismctl windows float active")
key_bind("Print", "prism-shell ipc screenshot")
key_bind("SHIFT + Print", "prism-shell ipc screenshotFull")
key_bind("XF86AudioRaiseVolume", "prismctl action volume-up", held)
key_bind("XF86AudioLowerVolume", "prismctl action volume-down", held)
key_bind("XF86AudioMute", "prismctl action mute", { locked = true })
key_bind("XF86AudioMicMute", "prismctl action microphone-mute", { locked = true })
key_bind("XF86MonBrightnessUp", "prismctl action brightness-up", held)
key_bind("XF86MonBrightnessDown", "prismctl action brightness-down", held)
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("prism-shell")
    hl.exec_cmd("prismctl input apply")
    hl.exec_cmd("prismctl display apply")
    hl.exec_cmd("hyprsunset")
    hl.exec_cmd("sleep 2 && prismctl action night-light-apply")
    hl.exec_cmd("prismctl android resume")
    hl.exec_cmd("hypridle --config \"$PRISM_HYPRIDLE_CONFIG\"")
end)
