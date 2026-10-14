import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.drawerOpen && ShellState.activeScreen === screen
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-drawer"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    onOpenedChanged: if (opened) {
        search.text = "";
        search.forceActiveFocus();
    }
    Rectangle {
        anchors.fill: parent
        color: "#551b1425"
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
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(980, root.width - 40)
        height: Math.min(730, root.height - 100)
        color: Theme.surface
        radius: 40
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .94
        transform: Translate {
            y: root.opened ? 0 : 60
            Behavior on y {
                NumberAnimation {
                    duration: Theme.standard
                    easing.type: Easing.OutBack
                    easing.overshoot: .5
                }
            }
        }
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
                easing.overshoot: .5
            }
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        Label {
            x: 28
            y: 25
            text: "Your apps"
            font.pixelSize: 32
            font.weight: Font.Bold
        }
        PillButton {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 20
            text: "×"
            Accessible.name: "Close app drawer"
            onClicked: ShellState.close()
        }
        TextField {
            id: search
            x: 24
            y: 82
            width: parent.width - 48
            height: 54
            placeholderText: "Search your apps"
            color: Theme.onSurface
            font.family: Theme.font
            font.pixelSize: 16
            leftPadding: 22
            background: Rectangle {
                radius: 27
                color: Theme.surfaceContainer
                border.width: search.activeFocus ? 2 : 0
                border.color: Theme.primaryStrong
            }
            Keys.onEscapePressed: ShellState.close()
            Keys.onReturnPressed: {
                const matches = grid.model;
                if (matches.length)
                    ShellState.launch(matches[0], root.screen, root.width / 2, root.height / 2);
            }
        }
        GridView {
            id: grid
            x: 24
            y: 158
            width: parent.width - 48
            height: parent.height - 186
            clip: true
            cellWidth: width / Math.max(2, Math.floor(width / 130))
            cellHeight: 122
            model: SystemBridge.apps.filter(app => (app.name + " " + app.description).toLowerCase().includes(search.text.toLowerCase()))
            ScrollBar.vertical: ScrollBar {}
            delegate: Button {
                id: appButton
                required property var modelData
                width: grid.cellWidth
                height: grid.cellHeight
                hoverEnabled: true
                Accessible.name: modelData.name
                background: Rectangle {
                    anchors.margins: 5
                    radius: 28
                    color: appButton.hovered || appButton.activeFocus ? Theme.surfaceContainer : "transparent"
                }
                contentItem: Column {
                    spacing: 10
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 64
                        height: 64
                        radius: 24
                        color: index % 3 === 0 ? Theme.primary : index % 3 === 1 ? Theme.secondary : Theme.tertiary
                        scale: appButton.down ? .9 : 1
                        Behavior on scale {
                            NumberAnimation {
                                duration: Theme.fast
                                easing.type: Easing.OutBack
                            }
                        }
                        Image {
                            anchors.centerIn: parent
                            width: 40
                            height: 40
                            sourceSize: Qt.size(40, 40)
                            fillMode: Image.PreserveAspectFit
                            source: Quickshell.iconPath(appButton.modelData.icon, "application-x-executable")
                        }
                    }
                    Label {
                        width: parent.width - 8
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: appButton.modelData.name
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                    }
                }
                onClicked: {
                    const p = mapToItem(root.contentItem, width / 2, 36);
                    ShellState.launch(modelData, root.screen, p.x, p.y);
                }
            }
            Label {
                anchors.centerIn: parent
                visible: grid.count === 0
                text: SystemBridge.apps.length ? "No apps match your search" : "No desktop applications found"
            }
        }
    }
}
