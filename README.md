# BlueberryPie-17

**Arch at heart. A little more you.**

Arch Linux with an Android 17-inspired Material 3 Expressive desktop.
**PrismOS** is the working name of the native desktop in this repository.

PrismOS is a new Arch Linux desktop project inspired by Android 17 and Material
3 Expressive: playful color, tactile rounded controls, emphasized typography,
and motion that connects an action to its result.

The v0.9 source release rebuilds the native **Qt Quick / Quickshell** shell on a
real Material 3 color system (CAM16/HCT Tonal Spot), shared Expressive components,
an Android-style Settings app, a dual notification/Quick Settings shade, a
running-app dock, Recents, and an offscreen QML runtime harness. It also keeps the
interactive offline preview, real Linux system adapters, and the Arch
package/live-ISO staging pipeline. This is a development foundation. A bootable
ISO and hardware qualification have not been completed in this release.

### What's new in v0.9

- **Material 3 dynamic color**: `prismos/hct.py` implements CAM16/HCT; the Tonal Spot
  scheme produces the full M3 role set, validated against published reference values.
  The wallpaper, Settings preview and every surface follow the palette and dark mode.
- **Fixed**: clipped button labels, unreadable dark mode (content-color roles rendered
  black), a dock that clipped its last button, and glyph icons. Icons are now a 68-symbol
  original set recolored at runtime.
- **Quick Settings**: large and compact tiles (active = pill, inactive = squircle),
  brightness/volume sliders, MPRIS media card, and Android's dual shade on wide
  screens with grouped, swipe-to-dismiss notifications and heads-up banners.
- **Settings**: searchable two-pane app with Network, Bluetooth, Display, Sound,
  Notifications, Wallpaper & style, Pointer & keyboard, Shortcuts, Apps, Battery & power
  and About (real system facts).
- **Launcher** with ranked search, categories and recents; **dock** with running-app
  indicators and window cycling; **Recents** overview (Super + Tab).
- **Wallpaper picker**: choose any PNG/JPEG/WebP from `~/Pictures` (home folder only);
  the whole shell recolors from the picture's accent. The default wallpaper is drawn
  from the current palette.
- **Hardware keys**: volume, mute, microphone mute and brightness bind to fixed actions.
- **Verification**: `tests/test_shell_runtime.py` loads the real shell QML offscreen with
  stub Quickshell modules; it needs PySide6 and is skipped when unavailable.

### Added after v0.9: window controls, desktop widgets and an installer

- **Window controls**: the status bar carries Google-style caption controls for the
  focused window (minimize, maximize/restore, snap left/right, close; the title and app
  icon sit beside them). Windows can be floated, snapped to halves of the work area,
  minimized to a hidden workspace and restored from the dock or Recents. Keys:
  `Super + ↑/↓/←/→` maximize, minimize and snap, `Super + F` float. Everything goes through
  `prismctl windows ...` with fixed `hyprctl dispatch` calls; the dispatchers are
  unverified on Hyprland 0.56 with a Lua config (see `docs/VALIDATION.md`).
- **Desktop widgets** in a classic Google style, chosen in Settings → Widgets: At a glance,
  clock, search (apps first, then a web search), month calendar, now playing, system
  (CPU, memory, storage), analog clock and opt-in weather. Weather talks only to fixed
  HTTPS hosts after you pick a place; nothing leaves the machine otherwise.
- **Installer**: a wizard from the live USB (`docs/INSTALLER.md`). It erases and installs
  to one whole disk after a typed confirmation and runs the root work through a
  polkit-protected helper. It is **unrun on real disks**; try it in a VM first.

## Build the ISO on Windows

See **[Windows build instructions](docs/WINDOWS-ISO.md)** for the
one-click GitHub Actions option and the local Arch Linux VirtualBox VM
workflow. A finished artifact is an unverified boot candidate until a
real VM or USB boot is tested.

## Try the look immediately

Open `PrismOS-Preview-v0.4.html` directly for the complete standalone preview, or
open `preview/index.html` alongside its local assets. Neither needs external dependencies.
Alternatively:

```bash
./scripts/preview.sh
# Open http://127.0.0.1:8787/
```

