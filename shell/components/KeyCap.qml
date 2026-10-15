import QtQuick
import "."
import "../services"

// A keyboard key drawn as a small rounded cap.
Rectangle {
    id: root
    property alias text: label.text
    implicitWidth: Math.max(30, label.implicitWidth + 16)
    implicitHeight: 28
    radius: 8
    color: Theme.surfaceContainerHighest
    border.width: 1
    border.color: Theme.outlineVariant
    Label {
        id: label
        anchors.centerIn: parent
        role: "labelMedium"
        color: Theme.surfaceInk
    }
}
