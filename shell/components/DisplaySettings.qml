import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Monitor scale (with 20-second automatic rollback) and relative arrangement.
Column {
    id: root
    width: parent.width
    spacing: 12
    Label {
        text: "Displays"
        role: "titleSmall"
        color: Theme.primary
        leftPadding: 16
    }
    Column {
        width: parent.width
        spacing: 3
        Repeater {
            model: DisplayState.monitors
            delegate: ListRow {
                id: screenRow
                required property var modelData
                required property int index
                width: root.width
                implicitHeight: 76
                interactive: false
                symbol: "display"
                title: modelData.name
                supporting: modelData.width + " × " + modelData.height + " · " + Math.round(modelData.refresh) + " Hz"
                shapePosition: DisplayState.monitors.length === 1 ? "single" : index === 0 ? "top" : index === DisplayState.monitors.length - 1 ? "bottom" : "middle"
                ComboBox {
                    id: scalePicker
                    implicitWidth: 156
                    implicitHeight: 48
                    model: screenRow.modelData.choices
                    currentIndex: model.indexOf(screenRow.modelData.scale)
                    enabled: !DisplayState.busy
                    displayText: "Scale " + (currentIndex >= 0 ? model[currentIndex] : screenRow.modelData.scale) + "×"
                    Accessible.name: "Scale for " + screenRow.modelData.name
                    font.family: Theme.font
                    background: Rectangle {
                        radius: 24
                        color: Theme.surfaceContainerHighest
                        border.width: scalePicker.visualFocus ? 2 : 0
                        border.color: Theme.primary
                    }
                    contentItem: Label {
                        leftPadding: 16
                        text: scalePicker.displayText
                        role: "labelLarge"
                        verticalAlignment: Text.AlignVCenter
                    }
                    onActivated: index => DisplayState.preview(screenRow.modelData.name, model[index])
                }
            }
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        visible: DisplayState.monitors.length === 0
        text: "No monitors were detected. Display settings require an active PrismOS session."
        wrapMode: Text.WordWrap
        role: "bodyMedium"
        color: Theme.surfaceVariantInk
    }
    Rectangle {
        width: parent.width
        height: arrangement.height + 32
        radius: Theme.shape.extraLarge - 4
        color: Theme.surfaceContainer
        visible: DisplayState.monitors.length > 1
        Column {
            id: arrangement
            x: 16
            y: 16
            width: parent.width - 32
            spacing: 10
            Label {
                text: "Arrange monitors"
                role: "titleMedium"
            }
            Label {
                width: parent.width
                text: "Choose a screen, then place it beside another."
                role: "bodyMedium"
                color: Theme.surfaceVariantInk
                wrapMode: Text.WordWrap
            }
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
                spacing: 8
                Repeater {
                    model: [
                        {
                            label: "Left",
                            direction: "left"
                        },
                        {
                            label: "Right",
                            direction: "right"
                        },
                        {
                            label: "Above",
                            direction: "above"
                        },
                        {
                            label: "Below",
                            direction: "below"
                        }
                    ]
                    delegate: PillButton {
                        required property var modelData
                        text: modelData.label
                        variant: "tonal"
                        enabled: !DisplayState.busy && targetMonitor.currentText.length > 0
                        onClicked: DisplayState.arrange(movedMonitor.currentText, modelData.direction, targetMonitor.currentText)
                    }
                }
            }
        }
    }
    Rectangle {
        width: parent.width
        height: trial.height + 32
        radius: Theme.shape.extraLarge - 4
        color: Theme.primaryContainer
        visible: DisplayState.trialToken.length > 0
        Column {
            id: trial
            x: 16
            y: 16
            width: parent.width - 32
            spacing: 8
            Label {
                text: "Keep these display settings?"
                role: "titleMedium"
                color: Theme.primaryContainerInk
            }
            Label {
                text: "Reverting automatically in " + DisplayState.seconds + " seconds"
                role: "bodyMedium"
                color: Theme.primaryContainerInk
            }
            PillButton {
                text: "Keep changes"
                variant: "filled"
                enabled: !DisplayState.confirmer.running
                onClicked: DisplayState.confirm()
            }
        }
    }
    Row {
        spacing: 10
        leftPadding: 16
        visible: DisplayState.busy && DisplayState.trialToken.length === 0
        ExpressiveLoader {
            width: 25
            height: 25
        }
        Label {
            text: "Updating displays…"
            role: "bodyMedium"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        visible: DisplayState.error.length > 0 || DisplayState.notice.length > 0
        text: DisplayState.error || DisplayState.notice
        color: DisplayState.error ? Theme.error : Theme.primary
        wrapMode: Text.WordWrap
        role: "bodyMedium"
    }
}
