import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../components"
import "../services"
import "../services/LaunchTracking.js" as LaunchTracking

// Recents overview: open windows, most recently used first. Pick one to switch
// to it, dismiss one to close it. Cards show a preview taken when the overview opened (older for windows on other workspaces).
PanelWindow {
    id: root
    property bool opened: ShellState.recentsOpen && ShellState.activeScreen === screen
    readonly property var windows: Windows.list.slice().sort((a, b) => a.recency - b.recency)
    // Live window contents through the compositor's screencopy support, when it offers them.
    // Quickshell hands Hyprland's address back with or without the 0x prefix, so compare without it.
    readonly property var toplevels: Hyprland.toplevels ? Hyprland.toplevels.values : []
    function liveSource(window) {
        const want = String(window.address).replace(/^0x/, "").toLowerCase();
        const match = toplevels.find(item => String(item.address).replace(/^0x/, "").toLowerCase() === want);
        return match && match.wayland ? match.wayland : null;
    }
    function appFor(window) {
        return SystemBridge.apps.find(app => LaunchTracking.matches(app, window.class)) || null;
    }
    // Address of the first app chosen for split screen; the next card picked is put beside it.
    property string splitFirst: ""
    function focusWindow(window) {
        if (splitFirst.length > 0 && splitFirst !== window.address) {
            const first = splitFirst;
            ShellState.close();
            Windows.split(first, window.address);
            return;
        }
        ShellState.close();
        Windows.show(window);
    }
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-recents"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || scrim.opacity > .01
    onOpenedChanged: {
        splitFirst = "";
        if (opened)
            openedSetup();
    }
    function openedSetup() {
        Hyprland.refreshToplevels();
        strip.currentIndex = 0;
        strip.forceActiveFocus();
    }
    Rectangle {
        id: scrim
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.55)
        opacity: root.opened ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Column {
        anchors.centerIn: parent
        width: parent.width
        spacing: 28
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : 0.96
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
            }
        }
        ListView {
            id: strip
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(parent.width - 48, Math.max(1, count) * 288)
            height: 352
            orientation: ListView.Horizontal
            spacing: 24
            clip: false
            model: root.windows
            keyNavigationEnabled: true
            highlightFollowsCurrentItem: true
            boundsBehavior: Flickable.StopAtBounds
            Keys.onEscapePressed: {
                if (root.splitFirst.length > 0)
                    root.splitFirst = "";
                else
                    ShellState.close();
            }
            Keys.onReturnPressed: if (root.windows.length)
                root.focusWindow(root.windows[currentIndex])
            Keys.onDeletePressed: if (root.windows.length)
                Windows.close(root.windows[currentIndex].address)
            delegate: Item {
                id: slot
                required property var modelData
                required property int index
                readonly property var app: root.appFor(modelData)
                width: 264
                height: strip.height
                Rectangle {
                    id: card
                    anchors.fill: parent
                    radius: Theme.shape.extraLarge
                    color: slot.modelData.focused ? Theme.primaryContainer : Theme.surfaceContainerHigh
                    border.width: root.splitFirst === slot.modelData.address || (strip.activeFocus && strip.currentIndex === slot.index) ? 3 : 0
                    border.color: Theme.primary
                    scale: cardArea.pressed ? 0.97 : cardArea.containsMouse ? 1.02 : 1
                    Behavior on scale {
                        NumberAnimation {
                            duration: Theme.fast
                            easing.type: Easing.OutBack
                        }
                    }
                    Behavior on color {
                        ColorAnimation {
                            duration: Theme.fast
                        }
                    }
                    MouseArea {
                        id: cardArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        Accessible.role: Accessible.Button
                        Accessible.name: "Switch to " + (slot.app ? slot.app.name : slot.modelData.class) + ", " + slot.modelData.title
                        onClicked: root.focusWindow(slot.modelData)
                    }
                    Row {
                        x: 16
                        y: 14
                        spacing: 10
                        AppIcon {
                            width: 28
                            height: 28
                            icon: slot.app ? slot.app.icon : slot.modelData.class.toLowerCase()
                            label: slot.app ? slot.app.name : slot.modelData.class
                        }
                        Label {
                            anchors.verticalCenter: parent.verticalCenter
                            width: card.width - 16 - 28 - 10 - 16 - 88
                            text: slot.app ? slot.app.name : slot.modelData.class
                            role: "titleSmall"
                            color: slot.modelData.focused ? Theme.primaryContainerInk : Theme.surfaceInk
                            elide: Text.ElideRight
                        }
                    }
                    IconButton {
                        objectName: "recents-split-" + slot.index
                        anchors.right: parent.right
                        anchors.rightMargin: 52
                        y: 8
                        implicitWidth: 40
                        implicitHeight: 40
                        iconSize: 20
                        symbol: "snap_left"
                        Accessible.name: root.splitFirst === slot.modelData.address ? "Cancel split screen" : "Split screen with " + slot.modelData.title
                        onClicked: root.splitFirst = root.splitFirst === slot.modelData.address ? "" : slot.modelData.address
                    }
                    IconButton {
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        y: 8
                        implicitWidth: 40
                        implicitHeight: 40
                        iconSize: 20
                        symbol: "close"
                        Accessible.name: "Close " + slot.modelData.title
                        onClicked: Windows.close(slot.modelData.address)
                    }
                    Rectangle {
                        id: preview
                        readonly property string shot: Windows.thumbFor(slot.modelData.address)
                        x: 16
                        y: 56
                        width: card.width - 32
                        height: 140
                        radius: 24
                        clip: true
                        color: slot.modelData.focused ? Theme.primary : Theme.secondaryContainer
                        Image {
                            anchors.fill: parent
                            visible: preview.shot.length > 0 && status === Image.Ready && !live.hasContent
                            source: preview.shot
                            asynchronous: true
                            cache: false
                            fillMode: Image.PreserveAspectCrop
                            horizontalAlignment: Image.AlignLeft
                            verticalAlignment: Image.AlignTop
                        }
                        Loader {
                            id: live
                            anchors.fill: parent
                            // Capture only while the overview is open and the window is not minimized.
                            active: root.opened && !slot.modelData.minimized && root.liveSource(slot.modelData) !== null
                            source: "../components/LivePreview.qml"
                            readonly property bool hasContent: status === Loader.Ready && item !== null && item.hasContent
                            onLoaded: item.source = Qt.binding(() => root.liveSource(slot.modelData))
                            visible: hasContent
                        }
                        AppIcon {
                            anchors.centerIn: parent
                            width: 72
                            height: 72
                            visible: preview.shot.length === 0 && !live.hasContent
                            icon: slot.app ? slot.app.icon : slot.modelData.class.toLowerCase()
                            label: slot.app ? slot.app.name : slot.modelData.class
                        }
                    }
                    Label {
                        x: 16
                        y: 212
                        width: parent.width - 32
                        text: slot.modelData.title || slot.modelData.class
                        role: "bodyMedium"
                        color: slot.modelData.focused ? Theme.primaryContainerInk : Theme.surfaceInk
                        wrapMode: Text.WordWrap
                        maximumLineCount: 3
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        x: 16
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 14
                        height: 28
                        width: wsLabel.implicitWidth + 24
                        radius: 14
                        color: Theme.withAlpha(slot.modelData.focused ? Theme.primaryContainerInk : Theme.surfaceInk, 0.08)
                        Label {
                            id: wsLabel
                            anchors.centerIn: parent
                            text: slot.modelData.minimized ? "Minimized" : "Workspace " + slot.modelData.workspace
                            role: "labelMedium"
                            color: slot.modelData.focused ? Theme.primaryContainerInk : Theme.surfaceVariantInk
                        }
                    }
                }
            }
            Column {
                anchors.centerIn: parent
                spacing: 12
                visible: strip.count === 0
                Symbol {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 56
                    height: 56
                    name: "recents"
                    color: Theme.inverseSurfaceInk
                }
                Label {
                    text: Windows.available ? "No recent apps" : "Open windows are unavailable in this session"
                    role: "titleLarge"
                    color: Theme.inverseSurfaceInk
                }
            }
        }
        RowLayout {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 12
            visible: strip.count > 0
            PillButton {
                text: "Close all"
                symbol: "trash"
                variant: "filled"
                onClicked: {
                    Windows.closeMany(root.windows.map(window => window.address));
                    ShellState.close();
                }
            }
            Label {
                objectName: "recents-hint"
                text: root.splitFirst.length > 0 ? "Choose the second app for split screen · Esc to cancel" : "Enter to open · Delete to close · Esc to leave"
                role: "labelMedium"
                color: Theme.inverseSurfaceInk
                opacity: 0.8
            }
        }
    }
}
