import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Selectable filter chip (checkmark when selected).
Button {
    id: root
    property bool selected: false
    checkable: false
    leftPadding: selected ? 12 : 16
    rightPadding: 16
    topPadding: 0
    bottomPadding: 0
    implicitHeight: 40
    implicitWidth: row.implicitWidth + leftPadding + rightPadding
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    Accessible.checkable: true
    Accessible.checked: selected
    background: Rectangle {
        radius: root.down ? Theme.shape.medium : height / 2
        color: root.selected ? Theme.secondaryContainer : "transparent"
        border.width: root.visualFocus ? 2 : root.selected ? 0 : 1
        border.color: root.visualFocus ? Theme.primary : Theme.outlineVariant
        Behavior on color {
            ColorAnimation {
                duration: Theme.fast
            }
        }
        StateLayer {
            anchors.fill: parent
            radius: parent.radius
            tint: root.selected ? Theme.secondaryContainerInk : Theme.surfaceVariantInk
            hovered: root.hovered
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
        Row {
            id: row
            anchors.centerIn: parent
            spacing: 8
            Symbol {
                visible: root.selected
                anchors.verticalCenter: parent.verticalCenter
                width: 18
                height: 18
                name: "check"
                color: Theme.secondaryContainerInk
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: root.text
                role: "labelLarge"
                color: root.selected ? Theme.secondaryContainerInk : Theme.surfaceVariantInk
            }
        }
    }
}
