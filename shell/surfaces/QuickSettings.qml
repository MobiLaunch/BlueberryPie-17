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
    property string dateText: Qt.formatDate(new Date(), "dddd, MMMM d")
    property string connectionKind: ""
    property bool soundOpen: false
    readonly property var battery: SystemBridge.snapshot.battery
    readonly property string batteryText: battery.available ? battery.value + "%" + (battery.charging ? " · Charging" : "") : ""
    onSoundOpenChanged: AudioState.panelOpen = soundOpen
    onConnectionKindChanged: Wireless.watchedKind = connectionKind
    function showConnections(kind) {
        soundOpen = false;
        connectionKind = connectionKind === kind ? "" : kind;
        Wireless.error = "";
        Wireless.notice = "";
        Wireless.operation = "";
        if (connectionKind)
            Wireless.refresh(kind);
    }
    function showSound(kind = "output") {
        connectionKind = "";
        const open = !soundOpen || AudioState.tab !== kind;
        AudioState.tab = kind;
        soundOpen = open;
    }
    Timer {
        interval: 1000
        running: root.opened
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.clockText = Qt.formatTime(new Date(), "hh:mm");
            root.dateText = Qt.formatDate(new Date(), "dddd, MMMM d");
        }
    }
    anchors {
        top: true
        right: true
    }
    margins {
        top: 48
        right: 12
    }
    // Wide screens get Android's dual shade: notifications beside Quick Settings.
    readonly property bool dual: screen.width >= 1000
    readonly property real paneWidth: Math.min(424, screen.width - 24)
    implicitWidth: dual ? paneWidth * 2 + 12 : paneWidth
    implicitHeight: Math.min(820, screen.height - 140)
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-shade"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    onOpenedChanged: {
        if (opened)
            card.forceActiveFocus();
        else {
            connectionKind = "";
            soundOpen = false;
        }
    }
    HyprlandFocusGrab {
        active: root.opened
        windows: [root]
        onCleared: ShellState.shadeOpen = false
    }
    Rectangle {
        id: notifCard
        visible: root.dual
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.paneWidth
        radius: Theme.shape.extraLargeIncreased + 4
        color: Theme.surfaceContainerLow
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.6)
        opacity: card.opacity
        scale: card.scale
        transformOrigin: Item.TopRight
        transform: Translate {
            y: card.transform[0].y
        }
        Flickable {
            anchors.fill: parent
            anchors.margins: 18
            clip: true
            contentHeight: dualList.height
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }
            NotificationList {
                id: dualList
                width: parent.width
            }
        }
    }
    Rectangle {
        id: card
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.paneWidth
        radius: Theme.shape.extraLargeIncreased + 4
        color: Theme.surfaceContainerLow
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.6)
        opacity: root.opened ? 1 : 0
        transform: Translate {
            y: root.opened ? 0 : -24
            Behavior on y {
                NumberAnimation {
                    duration: Theme.standard
                    easing.type: Easing.OutBack
                    easing.overshoot: .7
                }
            }
        }
        scale: root.opened ? 1 : .96
        transformOrigin: Item.TopRight
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
            anchors.margins: 18
            clip: true
            contentHeight: content.height
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }
            Column {
                id: content
                width: parent.width
                spacing: 12
                RowLayout {
                    width: parent.width
                    spacing: 8
                    Column {
                        Layout.fillWidth: true
                        Label {
                            text: root.clockText
                            role: "displaySmall"
                            font.weight: Font.DemiBold
                            font.letterSpacing: -1
                        }
                        Label {
                            text: root.dateText + (root.batteryText ? "  ·  " + root.batteryText : "")
                            role: "bodyMedium"
                            color: Theme.surfaceVariantInk
                        }
                    }
                    IconButton {
                        symbol: "settings"
                        variant: "tonal"
                        Accessible.name: "Settings"
                        onClicked: ShellState.openSettings(root.screen)
                    }
                    IconButton {
                        symbol: "power"
                        variant: "tonal"
                        Accessible.name: "Power options"
                        onClicked: ShellState.openPower(root.screen)
                    }
                }
                ExpressiveSlider {
                    width: parent.width
                    label: "Brightness"
                    symbol: "brightness"
                    enabled: SystemBridge.snapshot.brightness.available
                    modelValue: SystemBridge.snapshot.brightness.value
                    onCommitted: level => SystemBridge.action("brightness", level)
                }
                GridLayout {
                    width: parent.width
                    columns: 4
                    columnSpacing: 8
                    rowSpacing: 8
                    QuickTile {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        title: "Wi-Fi"
                        subtitle: SystemBridge.snapshot.wifi.available ? SystemBridge.snapshot.wifi.label : "Unavailable"
                        symbol: SystemBridge.snapshot.wifi.enabled ? "wifi" : "wifi_off"
                        hasDetails: true
                        onDetailsRequested: root.showConnections("wifi")
                        activated: SystemBridge.snapshot.wifi.enabled
                        enabled: SystemBridge.snapshot.wifi.available
                        onClicked: SystemBridge.action("wifi")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        title: "Bluetooth"
                        subtitle: SystemBridge.snapshot.bluetooth.available ? (activated ? "On" : "Off") : "Unavailable"
                        symbol: SystemBridge.snapshot.bluetooth.enabled ? "bluetooth" : "bluetooth_off"
                        hasDetails: true
                        onDetailsRequested: root.showConnections("bluetooth")
                        activated: SystemBridge.snapshot.bluetooth.enabled
                        enabled: SystemBridge.snapshot.bluetooth.available
                        onClicked: SystemBridge.action("bluetooth")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        title: "Sound"
                        subtitle: !SystemBridge.snapshot.volume.available ? "Unavailable" : activated ? SystemBridge.snapshot.volume.value + "%" : "Muted"
                        symbol: activated ? "volume" : "volume_off"
                        hasDetails: true
                        onDetailsRequested: root.showSound()
                        activated: !SystemBridge.snapshot.volume.muted
                        enabled: SystemBridge.snapshot.volume.available && !AudioState.writing
                        onClicked: SystemBridge.action("mute")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        title: "Microphone"
                        subtitle: SystemBridge.snapshot.microphone.available ? (activated ? "On" : "Muted") : "Unavailable"
                        symbol: activated ? "microphone" : "microphone_off"
                        activated: SystemBridge.snapshot.microphone.available && !SystemBridge.snapshot.microphone.muted
                        enabled: SystemBridge.snapshot.microphone.available && !AudioState.writing
                        hasDetails: true
                        onDetailsRequested: root.showSound("input")
                        onClicked: SystemBridge.action("microphone-mute")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        large: false
                        title: "Do Not Disturb"
                        subtitle: activated ? "On" : "Off"
                        symbol: activated ? "notifications_off" : "dnd"
                        activated: SystemBridge.snapshot.settings.dnd
                        onClicked: SystemBridge.action("dnd")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        large: false
                        title: "Dark theme"
                        subtitle: activated ? "On" : "Off"
                        symbol: "moon"
                        activated: Theme.dark
                        onClicked: SystemBridge.action("dark")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        large: false
                        title: "Reduced motion"
                        subtitle: activated ? "On" : "Off"
                        symbol: "motion"
                        activated: Theme.reducedMotion
                        onClicked: SystemBridge.action("reduced_motion")
                    }
                    QuickTile {
                        Layout.fillWidth: true
                        large: false
                        title: "Audio devices"
                        symbol: "headphones"
                        activated: root.soundOpen
                        onClicked: root.showSound()
                    }
                }
                WirelessPanel {
                    width: parent.width
                    kind: root.connectionKind || "wifi"
                    visible: root.connectionKind.length > 0
                    height: visible ? implicitHeight : 0
                    onCloseRequested: root.connectionKind = ""
                }
                SoundPanel {
                    width: parent.width
                    visible: root.soundOpen
                    height: visible ? implicitHeight : 0
                    onCloseRequested: root.soundOpen = false
                }
                ExpressiveSlider {
                    width: parent.width
                    label: "Volume"
                    symbol: SystemBridge.snapshot.volume.muted ? "volume_off" : "volume"
                    enabled: SystemBridge.snapshot.volume.available && !AudioState.writing
                    modelValue: SystemBridge.snapshot.volume.value
                    onCommitted: level => SystemBridge.action("volume", level)
                }
                MediaCard {
                    width: parent.width
                    height: visible ? implicitHeight : 0
                }
                NotificationList {
                    visible: !root.dual
                    width: parent.width
                    height: visible ? implicitHeight : 0
                }
            }
        }
    }
}
