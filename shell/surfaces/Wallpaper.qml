import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Background layer: artwork, home clock, desktop menu and wallpaper-only swipes.
PanelWindow {
    id: root
    anchors {
        top: true
        left: true
        right: true
        bottom: true
    }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Background
    WlrLayershell.namespace: "prism-wallpaper"
    color: Theme.primaryContainer
    readonly property string photoPath: SystemBridge.snapshot.settings.wallpaper || ""
    readonly property bool photo: photoPath.length > 0 && photoImage.status === Image.Ready
    readonly property color ink: photo ? "#ffffff" : Theme.wallpaperInk
    WallpaperArt {
        anchors.fill: parent
        visible: !root.photo
    }
    Image {
        id: photoImage
        anchors.fill: parent
        source: WallpaperState.fileUrl(root.photoPath)
        asynchronous: true
        fillMode: Image.PreserveAspectCrop
        sourceSize.width: root.width
        sourceSize.height: root.height
        visible: status === Image.Ready
    }
    // Keeps the clock readable over any picture; dims further in dark theme.
    Rectangle {
        anchors.fill: parent
        visible: root.photo
        gradient: Gradient {
            GradientStop {
                position: 0
                color: Theme.withAlpha("#000000", Theme.dark ? 0.55 : 0.38)
            }
            GradientStop {
                position: 0.6
                color: Theme.withAlpha("#000000", Theme.dark ? 0.25 : 0.05)
            }
            GradientStop {
                position: 1
                color: Theme.withAlpha("#000000", Theme.dark ? 0.35 : 0.0)
            }
        }
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
            text: "Widgets"
            onTriggered: ShellState.openSettings(root.screen, "widgets")
        }
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
    DesktopWidgets {
        anchors.fill: parent
        screen: root.screen
        ink: root.ink
    }
}
