import QtQuick
import "."
import "../services"

// Container for a card-style desktop widget.
Rectangle {
    id: root
    default property alias content: slot.data
    property real padding: 16
    implicitWidth: 280
    implicitHeight: slot.childrenRect.height + padding * 2
    radius: Theme.shape.extraLarge
    color: Theme.withAlpha(Theme.surfaceContainer, 0.93)
    border.width: 1
    border.color: Theme.withAlpha(Theme.outlineVariant, 0.5)
    Item {
        id: slot
        x: root.padding
        y: root.padding
        width: root.width - root.padding * 2
        height: childrenRect.height
    }
}
