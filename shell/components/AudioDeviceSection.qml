pragma ComponentBehavior: Bound
import QtQuick
import "."
import "../services"

// Device list, level and mute for either outputs or microphones.
Column {
    id: root
    property string kind: "output"
    property var devices: []
    property var current: null
    width: parent ? parent.width : 340
    spacing: 8
    Label {
        width: parent.width
        leftPadding: 4
        text: root.kind === "output" ? "Play through" : "Microphone"
        role: "titleSmall"
        color: Theme.primary
    }
    Label {
        width: parent.width
        leftPadding: 4
        visible: root.devices.length === 0
        text: root.kind === "output" ? "No playback devices available" : "No microphones available"
        role: "bodyMedium"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: root.devices
        delegate: ListRow {
            required property var modelData
            width: root.width
            implicitHeight: 60
            title: modelData.label
            supporting: modelData.selected ? "Selected" : ""
            symbol: root.kind === "output" ? "volume" : "microphone"
            selected: modelData.selected
            chipColor: modelData.selected ? Theme.primary : Theme.secondaryContainer
            chipInk: modelData.selected ? Theme.primaryInk : Theme.secondaryContainerInk
            enabled: !AudioState.busy && !AudioState.adjusting
            Accessible.name: (root.kind === "output" ? "Play through " : "Use microphone ") + modelData.label + (modelData.selected ? ", selected" : "")
            Accessible.checkable: true
            Accessible.checked: modelData.selected
            onClicked: AudioState.change("select", root.kind, modelData)
            Symbol {
                visible: modelData.selected
                width: 20
                height: 20
                name: "check"
                color: Theme.primaryContainerInk
            }
        }
    }
    Label {
        width: parent.width
        leftPadding: 4
        visible: root.current !== null
        text: root.current ? root.current.label + (root.current.muted ? " · Muted" : " · " + root.current.value + "%") : ""
        wrapMode: Text.WordWrap
        role: "bodySmall"
        color: Theme.surfaceVariantInk
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
        visible: root.current !== null
        enabled: root.current !== null && root.current.available && !AudioState.busy
        variant: root.current !== null && root.current.muted ? "filled" : "tonal"
        symbol: root.kind === "output" ? (root.current && root.current.muted ? "volume" : "volume_off") : (root.current && root.current.muted ? "microphone" : "microphone_off")
        text: root.kind === "output" ? (root.current && root.current.muted ? "Unmute output" : "Mute output") : (root.current && root.current.muted ? "Unmute microphone" : "Mute microphone")
        onClicked: if (root.current)
            AudioState.change("mute", root.kind, root.current, root.current.muted ? 0 : 1)
    }
}
