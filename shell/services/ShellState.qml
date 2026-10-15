pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import "LaunchTracking.js" as LaunchTracking

QtObject {
    id: root
    property var activeScreen: Quickshell.screens.length ? Quickshell.screens[0] : null
    property bool onboardingOpen: false
    property bool installerOpen: false
    property bool utilitiesOpen: false
    property string utilitiesTab: "calculator"
    property bool firstRunChecked: false
    property bool shadeOpen: false
    property bool drawerOpen: false
    property bool settingsOpen: false
    // Settings page to show when Settings opens ("" keeps the last one).
    property string settingsPage: ""
    // Text to prefill in the launcher search when it opens.
    property string launcherQuery: ""
    property bool powerOpen: false
    property bool storeOpen: false
    property bool filesOpen: false
    property bool recentsOpen: false
    property var launching: null
    property point launchOrigin: Qt.point(200, 200)
    property bool launchReady: false
    property bool launchMinimumElapsed: false
    property string toast: ""
    // On-screen indicator for hardware volume, microphone and brightness keys.
    property string osdKind: ""
    property var osdScreen: null
    function showOsd(kind) {
        osdScreen = focusedScreen();
        osdKind = kind;
        osdTimer.restart();
    }
    property Timer osdTimer: Timer {
        interval: 1600
        onTriggered: root.osdKind = ""
    }

    function checkFirstRun() {
        if (firstRunChecked)
            return;
        const prefs = SystemBridge.snapshot.settings;
        if (!prefs || typeof prefs.onboarding_complete !== "boolean")
            return;
        firstRunChecked = true;
        if (!prefs.onboarding_complete) {
            close();
            activeScreen = focusedScreen();
            onboardingOpen = true;
        }
    }
    property Connections welcomeObserver: Connections {
        target: SystemBridge
        function onSnapshotChanged() {
            root.checkFirstRun();
        }
    }
    function close() {
        cancelLaunch();
        shadeOpen = false;
        drawerOpen = false;
        settingsOpen = false;
        powerOpen = false;
        storeOpen = false;
        filesOpen = false;
        recentsOpen = false;
        utilitiesOpen = false;
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
    function openLauncher(screen, query) {
        close();
        activeScreen = screen || focusedScreen();
        launcherQuery = query || "";
        drawerOpen = true;
        SystemBridge.refreshApps();
    }
    // Capture after the panels have faded so they are not in the picture.
    property string screenshotMode: "area"
    function screenshot(mode) {
        close();
        screenshotMode = mode;
        shotTimer.restart();
    }
    property Timer shotTimer: Timer {
        interval: 380
        onTriggered: SystemBridge.screenshot(root.screenshotMode)
    }
    function openInstaller(screen) {
        if (!InstallerState.live) {
            toast = "Installing is only available from the PrismOS live USB";
            toastTimer.restart();
            return;
        }
        close();
        activeScreen = screen || focusedScreen();
        InstallerState.open();
        installerOpen = true;
    }
    function openUtilities(screen, tab) {
        const same = utilitiesOpen && activeScreen === screen && utilitiesTab === tab;
        close();
        if (same)
            return;
        activeScreen = screen || focusedScreen();
        utilitiesTab = tab || "calculator";
        utilitiesOpen = true;
    }
    function openSettings(screen, page) {
        close();
        activeScreen = screen;
        if (page)
            settingsPage = page;
        settingsOpen = true;
    }
    function openStore(screen) {
        close();
        activeScreen = screen;
        storeOpen = true;
    }
    function openFiles(screen) {
        close();
        activeScreen = screen;
        filesOpen = true;
    }
    // Recents takes fresh window previews first (the overview itself must not be in them).
    property var pendingRecents: null
    function toggleRecents(screen) {
        const open = !recentsOpen || activeScreen !== screen;
        close();
        pendingRecents = null;
        recentsFallback.stop();
        if (!open)
            return;
        Windows.refresh();
        if (SystemBridge.snapshot.settings.recents_previews === false || !Windows.capture()) {
            showRecents(screen);
            return;
        }
        pendingRecents = screen;
        recentsFallback.restart();
    }
    function showRecents(screen) {
        activeScreen = screen;
        recentsOpen = true;
        Windows.refresh();
    }
    function finishRecents() {
        recentsFallback.stop();
        if (pendingRecents === null)
            return;
        const screen = pendingRecents;
        pendingRecents = null;
        showRecents(screen);
    }
    property Timer recentsFallback: Timer {
        interval: 1500
        onTriggered: root.finishRecents()
    }
    property Connections previewsReady: Connections {
        target: Windows
        function onCaptured() {
            root.finishRecents();
        }
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
        function onScreenshotFinished(success, message) {
            if (success || message !== "Screenshot cancelled") {
                root.toast = message;
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
