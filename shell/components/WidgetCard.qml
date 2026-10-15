import QtQuick
import "."
import "../services"

// Container for a card-style desktop widget.
Rectangle {
    id: root
    default property alias content: slot.data
    property real padding: 16
    // Resizable cards name themselves; Settings → Widgets chooses small, medium or large.
    property string widgetId: ""
    property real baseWidth: 292
    readonly property real sizeFactor: WidgetsState.sizeFactor(widgetId)
    implicitWidth: Math.round(baseWidth * sizeFactor)
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
