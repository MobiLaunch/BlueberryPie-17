import QtQuick
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.launching !== null && ShellState.activeScreen === screen
    property var lastApp: ({
            name: "",
            icon: "application-x-executable"
        })
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-launch"
    color: "transparent"
    visible: opened || splash.opacity > .01
    // Fade when a matching Hyprland window opens/focuses, with a bounded fallback.
    // This still animates a shell surface rather than morphing the app's surface.
    // Keep it non-interactive; the real application receives input immediately.
    mask: Region {}
    onOpenedChanged: if (opened) {
        lastApp = ShellState.launching;
        expansion.restart();
    }
    Rectangle {
        id: splash
        property real progress: 0
        x: ShellState.launchOrigin.x + (root.width / 2 - width / 2 - ShellState.launchOrigin.x) * progress
        y: ShellState.launchOrigin.y + (root.height / 2 - height / 2 - ShellState.launchOrigin.y) * progress
        width: 64 + (Math.min(760, root.width - 60) - 64) * progress
        height: 64 + (Math.min(520, root.height - 120) - 64) * progress
        radius: 30 + (10 * progress)
        color: Theme.primary
        opacity: root.opened ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Column {
            anchors.centerIn: parent
            spacing: 20
            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 56
                height: 56
                source: Quickshell.iconPath(root.lastApp.icon, "application-x-executable")
                sourceSize: Qt.size(56, 56)
            }
            Label {
                text: root.lastApp.name
                color: Theme.onPrimary
                font.pixelSize: 20
                font.weight: Font.DemiBold
                anchors.horizontalCenter: parent.horizontalCenter
                opacity: splash.progress
                width: Math.min(500, splash.width - 48)
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignHCenter
            }
            ExpressiveLoader {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: root.opened && splash.progress > .7
            }
        }
        NumberAnimation {
            id: expansion
            target: splash
            property: "progress"
            from: 0
            to: 1
            duration: Theme.standard
            easing.type: Easing.OutBack
            easing.overshoot: .5
        }
    }
}
