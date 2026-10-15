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
    readonly property var schemes: [
        {
            id: "tonal_spot",
            label: "Tonal Spot",
            description: "Calm and balanced, Android's default"
        },
        {
            id: "vibrant",
            label: "Vibrant",
            description: "Saturated and lively"
        },
        {
            id: "expressive",
            label: "Expressive",
            description: "Playful, with shifted hues"
        },
        {
            id: "neutral",
            label: "Neutral",
            description: "Nearly gray with a hint of color"
        },
        {
            id: "monochrome",
            label: "Monochrome",
            description: "Pure grays, maximum calm"
        }
    ]
    readonly property var scales: [
        {
            label: "Small",
            value: 0.9
        },
        {
            label: "Default",
            value: 1
        },
        {
            label: "Large",
            value: 1.15
        },
        {
            label: "Largest",
            value: 1.3
        }
    ]
    readonly property string seed: SystemBridge.snapshot.settings.seed || "#8469cf"
    property string customError: ""
    Component.onCompleted: WallpaperState.refresh()
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
        title: "Wallpaper"
        Rectangle {
            width: parent.width
            height: 160
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            Flickable {
                id: papers
                anchors.fill: parent
                anchors.margins: 14
                contentWidth: paperRow.implicitWidth
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Row {
                    id: paperRow
                    spacing: 12
                    PaperTile {
                        title: "Material"
                        current: WallpaperState.current === ""
                        onPicked: WallpaperState.clear()
                    }
                    Repeater {
                        model: WallpaperState.items
                        delegate: PaperTile {
                            required property var modelData
                            title: modelData.name
                            preview: modelData.thumbnail
                            current: WallpaperState.current === modelData.path
                            onPicked: WallpaperState.choose(modelData.path)
                        }
                    }
                }
            }
        }
        Label {
            width: parent.width
            leftPadding: 16
            rightPadding: 16
            visible: WallpaperState.error.length > 0 || WallpaperState.items.length === 0
            text: WallpaperState.error || "Put pictures in ~/Pictures/Wallpapers to choose them here. Your colors follow the picture you pick."
            role: "bodySmall"
            color: WallpaperState.error ? Theme.error : Theme.surfaceVariantInk
            wrapMode: Text.WordWrap
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
                    delegate: PaletteSwatch {
                        required property var modelData
                        text: modelData.name
                        seed: modelData.seed
                        current: page.seed === modelData.seed
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
        title: "Color scheme"
        Repeater {
            model: page.schemes
            delegate: ListRow {
                required property var modelData
                width: parent ? parent.width : 600
                title: modelData.label
                supporting: modelData.description
                symbol: "palette"
                selected: (SystemBridge.snapshot.settings.scheme || "tonal_spot") === modelData.id
                Accessible.role: Accessible.RadioButton
                onClicked: SystemBridge.setScheme(modelData.id)
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Text size"
        Rectangle {
            width: parent.width
            height: 96
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            property bool interactive: false
            Column {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10
                Row {
                    spacing: 8
                    Repeater {
                        model: page.scales
                        delegate: FilterChip {
                            required property var modelData
                            text: modelData.label
                            selected: Theme.fontScale === modelData.value
                            onClicked: SystemBridge.setFontScale(modelData.value)
                        }
                    }
                }
                Label {
                    width: parent.width
                    text: "The quick brown fox jumps over the lazy dog"
                    role: "bodyLarge"
                    color: Theme.surfaceVariantInk
                    elide: Text.ElideRight
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
            title: "Window previews in Recents"
            supporting: on ? "Small screenshots of open windows, removed at sign-out" : "Recents shows app icons only"
            symbol: "recents"
            on: SystemBridge.snapshot.settings.recents_previews !== false
            onSwitched: value => SystemBridge.setPreviews(value)
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
