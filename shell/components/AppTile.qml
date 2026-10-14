import QtQuick
import QtQuick.Controls
import Quickshell
import "."
import "../services"

// Launcher grid cell: squircle icon plate, name, pinned and running markers,
// app menu on right-click, long-press or the Menu key.
Button {
    id: root
    required property var app
    property bool held: false
    readonly property var windows: Windows.forApp(app)
    signal launched(real x, real y)
    leftPadding: 4
    rightPadding: 4
    topPadding: 8
    bottomPadding: 6
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: app.name
    ToolTip.visible: hovered && app.description.length > 0
    ToolTip.delay: 800
    ToolTip.text: app.description
    function openApp() {
        const p = mapToItem(null, width / 2, 40);
        launched(p.x, p.y);
    }
    background: Rectangle {
        radius: Theme.shape.extraLarge - 4
        color: "transparent"
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.primary
        StateLayer {
            anchors.fill: parent
            radius: parent.radius
            tint: Theme.onSurface
            hovered: root.hovered
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Column {
        spacing: 8
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 64
            height: 64
            radius: root.down ? 16 : 22
            color: Theme.surfaceContainerHigh
            scale: root.down ? 0.92 : 1
            Behavior on scale {
                NumberAnimation {
                    duration: Theme.fast
                    easing.type: Easing.OutBack
                }
            }
            Behavior on radius {
                NumberAnimation {
                    duration: Theme.fast
                }
            }
            Image {
                anchors.centerIn: parent
                width: 44
                height: 44
                sourceSize: Qt.size(88, 88)
                fillMode: Image.PreserveAspectFit
                source: Quickshell.iconPath(root.app.icon, "application-x-executable")
            }
            Rectangle {
                visible: Applications.isPinned(root.app.id)
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: -2
                width: 16
                height: 16
                radius: 8
                color: Theme.primary
                Symbol {
                    anchors.centerIn: parent
                    width: 10
                    height: 10
                    name: "check"
                    weight: 3
                    color: Theme.onPrimary
                }
            }
            Rectangle {
                visible: root.windows.length > 0
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 3
                width: 16
                height: 4
                radius: 2
                color: Theme.primary
            }
        }
        Label {
            width: parent.width
            text: root.app.name
            role: "labelMedium"
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
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
    Keys.onReturnPressed: openApp()
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
