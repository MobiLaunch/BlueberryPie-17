pragma Singleton
import QtQuick
import Quickshell.Io

// Storage breakdown for Settings > Storage, read on demand from the bridge.
QtObject {
    id: root
    property var usage: ({})
    property bool loaded: false
    property string error: ""
    readonly property bool busy: reader.running || cleaner.running

    function refresh() {
        if (!reader.running) {
            error = "";
            reader.running = true;
        }
    }
    function clearPreviews() {
        if (!cleaner.running)
            cleaner.running = true;
    }
    function size(bytes) {
        if (bytes === undefined || bytes === null)
            return "Unknown";
        const units = ["B", "KB", "MB", "GB", "TB"];
        let value = bytes;
        let step = 0;
        while (value >= 1000 && step < units.length - 1) {
            value /= 1000;
            step++;
        }
        const digits = step === 0 || value >= 100 ? 0 : value >= 10 ? 1 : 2;
        return value.toFixed(digits).replace(/\.0+$/, "").replace(/(\.\d)0$/, "$1") + " " + units[step];
    }
    property Process reader: Process {
        command: ["prismctl", "storage", "usage"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok) {
                        root.usage = data;
                        root.loaded = true;
                    } else {
                        root.error = data.error || "Could not read storage";
                    }
                } catch (e) {
                    root.error = "Could not read storage";
                }
            }
        }
    }
    property Process cleaner: Process {
        command: ["prismctl", "storage", "clear-previews"]
        stdout: StdioCollector {
            onStreamFinished: root.refresh()
        }
    }
}
