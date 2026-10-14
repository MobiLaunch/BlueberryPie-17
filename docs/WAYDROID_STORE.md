# Prism Store and Android apps

Prism Store is a native Quickshell surface backed by **real user-scoped Flatpak**
operations. Flathub setup requires an explicit click; no repository changes
happen merely because you open Prism Store.

- Open Prism Store from the dock or app drawer.
- Select **Enable Flathub** once.
- Search Games or Apps, then **Install**, **Open** or **Remove**.
- Apps are installed per-user. A live USB does **not** preserve changes at reboot.

This initial catalog uses Flathub's search metadata, without rich artwork,
publisher verification, ratings, or purchase support. Those require a subsequent
AppStream metadata integration. This is **not** a Google Play Store clone.

## Optional Waydroid for Android applications

Waydroid is an Android container for Wayland, not Android 17 itself. On
compatible hardware with kernel Android binder support, after installing
the package and checking the kernel:

```bash
sudo pacman -S --needed waydroid
sudo waydroid init
sudo systemctl enable --now waydroid-container.service
waydroid session start
waydroid show-full-ui
```

The Prism Store **Android** tab exposes the Waydroid launcher after setup.
Waydroid desktop entries may appear in the ordinary PrismOS app drawer.

To install an APK that **you** downloaded from a trusted source:

```bash
prismctl android status
prismctl android install ~/Downloads/example.apk
```

For open-source Android games, F-Droid can be added inside Waydroid from its
official website after Waydroid is functional. Do not blindly install APKs from
unknown mirrors. Neither Google Play Services nor an Android system image are
bundled. Native ARM-only or DRM-dependent games may not work on x86_64.

On a live USB, the environment is ephemeral; first-run Waydroid images and app
installs vanish on reboot. For full prerequisites, see:
https://wiki.archlinux.org/title/Waydroid and https://docs.waydro.id/

## First-run consent and backstage Android runtime

PrismOS presents optional Android support during the first-run wizard and
later as a toggle in Settings. With consent, an administrator-approved polkit
helper runs only the fixed Waydroid initialization and container-service
actions. It downloads the official VANILLA Waydroid image when needed.

Settings shows a small expressive spinner, driven by real setup stages.
Waydroid session readiness and app enumeration are checked before announcing
success. Setup does not report guessed percentages. First-run and saved
preferences belong to the current user; the live ISO is ephemeral.

F-Droid is optional and user-initiated: its APK comes from the official
HTTPS download URL with a file-size limit, then is installed into Waydroid.
After installation, Settings changes the button to Open F-Droid.
Full APK publisher-signature pinning and richer Android catalog metadata
remain future security hardening; Android image/GApps are not bundled.


## Prism Store unified discovery (v0.6)

In Prism Store, All shows Linux Flatpak results together with Android F-Droid
results when the user has enabled Android. Linux and Android are also available
as source filters. F-Droid metadata comes from the official public search API.
Results are clearly marked by platform and source.

Android applications are not installed from unverified API URLs. The Details
action passes a validated package ID as an official F-Droid package URL through
the Waydroid Android intent interface. F-Droid must be installed and Android
ready; the user performs the final installation confirmation in F-Droid.

Android compatibility varies by hardware/ABI. An Android listing in search
is not a promise that its game will work on x86_64.