Try Quick Settings, the lilac/mint/tangerine/rose palettes, dark theme, reduced
motion, app search, and icon-to-window launch transitions. Preview hardware
controls and app contents are explicitly simulated. Native controls use Linux.

## What is implemented

| Area | First implementation |
| --- | --- |
| Native shell | Theme-following wallpaper, status bar with live status icons, running-app dock, system tray, ranked app launcher, Recents, Settings app |
| Quick Settings | Large/compact tiles, split radio/sound/microphone controls, inline connection and audio panels, Do Not Disturb, dark theme, brightness, reduced motion, dual notification shade |
| System controls | NetworkManager, BlueZ, WirePlumber/PipeWire, brightnessctl; no shell evaluation |
| Color | CAM16/HCT Tonal Spot, four palettes, custom seed, optional wallpaper sampling, full Material 3 role set, M3 type scale and shape tokens |
| Motion | Tile shape response, slider feedback, shade/drawer transitions, morphing loader, launch splash that ends on matching Hyprland window arrival/focus |
| Notifications | Grouped by app, swipe to dismiss, action buttons, urgency, heads-up banners, 50-item retention cap, plain-text cards, quiet mode |
| Media | MPRIS metadata/artwork, capability-guarded playback controls and player selection |
| Sound devices | Output/microphone tabs, default selection, levels, independent mute, unavailable-device feedback and filtered PipeWire event updates |
| Session | Confirmed power actions, idle locking, per-monitor shortcuts and unplug recovery |
| Arch integration | Dedicated session, PKGBUILD, complete upstream releng profile staging |

Native launch combines an icon-origin **splash** with the compositor's window-open
animation. It listens for matching `openwindow`/`activewindow` events using the
desktop ID and `StartupWMClass`, including an already-running application. It
waits briefly for the entrance animation, fades on arrival, and times out after
eight seconds for background apps or unmatched IDs. Cancellation and launch
errors clear it. It does not morph the actual application surface from its icon;
that remains a later compositor integration milestone.

## Run the native shell on Arch

The session targets **Hyprland 0.56+ (Lua configuration)** and **Quickshell 0.3.2+**.
Get the source from this repository:

```bash
git clone https://github.com/MobiLaunch/BlueberryPie-17.git
cd BlueberryPie-17
```

On an existing Arch installation, fully update and install dependencies:

```bash
sudo pacman -Syu --needed base-devel git quickshell hyprland python python-pillow \
  qt6-declarative qt6-svg qt6-shadertools networkmanager nm-connection-editor \
  bluez bluez-utils blueman pipewire pipewire-pulse wireplumber brightnessctl \
  glib2 dbus hyprlock hypridle foot thunar polkit-kde-agent ttf-roboto xdg-desktop-portal-hyprland
```

From an existing Hyprland session, test just the shell:

```bash
./scripts/run-shell.sh
```

Another shell or notification daemon may already own the same screen space or
notification D-Bus name. Use the separate PrismOS session for a complete test.
Existing Hyprland configuration files are not overwritten.

For the separate login-screen session, build and install the package **as your
regular user**:

```bash
./scripts/build-package.sh -i
sudo systemctl enable --now NetworkManager bluetooth
```

Log out, select **PrismOS** in your display manager, and log in. From a fresh
TTY, `prism-session` starts the same session. Its editable configs are created
under `~/.config/prismos/hypr/` on first launch.

Right-click, long-press or use the Menu key on an app to pin/unpin it. Up to eight
favorites are saved; missing apps reappear in the dock if reinstalled. The dock
scrolls on narrow screens. The tray supports activation and app menus.
Quick Settings shows a media card when a compatible MPRIS player is available.

Use the arrow on the Wi-Fi or Bluetooth tile for connections; the tile body toggles
the radio. Wi-Fi offers nearby networks, signal/security labels, saved-profile
reuse, an inline masked password field and disconnect. New open, WPA-PSK and
WPA3 SAE networks are supported; enterprise/legacy/hidden networks use Advanced
network settings. Pairing PINs and confirmation use Blueman. Once paired, devices
can connect/disconnect from the shell. Refresh performs a bounded scan.

