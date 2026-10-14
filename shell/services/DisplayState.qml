pragma Singleton
import QtQuick
import Quickshell.Io

// Compositor-backed display scaling with confirmation and automatic rollback.
QtObject {
    id: root
    property var monitors: []
    property string error: ""
    property string notice: ""
    property string trialToken: ""
    property string trialName: ""
    property real trialScale: 1
    property int seconds: 0
    readonly property bool busy: previewer.running || confirmer.running
    function refresh() {
        if (!reader.running && !previewer.running)
            reader.running = true;
    }
    function preview(name, scale) {
        if (busy) return;
        error = "";
        notice = "";
        trialToken = "";
        previewer.command = ["prismctl", "display", "preview", name, String(scale)];
        previewer.running = true;
    }
    function confirm() {
        if (!trialToken || confirmer.running) return;
        confirmer.command = ["prismctl", "display", "confirm", trialToken];
        confirmer.running = true;
    }
    function consumeLine(line) {
        try {
            const data = JSON.parse(line);
            if (data.ok === false) {
                error = data.error || "Display change failed";
                return;
            }
            if (data.phase === "trial") {
                trialToken = data.token || "";
                trialName = data.name || "";
                trialScale = data.scale || 1;
                seconds = data.seconds || 20;
                ticker.start();
            } else if (data.phase === "confirmed") {
                notice = "Display scale saved";
                trialToken = "";
                ticker.stop();
            } else if (data.phase === "reverted") {
                notice = "Previous display scale restored";
                trialToken = "";
                ticker.stop();
            }
        } catch (e) {
            error = "Display service returned an invalid status";
        }
    }
    property Process reader: Process {
        command: ["prismctl", "display", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const payload = JSON.parse(text);
                    if (payload.ok === false)
                        root.error = payload.error;
                    else
                        root.monitors = payload.monitors || [];
                } catch (e) {
                    root.error = "Could not read connected displays";
                }
            }
        }
    }
    property Process previewer: Process {
        stdout: SplitParser { onRead: root.consumeLine(data) }
        onExited: {
            root.trialToken = "";
            ticker.stop();
            refreshAfter.restart();
        }
    }
    property Process confirmer: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const payload = JSON.parse(text);
                    if (payload.ok === false)
                        root.error = payload.error;
                } catch (e) {
                    root.error = "Could not confirm display changes";
                }
            }
        }
    }
    property Timer ticker: Timer {
        interval: 1000
        repeat: true
        onTriggered: {
            root.seconds = Math.max(0, root.seconds - 1);
            if (root.seconds === 0) stop();
        }
    }
    property Timer refreshAfter: Timer {
        interval: 150
        onTriggered: root.refresh()
    }
    property Connections settingsObserver: Connections {
        target: ShellState
        function onSettingsOpenChanged() {
            if (ShellState.settingsOpen)
                root.refresh();
        }
    }
}
