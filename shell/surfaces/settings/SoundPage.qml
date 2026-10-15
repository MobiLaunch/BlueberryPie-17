import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    title: "Sound"
    Component.onCompleted: AudioState.panelOpen = true
    Component.onDestruction: AudioState.panelOpen = false
    SliderRow {
        width: parent.width
        title: "Output volume"
        symbol: SystemBridge.snapshot.volume.muted ? "volume_off" : "volume"
        enabled: SystemBridge.snapshot.volume.available && !AudioState.writing
        modelValue: SystemBridge.snapshot.volume.value
        supporting: SystemBridge.snapshot.volume.available ? "" : "No audio output found"
        onCommitted: level => SystemBridge.action("volume", level)
    }
    SettingsGroup {
        width: parent.width
        ToggleRow {
            width: parent.width
            title: "Sound"
            supporting: on ? "Playing through the selected output" : "Muted"
            symbol: on ? "volume" : "volume_off"
            on: !SystemBridge.snapshot.volume.muted
            enabled: SystemBridge.snapshot.volume.available && !AudioState.writing
            onSwitched: SystemBridge.action("mute")
        }
        ToggleRow {
            width: parent.width
            title: "Microphone"
            supporting: SystemBridge.snapshot.microphone.available ? (on ? "On" : "Muted") : "No microphone found"
            symbol: on ? "microphone" : "microphone_off"
            on: SystemBridge.snapshot.microphone.available && !SystemBridge.snapshot.microphone.muted
            enabled: SystemBridge.snapshot.microphone.available && !AudioState.writing
            onSwitched: SystemBridge.action("microphone-mute")
        }
    }
    SoundPanel {
        width: parent.width
        showClose: false
    }
}
