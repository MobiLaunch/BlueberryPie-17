import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import "../components"
import "../services"

// Linux Flatpak titles and Android F-Droid titles share the same native catalog.
// APK downloads and approvals happen only inside the F-Droid Android client.
PanelWindow {
    id: root
    property bool opened: ShellState.storeOpen && ShellState.activeScreen === screen
    property bool linuxAvailable: false
    property bool linuxConfigured: false
    property var linuxItems: []
    property var androidItems: []
    property string category: "Games"
    property string sourceFilter: "All"
    property string notice: ""
    property string error: ""
    property string linuxOperation: ""
    property bool busy: linuxStatus.running || linuxSearch.running || androidSearch.running ||
                        linuxWriter.running || androidDetails.running
    property var results: sourceFilter === "Linux" ? linuxItems :
                          sourceFilter === "Android" ? androidItems :
                          linuxItems.concat(androidItems)

    anchors { top: true; left: true; right: true; bottom: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-store"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01

    function refresh() {
        error = "";
        notice = "";
        if (!linuxStatus.running) linuxStatus.running = true;
        searchNow();
    }
    function searchNow() {
        error = "";
        const term = searchField.text.trim() || (category === "Games" ? "game" : "app");
        if (linuxConfigured && !linuxSearch.running) {
            linuxSearch.command = ["prismctl", "store", "search", term];
            linuxSearch.running = true;
        }
        if (AndroidState.enabled && !androidSearch.running) {
            androidSearch.command = ["prismctl", "fdroid", "search", term];
            androidSearch.running = true;
        } else if (!AndroidState.enabled) {
            androidItems = [];
        }
    }
    function writeLinux(operation, appid) {
        if (busy) return;
        error = "";
        linuxOperation = operation;
        linuxWriter.command = appid ?
            ["prismctl", "store", operation, appid] :
            ["prismctl", "store", operation];
        linuxWriter.running = true;
    }
    function showAndroid(item) {
        if (!AndroidState.ready || !AndroidState.fdroidInstalled) {
            ShellState.openSettings(screen);
            return;
        }
        if (busy) return;
        error = "";
        androidDetails.command = ["prismctl", "fdroid", "details", item.id];
        androidDetails.running = true;
    }
    function switchCategory(name) {
        category = name;
        searchField.text = name === "Games" ? "game" : "app";
        searchNow();
    }
    onOpenedChanged: if (opened) {
        category = "Games";
        sourceFilter = "All";
        searchField.text = "game";
        refresh();
    }

    Process {
        id: linuxStatus
        command: ["prismctl", "store", "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (state.ok === false) { root.error = state.error; return; }
                    const wasConfigured = root.linuxConfigured;
                    root.linuxAvailable = state.available === true;
                    root.linuxConfigured = state.configured === true;
                    if (!wasConfigured && root.linuxConfigured)
                        startLinux.restart();
                } catch (e) { root.error = "Could not load Linux software sources"; }
            }
        }
    }
    Timer {
        id: startLinux
        interval: 70
        onTriggered: if (!linuxSearch.running && root.linuxConfigured) {
            linuxSearch.command = ["prismctl", "store", "search",
                                   searchField.text.trim() || "game"];
            linuxSearch.running = true;
        }
    }
    Process {
        id: linuxSearch
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (state.ok === false) { root.error = state.error; return; }
                    root.linuxItems = (state.items || []).map(app => ({
                        id: app.id, name: app.name, description: app.description,
                        installed: app.installed === true, kind: "linux",
                        source: "Flathub"
                    }));
                } catch (e) { root.error = "Could not read Flathub listings"; }
            }
        }
    }
    Process {
        id: androidSearch
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (state.ok === false) { root.error = state.error; return; }
                    root.androidItems = state.items || [];
                } catch (e) { root.error = "Could not read F-Droid listings"; }
            }
        }
    }
    Process {
        id: linuxWriter
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (state.ok === false) { root.error = state.error; return; }
                    root.notice = root.linuxOperation === "enable" ? "Flathub is connected" :
                                  root.linuxOperation === "install" ? "Application installed" :
                                  root.linuxOperation === "remove" ? "Application removed" :
                                  "Opening application";
                } catch (e) { root.error = "Software operation failed"; }
            }
        }
        onExited: {
            SystemBridge.refreshApps();
            refreshAfterWrite.restart();
        }
    }
    Timer {
        id: refreshAfterWrite
        interval: 100
        onTriggered: root.refresh()
    }
    Process {
        id: androidDetails
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const state = JSON.parse(text);
                    if (state.ok === false) { root.error = state.error; return; }
                    root.notice = "Continue in F-Droid to review and install";
                } catch (e) { root.error = "Could not open the F-Droid listing"; }
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.withAlpha(Theme.scrim, 0.45)
        opacity: root.opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }
    MouseArea { anchors.fill: parent; onClicked: ShellState.close() }
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(1020, root.width - 32)
        height: Math.min(800, root.height - 52)
        radius: Theme.shape.extraExtraLarge - 8
        color: Theme.surface
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .95
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
        Behavior on scale { NumberAnimation { duration: Theme.standard; easing.type: Easing.OutBack } }
        MouseArea { anchors.fill: parent; onClicked: {} }
        Row {
            x: 28; y: 22
            spacing: 12
            Symbol {
                anchors.verticalCenter: parent.verticalCenter
                width: 30; height: 30
                name: "store"
                color: Theme.primary
            }
            Column {
                Label { text: "Prism Store"; role: "headlineMedium" }
                Label {
                    text: "Linux and Android, all in one place"
                    role: "bodyMedium"
                    color: Theme.surfaceVariantInk
                }
            }
        }
        IconButton {
            anchors.top: parent.top; anchors.right: parent.right; anchors.margins: 18
            symbol: "close"
            variant: "tonal"
            Accessible.name: "Close Prism Store"
            onClicked: ShellState.close()
        }
        Row {
            x: 28; y: 96; spacing: 8
            Repeater {
                model: ["Games", "Apps"]
                delegate: FilterChip {
                    required property string modelData
                    text: modelData
                    selected: root.category === modelData
                    onClicked: root.switchCategory(modelData)
                }
            }
        }
        SearchField {
            id: searchField
            x: 26; y: 146
            width: parent.width - 52
            placeholderText: "Find Linux and Android games or apps"
            onAccepted: root.searchNow()
            onEscaped: ShellState.close()
        }
        Row {
            x: 28; y: 214; spacing: 8
            Repeater {
                model: ["All", "Linux", "Android"]
                delegate: FilterChip {
                    required property string modelData
                    text: modelData
                    selected: root.sourceFilter === modelData
                    onClicked: root.sourceFilter = modelData
                }
            }
        }
        Row {
            x: 28; y: 268; spacing: 12
            visible: root.busy
            ExpressiveLoader { width: 26; height: 26 }
            Label { text: "Finding your next favorite…"; role: "bodyMedium"; color: Theme.surfaceVariantInk }
        }
        Label {
            x: 28; y: 270; width: parent.width - 56
            visible: !root.busy && (root.error.length > 0 || root.notice.length > 0)
            color: root.error.length ? Theme.error : Theme.primary
            text: root.error.length ? root.error : root.notice
            role: "bodyMedium"
            elide: Text.ElideRight
        }
        ListView {
            id: results
            x: 26; y: 304
            width: parent.width - 52
            height: Math.max(90, parent.height - 330)
            clip: true
            spacing: 8
            model: root.results
            ScrollBar.vertical: ScrollBar {}
            delegate: Rectangle {
                id: resultRow
                required property var modelData
                width: results.width
                height: 100
                radius: Theme.shape.extraLarge - 4
                color: Theme.surfaceContainer
                Rectangle {
                    x: 14
                    anchors.verticalCenter: parent.verticalCenter
                    width: 68; height: 68; radius: 22
                    color: resultRow.modelData.kind === "android" ? Theme.secondaryContainer : Theme.primaryContainer
                    Symbol {
                        anchors.centerIn: parent
                        width: 32; height: 32
                        name: resultRow.modelData.kind === "android" ? "android" : "store"
                        color: resultRow.modelData.kind === "android" ? Theme.secondaryContainerInk : Theme.primaryContainerInk
                    }
                }
                Label {
                    x: 96; y: 12
                    width: Math.max(80, parent.width - 250)
                    text: resultRow.modelData.name
                    role: "titleMedium"
                    elide: Text.ElideRight
                }
                Label {
                    x: 96; y: 38
                    width: Math.max(80, parent.width - 250)
                    text: resultRow.modelData.source + " · " +
                          (resultRow.modelData.kind === "android" ? "Android" : "Linux")
                    role: "labelMedium"
                    color: Theme.primary
                    elide: Text.ElideRight
                }
                Label {
                    x: 96; y: 58
                    width: Math.max(80, parent.width - 250)
                    text: resultRow.modelData.description || "Open-source software"
                    maximumLineCount: 2
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    role: "bodySmall"
                    color: Theme.surfaceVariantInk
                }
                PillButton {
                    anchors.right: parent.right; anchors.rightMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    variant: "filled"
                    enabled: !root.busy
                    text: resultRow.modelData.kind === "android" ?
                          (AndroidState.ready && AndroidState.fdroidInstalled ?
                            "View in F-Droid" : "Set up") :
                          (resultRow.modelData.installed ? "Open" : "Install")
                    onClicked: {
                        if (resultRow.modelData.kind === "android")
                            root.showAndroid(resultRow.modelData);
                        else
                            root.writeLinux(resultRow.modelData.installed ? "open" : "install",
                                            resultRow.modelData.id);
                    }
                }
            }
            Label {
                anchors.centerIn: parent
                width: Math.min(parent.width - 40, 340)
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                visible: results.count === 0 && !root.busy
                role: "bodyLarge"
                color: Theme.surfaceVariantInk
                text: root.sourceFilter === "Android" && !AndroidState.enabled ?
                      "Enable Android apps in Settings to browse F-Droid." :
                      root.sourceFilter === "Linux" && !root.linuxConfigured ?
                      "Connect Flathub to explore Linux apps and games." :
                      "No matches yet. Try another search."
            }
        }
        Row {
            x: 28
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            spacing: 8
            visible: !root.linuxConfigured || !AndroidState.enabled
            PillButton {
                text: root.linuxAvailable ? "Connect Flathub" : "Flatpak unavailable"
                visible: !root.linuxConfigured
                variant: "tonal"
                enabled: root.linuxAvailable && !root.busy
                implicitHeight: 40
                onClicked: root.writeLinux("enable", "")
            }
            PillButton {
                text: "Set up Android in Settings"
                visible: !AndroidState.enabled
                variant: "tonal"
                implicitHeight: 40
                onClicked: ShellState.openSettings(root.screen, "apps")
            }
        }
    }
}
