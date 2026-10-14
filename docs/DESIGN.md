# Design contract

## Reference direction

- [Android 17 platform](https://developer.android.com/about/versions/17)
- [Google's Material 3 Expressive introduction](https://blog.google/products-and-platforms/platforms/android/material-3-expressive-android-wearos-launch/)
- [Material motion overview](https://m3.material.io/styles/motion/overview/how-it-works)
- [Material loading indicator](https://m3.material.io/components/loading-indicator/overview)
- [Quickshell 0.3.2 APIs](https://quickshell.org/docs/v0.3.2/types/)
- [Current Hyprland Lua example](https://github.com/hyprwm/Hyprland/blob/main/example/hyprland.lua)
- [Archiso releng workflow](https://wiki.archlinux.org/title/Archiso)

Material 3 Expressive is the design system; Android 17 Pixel SystemUI is the
desired shell reference. They are related but not interchangeable specifications.
The first pass establishes the visual direction. The exact Quick Settings match
requires a frozen Pixel reference and side-by-side geometry/motion measurements.

## Visual rules

1. Expressive color comes from semantic tokens, not separate hardcoded app themes.
2. Active Quick Settings tiles use the primary container and a tighter rounded
   shape; inactive tiles use a neutral container with fuller pill corners.
3. A large brightness track sits above a dense, regular Quick Settings grid.
4. Display type gets emphasis; labels stay readable and avoid excessive weight.
5. Icons use consistent rounded strokes. Original SVG symbols are bundled;
   Google marks and proprietary assets are not copied.
6. Blur belongs behind the shade, with softly tinted surfaces and restrained shadows.
7. Touch controls aim for at least 48 logical pixels. Keyboard focus stays visible.

## Motion rules

| Interaction | First motion contract |
| --- | --- |
| Tile press | Small scale compression; radius softens and returns |
| Tile state | Color and corner shape transition together |
| Slider | Thumb grows on press; writes commit when dragging ends |
| Shade | Short downward entrance with mild spring overshoot |
| Drawer | Upward entrance with a low-amplitude spring |
| App launch | Origin expansion; native splash waits for matching open/focus events, with minimum movement and a bounded fallback |
| Loading | Rotating/morphing six-to-eight-lobed shape; static reduced-motion variant |
| Reduced motion | Remove overshoot, movement loops and long transitions |

Initial timings are 160 ms for effects, 320 ms for ordinary spatial movement and
500 ms for slower transitions. These are prototype choices inspired by the motion
system, not a claim to reproduce Google's spring token values exactly.

## Color generation

`prismos/theme.py` owns the generator. `scripts/generate-design.py` generates the
preview palette data and original vector assets. Native QML reads the same
generator through `prismctl theme`. Body text color is selected using WCAG
contrast; generated pairs are regression tested.

The current algorithm extracts a sample seed with Pillow and constructs HSL
tones. HCT/Monet, automatic wallpaper updates, themed application icons and
third-party GTK/Qt application theming are explicit later work.

## Fidelity and preview boundaries

The browser preview is a review aid, not the operating system. Its hardware
controls, media player, files, terminal and application contents are simulated
and labeled. Native code launches installed Linux apps and changes actual
supported system controls. The v0.3 native shell includes power/session actions,
tray, MPRIS and inline wireless selection/passwords. PIN pairing uses Blueman and
advanced network configuration uses NetworkManager's editor. Native wallpaper
customization and actual app-surface morphs remain planned.
