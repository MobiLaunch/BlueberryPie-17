pragma Singleton
import QtQuick
import Quickshell.Io

// Opt-in clipboard history through `prismctl clipboard` (cliphist + wl-clipboard).
QtObject {
    id: root
    property bool enabled: false
    property bool available: true
    property var items: []
    property string error: ""
    property string lastAction: ""
    readonly property bool busy: reader.running || writer.running

    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function run(action, args) {
        if (writer.running)
            return;
        error = "";
        lastAction = action;
        writer.command = ["prismctl", "clipboard", action].concat(args || []);
        writer.running = true;
    }
    function copy(id) {
        run("copy", [id]);
    }
    function remove(id) {
        run("delete", [id]);
    }
    function clear() {
        run("clear");
    }
    function setEnabled(on) {
        run(on ? "enable" : "disable");
    }
    function apply(data) {
        if (data.ok === false) {
            error = data.error;
            return;
        }
        if (data.enabled !== undefined) {
            enabled = data.enabled === true;
            available = data.available !== false;
            items = data.items || [];
        }
    }
    property Process reader: Process {
        command: ["prismctl", "clipboard", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.apply(JSON.parse(text));
                } catch (e) {
                    root.error = "Could not read the clipboard history";
                }
            }
        }
    }
    property Process writer: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else if (root.lastAction === "copy") {
                        ShellState.toast = "Copied to the clipboard";
                        ShellState.toastTimer.restart();
                    } else
                        root.apply(data);
                } catch (e) {
                    root.error = "The clipboard action did not finish";
                }
            }
        }
        onExited: if (root.lastAction !== "copy")
            root.refresh()
    }
}
