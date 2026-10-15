import QtQuick
import "../../components"
import "../../services"

// Read-only reference of the session's key and gesture bindings (config/hypr/hyprland.lua).
SettingsPage {
    id: page
    title: "Shortcuts & gestures"
    readonly property var groups: [
        {
            title: "Apps and panels",
            rows: [
                {label: "App launcher", keys: ["Super", "Space"]},
                {label: "Recent apps", keys: ["Super", "Tab"]},
                {label: "Quick Settings and notifications", keys: ["Super", "Q"]},
                {label: "Settings", keys: ["Super", ","]},
                {label: "Files", keys: ["Super", "E"]},
                {label: "Prism Store", keys: ["Super", "S"]},
                {label: "Terminal", keys: ["Super", "Enter"]}
            ]
        },
        {
            title: "Windows and session",
            rows: [
                {label: "Move a window", keys: ["Alt", "drag"]},
                {label: "Resize a window", keys: ["Alt", "right-drag"]},
                {label: "Close the focused window", keys: ["Super", "Shift", "Q"]},
                {label: "Lock the screen", keys: ["Super", "L"]}
            ]
        },
        {
            title: "Hardware keys",
            rows: [
                {label: "Volume up and down", keys: ["Vol +", "Vol −"]},
                {label: "Mute speakers or microphone", keys: ["Mute", "Mic mute"]},
                {label: "Screen brightness", keys: ["Bright +", "Bright −"]}
            ]
        },
        {
            title: "Touchpad",
            rows: [
                {label: "Switch workspace", keys: ["3-finger swipe left or right"]},
                {label: "Open the launcher", keys: ["4-finger swipe up"]},
                {label: "Open Quick Settings", keys: ["4-finger swipe down"]}
            ]
        }
    ]
    Repeater {
        model: page.groups
        delegate: SettingsGroup {
            required property var modelData
            width: page.width > 0 ? Math.min(page.width - 8, 720) : 600
            title: modelData.title
            Repeater {
                model: modelData.rows
                delegate: ListRow {
                    required property var modelData
                    width: parent ? parent.width : 600
                    implicitHeight: 56
                    interactive: false
                    title: modelData.label
                    Row {
                        spacing: 6
                        Repeater {
                            model: modelData.keys
                            delegate: KeyCap {
                                required property string modelData
                                text: modelData
                            }
                        }
                    }
                }
            }
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        text: "Touchpad gestures need a compatible touchpad. Bindings live in the session's Hyprland configuration."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
}
