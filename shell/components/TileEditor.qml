import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Choose which Quick Settings tiles appear and in what order.
Column {
    id: root
    signal done
    spacing: 4
    RowLayout {
        width: parent.width
        Label {
            Layout.fillWidth: true
            text: "Edit tiles"
            role: "titleMedium"
        }
        PillButton {
            text: "Reset"
            variant: "text"
            implicitHeight: 40
            onClicked: TilesState.reset()
        }
        PillButton {
            text: "Done"
            variant: "filled"
            implicitHeight: 40
            onClicked: root.done()
        }
    }
    Repeater {
        model: TilesState.arranged
        delegate: ListRow {
            id: row
            required property string modelData
            required property int index
            readonly property bool shown: TilesState.enabled.indexOf(modelData) >= 0
            readonly property var info: TilesState.describe(modelData)
            width: root.width
            implicitHeight: 52
            title: info.title
            symbol: info.symbol
            interactive: false
            RowLayout {
                spacing: 0
                IconButton {
                    symbol: "chevron_up"
                    visible: row.shown
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 20
                    enabled: row.index > 0
                    Accessible.name: "Move " + row.info.title + " up"
                    onClicked: TilesState.move(row.modelData, -1)
                }
                IconButton {
                    symbol: "chevron_down"
                    visible: row.shown
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 20
                    enabled: row.index < TilesState.enabled.length - 1
                    Accessible.name: "Move " + row.info.title + " down"
                    onClicked: TilesState.move(row.modelData, 1)
                }
                AndroidToggle {
                    checked: row.shown
                    Accessible.name: "Show " + row.info.title
                    onToggled: TilesState.show(row.modelData, !row.shown)
                }
            }
        }
    }
}
