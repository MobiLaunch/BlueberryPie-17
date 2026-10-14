import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Background layer: artwork, home clock, desktop menu and wallpaper-only swipes.
PanelWindow {
    id: root
    property string timeText: Qt.formatTime(new Date(), "hh:mm")
    property string dateText: Qt.formatDate(new Date(), "dddd, MMMM d")
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Background
    WlrLayershell.namespace: "prism-wallpaper"
    color: Theme.dark ? "#211b2d" : "#e8dff4"
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            root.timeText = Qt.formatTime(new Date(), "hh:mm");
            root.dateText = Qt.formatDate(new Date(), "dddd, MMMM d");
        }
    }
    Image {
        anchors.fill: parent
        source: Quickshell.shellPath("../design/wallpaper.svg")
        fillMode: Image.PreserveAspectCrop
        opacity: Theme.dark ? .5 : 1
    }
    // Touchscreen gesture zone on *empty wallpaper* only. This does not
    // steal swipes from regular app windows, app toolbars or Quick Settings.
    Item {
        anchors.fill: parent
        DragHandler {
            target: null
            acceptedDevices: PointerDevice.TouchScreen
            onActiveChanged: {
                if (active)
                    return;
                const dy = activeTranslation.y;
                const dx = activeTranslation.x;
                const beganAt = centroid.pressPosition.y;
                if (Math.abs(dy) < 105 || Math.abs(dx) > Math.abs(dy) * .6)
                    return;
                if (dy < 0 && beganAt > root.height * .65)
                    ShellState.toggleDrawer(root.screen);
                else if (dy > 0 && beganAt < root.height * .35)
                    ShellState.toggleShade(root.screen);
            }
        }
    }
    // Only the wallpaper layer receives these right-clicks.
    // Regular application windows keep their own context menus.
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: desktopMenu.popup()
    }
    ExpressiveMenu {
        id: desktopMenu
        MenuItem {
            text: "All applications"
            onTriggered: ShellState.toggleDrawer(root.screen)
        }
        MenuItem {
            text: "Files"
            onTriggered: ShellState.openFiles(root.screen)
        }
        MenuItem {
            text: "Prism Store"
            onTriggered: ShellState.openStore(root.screen)
        }
        MenuSeparator {}
        MenuItem {
            text: "Settings"
            onTriggered: ShellState.openSettings(root.screen)
        }
        MenuItem {
            text: "Quick Settings"
            onTriggered: ShellState.toggleShade(root.screen)
        }
        MenuItem {
            text: "Refresh desktop"
            onTriggered: {
                SystemBridge.refresh();
                SystemBridge.refreshApps();
                Windows.refresh();
            }
        }
    }
    Column {
        x: Math.max(40, root.width * .075)
        y: Math.max(90, root.height * .14)
        spacing: 4
        Label {
            text: root.dateText
            role: "titleLarge"
            color: Theme.onWallpaper
        }
        Label {
            text: root.timeText
            font.pixelSize: Math.min(130, root.width * .12)
            font.weight: Font.Black
            font.letterSpacing: -6
            color: Theme.onWallpaper
        }
        Label {
            text: "A little more you."
            role: "titleMedium"
            color: Theme.onWallpaper
        }
    }
}
