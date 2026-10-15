import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../components"
import "../services"

// The first-run wizard is per-user, not a disk installer.
PanelWindow {
    id: root
    property int step: 0
    property bool includeAndroid: false
    property bool saving: finisher.running
    property string error: ""
    property bool opened: ShellState.onboardingOpen && ShellState.activeScreen === screen
    readonly property string seed: SystemBridge.snapshot.settings.seed || "#8469cf"
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
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "prism-welcome"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    visible: opened
    color: Theme.surface
    Rectangle {
        anchors.fill: parent
        color: Theme.surfaceContainerLow
        // Soft shapes in the current palette; they recolor live as the user picks.
        Rectangle {
            x: parent.width - 360
            y: -140
            width: 520
            height: 520
            radius: 260
            color: Theme.primaryContainer
            opacity: 0.8
        }
        Rectangle {
            x: -160
            y: parent.height - 300
            width: 460
            height: 460
            radius: 150
            color: Theme.tertiaryContainer
            opacity: 0.7
        }
        Rectangle {
            x: parent.width * 0.62
            y: parent.height - 190
            width: 220
            height: 220
            radius: 70
            rotation: 18
            color: Theme.secondaryContainer
            opacity: 0.8
        }
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(760, root.width - 32)
        height: Math.min(600, root.height - 48)
        radius: Theme.shape.extraExtraLarge - 6
        color: Theme.surface
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.7)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 18
            Row {
                Layout.fillWidth: true
                spacing: 8
                Repeater {
                    model: 3
                    delegate: Rectangle {
                        required property int index
                        width: (card.width - 64 - 16) / 3
                        height: 6
                        radius: 3
                        color: index <= root.step ? Theme.primary : Theme.surfaceContainerHigh
                        Behavior on color {
                            ColorAnimation {
                                duration: Theme.fast
                            }
                        }
                    }
                }
            }
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                // Step 0: welcome
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 16
                    visible: root.step === 0
                    Item {
                        Layout.preferredHeight: 8
                    }
                    Rectangle {
                        Layout.preferredWidth: 96
                        Layout.preferredHeight: 96
                        radius: 32
                        color: Theme.primaryContainer
                        Symbol {
                            anchors.centerIn: parent
                            width: 52
                            height: 52
                            name: "spark"
                            color: Theme.primaryContainerInk
                        }
                    }
                    Label {
                        text: "Welcome to PrismOS"
                        role: "displaySmall"
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "A colorful, expressive desktop made for your computer."
                        role: "titleLarge"
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "Personalize your colors, then choose whether you'd like Android apps. You can change any of this later in Settings."
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                }
                // Step 1: colors
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 1
                    Label {
                        text: "Make it yours"
                        role: "headlineLarge"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "Pick an accent color. The whole desktop follows."
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 12
                        Repeater {
                            model: root.presets
                            delegate: PaletteSwatch {
                                required property var modelData
                                text: modelData.name
                                seed: modelData.seed
                                current: root.seed === modelData.seed
                                onClicked: SystemBridge.setSeed(modelData.seed)
                            }
                        }
                    }
                    SettingsGroup {
                        Layout.fillWidth: true
                        ToggleRow {
                            width: parent.width
                            title: "Dark theme"
                            supporting: "Easier on the eyes in low light"
                            symbol: "moon"
                            on: Theme.dark
                            onSwitched: SystemBridge.action("dark")
                        }
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
                // Step 2: Android apps
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14
                    visible: root.step === 2
                    Label {
                        text: "More apps, more fun"
                        role: "headlineLarge"
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "Would you like to run Android apps and games? PrismOS runs them alongside Linux apps using Waydroid."
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    SettingsGroup {
                        Layout.fillWidth: true
                        ToggleRow {
                            width: parent.width
                            title: "Enable Android apps"
                            supporting: "Optional system image download and first-time setup"
                            symbol: "android"
                            on: root.includeAndroid
                            onSwitched: value => root.includeAndroid = value
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "If enabled, you'll be asked to approve one-time setup. Settings shows progress while it runs, and F-Droid can be added afterward."
                        role: "bodyMedium"
                        color: Theme.surfaceVariantInk
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.error
                        visible: root.error.length > 0
                        wrapMode: Text.WordWrap
                        color: Theme.error
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                PillButton {
                    text: "Back"
                    variant: "text"
                    enabled: root.step > 0 && !root.saving
                    onClicked: root.step -= 1
                }
                Item {
                    Layout.fillWidth: true
                }
                PillButton {
                    id: nextButton
                    text: root.step < 2 ? "Continue" : root.saving ? "Saving…" : "Enter PrismOS"
                    variant: "filled"
                    enabled: !root.saving
                    onClicked: {
                        if (root.step < 2)
                            root.step += 1;
                        else {
                            root.error = "";
                            finisher.command = ["prismctl", "welcome", "finish", "--android", root.includeAndroid ? "yes" : "no"];
                            finisher.running = true;
                        }
                    }
                }
            }
        }
    }
    Process {
        id: finisher
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const response = JSON.parse(text);
                    if (response.ok === false) {
                        root.error = response.error || "Could not save your settings";
                        return;
                    }
                    ShellState.onboardingOpen = false;
                    SystemBridge.refresh();
                    if (root.includeAndroid) {
                        ShellState.openSettings(root.screen, "apps");
                        AndroidState.setEnabled(true);
                    }
                } catch (e) {
                    root.error = "Unable to finish first-use setup";
                }
            }
        }
    }
}
