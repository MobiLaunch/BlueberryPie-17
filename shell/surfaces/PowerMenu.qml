import QtQuick
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

PanelWindow {
    id: root
    property bool opened: ShellState.powerOpen && ShellState.activeScreen === screen
    property string confirming: ""
    property var titles: ({
            lock: "Lock",
            suspend: "Suspend",
            logout: "Sign out",
            restart: "Restart",
            shutdown: "Power off"
        })
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-power"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened
    onOpenedChanged: {
        confirming = "";
        if (opened)
            card.forceActiveFocus();
    }
    Rectangle {
        anchors.fill: parent
        color: "#661b1425"
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(420, root.width - 32)
        height: Math.min(520, root.height - 80)
        color: Theme.surface
        radius: 36
        focus: true
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        Keys.onEscapePressed: {
            if (root.confirming)
                root.confirming = "";
            else
                ShellState.close();
        }
        Flickable {
            anchors.fill: parent
            anchors.margins: 26
            clip: true
            contentHeight: choices.height
            Column {
                id: choices
                width: parent.width
                spacing: 12
                Label {
                    width: parent.width
                    text: root.confirming ? root.titles[root.confirming] + " your session?" : "Take a moment."
                    font.pixelSize: 28
                    font.weight: Font.Bold
                    wrapMode: Text.WordWrap
                }
                Label {
                    width: parent.width
                    text: root.confirming === "restart" || root.confirming === "shutdown" || root.confirming === "logout" ? "Save your work before continuing." : "Choose what happens next."
                    wrapMode: Text.WordWrap
                }
                Repeater {
                    model: root.confirming ? [] : ["lock", "suspend", "logout", "restart", "shutdown"]
                    delegate: PillButton {
                        required property string modelData
                        width: choices.width
                        text: root.titles[modelData]
                        filled: modelData === "lock"
                        enabled: !!SystemBridge.snapshot.power[modelData] && !SystemBridge.busy
                        onClicked: root.confirming = modelData
                    }
                }
                PillButton {
                    width: parent.width
                    text: "Confirm " + (root.titles[root.confirming] || "")
                    filled: true
                    visible: !!root.confirming
                    enabled: !SystemBridge.busy
                    onClicked: {
                        const action = root.confirming;
                        ShellState.close();
                        SystemBridge.action(action);
                    }
                }
                PillButton {
                    width: parent.width
                    text: "Cancel"
                    onClicked: {
                        if (root.confirming)
                            root.confirming = "";
                        else
                            ShellState.close();
                    }
                }
            }
        }
    }
}
