# BlueberryPie-17

**Arch at heart. A little more you.**

Arch Linux with an Android 17-inspired Material 3 Expressive desktop.
**PrismOS** is the working name of the native desktop in this repository.

PrismOS is a new Arch Linux desktop project inspired by Android 17 and Material
3 Expressive: playful color, tactile rounded controls, emphasized typography,
and motion that connects an action to its result.

The v0.4 source release includes a native **Qt Quick / Quickshell** shell, an
interactive offline design preview, real Linux system adapters, and an Arch
package/live-ISO staging pipeline. This is a development foundation. A bootable
ISO and hardware qualification have not been completed in this release.

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
| Native shell | Wallpaper, top bar, saved dock favorites, app badges, system tray, searchable app drawer, appearance panel |
| Quick Settings | Split radio/sound/microphone controls, inline connection and audio panels, Do Not Disturb, dark theme, brightness, reduced motion |
| System controls | NetworkManager, BlueZ, WirePlumber/PipeWire, brightnessctl; no shell evaluation |
| Color | Four palettes, custom seed, optional wallpaper sampling, contrast-checked semantic roles |
| Motion | Tile shape response, slider feedback, shade/drawer transitions, morphing loader, launch splash that ends on matching Hyprland window arrival/focus |
| Notifications | Action buttons, urgency, 50-item retention cap, plain-text cards, dismissal and quiet mode |
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
| Super + comma | Appearance |
| Super + Enter | Terminal |
| Super + E | Files |
| Super + L | Lock |
| Super + Shift + Q | Close focused application |

### Color from a wallpaper

```bash
./bin/prismctl theme --wallpaper /path/to/wallpaper.png
./bin/prismctl theme --seed '#47846a'
```

Wallpaper sampling changes the shell palette. The v0.4 desktop still uses the
bundled vector wallpaper; a wallpaper picker is planned. The initial tonal
algorithm is HSL-based with contrast checks, **not** Google's HCT/Monet system.
Third-party Linux applications retain their own themes in this milestone.

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
There is no permanent disk installer yet. Live login: `prism` / `prism`.

### Make a bootable USB

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
This project is an independent Linux desktop; it does not ship Android, Google
services, or Android application compatibility. Optional Waydroid integration
comes later, after the core desktop is reliable.
