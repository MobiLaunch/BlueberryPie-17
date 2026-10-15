# PrismOS roadmap

The objective is a coherent Arch distribution with Android 17-inspired Material
3 Expressive across PrismOS surfaces. Reliability and visual fidelity advance
together: each milestone has a working demo and a clear acceptance gate.

## M0 — The first expressive foundation

Source implemented in this release:

- Shared semantic color roles, four palettes, dark mode and motion preferences.
- Native wallpaper, status bar, dock, app drawer and appearance settings.
- Quick Settings layout, large brightness track, rounded active/inactive tiles,
  volume, footer actions and notifications.
- Real NetworkManager, BlueZ, audio and backlight adapters with error feedback.
- Original vector symbols, abstract wallpaper and morphing loading indicator.
- Native launch splash and compositor animation; browser end-state demonstration.
- Dedicated Arch session, package recipe and upstream releng ISO staging.
- Offline preview, interaction tests and system adapter regression tests.

**Gate:** desktop and phone preview QA, native QML parse, bridge tests. Native
runtime and ISO boot qualification remain open and are recorded separately.

## M1 — Make the desktop dependable on hardware

### v0.2 source slice completed

- Saved favorites, default browser/files/terminal selection, app context menus,
  narrow-screen dock scrolling and notification badges.
- Native tray activation/context menus and MPRIS controls/player selection.
- Notification actions, critical emphasis and bounded in-memory retention.
- Confirmed lock/suspend/logout/restart/shutdown actions and logind capability checks.
- Idle lock configuration, session D-Bus bootstrap, focused-monitor shortcuts
  and monitor unplug recovery.
- Native offscreen component runtime check in Arch CI and additional adapter tests.
- Preview favorites persistence and power confirmation flows.

### v0.3 connectivity and launch slice completed

- Split radio/detail actions on Wi-Fi and Bluetooth tiles.
- Nearby network discovery, signal/security labels, saved profile reuse, masked
  password entry within the selected row, connect/disconnect and bounded refresh.
- Private stdin/password-file transport, revalidated selections, secret cleanup,
  failed-new-profile cleanup and preservation of existing profiles.
- Bluetooth device state, paired-device connect/disconnect and explicit Blueman
  handoff for PIN/confirmation pairing.
- NetworkManager event refresh with polling recovery; editing pauses list refresh.
- Launch readiness from matching Hyprland open/focus events, already-running app
  support, a minimum entrance interval, cancellation and bounded fallback.
- Wireless preview interactions and native offscreen stdin/launch-state coverage.

### v0.4 sound and microphone slice completed

- Separate output/microphone tabs, discovered devices, selected-device labels,
  0–100% levels, independent mute and a default-microphone Quick Settings tile.
- PipeWire JSON discovery, actual default metadata, lifetime serial/name checks
  and structured unavailable/removed-device errors.
- Filtered PipeWire event subscriptions with polling recovery; client-query
  churn is ignored to prevent refresh loops.
- Slider model bindings survive keyboard edits and refresh waits during a drag.
- New microphone/headphone symbols shared by preview and native shell.
- Audio adapter/event tests, native panel/binding checks, preview sound flows and
  a real PipeWire/WirePlumber integration check using isolated virtual endpoints.

Still open: native Bluetooth pairing agent, hidden/enterprise setup in the shell,
full event-driven BlueZ services, per-app stream routing, actual app surface
morphs, third-party theming and compositor/hardware/ISO qualification.
The list below retains the full acceptance scope.

1. Run the packaged session on Arch + Hyprland 0.56/Quickshell 0.3.2.
2. Fix all QML runtime errors and confirm monitor focus, scale and hotplug.
3. Complete Wi-Fi selection and inline password flow; pairing/connected devices.
4. Replace periodic command polling with event-driven service subscriptions.
5. Persist favorites instead of using the first installed apps in the prototype dock.
6. Add tray, microphone/output picker, actual MPRIS media card and power menu.
7. Add notification actions, urgency, history cap and native time updates.
8. Implement lock/idle/session restoration and compositor reduced-motion parity.

**Gate:** network reconnects, Bluetooth recovery, missing hardware, suspend/resume,
1x/1.5x/2x scale, two monitors, and repeated app opening/closing pass on hardware.

## M2 — Match the Android reference carefully

1. Freeze one Android 17 Pixel SystemUI reference version and measurement set.
2. Compare Quick Settings proportions, tile density, spacing, icon weight,
   brightness track, header, page indicators, footer and edit mode directly.
3. Support tile resize/reorder and compact/expanded shade states.
4. Extend event-aware splash readiness to actual app-surface geometry/morphs and
   app-close animation; validate slow launches, already-running apps and errors.
5. Add touch drag physics, dismiss gestures and desktop-friendly overscroll.
6. Replace initial tonal generator with a licensed Material HCT adapter.
7. Themed symbolic icons and font variants (a wallpaper picker with accent extraction shipped in v0.9).

**Gate:** reference comparisons and slow-motion recordings. "Exact" is a measured
acceptance target, not a claim about the first prototype.

## M3 — A bootable distribution

1. Build the ISO on Arch using the staged complete releng profile.
2. Verify UEFI and legacy BIOS, Intel/AMD graphics, laptops and physical USB.
3. Add a first-run wizard: language, keyboard, account, network, accessibility.
4. Build a disk installer with explicit target selection, review and progress.
   *Source slice delivered after v0.9 (`docs/INSTALLER.md`); not yet run on a disk or VM.*
