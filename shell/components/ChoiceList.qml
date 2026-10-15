import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../services"

// Titled, scrollable single-choice list (language, keyboard, time zone).
// `model` is [{id, label}]; `picked(id)` fires on selection.
ColumnLayout {
    id: root
    property string title: ""
    property var model: []
    property string current: ""
    property bool searchable: false
    readonly property var filtered: {
        const needle = filter.text.trim().toLowerCase();
        return needle.length === 0 ? model : model.filter(item => item.label.toLowerCase().includes(needle));
    }
    signal picked(string id)
    function reveal() {
        const index = filtered.findIndex(item => item.id === current);
        if (index >= 0)
            list.positionViewAtIndex(index, ListView.Center);
    }
    onModelChanged: Qt.callLater(reveal)
    spacing: 8
    Label {
        text: root.title
        role: "titleSmall"
        color: Theme.primary
        leftPadding: 4
    }
    SearchField {
        id: filter
        visible: root.searchable
        Layout.fillWidth: true
        implicitHeight: 44
        placeholderText: "Search"
    }
    ListView {
        id: list
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 3
        model: root.filtered
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }
        delegate: ListRow {
            required property var modelData
            width: list.width
            implicitHeight: 48
            title: modelData.label
            selected: modelData.id === root.current
            Accessible.role: Accessible.RadioButton
            onClicked: root.picked(modelData.id)
        }
    }
}
