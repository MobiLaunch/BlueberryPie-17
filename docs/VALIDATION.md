# Validation record — 2026-10-14

This record distinguishes source/preview verification from a running desktop and
a bootable distribution. The latter still require an Arch machine or VM.

| Check | Result |
| --- | --- |
| Python bridge, desktop entry, settings, wireless, audio and color regression suite | 77 tests passed |
| CLI on host without Linux hardware tools | Missing services returned structured unavailable/error state |
| Missing percentage CLI input | Structured JSON error; no unhandled traceback |
| QML parser | All 27 native QML files and smoke fixture parsed using Qt 6.12 tooling |
| QML type lint | Checked with official Quickshell 0.3.2 package type definitions; tooling warnings are not hardware qualification |
| Hyprland Lua syntax | Passed through Lua 5.4 parser |
| Shell scripts and PKGBUILD syntax | Passed `bash -n` |
| JavaScript syntax | Passed Node syntax checks |
| Preview interactions | Passed in Chromium 140 through Qt WebEngine / Playwright CDP |
| Desktop preview | Reviewed at 1440 × 900 |
| Phone preview | Reviewed at 390 × 844; shade stays in viewport |
| Arch package layout | `package()` stage installed expected shell, data, Python module and session entry |
| Installed bridge entry point | Staged CLI returned a valid theme |
| Archiso profile staging | Passed against official archiso 91 releng; 14 bootloader files preserved byte for byte |
| Package repository index | Stubbed for staging review; real `repo-add` remains an Arch check |
| Full `makepkg` / dependency resolution | Not run on this Ubuntu host |
| Native offscreen component load | Arch CI covers shared components, wireless panel delegates, private stdin and synthetic launch readiness |
| Launch matching logic | Node checks exact desktop/StartupWMClass matching and comma-containing titles |
| PipeWire event stream | Node checks framing across reads, defaults, partial updates, removals and ignored client churn |
| Virtual audio API integration | Arch CI runs a private PipeWire/WirePlumber policy-only server with four null endpoints |
| Native Quickshell + Hyprland compositor session | Not run |
| Physical Wi-Fi/Bluetooth/audio/backlight writes | Not run on hardware |
| Full ISO build, UEFI/BIOS and USB boot | Not run |
| GitHub repository publication target | MobiLaunch/BlueberryPie-17, branch `main` |

The preview interaction sequence exercised palette switching, dark mode, reduced
motion, app filtering and keyboard launch, terminal input escaping, brightness
updates, notification clearing, empty search results, settings launch and mobile
layout. No JavaScript page errors were observed in the successful run.

Native type lint validates API/property usage but does not prove live D-Bus
ownership, focus grabs, graphics rendering or compositor behavior. Staging checks
do not prove that an ISO boots. These remain M1/M3 acceptance gates in the roadmap.

## Corrections made during this pass

- Added a contrast fallback for saturated palette seeds.
- Restricted brightness queries and writes to backlight devices.
- Normalized malformed preference values and rejected missing percentages.
- Corrected the current Hyprland close dispatcher to `hl.dsp.window.close()`.
- Tinted native SVG symbols for dark surfaces.
- Stopped loading-indicator loops when the launch surface is hidden.
- Added native shade clock refresh and hidden-shade accessibility state in preview.
- Removed the preview dialog's browser-default focus frame; actionable controls
  retain visible keyboard focus.
- Preserved releng boot templates and isolated live/session configuration.

## First native test

Install the package in a current Arch environment, select the PrismOS session,
and inspect `qs log` for component errors. Verify each control against the system
state, then test monitor scale/hotplug, focus, app launch/close and suspend/resume.
Only after these pass should the live ISO and installer milestones advance.

## v0.2 desktop slice

Favorites tests cover saved order, empty docks, duplicates, missing applications,
capacity and concurrent writes. Power tests cover capability denial, fixed command
mapping and current-session-only logout. The native smoke test runs real
Quickshell shared components with an isolated D-Bus/config environment and synthetic
media/notification objects; it never launches apps or changes hardware state.
It does not qualify layer-shell focus, the compositor, actual MPRIS clients,
physical suspend/resume or shutdown. Those remain hardware acceptance gates.

## v0.3 connectivity and launch slice

The wireless suite covers escaped SSIDs/BSSIDs, security type selection, saved
profile reuse, unavailable/disappearing networks, fixed command arguments,
password transport/permissions/cleanup, activation failure cleanup, retained
existing profiles, autoconnect preference failure and BlueZ errors. Commands are
mocked; no test changes physical network or Bluetooth state.

The preview checks inline password validation, simulated connect/disconnect,
password removal/no preference retention, paired-device actions and the phone
connection panel bounds. The native smoke adds actual QProcess stdin transport
to a synthetic subprocess and exercises the production launch state machine
with synthetic window events, minimum timing, existing-window focus and timeout.
It loads both connection panel delegates. This does not prove hardware
authentication, saved-secret reuse, RF discovery, pairing, or real compositor
event timing. Full app-surface morphs are not implemented.

## v0.4 sound and microphone slice

Audio tests cover graph filtering/default metadata, malformed or missing services,
serial/name revalidation, stale node IDs, bounds, explicit mute, command failures
and JSON CLI errors. The event parser is tested with fragmented/concatenated JSON,
quoted brackets, partial updates, removal and client changes that must not cause
query loops. The native smoke loads sound delegates and checks that a slider
keeps its model binding after a local edit and defers reads during adjustment.

The preview exercises device selection, per-device levels, independent microphone
mute and the output/microphone tabs at desktop and phone widths. It is simulated.
The separate integration check uses real PipeWire and WirePlumber APIs on four
private null endpoints, with the policy-only profile and isolated runtime/config/
state. It exercises default changes, level/mute readback, independent microphone
unmute, output switching and removed-device rejection. No physical hardware
monitor is started. Physical sound output/capture, Bluetooth profiles, headset
hotplug, suspend/resume and per-app routing remain hardware acceptance work.

## v0.5 source slice

New store backend tests validate scoped search, install arguments, IDs and explicit remote setup. Not yet tested: live Flathub catalogue, hardware Waydroid/binder, the store QML surface running under Hyprland, Arch ISO build and USB boot. No hardware or boot success is claimed.

## v0.5 first-use Android setup

The new sources implement onboarding consent, a non-privileged user toggle,
an explicitly authorized fixed-purpose polkit helper, streamed setup stages,
a small native loader, optional F-Droid APK installation and session resume.
Source CI validates Python and QML syntax and regressions, but does not
establish a functioning Waydroid session, polkit prompt, successful APK
install or physical ISO/USB boot. No hardware success has been claimed.
