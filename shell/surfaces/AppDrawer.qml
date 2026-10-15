import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"
import "../services/AppSearch.js" as AppSearch

// App launcher: search-first, category chips, recents and an alphabetical grid.
PanelWindow {
    id: root
    property bool opened: ShellState.drawerOpen && ShellState.activeScreen === screen
    property string category: "All"
    readonly property var chips: AppSearch.categories(SystemBridge.apps)
    readonly property var results: AppSearch.rank(SystemBridge.apps, search.text, category)
    readonly property var recent: AppSearch.recents(SystemBridge.apps, SystemBridge.snapshot.settings.recent_apps, 6)
    readonly property bool browsing: search.text.length === 0 && category === "All"
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
        search.text = ShellState.launcherQuery;
        ShellState.launcherQuery = "";
        category = "All";
        search.focusField();
    }
    function launchApp(app, x, y) {
        ShellState.launch(app, root.screen, x, y);
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.42)
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
        width: Math.min(1040, root.width - 48)
        height: Math.min(780, root.height - 112)
        color: Theme.surfaceContainerLow
        radius: Theme.shape.extraExtraLarge
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .94
        transform: Translate {
            y: root.opened ? 0 : 48
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
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                SearchField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: "Search apps"
                    onEscaped: ShellState.close()
                    onDownPressed: grid.forceActiveFocus()
                    onAccepted: {
                        if (root.results.length)
                            root.launchApp(root.results[0], root.width / 2, root.height / 2);
                    }
                }
                IconButton {
                    symbol: "close"
                    variant: "tonal"
                    Accessible.name: "Close app launcher"
                    onClicked: ShellState.close()
                }
            }
            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: 44
                contentWidth: chipRow.implicitWidth
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Row {
                    id: chipRow
                    spacing: 8
                    anchors.verticalCenter: parent.verticalCenter
                    Repeater {
                        model: root.chips
                        delegate: FilterChip {
                            required property string modelData
                            text: modelData
                            selected: root.category === modelData
                            onClicked: root.category = modelData
                        }
                    }
                }
            }
            GridView {
                id: grid
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                readonly property int columns: Math.max(3, Math.floor(width / 128))
                cellWidth: width / columns
                cellHeight: 118
                model: root.results
                boundsBehavior: Flickable.StopAtBounds
                keyNavigationEnabled: true
                focus: false
                ScrollBar.vertical: ScrollBar {}
                header: Column {
                    width: grid.width
                    spacing: 6
                    visible: root.browsing && root.recent.length > 0
                    height: visible ? implicitHeight : 0
                    Label {
                        text: "Recent"
                        role: "titleSmall"
                        color: Theme.surfaceVariantInk
                        leftPadding: 8
                        topPadding: 2
                    }
                    Row {
                        Repeater {
                            model: root.recent
                            delegate: AppTile {
                                required property var modelData
                                width: grid.cellWidth
                                height: grid.cellHeight
                                app: modelData
                                onLaunched: (x, y) => root.launchApp(modelData, x, y)
                            }
                        }
                    }
                    Label {
                        text: "All apps"
                        role: "titleSmall"
                        color: Theme.surfaceVariantInk
                        leftPadding: 8
                        topPadding: 6
                    }
                }
                delegate: AppTile {
                    required property var modelData
                    width: grid.cellWidth
                    height: grid.cellHeight
                    app: modelData
                    onLaunched: (x, y) => root.launchApp(modelData, x, y)
                }
                Keys.onEscapePressed: ShellState.close()
                Keys.onUpPressed: event => {
                    if (grid.currentIndex < grid.columns)
                        search.focusField();
                    else
                        event.accepted = false;
                }
                Column {
                    anchors.centerIn: parent
                    spacing: 10
                    visible: grid.count === 0
                    Symbol {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 40
                        height: 40
                        name: "search"
                        color: Theme.surfaceVariantInk
                    }
                    Label {
                        text: SystemBridge.apps.length ? "No apps match your search" : "No desktop applications found"
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    text: root.results.length + (root.results.length === 1 ? " app" : " apps")
                    role: "labelMedium"
                    color: Theme.surfaceVariantInk
                }
                PillButton {
                    visible: search.text.trim().length > 0
                    text: "Search the web for \u201c" + search.text.trim() + "\u201d"
                    symbol: "browser"
                    variant: "filled"
                    onClicked: {
                        SystemBridge.webSearch(search.text.trim());
                        ShellState.close();
                    }
                }
                PillButton {
                    text: "Get more apps"
                    symbol: "store"
                    variant: "tonal"
                    onClicked: ShellState.openStore(root.screen)
                }
            }
        }
    }
}
