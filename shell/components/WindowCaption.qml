import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "."
import "../services"
import "../services/LaunchTracking.js" as LaunchTracking

// Caption controls for the focused window: icon and title, minimize, maximize or
// restore, a snap/float menu, and close. Wayland gives the shell no per-window
// title bars, so these live in the status bar and always act on the focused window.
Item {
    id: root
    readonly property var window: Windows.focused
    readonly property var app: window ? SystemBridge.apps.find(item => LaunchTracking.matches(item, window.class)) || null : null
    readonly property bool idle: Windows.busy
    implicitWidth: row.implicitWidth
    implicitHeight: 36
    visible: window !== null
    opacity: visible ? 1 : 0
    Behavior on opacity {
        NumberAnimation {
            duration: Theme.fast
        }
    }
    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 4
        Image {
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            Layout.rightMargin: 6
            sourceSize: Qt.size(40, 40)
            source: Quickshell.iconPath(root.app ? root.app.icon : (root.window ? root.window.class.toLowerCase() : ""), "application-x-executable")
        }
        Label {
            Layout.maximumWidth: 320
            text: root.window ? (root.window.title || root.window.class) : ""
            role: "labelLarge"
            color: Theme.surfaceVariantInk
            elide: Text.ElideRight
            Layout.rightMargin: 8
        }
        IconButton {
            symbol: "minimize"
            implicitWidth: 32
            implicitHeight: 32
            iconSize: 18
            enabled: !root.idle
            Accessible.name: "Minimize window"
            onClicked: Windows.minimize(root.window.address)
        }
        IconButton {
            symbol: root.window && root.window.maximized ? "restore" : "maximize"
            implicitWidth: 32
            implicitHeight: 32
            iconSize: 18
            enabled: !root.idle
            Accessible.name: root.window && root.window.maximized ? "Restore window size" : "Maximize window"
            onClicked: Windows.maximize(root.window.address)
        }
        IconButton {
            id: arrange
            symbol: "snap_left"
            implicitWidth: 32
            implicitHeight: 32
            iconSize: 18
            enabled: !root.idle
            Accessible.name: "Snap or float window"
            onClicked: snapMenu.open()
            ExpressiveMenu {
                id: snapMenu
                y: arrange.height + 6
                MenuItem {
                    text: "Snap to left half"
                    onTriggered: Windows.snap(root.window.address, "left")
                }
                MenuItem {
                    text: "Snap to right half"
                    onTriggered: Windows.snap(root.window.address, "right")
                }
                MenuItem {
                    text: root.window && root.window.floating ? "Tile window" : "Float window"
                    onTriggered: Windows.toggleFloat(root.window.address)
                }
                MenuSeparator {}
                MenuItem {
                    text: "Show all windows"
                    onTriggered: ShellState.toggleRecents(ShellState.focusedScreen())
                }
            }
        }
        IconButton {
            id: closeButton
            symbol: "close"
            implicitWidth: 32
            implicitHeight: 32
            iconSize: 18
            enabled: !root.idle
            Accessible.name: "Close window"
            onClicked: Windows.close(root.window.address)
            // Destructive action: error container on hover, like Material window controls.
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: Theme.errorContainer
                opacity: closeButton.hovered ? 1 : 0
                z: -1
                Behavior on opacity {
                    NumberAnimation {
                        duration: Theme.fast
                    }
                }
            }
        }
    }
}
