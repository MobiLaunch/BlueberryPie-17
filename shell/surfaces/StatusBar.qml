import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.SystemTray
import "../components"
import "../services"

// Top bar: launcher and clock with notification chips on the left, the focused
// window in the middle, tray and a system-status pill (opens Quick Settings).
PanelWindow {
    id: root
    property string timeText: Qt.formatTime(new Date(), "hh:mm")
    property string dateText: Qt.formatDate(new Date(), "ddd, MMM d")
    readonly property var snap: SystemBridge.snapshot
    anchors {
        top: true
        left: true
        right: true
    }
    implicitHeight: 44
    exclusiveZone: 44
    WlrLayershell.namespace: "prism-bar"
    color: Theme.withAlpha(Theme.surface, 0.8)
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            root.timeText = Qt.formatTime(new Date(), "hh:mm");
            root.dateText = Qt.formatDate(new Date(), "ddd, MMM d");
        }
    }
    RowLayout {
        id: leftCluster
        x: 8
        anchors.verticalCenter: parent.verticalCenter
        spacing: 6
        IconButton {
            symbol: "apps_grid"
            variant: "tonal"
            implicitWidth: 38
            implicitHeight: 38
            iconSize: 20
            Accessible.name: "All applications"
            onClicked: ShellState.toggleDrawer(root.screen)
        }
        Rectangle {
            Layout.preferredWidth: clockRow.implicitWidth + 24
            Layout.preferredHeight: 36
            radius: 18
            color: clockArea.containsMouse || ShellState.shadeOpen ? Theme.surfaceContainerHigh : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: Theme.fast
                }
            }
            Row {
                id: clockRow
                anchors.centerIn: parent
                spacing: 10
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.timeText
                    role: "titleMedium"
                    font.weight: Font.Bold
                }
                Label {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.dateText
                    role: "bodyMedium"
                    color: Theme.surfaceVariantInk
                }
            }
            MouseArea {
                id: clockArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Accessible.role: Accessible.Button
                Accessible.name: "Notifications and Quick Settings"
                onClicked: ShellState.toggleShade(root.screen)
            }
        }
        Row {
            spacing: 4
            visible: Notifications.count > 0
            Repeater {
                model: Notifications.groups.slice(0, 4)
                delegate: Rectangle {
                    required property var modelData
                    width: 26
                    height: 26
                    radius: 13
                    color: modelData.items.some(note => note.urgency === 2) ? Theme.errorContainer : Theme.tertiaryContainer
                    Label {
                        anchors.centerIn: parent
                        text: (modelData.app || "?").charAt(0).toUpperCase()
                        role: "labelMedium"
                        color: Theme.tertiaryContainerInk
                    }
                }
            }
            Label {
                visible: Notifications.groups.length > 4
                anchors.verticalCenter: parent.verticalCenter
                text: "+" + (Notifications.groups.length - 4)
                role: "labelMedium"
                color: Theme.surfaceVariantInk
            }
        }
    }
    WindowCaption {
        anchors.centerIn: parent
        // Needs room between the left cluster and the status pill.
        visible: Windows.focused !== null && root.width >= 1100
        width: Math.min(implicitWidth, root.width * 0.42)
    }
    RowLayout {
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        spacing: 6
        Flickable {
            visible: SystemTray.items.values.length > 0
            Layout.preferredWidth: Math.max(0, Math.min(trayRow.implicitWidth, 160))
            Layout.preferredHeight: 36
            contentWidth: trayRow.implicitWidth
            clip: true
            Row {
                id: trayRow
                spacing: 3
                Repeater {
                    model: SystemTray.items
                    delegate: Button {
                        id: trayButton
                        required property var modelData
                        property bool held: false
                        implicitWidth: 34
                        implicitHeight: 36
                        leftPadding: 0
                        rightPadding: 0
                        topPadding: 0
                        bottomPadding: 0
                        hoverEnabled: true
                        Accessible.name: modelData.tooltipTitle || modelData.title || "Tray application"
                        ToolTip.visible: hovered
                        ToolTip.text: modelData.tooltipTitle || modelData.title
                        background: Rectangle {
                            radius: 17
                            color: trayButton.hovered ? Theme.surfaceContainerHigh : "transparent"
                        }
                        contentItem: Image {
                            source: trayButton.modelData.icon
                            sourceSize: Qt.size(22, 22)
                            fillMode: Image.PreserveAspectFit
                        }
                        function showMenu() {
                            if (modelData.hasMenu) {
                                const p = mapToItem(root.contentItem, 0, height);
                                modelData.display(root, p.x, p.y);
                            }
                        }
                        onPressedChanged: if (pressed)
                            held = false
                        onPressAndHold: {
                            held = true;
                            showMenu();
                        }
                        onClicked: if (!held) {
                            if (modelData.onlyMenu)
                                showMenu();
                            else
                                modelData.activate();
                        }
                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            onTapped: trayButton.showMenu()
                        }
                    }
                }
            }
        }
        Rectangle {
            id: statusPill
            Layout.preferredWidth: statusRow.implicitWidth + 28
            Layout.preferredHeight: 36
            radius: 18
            color: ShellState.shadeOpen ? Theme.primaryContainer : statusArea.containsMouse ? Theme.surfaceContainerHigh : Theme.surfaceContainer
            Behavior on color {
                ColorAnimation {
                    duration: Theme.fast
                }
            }
            Row {
                id: statusRow
                anchors.centerIn: parent
                spacing: 12
                Symbol {
                    visible: root.snap.settings.dnd
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18
                    height: 18
                    name: "notifications_off"
                    color: Theme.surfaceInk
                }
                Symbol {
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18
                    height: 18
                    name: root.snap.wifi.enabled ? "wifi" : "wifi_off"
                    color: Theme.surfaceInk
                    opacity: root.snap.wifi.available ? 1 : 0.5
                }
                Symbol {
                    visible: root.snap.bluetooth.enabled
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18
                    height: 18
                    name: "bluetooth"
                    color: Theme.surfaceInk
                }
                Symbol {
                    visible: root.snap.volume.available
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18
                    height: 18
                    name: root.snap.volume.muted ? "volume_off" : "volume"
                    color: Theme.surfaceInk
                }
                Row {
                    visible: root.snap.battery.available
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Symbol {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 22
                        height: 22
                        name: root.snap.battery.charging ? "battery_charging" : "battery"
                        level: root.snap.battery.available ? root.snap.battery.value / 100 : -1
                        color: root.snap.battery.value <= 15 && !root.snap.battery.charging ? Theme.error : Theme.surfaceInk
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.snap.battery.value + "%"
                        role: "labelMedium"
                    }
                }
            }
            MouseArea {
                id: statusArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                Accessible.role: Accessible.Button
                Accessible.name: "Quick Settings"
                onClicked: ShellState.toggleShade(root.screen)
            }
        }
    }
}
