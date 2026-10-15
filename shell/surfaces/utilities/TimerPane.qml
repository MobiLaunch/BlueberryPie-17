import QtQuick
import QtQuick.Layouts
import "../../components"
import "../../services"

// Countdown timer. It keeps running when the panel is closed.
ColumnLayout {
    id: root
    spacing: 14
    readonly property real fraction: ClockState.timerTotal > 0 ? ClockState.timerLeft / ClockState.timerTotal : 0
    Item {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 240
        Layout.preferredHeight: 240
        Canvas {
            id: ring
            anchors.fill: parent
            property real value: root.fraction
            property color track: Theme.surfaceContainerHighest
            property color arc: ClockState.timerFinished ? Theme.error : Theme.primary
            onValueChanged: requestPaint()
            onTrackChanged: requestPaint()
            onArcChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                const cx = width / 2, cy = height / 2, radius = Math.min(width, height) / 2 - 12;
                ctx.lineWidth = 14;
                ctx.lineCap = "round";
                ctx.strokeStyle = track;
                ctx.beginPath();
                ctx.arc(cx, cy, radius, 0, Math.PI * 2);
                ctx.stroke();
                if (value > 0.002) {
                    ctx.strokeStyle = arc;
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, value));
                    ctx.stroke();
                }
            }
        }
        Column {
            anchors.centerIn: parent
            spacing: 2
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                text: ClockState.clock(Math.ceil(ClockState.timerLeft / 1000) * 1000, false)
                role: "displaySmall"
                font.weight: Font.DemiBold
                color: ClockState.timerFinished ? Theme.error : Theme.surfaceInk
            }
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                text: ClockState.timerFinished ? "Time's up" : ClockState.timerRunning ? "Running" : "Set the time"
                role: "bodyMedium"
                color: Theme.surfaceVariantInk
            }
        }
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: 8
        Repeater {
            model: [
                {
                    label: "−1 min",
                    seconds: -60
                },
                {
                    label: "+1 min",
                    seconds: 60
                },
                {
                    label: "+5 min",
                    seconds: 300
                },
                {
                    label: "+10 min",
                    seconds: 600
                }
            ]
            delegate: PillButton {
                required property var modelData
                variant: "neutral"
                implicitHeight: 40
                text: modelData.label
                enabled: !ClockState.timerRunning
                onClicked: ClockState.adjustTimer(modelData.seconds)
            }
        }
    }
    Flow {
        Layout.alignment: Qt.AlignHCenter
        Layout.maximumWidth: parent.width
        spacing: 8
        Repeater {
            model: [
                {
                    label: "1 min",
                    seconds: 60
                },
                {
                    label: "5 min",
                    seconds: 300
                },
                {
                    label: "10 min",
                    seconds: 600
                },
                {
                    label: "25 min",
                    seconds: 1500
                }
            ]
            delegate: FilterChip {
                required property var modelData
                text: modelData.label
                selected: Math.round(ClockState.timerTotal / 1000) === modelData.seconds
                enabled: !ClockState.timerRunning
                onClicked: ClockState.setTimer(modelData.seconds)
            }
        }
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: 12
        PillButton {
            text: "Reset"
            variant: "tonal"
            enabled: ClockState.timerRunning || ClockState.timerFinished || ClockState.timerLeft < ClockState.timerTotal
            onClicked: ClockState.resetTimer()
        }
        PillButton {
            text: ClockState.timerRunning ? "Pause" : ClockState.timerFinished ? "Restart" : "Start"
            variant: "filled"
            symbol: ClockState.timerRunning ? "pause" : "play"
            onClicked: ClockState.timerRunning ? ClockState.pauseTimer() : ClockState.startTimer()
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
