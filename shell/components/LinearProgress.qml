import QtQuick
import "."
import "../services"

// Determinate progress bar. `value` is 0 to 1.
Item {
    id: root
    property real value: 0
    implicitHeight: 12
    implicitWidth: 320
    Accessible.role: Accessible.ProgressBar
    Accessible.name: Math.round(value * 100) + " percent"
    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Theme.surfaceContainerHighest
    }
    Rectangle {
        width: Math.max(parent.height, parent.width * Math.max(0, Math.min(1, root.value)))
        height: parent.height
        radius: height / 2
        color: Theme.primary
        Behavior on width {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutCubic
            }
        }
    }
}
