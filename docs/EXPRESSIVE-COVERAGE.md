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
| Status bar, theme-following wallpaper, running-app dock, ranked launcher | SOURCE / QA | monitor DPI + touch hardware |
| Window caption controls, snap, minimize / restore, float | SOURCE / QA | `hyprctl dispatch` names and `special:minimized` unverified on Hyprland 0.56 Lua; snap math assumes the monitor's reserved area |
| Desktop widgets (glance, clock, search, calendar, system, analog, media, weather) | SOURCE / QA | classic-style original designs; weather network path and layout on real monitors unverified |
| Disk installer wizard + polkit helper | SOURCE / QA | never run on a disk; needs UEFI/BIOS VM and hardware passes (`docs/INSTALLER.md`) |
| Color schemes (5) and text size | SOURCE / QA | Vibrant/Expressive hues approximate Material's tables |
| Quick Settings tile editor; airplane, battery saver, night light, screenshot, lock tiles | SOURCE / QA | needs power-profiles-daemon, hyprsunset, grim/slurp on hardware |
| Per-app notification mute | SOURCE / QA | real notification clients |
| Calculator, timer, stopwatch | SOURCE / QA | no alarms; timer has no sound |
| Alarms, quiet hours, clipboard history, converter | SOURCE / QA | no snooze or looping ringer; real cliphist and audio unverified |
| Date & time page, 12/24-hour clock, keyboard layouts, world clock, ringing banner | SOURCE / QA | timedatectl/polkit and live layout changes unverified |
| Lock screen layout and glance alarm/timer | SOURCE / QA | hyprlock rendering unverified |
| Recents overview (windows via hyprctl) with window previews | SOURCE / QA | verify focus/close dispatch and grim captures on Hyprland 0.56 Lua; previews are snapshots, not live |
| Heads-up banners and grouped swipe-dismiss shade | SOURCE / QA | real notification clients, long text, many apps |
| Settings app (11 sections) | SOURCE / QA | real adapters on hardware; per-app notification controls missing |
| Hardware volume / brightness / mute keys | SOURCE | real keyboard; bind flags unverified |
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
| Native file browser | SOURCE / QA | validate drag-drop, USB devices and large folder performance |
| XDG file chooser portals | SOURCE / QA | GTK portal open/save from web browser and sandboxed apps |
| Keyboard layouts, IMEs, accessibility, on-screen keyboard | GAP | device-specific settings, ibus/fcitx testing |
| Touchpad swipe gestures | SOURCE / QA | compatible touchpad hardware, input inhibitors and focus checks |
| Touchscreen edge swipes and tablet layout | GAP | dedicated touch input and tablet hardware QA |
| Display scaling and arrangement with rollback | SOURCE / QA | physical multi-monitor hotplug and arrangement checks |
| Printer, monitor arrangement, audio streams, permissions | GAP | settings panels with service APIs |
| Installer, disk manager, Wi-Fi first boot, persistence | GAP | supervised destructive disk QA |
| HCT dynamic material color in the shell | SOURCE / QA | other scheme variants (Vibrant, Expressive); GTK/Qt accent handoff stays a GAP |
| Dynamic color across GTK/Qt/Electron apps | GAP | supported accent handoff, live reapply |
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


## v0.7 experience integration

- Prism Files: bookmarks, navigation, search/filter, create folder, rename,
  open with default association, Trash confirmation and themed menus. File
  operations use user permissions and argv-only subprocesses.
- Fixed XDG file chooser portal fallback for a PrismOS-specific session.
- Display scaling: supported monitor scales are calculated from actual
  compositor resolution. A monitored 20-second preview reverts unless explicitly
  confirmed, then saves settings for PrismOS logins.
- Hyprland session now launches the shipped config, not an obsolete copied
  default from v0.6. Existing personal files are preserved, and advanced users
  can opt into a custom PrismOS config with PRISM_HYPRLAND_CONFIG.
- Pending: physical boot, removable-media mounting, thumbnailing, file drag,
  cut/copy/paste, advanced display arrangements, external file picker rendering.


## v0.8 engineering status

- File copy/cut/paste: per-user short-lived clipboard, no silent overwrite;
  symlink preservation and self-copy guard; explicit GIO cut/move.
- Local picture thumbnails: cached PNGs, bounded original size and 30/visit cap.
- Removable drives: user-scoped `lsblk` discovery and
  `udisksctl mount/unmount` with standard polkit decisions.
- Internal Prism Files drag-and-drop: initial UI with Qt Quick DropArea; not
  yet qualified on a live compositor for mouse and touchscreen.
- Relative multi-monitor placement: edge alignment, overlap rejection,
  confirmation and rollback, per-user persistence.
- Touchpad: 3-finger workspace transition and 4-finger drawer/quick panel
  through Hyprland Lua gestures.
- Still open: robust large file transfer progress/cancellation, copy conflict
  rename resolution, removable-drive hotplug push notifications, drag across
  processes, actual touchscreen edge gestures, display rotation/duplicate mode
  with rollback, and real hardware testing.


## v0.9 engineering status

- Color: validated CAM16/HCT Tonal Spot with the full M3 role set; `*Ink` content roles
  (an `onX` property naming collision made default text black in Qt 6.12).
- UI: the harness-detected defects (clipped labels, 62 px dock overflow, black text in
  dark mode, glyph icons) are fixed and covered by tests that scan the live item tree.
- Wallpaper picker (home pictures, accent extraction) is SOURCE / QA; videos, folders
  outside `~/Pictures`, and per-monitor wallpapers are not supported.
- Open: Recents thumbnails (needs screencopy), Quick Settings edit/reorder, notification history persistence, on-screen keyboard and accessibility
  settings, and every hardware or compositor check listed in `docs/VALIDATION.md`.
