pragma Singleton
import QtQuick
import Quickshell.Io

// Semantic Material 3 roles, type scale, shape and motion tokens.
// Role values come from `prismctl theme` (HCT Tonal Spot); the defaults below
// are the Lilac light scheme so the first frame is already coherent.
QtObject {
    id: root
    property var roles: ({
            primary: "#64558f",
            onPrimary: "#ffffff",
            primaryContainer: "#e8ddff",
            onPrimaryContainer: "#201047",
            inversePrimary: "#cfbdfe",
            secondary: "#625b71",
            onSecondary: "#ffffff",
            secondaryContainer: "#e8def8",
            onSecondaryContainer: "#1e192b",
            tertiary: "#7d5260",
            onTertiary: "#ffffff",
            tertiaryContainer: "#ffd9e3",
            onTertiaryContainer: "#31101d",
            error: "#ba1a1a",
            onError: "#ffffff",
            errorContainer: "#ffdad6",
            onErrorContainer: "#410002",
            surface: "#fdf7ff",
            onSurface: "#1d1b20",
            surfaceDim: "#ded8e0",
            surfaceBright: "#fdf7ff",
            surfaceContainerLowest: "#ffffff",
            surfaceContainerLow: "#f8f2fa",
            surfaceContainer: "#f2ecf4",
            surfaceContainerHigh: "#ece6ee",
            surfaceContainerHighest: "#e6e1e9",
            surfaceVariant: "#e7e0ec",
            onSurfaceVariant: "#49454e",
            outline: "#7a757f",
            outlineVariant: "#cac4cf",
            inverseSurface: "#322f35",
            inverseOnSurface: "#f5eff7",
            scrim: "#000000",
            shadow: "#000000"
        })

    // Typography: Google Sans Flex / Roboto Flex when installed, Roboto otherwise.
    readonly property var fontFamilies: ["Google Sans Flex", "Roboto Flex", "Roboto", "Noto Sans"]
    readonly property string font: {
        const installed = Qt.fontFamilies();
        return fontFamilies.find(name => installed.indexOf(name) >= 0) || "sans-serif";
    }

    readonly property bool reducedMotion: SystemBridge.snapshot.settings.reduced_motion || false
    readonly property bool dark: SystemBridge.snapshot.settings.dark || false
    readonly property int fast: reducedMotion ? 0 : 160
    readonly property int standard: reducedMotion ? 0 : 320
    readonly property int slow: reducedMotion ? 0 : 500

    // Material 3 type scale (size, line height, weight, tracking). "Emphasized"
    // variants carry the Expressive weight bump.
    readonly property var typeBase: ({
            displayLarge: {size: 57, line: 64, weight: Font.Normal, tracking: -0.25},
            displayMedium: {size: 45, line: 52, weight: Font.Normal, tracking: 0},
            displaySmall: {size: 36, line: 44, weight: Font.Normal, tracking: 0},
            headlineLarge: {size: 32, line: 40, weight: Font.Normal, tracking: 0},
            headlineMedium: {size: 28, line: 36, weight: Font.Normal, tracking: 0},
            headlineSmall: {size: 24, line: 32, weight: Font.Normal, tracking: 0},
            headlineSmallEmphasized: {size: 24, line: 32, weight: Font.DemiBold, tracking: 0},
            titleLarge: {size: 22, line: 28, weight: Font.Normal, tracking: 0},
            titleLargeEmphasized: {size: 22, line: 28, weight: Font.DemiBold, tracking: 0},
            titleMedium: {size: 16, line: 24, weight: Font.Medium, tracking: 0.15},
            titleSmall: {size: 14, line: 20, weight: Font.Medium, tracking: 0.1},
            bodyLarge: {size: 16, line: 24, weight: Font.Normal, tracking: 0.5},
            bodyMedium: {size: 14, line: 20, weight: Font.Normal, tracking: 0.25},
            bodySmall: {size: 12, line: 16, weight: Font.Normal, tracking: 0.4},
            labelLarge: {size: 14, line: 20, weight: Font.Medium, tracking: 0.1},
            labelMedium: {size: 12, line: 16, weight: Font.Medium, tracking: 0.5},
            labelSmall: {size: 11, line: 16, weight: Font.Medium, tracking: 0.5}
        })

    // User text size (Settings > Wallpaper & style). Line heights scale with the text.
    readonly property real fontScale: SystemBridge.snapshot.settings.font_scale || 1
    readonly property var type: {
        const scaled = {};
        for (const name in typeBase) {
            const entry = typeBase[name];
            scaled[name] = {
                size: Math.round(entry.size * fontScale),
                line: Math.round(entry.line * fontScale),
                weight: entry.weight,
                tracking: entry.tracking
            };
        }
        return scaled;
    }

    // Corner radii (Material 3 shape scale).
    readonly property var shape: ({
            none: 0,
            extraSmall: 4,
            small: 8,
            medium: 12,
            large: 16,
            largeIncreased: 20,
            extraLarge: 28,
            extraLargeIncreased: 32,
            extraExtraLarge: 48
        })

    readonly property color primary: roles.primary
    readonly property color primaryInk: roles.onPrimary
    readonly property color primaryContainer: roles.primaryContainer
    readonly property color primaryContainerInk: roles.onPrimaryContainer
    readonly property color inversePrimary: roles.inversePrimary
    readonly property color secondary: roles.secondary
    readonly property color secondaryInk: roles.onSecondary
    readonly property color secondaryContainer: roles.secondaryContainer
    readonly property color secondaryContainerInk: roles.onSecondaryContainer
    readonly property color tertiary: roles.tertiary
    readonly property color tertiaryInk: roles.onTertiary
    readonly property color tertiaryContainer: roles.tertiaryContainer
    readonly property color tertiaryContainerInk: roles.onTertiaryContainer
    readonly property color error: roles.error
    readonly property color errorInk: roles.onError
    readonly property color errorContainer: roles.errorContainer
    readonly property color errorContainerInk: roles.onErrorContainer
    readonly property color surface: roles.surface
    readonly property color surfaceInk: roles.onSurface
    readonly property color surfaceDim: roles.surfaceDim
    readonly property color surfaceBright: roles.surfaceBright
    readonly property color surfaceContainerLowest: roles.surfaceContainerLowest
    readonly property color surfaceContainerLow: roles.surfaceContainerLow
    readonly property color surfaceContainer: roles.surfaceContainer
    readonly property color surfaceContainerHigh: roles.surfaceContainerHigh
    readonly property color surfaceContainerHighest: roles.surfaceContainerHighest
    readonly property color surfaceVariant: roles.surfaceVariant
    readonly property color surfaceVariantInk: roles.onSurfaceVariant
    readonly property color outline: roles.outline
    readonly property color outlineVariant: roles.outlineVariant
    readonly property color inverseSurface: roles.inverseSurface
    readonly property color inverseSurfaceInk: roles.inverseOnSurface
    readonly property color scrim: roles.scrim

    // Wallpaper-adjacent text must hold contrast against any wallpaper art.
    readonly property color wallpaperInk: dark ? "#f5eafa" : "#3b2b53"

    function withAlpha(color, alpha) {
        return Qt.rgba(color.r, color.g, color.b, alpha);
    }
    function hex(color) {
        const part = value => ("0" + Math.round(value * 255).toString(16)).slice(-2);
        return "#" + part(color.r) + part(color.g) + part(color.b);
    }

    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    property Process reader: Process {
        command: ["prismctl", "theme"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.primary && data.surfaceContainerHigh)
                        root.roles = data;
                } catch (e) {
                    console.warn("PrismOS theme:", e);
                }
            }
        }
    }
    property Timer initial: Timer {
        interval: 1
        running: true
        onTriggered: root.refresh()
    }
    // Recompute roles only when the seed or light/dark preference changes,
    // not on every 5-second status poll.
    readonly property string themeKey: (SystemBridge.snapshot.settings.seed || "") + "|" + (SystemBridge.snapshot.settings.scheme || "") + "|" + dark
    onThemeKeyChanged: refresh()
}
