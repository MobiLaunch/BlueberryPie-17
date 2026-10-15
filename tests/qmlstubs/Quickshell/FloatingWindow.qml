import QtQuick

// Free-floating window approximation: centered on the shared desk.
QtObject {
    id: win
    default property alias data: contentRoot.data
    property real implicitWidth: 400
    property real implicitHeight: 300
    property bool visible: true
    property color color: "white"
    property string title: ""
    property Item contentItem: Item {
        id: contentRoot
        visible: win.visible
        parent: HarnessDesk.item
        width: win.implicitWidth
        height: win.implicitHeight
        x: parent ? (parent.width - width) / 2 : 0
        y: parent ? (parent.height - height) / 2 : 0
        z: 100000
        Rectangle {
            anchors.fill: parent
            color: win.color
            z: -1000
        }
    }
}
