import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Shared rounded menu behavior for dock, launcher, desktop and future system apps.
Menu {
    id: root
    padding: 8
    implicitWidth: 230
    background: Rectangle {
        radius: 24
        color: Theme.surfaceContainer
        border.width: 1
        border.color: Theme.outline
        scale: root.opened ? 1 : .96
        opacity: root.opened ? 1 : 0
        Behavior on scale {
            NumberAnimation { duration: Theme.fast; easing.type: Easing.OutBack }
        }
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }
    delegate: MenuItem {
        id: item
        implicitHeight: visible ? 46 : 0
        implicitWidth: 210
        contentItem: Label {
            text: item.text
            font.pixelSize: 14
            font.weight: item.highlighted ? Font.DemiBold : Font.Normal
            color: item.highlighted ? Theme.primaryContainerInk : Theme.surfaceInk
            leftPadding: 14
            rightPadding: 10
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 16
            color: item.highlighted ? Theme.primaryContainer : "transparent"
            Behavior on color { ColorAnimation { duration: Theme.fast } }
        }
    }
}