Wi-Fi passwords go to the bridge through stdin and to NetworkManager using a
temporary private password file, removed on success or handled failure. They
never enter process arguments or PrismOS settings. New failed profiles are
removed; existing profiles are retained. NetworkManager owns saved network
configuration. Credential reuse and reconnect still require hardware validation.
Network events refresh status promptly, with periodic recovery polling. Automatic
network-list refresh pauses while a row is expanded, so typing is not interrupted.

Open the Sound or Microphone tile's arrow for playback and input devices. Select
a device, adjust its level, or mute it independently. The microphone tile toggles
the current default input; it does not block every microphone or recording app.
The picker changes the WirePlumber default. Apps with explicit device routing may
keep their own selection; this release does not move individual app streams.
Levels stay within 0–100%, and changing volume does not implicitly unmute a device.
Device names and lifetime serials are checked against a fresh PipeWire graph
before each picker action. Device removal clears unavailable choices on refresh.

Power actions require confirmation and are disabled when unavailable for the
current login session. Idle locking uses `hypridle` after ten minutes and before
sleep. If you previously ran v0.1, add the new hypridle startup line from the
packaged `hyprland.lua` to your existing PrismOS config; configs are preserved
when upgrading. Native hardware qualification remains open.


| Shortcut | Action |
| --- | --- |
| Super + Space / Super + A | App drawer |
| Super + Q | Quick Settings |
| Super + Tab | Recent apps |
| Super + comma | Settings |
| Super + S | Prism Store |
| Volume, mute, microphone mute, brightness keys | Fixed `prismctl` actions |
| Super + Enter | Terminal |
| Super + E | Files |
| Super + L | Lock |
| Super + Shift + Q | Close focused application |

### Color from a wallpaper

```bash
./bin/prismctl theme --wallpaper /path/to/wallpaper.png
./bin/prismctl theme --seed '#47846a'
```

Wallpaper sampling changes the shell palette. The default wallpaper is drawn from the
current color roles, so it follows the palette and dark mode; Settings > Wallpaper &
style picks pictures from `~/Pictures`. Color uses a CAM16/HCT Tonal Spot implementation validated against
published Material values; it is not Google's Monet service, and wallpaper seed
scoring is a simplified version of Material's. Third-party Linux applications retain
their own themes in this milestone.

### Run the offscreen shell checks

```bash
python -m venv .venv && .venv/bin/pip install PySide6-Essentials pillow
.venv/bin/python -m unittest tests.test_shell_runtime -v
```

The harness needs Qt's EGL libraries (`libEGL.so.1`) and optionally `lua` for the
Hyprland config test. It uses stub Quickshell modules; see `docs/VALIDATION.md` for
exactly what it does and does not prove.

## Build a live ISO on Arch

Run these commands on your Arch Linux machine **as a normal user**:

```bash
sudo pacman -Syu --needed base-devel archiso git ripgrep
git clone https://github.com/MobiLaunch/BlueberryPie-17.git
cd BlueberryPie-17
bash ./build.sh
```

If you have already cloned the repository, run `git pull --ff-only` from the
existing checkout instead of cloning it again. The new root `build.sh` handles
package creation, locates the actual package file, stages the complete upstream
Arch releng profile and attempts `mkarchiso`. No manual package paths required.
Logs go to `build/iso-build.log`; successful ISO output goes to `out/`.
Use `bash ./build.sh --stage-only` to inspect just the generated Arch profile.

This ISO remains **unverified until an Arch build and physical boot succeed**.
The live session has an "Install PrismOS" wizard (see `docs/INSTALLER.md`; it has never been run on a real disk). Live login: `prism` / `prism`.

### Make a bootable USB

For an extra safety check, use the included USB writer. It refuses non-USB
or mounted disks and requires an explicit erase confirmation:

```bash
lsblk -o NAME,SIZE,MODEL,TRAN,MOUNTPOINTS
sudo bash ./scripts/flash-usb.sh /dev/sdX
```

Replace `/dev/sdX` with the verified **whole USB device**. This erases it.
The manual `dd` method below remains available.

**All data on the target USB disk will be erased.** First identify its model
and unmount its partitions. Use the entire disk, not a numbered partition.

