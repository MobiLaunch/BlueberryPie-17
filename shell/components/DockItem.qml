import QtQuick
import QtQuick.Controls
import Quickshell
import "."
import "../services"

// One application in the dock. Shows a running indicator, a notification badge
// and an app menu (right-click, long-press or the Menu key).
Button {
    id: root
    required property var app
    property var windows: Windows.forApp(app)
    readonly property bool running: windows.length > 0
    readonly property bool focusedApp: windows.some(window => window.focused)
    readonly property bool allMinimized: running && windows.every(window => window.minimized)
    property bool held: false
    signal activated(real x, real y)
    implicitWidth: 56
    implicitHeight: 60
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: app.name + (running ? ", " + windows.length + (windows.length === 1 ? " window open" : " windows open") : "")
    ToolTip.visible: hovered && !menu.opened
    ToolTip.delay: 450
    ToolTip.text: app.name + (windows.length === 1 && windows[0].title ? " — " + windows[0].title : "") + (allMinimized ? " (minimized)" : "")
    scale: down ? 0.9 : hovered ? 1.06 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    background: Rectangle {
        radius: 20
        color: root.focusedApp ? Theme.secondaryContainer : "transparent"
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.primary
        StateLayer {
            anchors.fill: parent
            radius: parent.radius
            tint: Theme.surfaceInk
            hovered: root.hovered
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Item {
        AppIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 6
            width: 40
            height: 40
            icon: root.app.icon
            label: root.app.name
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 3
            visible: root.running
            width: root.focusedApp ? 18 : 6
            height: 4
            radius: 2
            color: root.allMinimized ? "transparent" : Theme.primary
            border.width: root.allMinimized ? 1 : 0
            border.color: Theme.outline
            Behavior on width {
                NumberAnimation {
                    duration: Theme.fast
                    easing.type: Easing.OutBack
                }
            }
        }
        Rectangle {
            visible: root.app.id.length > 0 && Applications.badgeCount(root.app.id) > 0
            anchors.right: parent.right
            anchors.rightMargin: 6
            y: 4
            width: 12
            height: 12
            radius: 6
            color: Theme.error
            border.width: 2
            border.color: Theme.surfaceContainer
        }
    }
    function openApp() {
        const p = mapToItem(null, width / 2, height / 2);
        activated(p.x, p.y);
    }
    onPressedChanged: if (pressed)
        held = false
    onPressAndHold: {
        held = true;
        menu.open();
    }
    onClicked: if (!held)
        openApp()
    Keys.onMenuPressed: menu.open()
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: menu.open()
    }
    AppMenu {
        id: menu
        app: root.app
        windows: root.windows
        onLaunchRequested: root.openApp()
    }
}
