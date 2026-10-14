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
                Label { text: "Connections"; font.pixelSize: 21; font.weight: Font.DemiBold }
                QuickTile {
                    width: parent.width
                    title: "Wi-Fi"
                    subtitle: SystemBridge.snapshot.wifi.available ?
                              SystemBridge.snapshot.wifi.label : "No wireless adapter"
                    symbol: "wifi"
                    activated: SystemBridge.snapshot.wifi.enabled
                    enabled: SystemBridge.snapshot.wifi.available
                    onClicked: SystemBridge.action("wifi")
                }
                QuickTile {
                    width: parent.width
                    title: "Bluetooth"
                    subtitle: SystemBridge.snapshot.bluetooth.available ?
                              (activated ? "On" : "Off") : "Not available"
                    symbol: "bluetooth"
                    activated: SystemBridge.snapshot.bluetooth.enabled
                    enabled: SystemBridge.snapshot.bluetooth.available
                    onClicked: SystemBridge.action("bluetooth")
                }
                PillButton {
                    width: parent.width
                    text: "Manage Wi-Fi and Bluetooth devices"
                    onClicked: ShellState.toggleShade(root.screen)
                }
                Rectangle { width: parent.width; height: 1; color: Theme.outline; opacity: .26 }
                Label { text: "Display & audio"; font.pixelSize: 21; font.weight: Font.DemiBold }
                DisplaySettings { width: parent.width }
                ExpressiveSlider {
                    width: parent.width
                    symbol: "brightness"
                    label: "Brightness"
                    enabled: SystemBridge.snapshot.brightness.available
                    modelValue: SystemBridge.snapshot.brightness.value
                    onCommitted: level => SystemBridge.action("brightness", level)
                }
                ExpressiveSlider {
                    width: parent.width
                    symbol: "volume"
                    label: "Output volume"
                    enabled: SystemBridge.snapshot.volume.available
                    modelValue: SystemBridge.snapshot.volume.value
                    onCommitted: level => SystemBridge.action("volume", level)
                }
                QuickTile {
                    width: parent.width
                    title: "Sound output"
                    subtitle: activated ? "On" : "Muted"
                    symbol: "volume"
                    activated: !SystemBridge.snapshot.volume.muted
                    enabled: SystemBridge.snapshot.volume.available
                    onClicked: SystemBridge.action("mute")
                }
                QuickTile {
                    width: parent.width
                    title: "Microphone"
                    subtitle: activated ? "On" : "Muted"
                    symbol: "microphone"
                    activated: !SystemBridge.snapshot.microphone.muted
                    enabled: SystemBridge.snapshot.microphone.available
                    onClicked: SystemBridge.action("microphone-mute")
                }
                Rectangle { width: parent.width; height: 1; color: Theme.outline; opacity: .26 }
                Label { text: "Notifications & privacy"; font.pixelSize: 21; font.weight: Font.DemiBold }
                QuickTile {
                    width: parent.width
                    title: "Do Not Disturb"
                    subtitle: activated ? "Notifications are quiet" : "Notifications enabled"
                    symbol: "dnd"
                    activated: SystemBridge.snapshot.settings.dnd
                    onClicked: SystemBridge.action("dnd")
                }
                Rectangle { width: parent.width; height: 1; color: Theme.outline; opacity: .26 }
                Label { text: "Pointer & keyboard"; font.pixelSize: 21; font.weight: Font.DemiBold }
                Rectangle {
                    width: parent.width
                    height: 82
                    radius: 25
                    color: Theme.surfaceContainer
                    Label {
                        x: 17; y: 12
                        text: "Natural scrolling"
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label { x: 17; y: 43; text: "Scroll in the direction content moves"; opacity: .74 }
                    AndroidToggle {
                        anchors.right: parent.right
                        anchors.rightMargin: 18
                        anchors.verticalCenter: parent.verticalCenter
                        checked: InputState.values.natural_scroll === true
                        enabled: !InputState.busy
                        Accessible.name: "Natural scrolling"
                        onClicked: InputState.setValue("natural_scroll", checked)
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 82
                    radius: 25
                    color: Theme.surfaceContainer
                    Label {
                        x: 17; y: 12
                        text: "Tap to click"
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label { x: 17; y: 43; text: "Use a light tap on the touchpad"; opacity: .74 }
                    AndroidToggle {
                        anchors.right: parent.right
                        anchors.rightMargin: 18
                        anchors.verticalCenter: parent.verticalCenter
                        checked: InputState.values.tap_to_click === true
                        enabled: !InputState.busy
                        Accessible.name: "Tap to click"
                        onClicked: InputState.setValue("tap_to_click", checked)
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 104
                    radius: 25
                    color: Theme.surfaceContainer
                    Label { x: 17; y: 9; text: "Pointer speed"; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Slider {
                        id: speed
                        x: 16; y: 38
                        width: parent.width - 32
                        height: 56
                        from: -1; to: 1; stepSize: .1
                        value: InputState.values.pointer_speed
                        enabled: !InputState.busy
                        Accessible.name: "Pointer speed"
                        onPressedChanged: if (!pressed) InputState.setValue("pointer_speed", value.toFixed(1))
                        background: Rectangle {
                            x: speed.leftPadding
                            y: speed.topPadding + speed.availableHeight / 2 - height / 2
                            width: speed.availableWidth; height: 12; radius: 6
                            color: Theme.surfaceContainerHigh
                            Rectangle {
                                width: speed.visualPosition * parent.width
                                height: parent.height
                                radius: parent.radius
                                color: Theme.primary
                            }
                        }
                        handle: Rectangle {
                            x: speed.leftPadding + speed.visualPosition * (speed.availableWidth - width)
                            y: speed.topPadding + speed.availableHeight / 2 - height / 2
                            width: 26; height: 26; radius: 13
                            color: Theme.primary
                            scale: speed.pressed ? 1.18 : 1
                            Behavior on scale { NumberAnimation { duration: Theme.fast } }
                        }
                    }
                }
                Rectangle {
                    width: parent.width; height: 102; radius: 25
                    color: Theme.surfaceContainer
                    Label { x: 17; y: 10; text: "Key repeat speed"; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Slider {
                        id: repeatSpeed
                        x: 16; y: 39
                        width: parent.width - 32; height: 54
                        from: 10; to: 60; stepSize: 5
                        value: InputState.values.repeat_rate
                        enabled: !InputState.busy
                        Accessible.name: "Keyboard repeat speed"
                        onPressedChanged: if (!pressed) InputState.setValue("repeat_rate", Math.round(value))
                    }
                }
                Label {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    visible: InputState.error.length > 0
                    color: Theme.error
                    text: InputState.error
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
                    AndroidToggle {
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
                        color: Theme.primary
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
                    color: Theme.error
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
                Rectangle { width: parent.width; height: 1; color: Theme.outline; opacity: .26 }
                Label { text: "System"; font.pixelSize: 21; font.weight: Font.DemiBold }
                Rectangle {
                    width: parent.width
                    height: 104
                    radius: 28
                    color: Theme.surfaceContainer
                    Column {
                        x: 17; y: 15
                        width: parent.width - 34; spacing: 6
                        Label { text: "PrismOS · Arch Linux"; font.pixelSize: 17; font.weight: Font.DemiBold }
                        Label {
                            width: parent.width
                            text: "Hyprland · Quickshell · Wayland"
                            opacity: .74
                        }
                        Label {
                            width: parent.width
                            text: SystemBridge.snapshot.battery.available ?
                                  ("Battery " + SystemBridge.snapshot.battery.value + "%") :
                                  "Desktop power"
                            opacity: .74
                        }
                    }
                }
                Row {
                    spacing: 8
                    width: parent.width
                    PillButton {
                        text: "Power options"
                        onClicked: ShellState.openPower(root.screen)
                    }
                    PillButton {
                        text: "Software"
                        filled: true
                        onClicked: ShellState.openStore(root.screen)
                    }
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
