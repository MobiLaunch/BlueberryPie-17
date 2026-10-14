import QtQuick
import QtQuick.Controls
import "../services"

Menu {
    id: root
    property var app: null
    signal launchRequested
    padding: 8
    background: Rectangle {
        radius: 22
        color: Theme.surfaceContainer
        border.width: 1
        border.color: Theme.outline
    }
    delegate: MenuItem {
        id: item
        implicitHeight: 44
        contentItem: Label {
            text: item.text
            verticalAlignment: Text.AlignVCenter
            color: Theme.onSurface
            leftPadding: 14
            rightPadding: 14
        }
        background: Rectangle {
            radius: 16
            color: item.highlighted ? Theme.primary : "transparent"
        }
    }
    MenuItem {
        text: "Open"
        onTriggered: root.launchRequested()
    }
    MenuItem {
        text: root.app && Applications.isPinned(root.app.id) ? "Unpin from dock" : "Pin to dock"
        onTriggered: if (root.app)
            Applications.togglePin(root.app.id)
    }
}
