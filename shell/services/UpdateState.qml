pragma Singleton
import QtQuick
import Quickshell.Io

// Software updates for Settings. Reading the cached result is instant; "check" talks to
// the package servers and can take a while, so it runs on its own process. Installing
// opens the session terminal (the bridge starts it), it never happens silently.
QtObject {
    id: root
    property var info: ({
            checked: 0,
            total: 0,
            pacman: {
                available: true,
                count: 0,
                items: [],
                error: ""
            },
            flatpak: {
                available: true,
                count: 0,
                items: [],
                error: ""
            }
        })
    property bool loaded: false
    property string error: ""
    readonly property bool checking: checker.running
    readonly property int total: info.total || 0
    readonly property real checked: info.checked || 0
    readonly property string summary: !loaded ? "Check for updates" : checked === 0 ? "Not checked yet" : total === 0 ? "Up to date" : total + (total === 1 ? " update available" : " updates available")

    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function check() {
        if (checker.running)
            return;
        error = "";
        checker.running = true;
    }
    // kind: "pacman", "flatpak" or "all"
    function install(kind) {
        if (applier.running)
            return;
        error = "";
        applier.command = ["prismctl", "updates", "apply", kind];
        applier.running = true;
    }
    function ago(seconds) {
        if (!seconds)
            return "never";
        const minutes = Math.max(0, Math.round((Date.now() / 1000 - seconds) / 60));
        if (minutes < 1)
            return "just now";
        if (minutes < 60)
            return minutes + (minutes === 1 ? " minute ago" : " minutes ago");
        const hours = Math.round(minutes / 60);
        if (hours < 48)
            return hours + (hours === 1 ? " hour ago" : " hours ago");
        return Math.round(hours / 24) + " days ago";
    }
    function accept(text, fallback) {
        try {
            const result = JSON.parse(text);
            if (result.ok) {
                info = result;
                loaded = true;
            } else {
                error = result.error || fallback;
            }
        } catch (e) {
            error = fallback;
        }
    }
    property Process reader: Process {
        command: ["prismctl", "updates", "list"]
        stdout: StdioCollector {
            onStreamFinished: root.accept(text, "Could not read update information")
        }
    }
    property Process checker: Process {
        command: ["prismctl", "updates", "check"]
        stdout: StdioCollector {
            onStreamFinished: root.accept(text, "The update check did not respond")
        }
    }
    property Process applier: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const result = JSON.parse(text);
                    if (!result.ok)
                        root.error = result.error || "Could not open the terminal";
                } catch (e) {
                    root.error = "Could not open the terminal";
                }
            }
        }
    }
}
