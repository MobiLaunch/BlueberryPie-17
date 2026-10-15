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
