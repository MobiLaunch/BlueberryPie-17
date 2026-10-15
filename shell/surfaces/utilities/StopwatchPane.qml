import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

// Stopwatch with laps. It keeps running when the panel is closed.
ColumnLayout {
    id: root
    spacing: 14
    Label {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 18
        text: ClockState.clock(ClockState.watchElapsed, true)
        role: "displayMedium"
        font.weight: Font.DemiBold
        font.features: {
            "tnum": 1
        }
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: 12
        PillButton {
            text: ClockState.watchRunning ? "Lap" : "Reset"
            variant: "tonal"
            enabled: ClockState.watchRunning || ClockState.watchElapsed > 0
            onClicked: ClockState.watchRunning ? ClockState.lap() : ClockState.resetWatch()
        }
        PillButton {
            text: ClockState.watchRunning ? "Stop" : "Start"
            variant: "filled"
            symbol: ClockState.watchRunning ? "pause" : "play"
            onClicked: ClockState.watchRunning ? ClockState.stopWatch() : ClockState.startWatch()
        }
    }
    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        model: ClockState.laps
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }
        delegate: Rectangle {
            required property var modelData
            width: ListView.view.width
            height: 44
            radius: Theme.shape.large
            color: Theme.surfaceContainer
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                Label {
                    text: "Lap " + modelData.number
                    role: "bodyMedium"
                    color: Theme.surfaceVariantInk
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    text: ClockState.clock(modelData.split, true)
                    role: "titleSmall"
                }
                Label {
                    Layout.preferredWidth: 90
                    horizontalAlignment: Text.AlignRight
                    text: ClockState.clock(modelData.total, true)
                    role: "bodyMedium"
                    color: Theme.surfaceVariantInk
                }
            }
        }
        Label {
            anchors.centerIn: parent
            visible: parent.count === 0
            text: ClockState.watchRunning ? "Tap Lap to mark a split" : "Start the stopwatch"
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
    }
}
