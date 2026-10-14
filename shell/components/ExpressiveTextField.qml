import QtQuick
import QtQuick.Controls.Basic
import "."
import "../services"

// Shared touch-friendly keyboard/mouse input visual for PrismOS native surfaces.
TextField {
    id: root
    implicitHeight: 50
    font.family: Theme.font
    font.pixelSize: 15
    color: Theme.onSurface
    placeholderTextColor: Theme.outline
    selectionColor: Theme.primaryContainer
    selectedTextColor: Theme.onPrimaryContainer
    leftPadding: 18
    rightPadding: 18
    selectByMouse: true
    background: Rectangle {
        radius: root.activeFocus ? 19 : 25
        color: Theme.surfaceContainer
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? Theme.primary : Theme.surfaceContainerHigh
        opacity: root.enabled ? 1 : .54
        Behavior on radius { NumberAnimation { duration: Theme.fast } }
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}
