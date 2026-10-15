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
    property date now: new Date()
    readonly property string clockText: Theme.timeText(now)
    property string dateText: Qt.formatDate(new Date(), "dddd, MMMM d")
    property string connectionKind: ""
    property bool soundOpen: false
    property bool editing: false
    property string detailTile: ""
    readonly property var battery: SystemBridge.snapshot.battery
    readonly property string batteryText: battery.available ? battery.value + "%" + (battery.charging ? " · Charging" : "") : ""
    onSoundOpenChanged: AudioState.panelOpen = soundOpen
    onConnectionKindChanged: Wireless.watchedKind = connectionKind
    function showConnections(kind) {
        soundOpen = false;
        detailTile = "";
        connectionKind = connectionKind === kind ? "" : kind;
        Wireless.error = "";
        Wireless.notice = "";
        Wireless.operation = "";
        if (connectionKind)
            Wireless.refresh(kind);
    }
    function activateTile(id) {
        switch (id) {
        case "wifi":
            SystemBridge.action("wifi");
            break;
        case "bluetooth":
            SystemBridge.action("bluetooth");
            break;
        case "sound":
            SystemBridge.action("mute");
            break;
        case "microphone":
            SystemBridge.action("microphone-mute");
            break;
        case "dnd":
            SystemBridge.action("dnd");
            break;
        case "dark":
            SystemBridge.action("dark");
            break;
        case "focus":
            // With no apps chosen there is nothing to pause: go and choose some.
            if (Notifications.focusApps.length === 0 && !SystemBridge.snapshot.settings.focus)
                ShellState.openSettings(root.screen, "notifications");
            else
                SystemBridge.action("focus");
            break;
        case "reduced_motion":
            SystemBridge.action("reduced_motion");
            break;
        case "audio_devices":
            showSound();
            break;
        case "airplane":
            SystemBridge.action("airplane");
            break;
        case "battery_saver":
            SystemBridge.action("battery-saver");
            break;
        case "night_light":
            SystemBridge.action("night-light");
            break;
        case "hotspot":
            SystemBridge.action("hotspot");
            break;
        case "screen_record":
            ShellState.toggleRecording();
            break;
        case "vpn":
            // With no VPN set up there is nothing to switch: show how to add one instead.
            if (SystemBridge.snapshot.vpn.available)
                SystemBridge.action("vpn");
            else
                tileDetails("vpn");
            break;
        case "screenshot":
            ShellState.screenshot("area");
            break;
        case "lock":
            ShellState.close();
            SystemBridge.action("lock");
            break;
        }
    }
    function tileDetails(id) {
        if (TilesState.detailTiles.indexOf(id) >= 0) {
            soundOpen = false;
            connectionKind = "";
            detailTile = detailTile === id ? "" : id;
        } else if (id === "wifi" || id === "bluetooth")
            showConnections(id);
        else if (id === "sound")
            showSound();
        else if (id === "microphone")
            showSound("input");
    }
    function showSound(kind = "output") {
        connectionKind = "";
        detailTile = "";
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
            root.now = new Date();
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
            editing = false;
            detailTile = "";
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
        // Sized to what it shows (a few cards, or the "all caught up" note), up to the full height.
        height: Math.max(160, Math.min(parent.height, dualList.height + 36))
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
                            width: parent.width
                            text: root.dateText
                            role: "bodyMedium"
                            color: Theme.surfaceVariantInk
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            width: parent.width
                            visible: root.batteryText.length > 0
                            text: "Battery " + root.batteryText
                            role: "bodySmall"
                            color: Theme.surfaceVariantInk
                            wrapMode: Text.WordWrap
                        }
                    }
                    IconButton {
                        symbol: "edit"
                        variant: "tonal"
                        toggle: true
                        checked: root.editing
                        Accessible.name: "Edit tiles"
                        onClicked: root.editing = !root.editing
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
                    id: tileGrid
                    width: parent.width
                    visible: !root.editing
                    height: visible ? implicitHeight : 0
                    columns: 4
                    columnSpacing: 8
                    rowSpacing: 8
                    Repeater {
                        model: TilesState.enabled
                        delegate: QuickTile {
                            id: tile
                            required property string modelData
                            readonly property var info: TilesState.describe(modelData)
                            Layout.fillWidth: true
                            Layout.columnSpan: info.large ? 2 : 1
                            large: info.large
                            title: info.title
                            subtitle: info.subtitle
                            symbol: info.symbol
                            hasDetails: info.hasDetails
                            activated: modelData === "audio_devices" ? root.soundOpen : info.activated
                            enabled: info.enabled || info.hasDetails
                            dimmed: !info.enabled
                            onClicked: if (info.enabled)
                                root.activateTile(modelData)
                            onDetailsRequested: root.tileDetails(modelData)
                        }
                    }
                }
                TileEditor {
                    width: parent.width
                    visible: root.editing
                    height: visible ? implicitHeight : 0
                    onDone: root.editing = false
                }
                WirelessPanel {
                    width: parent.width
                    kind: root.connectionKind || "wifi"
                    visible: root.connectionKind.length > 0
                    height: visible ? implicitHeight : 0
                    onCloseRequested: root.connectionKind = ""
                }
                TileDetails {
                    width: parent.width
                    tile: root.detailTile
                    visible: tile.length > 0 && !root.editing
                    height: visible ? implicitHeight : 0
                    onCloseRequested: root.detailTile = ""
                    onSettingsRequested: page => ShellState.openSettings(root.screen, page)
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
