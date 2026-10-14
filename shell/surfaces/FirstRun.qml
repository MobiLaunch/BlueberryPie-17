import QtQuick
import QtQuick.Controls
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
    anchors { top: true; left: true; right: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "prism-welcome"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    visible: opened
    color: Theme.surface

    Rectangle {
        anchors.fill: parent
        color: Theme.dark ? "#20182a" : "#f5f0fb"
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(720, root.width - 32)
        height: Math.min(570, root.height - 48)
        radius: 42
        color: Theme.surfaceContainer
        Column {
            x: 30
            y: 27
            width: parent.width - 60
            spacing: 17
            Row {
                spacing: 8
                Repeater {
                    model: 3
                    delegate: Rectangle {
                        required property int index
                        width: (card.width - 92) / 3
                        height: 6
                        radius: 3
                        color: index <= root.step ? Theme.primary : Theme.surfaceContainerHigh
                        Behavior on color { ColorAnimation { duration: Theme.fast } }
                    }
                }
            }
            Item {
                height: Math.min(405, card.height - 155)
                width: parent.width
                Column {
                    anchors.fill: parent
                    spacing: 15
                    visible: root.step === 0
                    Label { text: "✦"; font.pixelSize: 64; color: Theme.primary }
                    Label { text: "Welcome to PrismOS"; font.pixelSize: 34; font.weight: Font.Bold }
                    Label {
                        width: parent.width
                        text: "A colorful, expressive desktop made for your computer."
                        font.pixelSize: 19
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        width: parent.width
                        text: "Personalize your experience, then choose whether you'd like Android apps. You can always change that later."
                        wrapMode: Text.WordWrap
                        opacity: .75
                    }
                }
                Column {
                    anchors.fill: parent
                    spacing: 15
                    visible: root.step === 1
                    Label { text: "Make it yours"; font.pixelSize: 33; font.weight: Font.Bold }
                    Label { text: "Pick a color. Your desktop will follow."; font.pixelSize: 16 }
                    Flow {
                        width: parent.width
                        spacing: 10
                        Repeater {
                            model: [
                                {name: "Lilac", seed: "#8469cf"},
                                {name: "Mint", seed: "#47846a"},
                                {name: "Tangerine", seed: "#c27443"},
                                {name: "Rose", seed: "#b85c80"}
                            ]
                            delegate: PillButton {
                                required property var modelData
                                text: modelData.name
                                filled: true
                                onClicked: SystemBridge.setSeed(modelData.seed)
                            }
                        }
                    }
                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        text: "You can change the theme and accessibility settings later."
                        opacity: .75
                    }
                }
                Column {
                    anchors.fill: parent
                    spacing: 15
                    visible: root.step === 2
                    Label { text: "More apps, more fun"; font.pixelSize: 33; font.weight: Font.Bold }
                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        text: "Would you like to enable Android apps and games? PrismOS runs them alongside Linux apps using Waydroid."
                        font.pixelSize: 17
                    }
                    Rectangle {
                        width: parent.width
                        height: 100
                        radius: 28
                        color: Theme.surfaceContainerHigh
                        Label {
                            x: 17; y: 15
                            text: "Enable Android apps"
                            font.pixelSize: 17; font.weight: Font.DemiBold
                        }
                        Label {
                            x: 17; y: 48
                            width: parent.width - 120
                            wrapMode: Text.WordWrap
                            text: "Optional system image download and first-time setup"
                            font.pixelSize: 13
                        }
                        AndroidToggle {
                            checked: root.includeAndroid
                            anchors.right: parent.right
                            anchors.rightMargin: 18
                            anchors.verticalCenter: parent.verticalCenter
                            onClicked: root.includeAndroid = checked
                        }
                    }
                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        opacity: .75
                        text: "If enabled, you'll be asked to approve one-time setup. A small progress indicator in Settings shows what's happening. F-Droid can be added afterward."
                    }
                    Label {
                        width: parent.width
                        text: root.error
                        visible: root.error.length > 0
                        wrapMode: Text.WordWrap
                        color: Theme.error
                    }
                }
            }
            Row {
                width: parent.width
                spacing: 12
                PillButton {
                    text: "Back"
                    enabled: root.step > 0 && !root.saving
                    onClicked: root.step -= 1
                }
                Item { width: Math.max(0, parent.width - nextButton.width - 115); height: 1 }
                PillButton {
                    id: nextButton
                    text: root.step < 2 ? "Continue" : root.saving ? "Saving…" : "Enter PrismOS"
                    filled: true
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
                        ShellState.openSettings(root.screen);
                        AndroidState.setEnabled(true);
                    }
                } catch (e) {
                    root.error = "Unable to finish first-use setup";
                }
            }
        }
    }
}
