import QtQuick

// Test double for Quickshell.Wayland.ScreencopyView: paints a flat color once it has a source.
Rectangle {
    property var captureSource: null
    property bool live: false
    property bool paintCursors: false
    property size constraintSize: Qt.size(0, 0)
    readonly property bool hasContent: captureSource !== null
    color: hasContent ? "#2e7d32" : "transparent"
}
