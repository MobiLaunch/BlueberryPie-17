import QtQuick
import QtQuick.Controls.Basic as Basic
import Quickshell.Io
import "../components"
import "../services"

// A scratchpad note kept in ~/.local/share/prismos/notes.txt (through prismctl).
WidgetCard {
    id: root
    property bool loaded: false
    property string status: ""
    property string error: ""
    padding: 14
    implicitWidth: 300
    implicitHeight: 220
    function save() {
        if (!loaded || writer.running)
            return;
        pendingText = field.text;
        writer.running = true;
    }
    property string pendingText: ""
    Component.onCompleted: reader.running = true
    Process {
        id: reader
        command: ["prismctl", "notes", "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok !== false)
                        field.text = data.text;
                    else
                        root.error = data.error;
                } catch (e) {
                    root.error = "Could not read your note";
                }
                root.loaded = true;
            }
        }
    }
    Process {
        id: writer
        command: ["prismctl", "notes", "set"]
        stdinEnabled: true
        onStarted: {
            write(JSON.stringify({
                text: root.pendingText
            }));
            stdinEnabled = false;
        }
        onExited: {
            stdinEnabled = true;
            if (field.text !== root.pendingText)
                saveSoon.restart();
        }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.error = data.ok === false ? data.error : "";
                    root.status = data.ok === false ? "" : "Saved";
                } catch (e) {
                    root.error = "Could not save your note";
                }
            }
        }
    }
    Timer {
        id: saveSoon
        interval: 900
        onTriggered: root.save()
    }
    Column {
        width: parent.width
        spacing: 8
        Row {
            width: parent.width
            spacing: 8
            Symbol {
                anchors.verticalCenter: parent.verticalCenter
                width: 20
                height: 20
                name: "document"
                color: Theme.primary
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 28 - saved.width
                text: "Notes"
                role: "titleSmall"
            }
            Label {
                id: saved
                anchors.verticalCenter: parent.verticalCenter
                text: root.error.length > 0 ? root.error : root.status
                role: "labelSmall"
                color: root.error.length > 0 ? Theme.error : Theme.surfaceVariantInk
            }
        }
        Rectangle {
            width: parent.width
            height: root.implicitHeight - root.padding * 2 - 36
            radius: Theme.shape.large
            color: Theme.surfaceContainerHigh
            clip: true
            Basic.ScrollView {
                anchors.fill: parent
                Basic.TextArea {
                    id: field
                    enabled: root.loaded
                    wrapMode: TextEdit.Wrap
                    placeholderText: "Jot something down…"
                    placeholderTextColor: Theme.outline
                    color: Theme.surfaceInk
                    font.family: Theme.font
                    font.pixelSize: Math.round(14 * Theme.fontScale)
                    selectByMouse: true
                    background: Item {}
                    Accessible.name: "Notes"
                    onTextChanged: if (root.loaded) {
                        root.status = "";
                        saveSoon.restart();
                    }
                }
            }
        }
    }
}
