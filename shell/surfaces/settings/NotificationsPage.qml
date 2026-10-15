import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    title: "Notifications"
    SettingsGroup {
        width: parent.width
        ToggleRow {
            width: parent.width
            title: "Do Not Disturb"
            supporting: on ? "Notifications arrive quietly" : "Notifications show a banner"
            symbol: on ? "notifications_off" : "dnd"
            on: SystemBridge.snapshot.settings.dnd
            onSwitched: SystemBridge.action("dnd")
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Current notifications"
        ListRow {
            width: parent.width
            title: Notifications.count === 0 ? "You're all caught up" : Notifications.count + (Notifications.count === 1 ? " notification" : " notifications")
            supporting: Notifications.count === 0 ? "New notifications appear in the shade" : "From " + Notifications.groups.length + (Notifications.groups.length === 1 ? " app" : " apps")
            symbol: "notifications"
            interactive: false
        }
        ListRow {
            width: parent.width
            title: "Clear all notifications"
            symbol: "trash"
            enabled: Notifications.count > 0
            onClicked: Notifications.clear()
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        text: "Important notifications from apps keep a distinct color so they stand out, even in Do Not Disturb."
        role: "bodyMedium"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
}
