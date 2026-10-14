pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import "LaunchTracking.js" as LaunchTracking

QtObject {
    id: root
    property var activeScreen: Quickshell.screens.length ? Quickshell.screens[0] : null
    property bool shadeOpen: false
    property bool drawerOpen: false
    property bool settingsOpen: false
    property bool powerOpen: false
    property var launching: null
    property point launchOrigin: Qt.point(200, 200)
    property bool launchReady: false
    property bool launchMinimumElapsed: false
    property string toast: ""

    function close() {
        cancelLaunch();
        shadeOpen = false;
        drawerOpen = false;
        settingsOpen = false;
        powerOpen = false;
    }
    function cancelLaunch() {
        launching = null;
        launchReady = false;
        launchMinimumElapsed = false;
        launchTimer.stop();
        minimumLaunch.stop();
    }
    function windowArrived(name, data) {
        if (!launching || !LaunchTracking.matches(launching, LaunchTracking.eventClass(name, data)))
            return;
        launchReady = true;
        if (launchMinimumElapsed)
            cancelLaunch();
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
            launchReady = false;
            launchMinimumElapsed = false;
            minimumLaunch.restart();
            launchTimer.restart();
        }
    }
    property Timer launchTimer: Timer {
        interval: 8000
        // Unmatched IDs, background apps and missed IPC events never leave an overlay stuck.
        onTriggered: root.cancelLaunch()
    }
    property Timer minimumLaunch: Timer {
        interval: Theme.reducedMotion ? 0 : 220
        onTriggered: {
            root.launchMinimumElapsed = true;
            if (root.launchReady)
                root.cancelLaunch();
        }
    }
    property Connections launchEvents: Connections {
        target: Hyprland
        function onRawEvent(event) {
            root.windowArrived(event.name, event.data);
        }
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
                root.cancelLaunch();
                root.toast = message;
                toastTimer.restart();
            }
        }
    }
}
