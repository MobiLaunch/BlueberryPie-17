import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// All notifications from one app: newest first, expandable when there are several.
Column {
    id: root
    required property var group
    property bool expanded: false
    readonly property int count: group.items.length
    spacing: 6
    RowLayout {
        width: parent.width
        visible: root.count > 1
        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 8
            text: root.group.app + " · " + root.count
            role: "labelLarge"
            color: Theme.surfaceVariantInk
            elide: Text.ElideRight
        }
        PillButton {
            text: root.expanded ? "Show less" : "Show all"
            variant: "text"
            implicitHeight: 36
            symbol: root.expanded ? "chevron_up" : "chevron_down"
            onClicked: root.expanded = !root.expanded
        }
    }
    Repeater {
        model: root.expanded ? root.group.items : root.group.items.slice(0, 1)
        delegate: NotificationCard {
            required property var modelData
            width: root.width
            notification: modelData
        }
    }
}
