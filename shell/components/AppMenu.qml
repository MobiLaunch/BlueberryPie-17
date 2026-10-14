import QtQuick
import QtQuick.Controls
import "../services"

ExpressiveMenu {
    id: root
    property var app: null
    signal launchRequested
    MenuItem {
        text: "Open"
        onTriggered: root.launchRequested()
    }
    MenuItem {
        text: root.app && Applications.isPinned(root.app.id) ?
              "Unpin from dock" : "Pin to dock"
        onTriggered: if (root.app)
            Applications.togglePin(root.app.id)
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
