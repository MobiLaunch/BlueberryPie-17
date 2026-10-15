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
2. Active Quick Settings tiles are pills in the `primary` role; inactive tiles are
   squircles on `surfaceContainerHighest`; a pressed tile tightens its corners
   (Android 12+ behavior). Large tiles carry a title and state; compact tiles are
   icon-only with a tooltip and accessible name.
3. A large brightness track sits above a regular Quick Settings grid (two large
   tiles per row, then four compact tiles). Wide screens split notifications into
   their own card beside Quick Settings, as Android does on large displays.
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

## Roles, naming and tokens

Components read semantic roles from `Theme.qml`, never hex values. The role names
are Material 3's, with one deliberate exception: **content colors are `*Ink`**
(`Theme.primaryInk` is M3 `onPrimary`, `Theme.surfaceInk` is `onSurface`). In Qt 6.12
a property named `onX` beside a property `x` silently loses its binding and renders
black, which made default text unreadable in dark mode. Do not reintroduce `on…`
property names; `tests/test_shell_runtime.py` guards this.

Also in `Theme.qml`: the M3 type scale (`Theme.type`, used through `Label.role`),
the M3 shape scale (`Theme.shape`), and motion durations that collapse to zero
under reduced motion. Shared components: `PillButton` (filled, tonal, neutral,
outlined, text), `IconButton`, `QuickTile`, `ListRow`, `ToggleRow`, `SliderRow`,
`SettingsGroup`/`SettingsPage`, `FilterChip`, `SearchField`, `AppTile`, `DockItem`,
`PaletteSwatch`, `KeyCap`, `NotificationCard`/`Group`/`List`, `MediaCard`, `StateLayer`.

Qt's Material style pins `Button` paddings, so controls that draw their own
content set all four paddings explicitly. Inside `components/`, import `"."` after
`QtQuick.Controls` so `Label` is the themed one.

## Color generation

`prismos/hct.py` implements CAM16 and the HCT solver; `prismos/theme.py` builds the
Material 3 Tonal Spot scheme (primary chroma 36, secondary 16, tertiary 24 at +60°,
neutrals 6/8) with M3's tone mapping for the light and dark role sets.
`scripts/generate-design.py` writes preview tokens (a documented legacy mapping of
the same scheme) and the original vector icons, including `IconData.js` for the
native recolored symbols. QML reads the scheme through `prismctl theme`.

Because tone fixes luminance, role pairs meet contrast by construction; the pairs
are also regression tested, and the solver is tested against the published scheme
for source `#6750A4`. Not implemented: Monet's wallpaper quantizer (a simplified
Material-style scorer is used), other scheme variants (Vibrant, Expressive, Fidelity),
themed application icons and third-party GTK/Qt/Electron theming.

## Fidelity and preview boundaries

The browser preview is a review aid, not the operating system. Its hardware
controls, media player, files, terminal and application contents are simulated
and labeled. Native code launches installed Linux apps and changes actual
supported system controls. The v0.4 native shell includes power/session actions,
tray, MPRIS, inline wireless selection/passwords and sound-device controls.
Output and microphone tabs keep the sound surface compact on narrow screens.
PIN pairing uses Blueman and
advanced network configuration uses NetworkManager's editor. A wallpaper picker and actual app-surface morphs remain planned. The preview has
not been rebuilt to match the v0.9 dual shade and Settings app; it shares tokens and
icons with the native shell but is otherwise the v0.8 review aid.
