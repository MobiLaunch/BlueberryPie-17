pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../services"

Rectangle {
    id: root
    property string kind: "wifi"
    property string selected: ""
    readonly property var adapterState: kind === "wifi" ? Wireless.wifi : Wireless.bluetooth
    signal closeRequested
    implicitHeight: content.implicitHeight + 32
    radius: 28
    color: Theme.surfaceHigh
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
            Label {
                text: root.kind === "wifi" ? "Choose a network" : "Your devices"
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            PillButton {
                text: "×"
                implicitWidth: 36
                implicitHeight: 36
                Accessible.name: "Close connections"
                onClicked: root.closeRequested()
            }
        }
        RowLayout {
            width: parent.width
            ExpressiveLoader {
                Layout.preferredWidth: 26
                Layout.preferredHeight: 26
                visible: Wireless.busy
            }
            Label {
                Layout.fillWidth: true
                text: Wireless.busy ? (Wireless.operation === "connect" ? "Connecting…" : "Just a moment…") : Wireless.notice
                visible: text.length > 0
                font.pixelSize: 12
            }
            PillButton {
                text: "Refresh"
                implicitHeight: 36
                enabled: !Wireless.busy
                onClicked: {
                    Wireless.operation = "";
                    Wireless.refresh(root.kind, true);
                }
            }
        }
        Label {
            width: parent.width
            visible: Wireless.error.length > 0
            text: Wireless.error
            color: Theme.roles.error
            wrapMode: Text.WordWrap
            font.pixelSize: 12
            Accessible.role: Accessible.AlertMessage
        }
        Label {
            width: parent.width
            visible: !root.adapterState.available || !root.adapterState.enabled
            text: root.adapterState.available ? "Turn on " + (root.kind === "wifi" ? "Wi-Fi" : "Bluetooth") + " to find connections." : "No available adapter. Check that the service and device are enabled."
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        Label {
            width: parent.width
            visible: root.adapterState.available && root.adapterState.enabled && !Wireless.busy && (root.kind === "wifi" ? Wireless.wifi.networks.length === 0 : Wireless.bluetooth.devices.length === 0)
            text: "Nothing nearby yet. Try Refresh."
            wrapMode: Text.WordWrap
            font.pixelSize: 12
        }
        Repeater {
            model: root.kind === "wifi" ? Wireless.wifi.networks : []
            delegate: Column {
                id: networkRow
                required property var modelData
                width: content.width
                spacing: 8
                readonly property bool expanded: root.selected === modelData.bssid + "/" + modelData.interface
                onExpandedChanged: if (!expanded)
                    password.clear()
                PillButton {
                    width: parent.width
                    implicitHeight: 58
                    filled: networkRow.modelData.connected || networkRow.expanded
                    enabled: !Wireless.busy
                    text: networkRow.modelData.ssid + "  ·  " + networkRow.modelData.signal + "%\n" + (networkRow.modelData.connected ? "Connected" : networkRow.modelData.profile ? "Saved" : networkRow.modelData.secured ? networkRow.modelData.security : "Open network")
                    onClicked: {
                        root.selected = networkRow.expanded ? "" : networkRow.modelData.bssid + "/" + networkRow.modelData.interface;
                        Wireless.error = "";
                        Wireless.notice = "";
                        if (networkRow.expanded && password.visible)
                            password.forceActiveFocus();
                    }
                }
                Column {
                    width: parent.width
                    spacing: 8
                    visible: networkRow.expanded
                    Label {
                        width: parent.width
                        visible: !networkRow.modelData.supported
                        text: "This network needs advanced setup."
                        wrapMode: Text.WordWrap
                        font.pixelSize: 12
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
                        color: Theme.onSurface
                        onAccepted: connectButton.clicked()
                        Component.onDestruction: clear()
                    }
                    PillButton {
                        id: connectButton
                        width: parent.width
                        enabled: !Wireless.busy
                        filled: true
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
            delegate: Column {
                id: deviceRow
                required property var modelData
                width: content.width
                spacing: 5
                Label {
                    width: parent.width
                    text: deviceRow.modelData.name
                    wrapMode: Text.WordWrap
                    font.weight: Font.DemiBold
                }
                PillButton {
                    width: parent.width
                    implicitHeight: 40
                    enabled: !Wireless.busy
                    filled: deviceRow.modelData.connected
                    text: deviceRow.modelData.connected ? "Disconnect" : deviceRow.modelData.paired ? "Connect" : "Pair in Bluetooth settings"
                    Accessible.name: text + " " + deviceRow.modelData.name
                    onClicked: {
                        if (deviceRow.modelData.paired)
                            Wireless.deviceAction(deviceRow.modelData);
                        else
                            SystemBridge.action("bluetooth-settings");
                    }
                }
            }
        }
        PillButton {
            width: parent.width
            implicitHeight: 38
            text: root.kind === "wifi" ? "Advanced network settings" : "Pair a new device…"
            onClicked: SystemBridge.action(root.kind === "wifi" ? "network-settings" : "bluetooth-settings")
        }
    }
}
