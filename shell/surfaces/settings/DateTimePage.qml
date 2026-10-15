import QtQuick
import QtQuick.Layouts
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Date & time"
    readonly property var zones: InstallerState.timezones.map(name => ({
                id: name,
                label: name.replace(/_/g, " ")
            }))
    Component.onCompleted: {
        DateTimeState.refresh();
        InstallerState.loadOptions();
    }
    SettingsGroup {
        width: parent.width
        title: "Clock"
        ToggleRow {
            width: parent.width
            title: "24-hour clock"
            supporting: Theme.clock24 ? "For example 17:30" : "For example 5:30 PM"
            symbol: "recents"
            on: Theme.clock24
            onSwitched: value => DateTimeState.set24h(value)
        }
        ToggleRow {
            width: parent.width
            title: "Set time automatically"
            supporting: !DateTimeState.available ? "Needs systemd-timedated" : DateTimeState.ntp ? (DateTimeState.inSync ? "Synchronized with the internet" : "Waiting to synchronize") : "Off"
            symbol: "wifi"
            enabled: DateTimeState.available && !DateTimeState.busy
            on: DateTimeState.ntp
            onSwitched: value => DateTimeState.setAutomatic(value)
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Time zone"
        ListRow {
            width: parent.width
            interactive: false
            title: DateTimeState.timezone.length > 0 ? DateTimeState.timezone.replace(/_/g, " ") : "Unknown"
            supporting: "Current time zone"
            symbol: "globe"
        }
        Rectangle {
            width: parent.width
            height: 340
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            ChoiceList {
                anchors.fill: parent
                anchors.margins: 12
                searchable: true
                model: page.zones
                current: DateTimeState.timezone
                onPicked: id => DateTimeState.setTimezone(id)
            }
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        visible: DateTimeState.error.length > 0 || DateTimeState.notice.length > 0
        text: DateTimeState.error.length > 0 ? DateTimeState.error : DateTimeState.notice
        role: "bodyMedium"
        color: DateTimeState.error.length > 0 ? Theme.error : Theme.primary
        wrapMode: Text.WordWrap
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        text: "Changing the time zone or automatic time asks for administrator approval."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
}
