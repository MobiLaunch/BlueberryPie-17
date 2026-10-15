import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

// Clipboard history. It is off until you turn it on; click an entry to copy it again.
ColumnLayout {
    id: root
    spacing: 10
    readonly property var shown: {
        const needle = search.text.trim().toLowerCase();
        return needle.length === 0 ? ClipboardState.items : ClipboardState.items.filter(item => item.preview.toLowerCase().includes(needle));
    }
    function load() {
        ClipboardState.refresh();
    }
    SettingsGroup {
        Layout.fillWidth: true
        ToggleRow {
            width: parent.width
            title: "Keep clipboard history"
            supporting: !ClipboardState.available ? "Needs cliphist and wl-clipboard" : ClipboardState.enabled ? "Saving what you copy" : "Off, nothing is saved"
            symbol: "document"
            enabled: ClipboardState.available
            on: ClipboardState.enabled
            onSwitched: value => ClipboardState.setEnabled(value)
        }
    }
    Label {
        Layout.fillWidth: true
        visible: !ClipboardState.enabled && ClipboardState.available
        text: "Copied text and images stay on this computer until you clear them. Passwords you copy are saved too, so turn this on only if you want that. Pinned snippets are kept until you unpin them."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
    SettingsGroup {
        Layout.fillWidth: true
        visible: ClipboardState.pins.length > 0
        title: "Pinned"
        Repeater {
            model: ClipboardState.pins
            delegate: ListRow {
                required property var modelData
                width: parent ? parent.width : 400
                implicitHeight: 48
                title: modelData.preview
                symbol: "pin"
                chipColor: Theme.primaryContainer
                chipInk: Theme.primaryContainerInk
                Accessible.name: "Copy pinned: " + modelData.preview
                onClicked: ClipboardState.copyPin(modelData.id)
                IconButton {
                    symbol: "close"
                    implicitWidth: 36
                    implicitHeight: 36
                    iconSize: 18
                    Accessible.name: "Unpin"
                    onClicked: ClipboardState.unpin(modelData.id)
                }
            }
        }
    }
    SearchField {
        id: search
        Layout.fillWidth: true
        implicitHeight: 44
        visible: ClipboardState.enabled
        placeholderText: "Search history"
    }
    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 4
        visible: ClipboardState.enabled
        model: root.shown
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {
            policy: ScrollBar.AsNeeded
        }
        delegate: ListRow {
            required property var modelData
            width: ListView.view.width
            implicitHeight: 52
            title: modelData.preview
            symbol: modelData.kind === "image" ? "photo" : "document"
            Accessible.name: "Copy: " + modelData.preview
            onClicked: ClipboardState.copy(modelData.id)
            RowLayout {
                spacing: 0
                IconButton {
                    visible: modelData.kind === "text"
                    symbol: "pin"
                    implicitWidth: 36
                    implicitHeight: 36
                    iconSize: 18
                    Accessible.name: "Pin"
                    onClicked: ClipboardState.pin(modelData.id)
                }
                IconButton {
                    symbol: "close"
                    implicitWidth: 36
                    implicitHeight: 36
                    iconSize: 18
                    Accessible.name: "Remove from history"
                    onClicked: ClipboardState.remove(modelData.id)
                }
            }
        }
        Label {
            anchors.centerIn: parent
            visible: parent.count === 0
            text: ClipboardState.items.length === 0 ? "Nothing copied yet" : "No matches"
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
    }
    Label {
        Layout.fillWidth: true
        visible: ClipboardState.error.length > 0
        text: ClipboardState.error
        role: "bodySmall"
        color: Theme.error
        wrapMode: Text.WordWrap
    }
    PillButton {
        visible: ClipboardState.enabled
        text: "Clear history"
        variant: "tonal"
        enabled: ClipboardState.items.length > 0
        onClicked: ClipboardState.clear()
    }
    Item {
        Layout.fillHeight: !ClipboardState.enabled
    }
}
