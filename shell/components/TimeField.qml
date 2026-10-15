import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Hour and minute steppers. `value` is "HH:MM"; `edited(value)` fires on a change.
RowLayout {
    id: root
    property string value: "07:00"
    readonly property int hour: parseInt(value.slice(0, 2))
    readonly property int minute: parseInt(value.slice(3, 5))
    signal edited(string value)
    spacing: 6
    function pad(number) {
        return (number < 10 ? "0" : "") + number;
    }
    function change(hours, minutes) {
        const total = ((root.hour + hours) * 60 + root.minute + minutes + 1440 * 2) % 1440;
        root.edited(pad(Math.floor(total / 60)) + ":" + pad(total % 60));
    }
    component Stepper: ColumnLayout {
        id: unit
        property bool isHour: true
        spacing: 0
        IconButton {
            Layout.alignment: Qt.AlignHCenter
            symbol: "chevron_up"
            implicitWidth: 40
            implicitHeight: 40
            iconSize: 20
            Accessible.name: "Increase " + (unit.isHour ? "hour" : "minute")
            onClicked: unit.isHour ? root.change(1, 0) : root.change(0, 5)
        }
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 76
            Layout.preferredHeight: 56
            radius: Theme.shape.large
            color: Theme.surfaceContainerHigh
            Label {
                anchors.centerIn: parent
                text: root.pad(unit.isHour ? root.hour : root.minute)
                role: "headlineMedium"
            }
        }
        IconButton {
            Layout.alignment: Qt.AlignHCenter
            symbol: "chevron_down"
            implicitWidth: 40
            implicitHeight: 40
            iconSize: 20
            Accessible.name: "Decrease " + (unit.isHour ? "hour" : "minute")
            onClicked: unit.isHour ? root.change(-1, 0) : root.change(0, -5)
        }
    }
    Stepper {
        isHour: true
    }
    Label {
        text: ":"
        role: "headlineMedium"
    }
    Stepper {
        isHour: false
    }
}
