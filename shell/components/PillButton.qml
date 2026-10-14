import QtQuick
import QtQuick.Controls
import "../services"

Button {
    id: root
    property bool filled: false
    property string symbol: ""
    implicitWidth: Math.max(48, contentItem.implicitWidth + 32)
    implicitHeight: 48
    font.family: Theme.font
    font.pixelSize: 14
    hoverEnabled: true
    Accessible.name: text
    scale: down ? 0.95 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    background: Rectangle {
        radius: root.down ? 15 : 24
        color: root.filled ? Theme.primary : root.hovered ? Theme.surfaceHigh : Theme.surfaceContainer
        opacity: root.enabled ? 1 : 0.45
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.primaryStrong
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
    }
    contentItem: Label {
        text: root.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: root.filled ? Theme.onPrimary : Theme.onSurface
        opacity: root.enabled ? 1 : 0.45
    }
}