5. Add transactional configuration updates, logs, rollback and recovery shell.
6. Sign packages, publish a distribution repository and record ISO manifests.

**Gate:** clean install in disposable VMs, boot on real hardware, update and
rollback, correct permissions, no UI controls outside the usable screen bounds.

## M4 — Expressive system apps and continuity

Build a small shared component library into Settings, Files, Software, Calendar,
and a media surface. Add portals, GTK/Qt theme bridging and optional Waydroid.
An app store should use the system package APIs; custom browser engines and AI
services can wait until the desktop fundamentals are stable.

**Gate:** shared color/type/motion contracts, keyboard/touch accessibility,
working permissions and predictable error/retry handling across every app.

## v0.5 — Prism Store and Android integration (source slice)

- Native Flathub search, real Flatpak user installs, launch and uninstall.
- Android tab with optional Waydroid container launch; no bundled Android images.
- One-command build.sh wrapper to find real Arch package and assemble ISO.

**Gate:** Full ISO, compositor, Flatpak games and Waydroid on hardware remain unverified.

## M4 / v0.5 native Android slice

- First-run Material Expressive pages and saved opt-in.
- Optional Waydroid initialization via polkit-protected fixed-action helper.
- Native Settings toggle, real staged indeterminate loader and error/retry.
- Quiet session resume for consenting users, without deleting data on opt-out.
- User-triggered F-Droid install/open and regular app-drawer integration.
- Unverified: real image download, binder/kernel compatibility, USB boot,
  compositor transitions and robust F-Droid APK publisher verification.


## v0.8 delivered development slice

- File copy/cut/paste with conflict protection; thumbnail cache.
- Removable USB volume discovery, mount/unmount through UDisks2.
- Initial within-Prism-Files drag-to-copy, pending compositor QA.
- Multi-monitor relative arrangement with overlap validation and 20-second
  reversible preview.
- Trackpad gesture integration with workspace swipe, drawer and Quick Settings.

Follow-on acceptance: boot and run PrismOS on real Arch hardware, test
touchscreen gestures, external displays, live drag/drop, XDG portals, and
review large file transfers, media indexing and hotplug behavior.


## v0.9 delivered development slice

- Material 3 dynamic color (CAM16/HCT Tonal Spot), M3 type, shape and state-layer tokens.
- Rebuilt shared component set; icons recolored at runtime from one original SVG set.
- Quick Settings (large/compact tiles), dual shade, grouped swipe-dismiss notifications,
  heads-up banners, MPRIS card.
- Status bar with live status, running-app dock, ranked launcher, Recents (Super + Tab).
- Settings app (11 sections incl. About and Shortcuts), restyled Files, Store, power
  menu and first-run wizard; theme-following wallpaper; refreshed lock screen.
- Wallpaper picker with accent extraction; hardware volume/brightness/mute keys; offscreen QML runtime harness.

Follow-on acceptance: run the packaged session on real Arch + Hyprland hardware,
verify `hyprctl` focus/close and hardware-key binds, then M2 reference measurements
(Pixel SystemUI proportions), Recents thumbnails, tile edit/reorder,
other Material scheme variants and per-app notification controls.

## Delivered after v0.9 (development slice)

- Window management: caption controls in the status bar, snap/maximize/minimize/float,
  minimized state in the dock and Recents, `Super + arrows/F` binds.
- Desktop widgets (glance, clock, search, calendar, system, analog clock, media, opt-in weather).
- Disk installer (whole disk, UEFI/BIOS, GRUB, polkit helper) and a live-USB entry point.

Follow-on acceptance: run all three on Arch + Hyprland; install into UEFI and BIOS VMs and
on hardware; measure caption-control hit areas against the reference; add resizable
widgets, thumbnails in Recents, an offline install mode and a published package repository.

## Round two (development slice)

- Five Material color schemes, a four-step text size, Quick Settings tile editor and five more tiles.
- Screenshot adapter and keys, per-app notification mute, calculator/timer/stopwatch panel.

Still open from the M2 list: Recents thumbnails (needs a screencopy path), per-tile detail panels,
bit-exact Vibrant/Expressive hue tables, alarms, and measurements against the reference.

## Round three (development slice)

- Alarms with sound, scheduled Do Not Disturb, opt-in clipboard history, unit converter.

Still open: Recents thumbnails, per-tile detail panels, looping alarm ringing screen, snooze,
clipboard search and pinning, world clock.

## Round four (development slice)

- Date & time settings with a 12/24-hour clock, keyboard layout picker, world clock, alarm snooze and ringing banner.

## Round five (development slice)

- Recents window previews, refreshed lock screen, next alarm and timer on the desktop glance.

Still open: per-tile detail panels, clipboard search/pinning, resizable widgets, true live thumbnails
(needs a screencopy client), measurements against the Android reference.

## Round six (development slice)

- Notes widget, Night Light warmth, power modes, clipboard search.

## Round seven (development slice)

- Clipboard pinning, Quick Settings tile detail panels, widget sizes, live Recents when screencopy is available.

## Round eight (development slice)

- Settings Storage page: bounded usage breakdown and clearing of window previews.

Still open: measurements against the Android reference and everything listed under "Not executed" in `docs/VALIDATION.md`.
