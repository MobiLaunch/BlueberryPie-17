import QtQuick
import "."
import "../services"

// A titled stack of ListRows; call `arrange()` implicitly by child order so the
// outer corners are large and inner ones small (Android Settings grouping).
Column {
    id: root
    property string title: ""
    default property alias rows: stack.data
    spacing: 8
    Label {
        visible: root.title.length > 0
        width: parent.width
        text: root.title
        role: "titleSmall"
        color: Theme.primary
        leftPadding: 16
    }
    Column {
        id: stack
        width: parent.width
        spacing: 3
        onChildrenChanged: Qt.callLater(root.shape)
    }
    function shape() {
        const rows = Array.from(stack.children).filter(item => item.shapePosition !== undefined && item.visible !== false);
        rows.forEach((row, index) => {
            row.shapePosition = rows.length === 1 ? "single" : index === 0 ? "top" : index === rows.length - 1 ? "bottom" : "middle";
        });
    }
    Component.onCompleted: shape()
}
