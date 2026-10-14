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
7. Add wallpaper picker/extraction, themed symbolic icons and font variants.

**Gate:** reference comparisons and slow-motion recordings. "Exact" is a measured
acceptance target, not a claim about the first prototype.

## M3 — A bootable distribution

1. Build the ISO on Arch using the staged complete releng profile.
2. Verify UEFI and legacy BIOS, Intel/AMD graphics, laptops and physical USB.
3. Add a first-run wizard: language, keyboard, account, network, accessibility.
4. Build a disk installer with explicit target selection, review and progress.
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
