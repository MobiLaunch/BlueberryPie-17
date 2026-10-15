# Validation record — 2026-10-15 (v0.9 through round three)

## Addendum: round three (alarms, quiet hours, clipboard history, converter)

### Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` | Python suites, Node specs (calculator and unit converter parsers), shell syntax and the QML runtime suite passed |
| Alarms | Adapter tests (validation, id reuse, limit, corrupt-file filtering, argv-only sound player); in the shell, a due alarm toasted once, asked for the sound and switched itself off; adding from the panel persisted |
| Quiet hours | Banners suppressed inside the window (including a window spanning midnight in the Python/QML logic), shown outside it and when disabled; edited from Settings through the bridge |
| Clipboard history | Adapter tests with mocked `cliphist`/`wl-copy` (numeric ids only, no shell, delete by original line, watcher pids verified by `/proc/PID/cmdline` before signalling); the pane explains missing tools and copies by id |
| Converter | Spec covers every category, round trips, decimal commas, absolute zero and prototype-name rejection; clicked through in the shell |

### Not executed

- Real `cliphist`, `wl-paste --watch` and `wl-copy`; real `pw-play`/`paplay` with the sound theme.
- Alarm ringing across a suspend/resume or while the screen is locked; the sound is a single short clip, not a looping alarm.
- Quiet hours over a real day/night boundary (tests use windows around "now").

## Previous record (through round two)

## Addendum: round two (schemes, tiles, screenshots, notifications, utilities)

### Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` | 308 Python tests passed, 0 skipped; Node specs (including the new calculator parser spec) passed; `qmlformat` accepted all QML files |
| Color schemes | Contrast ≥ 4.5:1 for nine role pairs × 5 schemes × 8 seeds × light/dark; monochrome stays gray; invalid scheme names refused |
| Text size at Largest | Every surface and Settings section opened with no QML errors or elided text (this found and fixed truncation in Quick Settings tiles and the Settings sidebar) |
| Tile editor, mute, screenshot tile | Clicked through the offscreen shell; tile layout persisted by `prismctl tiles`; muted app dropped, critical alert shown; the screenshot tile ran `prismctl screenshot area` |
| Airplane, Battery Saver, Night Light, screenshots | Adapters tested with mocked `nmcli`, `bluetoothctl`, `powerprofilesctl`, `hyprctl hyprsunset`, `grim`, `slurp` (argv lists, region pattern, failure does not persist state) |
| Calculator | Parser spec (precedence, functions, errors, hostile text never executed) and a typed/clicked session in the shell |
| Timer / stopwatch | Countdown, finish toast, laps and pause stability in the shell |

### Not executed

- Real `grim`/`slurp`/`wl-copy`, `hyprsunset`, `powerprofilesctl` and rfkill-style radio toggles on hardware.
- `hyprctl hyprsunset ...` IPC names and the `Print` binds under Hyprland 0.56 with a Lua config.
- Notification muting against real clients (a stub server only).
- Timer sound and alarms do not exist yet.

## Previous addendum — 2026-10-15 (v0.9 + window management, widgets, installer)

## Addendum: window controls, desktop widgets, disk installer

### Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` | 270 Python tests passed, 0 skipped (PySide6, Lua and Pillow present); shell, PKGBUILD, Node and compile checks passed |
| `qmlformat` over all 92 QML files | Pass (the `check.sh` QML step still skips without Qt's own `qmlformat`) |
| Window adapter (`prismos/windows.py`) with mocked `hyprctl`: focus, close, minimize, restore, maximize, float, snap | Argument lists, refusal of bad addresses/minimized snaps/too-small areas and the `special:minimized` workspace checked |
| Caption controls clicked in the offscreen shell | Buttons call the adapter with the focused address; snap menu opens; no QML errors or elided text |
| `config/hypr/hyprland.lua` against a mock `hl` | New `Super + arrow/F` binds exist and map to `prismctl windows ...` |
| Widgets: adapters (`stats`, `weather`, `widgets`, `websearch`) and every widget rendered | Weather host allowlist, no-redirect and size bounds, cache, WMO mapping; light and dark screenshots reviewed; search hands off to the launcher |
| Installer engine with a recording host | Disk eligibility (live USB incl. label/ISO 9660, mounted, read-only, small, zram/loop), strict request validation, typed confirmation, UEFI/BIOS/NVMe layouts, argv-only commands, password only on `chpasswd` stdin, step ordering, failure → unmount, optional steps, progress, write containment, pacman.conf generation |
| Installer wizard clicked through in the offscreen shell | Every page, unusable disks unselectable, password mismatch, typed confirmation gate, progress, success and failure/return; the password reached the process on stdin and never in argv; light and dark screenshots reviewed |

### Not executed — still open

- **Any real installation.** No partition table, filesystem, `pacstrap`, `arch-chroot`,
  `grub-install` or `efibootmgr` call has run. The installer's commands are asserted as
  data, not executed. Needs UEFI and BIOS VMs, NVMe/virtio/SATA, failure and retry, and
  hardware.
- **polkit on the live session**: the prompt, the admin identity and `pkexec` stdin/stdout
  passing are unverified. The package/ISO changes (`/opt/prismos/repo`, the desktop entry,
  extra packages) are unbuilt.
- **`hyprctl dispatch` names** `movetoworkspacesilent`, `resizewindowpixel`,
  `movewindowpixel`, `fullscreen 1`, `togglefloating` and the `special:minimized`
  workspace on Hyprland 0.56 with a Lua config; the adapter reports a rejected dispatch
  and leaves windows untouched. Snap uses the monitor's reserved area and may disagree
  with real gaps.
- **Weather over the network** (only fixtures were used); CPU/memory/storage values on
  real machines; widget layout on real monitors and at fractional scales.
- **Hyprland keyboard layout** via `input:kb_layout` / `input:kb_variant` at session start.
- Windows are not exercised under a real compositor; the harness stubs layer-shell.

## Earlier record — v0.9 shell pass

This pass rebuilt most of the native shell. A new **offscreen QML runtime harness**
(`tests/qml_runtime/`) loads the real `shell/` QML with *stub* Quickshell modules
under plain Qt Quick (PySide6 / Qt 6.12, software renderer, offscreen platform),
runs the genuine `prismctl` bridge against an isolated config, and can screenshot
the composited desktop. It finds binding, reference and layout errors without a
compositor. **It is an approximation, not Quickshell or Hyprland qualification.**

## Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` (Python suites, shell syntax, Node specs, QML syntax) | 186 tests passed; 0 skipped with Qt, Lua and Pillow present (on a bare host the runtime and Lua tests skip) |
| HCT color engine against published Material Tonal Spot values (seed `#6750A4`) | Roles matched the reference scheme within 2/255 per channel; tone round-trips within 0.6 L* |
| Contrast pairs (primary, containers, error, surface, inverse; 6 seeds × light/dark) | All ≥ 4.5:1 |
| Real shell QML under the harness | Loads with zero QML errors; every surface (Quick Settings, launcher, Settings, Files, Store, power, Recents, first run) opens without errors |
| Elided or clipped text on every surface | None (automated item-tree scan) |
| Settings: all 11 sections loaded by clicking their rows | No errors, no elided text |
| First-run wizard clicked through to completion | `prismctl welcome finish` ran; `onboarding_complete` persisted |
| Notifications: grouping, swipe-target, dismiss, banner, Do Not Disturb, critical break-through | Pass |
| Wallpaper picker: list, choose, accent extraction, path/symlink/size rejection | Pass (adapter tests and a clicked-through runtime test) |
| Dark theme legibility | Ink roles resolve to scheme values; dark surface is dark, text is light |
| `tests/native-smoke.qml` (the fixture CI runs on real Quickshell) | `PRISM_NATIVE_SMOKE_OK` under stub modules |
| `config/hypr/hyprland.lua` | Lua 5.4 parse; executed against a mock `hl`; every bind checked against the shell IPC and `prism-shell` allowlist |
| `qmlformat` over 72 QML files | Pass |
| `qmllint` with stub type roots | 0 errors (warnings remain; real-type lint runs in Arch CI) |
| Browser preview interactions (Playwright 1.56.1, Chromium 1194) | Passed with regenerated Material 3 tokens |
| Generated assets reproducible (`generate-design.py`) | No diff |

## Not executed — treat as open

- **Native Quickshell + Hyprland session.** Layer-shell focus, `HyprlandFocusGrab`,
  stacking of overlays over the dock, input regions and monitor hotplug are
  stubbed in the harness.
- **Hyprland control calls.** `hyprctl dispatch focuswindow|closewindow` (dock,
  Recents) is unverified on Hyprland 0.56 with a Lua config; failures surface as
  a toast and leave windows untouched. Bind options `locked`/`repeating` for
  hardware keys are unverified; the binds are `pcall`-guarded so an unsupported
  option cannot break the session config.
- **Hardware keys, touchpad gestures, brightness/volume steps** on real devices.
- **`hyprlock` configuration** (new layout): not run; it uses documented options only.
- **GPU rendering.** All screenshots are from the software renderer. Icons are
  recolored SVG data URIs (no shader effects) and should render the same on GL.
- **Fonts.** The harness host lacks Roboto/Google Sans Flex and fell back to Inter;
  metrics on Arch with Roboto may differ slightly (labels are measured, not guessed).
- **Real MPRIS, tray and notification clients** (stubs only), PipeWire/NetworkManager/
  BlueZ writes (hosts lacked them), Waydroid, Flatpak.
- **ISO build and boot, `makepkg`.** Not run on this host.
- **Publication.** These commits were made locally; the push was refused because the
  session lacked GitHub access to the repository.

## Defects found and fixed this pass

- Every button label was clipped: Qt's Material `Button` pins 24/16 px padding that
  `PillButton` did not budget for. Close (`×`) and tile chevrons had zero content width.
- Inside `components/`, `Label` resolved to `QtQuick.Controls.Label`, so shared
  components never used the Theme font or color for text.
- **Content-color roles (`onPrimary`, `onSurface`, …) silently evaluated to black.** A
  property named `onX` beside a property `x` loses its binding in Qt 6.12. Default
  text was therefore black on every surface, which is unreadable in dark mode. The
  roles are now `*Ink` (for example `Theme.surfaceInk`) and covered by a test.
- The dock was 62 px too narrow, clipping its last button for any number of favorites.
- A stray "Prism Store" button overlapped the app drawer header, and the Settings page
  was one long mixed scroll. (While rebuilding, the harness also caught `ToggleRow`
  redeclaring `Button`'s final `checked` property before it shipped.)

## Previous record — 2026-10-14 (v0.8)

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

## v0.6 Expressive system coverage (source scope)

Implemented F-Droid display-only discovery, Android package detail handoff,
shared Linux/Android store results, editable pointer/touchpad/repeat preferences,
shared input/menu visuals, desktop context menu, consolidated system settings,
and session-scoped GTK3/GTK4 and QtQuick Material skins. The eight packaged
GTK palettes are checked by unit tests. CI validates syntax and service
adapters, not real USB boot or Waydroid/GTK application rendering. Third-party
apps may not use the session theme. See docs/EXPRESSIVE-COVERAGE.md for the
remaining work required before claiming full user-facing consistency.


## v0.7 file/portal/display milestone

Code: native Prism Files frontend/backend, bounded directory listing, safe
renames (including symlinks), no-shell GIO Trash, per-session XDG portal
configuration and a managed PrismOS Hyprland session file.
Display scaling has real-hardware monitor discovery, choices based on physical
resolution and an explicit 20-second confirmation/automatic rollback.

Unit tests cover file operations, safe paths, display input validation,
rolled-back vs confirmed scaling, and persistent prefs. CI source and native
QML checks do **not** qualify physical multi-monitor transitions or prove
Waydroid and GTK portals work on a real ISO. Full device QA pending.


## v0.8 source validation versus hardware

Unit test coverage expanded to local file copying/cutting/pasting, collision
and subfolder guards, symlink copy, image thumbnail caching, removable volume
filtering, safe UDisks2 calls, display relative placement, collision checks
and confirmation rollback. Native Qt lint and the existing UI interaction
tests run in GitHub Actions. The optional internal drag-and-drop interaction
is NOT certified on real hardware, and no Arch ISO, USB mount, display-hotplug,
or touchpad/touchscreen gesture was exercised from this environment.

### v0.8 wallpaper touch gestures

A device-filtered Qt Quick DragHandler captures upward/downward gestures
originating on empty wallpaper. It does not capture app touches. This remains
unqualified on physical touchscreen hardware; mouse/touch drag behavior and
Wayland gesture inhibition still require live testing.
