import QtQuick
import QtQuick.Controls
import "."
import "../services"

// A selectable accent color: a squircle that becomes a circle with a check
// when it is the current one.
Button {
    id: root
    property string seed: "#8469cf"
    property bool current: false
    implicitWidth: 76
    implicitHeight: 96
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text + " palette" + (current ? ", selected" : "")
    Accessible.checkable: true
    Accessible.checked: current
    background: Item {}
    contentItem: Column {
        spacing: 8
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 64
            height: 64
            radius: root.current ? 32 : root.down ? 14 : 20
            color: root.seed
            border.width: root.visualFocus ? 3 : 0
            border.color: Theme.primary
            Behavior on radius {
                NumberAnimation {
                    duration: Theme.standard
                    easing.type: Easing.OutBack
                }
            }
            Symbol {
                anchors.centerIn: parent
                width: 28
                height: 28
                visible: root.current
                name: "check"
                weight: 2.6
                color: "#ffffff"
            }
        }
        Label {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: root.text
            role: "labelMedium"
        }
    }
}
