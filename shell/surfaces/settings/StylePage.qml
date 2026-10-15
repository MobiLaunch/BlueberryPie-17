import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Wallpaper & style"
    readonly property var presets: [
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
    readonly property string seed: SystemBridge.snapshot.settings.seed || "#8469cf"
    property string customError: ""
    // A live miniature of the home screen, painted with the current roles.
    Rectangle {
        width: parent.width
        height: 196
        radius: Theme.shape.extraLargeIncreased
        color: Theme.primaryContainer
        clip: true
        Rectangle {
            x: parent.width - 150
            y: -50
            width: 220
            height: 220
            radius: 110
            color: Theme.tertiaryContainer
        }
        Rectangle {
            x: -40
            y: 110
            width: 220
            height: 150
            radius: 75
            color: Theme.secondaryContainer
        }
        Label {
            x: 20
            y: 14
            text: "10:09"
            role: "displaySmall"
            font.weight: Font.Bold
            color: Theme.primaryContainerInk
        }
        Label {
            x: 22
            y: 62
            text: "Preview of your colors"
            role: "bodyMedium"
            color: Theme.primaryContainerInk
        }
        Row {
            x: 20
            y: 104
            spacing: 8
            Rectangle {
                width: 110
                height: 40
                radius: 20
                color: Theme.primary
                Symbol {
                    x: 12
                    anchors.verticalCenter: parent.verticalCenter
                    width: 20
                    height: 20
                    name: "wifi"
                    color: Theme.primaryInk
                }
                Label {
                    x: 40
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Wi-Fi"
                    role: "labelLarge"
                    color: Theme.primaryInk
                }
            }
            Rectangle {
                width: 40
                height: 40
                radius: 14
                color: Theme.surfaceContainerHighest
                Symbol {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    name: "moon"
                    color: Theme.surfaceInk
                }
            }
            Rectangle {
                width: 40
                height: 40
                radius: 14
                color: Theme.surfaceContainerHighest
                Symbol {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    name: "dnd"
                    color: Theme.surfaceInk
                }
            }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 12
            width: 190
            height: 28
            radius: 14
            color: Theme.surfaceContainer
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Color palette"
        Rectangle {
            width: parent.width
            height: swatches.height + 32
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            Flow {
                id: swatches
                x: 16
                y: 16
                width: parent.width - 32
                spacing: 12
                Repeater {
                    model: page.presets
                    delegate: Button {
                        id: swatch
                        required property var modelData
                        readonly property bool current: page.seed === modelData.seed
                        implicitWidth: 76
                        implicitHeight: 96
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 0
                        bottomPadding: 0
                        hoverEnabled: true
                        Accessible.name: modelData.name + " palette" + (current ? ", selected" : "")
                        Accessible.checkable: true
                        Accessible.checked: current
                        background: Item {}
                        contentItem: Column {
                            spacing: 8
                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 64
                                height: 64
                                radius: swatch.current ? 32 : 20
                                color: swatch.modelData.seed
                                border.width: swatch.activeFocus ? 3 : 0
                                border.color: Theme.primary
                                Behavior on radius {
                                    NumberAnimation {
                                        duration: Theme.standard
                                        easing.type: Easing.OutBack
                                    }
                                }
                                Symbol {
                                    anchors.centerIn: parent
                                    width: 28
                                    height: 28
                                    visible: swatch.current
                                    name: "check"
                                    weight: 2.6
                                    color: "#ffffff"
                                }
                            }
                            Label {
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                                text: swatch.modelData.name
                                role: "labelMedium"
                                color: Theme.surfaceInk
                            }
                        }
                        onClicked: {
                            page.customError = "";
                            SystemBridge.setSeed(modelData.seed);
                        }
                    }
                }
            }
        }
        Rectangle {
            width: parent.width
            height: 88
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12
                Rectangle {
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 40
                    radius: 20
                    color: hexField.valid ? hexField.text : Theme.surfaceContainerHighest
                    border.width: 1
                    border.color: Theme.outlineVariant
                }
                ExpressiveTextField {
                    id: hexField
                    readonly property bool valid: /^#[0-9a-fA-F]{6}$/.test(text)
                    Layout.fillWidth: true
                    placeholderText: "Custom color, for example #3a7bd5"
                    maximumLength: 7
                    inputMethodHints: Qt.ImhNoPredictiveText
                    Accessible.name: "Custom accent color"
                    onAccepted: apply.clicked()
                }
                PillButton {
                    id: apply
                    text: "Apply"
                    variant: "filled"
                    enabled: hexField.valid
                    onClicked: SystemBridge.setSeed(hexField.text.toLowerCase())
                }
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Appearance"
        ToggleRow {
            width: parent.width
            title: "Dark theme"
            supporting: "Easier on the eyes in low light"
            symbol: "moon"
            on: Theme.dark
            onSwitched: SystemBridge.action("dark")
        }
        ToggleRow {
            width: parent.width
            title: "Reduce motion"
            supporting: "Keep the colors, simplify movement"
            symbol: "motion"
            on: Theme.reducedMotion
            onSwitched: SystemBridge.action("reduced_motion")
        }
    }
}
