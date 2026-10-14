import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.settingsOpen && ShellState.activeScreen === screen
    anchors { top: true; left: true; right: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-settings"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01

    Rectangle { anchors.fill: parent; color: "#551b1425"; visible: root.opened }
    MouseArea { anchors.fill: parent; onClicked: ShellState.close() }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(650, root.width - 32)
        height: Math.min(690, root.height - 64)
        radius: 38
        color: Theme.surface
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .95
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
        Behavior on scale { NumberAnimation { duration: Theme.standard; easing.type: Easing.OutBack } }
        MouseArea { anchors.fill: parent; onClicked: {} }
        PillButton {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 18
            text: "×"
            Accessible.name: "Close Settings"
            onClicked: ShellState.close()
        }
        Flickable {
            anchors.fill: parent
            anchors.margins: 26
            anchors.topMargin: 30
            anchors.bottomMargin: 22
            clip: true
            contentHeight: content.height
            ScrollBar.vertical: ScrollBar {}
            Column {
                id: content
                width: parent.width
                spacing: 15
                Label { text: "Settings"; font.pixelSize: 32; font.weight: Font.Bold }
                Label { text: "Make PrismOS yours"; font.pixelSize: 15; opacity: .7 }
                Label { text: "Color & appearance"; font.pixelSize: 20; font.weight: Font.DemiBold }
                Flow {
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: [
                            { name: "Lilac", seed: "#8469cf" },
                            { name: "Mint", seed: "#47846a" },
                            { name: "Tangerine", seed: "#c27443" },
                            { name: "Rose", seed: "#b85c80" }
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
                    subtitle: "Keep the color, simplify movement"
                    symbol: "motion"
                    activated: Theme.reducedMotion
                    onClicked: SystemBridge.action("reduced_motion")
                }
                Rectangle { width: parent.width; height: 1; color: Theme.outline; opacity: .26 }
                Label { text: "Android apps"; font.pixelSize: 21; font.weight: Font.DemiBold }
                Rectangle {
                    width: parent.width
                    height: 100
                    radius: 28
                    color: Theme.surfaceContainer
                    Label {
                        x: 18; y: 17; width: parent.width - 125
                        text: "Run Android apps"
                        font.pixelSize: 18; font.weight: Font.DemiBold
                    }
                    Label {
                        x: 18; y: 46; width: parent.width - 125
                        wrapMode: Text.WordWrap
                        text: "Games and apps alongside Linux windows"
                        opacity: .75
                    }
                    Switch {
                        id: androidToggle
                        anchors.right: parent.right; anchors.rightMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        checked: AndroidState.enabled
                        enabled: !AndroidState.busy
                        Accessible.name: "Enable Android apps"
                        onClicked: AndroidState.setEnabled(checked)
                    }
                }
                Row {
                    spacing: 12
                    width: parent.width
                    visible: AndroidState.enabled
                    ExpressiveLoader {
                        width: 32; height: 32
                        visible: AndroidState.busy
                        color: Theme.primaryStrong
                    }
                    Label {
                        width: parent.width - (AndroidState.busy ? 44 : 0)
                        wrapMode: Text.WordWrap
                        text: AndroidState.label
                        font.pixelSize: 14
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                Label {
                    width: parent.width
                    visible: AndroidState.error.length > 0
                    wrapMode: Text.WordWrap
                    color: Theme.roles.error
                    text: AndroidState.error
                }
                Row {
                    spacing: 10
                    visible: AndroidState.enabled && !AndroidState.busy
                    PillButton {
                        text: "Retry setup"
                        visible: !AndroidState.ready
                        onClicked: AndroidState.setEnabled(true)
                    }
                    PillButton {
                        text: AndroidState.fdroidInstalled ? "Open F-Droid" : "Install F-Droid"
                        filled: true
                        visible: AndroidState.ready
                        onClicked: {
                            if (AndroidState.fdroidInstalled)
                                AndroidState.openFdroid();
                            else
                                AndroidState.installFdroid();
                        }
                    }
                    PillButton {
                        text: "Open Android"
                        visible: AndroidState.ready
                        onClicked: AndroidState.openAndroid()
                    }
                }
                Label {
                    width: parent.width
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    opacity: .65
                    text: "Optional. Downloads the Android system image on first use; an administrator may need to approve setup. Turning this off never deletes your Android data. F-Droid is installed only when you request it."
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
