import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

// Alarms kept in the user's settings. They ring even while the panel is closed.
ColumnLayout {
    id: root
    property string newTime: "07:00"
    property var newDays: []
    readonly property var names: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    function describe(days) {
        if (days.length === 0)
            return "Once";
        if (days.length === 7)
            return "Every day";
        if (days.join() === "0,1,2,3,4")
            return "Weekdays";
        if (days.join() === "5,6")
            return "Weekends";
        return days.map(day => names[day]).join(", ");
    }
    function toggleDay(day) {
        const next = newDays.indexOf(day) >= 0 ? newDays.filter(item => item !== day) : newDays.concat([day]);
        newDays = next.sort();
    }
    spacing: 10
    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: ClockState.alarmList
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }
        delegate: ListRow {
            required property var modelData
            width: ListView.view.width
            interactive: false
            implicitHeight: 64
            title: modelData.time
            supporting: (modelData.label.length > 0 ? modelData.label + " · " : "") + root.describe(modelData.days)
            symbol: "recents"
            RowLayout {
                spacing: 4
                AndroidToggle {
                    checked: modelData.enabled
                    Accessible.name: "Alarm " + modelData.time
                    onToggled: SystemBridge.toggleAlarm(modelData.id)
                }
                IconButton {
                    symbol: "trash"
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 20
                    Accessible.name: "Delete alarm " + modelData.time
                    onClicked: SystemBridge.removeAlarm(modelData.id)
                }
            }
        }
        Label {
            anchors.centerIn: parent
            visible: parent.count === 0
            text: "No alarms yet"
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: newColumn.implicitHeight + 28
        radius: Theme.shape.extraLarge
        color: Theme.surfaceContainer
        ColumnLayout {
            id: newColumn
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                TimeField {
                    value: root.newTime
                    onEdited: value => root.newTime = value
                }
                Item {
                    Layout.fillWidth: true
                }
                ColumnLayout {
                    spacing: 8
                    ExpressiveTextField {
                        id: labelField
                        Layout.preferredWidth: 150
                        implicitHeight: 44
                        placeholderText: "Label"
                        maximumLength: 40
                        Accessible.name: "Alarm label"
                    }
                    PillButton {
                        Layout.fillWidth: true
                        text: "Add alarm"
                        variant: "filled"
                        enabled: ClockState.alarmList.length < 10
                        onClicked: {
                            SystemBridge.addAlarm(root.newTime, root.newDays, labelField.text.trim());
                            labelField.text = "";
                        }
                    }
                }
            }
            Flow {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: root.names
                    delegate: FilterChip {
                        required property string modelData
                        required property int index
                        text: modelData
                        implicitHeight: 34
                        selected: root.newDays.indexOf(index) >= 0
                        onClicked: root.toggleDay(index)
                    }
                }
            }
        }
    }
}
