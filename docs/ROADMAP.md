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
4. Synchronize icon-to-window animation with actual toplevel arrival, including
   slow launches, already-running apps, errors, cancellation and app close.
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
