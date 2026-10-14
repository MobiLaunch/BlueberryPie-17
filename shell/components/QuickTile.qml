import QtQuick
import QtQuick.Controls
import "../services"

Button {
    id: root
    property string title: ""
    property string subtitle: ""
    property string symbol: "spark"
    property bool activated: false
    implicitWidth: 168
    implicitHeight: 78
    hoverEnabled: true
    Accessible.name: title + ", " + subtitle
    Accessible.checkable: true
    Accessible.checked: activated
    scale: down ? 0.96 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    background: Rectangle {
        radius: root.down ? 16 : root.activated ? 26 : 36
        color: root.activated ? Theme.primary : Theme.surfaceHigh
        opacity: root.enabled ? 1 : .5
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.primaryStrong
        Behavior on radius {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: Theme.fast
            }
        }
    }
    contentItem: Item {
        Symbol {
            x: 16
            y: 14
            width: 24
            height: 24
            name: root.symbol
            color: root.activated ? Theme.onPrimary : Theme.onSurfaceHigh
            opacity: root.enabled ? 1 : .45
        }
        Column {
            x: 49
            y: 15
            width: parent.width - 59
            spacing: 3
            Label {
                width: parent.width
                text: root.title
                font.weight: Font.DemiBold
                font.pixelSize: 14
                elide: Text.ElideRight
                color: root.activated ? Theme.onPrimary : Theme.onSurfaceHigh
            }
            Label {
                width: parent.width
                text: root.subtitle
                font.pixelSize: 11
                elide: Text.ElideRight
                color: root.activated ? Theme.onPrimary : Theme.onSurfaceHigh
            }
        }
    }
}
