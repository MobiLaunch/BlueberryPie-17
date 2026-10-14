import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../components"
import "../services"

// Prism Files is an expressive, nonprivileged user file browser.
// It never requests root and uses gio/xdg-open for associated file actions.
PanelWindow {
    id: root
    property bool opened: ShellState.filesOpen && ShellState.activeScreen === screen
    property string currentPath: ""
    property string parentPath: ""
    property string selectedPath: ""
    property var entries: []
    property var bookmarks: []
    property bool showHidden: false
    property bool more: false
    property var volumes: []
    property bool hasClipboard: false
    property string clipboardLabel: ""
    property bool volumeBusy: driveWriter.running
    property string error: ""
    property string message: ""
    property string operation: ""
    property string dialogKind: ""
    property string targetPath: ""
    property string targetName: ""
    property bool busy: worker.running
    readonly property var filtered: entries.filter(e =>
        !searchField.text.trim() ||
        e.name.toLowerCase().includes(searchField.text.trim().toLowerCase()))

    anchors { top: true; left: true; right: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-files"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || frame.opacity > .01

    function request(args, kind) {
        if (busy) return false;
        error = "";
        message = "";
        operation = kind;
        worker.command = ["prismctl", "files"].concat(args);
        worker.running = true;
        return true;
    }
    function navigate(path) {
        if (dialogKind) return;
        searchField.text = "";
        selectedPath = "";
        request(path ? ["list", path].concat(showHidden ? ["--hidden"] : []) :
                       ["list"].concat(showHidden ? ["--hidden"] : []), "list");
    }
    function refresh() { navigate(currentPath); }
    function pasteInto(folder) { request(["paste", folder], "paste"); }
    function copyDrop(source, folder) {
        if (!source || !folder || root.busy) return;
        request(["transfer", source, "--dest", folder], "paste");
    }
    function stageItem(path, action) { request(["stage", path, "--action", action], "stage"); }
    function loadDrives() { if (!driveReader.running && !volumeBusy) driveReader.running = true; }
    function driveAction(item) {
        if (driveWriter.running) return;
        driveWriter.command = ["prismctl", "drives", item.mounted ? "unmount" : "mount", item.device];
        driveWriter.running = true;
    }
    function openItem(item) {
        if (item.directory) {
            navigate(item.path);
        } else {
            request(["open", item.path], "open");
        }
    }
    function prompt(kind, path, name) {
        if (busy) return;
        targetPath = path || "";
        targetName = name || "";
        dialogKind = kind;
        dialogField.text = kind === "rename" ? targetName : "";
        if (kind !== "trash") dialogField.forceActiveFocus();
    }
    function applyPrompt() {
        if (busy) return;
        let args = [];
        const kind = dialogKind;
        if (kind === "new")
            args = ["mkdir", currentPath, "--name", dialogField.text];
        else if (kind === "rename")
            args = ["rename", targetPath, "--name", dialogField.text];
        else if (kind === "trash")
            args = ["trash", targetPath];
        else return;
        if (request(args, kind))
            dialogKind = "";
    }
    function consume(text) {
        try {
            const data = JSON.parse(text);
            if (data.ok === false) {
                error = data.error || "File action failed";
                return;
            }
            if (operation === "list") {
                currentPath = data.path || currentPath;
                parentPath = data.parent || currentPath;
                entries = data.items || [];
                more = data.more === true;
            } else {
                message = data.message || "Done";
                if (operation === "stage" || operation === "paste") clipboardRefresh.restart();
                if (operation === "new" || operation === "rename" || operation === "trash" || operation === "paste")
                    afterWrite.restart();
            }
        } catch (e) {
            error = "Could not read the Files service";
        }
    }
    onOpenedChanged: if (opened) {
        navigate(currentPath);
        if (!favorites.running) favorites.running = true;
        clipboardRefresh.restart();
        loadDrives();
    }
    Timer {
        id: afterWrite
        interval: 120
        onTriggered: root.refresh()
    }
    Process {
        id: worker
        stdout: StdioCollector { onStreamFinished: root.consume(text) }
    }
    Timer {
        id: clipboardRefresh
        interval: 80
        onTriggered: if (!clipboardReader.running) clipboardReader.running = true
    }
    Process {
        id: clipboardReader
        command: ["prismctl", "files", "clipboard"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.hasClipboard = data.has_item === true;
                    root.clipboardLabel = data.name || "";
                } catch (e) { root.hasClipboard = false; }
            }
        }
    }
    Process {
        id: driveReader
        command: ["prismctl", "drives", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === true) root.volumes = data.items || [];
                } catch (e) { root.volumes = []; }
            }
        }
    }
    Process {
        id: driveWriter
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false) root.error = data.error;
                    else root.message = data.message || "Drive updated";
                } catch (e) { root.error = "Drive operation failed"; }
            }
        }
        onExited: driveRefresh.restart()
    }
    Timer {
        id: driveRefresh
        interval: 300
        onTriggered: root.loadDrives()
    }
    Process {
        id: favorites
        command: ["prismctl", "files", "bookmarks"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const payload = JSON.parse(text);
                    if (payload.items)
                        root.bookmarks = payload.items;
                } catch (e) {
                    root.error = "Could not load favorite folders";
                }
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        color: "#651b1425"
        opacity: root.opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }
    MouseArea { anchors.fill: parent; onClicked: ShellState.close() }
    Rectangle {
        id: frame
        anchors.centerIn: parent
        width: Math.min(1100, root.width - 32)
        height: Math.min(760, root.height - 64)
        radius: 38
        color: Theme.surface
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .96
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
        Behavior on scale {
            NumberAnimation { duration: Theme.standard; easing.type: Easing.OutBack }
        }
        MouseArea { anchors.fill: parent; onClicked: {} }
        Keys.onEscapePressed: {
            if (root.dialogKind) root.dialogKind = "";
            else ShellState.close();
        }
        focus: root.opened
        Keys.onPressed: event => {
            if (root.dialogKind || root.busy) return;
            if (event.key === Qt.Key_V && (event.modifiers & Qt.ControlModifier)) {
                root.pasteInto(root.currentPath);
                event.accepted = true;
            } else if (root.selectedPath && (event.modifiers & Qt.ControlModifier)) {
                if (event.key === Qt.Key_C) {
                    root.stageItem(root.selectedPath, "copy");
                    event.accepted = true;
                } else if (event.key === Qt.Key_X) {
                    root.stageItem(root.selectedPath, "cut");
                    event.accepted = true;
                }
            }
        }
        Label {
            x: 28; y: 20
            text: "▣  Files"
            font.pixelSize: 30
            font.weight: Font.Bold
        }
        PillButton {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 18
            text: "×"
            Accessible.name: "Close Files"
            onClicked: ShellState.close()
        }
        Row {
            x: 28; y: 76
            spacing: 8
            PillButton {
                text: "↑"
                Accessible.name: "Parent folder"
                enabled: root.currentPath !== root.parentPath && !root.busy
                onClicked: root.navigate(root.parentPath)
            }
            PillButton {
                text: "⌂"
                Accessible.name: "Home folder"
                enabled: !root.busy
                onClicked: root.navigate("")
            }
            PillButton {
                text: "↻"
                Accessible.name: "Refresh folder"
                enabled: !root.busy
                onClicked: root.refresh()
            }
            PillButton {
                text: "New folder"
                enabled: !root.busy
                onClicked: root.prompt("new", "", "")
            }
            PillButton {
                text: "Paste"
                enabled: root.hasClipboard && !root.busy
                onClicked: root.pasteInto(root.currentPath)
            }
            PillButton {
                text: root.showHidden ? "Hide dotfiles" : "Show dotfiles"
                enabled: !root.busy
                onClicked: {
                    root.showHidden = !root.showHidden;
                    root.refresh();
                }
            }
        }
        Rectangle {
            x: 28; y: 138
            width: parent.width - 56
            height: 40
            radius: 20
            color: Theme.surfaceContainer
            Label {
                anchors.fill: parent
                anchors.margins: 10
                verticalAlignment: Text.AlignVCenter
                text: root.currentPath || "Home"
                elide: Text.ElideMiddle
                font.pixelSize: 13
            }
        }
        Row {
            x: 24; y: 193
            width: parent.width - 48
            height: parent.height - 215
            spacing: 16
            Rectangle {
                width: Math.min(190, parent.width * .25)
                height: parent.height
                radius: 25
                color: Theme.surfaceContainer
                Flickable {
                    anchors.fill: parent
                    anchors.margins: 12
                    contentHeight: places.height
                    clip: true
                    Column {
                        id: places
                        width: parent.width
                        spacing: 8
                        Label {
                            text: "Places"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                        Repeater {
                            model: root.bookmarks
                            delegate: PillButton {
                                required property var modelData
                                text: modelData.symbol + "  " + modelData.name
                                width: places.width
                                filled: root.currentPath === modelData.path
                                enabled: !root.busy
                                onClicked: root.navigate(modelData.path)
                                DropArea {
                                    anchors.fill: parent
                                    keys: ["prism-file"]
                                    onDropped: event => {
                                        if (event.source && event.source.filePath) {
                                            root.copyDrop(event.source.filePath, modelData.path);
                                            event.acceptProposedAction();
                                        }
                                    }
                                }
                            }
                        }
                        Label { text: "Removable drives"; font.weight: Font.DemiBold }
                        Repeater {
                            model: root.volumes
                            delegate: Column {
                                required property var modelData
                                width: places.width
                                spacing: 3
                                PillButton {
                                    width: parent.width
                                    text: "◉ " + modelData.label
                                    implicitHeight: 42
                                    enabled: modelData.mounted && !root.busy
                                    onClicked: root.navigate(modelData.mountpoint)
                                }
                                PillButton {
                                    width: parent.width
                                    implicitHeight: 36
                                    text: modelData.mounted ? "Safely unmount" : "Mount"
                                    enabled: !root.volumeBusy
                                    onClicked: root.driveAction(modelData)
                                }
                            }
                        }
                        PillButton {
                            width: places.width
                            text: "↻ Refresh drives"
                            implicitHeight: 38
                            enabled: !root.volumeBusy
                            onClicked: root.loadDrives()
                        }
                    }
                }
            }
            Rectangle {
                width: parent.width - Math.min(190, parent.width * .25) - 16
                height: parent.height
                radius: 26
                color: Theme.surfaceContainer
                ExpressiveTextField {
                    id: searchField
                    x: 12; y: 12
                    width: parent.width - 24
                    height: 45
                    placeholderText: "Search this folder"
                    Accessible.name: "Find files in current folder"
                }
                Label {
                    x: 17; y: 63
                    text: root.busy ? "Loading…" : root.error ? root.error :
                          root.message ? root.message :
                          root.filtered.length + " items" + (root.more ? " · more in folder" : "")
                    color: root.error ? Theme.roles.error : Theme.onSurface
                    font.pixelSize: 12
                    width: parent.width - 34
                    elide: Text.ElideRight
                }
                ExpressiveLoader {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 20
                    width: 24; height: 24
                    visible: root.busy
                }
                ListView {
                    id: listing
                    x: 8; y: 87
                    width: parent.width - 16
                    height: parent.height - 96
                    model: root.filtered
                    spacing: 4
                    clip: true
                    ScrollBar.vertical: ScrollBar {}
                    delegate: Rectangle {
                        id: fileRow
                        required property var modelData
                        property string filePath: modelData.path
                        Drag.active: rowDrag.active
                        Drag.keys: ["prism-file"]
                        Drag.source: fileRow
                        Drag.hotSpot.x: 22
                        Drag.hotSpot.y: 32
                        width: listing.width
                        height: 64
                        radius: 20
                        color: root.selectedPath === modelData.path ?
                               Theme.primary : area.containsMouse ? Theme.surfaceHigh :
                               "transparent"
                        Behavior on color { ColorAnimation { duration: Theme.fast } }
                        DragHandler {
                            id: rowDrag
                            target: fileRow
                            onActiveChanged: if (!active) {
                                fileRow.Drag.drop();
                                listing.forceLayout();
                            }
                        }
                        DropArea {
                            anchors.fill: parent
                            enabled: fileRow.modelData.directory
                            keys: ["prism-file"]
                            onDropped: event => {
                                if (event.source && event.source.filePath !== fileRow.filePath) {
                                    root.copyDrop(event.source.filePath, fileRow.filePath);
                                    event.acceptProposedAction();
                                }
                            }
                        }
                        Rectangle {
                            x: 8
                            anchors.verticalCenter: parent.verticalCenter
                            width: 44
                            height: 44
                            radius: 14
                            color: Theme.surfaceHigh
                            Image {
                                anchors.fill: parent
                                anchors.margins: 2
                                source: fileRow.modelData.thumbnail || ""
                                visible: status === Image.Ready && source.toString().length > 0
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                sourceSize.width: 128
                                sourceSize.height: 128
                            }
                            Label {
                                anchors.centerIn: parent
                                visible: !fileRow.modelData.thumbnail
                                text: fileRow.modelData.symbol
                                font.pixelSize: 26
                                color: Theme.primaryStrong
                            }
                        }
                        Label {
                            x: 60; y: 9
                            width: parent.width - 136
                            text: modelData.name
                            elide: Text.ElideRight
                            color: root.selectedPath === modelData.path ?
                                   Theme.onPrimary : Theme.onSurface
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                        Label {
                            x: 60; y: 34
                            width: parent.width - 136
                            text: modelData.directory ? "Folder" : modelData.size
                            color: root.selectedPath === modelData.path ?
                                   Theme.onPrimary : Theme.onSurface
                            opacity: .7
                            font.pixelSize: 12
                        }
                        MouseArea {
                            id: area
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onClicked: mouse => {
                                root.selectedPath = fileRow.modelData.path;
                                if (mouse.button === Qt.RightButton)
                                    itemMenu.popup();
                            }
                            onDoubleClicked: if (!root.busy)
                                root.openItem(fileRow.modelData)
                            onPressAndHold: itemMenu.popup()
                        }
                        PillButton {
                            anchors.right: parent.right
                            anchors.rightMargin: 7
                            anchors.verticalCenter: parent.verticalCenter
                            text: "⋮"
                            implicitWidth: 42
                            implicitHeight: 42
                            Accessible.name: "Actions for " + modelData.name
                            onClicked: itemMenu.popup()
                        }
                        ExpressiveMenu {
                            id: itemMenu
                            MenuItem {
                                text: "Open"
                                onTriggered: root.openItem(fileRow.modelData)
                            }
                            MenuItem {
                                text: "Copy"
                                onTriggered: root.stageItem(fileRow.modelData.path, "copy")
                            }
                            MenuItem {
                                text: "Cut"
                                onTriggered: root.stageItem(fileRow.modelData.path, "cut")
                            }
                            MenuItem {
                                text: "Paste into folder"
                                enabled: fileRow.modelData.directory && root.hasClipboard
                                onTriggered: root.pasteInto(fileRow.modelData.path)
                            }
                            MenuSeparator {}
                            MenuItem {
                                text: "Rename"
                                onTriggered: root.prompt("rename", fileRow.modelData.path,
                                                         fileRow.modelData.name)
                            }
                            MenuSeparator {}
                            MenuItem {
                                text: "Move to Trash"
                                onTriggered: root.prompt("trash", fileRow.modelData.path,
                                                         fileRow.modelData.name)
                            }
                        }
                    }
                    Label {
                        anchors.centerIn: parent
                        visible: listing.count === 0 && !root.busy
                        text: "Nothing here yet"
                    }
                }
            }
        }
        Rectangle {
            anchors.fill: parent
            color: "#781b1425"
            radius: frame.radius
            visible: root.dialogKind.length > 0
            MouseArea { anchors.fill: parent; onClicked: {} }
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(470, parent.width - 32)
                height: root.dialogKind === "trash" ? 220 : 248
                radius: 32
                color: Theme.surface
                Column {
                    anchors.fill: parent
                    anchors.margins: 22
                    spacing: 14
                    Label {
                        text: root.dialogKind === "new" ? "New folder" :
                              root.dialogKind === "rename" ? "Rename item" :
                              "Move to Trash?"
                        font.pixelSize: 24
                        font.weight: Font.Bold
                    }
                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        text: root.dialogKind === "trash" ?
                              "Move " + root.targetName + " to your Trash? You can recover it later." :
                              "Choose a name for this item."
                    }
                    ExpressiveTextField {
                        id: dialogField
                        width: parent.width
                        visible: root.dialogKind !== "trash"
                        placeholderText: "Folder or file name"
                        onAccepted: root.applyPrompt()
                    }
                    Row {
                        spacing: 12
                        PillButton { text: "Cancel"; onClicked: root.dialogKind = "" }
                        PillButton {
                            text: root.dialogKind === "trash" ? "Move to Trash" : "Save"
                            filled: true
                            onClicked: root.applyPrompt()
                        }
                    }
                }
            }
        }
    }
}
