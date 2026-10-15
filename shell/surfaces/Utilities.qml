import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"
import "utilities"

// Calculator, timer and stopwatch in one compact panel.
PanelWindow {
    id: root
    readonly property bool opened: ShellState.utilitiesOpen && ShellState.activeScreen === screen
    readonly property var tabs: [
        {
            id: "calculator",
            title: "Calculator"
        },
        {
            id: "timer",
            title: "Timer"
        },
        {
            id: "stopwatch",
            title: "Stopwatch"
        },
        {
            id: "alarms",
            title: "Alarms"
        },
        {
            id: "converter",
            title: "Convert"
        },
        {
            id: "clipboard",
            title: "Clipboard"
        }
    ]
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-utilities"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    onOpenedChanged: if (opened)
        Qt.callLater(root.focusStart)
    function focusStart() {
        card.forceActiveFocus();
        if (ShellState.utilitiesTab === "calculator")
            calculator.focusInput();
        if (ShellState.utilitiesTab === "clipboard")
            clipboardPane.load();
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.32)
        opacity: root.opened ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(Math.round(420 * Math.max(1, Theme.fontScale)), root.width - 24)
        height: Math.min(Math.round(640 * Math.max(1, Theme.fontScale)), root.height - 56)
        radius: Theme.shape.extraExtraLarge - 8
        color: Theme.surface
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.7)
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .95
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
            }
        }
        focus: root.opened
        Keys.onEscapePressed: ShellState.close()
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                        model: root.tabs
                        delegate: FilterChip {
                            required property var modelData
                            text: modelData.title
                            selected: ShellState.utilitiesTab === modelData.id
                            onClicked: {
                                ShellState.utilitiesTab = modelData.id;
                                if (modelData.id === "calculator")
                                    calculator.focusInput();
                            }
                        }
                    }
                }
                IconButton {
                    symbol: "close"
                    variant: "tonal"
                    Accessible.name: "Close"
                    onClicked: ShellState.close()
                }
            }
            CalculatorPane {
                id: calculator
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "calculator"
            }
            TimerPane {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "timer"
            }
            StopwatchPane {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "stopwatch"
            }
            AlarmsPane {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "alarms"
            }
            ConverterPane {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "converter"
            }
            ClipboardPane {
                id: clipboardPane
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: ShellState.utilitiesTab === "clipboard"
                onVisibleChanged: if (visible)
                    load()
            }
        }
    }
}
