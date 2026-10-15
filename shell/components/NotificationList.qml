import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Header, empty state and grouped notifications. Hosted in a scroll view.
Column {
    id: root
    spacing: 12
    RowLayout {
        width: parent.width
        Label {
            text: "Notifications"
            role: "titleMedium"
            Layout.fillWidth: true
            Layout.leftMargin: 4
        }
        PillButton {
            visible: Notifications.count > 0
            text: "Clear all"
            variant: "tonal"
            implicitHeight: 40
            onClicked: Notifications.clear()
        }
    }
    Column {
        visible: Notifications.count === 0
        width: parent.width
        spacing: 8
        topPadding: 24
        bottomPadding: 24
        Symbol {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 40
            height: 40
            name: SystemBridge.snapshot.settings.dnd ? "notifications_off" : "notifications"
            color: Theme.surfaceVariantInk
        }
        Label {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: SystemBridge.snapshot.settings.dnd ? "Do Not Disturb is on" : "You're all caught up"
            role: "bodyLarge"
            color: Theme.surfaceVariantInk
        }
    }
    Repeater {
        model: Notifications.groups
        delegate: NotificationGroup {
            required property var modelData
            width: root.width
            group: modelData
        }
    }
}
