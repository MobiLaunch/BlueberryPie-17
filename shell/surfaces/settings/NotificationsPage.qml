import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Notifications"
    readonly property var apps: {
        const names = Notifications.mutedApps.concat(Notifications.focusApps, Notifications.seenApps, Notifications.groups.map(group => group.app));
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
        title: "Focus mode"
        ToggleRow {
            width: parent.width
            objectName: "focus-toggle"
            title: "Focus mode"
            supporting: on ? "Notifications from the apps below stay quiet" : Notifications.focusApps.length === 0 ? "Choose the apps to quiet, then switch it on" : "Off"
            symbol: "focus"
            on: Notifications.focusOn
            onSwitched: SystemBridge.action("focus")
        }
        Repeater {
            model: page.apps
            delegate: ToggleRow {
                required property string modelData
                required property int index
                objectName: "focus-app-" + index
                width: parent ? parent.width : 600
                title: modelData
                supporting: on ? "Quiet during Focus mode" : "Notifies as usual"
                symbol: on ? "notifications_off" : "notifications"
                on: Notifications.focusApps.indexOf(modelData) >= 0
                onSwitched: value => SystemBridge.setFocusApp(modelData, value)
            }
        }
        Label {
            width: parent.width
            visible: page.apps.length === 0
            leftPadding: 16
            rightPadding: 16
            topPadding: 8
            bottomPadding: 8
            text: "Apps that send notifications will appear here so you can choose which ones Focus mode quiets."
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
            wrapMode: Text.WordWrap
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
        title: "Lock screen"
        ToggleRow {
            width: parent.width
            objectName: "lock-count-toggle"
            title: "Show notification count"
            supporting: on ? "The lock screen says how many are waiting, never what they say" : "The lock screen shows no notification information"
            symbol: "lock"
            on: SystemBridge.snapshot.settings.lock_notifications !== false
            onSwitched: value => SystemBridge.setLockScreenCount(value)
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Notification history"
        ToggleRow {
            width: parent.width
            objectName: "history-toggle"
            title: "Keep recent notifications"
            supporting: on ? "The last " + Notifications.historyLimit + " are kept until you log out" : "Off. Nothing is remembered once a notification is dismissed"
            symbol: "recents"
            on: Notifications.historyEnabled
            onSwitched: value => SystemBridge.setNotificationHistory(value)
        }
        ListRow {
            width: parent.width
            visible: Notifications.historyEnabled && Notifications.history.length === 0
            interactive: false
            title: "No history yet"
            supporting: "New notifications will be listed here"
            symbol: "notifications"
        }
        Repeater {
            model: Notifications.historyEnabled ? Notifications.history.slice(0, 30) : []
            delegate: ListRow {
                required property var modelData
                width: parent ? parent.width : 600
                interactive: false
                objectName: "history-item"
                title: modelData.summary || modelData.app
                supporting: modelData.app + " · " + Theme.timeText(new Date(modelData.time)) + (modelData.body ? " · " + modelData.body.replace(/\s+/g, " ").slice(0, 80) : "")
                symbol: modelData.critical ? "warning" : "notifications"
                chipColor: modelData.critical ? Theme.errorContainer : Theme.secondaryContainer
                chipInk: modelData.critical ? Theme.errorContainerInk : Theme.secondaryContainerInk
            }
        }
        ListRow {
            width: parent.width
            objectName: "history-clear"
            visible: Notifications.historyEnabled
            enabled: Notifications.history.length > 0
            title: "Clear history"
            symbol: "trash"
            onClicked: Notifications.clearHistory()
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
