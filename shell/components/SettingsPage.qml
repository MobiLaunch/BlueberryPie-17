import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Scrollable page scaffold used by every Settings section.
Flickable {
    id: root
    default property alias content: column.data
    property string title: ""
    property real spacing: 20
    contentHeight: column.height + 24
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
    }
    Column {
        id: column
        width: Math.min(root.width - 8, 720)
        spacing: root.spacing
    }
}
