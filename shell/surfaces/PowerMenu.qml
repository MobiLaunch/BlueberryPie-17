import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Session actions. Every action asks for confirmation; unavailable ones say why.
PanelWindow {
    id: root
    property bool opened: ShellState.powerOpen && ShellState.activeScreen === screen
    property string confirming: ""
    readonly property var actions: [
        {
            id: "lock",
            title: "Lock",
            note: "Require your password to continue",
            symbol: "lock",
            warn: false
        },
        {
            id: "suspend",
            title: "Sleep",
            note: "Pause and save power",
            symbol: "sleep",
            warn: false
        },
        {
            id: "logout",
            title: "Sign out",
            note: "Close apps and end this session",
            symbol: "logout",
            warn: true
        },
        {
            id: "restart",
            title: "Restart",
            note: "Close everything and start again",
            symbol: "restart",
            warn: true
        },
        {
            id: "shutdown",
            title: "Power off",
            note: "Close everything and turn off",
            symbol: "power",
            warn: true
        }
    ]
    readonly property var pending: actions.find(item => item.id === confirming) || null
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
        color: Theme.withAlpha(Theme.scrim, 0.5)
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(440, root.width - 32)
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
                root.confirming = "";
            else
                ShellState.close();
        }
        ColumnLayout {
            id: content
            anchors.fill: parent
            anchors.margins: 24
            spacing: 14
            Rectangle {
                visible: !!root.confirming
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 64
                Layout.preferredHeight: 64
                radius: 32
                color: root.pending && root.pending.warn ? Theme.errorContainer : Theme.primaryContainer
                Symbol {
                    anchors.centerIn: parent
                    width: 30
                    height: 30
                    name: root.pending ? root.pending.symbol : "power"
                    color: root.pending && root.pending.warn ? Theme.errorContainerInk : Theme.primaryContainerInk
                }
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: root.confirming ? Text.AlignHCenter : Text.AlignLeft
                text: root.pending ? root.pending.title + "?" : "Power options"
                role: "headlineSmall"
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: root.confirming ? Text.AlignHCenter : Text.AlignLeft
                visible: !!root.confirming
                text: root.pending && root.pending.warn ? "Save your work first. Unsaved changes in open apps may be lost." : "You can unlock again any time."
                role: "bodyMedium"
                color: Theme.surfaceVariantInk
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: root.confirming ? [] : root.actions
                delegate: ListRow {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    title: modelData.title
                    supporting: SystemBridge.snapshot.power[modelData.id] ? modelData.note : "Not available in this session"
                    symbol: modelData.symbol
                    shapePosition: index === 0 ? "top" : index === 4 ? "bottom" : "middle"
                    chipColor: modelData.warn ? Theme.errorContainer : Theme.primaryContainer
                    chipInk: modelData.warn ? Theme.errorContainerInk : Theme.primaryContainerInk
                    enabled: !!SystemBridge.snapshot.power[modelData.id] && !SystemBridge.busy
                    onClicked: root.confirming = modelData.id
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                PillButton {
                    Layout.fillWidth: true
                    text: "Cancel"
                    variant: root.confirming ? "tonal" : "text"
                    onClicked: {
                        if (root.confirming)
                            root.confirming = "";
                        else
                            ShellState.close();
                    }
                }
                PillButton {
                    Layout.fillWidth: true
                    visible: !!root.confirming
                    text: root.pending ? root.pending.title : ""
                    variant: "filled"
                    enabled: !SystemBridge.busy
                    onClicked: {
                        const action = root.confirming;
                        ShellState.close();
                        SystemBridge.action(action);
                    }
                }
            }
        }
    }
}
