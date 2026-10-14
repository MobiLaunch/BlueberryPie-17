# Validation record — 2026-10-14

This record distinguishes source/preview verification from a running desktop and
a bootable distribution. The latter still require an Arch machine or VM.

| Check | Result |
| --- | --- |
| Python bridge, desktop entry, settings and color regression suite | 27 tests passed |
| CLI on host without Linux hardware tools | Missing services returned structured unavailable/error state |
| Missing percentage CLI input | Structured JSON error; no unhandled traceback |
| QML parser | All 16 native QML files parsed using Qt 6.12 tooling |
| QML type lint | All 16 files passed with official Quickshell 0.3.2 package type definitions |
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
