pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "."
import QtQuick.Layouts
import "../services"

// Nearby Wi-Fi networks or Bluetooth devices, with inline password entry.
Rectangle {
    id: root
    property string kind: "wifi"
    property string selected: ""
    property bool showClose: true
    property bool showAdvanced: true
    readonly property var adapterState: kind === "wifi" ? Wireless.wifi : Wireless.bluetooth
    signal closeRequested
    implicitHeight: content.implicitHeight + 32
    radius: Theme.shape.extraLarge
    color: Theme.surfaceContainer
    onKindChanged: reset()
    onVisibleChanged: if (!visible)
        reset()
    function reset() {
        selected = "";
        Wireless.editing = false;
    }
    onSelectedChanged: Wireless.editing = selected.length > 0 && kind === "wifi"
    Column {
        id: content
        x: 16
        y: 16
        width: parent.width - 32
        spacing: 10
        RowLayout {
            width: parent.width
            spacing: 8
            Label {
                text: root.kind === "wifi" ? "Wi-Fi networks" : "Bluetooth devices"
                role: "titleMedium"
                Layout.fillWidth: true
                Layout.leftMargin: 4
            }
            ExpressiveLoader {
                Layout.preferredWidth: 26
                Layout.preferredHeight: 26
                visible: Wireless.busy
            }
            PillButton {
                text: "Refresh"
                symbol: "refresh"
                variant: "tonal"
                implicitHeight: 40
                enabled: !Wireless.busy
                onClicked: {
                    Wireless.operation = "";
                    Wireless.refresh(root.kind, true);
                }
            }
            IconButton {
                visible: root.showClose
                symbol: "close"
                implicitWidth: 40
                implicitHeight: 40
                iconSize: 20
                Accessible.name: "Close connections"
                onClicked: root.closeRequested()
            }
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: text.length > 0
            text: Wireless.busy ? (Wireless.operation === "connect" ? "Connecting…" : "Just a moment…") : Wireless.notice
            role: "bodySmall"
            color: Theme.surfaceVariantInk
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: Wireless.error.length > 0
            text: Wireless.error
            color: Theme.error
            wrapMode: Text.WordWrap
            role: "bodySmall"
            Accessible.role: Accessible.AlertMessage
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: !root.adapterState.available || !root.adapterState.enabled
            text: root.adapterState.available ? "Turn on " + (root.kind === "wifi" ? "Wi-Fi" : "Bluetooth") + " to find connections." : "No available adapter. Check that the service and device are enabled."
            wrapMode: Text.WordWrap
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: root.adapterState.available && root.adapterState.enabled && !Wireless.busy && (root.kind === "wifi" ? Wireless.wifi.networks.length === 0 : Wireless.bluetooth.devices.length === 0)
            text: "Nothing nearby yet. Try Refresh."
            wrapMode: Text.WordWrap
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
        Repeater {
            model: root.kind === "wifi" ? Wireless.wifi.networks : []
            delegate: Column {
                id: networkRow
                required property var modelData
                width: content.width
                spacing: 6
                readonly property bool expanded: root.selected === modelData.bssid + "/" + modelData.interface
                onExpandedChanged: if (!expanded)
                    password.clear()
                ListRow {
                    width: parent.width
                    implicitHeight: 64
                    title: networkRow.modelData.ssid
                    supporting: (networkRow.modelData.connected ? "Connected" : networkRow.modelData.profile ? "Saved" : networkRow.modelData.secured ? networkRow.modelData.security : "Open network") + "  ·  " + networkRow.modelData.signal + "%"
                    symbol: "wifi"
                    chipColor: networkRow.modelData.connected ? Theme.primary : Theme.secondaryContainer
                    chipInk: networkRow.modelData.connected ? Theme.primaryInk : Theme.secondaryContainerInk
                    selected: networkRow.modelData.connected || networkRow.expanded
                    enabled: !Wireless.busy
                    Accessible.name: networkRow.modelData.ssid + ", signal " + networkRow.modelData.signal + " percent" + (networkRow.modelData.connected ? ", connected" : "")
                    onClicked: {
                        root.selected = networkRow.expanded ? "" : networkRow.modelData.bssid + "/" + networkRow.modelData.interface;
                        Wireless.error = "";
                        Wireless.notice = "";
                        if (networkRow.expanded && password.visible)
                            password.forceActiveFocus();
                    }
                    Symbol {
                        visible: networkRow.modelData.secured
                        width: 20
                        height: 20
                        name: "lock"
                        color: Theme.surfaceVariantInk
                    }
                }
                Column {
                    width: parent.width
                    spacing: 8
                    visible: networkRow.expanded
                    Label {
                        width: parent.width
                        leftPadding: 4
                        visible: !networkRow.modelData.supported
                        text: "This network needs advanced setup."
                        wrapMode: Text.WordWrap
                        role: "bodySmall"
                    }
                    ExpressiveTextField {
                        id: password
                        width: parent.width
                        visible: !networkRow.modelData.connected && networkRow.modelData.secured && networkRow.modelData.key !== null
                        enabled: !Wireless.busy
                        placeholderText: networkRow.modelData.profile ? "Password (leave empty to use saved)" : "Network password"
                        echoMode: TextInput.Password
                        maximumLength: 64
                        selectByMouse: true
                        inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText | Qt.ImhHiddenText
                        Accessible.name: "Password for " + networkRow.modelData.ssid
                        font.family: Theme.font
                        color: Theme.surfaceInk
                        onAccepted: connectButton.clicked()
                        Component.onDestruction: clear()
                    }
                    PillButton {
                        id: connectButton
                        width: parent.width
                        enabled: !Wireless.busy
                        variant: "filled"
                        text: networkRow.modelData.connected ? "Disconnect" : networkRow.modelData.supported ? "Connect" : "Advanced network settings"
                        onClicked: {
                            if (Wireless.busy)
                                return;
                            if (!networkRow.modelData.supported)
                                SystemBridge.action("network-settings");
                            else if (networkRow.modelData.connected) {
                                Wireless.disconnectWifi(networkRow.modelData);
                                root.selected = "";
                            } else if (Wireless.connectWifi(networkRow.modelData, password.text)) {
                                password.clear();
                                root.selected = "";
                            }
                        }
                    }
                }
            }
        }
        Repeater {
            model: root.kind === "bluetooth" ? Wireless.bluetooth.devices : []
            delegate: ListRow {
                id: deviceRow
                required property var modelData
                width: content.width
                implicitHeight: 64
                title: modelData.name
                supporting: modelData.connected ? "Connected · tap to disconnect" : modelData.paired ? "Paired · tap to connect" : "Not paired · opens Bluetooth settings"
                symbol: "bluetooth"
                chipColor: modelData.connected ? Theme.primary : Theme.secondaryContainer
                chipInk: modelData.connected ? Theme.primaryInk : Theme.secondaryContainerInk
                selected: modelData.connected
                enabled: !Wireless.busy
                Accessible.name: (modelData.connected ? "Disconnect " : modelData.paired ? "Connect " : "Pair ") + modelData.name
                onClicked: {
                    if (modelData.paired)
                        Wireless.deviceAction(modelData);
                    else
                        SystemBridge.action("bluetooth-settings");
                }
            }
        }
        PillButton {
            visible: root.showAdvanced
            width: parent.width
            variant: "tonal"
            text: root.kind === "wifi" ? "Advanced network settings" : "Pair a new device…"
            onClicked: SystemBridge.action(root.kind === "wifi" ? "network-settings" : "bluetooth-settings")
        }
    }
}
