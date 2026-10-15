import QtQuick
import QtQuick.Controls
import "."
import "../services"

Slider {
    id: root
    property string symbol: "brightness"
    property string label: "Brightness"
    property real modelValue: 0
    property real keyStep: 5
    signal committed(real level)
    from: symbol === "brightness" ? 1 : 0
    to: 100
    stepSize: 1
    implicitHeight: 52
    Accessible.name: label
    // A separate Binding survives keyboard assignments to value. It also waits
    // until release before applying external hardware updates to the thumb.
    Binding {
        target: root
        property: "value"
        value: root.modelValue
        when: !root.pressed
        restoreMode: Binding.RestoreBindingOrValue
    }
    onPressedChanged: if (!pressed)
        committed(value)
    Keys.onLeftPressed: {
        value = Math.max(from, value - keyStep);
        committed(value);
    }
    Keys.onRightPressed: {
        value = Math.min(to, value + keyStep);
        committed(value);
    }
    background: Rectangle {
        x: root.leftPadding
        y: (root.height - height) / 2
        width: root.availableWidth
        height: 44
        radius: 22
        color: Theme.surfaceContainerHigh
        Rectangle {
            width: Math.max(44, parent.width * root.visualPosition)
            height: parent.height
            radius: 22
            color: Theme.primaryContainer
            Behavior on width {
                enabled: !root.pressed
                NumberAnimation {
                    duration: Theme.fast
                }
            }
        }
        Symbol {
            x: 14
            anchors.verticalCenter: parent.verticalCenter
            width: 22
            height: 22
            name: root.symbol
        }
        Label {
            anchors.right: parent.right
            anchors.rightMargin: 14
            anchors.verticalCenter: parent.verticalCenter
            text: root.enabled ? Math.round(root.value) + "%" : "Unavailable"
            font.pixelSize: 12
            color: Theme.surfaceInk
        }
        opacity: root.enabled ? 1 : .5
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.primary
    }
    handle: Rectangle {
        x: root.leftPadding + root.visualPosition * (root.availableWidth - width)
        y: (root.height - height) / 2
        width: 5
        height: root.pressed ? 35 : 28
        radius: 3
        color: Theme.primary
        Behavior on height {
            NumberAnimation {
                duration: Theme.fast
                easing.type: Easing.OutBack
            }
        }
    }
}
