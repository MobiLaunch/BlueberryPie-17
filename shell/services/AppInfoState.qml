pragma Singleton
import QtQuick
import Quickshell.Io

// App info for the application menu. One request runs at a time; a slow uninstall
// never blocks reading, and the result is always shown on the page.
QtObject {
    id: root
    property var app: null
    property var details: ({})
    property bool loaded: false
    property string error: ""
    property string notice: ""
    property bool gone: false
    readonly property bool busy: reader.running || actor.running
    readonly property string appId: app ? app.id : ""
    // "force-stop", "uninstall" or "copy-command" while that action runs.
    property string acting: ""

    function open(entry) {
        app = entry;
        details = ({});
        loaded = false;
        error = "";
        notice = "";
        acting = "";
        gone = false;
        refresh();
    }
    // The app a read in flight was started for; its answer is dropped if the page moved on.
    property string readingId: ""
    property bool again: false
    function refresh() {
        if (!app)
            return;
        if (reader.running) {
            again = true;
            return;
        }
        readingId = app.id;
        reader.command = ["prismctl", "appinfo", "info", app.id];
        reader.running = true;
    }
    function run(operation) {
        if (!app || actor.running)
            return false;
        acting = operation;
        error = "";
        notice = "";
        actor.command = ["prismctl", "appinfo", operation, app.id];
        actor.running = true;
        return true;
    }
    function forceStop() {
        return run("force-stop");
    }
    function uninstall() {
        return run("uninstall");
    }
    function copyRemoveCommand() {
        return run("copy-command");
    }
    property Process reader: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                const stale = root.readingId !== root.appId;
                if (root.again) {
                    root.again = false;
                    Qt.callLater(root.refresh);
                }
                if (stale)
                    return;
                try {
                    const data = JSON.parse(text);
                    if (data.ok) {
                        root.details = data;
                        root.loaded = true;
                    } else {
                        root.error = data.error || "Could not read app info";
                    }
                } catch (e) {
                    root.error = "Could not read app info";
                }
            }
        }
    }
    property Process actor: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                const operation = root.acting;
                root.acting = "";
                try {
                    const data = JSON.parse(text);
                    if (!data.ok) {
                        root.error = data.error || "That did not work";
                    } else if (operation === "uninstall") {
                        root.notice = data.name + " was removed";
                        root.gone = true;
                        SystemBridge.refreshApps();
                    } else if (operation === "force-stop") {
                        root.notice = "Stopped";
                    } else {
                        root.notice = "Command copied";
                    }
                } catch (e) {
                    root.error = "That did not work";
                }
                if (operation !== "uninstall")
                    root.refresh();
            }
        }
    }
}
