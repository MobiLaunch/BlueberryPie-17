import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Where an app came from, whether it is running, and the two safe actions:
// force stop, and removal of apps installed for this user. System packages are
// never removed from here; the remove command is shown to copy instead.
PanelWindow {
    id: root
    property bool opened: ShellState.appInfoOpen && ShellState.activeScreen === screen
    property bool confirming: false
    readonly property var details: AppInfoState.details
    readonly property var rows: {
        const d = details;
        const list = [];
        list.push({
            title: "Status",
            note: d.running ? "Running, " + d.windows + (d.windows === 1 ? " window" : " windows") : "Not running",
            symbol: "info"
        });
        if (d.source === "flatpak")
            list.push({
                title: "Installed from",
                note: "Flatpak" + (d.origin ? " (" + d.origin + ")" : ""),
                symbol: "apps"
            });
        else if (d.source === "pacman")
            list.push({
                title: "Installed from",
                note: "System package " + d.package,
                symbol: "apps"
            });
        else
            list.push({
                title: "Installed from",
                note: "Unknown source",
                symbol: "apps"
            });
        if (d.version)
            list.push({
                title: "Version",
                note: d.version,
                symbol: "info"
            });
        if (d.size)
            list.push({
                title: "Size",
                note: d.size,
                symbol: "storage"
            });
        return list;
    }
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-appinfo"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened
    onOpenedChanged: {
        confirming = false;
        if (opened)
            card.forceActiveFocus();
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.5)
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        objectName: "appinfo-card"
        anchors.centerIn: parent
        width: Math.min(460, root.width - 32)
        height: Math.min(content.implicitHeight + 56, root.height - 64)
        color: Theme.surfaceContainerHigh
        radius: Theme.shape.extraLargeIncreased + 4
        focus: true
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        Keys.onEscapePressed: {
            if (root.confirming)
                root.confirming = false;
            else
                ShellState.close();
        }
        ColumnLayout {
            id: content
            anchors.fill: parent
            anchors.margins: 24
            spacing: 12
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                AppIcon {
                    Layout.preferredWidth: 56
                    Layout.preferredHeight: 56
                    icon: AppInfoState.app ? AppInfoState.app.icon : ""
                    label: AppInfoState.app ? AppInfoState.app.name : ""
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        objectName: "appinfo-name"
                        Layout.fillWidth: true
                        text: AppInfoState.app ? AppInfoState.app.name : ""
                        role: "headlineSmall"
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: text.length > 0
                        text: root.details.description || ""
                        role: "bodyMedium"
                        color: Theme.surfaceVariantInk
                        elide: Text.ElideRight
                    }
                }
            }
            Label {
                objectName: "appinfo-status"
                Layout.fillWidth: true
                visible: text.length > 0
                text: AppInfoState.error || AppInfoState.notice
                role: "bodyMedium"
                color: AppInfoState.error ? Theme.error : Theme.primary
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.confirming && !AppInfoState.gone
                text: "Remove " + (AppInfoState.app ? AppInfoState.app.name : "this app") + " and its program files? Your documents are not touched."
                role: "bodyMedium"
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: root.confirming || !AppInfoState.loaded || AppInfoState.gone ? [] : root.rows
                delegate: ListRow {
                    required property var modelData
                    required property int index
                    objectName: "appinfo-row-" + index
                    Layout.fillWidth: true
                    title: modelData.title
                    supporting: modelData.note
                    symbol: modelData.symbol
                    interactive: false
                    shapePosition: index === 0 ? "top" : index === root.rows.length - 1 ? "bottom" : "middle"
                }
            }
            Label {
                objectName: "appinfo-command"
                Layout.fillWidth: true
                visible: !!root.details.remove_command && !root.confirming && !AppInfoState.gone
                text: "To remove it, run in a terminal:\n" + (root.details.remove_command || "")
                role: "bodySmall"
                color: Theme.surfaceVariantInk
                wrapMode: Text.WrapAnywhere
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                visible: !root.confirming && !AppInfoState.gone
                PillButton {
                    objectName: "appinfo-force-stop"
                    Layout.fillWidth: true
                    text: "Force stop"
                    symbol: "stop"
                    variant: "tonal"
                    enabled: !!root.details.running && !AppInfoState.busy
                    onClicked: AppInfoState.forceStop()
                }
                PillButton {
                    objectName: "appinfo-copy"
                    Layout.fillWidth: true
                    visible: !!root.details.remove_command
                    text: "Copy command"
                    symbol: "copy"
                    variant: "tonal"
                    enabled: !AppInfoState.busy
                    onClicked: AppInfoState.copyRemoveCommand()
                }
                PillButton {
                    objectName: "appinfo-uninstall"
                    Layout.fillWidth: true
                    visible: !!root.details.removable
                    text: "Uninstall"
                    symbol: "trash"
                    variant: "tonal"
                    enabled: !AppInfoState.busy
                    onClicked: root.confirming = true
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                PillButton {
                    objectName: "appinfo-cancel"
                    Layout.fillWidth: true
                    text: root.confirming ? "Cancel" : "Close"
                    variant: root.confirming ? "tonal" : "text"
                    onClicked: {
                        if (root.confirming)
                            root.confirming = false;
                        else
                            ShellState.close();
                    }
                }
                PillButton {
                    objectName: "appinfo-confirm"
                    Layout.fillWidth: true
                    visible: root.confirming && !AppInfoState.gone
                    text: AppInfoState.acting === "uninstall" ? "Removing…" : "Uninstall"
                    variant: "filled"
                    enabled: !AppInfoState.busy
                    onClicked: {
                        root.confirming = false;
                        AppInfoState.uninstall();
                    }
                }
            }
        }
    }
}
