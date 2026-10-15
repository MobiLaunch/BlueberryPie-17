# Validation record — 2026-10-15 (v0.9 through round eleven)

## Addendum: round eleven (closing the Android gaps)

### Slice 1: volume and brightness indicator — executed

| Check | Result |
| --- | --- |
| Key binds | Each hardware key runs `prism-shell ipc <target> \|\| prismctl action <fallback>`; every target exists in the wrapper allowlist and the shell's IPC handler |
| Indicator | Volume up, down, mute, microphone mute and brightness each show the right level or "Muted" straight after the press; brightness stops at 1%; it hides itself; nothing is shown when the control is missing (the command reports why); no elided text |
| Writes | Toggles and steps are never merged; slider values for the same control are (first and last run, middle superseded) |

### Not executed

- Real hardware keys, a real Hyprland `exec` of the `||` fallback, and the feel of a held key on real audio and backlight devices.

### Slice 2: notification reply, snooze and lock screen count — executed

| Check | Result |
| --- | --- |
| Inline reply | The server advertises reply support; only a notification that accepts replies shows the box; the trimmed text reaches the sending app; "Reply sent" shows and the card clears itself; the heads-up banner never offers a reply (it cannot take keyboard focus) |
| Snooze | Important notifications have no snooze; the chips set 15 / 60 / 240 minutes; a snoozed one leaves the shade and the count while the sender's notification stays alive; when its time is up it returns with a banner; clearing forgets snoozes |
| Lock screen count | The bridge stores only a number (0600 file in a 0700 runtime directory, atomic, bounded 0 to 999, bad or damaged values read as 0); the shell writes 0 at start and the count after each change; the summary is plain text for hyprlock and empty when off or zero; turning it off in Settings empties it; no notification text is ever stored |

### Slice 3: hotspot and VPN tiles — executed

| Check | Result |
| --- | --- |
| Hotspot adapter | Names (1 to 32 bytes) and passwords (8 to 63 printable ASCII) are validated; the first password is generated, saved and then reused, so the one shown, copied and used to start the hotspot is the same; the file is 0600 in a 0700 folder; turning it on never puts the password in a command line (a 0600 password file that is removed afterwards carries it) and marks the profile so NetworkManager keeps no copy; failures give fixed messages that do not echo settings; missing `dnsmasq`, no Wi-Fi adapter and no AP support are reported plainly; turning off only acts when it is on; changing the name or password applies next time and a running hotspot is not touched; copying uses a pipe |
| VPN adapter | Only `vpn` and `wireguard` profiles with real UUIDs are listed (names may contain colons); toggling disconnects an active VPN or connects the chosen (else first) one; unknown or malformed choices are refused before any command runs; "secrets were required" becomes a helpful message; a corrupt saved choice is ignored |
| Status | Hotspot and VPN come from the same single `nmcli` call as the other connection state; a missing `nmcli` marks both unavailable |
| Tiles | Both tiles toggle with an immediate predicted state; they run on their own write queue; the hotspot details hide the password until asked, copy it, switch off, make a new one and forget the password when closed (including when a late reply arrives after closing); the VPN details connect and disconnect profiles; with no VPN set up the tile opens an explanation; both sections appear in Settings → Network; no elided text |

### Not executed

- Real NetworkManager: hotspot activation with `passwd-file` and `psk-flags 2` (the fake `nmcli` accepts it), NAT through `dnsmasq` and firewall rules, single-radio adapters dropping their Wi-Fi, WPA3 hotspots, VPN plugins that prompt for secrets, and Quick Settings latency with a real VPN. The runtime tests use a small fake `nmcli`.

### Slice 4: screen recording — executed

| Check | Result |
| --- | --- |
| Recorder | With a stand-in `wf-recorder` that really runs and finishes on SIGINT: start, status with elapsed time, refusal of a second recording, stop saving a non-empty file, state file removed; files in `Videos/Screen recordings`, never overwriting (`-2`); a stale state file or a live process that is not a recorder is never signalled; a recorder that exits at once is reported and leaves no state |
| Arguments | Full screen uses the focused output (or lets the recorder choose when `hyprctl` is absent); an area comes from `slurp` and must match a strict region pattern (anything else counts as cancelled); a window uses its box from `hyprctl`; microphone audio is added only when switched on |
| Shell | The tile starts a recording after the shade has closed, the top-bar chip appears with an `m:ss` timer, pressing it stops at once and a "saved" toast follows with the file present; without `wf-recorder` the tile says what is missing and the details explain it; `Super + Shift + R` reaches the shell |

