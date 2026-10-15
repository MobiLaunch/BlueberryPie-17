pragma Singleton
import QtQuick
import Quickshell.Io

// System facts for Settings > About, read on demand from the bridge.
QtObject {
    id: root
    property var info: ({})
    property bool loaded: false
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function duration(seconds) {
        if (seconds === null || seconds === undefined)
            return "Unknown";
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor(seconds % 86400 / 3600);
        const minutes = Math.floor(seconds % 3600 / 60);
        return (days ? days + " d " : "") + (hours || days ? hours + " h " : "") + minutes + " min";
    }
    property Process reader: Process {
        command: ["prismctl", "about"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok) {
                        root.info = data;
                        root.loaded = true;
                    }
                } catch (e) {
                    root.loaded = false;
                }
            }
        }
    }
}
