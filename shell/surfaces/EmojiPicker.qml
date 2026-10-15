import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"
import "../services/EmojiData.js" as EmojiData
import "../services/EmojiSearch.js" as EmojiSearch

// Emoji picker (Super + .). Search or browse by group; choosing one copies it to the
// clipboard, because a Wayland shell cannot type into another app. Recently used first.
PanelWindow {
    id: root
    property bool opened: ShellState.emojiOpen && ShellState.activeScreen === screen
    // -1 is "recent" (when there are any) or everything; 0.. are the groups.
    property int group: EmojiState.recents.length > 0 ? -2 : 0
    property string hovered: ""
    readonly property string query: search.text.trim()
    readonly property var results: {
        if (query === "" && group === -2)
            return EmojiState.recents;
        return EmojiSearch.search(EmojiData.entries, query, query === "" ? Math.max(group, 0) : -1);
    }
    readonly property var chips: {
        const list = [];
        if (EmojiState.recents.length > 0)
            list.push({
                id: -2,
                glyph: "🕘",
                name: "Recent"
            });
        for (let i = 0; i < EmojiData.groups.length; i++) {
            const first = EmojiData.entries.find(entry => entry[3] === i);
            list.push({
                id: i,
                glyph: first ? first[0] : "",
                name: EmojiData.groups[i]
            });
        }
        return list;
    }
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-emoji"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened
    onOpenedChanged: {
        if (opened) {
            search.text = "";
            hovered = "";
            group = EmojiState.recents.length > 0 ? -2 : 0;
            search.focusField();
        }
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.4)
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        objectName: "emoji-card"
        anchors.centerIn: parent
        width: Math.min(480, root.width - 32)
        height: Math.min(560, root.height - 64)
        color: Theme.surfaceContainerHigh
        radius: Theme.shape.extraLargeIncreased + 4
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12
            SearchField {
                id: search
                objectName: "emoji-search"
                Layout.fillWidth: true
                placeholderText: "Search emoji"
                onAccepted: if (root.results.length > 0)
                    EmojiState.copy(root.results[0][0])
                onEscaped: ShellState.close()
            }
            Row {
                Layout.alignment: Qt.AlignHCenter
                spacing: 4
                visible: root.query === ""
                Repeater {
                    model: root.chips
                    delegate: Rectangle {
                        required property var modelData
                        objectName: "emoji-group-" + modelData.id
                        width: 44
                        height: 40
                        radius: 20
                        color: root.group === modelData.id ? Theme.secondaryContainer : "transparent"
                        Text {
                            anchors.centerIn: parent
                            text: modelData.glyph
                            font.pixelSize: 22
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            Accessible.role: Accessible.Button
                            Accessible.name: modelData.name
                            onClicked: root.group = modelData.id
                        }
                    }
                }
            }
            GridView {
                id: grid
                objectName: "emoji-grid"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 48)))
                cellHeight: 48
                model: root.results
                boundsBehavior: Flickable.StopAtBounds
                delegate: Item {
                    required property var modelData
                    objectName: "emoji-cell"
                    width: grid.cellWidth
                    height: grid.cellHeight
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 2
                        radius: 14
                        color: area.containsMouse ? Theme.secondaryContainer : "transparent"
                    }
                    Text {
                        anchors.centerIn: parent
                        text: modelData[0]
                        font.pixelSize: 28
                    }
                    MouseArea {
                        id: area
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData[1]
                        onEntered: root.hovered = modelData[1]
                        onClicked: EmojiState.copy(modelData[0])
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: root.results.length === 0
                    text: root.query !== "" ? "No emoji match “" + root.query + "”" : "Nothing here yet"
                    role: "bodyLarge"
                    color: Theme.surfaceVariantInk
                }
            }
            Label {
                objectName: "emoji-hint"
                Layout.fillWidth: true
                text: root.hovered !== "" ? root.hovered : "Choose one to copy it · Enter copies the first match"
                role: "labelLarge"
                color: Theme.surfaceVariantInk
                elide: Text.ElideRight
            }
        }
    }
}