### Not executed

- A real `wf-recorder` under Hyprland (portal and screencopy permissions, codecs, audio devices, large recordings, GPU load), and what happens to a recording if the session ends abruptly.

### Slice 5: app info — executed

| Check | Result |
| --- | --- |
| Adapter | Pacman apps show package, version and size plus a copyable `sudo pacman -Rns` command and are never uninstalled; a user Flatpak is removable with the fixed command `flatpak uninstall --user -y --noninteractive ID`; a system Flatpak only shows a command; unknown or malformed desktop IDs are refused before any command runs; running state matches windows by class like the dock |
| Force stop | With real child processes: a polite one ends on SIGTERM, one that ignores SIGTERM is killed after the grace period; the shell, the bridge, PID 1, other users' processes, protected names and processes that no longer exist are never signalled; stopping an app that is not running is an error |
| Copy | Only the generated command (never caller text) is written to `wl-copy`; nothing to copy for removable apps |
| Shell | The page opens from the app menu, shows name, status and source rows, Force stop works against a real process through a fake `hyprctl`, a user Flatpak is removed only after the confirm step, a slow earlier read can no longer overwrite the page of the app opened next, no elided text |

### Not executed (slice 5)

- Real Hyprland window PIDs (Flatpak sandboxes report the sandbox's PID namespace, so force stop may not reach a sandboxed app), a real `flatpak uninstall` and `pacman -Qo/-Qi` output across versions and locales.

### Slice 6: gestures, Home and split screen — executed

| Check | Result |
| --- | --- |
| Show desktop | Hides only the visible windows of the current workspace and remembers them in a private runtime file; the second press restores exactly those (skipping ones that closed or were minimized earlier); nothing to do when the workspace is empty; a corrupt or hostile state file is ignored |
| Split | Brings both windows to the current workspace silently, snaps the first left and the second right with the existing snap geometry, focuses the second; the same window twice, unknown, malformed or injected addresses are refused before any dispatch |
| Config | The Lua mock now validates `hl.gesture` (finger count, direction, action) and runs each gesture action: 3-finger up/down reach `prism-shell ipc recents`/`home`, `Super + D` falls back to `prismctl windows show-desktop`; refused gesture APIs still leave binds and autostart intact |
| Shell | Home closes an open panel first and only then shows the desktop; Recents split buttons choose a first then a second card (cancelable, Esc) and issue one `windows split` request |

### Not executed (slice 6)

- Real touchpad swipes (libinput finger counts, conflicts with app gestures), `hyprctl dispatch` behaviour for `movetoworkspacesilent` with `special:minimized` on a Lua-configured Hyprland, and the look of tiled windows being floated into halves.

### Slice 7: Focus mode — executed

| Check | Result |
| --- | --- |
| Settings | `focus` and `focus_apps` default off/empty, load validated (non-boolean flag, control characters, duplicates, overlong names dropped), toggle through the bridge, app list separate from the muted list, 50-app cap, bad names/flags refused |
| Tile | In the tile catalog; answers at once with "N apps paused"; with no apps chosen it opens Settings → Notifications instead of switching on |
| Notifications | While on, a chosen app gets no banner yet still appears in the shade; other apps and critical notifications still banner; turning it off restores banners; per-app switches in the Settings page persist |

### Not executed (slice 7)

- A schedule or timer for Focus mode, pausing the apps themselves (only their notifications are quieted), and notification sounds (the shell has no per-notification sound path to silence).

### Slice 8: software update — executed

| Check | Result |
| --- | --- |
| Adapter | Only well-formed `name old -> new` lines and Flatpak IDs are kept (injected names, broken lines dropped), sorted and capped; exit code 2 means "nothing to update"; errors and timeouts are reported per source; missing tools are explained and both missing is an error; checking runs only `checkupdates` and `flatpak remote-ls --updates` |
| Cache | The last result is stored 0600 in a 0700 folder, read back validated, and a corrupt file is ignored |
| Install | Opens `foot` on one of three fixed commands (`pacman`, `flatpak`, `all`); any other kind is refused, a missing terminal is reported |
| Shell | The page reads "Not checked yet", Install is disabled until there is something to install, a check lists packages and Flatpak apps, and Install starts the terminal with the expected fixed arguments; checking started no terminal; no elided text |

### Not executed (slice 8)

- A real `checkupdates` against live mirrors (network, mirror failures, partial-upgrade warnings), and the terminal flow with a real `sudo pacman -Syu`. Reboot-required detection and automatic or scheduled checks are not built: a check happens only when asked.

### Not executed (slice 2)

- Real messengers: whether their notifications set the inline-reply capability and how they react to a reply or to a dismissal; the lock screen label in a real `hyprlock` (the config is only checked for structure).

## Previous record — 2026-10-15 (through round ten)

## Addendum: round ten (icons, Hyprland errors, responsiveness, polish)

### Executed

| Check | Result |
| --- | --- |
| Hyprland Lua config | The mock now rejects a spring without numeric `mass`, `stiffness` and `dampening` and an animation naming a curve that does not exist. The previous config fails it with exactly the reported `dampening expects a number`; the new one passes, registers the spring and names it for `windowsIn`; a variant that Hyprland would refuse falls back to the bezier and the binds after it still run; with curves, animations and gestures all refused the file still finishes, registers every bind and still starts the shell at `hyprland.start` |
| Icon set | Generated data equals the vendored SVGs; every icon name used by the shell exists (a test scans the QML); every mapped symbol has outlined and filled variants; each vendored file is a single path; Apache-2.0 license and notice present; battery has all seven level glyphs |
| Icon theme | The shell wrapper selects Papirus when installed, leaves the system theme alone otherwise and lets an explicit `QS_ICON_THEME` win; the theme is in the PKGBUILD and ISO package list |
| App icons | An app with no `Icon=` key, or one the theme lacks, gets a letter tile with the right initial; nothing in the shell references the generic executable icon |
| Responsiveness | Dark mode, Wi-Fi, mute, volume and brightness clicks change the snapshot before the command returns; sliders stay in range; unavailable hardware and unknown actions are not guessed; a read that began before a click is discarded; a guess the system does not confirm is replaced by the real state; the command really runs and the final state matches |
| Bridge speed | Median `prismctl` call: about 150 ms to about 90 ms (`about`), 216 ms to 123 ms (`status`), 136 ms to 87 ms (`tiles list`) on the build machine |
| Layout | Slider rows show their value once, in their own units; no elided text on the Settings pages at normal and largest text size |
| Browser preview | `tests/preview.spec.cjs` passes with the new icons |
| `scripts/check.sh` | Passed |

### Not executed

- A real Hyprland session: whether 0.56 accepts the spring exactly as written (the field name comes from the error text you reported and the Hyprland wiki, which itself spells it both ways).
- Whether Quickshell honours `QS_ICON_THEME` and finds Papirus icons for every installed app; the harness uses a stand-in theme lookup.
- Optical comparison of the icons against Android 17 on a real display.

## Previous record — 2026-10-15 (through round nine)

## Addendum: round nine (notification history)

### Executed

| Check | Result |
| --- | --- |
| Setting | Off by default; only `yes`/`no` accepted by the bridge; persists; a non-boolean value in the file falls back to off |
| History | Nothing recorded before opting in; entries newest first with the app, title, a bounded body and the important flag; muted apps are not recorded; the list is capped at 100 and long text is cut; clearing and turning the setting off both empty it; nothing is written to disk |
| Settings page | The toggle reaches the bridge and the rows render without elided text |
| `scripts/check.sh` | Passed |

### Not executed

- Real notification clients: whether Quickshell reports an in-place replacement as a new notification (it would then be recorded again), and very large bodies from real apps.

## Previous record — 2026-10-15 (through round eight)

## Addendum: round eight (Storage)

### Executed

| Check | Result |
| --- | --- |
| Storage adapter | Top-level folders map to categories, the category sum equals the reported total, symbolic links are not followed, the entry cap and the time limit each stop the walk (including inside one huge directory) and set `truncated`, an unreadable home reports zero instead of failing |
| Clear previews | Removes only the preview folder; symlinked previews are not counted; unknown `storage` operations are refused by the CLI |
| Storage page | Boot, open Settings → Storage with real `prismctl`: folders appear with sizes, empty categories are hidden, nothing is elided at normal and largest text size, clearing previews deletes the folder and disables the button; byte formatting checked at unit boundaries |
| `scripts/check.sh` | Passed |

### Not executed

- Block-based sizes (`st_blocks`) on btrfs, ZFS, compressed or deduplicated filesystems, and homes with millions of files (the partial-count notice is tested, not the timing on real disks).

## Previous record — 2026-10-15 (through round seven)

## Addendum: round seven (pins, tile details, widget sizes, live Recents)

### Executed

| Check | Result |
| --- | --- |
| Clipboard pins | Private (0600) atomic file, text only, duplicate/oversize/limit refusal, survive clearing and a disabled history, corrupt files filtered; copy sends the text on stdin to `wl-copy`; the pane's rows send the right commands and images get no pin button |
| Tile details | Right-click opens the panel even on tiles that look unavailable (so they can say why); battery modes, color scheme and screenshot mode chips act through the bridge |
| Widget sizes | Validation (only four widgets, three sizes), persistence, corrupt files; small and large cards render at the expected widths with no elided text; Settings chips reach the bridge |
| Live Recents | With a stub toplevel list (addresses with and without `0x`), only the window with a handle gets a live view, none while closed; the live view loads on demand so a Quickshell without screencopy cannot break the overview |
| `scripts/check.sh` | Passed |

### Not executed

- **The real `ScreencopyView`**: whether Quickshell on Arch was built with screencopy, whether
  `HyprlandToplevel.address` matches `hyprctl` addresses as assumed, permission prompts, frame rates, and
  the cost of capturing many windows at once. The harness uses a flat-color test double.
- Pinned text is stored unencrypted in the user's data directory (by design, like the notes widget).

## Previous record — 2026-10-15 (through round six)

## Addendum: round six (notes, warmth, power modes, clipboard search)

### Executed

| Check | Result |
| --- | --- |
| Notes | Round trip, private (0600/0700) atomic writes, control characters stripped, 4000-character limit, bad input keeps the old note; the widget saved typed text through the bridge |
| Night Light warmth | Bounded integer only; applied live only while Night Light is on; the saved value is reused when it is turned on; failures not persisted |
| Power modes | Fixed `powerprofilesctl set` values for three modes; the Settings row sends the right action |
| Clipboard search | Filters the injected history and shows "No matches" |
| `scripts/check.sh` | Passed |

### Not executed

- `hyprsunset` warmth changes and `powerprofilesctl` on real hardware (mocked here); the Performance profile exists only on some machines.

## Previous record — 2026-10-15 (through round five)

## Addendum: round five (Recents previews, lock screen, glance)

### Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` | Python suites, Node specs (now including next-alarm arithmetic), shell syntax and the QML runtime suite passed |
| Preview adapter | Mocked `grim`/`hyprctl`: only visible windows on the current workspace are captured, bounded integer regions, old previews replaced, closed windows' previews deleted, earlier previews kept for other workspaces, one failure does not lose the rest, private (0700) runtime directory, off switch deletes everything |
| Recents | Opens even when no preview can be taken; a preview image renders on the right card, others fall back to icons; the Settings switch reaches the bridge |
| Next alarm arithmetic | Spec: later today, passed time rolls to tomorrow, weekday/weekend sets, once-only alarms, month/year rollover, malformed times ignored |
| Glance | Shows the next alarm and a running timer, no elided text |
| Lock screen config | Structural test of `hyprlock.conf` (documented blocks, color roles, static label commands) |

### Not executed

- `grim` window captures on a real compositor: overlapping floating windows will appear in each other's
  preview, HiDPI scaling and multi-monitor offsets are unverified, and capture latency before Recents opens
  (up to 1.5 s timeout) has not been measured.
- `hyprlock` rendering (`$USER`, the battery command, `brightness`) on a real session.

## Previous record — 2026-10-15 (through round four)

## Addendum: round four (Date & time, keyboard layout, world clock, snooze)

### Executed

| Check | Result |
| --- | --- |
| `scripts/check.sh` | Python suites, Node specs, shell syntax and the QML runtime suite passed |
| Date & time adapter | Mocked `timedatectl`: only listed zones and fixed booleans reach the command; 12/24-hour preference persists; clicked through in Settings |
| 12-hour clock | Every visible clock (bar, desktop widget) shows AM/PM with no elided text |
| Keyboard layout | Applies through `hyprctl keyword` before saving; failure is not persisted; unknown ids refused; the Settings row sends the right command |
| World clock | Day and offset arithmetic (including next-day) checked; adding a zone from the panel persisted; corrupt saved zones filtered |
| Ringing banner | Alarm and timer banners, Snooze → ring again, Dismiss; timers have no snooze |

### Not executed

- `timedatectl` and polkit approval on a real system; changing the zone while the shell runs.
- Live `input:kb_layout` changes on Hyprland 0.56 with a Lua config.
- Ringing on multiple monitors or over a locked screen; the repeated sound is not a looping clip.

## Previous record — 2026-10-15 (through round three)

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
