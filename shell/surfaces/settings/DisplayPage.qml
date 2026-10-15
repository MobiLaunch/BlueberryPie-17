import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    title: "Display"
    SliderRow {
        width: parent.width
        title: "Brightness"
        symbol: "brightness"
        supporting: SystemBridge.snapshot.brightness.available ? "" : "No adjustable backlight on this device"
        enabled: SystemBridge.snapshot.brightness.available
        modelValue: SystemBridge.snapshot.brightness.value
        onCommitted: level => SystemBridge.action("brightness", level)
    }
    SettingsGroup {
        width: parent.width
        title: "Night Light"
        ToggleRow {
            width: parent.width
            title: "Night Light"
            supporting: !SystemBridge.snapshot.night_light.available ? "Needs the hyprsunset package" : on ? "Warmer colors for the evening" : "Off"
            symbol: "night_light"
            enabled: SystemBridge.snapshot.night_light.available
            on: SystemBridge.snapshot.night_light.enabled
            onSwitched: SystemBridge.action("night-light")
        }
        SliderRow {
            width: parent.width
            title: "Warmth"
            symbol: "night_light"
            from: 2500
            to: 5500
            stepSize: 100
            keyStep: 100
            enabled: SystemBridge.snapshot.night_light.available
            modelValue: SystemBridge.snapshot.settings.night_temp || 3800
            valueText: (SystemBridge.snapshot.settings.night_temp || 3800) + " K"
            onCommitted: level => SystemBridge.action("night-temp", Math.round(level / 100) * 100)
        }
    }
    DisplaySettings {
        width: parent.width
    }
}
