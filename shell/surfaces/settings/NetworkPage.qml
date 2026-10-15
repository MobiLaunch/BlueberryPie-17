import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Network & internet"
    readonly property var wifi: SystemBridge.snapshot.wifi
    Component.onCompleted: {
        Wireless.watchedKind = "wifi";
        Wireless.error = "";
        Wireless.notice = "";
        Wireless.refresh("wifi");
    }
    Component.onDestruction: Wireless.watchedKind = ""
    SettingsGroup {
        width: parent.width
        ToggleRow {
            width: parent.width
            title: "Wi-Fi"
            supporting: page.wifi.available ? page.wifi.label : "No wireless adapter found"
            symbol: page.wifi.enabled ? "wifi" : "wifi_off"
            on: page.wifi.enabled
            enabled: page.wifi.available
            onSwitched: SystemBridge.action("wifi")
        }
    }
    WirelessPanel {
        width: parent.width
        kind: "wifi"
        showClose: false
        showAdvanced: false
        visible: page.wifi.available
        height: visible ? implicitHeight : 0
    }
    SettingsGroup {
        width: parent.width
        title: "Hotspot"
        Rectangle {
            width: parent.width
            height: hotspotPanel.implicitHeight + 28
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            HotspotPanel {
                id: hotspotPanel
                x: 16
                y: 14
                width: parent.width - 32
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "VPN"
        Rectangle {
            width: parent.width
            height: vpnPanel.implicitHeight + 28
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            VpnPanel {
                id: vpnPanel
                x: 16
                y: 14
                width: parent.width - 32
            }
        }
    }
    SettingsGroup {
        width: parent.width
        ListRow {
            width: parent.width
            title: "Advanced network settings"
            supporting: "Hidden networks, VPN, Ethernet and enterprise Wi-Fi"
            symbol: "settings"
            onClicked: SystemBridge.action("network-settings")
            Symbol {
                width: 20
                height: 20
                name: "arrow"
                color: Theme.surfaceVariantInk
            }
        }
    }
}
