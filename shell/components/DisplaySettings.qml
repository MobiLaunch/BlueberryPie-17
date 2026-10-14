import QtQuick
import QtQuick.Controls
import "."
import "../services"

Column {
    id: root
    width: parent.width
    spacing: 10
    Label {
        text: "Displays"
        font.pixelSize: 21
        font.weight: Font.DemiBold
    }
    Label {
        text: "Safely adjust the size of everything on screen."
        font.pixelSize: 13
        wrapMode: Text.WordWrap
        width: parent.width
        opacity: .72
    }
    Repeater {
        model: DisplayState.monitors
        delegate: Rectangle {
            id: screenCard
            required property var modelData
            width: root.width
            height: 110
            radius: 25
            color: Theme.surfaceContainer
            Label {
                x: 17; y: 13
                text: screenCard.modelData.name
                font.weight: Font.DemiBold
                font.pixelSize: 17
            }
            Label {
                x: 17; y: 45
                text: screenCard.modelData.width + " × " +
                      screenCard.modelData.height + " · " +
                      Math.round(screenCard.modelData.refresh) + " Hz"
                opacity: .7
                font.pixelSize: 13
            }
            ComboBox {
                id: scalePicker
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                implicitWidth: 148
                implicitHeight: 48
                model: screenCard.modelData.choices
                currentIndex: model.indexOf(screenCard.modelData.scale)
                enabled: !DisplayState.busy
                displayText: "Scale " + (currentIndex >= 0 ? model[currentIndex] : screenCard.modelData.scale) + "×"
                background: Rectangle {
                    radius: 24
                    color: Theme.surfaceContainerHigh
                    border.width: scalePicker.activeFocus ? 2 : 0
                    border.color: Theme.primary
                }
                onActivated: index => DisplayState.preview(
                    screenCard.modelData.name, model[index])
            }
        }
    }
    Label {
        text: "Arrange monitors"
        font.pixelSize: 17
        font.weight: Font.DemiBold
        visible: DisplayState.monitors.length > 1
    }
    Label {
        text: "Choose a screen, then place it beside another."
        width: parent.width
        font.pixelSize: 13
        wrapMode: Text.WordWrap
        opacity: .72
        visible: DisplayState.monitors.length > 1
    }
    Column {
        id: arrangement
        width: parent.width
        spacing: 8
        visible: DisplayState.monitors.length > 1
        ComboBox {
            id: movedMonitor
            width: parent.width
            model: DisplayState.monitors.map(m => m.name)
            currentIndex: 0
            Accessible.name: "Display to move"
        }
        ComboBox {
            id: targetMonitor
            width: parent.width
            model: DisplayState.monitors.map(m => m.name).filter(n => n !== movedMonitor.currentText)
            currentIndex: 0
            Accessible.name: "Place relative to display"
        }
        Flow {
            width: parent.width
            spacing: 7
            Repeater {
                model: [
                    {label: "← Left", direction: "left"},
                    {label: "Right →", direction: "right"},
                    {label: "↑ Above", direction: "above"},
                    {label: "Below ↓", direction: "below"}
                ]
                delegate: PillButton {
                    required property var modelData
                    text: modelData.label
                    enabled: !DisplayState.busy && targetMonitor.currentText.length > 0
                    onClicked: DisplayState.arrange(movedMonitor.currentText,
                                                    modelData.direction,
                                                    targetMonitor.currentText)
                }
            }
        }
    }
    Label {
        width: parent.width
        text: DisplayState.monitors.length === 0 ?
              "No monitors were detected. Display settings require an active PrismOS session." : ""
        visible: DisplayState.monitors.length === 0
        wrapMode: Text.WordWrap
        opacity: .7
    }
    Rectangle {
        width: parent.width
        height: 114
        radius: 25
        color: Theme.primaryContainer
        visible: DisplayState.trialToken.length > 0
        Column {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 7
            Label {
                text: "Keep these display settings?"
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: Theme.onPrimaryContainer
            }
            Label {
                text: "Reverting automatically in " + DisplayState.seconds + " seconds"
                color: Theme.onPrimaryContainer
                font.pixelSize: 12
            }
            PillButton {
                text: "Keep changes"
                enabled: !DisplayState.confirmer.running
                onClicked: DisplayState.confirm()
            }
        }
    }
    Row {
        spacing: 10
        visible: DisplayState.busy && DisplayState.trialToken.length === 0
        ExpressiveLoader { width: 25; height: 25 }
        Label { text: "Updating displays…"; opacity: .8 }
    }
    Label {
        width: parent.width
        visible: DisplayState.error.length > 0 || DisplayState.notice.length > 0
        text: DisplayState.error || DisplayState.notice
        color: DisplayState.error ? Theme.error : Theme.primary
        wrapMode: Text.WordWrap
        font.pixelSize: 13
    }
}
