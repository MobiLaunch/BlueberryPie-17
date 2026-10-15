import QtQuick
import "../components"
import "../services"

// Processor, memory and storage as three rounded meters. Values are real
// readings from /proc and the home filesystem; unavailable ones say so.
WidgetCard {
    id: root
    readonly property var stats: WidgetsState.stats
    implicitWidth: 292
    component Meter: Item {
        id: meter
        property string label
        property string symbol
        property var percent: null
        property string detail: ""
        width: parent.width
        height: 44
        Symbol {
            y: 2
            width: 22
            height: 22
            name: meter.symbol
            color: Theme.primary
        }
        Label {
            x: 34
            text: meter.label
            role: "labelLarge"
        }
        Label {
            anchors.right: parent.right
            text: meter.percent === null || meter.percent === undefined ? "Unavailable" : meter.detail || meter.percent + "%"
            role: "labelMedium"
            color: Theme.surfaceVariantInk
        }
        Rectangle {
            x: 34
            y: 26
            width: parent.width - 34
            height: 10
            radius: 5
            color: Theme.surfaceContainerHighest
            Rectangle {
                width: meter.percent ? Math.max(10, parent.width * Math.min(100, meter.percent) / 100) : 0
                height: parent.height
                radius: 5
                color: meter.percent > 90 ? Theme.error : Theme.primary
                Behavior on width {
                    NumberAnimation {
                        duration: Theme.standard
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }
    }
    Column {
        width: parent.width
        spacing: 12
        Label {
            text: "System"
            role: "titleMedium"
            leftPadding: 2
        }
        Meter {
            label: "Processor"
            symbol: "memory"
            percent: root.stats.cpu === undefined ? null : root.stats.cpu
        }
        Meter {
            label: "Memory"
            symbol: "apps_grid"
            percent: root.stats.memory ? root.stats.memory.percent : null
            detail: root.stats.memory ? root.stats.memory.used_gib + " / " + root.stats.memory.total_gib + " GiB" : ""
        }
        Meter {
            label: "Storage"
            symbol: "storage"
            percent: root.stats.storage ? root.stats.storage.percent : null
            detail: root.stats.storage ? root.stats.storage.used_gib + " / " + root.stats.storage.total_gib + " GiB" : ""
        }
    }
}
