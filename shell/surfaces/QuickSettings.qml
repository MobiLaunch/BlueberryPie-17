import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.shadeOpen && ShellState.activeScreen === screen
    property string clockText: Qt.formatTime(new Date(), "hh:mm")
    property string dateText: Qt.formatDate(new Date(), "ddd, MMM d")
    Timer {
        interval: 1000
        running: root.opened
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.clockText = Qt.formatTime(new Date(), "hh:mm");
            root.dateText = Qt.formatDate(new Date(), "ddd, MMM d");
        }
    }
    anchors {
        top: true
        right: true
    }
    margins {
        top: 52
        right: 12
    }
    implicitWidth: Math.min(404, screen.width - 24)
    implicitHeight: Math.min(770, screen.height - 150)
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-shade"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    onOpenedChanged: if (opened)
        card.forceActiveFocus()
    HyprlandFocusGrab {
        active: root.opened
        windows: [root]
        onCleared: ShellState.shadeOpen = false
    }
    Rectangle {
        id: card
        anchors.fill: parent
        radius: 36
        color: Theme.surfaceContainer
        opacity: root.opened ? .98 : 0
        transform: Translate {
            y: root.opened ? 0 : -30
            Behavior on y {
                NumberAnimation {
                    duration: Theme.standard
                    easing.type: Easing.OutBack
                    easing.overshoot: .7
                }
            }
        }
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
                easing.overshoot: .6
            }
        }
        focus: true
        Keys.onEscapePressed: ShellState.close()
        Flickable {
            anchors.fill: parent
            anchors.margins: 20
            clip: true
            contentHeight: content.height
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            Column {
                id: content
                width: parent.width
                spacing: 12
                RowLayout {
                    width: parent.width
                    Column {
                        Layout.fillWidth: true
                        Label {
                            text: root.clockText
                            font.pixelSize: 42
                            font.weight: Font.Bold
                            font.letterSpacing: -1
                        }
                        Label {
                            text: root.dateText
                            font.pixelSize: 13
                        }
                    }
                    PillButton {
                        text: "×"
                        implicitWidth: 46
                        Accessible.name: "Close Quick Settings"
                        onClicked: ShellState.close()
                    }
                }
                ExpressiveSlider {
                    width: parent.width
                    label: "Brightness"
                    symbol: "brightness"
                    enabled: SystemBridge.snapshot.brightness.available
                    value: SystemBridge.snapshot.brightness.value
                    onCommitted: level => SystemBridge.action("brightness", level)
                }
                GridLayout {
                    width: parent.width
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Wi-Fi"
                        subtitle: SystemBridge.snapshot.wifi.available ? SystemBridge.snapshot.wifi.label : "Unavailable"
                        symbol: "wifi"
                        activated: SystemBridge.snapshot.wifi.enabled
                        enabled: SystemBridge.snapshot.wifi.available
                        onClicked: SystemBridge.action("wifi")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Bluetooth"
                        subtitle: SystemBridge.snapshot.bluetooth.available ? (activated ? "On" : "Off") : "Unavailable"
                        symbol: "bluetooth"
                        activated: SystemBridge.snapshot.bluetooth.enabled
                        enabled: SystemBridge.snapshot.bluetooth.available
                        onClicked: SystemBridge.action("bluetooth")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Do Not Disturb"
                        subtitle: activated ? "On" : "Off"
                        symbol: "dnd"
                        activated: SystemBridge.snapshot.settings.dnd
                        onClicked: SystemBridge.action("dnd")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Dark theme"
                        subtitle: activated ? "On" : "Off"
                        symbol: "moon"
                        activated: Theme.dark
                        onClicked: SystemBridge.action("dark")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Sound"
                        subtitle: activated ? "On" : "Muted"
                        symbol: "volume"
                        activated: !SystemBridge.snapshot.volume.muted
                        enabled: SystemBridge.snapshot.volume.available
                        onClicked: SystemBridge.action("mute")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        title: "Reduced motion"
                        subtitle: activated ? "On" : "Off"
                        symbol: "motion"
                        activated: Theme.reducedMotion
                        onClicked: SystemBridge.action("reduced_motion")
                    }
                }
                ExpressiveSlider {
                    width: parent.width
                    label: "Volume"
                    symbol: "volume"
                    enabled: SystemBridge.snapshot.volume.available
                    value: SystemBridge.snapshot.volume.value
                    onCommitted: level => SystemBridge.action("volume", level)
                }
                MediaCard {
                    width: parent.width
                    height: visible ? implicitHeight : 0
                }
                RowLayout {
                    width: parent.width
                    Label {
                        text: "Notifications"
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    PillButton {
                        text: "Clear all"
                        implicitHeight: 36
                        onClicked: Notifications.clear()
                    }
                }
                Label {
                    visible: Notifications.items.values.length === 0
                    text: "You're all caught up"
                    font.pixelSize: 13
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    height: 40
                }
                Repeater {
                    model: Notifications.items
                    delegate: NotificationCard {
                        required property var modelData
                        width: content.width
                        notification: modelData
                    }
                }
                RowLayout {
                    width: parent.width
                    spacing: 8
                    PillButton {
                        text: "Style"
                        filled: true
                        Layout.fillWidth: true
                        onClicked: ShellState.openSettings(root.screen)
                    }
                    PillButton {
                        text: "Network"
                        Layout.fillWidth: true
                        onClicked: SystemBridge.action("network-settings")
                    }
                    PillButton {
                        text: "Power"
                        Layout.fillWidth: true
                        onClicked: ShellState.openPower(root.screen)
                    }
                }
            }
        }
    }
}
