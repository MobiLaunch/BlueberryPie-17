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
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("prism-shell")
    hl.exec_cmd("prismctl input apply")
    hl.exec_cmd("prismctl android resume")
    hl.exec_cmd("hypridle --config \"$PRISM_HYPRIDLE_CONFIG\"")
end)
