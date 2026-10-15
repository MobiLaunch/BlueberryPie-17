import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Inline details for a Quick Settings tile (long-press or right-click the tile).
Rectangle {
    id: root
    property string tile: ""
    signal closeRequested
    signal settingsRequested(string page)
    readonly property var info: tile.length > 0 ? TilesState.describe(tile) : null
    implicitHeight: content.implicitHeight + 28
    radius: Theme.shape.extraLarge
    color: Theme.surfaceContainer
    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 14
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: root.info ? root.info.title : ""
                role: "titleMedium"
            }
            IconButton {
                symbol: "close"
                implicitWidth: 36
                implicitHeight: 36
                iconSize: 18
                Accessible.name: "Close details"
                onClicked: root.closeRequested()
            }
        }
        // Night Light
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.tile === "night_light"
            spacing: 6
            Label {
                Layout.fillWidth: true
                text: SystemBridge.snapshot.night_light.available ? "Warmer colors reduce blue light in the evening." : "Night Light needs the hyprsunset package."
                role: "bodySmall"
                color: Theme.surfaceVariantInk
                wrapMode: Text.WordWrap
            }
            SliderRow {
                Layout.fillWidth: true
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
        // Battery Saver
        Flow {
            Layout.fillWidth: true
            visible: root.tile === "battery_saver"
            spacing: 8
            Repeater {
                model: [
                    {
                        id: "power-saver",
                        profile: "power-saver",
                        title: "Power saver"
                    },
                    {
                        id: "power-balanced",
                        profile: "balanced",
                        title: "Balanced"
                    },
                    {
                        id: "power-performance",
                        profile: "performance",
                        title: "Performance"
                    }
                ]
                delegate: FilterChip {
                    required property var modelData
                    text: modelData.title
                    enabled: SystemBridge.snapshot.profile.available
                    selected: SystemBridge.snapshot.profile.profile === modelData.profile
                    onClicked: SystemBridge.action(modelData.id)
                }
            }
        }
        // Screenshot
        Flow {
            Layout.fillWidth: true
            visible: root.tile === "screenshot"
            spacing: 8
            Repeater {
                model: [
                    {
                        mode: "area",
                        title: "Area"
                    },
                    {
                        mode: "window",
                        title: "Window"
                    },
                    {
                        mode: "full",
                        title: "Full screen"
                    }
                ]
                delegate: FilterChip {
                    required property var modelData
                    text: modelData.title
                    onClicked: ShellState.screenshot(modelData.mode)
                }
            }
        }
        // Do Not Disturb
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.tile === "dnd"
            spacing: 6
            Label {
                Layout.fillWidth: true
                text: Notifications.schedule.enabled ? "Quiet hours: every day from " + Notifications.schedule.start + " to " + Notifications.schedule.end : "Quiet hours are off."
                role: "bodyMedium"
                wrapMode: Text.WordWrap
            }
            PillButton {
                text: "Edit quiet hours"
                variant: "tonal"
                implicitHeight: 40
                onClicked: root.settingsRequested("notifications")
            }
        }
        // Dark theme / color scheme
        Flow {
            Layout.fillWidth: true
            visible: root.tile === "dark"
            spacing: 8
            Repeater {
                model: [
                    {
                        id: "tonal_spot",
                        title: "Tonal Spot"
                    },
                    {
                        id: "vibrant",
                        title: "Vibrant"
                    },
                    {
                        id: "expressive",
                        title: "Expressive"
                    },
                    {
                        id: "neutral",
                        title: "Neutral"
                    },
                    {
                        id: "monochrome",
                        title: "Monochrome"
                    }
                ]
                delegate: FilterChip {
                    required property var modelData
                    text: modelData.title
                    selected: (SystemBridge.snapshot.settings.scheme || "tonal_spot") === modelData.id
                    onClicked: SystemBridge.setScheme(modelData.id)
                }
            }
        }
    }
}
