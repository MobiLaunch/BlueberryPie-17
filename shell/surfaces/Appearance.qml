import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.settingsOpen && ShellState.activeScreen === screen
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-appearance"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    Rectangle {
        anchors.fill: parent
        color: "#551b1425"
        visible: root.opened
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(540, root.width - 32)
        height: Math.min(470, root.height - 90)
        radius: 36
        color: Theme.surface
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .93
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
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        Flickable {
            anchors.fill: parent
            anchors.margins: 26
            contentHeight: column.height
            clip: true
            Column {
                id: column
                width: parent.width
                spacing: 20
                Label {
                    text: "Make it yours"
                    font.pixelSize: 32
                    font.weight: Font.Bold
                }
                Label {
                    text: "One palette. Every PrismOS surface."
                    wrapMode: Text.WordWrap
                    width: parent.width
                }
                Flow {
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: [
                            {
                                name: "Lilac",
                                seed: "#8469cf"
                            },
                            {
                                name: "Mint",
                                seed: "#47846a"
                            },
                            {
                                name: "Tangerine",
                                seed: "#c27443"
                            },
                            {
                                name: "Rose",
                                seed: "#b85c80"
                            }
                        ]
                        delegate: PillButton {
                            required property var modelData
                            text: modelData.name
                            filled: true
                            onClicked: SystemBridge.setSeed(modelData.seed)
                        }
                    }
                }
                QuickTile {
                    width: parent.width
                    title: "Dark theme"
                    subtitle: "Comfortable after sunset"
                    symbol: "moon"
                    activated: Theme.dark
                    onClicked: SystemBridge.action("dark")
                }
                QuickTile {
                    width: parent.width
                    title: "Reduced motion"
                    subtitle: "Keep the colors, simplify movement"
                    symbol: "motion"
                    activated: Theme.reducedMotion
                    onClicked: SystemBridge.action("reduced_motion")
                }
                PillButton {
                    text: "Done"
                    width: parent.width
                    filled: true
                    onClicked: ShellState.close()
                }
            }
        }
        Keys.onEscapePressed: ShellState.close()
        focus: root.opened
    }
}
