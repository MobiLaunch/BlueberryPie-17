import QtQuick
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Snackbar for system feedback (errors, quiet notification summaries).
PanelWindow {
    id: root
    anchors.bottom: true
    margins.bottom: 112
    implicitWidth: Math.min(480, screen.width - 40)
    implicitHeight: bubble.height + 8
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-toast"
    color: "transparent"
    mask: Region {}
    visible: ShellState.toast.length > 0 && ShellState.activeScreen === screen
    Rectangle {
        id: bubble
        width: parent.width
        height: Math.max(52, message.implicitHeight + 28)
        radius: Theme.shape.extraLarge - 4
        color: Theme.inverseSurface
        Label {
            id: message
            anchors.fill: parent
            anchors.margins: 14
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            text: ShellState.toast
            role: "bodyMedium"
            color: Theme.inverseSurfaceInk
            wrapMode: Text.WordWrap
            maximumLineCount: 3
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
    }
}
