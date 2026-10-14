import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../components"
import "../services"

// Native Material-inspired software center. Flatpak calls are isolated in prismctl.
PanelWindow {
    id: root
    property bool opened: ShellState.storeOpen && ShellState.activeScreen === screen
    property bool configured: false
    property bool flatpakAvailable: false
    property string tab: "Games"
    property string task: ""
    property string notice: ""
    property var items: []
    property var followArgs: []
    property string followTask: ""
    property bool busy: worker.running

    anchors { top: true; left: true; right: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-store"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01

    function request(args, kind) {
        if (worker.running)
            return;
        task = kind;
        notice = "";
        worker.command = ["prismctl"].concat(args);
        worker.running = true;
    }
    function queue(args, kind) {
        followArgs = args;
        followTask = kind;
    }
    function lookUp() {
        if (!configured)
            return;
        request(["store", "search", searchField.text.trim() || (tab === "Games" ? "game" : "editor")], "search");
    }
    function activateTab(name) {
        tab = name;
        searchField.text = name === "Games" ? "game" : "editor";
        lookUp();
    }
    function handleReply(output) {
        try {
            const data = JSON.parse(output);
            if (data.ok === false) {
                notice = data.error || "Request failed";
                return;
            }
            if (task === "status" || task === "enable") {
                flatpakAvailable = data.available === true;
                configured = data.configured === true;
                if (configured && tab !== "Android")
                    queue(["store", "search", searchField.text || "game"], "search");
            } else if (task === "search") {
                items = data.items || [];

            } else if (task === "install" || task === "remove") {
                notice = task === "install" ? "Installed — ready to play!" : "Application removed";
                SystemBridge.refreshApps();
                queue(["store", "search", searchField.text || "game"], "search");
            } else if (task === "open") {
                notice = "Opening application…";
            }
        } catch (e) {
            notice = "The software service returned an invalid response";
        }
    }
    onOpenedChanged: if (opened) {
        tab = "Games";
        items = [];
        searchField.text = "game";
        request(["store", "status"], "status");
    }
    Timer {
        id: followUp
        interval: 80
        onTriggered: {
            if (root.followArgs.length && !worker.running) {
                const args = root.followArgs, nextTask = root.followTask;
                root.followArgs = [];
                root.followTask = "";
                root.request(args, nextTask);
            }
        }
    }
    Process {
        id: worker
        stdout: StdioCollector {
            onStreamFinished: root.handleReply(text)
        }
        onExited: if (root.followArgs.length) followUp.restart()
    }
    Rectangle {
        anchors.fill: parent
        color: "#661b1425"
        opacity: root.opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }
    MouseArea { anchors.fill: parent; onClicked: ShellState.close() }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(1020, root.width - 32)
        height: Math.min(760, root.height - 64)
        radius: 40
        color: Theme.surface
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .94
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
        Behavior on scale { NumberAnimation { duration: Theme.standard; easing.type: Easing.OutBack } }
        MouseArea { anchors.fill: parent; onClicked: {} }
        Label {
            x: 26; y: 24; text: "✦  Prism Store"
            font.pixelSize: 30; font.weight: Font.Bold
        }
        PillButton {
            anchors.top: parent.top; anchors.right: parent.right; anchors.margins: 20
            text: "×"; Accessible.name: "Close Prism Store"
            onClicked: ShellState.close()
        }
        Row {
            x: 26; y: 82; spacing: 10
            Repeater {
                model: ["Games", "Apps"]
                delegate: PillButton {
                    required property string modelData
                    text: modelData
                    filled: root.tab === modelData
                    enabled: !root.busy
                    onClicked: root.activateTab(modelData)
                }
            }
        }
        TextField {
            id: searchField
            x: 26; y: 144; width: parent.width - 52; height: 50
            visible: root.configured
            placeholderText: "Search Flathub games and apps"
            color: Theme.onSurface
            font.family: Theme.font
            font.pixelSize: 16
            leftPadding: 20
            background: Rectangle { color: Theme.surfaceContainer; radius: 25 }
            onAccepted: root.lookUp()
            Keys.onEscapePressed: ShellState.close()
        }
        Label {
            x: 30; y: 205; width: parent.width - 60
            text: root.busy ? "Working…" : root.notice
            color: Theme.primaryStrong
            visible: root.busy || root.notice.length > 0
            elide: Text.ElideRight
        }
        ListView {
            id: results
            x: 26; y: 240
            width: parent.width - 52
            height: Math.max(80, parent.height - 264)
            clip: true
            spacing: 10
            visible: root.configured
            model: root.items
            ScrollBar.vertical: ScrollBar {}
            delegate: Rectangle {
                id: resultRow
                required property var modelData
                width: results.width
                height: 100
                radius: 26
                color: Theme.surfaceContainer
                Rectangle {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    width: 64; height: 64; radius: 22
                    color: Theme.primary
                    Label {
                        anchors.centerIn: parent; text: "✦"
                        color: Theme.onPrimary; font.pixelSize: 28
                    }
                }
                Label {
                    x: 94; y: 15; width: Math.max(80, parent.width - 260)
                    text: modelData.name
                    font.pixelSize: 17; font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    x: 94; y: 42; width: Math.max(80, parent.width - 260)
                    text: modelData.description || modelData.id
                    maximumLineCount: 2
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    opacity: .75
                }
                PillButton {
                    anchors.right: parent.right; anchors.rightMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    filled: true
                    enabled: !root.busy
                    text: resultRow.modelData.installed ? "Open" : "Install"
                    onClicked: root.request(["store", resultRow.modelData.installed ? "open" : "install", resultRow.modelData.id], resultRow.modelData.installed ? "open" : "install")
                }
                PillButton {
                    anchors.right: parent.right; anchors.rightMargin: 110
                    anchors.verticalCenter: parent.verticalCenter
                    visible: resultRow.modelData.installed
                    enabled: !root.busy
                    text: "Remove"
                    Accessible.name: "Uninstall " + resultRow.modelData.name
                    onClicked: root.request(["store", "remove", resultRow.modelData.id], "remove")
                }
            }
            Label {
                anchors.centerIn: parent
                visible: results.count === 0 && !root.busy
                text: "Search to discover games and apps"
            }
        }
        Column {
            x: 30; y: 235; width: parent.width - 60; spacing: 18
            visible: !root.configured
            Label {
                text: root.flatpakAvailable ? "Connect to Flathub" : "Flatpak is not installed"
                font.pixelSize: 24; font.weight: Font.DemiBold
            }
            Label {
                width: parent.width; wrapMode: Text.WordWrap
                text: root.flatpakAvailable ? "Enable Flathub for this user to install real Linux games and apps. No repository changes happen until you select Enable." : "Install Flatpak using: sudo pacman -S flatpak"
            }
            PillButton {
                text: "Enable Flathub"; filled: true
                enabled: root.flatpakAvailable && !root.busy
                onClicked: root.request(["store", "enable"], "enable")
            }
        }
    }
}
