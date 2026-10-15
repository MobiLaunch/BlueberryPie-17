import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Notifications"
    readonly property var apps: {
        const names = Notifications.mutedApps.concat(Notifications.seenApps, Notifications.groups.map(group => group.app));
        return names.filter((name, index) => names.indexOf(name) === index).sort((a, b) => a.localeCompare(b));
    }
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
        title: "Quiet hours"
        ToggleRow {
            width: parent.width
            title: "Turn on automatically"
            supporting: Notifications.schedule.enabled ? "Every day from " + Notifications.schedule.start + " to " + Notifications.schedule.end : "Do Not Disturb follows a schedule"
            symbol: "moon"
            on: Notifications.schedule.enabled
            onSwitched: value => SystemBridge.setQuietHours(value, Notifications.schedule.start, Notifications.schedule.end)
        }
        Rectangle {
            width: parent.width
            height: 172
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            visible: Notifications.schedule.enabled
            Row {
                anchors.centerIn: parent
                spacing: 24
                Column {
                    spacing: 2
                    Label {
                        text: "From"
                        role: "labelMedium"
                        color: Theme.surfaceVariantInk
                    }
                    TimeField {
                        value: Notifications.schedule.start
                        onEdited: value => SystemBridge.setQuietHours(true, value, Notifications.schedule.end)
                    }
                }
                Column {
                    spacing: 2
                    Label {
                        text: "Until"
                        role: "labelMedium"
                        color: Theme.surfaceVariantInk
                    }
                    TimeField {
                        value: Notifications.schedule.end
                        onEdited: value => SystemBridge.setQuietHours(true, Notifications.schedule.start, value)
                    }
                }
            }
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
    SettingsGroup {
        width: parent.width
        title: "App notifications"
        visible: page.apps.length > 0
        Repeater {
            model: page.apps
            delegate: ToggleRow {
                required property string modelData
                width: parent ? parent.width : 600
                title: modelData
                supporting: on ? "Shows banners and appears in the shade" : "Muted"
                symbol: on ? "notifications" : "notifications_off"
                on: !Notifications.isMuted(modelData)
                onSwitched: value => SystemBridge.muteApp(modelData, !value)
            }
        }
    }
    Label {
        width: parent.width
        visible: page.apps.length === 0
        leftPadding: 16
        rightPadding: 16
        text: "Apps that send notifications will appear here so you can mute them one by one."
        role: "bodyMedium"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        text: "Important notifications keep a distinct color and still break through Do Not Disturb or a muted app."
        role: "bodyMedium"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
}
