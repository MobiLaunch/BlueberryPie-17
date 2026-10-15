import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    title: "Pointer & keyboard"
    SettingsGroup {
        width: parent.width
        title: "Touchpad"
        ToggleRow {
            width: parent.width
            title: "Natural scrolling"
            supporting: "Content follows your fingers"
            symbol: "mouse"
            on: InputState.values.natural_scroll === true
            enabled: !InputState.busy
            onSwitched: value => InputState.setValue("natural_scroll", value)
        }
        ToggleRow {
            width: parent.width
            title: "Tap to click"
            supporting: "Use a light tap on the touchpad"
            symbol: "mouse"
            on: InputState.values.tap_to_click === true
            enabled: !InputState.busy
            onSwitched: value => InputState.setValue("tap_to_click", value)
        }
    }
    SliderRow {
        width: parent.width
        title: "Pointer speed"
        symbol: "mouse"
        from: -1
        to: 1
        stepSize: 0.1
        keyStep: 0.1
        enabled: !InputState.busy
        modelValue: InputState.values.pointer_speed
        valueText: (InputState.values.pointer_speed > 0 ? "+" : "") + Number(InputState.values.pointer_speed).toFixed(1)
        onCommitted: level => InputState.setValue("pointer_speed", Number(level).toFixed(1))
    }
    SliderRow {
        width: parent.width
        title: "Key repeat speed"
        symbol: "keyboard"
        from: 10
        to: 60
        stepSize: 5
        keyStep: 5
        enabled: !InputState.busy
        modelValue: InputState.values.repeat_rate
        valueText: Math.round(InputState.values.repeat_rate) + " / s"
        onCommitted: level => InputState.setValue("repeat_rate", Math.round(level))
    }
    Label {
        width: parent.width
        visible: InputState.error.length > 0
        leftPadding: 16
        text: InputState.error
        color: Theme.error
        wrapMode: Text.WordWrap
    }
}
