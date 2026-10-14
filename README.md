# BlueberryPie-17

**Arch at heart. A little more you.**

Arch Linux with an Android 17-inspired Material 3 Expressive desktop.
**PrismOS** is the working name of the native desktop in this repository.

PrismOS is a new Arch Linux desktop project inspired by Android 17 and Material
3 Expressive: playful color, tactile rounded controls, emphasized typography,
and motion that connects an action to its result.

The v0.2 source release includes a native **Qt Quick / Quickshell** shell, an
interactive offline design preview, real Linux system adapters, and an Arch
package/live-ISO staging pipeline. This is a development foundation. A bootable
ISO and hardware qualification have not been completed in this release.

## Try the look immediately

Open `PrismOS-Preview-v0.2.html` directly for the complete standalone preview, or
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
| Quick Settings | Wi-Fi, Bluetooth, Do Not Disturb, dark theme, sound, brightness, reduced motion |
| System controls | NetworkManager, BlueZ, WirePlumber/PipeWire, brightnessctl; no shell evaluation |
| Color | Four palettes, custom seed, optional wallpaper sampling, contrast-checked semantic roles |
| Motion | Tile shape response, slider feedback, shade/drawer transitions, morphing loader, launch splash |
| Notifications | Action buttons, urgency, 50-item retention cap, plain-text cards, dismissal and quiet mode |
| Media | MPRIS metadata/artwork, capability-guarded playback controls and player selection |
| Session | Confirmed power actions, idle locking, per-monitor shortcuts and unplug recovery |
| Arch integration | Dedicated session, PKGBUILD, complete upstream releng profile staging |

Native launch currently combines a short icon-origin **splash** with the
compositor's window-open animation. It does not morph the actual application
surface from its icon. The browser preview demonstrates the intended end-state
motion; synchronized native surface transitions belong to the next milestone.

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

Wallpaper sampling changes the shell palette. The v0.2 desktop still uses the
bundled vector wallpaper; a wallpaper picker is planned. The initial tonal
algorithm is HSL-based with contrast checks, **not** Google's HCT/Monet system.
Third-party Linux applications retain their own themes in this milestone.

## Build a live ISO on Arch

First build the package without installing it:

```bash
./scripts/build-package.sh
sudo pacman -S --needed archiso ripgrep
sudo ./scripts/build-iso.sh --package "$(find build/package -maxdepth 1 -name 'prism-shell-*.pkg.tar.zst' -print -quit)"
```

The script copies the complete installed `/usr/share/archiso/configs/releng`
profile, preserving its bootloader files and `install_dir` relationship. It
adds a local package repository, packages, live account and greetd session.
The output goes to `out/`; this pipeline still needs a real Arch ISO build,
UEFI/BIOS boot tests, and hardware verification. No disk installer is included.

Use `--stage-only` to inspect the assembled profile before building. The live
demo uses username `prism`, password `prism`, and live-only passwordless sudo; it is not an
installed-system account policy.

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
```

Start with [the roadmap](docs/ROADMAP.md), [architecture](docs/ARCHITECTURE.md),
[design contract](docs/DESIGN.md), and [validation record](docs/VALIDATION.md).
This project is an independent Linux desktop; it does not ship Android, Google
services, or Android application compatibility. Optional Waydroid integration
comes later, after the core desktop is reliable.
