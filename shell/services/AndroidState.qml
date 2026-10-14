pragma Singleton
import QtQuick
import Quickshell.Io

// One controller shared by Settings, welcome flow and the desktop.
// Stage captions are driven by backend stdout, never estimated percentages.
QtObject {
    id: root
    property bool enabled: false
    property bool available: false
    property bool initialized: false
    property bool ready: false
    property string phase: "off"
    property string label: "Android is off"
    property string error: ""
    property bool setupRunning: initializer.running
    property bool fdroidRunning: installer.running
    readonly property bool busy: setupRunning || fdroidRunning || disabling.running
    property bool lastSetupSucceeded: false
    property bool setupHadOutput: false

    function refresh() {
        if (!statusReader.running && !busy)
            statusReader.running = true;
    }
    function setEnabled(wanted) {
        if (busy)
            return;
        error = "";
        if (wanted) {
            enabled = true;
            ready = false;
            phase = "preparing";
            label = "Preparing Android";
            lastSetupSucceeded = false;
            setupHadOutput = false;
            initializer.running = true;
        } else {
            enabled = false;
            ready = false;
            phase = "off";
            label = "Turning off the Android session";
            disabling.running = true;
        }
    }
    function installFdroid() {
        if (busy || !ready)
            return;
        phase = "downloading";
        label = "Downloading F-Droid";
        error = "";
        installer.running = true;
    }
    function openAndroid() {
        if (ready && !opener.running)
            opener.running = true;
    }
    function parseEvent(raw, fdroid) {
        try {
            const event = JSON.parse(raw);
            if (event.ok === false) {
                error = event.error || "Android setup failed";
                phase = "error";
                label = "Setup needs attention";
            } else if (event.phase) {
                setupHadOutput = true;
                phase = event.phase;
                label = event.label || phase;
                if (event.ready === true) {
                    lastSetupSucceeded = true;
                    if (!fdroid)
                        ready = true;
                }
            }
        } catch (e) {
            // pkexec and Waydroid messages that aren't JSON are not status.
        }
    }
    property Process statusReader: Process {
        command: ["prismctl", "android", "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        return;
                    root.enabled = data.enabled === true;
                    root.available = data.available === true;
                    root.initialized = data.initialized === true;
                    root.ready = data.ready === true;
                    if (!root.busy) {
                        root.phase = data.phase || "off";
                        root.label = root.ready ? "Android is ready" :
                            !root.enabled ? "Android is off" :
                            !root.available ? "Waydroid is missing" :
                            "Android needs setup";
                    }
                } catch (e) {
                    root.error = "Could not check Android status";
                }
            }
        }
    }
    property Process initializer: Process {
        command: ["prismctl", "android", "enable"]
        stdout: SplitParser {
            onRead: root.parseEvent(data, false)
        }
        onExited: {
            if (!root.lastSetupSucceeded && !root.error) {
                root.error = "Android could not start. Try again or inspect waydroid log.";
                root.phase = "error";
            }
            SystemBridge.refresh();
            refreshLater.restart();
        }
    }
    property Process disabling: Process {
        command: ["prismctl", "android", "disable"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false) root.error = data.error;
                } catch (e) { root.error = "Could not stop Android"; }
            }
        }
        onExited: refreshLater.restart()
    }
    property Process installer: Process {
        command: ["prismctl", "android", "fdroid"]
        stdout: SplitParser {
            onRead: root.parseEvent(data, true)
        }
        onExited: {
            if (!root.lastSetupSucceeded && !root.error) root.error = "F-Droid installation was not completed";
            if (!root.error) root.label = "F-Droid is installed";
            SystemBridge.refreshApps();
            refreshLater.restart();
        }
    }
    property Process opener: Process {
        command: ["prismctl", "android", "open"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false) root.error = data.error;
                } catch (e) { root.error = "Couldn't open Android"; }
            }
        }
    }
    property Timer refreshLater: Timer {
        interval: 180
        onTriggered: root.refresh()
    }
    property Timer heartbeat: Timer {
        interval: 15000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.refresh()
    }
}
