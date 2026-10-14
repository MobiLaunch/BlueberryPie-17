pragma Singleton
import QtQuick
import Quickshell.Io

QtObject {
    id: root
    property var roles: ({
            primary: "#d3c2f0",
            primaryStrong: "#5b3c94",
            onPrimary: "#19151e",
            onPrimaryStrong: "#ffffff",
            secondary: "#c9e5d8",
            onSecondary: "#19151e",
            tertiary: "#f2d2ba",
            onTertiary: "#19151e",
            surface: "#faf9fb",
            onSurface: "#19151e",
            surfaceContainer: "#f1eef5",
            onSurfaceContainer: "#19151e",
            surfaceHigh: "#e5e0ec",
            onSurfaceHigh: "#19151e",
            outline: "#807985",
            error: "#a8332a",
            onError: "#ffffff"
        })
    property string font: "Roboto"
    property bool reducedMotion: SystemBridge.snapshot.settings.reduced_motion || false
    property bool dark: SystemBridge.snapshot.settings.dark || false
    property int fast: reducedMotion ? 0 : 160
    property int standard: reducedMotion ? 0 : 320
    property int slow: reducedMotion ? 0 : 500
    readonly property color primary: roles.primary
    readonly property color primaryStrong: roles.primaryStrong
    readonly property color onPrimary: roles.onPrimary
    readonly property color onPrimaryStrong: roles.onPrimaryStrong
    readonly property color secondary: roles.secondary
    readonly property color onSecondary: roles.onSecondary
    readonly property color tertiary: roles.tertiary
    readonly property color onTertiary: roles.onTertiary
    readonly property color surface: roles.surface
    readonly property color onSurface: roles.onSurface
    readonly property color surfaceContainer: roles.surfaceContainer
    readonly property color surfaceHigh: roles.surfaceHigh
    readonly property color onSurfaceHigh: roles.onSurfaceHigh
    readonly property color outline: roles.outline

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
                    if (data.primary)
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
    property Connections statusConnection: Connections {
        target: SystemBridge
        function onSnapshotChanged() {
            root.refresh();
        }
    }
}
