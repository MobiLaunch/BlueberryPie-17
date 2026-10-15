import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

// Local times in a few other time zones.
ColumnLayout {
    id: root
    property string chosen: ""
    readonly property var zones: InstallerState.timezones.map(name => ({
                id: name,
                label: name.replace(/_/g, " ")
            }))
    function load() {
        WorldClockState.refresh();
        InstallerState.loadOptions();
    }
    spacing: 10
    Timer {
        interval: 30000
        repeat: true
        running: root.visible
        onTriggered: WorldClockState.refresh()
    }
    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: WorldClockState.clocks
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }
        delegate: ListRow {
            required property var modelData
            width: ListView.view.width
            interactive: false
            implicitHeight: 64
            title: modelData.label
            supporting: [WorldClockState.dayText(modelData.day), WorldClockState.offsetText(modelData.offset)].filter(part => part.length > 0).join(" · ")
            symbol: "globe"
            RowLayout {
                spacing: 4
                Label {
                    text: Theme.timeText(new Date(2000, 0, 1, modelData.hour, modelData.minute))
                    role: "titleLarge"
                }
                IconButton {
                    symbol: "close"
                    implicitWidth: 36
                    implicitHeight: 36
                    iconSize: 18
                    Accessible.name: "Remove " + modelData.label
                    onClicked: WorldClockState.remove(modelData.zone)
                }
            }
        }
        Label {
            anchors.centerIn: parent
            visible: parent.count === 0
            text: "Add a city to compare times"
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
    }
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 230
        radius: Theme.shape.extraLarge
        color: Theme.surfaceContainer
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8
            ChoiceList {
                Layout.fillWidth: true
                Layout.fillHeight: true
                searchable: true
                model: root.zones
                current: root.chosen
                onPicked: id => root.chosen = id
            }
            PillButton {
                Layout.alignment: Qt.AlignRight
                text: "Add"
                variant: "filled"
                enabled: root.chosen.length > 0 && WorldClockState.clocks.length < 6
                onClicked: {
                    WorldClockState.add(root.chosen);
                    root.chosen = "";
                }
            }
        }
    }
    Label {
        Layout.fillWidth: true
        visible: WorldClockState.error.length > 0
        text: WorldClockState.error
        role: "bodySmall"
        color: Theme.error
        wrapMode: Text.WordWrap
    }
}
