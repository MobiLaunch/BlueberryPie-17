# PrismOS full-system Expressive coverage

## Scope and truthfulness

PrismOS is an **Arch-based Linux desktop inspired by Android 17**. It is not
Android itself. Preserve the Arch kernel, pacman, BlueZ, NetworkManager, logind,
PipeWire, and XDG permission portals. The objective is to replace *user-facing
desktop chrome and workflows* with an accessible, cohesive Material Expressive
experience, without corrupting ordinary users' personal desktop settings.

Legend: SOURCE = implemented in repository, QA = verified in source CI only,
HARDWARE = real compositor/device testing still required, GAP = missing.

| Surface | Status | Expected next acceptance |
| --- | --- | --- |
| Top bar, wallpaper, dock, app launcher | SOURCE / QA | monitor DPI + touch hardware |
| Quick Settings: Wi-Fi, Bluetooth, brightness, microphone, volume | SOURCE / QA | pairing, secure network, backlight hardware |
| Desktop right-click background menu | SOURCE / QA | right-click positioning and high DPI |
| Dock and launcher app menus | SOURCE / QA | keyboard/long press/right click |
| Prism Store with Linux/Android cards | SOURCE / QA | live F-Droid API and installed apps |
| F-Droid install handoff | SOURCE / QA | check real Android client receives URL intents |
| Android opt-in / spinning setup loader | SOURCE / QA | real polkit, image download, binder |
| Pointer/touchpad/key repeat preferences | SOURCE / QA | Hyprland input device and persistence |
| Connections, display, sound, DND, power in Settings | SOURCE / QA | real changes + focus / layout |
| GTK3/GTK4 and QtQuick Material session skin | SOURCE / QA | Thunar + common Qt clients, light/dark |
| Third-party Electron/libadwaita/Java/Flutter UI | GAP | test each app; no universal style guarantee |
| Native file browser and file selection portals | GAP | build component library, XDG integration |
| Keyboard layouts, IMEs, accessibility, on-screen keyboard | GAP | device-specific settings, ibus/fcitx testing |
| Touch-first window management and tablet gestures | GAP | gesture compositor API and physical touch |
| Printer, display layouts, audio streams, permissions | GAP | settings panels with service APIs |
| Installer, disk manager, Wi-Fi first boot, persistence | GAP | supervised destructive disk QA |
| HCT dynamic material color across GTK/Qt | GAP | implement supported accent handoff, live reapply |
| Secure Android APK trust and seamless native install | GAP | publisher signatures, authorized F-Droid API |
| Notification history, clipboard, share sheet / portal UI | PARTIAL / GAP | full action tests |
| ISO and USB boot | HARDWARE | Arch mkarchiso, real USB, Intel+AMD |

## Rules for future passes

1. All system mutations must use named, allowlisted bridge actions. Never
   interpolate untrusted strings into shell commands or silently obtain root.
2. Android compatibility remains opt-in, with explicit consent for downloads
   and F-Droid installation. F-Droid does security-sensitive installation.
3. Every exposed button must perform a real action or be explicitly disabled
   with an explanation; do not silently invent a working feature.
4. Keep reduced motion, contrast, focus indication, screen reader labels and
   touch targets in every new control. Use shared components.
5. Do not overwrite another desktop session's config or theme and never assume
   GTK/Qt skinning changes Electron, Java, Flutter or libadwaita apps.
6. Run Python unit tests, native QML lint and scenario tests in CI. Record real
   hardware and ISO validation separately in docs/VALIDATION.md.
