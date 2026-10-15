import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Battery & power"
    readonly property var battery: SystemBridge.snapshot.battery
    Rectangle {
        width: parent.width
        height: 120
        radius: Theme.shape.extraLargeIncreased
        color: page.battery.available && page.battery.value <= 15 && !page.battery.charging ? Theme.errorContainer : Theme.primaryContainer
        Symbol {
            x: 24
            anchors.verticalCenter: parent.verticalCenter
            width: 56
            height: 56
            name: page.battery.charging ? "battery_charging" : "battery"
            level: page.battery.available ? page.battery.value / 100 : -1
            color: Theme.primaryContainerInk
        }
        Column {
            x: 96
            anchors.verticalCenter: parent.verticalCenter
            Label {
                text: page.battery.available ? page.battery.value + "%" : "Plugged in"
                role: "displaySmall"
                color: Theme.primaryContainerInk
            }
            Label {
                text: page.battery.available ? (page.battery.charging ? "Charging" : "On battery") : "This device has no battery"
                role: "bodyLarge"
                color: Theme.primaryContainerInk
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Power mode"
        visible: SystemBridge.snapshot.profile.available
        Repeater {
            model: [
                {
                    id: "power-saver",
                    profile: "power-saver",
                    title: "Power saver",
                    note: "Longest battery life",
                    symbol: "battery"
                },
                {
                    id: "power-balanced",
                    profile: "balanced",
                    title: "Balanced",
                    note: "A good mix of speed and battery",
                    symbol: "battery"
                },
                {
                    id: "power-performance",
                    profile: "performance",
                    title: "Performance",
                    note: "Fastest, uses more power",
                    symbol: "bolt"
                }
            ]
            delegate: ListRow {
                required property var modelData
                width: parent ? parent.width : 600
                title: modelData.title
                supporting: modelData.note
                symbol: modelData.symbol
                selected: SystemBridge.snapshot.profile.profile === modelData.profile
                Accessible.role: Accessible.RadioButton
                onClicked: SystemBridge.action(modelData.id)
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Session"
        ListRow {
            width: parent.width
            title: "Lock screen"
            supporting: SystemBridge.snapshot.power.lock ? "Lock now (Super + L)" : "Lock screen is not installed"
            symbol: "lock"
            enabled: SystemBridge.snapshot.power.lock
            onClicked: SystemBridge.action("lock")
        }
        ListRow {
            width: parent.width
            title: "Power options"
            supporting: "Sleep, sign out, restart or power off"
            symbol: "power"
            onClicked: ShellState.openPower(ShellState.focusedScreen())
        }
    }
}
