import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Share this computer's internet over Wi-Fi: state, network name, password and a new
// password. Used in the Quick Settings tile details and in Settings > Network.
ColumnLayout {
    id: root
    property bool active: true
    readonly property var info: NetShareState.hotspot
    readonly property var state: SystemBridge.snapshot.hotspot
    spacing: 8
    onActiveChanged: {
        if (active)
            NetShareState.refreshHotspot();
        else
            NetShareState.closeHotspot();
    }
    Component.onCompleted: if (active)
        NetShareState.refreshHotspot()
    Component.onDestruction: NetShareState.closeHotspot()
    Label {
        Layout.fillWidth: true
        text: !root.state.available ? (root.state.label || "The hotspot is not available.") : "Share this computer's internet over Wi-Fi. A single Wi-Fi adapter may leave your network while the hotspot is on."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Label {
            text: "Network name"
            role: "labelMedium"
            color: Theme.surfaceVariantInk
        }
        Label {
            objectName: "hotspot-ssid"
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignRight
            text: root.info.loaded ? root.info.ssid : "…"
            role: "titleSmall"
            elide: Text.ElideRight
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 4
        Label {
            text: "Password"
            role: "labelMedium"
            color: Theme.surfaceVariantInk
        }
        Label {
            objectName: "hotspot-password"
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignRight
            text: !root.info.loaded ? "…" : NetShareState.revealed ? root.info.password : "••••••••••••"
            role: "titleSmall"
            font.letterSpacing: NetShareState.revealed ? 1 : 0
            elide: Text.ElideRight
        }
        IconButton {
            objectName: "hotspot-reveal"
            implicitWidth: 36
            implicitHeight: 36
            iconSize: 18
            symbol: NetShareState.revealed ? "hide" : "show"
            enabled: root.info.loaded
            Accessible.name: NetShareState.revealed ? "Hide password" : "Show password"
            onClicked: NetShareState.revealed = !NetShareState.revealed
        }
        IconButton {
            objectName: "hotspot-copy"
            implicitWidth: 36
            implicitHeight: 36
            iconSize: 18
            symbol: "copy"
            enabled: root.info.loaded
            Accessible.name: "Copy password"
            onClicked: NetShareState.copyPassword()
        }
    }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        PillButton {
            objectName: "hotspot-toggle"
            text: root.state.enabled ? "Turn off hotspot" : "Turn on hotspot"
            variant: root.state.enabled ? "tonal" : "filled"
            implicitHeight: 40
            enabled: root.state.available
            onClicked: SystemBridge.action("hotspot")
        }
        PillButton {
            objectName: "hotspot-regenerate"
            text: "New password"
            variant: "text"
            implicitHeight: 40
            enabled: root.info.loaded && !NetShareState.busy
            onClicked: NetShareState.regeneratePassword()
        }
    }
    Label {
        Layout.fillWidth: true
        visible: NetShareState.error.length > 0 || NetShareState.notice.length > 0
        text: NetShareState.error.length > 0 ? NetShareState.error : NetShareState.notice
        role: "bodySmall"
        color: NetShareState.error.length > 0 ? Theme.error : Theme.primary
        wrapMode: Text.WordWrap
    }
}
