import QtQuick
import QtQuick.Layouts
import "../services"

Rectangle {
    id: root
    signal closeRequested
    implicitHeight: content.implicitHeight + 32
    radius: 28
    color: Theme.surfaceHigh
    Column {
        id: content
        x: 16
        y: 16
        width: parent.width - 32
        spacing: 12
        RowLayout {
            width: parent.width
            Symbol {
                name: "headphones"
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
            }
            Label {
                text: "Sound & microphone"
                font.weight: Font.DemiBold
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            PillButton {
                text: "×"
                implicitWidth: 36
                implicitHeight: 36
                Accessible.name: "Close sound devices"
                onClicked: root.closeRequested()
            }
        }
        RowLayout {
            width: parent.width
            ExpressiveLoader {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                visible: AudioState.busy
            }
            Label {
                text: AudioState.busy ? "Just a moment…" : AudioState.notice
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.pixelSize: 12
            }
            PillButton {
                text: "Refresh"
                implicitHeight: 36
                enabled: !AudioState.busy && !AudioState.adjusting
                onClicked: AudioState.refresh(true)
            }
        }
        Label {
            width: parent.width
            text: AudioState.error || (!AudioState.devices.available ? AudioState.devices.error || "Sound service unavailable" : "")
            visible: text.length > 0
            wrapMode: Text.WordWrap
            font.pixelSize: 12
            color: Theme.roles.error
            Accessible.role: Accessible.AlertMessage
        }
        RowLayout {
            width: parent.width
            PillButton {
                text: "Output"
                Layout.fillWidth: true
                filled: AudioState.tab === "output"
                Accessible.checkable: true
                Accessible.checked: filled
                onClicked: AudioState.tab = "output"
            }
            PillButton {
                text: "Microphone"
                Layout.fillWidth: true
                filled: AudioState.tab === "input"
                Accessible.checkable: true
                Accessible.checked: filled
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
            visible: AudioState.tab === "input"
            text: "Muting affects the selected microphone. Other microphones can remain available to apps."
            wrapMode: Text.WordWrap
            font.pixelSize: 11
        }
    }
}
