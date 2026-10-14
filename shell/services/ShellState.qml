pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

QtObject {
    id: root
    property var activeScreen: Quickshell.screens.length ? Quickshell.screens[0] : null
    property bool shadeOpen: false
    property bool drawerOpen: false
    property bool settingsOpen: false
    property bool powerOpen: false
    property var launching: null
    property point launchOrigin: Qt.point(200, 200)
    property string toast: ""

    function close() {
        shadeOpen = false;
        drawerOpen = false;
        settingsOpen = false;
        powerOpen = false;
    }
    function focusedScreen() {
        const monitor = Hyprland.focusedMonitor;
        return (monitor ? Quickshell.screens.find(screen => screen.name === monitor.name) : null) || activeScreen || Quickshell.screens[0] || null;
    }
    function toggleShade(screen) {
        const open = !shadeOpen || activeScreen !== screen;
        close();
        activeScreen = screen;
        shadeOpen = open;
    }
    function toggleDrawer(screen) {
        const open = !drawerOpen || activeScreen !== screen;
        close();
        activeScreen = screen;
        drawerOpen = open;
        if (open)
            SystemBridge.refreshApps();
    }
    function openSettings(screen) {
        close();
        activeScreen = screen;
        settingsOpen = true;
    }
    function openPower(screen) {
        close();
        activeScreen = screen;
        powerOpen = true;
    }
    property Connections screensConnection: Connections {
        target: Quickshell
        function onScreensChanged() {
            if (!Quickshell.screens.includes(root.activeScreen)) {
                root.close();
                root.launching = null;
                root.activeScreen = Quickshell.screens.length ? Quickshell.screens[0] : null;
            }
        }
    }
    function launch(app, screen, x, y) {
        if (SystemBridge.launch(app.id)) {
            close();
            activeScreen = screen;
            launchOrigin = Qt.point(x, y);
            launching = app;
            launchTimer.restart();
        }
    }
    property Timer launchTimer: Timer {
        interval: Theme.reducedMotion ? 100 : 650
        onTriggered: root.launching = null
    }
    property Timer toastTimer: Timer {
        interval: 5000
        onTriggered: root.toast = ""
    }
    property Connections failures: Connections {
        target: SystemBridge
        function onErrorChanged() {
            if (SystemBridge.error) {
                root.toast = SystemBridge.error;
                toastTimer.restart();
            }
        }
        function onLaunchFinished(success, message) {
            if (!success) {
                root.launching = null;
                root.toast = message;
                toastTimer.restart();
            }
        }
    }
}
