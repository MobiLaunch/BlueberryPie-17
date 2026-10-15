pragma Singleton
import QtQuick
import Quickshell.Io

// Drives the disk installer through `prismctl installer`. All privileged work is
// done by the polkit-protected helper; this service only passes a validated request
// on stdin (the account password never appears in a command line).
QtObject {
    id: root
    property bool live: false
    property string firmware: "uefi"
    property bool online: false
    property string connectivity: "unknown"
    property var battery: ({
            available: false
        })
    property string minDisk: "16 GB"
    property var disks: []
    property var locales: []
    property var keyboards: []
    property var timezones: []
    property string defaultTimezone: "UTC"
    property var preview: null
    property string error: ""
    property bool loadingDisks: diskReader.running
    property bool previewing: planner.running
    // Progress
    property bool running: runner.running
    property bool done: false
    property bool failed: false
    property string phase: ""
    property string label: ""
    property string detail: ""
    property real percent: 0
    // Held only until the process starts, then cleared.
    property string pendingRequest: ""
    property string pendingTarget: ""

    function probe() {
        if (!statusReader.running)
            statusReader.running = true;
    }
    function refreshDisks() {
        if (!diskReader.running)
            diskReader.running = true;
    }
    function loadOptions() {
        if (locales.length === 0 && !optionReader.running)
            optionReader.running = true;
    }
    function open() {
        error = "";
        probe();
        refreshDisks();
        loadOptions();
    }
    function requestPreview(request) {
        if (planner.running)
            return;
        preview = null;
        error = "";
        pendingRequest = JSON.stringify(request);
        pendingTarget = "plan";
        planner.running = true;
    }
    function start(request) {
        if (runner.running)
            return;
        done = false;
        failed = false;
        error = "";
        percent = 0;
        phase = "authorization";
        label = "Waiting for administrator approval";
        detail = "";
        pendingRequest = JSON.stringify(request);
        pendingTarget = "install";
        runner.running = true;
    }
    function reset() {
        done = false;
        failed = false;
        error = "";
        percent = 0;
        phase = "";
        label = "";
        detail = "";
        preview = null;
    }
    function parseEvent(raw) {
        try {
            const event = JSON.parse(raw);
            if (event.ok === false) {
                error = event.error || "The installation did not finish";
                failed = true;
            } else if (event.phase) {
                phase = event.phase;
                label = event.label || event.phase;
                detail = event.detail || "";
                if (typeof event.percent === "number")
                    percent = event.percent;
                if (event.done === true)
                    done = true;
            }
        } catch (e) {
            // Non-JSON helper chatter is not progress.
        }
    }
    property Process statusReader: Process {
        command: ["prismctl", "installer", "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        return;
                    root.live = data.live === true;
                    root.firmware = data.firmware || "uefi";
                    root.online = data.online === true;
                    root.connectivity = data.connectivity || "unknown";
                    root.battery = data.battery || {
                        available: false
                    };
                    root.minDisk = data.min_disk_label || "16 GB";
                } catch (e) {
                    root.live = false;
                }
            }
        }
    }
    property Process diskReader: Process {
        command: ["prismctl", "installer", "disks"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.disks = data.disks || [];
                } catch (e) {
                    root.error = "Could not read the list of disks";
                }
            }
        }
    }
    property Process optionReader: Process {
        command: ["prismctl", "installer", "options"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.locales = data.locales || [];
                    root.keyboards = data.keyboards || [];
                    root.timezones = data.timezones || [];
                    root.defaultTimezone = data.default_timezone || "UTC";
                } catch (e) {
                    root.error = "Could not load language options";
                }
            }
        }
    }
    property Process planner: Process {
        command: ["prismctl", "installer", "plan"]
        stdinEnabled: true
        onStarted: {
            write(root.pendingRequest);
            root.pendingRequest = "";
            stdinEnabled = false;
        }
        onExited: stdinEnabled = true
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.preview = data;
                } catch (e) {
                    root.error = "Could not prepare the installation plan";
                }
            }
        }
    }
    property Process runner: Process {
        command: ["prismctl", "installer", "install"]
        stdinEnabled: true
        onStarted: {
            write(root.pendingRequest);
            root.pendingRequest = "";
            stdinEnabled = false;
        }
        stdout: SplitParser {
            onRead: data => root.parseEvent(data)
        }
        onExited: {
            stdinEnabled = true;
            if (!root.done && !root.failed) {
                root.failed = true;
                root.error = root.error || "The installation stopped before it finished";
            }
            root.refreshDisks();
        }
    }
}
