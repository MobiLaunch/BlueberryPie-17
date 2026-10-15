import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Floating dock: launcher, pinned apps, other running apps and system shortcuts.
// Width follows its content, so nothing is ever clipped on a normal screen.
PanelWindow {
    id: root
    anchors.bottom: true
    margins.bottom: 10
    implicitWidth: Math.min(screen.width - 24, row.implicitWidth + 28)
    implicitHeight: 76
    exclusiveZone: implicitHeight + margins.bottom + 4
    WlrLayershell.namespace: "prism-dock"
    color: "transparent"
    function activate(item, x, y) {
        const open = Windows.forApp(item.app);
        if (open.length === 0) {
            ShellState.launch(item.app, root.screen, x, y);
            return;
        }
        // Cycle through that app's windows, starting with the one after the focused.
        const index = open.findIndex(window => window.focused);
        Windows.show(open[(index + 1) % open.length]);
    }
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Theme.withAlpha(Theme.surfaceContainer, 0.94)
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.6)
        Flickable {
            id: flick
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            contentWidth: row.implicitWidth
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Row {
                id: row
                x: Math.max(0, (flick.width - width) / 2)
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                IconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    symbol: "apps_grid"
                    variant: "filled"
                    implicitWidth: 52
                    implicitHeight: 52
                    Accessible.name: "All applications"
                    onClicked: ShellState.toggleDrawer(root.screen)
                }
                Repeater {
                    model: Applications.dockApps
                    delegate: DockItem {
                        id: pinned
                        required property var modelData
                        app: modelData
                        anchors.verticalCenter: parent.verticalCenter
                        onActivated: (x, y) => root.activate(pinned, x, y)
                    }
                }
                Rectangle {
                    visible: Applications.extraRunning.length > 0
                    anchors.verticalCenter: parent.verticalCenter
                    width: 1
                    height: 34
                    color: Theme.outlineVariant
                }
                Repeater {
                    model: Applications.extraRunning
                    delegate: DockItem {
                        id: running
                        required property var modelData
                        app: modelData
                        windows: modelData.windows
                        anchors.verticalCenter: parent.verticalCenter
                        onActivated: (x, y) => root.activate(running, x, y)
                    }
                }
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    width: 1
                    height: 34
                    color: Theme.outlineVariant
                }
                IconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    symbol: "recents"
                    variant: "tonal"
                    implicitWidth: 48
                    implicitHeight: 48
                    Accessible.name: "Recent apps"
                    onClicked: ShellState.toggleRecents(root.screen)
                }
                IconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    symbol: "folder"
                    variant: "tonal"
                    implicitWidth: 48
                    implicitHeight: 48
                    Accessible.name: "Files"
                    onClicked: ShellState.openFiles(root.screen)
                }
                IconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    symbol: "store"
                    variant: "tonal"
                    implicitWidth: 48
                    implicitHeight: 48
                    Accessible.name: "Prism Store"
                    onClicked: ShellState.openStore(root.screen)
                }
                IconButton {
                    anchors.verticalCenter: parent.verticalCenter
                    symbol: "settings"
                    variant: "tonal"
                    implicitWidth: 48
                    implicitHeight: 48
                    Accessible.name: "Settings"
                    onClicked: ShellState.openSettings(root.screen)
                }
            }
        }
    }
}
