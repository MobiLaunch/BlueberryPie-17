import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Shown on every screen while an alarm or timer is ringing.
PanelWindow {
    id: root
    readonly property var ringing: ClockState.ringing
    anchors.top: true
    margins.top: 56
    implicitWidth: Math.min(420, screen.width - 24)
    implicitHeight: card.height + 12
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "prism-alarm"
    color: "transparent"
    visible: ringing !== null
    Rectangle {
        id: card
        width: parent.width
        height: content.implicitHeight + 32
        radius: Theme.shape.extraLarge
        color: Theme.primaryContainer
        border.width: 2
        border.color: Theme.primary
        ColumnLayout {
            id: content
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12
            RowLayout {
                spacing: 14
                Rectangle {
                    Layout.preferredWidth: 52
                    Layout.preferredHeight: 52
                    radius: 18
                    color: Theme.primary
                    Symbol {
                        anchors.centerIn: parent
                        width: 28
                        height: 28
                        name: "recents"
                        color: Theme.primaryInk
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: root.ringing ? root.ringing.title : ""
                        role: "titleLarge"
                        color: Theme.primaryContainerInk
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.ringing ? root.ringing.detail : ""
                        role: "bodyMedium"
                        color: Theme.primaryContainerInk
                        elide: Text.ElideRight
                    }
                }
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                PillButton {
                    visible: root.ringing !== null && root.ringing.kind === "alarm"
                    text: "Snooze 10 min"
                    variant: "neutral"
                    onClicked: ClockState.snooze(10)
                }
                PillButton {
                    text: "Dismiss"
                    variant: "filled"
                    onClicked: ClockState.dismiss()
                }
            }
        }
    }
}
