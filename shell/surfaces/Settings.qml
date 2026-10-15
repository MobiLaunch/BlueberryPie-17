import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Settings: a searchable section list beside the selected page. On narrow
// screens it shows one pane at a time with a back button.
PanelWindow {
    id: root
    property bool opened: ShellState.settingsOpen && ShellState.activeScreen === screen
    property string current: ""
    readonly property bool compact: card.width < 760
    readonly property var snap: SystemBridge.snapshot
    readonly property var sections: [
        {
            id: "network",
            title: "Network & internet",
            symbol: "wifi",
            page: "NetworkPage",
            keywords: "wifi wi-fi wireless internet ethernet vpn connection"
        },
        {
            id: "bluetooth",
            title: "Bluetooth & devices",
            symbol: "bluetooth",
            page: "BluetoothPage",
            keywords: "bluetooth pair headphones devices"
        },
        {
            id: "display",
            title: "Display",
            symbol: "display",
            page: "DisplayPage",
            keywords: "screen monitor brightness scale resolution arrangement"
        },
        {
            id: "sound",
            title: "Sound",
            symbol: "volume",
            page: "SoundPage",
            keywords: "volume audio speaker microphone output input mute"
        },
        {
            id: "notifications",
            title: "Notifications",
            symbol: "notifications",
            page: "NotificationsPage",
            keywords: "notifications do not disturb dnd alerts"
        },
        {
            id: "style",
            title: "Wallpaper & style",
            symbol: "palette",
            page: "StylePage",
            keywords: "color palette theme dark light accent motion appearance"
        },
        {
            id: "input",
            title: "Pointer & keyboard",
            symbol: "keyboard",
            page: "InputPage",
            keywords: "mouse touchpad scrolling tap keyboard repeat pointer"
        },
        {
            id: "shortcuts",
            title: "Shortcuts & gestures",
            symbol: "keyboard",
            page: "ShortcutsPage",
            keywords: "shortcuts keys keyboard gestures touchpad swipe bindings hotkeys"
        },
        {
            id: "apps",
            title: "Apps",
            symbol: "apps_grid",
            page: "AppsPage",
            keywords: "apps android waydroid f-droid store installed"
        },
        {
            id: "power",
            title: "Battery & power",
            symbol: "battery",
            page: "PowerPage",
            keywords: "battery power lock sleep restart shut down"
        },
        {
            id: "about",
            title: "About",
            symbol: "info",
            page: "AboutPage",
            keywords: "about version kernel system memory storage device name"
        }
    ]
    readonly property var visibleSections: {
        const query = search.text.trim().toLowerCase();
        return query ? sections.filter(section => (section.title + " " + section.keywords).toLowerCase().includes(query)) : sections;
    }
    readonly property var currentSection: sections.find(section => section.id === current) || null
    function summary(id) {
        switch (id) {
        case "network":
            return snap.wifi.available ? (snap.wifi.enabled ? snap.wifi.label : "Wi-Fi off") : "No adapter";
        case "bluetooth":
            return snap.bluetooth.available ? (snap.bluetooth.enabled ? "On" : "Off") : "No adapter";
        case "display":
            return snap.brightness.available ? "Brightness " + snap.brightness.value + "%" : "Scale and arrangement";
        case "sound":
            return !snap.volume.available ? "No output" : snap.volume.muted ? "Muted" : "Volume " + snap.volume.value + "%";
        case "notifications":
            return snap.settings.dnd ? "Do Not Disturb is on" : Notifications.count + " now";
        case "style":
            return (Theme.dark ? "Dark" : "Light") + " theme";
        case "input":
            return "Touchpad, speed, repeat";
        case "shortcuts":
            return "Keys and touchpad gestures";
        case "apps":
            return SystemBridge.apps.length + " installed";
        case "power":
            return snap.battery.available ? snap.battery.value + "%" + (snap.battery.charging ? " · Charging" : "") : "Plugged in";
        default:
            return "PrismOS " + (AboutState.info.prismos || "");
        }
    }
    function select(id) {
        current = id;
        ShellState.settingsPage = id;
    }
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-settings"
    WlrLayershell.keyboardFocus: opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"
    visible: opened || card.opacity > .01
    onOpenedChanged: if (opened) {
        search.text = "";
        const wanted = ShellState.settingsPage;
        current = sections.some(section => section.id === wanted) ? wanted : (compact ? "" : "network");
        card.forceActiveFocus();
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
        width: Math.min(1060, root.width - 40)
        height: Math.min(720, root.height - 96)
        radius: Theme.shape.extraExtraLarge - 8
        color: Theme.surface
        clip: true
        opacity: root.opened ? 1 : 0
        scale: root.opened ? 1 : .95
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
            }
        }
        focus: root.opened
        Keys.onEscapePressed: {
            if (root.compact && root.current)
                root.current = "";
            else
                ShellState.close();
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }
        // Section list
        Item {
            id: listPane
            visible: !root.compact || root.current === ""
            width: root.compact ? parent.width : 330
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Settings"
                        role: "headlineMedium"
                        Layout.fillWidth: true
                        Layout.leftMargin: 8
                    }
                    IconButton {
                        visible: root.compact
                        symbol: "close"
                        variant: "tonal"
                        Accessible.name: "Close Settings"
                        onClicked: ShellState.close()
                    }
                }
                SearchField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: "Search settings"
                    onEscaped: {
                        if (text.length)
                            text = "";
                        else
                            ShellState.close();
                    }
                    onDownPressed: sectionList.forceActiveFocus()
                    onAccepted: if (root.visibleSections.length)
                        root.select(root.visibleSections[0].id)
                }
                ListView {
                    id: sectionList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: root.visibleSections
                    keyNavigationEnabled: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    delegate: ListRow {
                        id: row
                        required property var modelData
                        required property int index
                        objectName: "section-" + modelData.id
                        width: sectionList.width
                        implicitHeight: 64
                        title: modelData.title
                        supporting: root.summary(modelData.id)
                        symbol: modelData.symbol
                        selected: !root.compact && root.current === modelData.id
                        shapePosition: "single"
                        chipColor: index % 3 === 0 ? Theme.primaryContainer : index % 3 === 1 ? Theme.secondaryContainer : Theme.tertiaryContainer
                        chipInk: index % 3 === 0 ? Theme.primaryContainerInk : index % 3 === 1 ? Theme.secondaryContainerInk : Theme.tertiaryContainerInk
                        onClicked: root.select(modelData.id)
                        Keys.onReturnPressed: root.select(modelData.id)
                    }
                    Label {
                        anchors.centerIn: parent
                        visible: sectionList.count === 0
                        text: "No settings match"
                        role: "bodyLarge"
                        color: Theme.surfaceVariantInk
                    }
                }
            }
        }
        // Selected page
        Rectangle {
            visible: !root.compact || root.current !== ""
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.left: root.compact ? parent.left : listPane.right
            anchors.margins: root.compact ? 0 : 10
            anchors.leftMargin: root.compact ? 0 : 0
            radius: root.compact ? 0 : Theme.shape.extraExtraLarge - 12
            color: Theme.surfaceContainerLow
            Item {
                anchors.fill: parent
                anchors.margins: 22
                RowLayout {
                    id: pageHeader
                    width: parent.width
                    height: 56
                    spacing: 8
                    IconButton {
                        visible: root.compact
                        symbol: "back"
                        variant: "tonal"
                        Accessible.name: "Back to all settings"
                        onClicked: root.current = ""
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.currentSection ? root.currentSection.title : ""
                        role: "headlineMedium"
                        elide: Text.ElideRight
                    }
                    IconButton {
                        visible: !root.compact
                        symbol: "close"
                        variant: "tonal"
                        Accessible.name: "Close Settings"
                        onClicked: ShellState.close()
                    }
                }
                Loader {
                    id: pageLoader
                    anchors.top: pageHeader.bottom
                    anchors.topMargin: 8
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    active: root.opened && root.currentSection !== null
                    source: root.currentSection ? "settings/" + root.currentSection.page + ".qml" : ""
                    onStatusChanged: if (status === Loader.Error)
                        ShellState.toast = "Could not load this Settings page"
                }
            }
        }
    }
}
