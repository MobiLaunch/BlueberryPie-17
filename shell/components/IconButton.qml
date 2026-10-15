import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Round icon button with a 48px touch target. `variant`: standard | filled | tonal.
// Set `toggle: true` and bind `checked` for toggle buttons.
Button {
    id: root
    property string symbol: "spark"
    property string variant: "standard"
    property bool toggle: false
    property real iconSize: 24
    checkable: toggle
    readonly property bool selected: toggle && checked
    readonly property color containerColor: variant === "filled" ? (toggle && !checked ? Theme.surfaceContainerHighest : Theme.primary) : variant === "tonal" ? (selected || !toggle ? Theme.secondaryContainer : Theme.surfaceContainerHighest) : selected ? Theme.primaryContainer : "transparent"
    readonly property color contentColor: variant === "filled" ? (toggle && !checked ? Theme.primary : Theme.primaryInk) : variant === "tonal" ? Theme.secondaryContainerInk : selected ? Theme.primaryContainerInk : Theme.surfaceVariantInk
    implicitWidth: 48
    implicitHeight: 48
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.role: Accessible.Button
    ToolTip.visible: hovered && Accessible.name.length > 0
    ToolTip.delay: 600
    ToolTip.text: Accessible.name
    scale: down ? 0.92 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    background: Rectangle {
        radius: root.down ? Theme.shape.medium : width / 2
        color: root.containerColor
        opacity: root.enabled ? 1 : 0.38
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.primary
        Behavior on radius {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: Theme.fast
            }
        }
        StateLayer {
            anchors.fill: parent
            radius: parent.radius
            tint: root.contentColor
            hovered: root.hovered && root.enabled
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Item {
        Symbol {
            anchors.centerIn: parent
            width: root.iconSize
            height: root.iconSize
            name: root.symbol
            color: root.contentColor
            opacity: root.enabled ? 1 : 0.38
        }
    }
}
