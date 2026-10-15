import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Bluetooth & devices"
    readonly property var bluetooth: SystemBridge.snapshot.bluetooth
    Component.onCompleted: {
        Wireless.watchedKind = "bluetooth";
        Wireless.error = "";
        Wireless.notice = "";
        Wireless.refresh("bluetooth");
    }
    Component.onDestruction: Wireless.watchedKind = ""
    SettingsGroup {
        width: parent.width
        ToggleRow {
            width: parent.width
            title: "Bluetooth"
            supporting: page.bluetooth.available ? (page.bluetooth.enabled ? "On" : "Off") : "No Bluetooth adapter found"
            symbol: page.bluetooth.enabled ? "bluetooth" : "bluetooth_off"
            on: page.bluetooth.enabled
            enabled: page.bluetooth.available
            onSwitched: SystemBridge.action("bluetooth")
        }
    }
    WirelessPanel {
        width: parent.width
        kind: "bluetooth"
        showClose: false
        visible: page.bluetooth.available
        height: visible ? implicitHeight : 0
    }
}
