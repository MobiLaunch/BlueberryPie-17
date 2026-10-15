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
    DisplaySettings {
        width: parent.width
    }
}
