import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Context menu for an application: launch/focus, window actions and dock pinning.
ExpressiveMenu {
    id: root
    property var app: null
    property var windows: []
    readonly property bool running: windows.length > 0
    signal launchRequested
    MenuItem {
        text: root.running ? "Switch to " + (root.app ? root.app.name : "app") : "Open"
        onTriggered: root.launchRequested()
    }
    MenuItem {
        visible: root.running && root.app && root.app.id.length > 0
        text: "New window"
        onTriggered: if (root.app)
            ShellState.launch(root.app, ShellState.focusedScreen(), ShellState.focusedScreen().width / 2, ShellState.focusedScreen().height / 2)
    }
    MenuItem {
        visible: root.running
        text: root.windows.length > 1 ? "Close all windows" : "Close window"
        onTriggered: Windows.closeMany(root.windows.map(window => window.address))
    }
    MenuSeparator {
        visible: root.running
    }
    MenuItem {
        visible: root.app !== null && root.app.id.length > 0
        text: root.app && Applications.isPinned(root.app.id) ? "Unpin from dock" : "Pin to dock"
        onTriggered: if (root.app)
            Applications.togglePin(root.app.id)
    }
    MenuItem {
        visible: root.app !== null && root.app.id.length > 0
        text: "App info"
        onTriggered: if (root.app)
            ShellState.openAppInfo(root.app, ShellState.focusedScreen())
    }
    MenuSeparator {}
    MenuItem {
        text: "Refresh applications"
        onTriggered: SystemBridge.refreshApps()
    }
    MenuItem {
        text: "Browse more apps"
        onTriggered: ShellState.openStore(ShellState.focusedScreen())
    }
}
