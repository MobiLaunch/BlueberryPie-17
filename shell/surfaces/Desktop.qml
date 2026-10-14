import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

Scope {
    id: root
    required property var modelData
    property var screen: modelData
    property string timeText: Qt.formatTime(new Date(), "hh:mm")
    property string dateText: Qt.formatDate(new Date(), "dddd, MMMM d")
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            root.timeText = Qt.formatTime(new Date(), "hh:mm");
            root.dateText = Qt.formatDate(new Date(), "dddd, MMMM d");
        }
    }

    PanelWindow {
        id: wallpaper
        screen: root.screen
        anchors {
            top: true
            left: true
            right: true
            bottom: true
        }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Background
        WlrLayershell.namespace: "prism-wallpaper"
        color: Theme.dark ? "#211b2d" : "#e8dff4"
        Image {
            anchors.fill: parent
            source: Quickshell.shellPath("../design/wallpaper.svg")
            fillMode: Image.PreserveAspectCrop
            opacity: Theme.dark ? .5 : 1
        }
        Column {
            x: Math.max(40, wallpaper.width * .075)
            y: Math.max(90, wallpaper.height * .14)
            spacing: 4
            Label {
                text: root.dateText
                font.pixelSize: 20
                color: Theme.dark ? "#f5eafa" : "#3b2b53"
            }
            Label {
                text: root.timeText
                font.pixelSize: Math.min(130, wallpaper.width * .12)
                font.weight: Font.Black
                font.letterSpacing: -6
                color: Theme.dark ? "#f5eafa" : "#3b2b53"
            }
            Label {
                text: "A little more you."
                font.pixelSize: 21
                color: Theme.dark ? "#f5eafa" : "#3b2b53"
            }
        }
    }
    PanelWindow {
        id: bar
        screen: root.screen
        anchors {
            top: true
            left: true
            right: true
        }
        implicitHeight: 44
        exclusiveZone: 44
        WlrLayershell.namespace: "prism-bar"
        color: Theme.surface
        Row {
            x: 10
            anchors.verticalCenter: parent.verticalCenter
            spacing: 8
            PillButton {
                text: "✦  PrismOS"
                implicitHeight: 34
                onClicked: ShellState.toggleDrawer(root.screen)
            }
            Label {
                text: root.timeText
                anchors.verticalCenter: parent.verticalCenter
                font.weight: Font.DemiBold
            }
        }
        PillButton {
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: 34
            filled: ShellState.shadeOpen
            text: (SystemBridge.snapshot.wifi.enabled ? "Wi-Fi" : "Offline") + "   •   " + (SystemBridge.snapshot.battery.available ? SystemBridge.snapshot.battery.value + "%" : "Quick Settings")
            onClicked: ShellState.toggleShade(root.screen)
        }
    }
    PanelWindow {
        id: dock
        screen: root.screen
        anchors.bottom: true
        margins.bottom: 12
        implicitWidth: Math.min(root.screen.width - 32, 450)
        implicitHeight: 76
        exclusiveZone: 92
        WlrLayershell.namespace: "prism-dock"
        color: "transparent"
        Rectangle {
            anchors.fill: parent
            radius: 38
            color: Theme.surfaceContainer
            Row {
                anchors.centerIn: parent
                spacing: 8
                PillButton {
                    text: "▦"
                    Accessible.name: "All applications"
                    filled: true
                    implicitWidth: 52
                    implicitHeight: 52
                    onClicked: ShellState.toggleDrawer(root.screen)
                }
                Repeater {
                    model: SystemBridge.apps.slice(0, 4)
                    delegate: Button {
                        id: appButton
                        required property var modelData
                        implicitWidth: 56
                        implicitHeight: 56
                        Accessible.name: modelData.name
                        ToolTip.visible: hovered
                        ToolTip.text: modelData.name
                        hoverEnabled: true
                        scale: down ? .9 : hovered ? 1.06 : 1
                        Behavior on scale {
                            NumberAnimation {
                                duration: Theme.fast
                                easing.type: Easing.OutBack
                            }
                        }
                        background: Rectangle {
                            radius: 24
                            color: appButton.hovered ? Theme.primary : "transparent"
                        }
                        contentItem: Image {
                            source: Quickshell.iconPath(appButton.modelData.icon, "application-x-executable")
                            sourceSize: Qt.size(36, 36)
                            fillMode: Image.PreserveAspectFit
                        }
                        onClicked: {
                            const p = mapToItem(dock.contentItem, width / 2, height / 2);
                            ShellState.launch(modelData, root.screen, (root.screen.width - dock.width) / 2 + p.x, root.screen.height - dock.height - 12 + p.y);
                        }
                    }
                }
                PillButton {
                    text: "⚙"
                    Accessible.name: "Appearance settings"
                    implicitWidth: 52
                    implicitHeight: 52
                    onClicked: ShellState.openSettings(root.screen)
                }
            }
        }
    }
    QuickSettings {
        screen: root.screen
    }
    AppDrawer {
        screen: root.screen
    }
    Appearance {
        screen: root.screen
    }
    LaunchSplash {
        screen: root.screen
    }
    PanelWindow {
        screen: root.screen
        anchors {
            bottom: true
            right: true
        }
        margins {
            bottom: 110
            right: 20
        }
        implicitWidth: Math.min(390, root.screen.width - 40)
        implicitHeight: 80
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "prism-toast"
        color: "transparent"
        visible: ShellState.toast.length > 0 && ShellState.activeScreen === root.screen
        Rectangle {
            anchors.fill: parent
            radius: 28
            color: Theme.surfaceContainer
            Label {
                anchors.fill: parent
                anchors.margins: 20
                text: ShellState.toast
                wrapMode: Text.WordWrap
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