```bash
lsblk -o NAME,SIZE,MODEL,TRAN,MOUNTPOINTS
ISO="$(find "$PWD/out" -maxdepth 1 -name '*.iso' -type f | sort | tail -n 1)"
test -f "$ISO" || { echo 'No ISO found. Build it first.'; exit 1; }
# Replace /dev/sdX with your carefully verified USB disk
sudo dd if="$ISO" of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

Reboot and select the USB entry in your firmware boot menu.

## Prism Store and optional Android apps

Prism Store now offers real Flathub search and user-scoped Flatpak install,
remove and launch actions. Open it from the dock or app drawer and explicitly
enable the Flathub remote. The Android tab opens optional Waydroid after setup.
Waydroid requires a compatible binder-enabled kernel and separately downloaded
Android image; it is not proof of native Android 17, and some games will not work.
See [Prism Store and Waydroid setup](docs/WAYDROID_STORE.md).
## Publish updates to this repository

Commit your changes in a clone of this repository. The included script checks
that your branch contains the current remote `main`, then pushes without force:

```bash
sudo pacman -S --needed github-cli
gh auth login
./scripts/publish-github.sh MobiLaunch/BlueberryPie-17
```

The script refuses unrelated history, a different `origin`, or uncommitted
changes. Run `git config user.name` and `git config user.email` first if Git asks
for an identity when you commit.

## Development and planning

```bash
python3 -m unittest discover -s tests -v
python3 scripts/generate-design.py
./scripts/check.sh
# Optional preview interaction tests, after installing Playwright:
node tests/preview.spec.cjs
# On Arch, verify real audio APIs against private virtual devices:
dbus-run-session -- python3 tests/audio_integration.py
```

Start with [the roadmap](docs/ROADMAP.md), [architecture](docs/ARCHITECTURE.md),
[design contract](docs/DESIGN.md), and [validation record](docs/VALIDATION.md).
This is an independent Linux desktop. Android compatibility uses Waydroid as an optional user-enabled runtime; no Android images or Google services are bundled. Hardware qualification remains outstanding.

## First-use Android experience (v0.5)

On first login, a Material Expressive wizard offers theme colors and an
optional Android switch. Android stays off if the user declines. Opting in
opens Settings with a small animated spinner and actual setup stage labels
(authorization, image download, container start, app readiness). There are no
fabricated download percentages. The administrator prompt authorizes a
fixed-purpose polkit helper, not arbitrary shell commands.

Once ready, users can explicitly Install F-Droid from its official HTTPS site,
then open it from the same Settings section. Compatible Android applications
can appear in the regular PrismOS launcher. Switching Android off stops the
current user's session without uninstalling Android apps; consenting users
get a quiet session resume at the next login.

**Limits:** no tested bootable ISO yet, no real disk installer, and Waydroid
needs compatible kernel Android Binder support. Games dependent on ARM,
Google services, DRM or anti-cheat can fail. Live USB changes are not
persistent. No Android compatibility is silently activated.



## v0.6 — Full-desktop expressive integration pass

Prism Store combines Flatpak/Flathub **Linux** listings and search metadata
from the official F-Droid **Android** catalog, with source labels for each
result. Selecting an Android title opens its official F-Droid package listing
through Waydroid; the Android client, not a Linux-side APK downloader, confirms
actual installation and updates. The public F-Droid search API is for display
metadata, not signature verification.

The PrismOS Settings surface now groups working connections, brightness,
audio, DND, appearance, input preferences, Android consent and system actions.
The native touchpad and pointer changes persist per user and are applied only
in the PrismOS Hyprland session. Shared expressive context menus now cover the
desktop background, dock and launcher. Text fields in Wi-Fi setup, Prism Store
and app search use shared Material-inspired controls.

The PrismOS login session sets a bundled, per-palette GTK3/GTK4 theme and the
Qt Quick Material style without editing another desktop's settings. A newly
selected color is applied **immediately to the PrismOS shell**; existing GTK/Qt
applications may need restarting, and the toolkit theme preset is selected at
the **next PrismOS login**. Some libadwaita, Electron, Flutter, Java and
other third-party applications may not fully honor these themes.

**Real ISO boot, Waydroid F-Droid intent support and physical input/device
behavior still require testing on Arch hardware.** Complete feature coverage
is tracked in [Expressive coverage audit](docs/EXPRESSIVE-COVERAGE.md).

Useful PrismOS shortcuts:

- Super + S — Prism Store
- Super + comma — Settings (appearance, connections, sound and input)
- Super + Q — Quick Settings
- Super + Space — App launcher
- Alt + left-drag / right-drag — Move / resize an eligible app window



## v0.7 — Prism Files, file picker, and safe display scaling

- Native **Prism Files** panel opened with Super+E, dock icon or app drawer.
  Includes bookmarks, folder navigation, local search, hidden files,
  open-with-default, new folders, rename and **Move to Trash** with confirmation.
  Actions always run as the logged-in user, never root.
- PrismOS-specific XDG portal preference selects the GTK file chooser for
  ordinary application upload/open/save dialogs. The Hyprland portal retains
  screen-sharing functionality. The `xdg-desktop-portal-gtk` package is an
  explicit dependency.
- **Display scaling** in Settings discovers attached displays and supports safe
  scale options. Each change starts a **20-second confirmation trial**; an
  unconfirmed change automatically reverts. Confirmed options persist per user.
  Display rotation, resolution changes and mirroring are not exposed until they
  have equally safe rollback and physical tests.
- Fixed launcher shortcut routing for Prism Store and Files.
- The PrismOS session now loads its **versioned packaged Hyprland config**
  automatically, so upgrades bring updated shortcuts and compositor behavior
  to existing users. It never deletes the prior copied config at
  `~/.config/prismos/hypr/hyprland.lua`.
  To intentionally launch a custom config, set
  `PRISM_HYPRLAND_CONFIG=/absolute/path/to/custom.lua` before starting
  `prism-session`.

Testing this release requires logging out and starting PrismOS again (toolkit
and session config startup). The updated Arch package can be installed using
`./scripts/build-package.sh -i`; rebuild the ISO using `bash ./build.sh`.
CI tests verify source/logic; **real USB boot, XDG portal integration,
multi-monitor changes and Waydroid still require a machine/VM test**.


## v0.8 — Files, drives, multi-monitor layouts and gestures

**Prism Files** now supports Copy, Cut and Paste with a per-user clipboard and
name-collision protection. File and folder operations preserve symlinks and
refuse copying a directory into itself. Use the context menu or Ctrl+C,
Ctrl+X, Ctrl+V (when the Files window has keyboard focus).
Image files get cached preview thumbnails (bounded size, max 30 generated per
folder listing). The file manager can discover removable drives, mount them
through UDisks2 with standard Linux/polkit approval, open the mounted volume,
and safely unmount it.

An **experimental internal drag-to-copy** path lets you drag files onto
folders or saved places in Prism Files. It only copies: moves require explicit
Cut/Paste, and overwrites are refused. Physical mouse/touch drag needs live
Quickshell/Hyprland verification.

**Display arrangement** allows placing a screen left/right/above/below another.
Overlaps are refused. Changes require confirmation within 20 seconds; otherwise
the old position is restored. Validated positions are saved per PrismOS user.

**Compositor gestures** supported on compatible touchpads:

- 3-finger horizontal swipe: change workspaces (continuous Hyprland gesture).
- 4-finger swipe up: open PrismOS app drawer.
- 4-finger swipe down: open Quick Settings.

These use the official Hyprland 0.56 Lua gesture configuration. This does not
implement system-wide touchscreen edge swipes; touch-display hardware gestures
are a separate compatibility target.

Source checks and unit tests cover critical data safety behaviors, but ISO
boot, real USB devices and monitor layout transitions require physical QA.

### Early touchscreen swipe support

A touchscreen gesture surface on empty desktop wallpaper now supports swiping
up from the lower region to open the app drawer and swiping down from the upper
region to reveal Quick Settings. It is deliberately constrained to the wallpaper
so app-local touch gestures and scrolling keep priority. This is not a global
Android touch gesture implementation, and must be verified on real touch
hardware and in tablet mode.
