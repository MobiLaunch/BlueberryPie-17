import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// VPN profiles from NetworkManager: connect, disconnect and pick the one the Quick Settings
// tile switches. PrismOS never creates VPNs or handles their credentials.
ColumnLayout {
    id: root
    property bool active: true
    readonly property var vpnData: NetShareState.vpn
    spacing: 8
    onActiveChanged: if (active)
        NetShareState.refreshVpn()
    Component.onCompleted: if (active)
        NetShareState.refreshVpn()
    Label {
        Layout.fillWidth: true
        visible: root.vpnData.loaded && root.vpnData.profiles.length === 0
        objectName: "vpn-empty"
        text: "No VPN is set up yet. Add one in Network settings and it will appear here."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: root.vpnData.profiles
        delegate: RowLayout {
            required property var modelData
            required property int index
            Layout.fillWidth: true
            spacing: 8
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Label {
                    objectName: "vpn-name-" + index
                    Layout.fillWidth: true
                    text: modelData.name
                    role: "titleSmall"
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: modelData.active ? "Connected" : modelData.uuid === root.vpnData.preferred ? "Used by the tile" : modelData.type === "wireguard" ? "WireGuard" : "VPN"
                    role: "bodySmall"
                    color: modelData.active ? Theme.primary : Theme.surfaceVariantInk
                }
            }
            PillButton {
                objectName: "vpn-toggle-" + index
                text: modelData.active ? "Disconnect" : "Connect"
                variant: modelData.active ? "tonal" : "filled"
                implicitHeight: 36
                enabled: !NetShareState.busy
                onClicked: modelData.active ? NetShareState.disconnectVpn(modelData.uuid) : NetShareState.connectVpn(modelData.uuid)
            }
        }
    }
    Label {
        Layout.fillWidth: true
        visible: NetShareState.error.length > 0
        text: NetShareState.error
        role: "bodySmall"
        color: Theme.error
        wrapMode: Text.WordWrap
    }
    PillButton {
        objectName: "vpn-settings"
        text: "Open network settings"
        variant: "text"
        implicitHeight: 40
        onClicked: SystemBridge.action("network-settings")
    }
}
