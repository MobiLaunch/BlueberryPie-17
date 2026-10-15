import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Output and microphone device chooser (shared by Quick Settings and Settings).
Rectangle {
    id: root
    property bool showClose: true
    signal closeRequested
    implicitHeight: content.implicitHeight + 32
    radius: Theme.shape.extraLarge
    color: Theme.surfaceContainer
    Column {
        id: content
        x: 16
        y: 16
        width: parent.width - 32
        spacing: 12
        RowLayout {
            width: parent.width
            spacing: 8
            Label {
                text: "Sound devices"
                role: "titleMedium"
                Layout.fillWidth: true
                Layout.leftMargin: 4
            }
            ExpressiveLoader {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                visible: AudioState.busy
            }
            PillButton {
                text: "Refresh"
                symbol: "refresh"
                variant: "tonal"
                implicitHeight: 40
                enabled: !AudioState.busy && !AudioState.adjusting
                onClicked: AudioState.refresh(true)
            }
            IconButton {
                visible: root.showClose
                symbol: "close"
                implicitWidth: 40
                implicitHeight: 40
                iconSize: 20
                Accessible.name: "Close sound devices"
                onClicked: root.closeRequested()
            }
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: text.length > 0
            text: AudioState.busy ? "Just a moment…" : AudioState.notice
            wrapMode: Text.WordWrap
            role: "bodySmall"
            color: Theme.surfaceVariantInk
        }
        Label {
            width: parent.width
            leftPadding: 4
            text: AudioState.error || (!AudioState.devices.available ? AudioState.devices.error || "Sound service unavailable" : "")
            visible: text.length > 0
            wrapMode: Text.WordWrap
            role: "bodySmall"
            color: Theme.error
            Accessible.role: Accessible.AlertMessage
        }
        Row {
            spacing: 8
            FilterChip {
                text: "Output"
                selected: AudioState.tab === "output"
                onClicked: AudioState.tab = "output"
            }
            FilterChip {
                text: "Microphone"
                selected: AudioState.tab === "input"
                onClicked: AudioState.tab = "input"
            }
        }
        AudioDeviceSection {
            kind: "output"
            visible: AudioState.tab === "output"
            devices: AudioState.devices.outputs
            current: AudioState.devices.output
        }
        AudioDeviceSection {
            kind: "input"
            visible: AudioState.tab === "input"
            devices: AudioState.devices.inputs
            current: AudioState.devices.input
        }
        Label {
            width: parent.width
            leftPadding: 4
            visible: AudioState.tab === "input"
            text: "Muting affects the selected microphone. Other microphones can remain available to apps."
            wrapMode: Text.WordWrap
            role: "bodySmall"
            color: Theme.surfaceVariantInk
        }
    }
}
