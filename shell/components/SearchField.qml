import QtQuick
import QtQuick.Controls.Basic as Basic
import "."
import "../services"

// Pill search bar: leading icon, borderless field, clear button.
Rectangle {
    id: root
    property alias text: field.text
    property alias placeholderText: field.placeholderText
    property alias field: field
    signal accepted
    signal escaped
    signal downPressed
    function focusField() {
        field.forceActiveFocus();
    }
    implicitHeight: 56
    implicitWidth: 360
    radius: height / 2
    color: field.activeFocus ? Theme.surfaceContainerHighest : Theme.surfaceContainerHigh
    border.width: field.activeFocus ? 2 : 0
    border.color: Theme.primary
    Behavior on color {
        ColorAnimation {
            duration: Theme.fast
        }
    }
    Symbol {
        x: 20
        anchors.verticalCenter: parent.verticalCenter
        width: 22
        height: 22
        name: "search"
        color: Theme.surfaceVariantInk
    }
    Basic.TextField {
        id: field
        anchors.fill: parent
        anchors.leftMargin: 54
        anchors.rightMargin: 52
        leftPadding: 0
        rightPadding: 0
        topPadding: 0
        bottomPadding: 0
        verticalAlignment: TextInput.AlignVCenter
        font.family: Theme.font
        font.pixelSize: 16
        color: Theme.surfaceInk
        placeholderTextColor: Theme.surfaceVariantInk
        selectionColor: Theme.primaryContainer
        selectedTextColor: Theme.primaryContainerInk
        selectByMouse: true
        background: Item {}
        Accessible.name: root.placeholderText
        onAccepted: root.accepted()
        Keys.onEscapePressed: root.escaped()
        Keys.onDownPressed: root.downPressed()
    }
    IconButton {
        visible: field.text.length > 0
        anchors.right: parent.right
        anchors.rightMargin: 6
        anchors.verticalCenter: parent.verticalCenter
        implicitWidth: 40
        implicitHeight: 40
        iconSize: 20
        symbol: "close"
        Accessible.name: "Clear search"
        onClicked: {
            field.clear();
            field.forceActiveFocus();
        }
    }
}
