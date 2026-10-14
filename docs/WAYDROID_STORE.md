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
