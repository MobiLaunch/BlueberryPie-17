pragma Singleton
import QtQuick
import Quickshell

QtObject {
    id: root
    property var activeScreen: Quickshell.screens.length ? Quickshell.screens[0] : null
    property bool shadeOpen: false
    property bool drawerOpen: false
    property bool settingsOpen: false
    property var launching: null
    property point launchOrigin: Qt.point(200, 200)
    property string toast: ""

    function close() {
        shadeOpen = false;
        drawerOpen = false;
        settingsOpen = false;
    }
    function toggleShade(screen) {
        const open = !shadeOpen;
        close();
        activeScreen = screen;
        shadeOpen = open;
    }
    function toggleDrawer(screen) {
        const open = !drawerOpen;
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
