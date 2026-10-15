import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../services"

// Settings-style list row: optional leading icon chip, title, supporting text
// and a trailing slot (put a switch, chevron or value Label inside).
// `shapePosition` rounds the outer corners of a grouped list (Android Settings).
Button {
    id: root
    property string title: ""
    property string supporting: ""
    property string symbol: ""
    property bool selected: false
    property bool interactive: true
    property string shapePosition: "single"
    property color chipColor: Theme.secondaryContainer
    property color chipInk: Theme.secondaryContainerInk
    default property alias trailing: slot.data
    readonly property real outer: Theme.shape.extraLarge - 4
    readonly property real inner: Theme.shape.extraSmall + 2
    implicitHeight: supporting.length > 0 ? 72 : 60
    implicitWidth: 320
    leftPadding: 16
    rightPadding: 16
    topPadding: 8
    bottomPadding: 8
    hoverEnabled: true
    focusPolicy: interactive ? Qt.StrongFocus : Qt.NoFocus
    Accessible.name: title + (supporting ? ", " + supporting : "")
    background: Rectangle {
        topLeftRadius: root.shapePosition === "single" || root.shapePosition === "top" ? root.outer : root.inner
        topRightRadius: topLeftRadius
        bottomLeftRadius: root.shapePosition === "single" || root.shapePosition === "bottom" ? root.outer : root.inner
        bottomRightRadius: bottomLeftRadius
        color: root.selected ? Theme.primaryContainer : Theme.surfaceContainer
        opacity: root.enabled ? 1 : 0.5
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.primary
        Behavior on color {
            ColorAnimation {
                duration: Theme.fast
            }
        }
        StateLayer {
            anchors.fill: parent
            radius: parent.topLeftRadius
            tint: root.selected ? Theme.primaryContainerInk : Theme.surfaceInk
            hovered: root.hovered && root.enabled && root.interactive
            pressed: root.down && root.interactive
            focused: root.visualFocus
        }
    }
    contentItem: RowLayout {
        spacing: 16
        opacity: root.enabled ? 1 : 0.5
        Rectangle {
            visible: root.symbol.length > 0
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            radius: 20
            color: root.chipColor
            Symbol {
                anchors.centerIn: parent
                width: 22
                height: 22
                name: root.symbol
                color: root.chipInk
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Label {
                Layout.fillWidth: true
                text: root.title
                role: "bodyLarge"
                color: root.selected ? Theme.primaryContainerInk : Theme.surfaceInk
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: root.supporting
                role: "bodyMedium"
                color: root.selected ? Theme.primaryContainerInk : Theme.surfaceVariantInk
                elide: Text.ElideRight
                maximumLineCount: 2
                wrapMode: Text.WordWrap
            }
        }
        Item {
            id: slot
            visible: children.length > 0
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: childrenRect.width
            Layout.preferredHeight: childrenRect.height
        }
    }
}
