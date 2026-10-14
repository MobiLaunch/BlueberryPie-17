pragma ComponentBehavior: Bound
import QtQuick
import "../services"

Column {
    id: root
    property string kind: "output"
    property var devices: []
    property var current: null
    width: parent ? parent.width : 340
    spacing: 8
    Label {
        width: parent.width
        text: root.kind === "output" ? "Play through" : "Microphone"
        font.weight: Font.DemiBold
    }
    Label {
        width: parent.width
        visible: root.devices.length === 0
        text: root.kind === "output" ? "No playback devices available" : "No microphones available"
        font.pixelSize: 12
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: root.devices
        delegate: PillButton {
            required property var modelData
            width: root.width
            implicitHeight: 54
            filled: modelData.selected
            enabled: !AudioState.busy && !AudioState.adjusting
            text: modelData.label + (modelData.selected ? "\nSelected" : "")
            Accessible.name: (root.kind === "output" ? "Play through " : "Use microphone ") + modelData.label + (modelData.selected ? ", selected" : "")
            Accessible.checkable: true
            Accessible.checked: modelData.selected
            onClicked: AudioState.change("select", root.kind, modelData)
        }
    }
    Label {
        width: parent.width
        visible: root.current !== null
        text: root.current ? root.current.label + (root.current.muted ? " · Muted" : " · " + root.current.value + "%") : ""
        wrapMode: Text.WordWrap
        font.pixelSize: 12
    }
    ExpressiveSlider {
        width: parent.width
        visible: root.current !== null
        enabled: root.current !== null && root.current.available && !AudioState.busy
        label: root.kind === "output" ? "Output volume" : "Microphone level"
        symbol: root.kind === "output" ? "volume" : "microphone"
        modelValue: root.current ? root.current.value : 0
        // Refresh waits until release, preserving the thumb and its target.
        onPressedChanged: AudioState.adjusting = pressed
        onCommitted: level => {
            if (root.current && !AudioState.busy)
                AudioState.change("volume", root.kind, root.current, level);
        }
    }
    PillButton {
        width: parent.width
        implicitHeight: 40
        visible: root.current !== null
        enabled: root.current !== null && root.current.available && !AudioState.busy
        filled: root.current !== null && root.current.muted
        text: root.kind === "output" ? (root.current && root.current.muted ? "Unmute output" : "Mute output") : (root.current && root.current.muted ? "Unmute microphone" : "Mute microphone")
        onClicked: if (root.current)
            AudioState.change("mute", root.kind, root.current, root.current.muted ? 0 : 1)
    }
}
