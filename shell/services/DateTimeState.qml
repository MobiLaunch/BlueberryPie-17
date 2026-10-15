pragma Singleton
import QtQuick
import Quickshell.Io

// Time zone and automatic time through `prismctl datetime` (timedated). Changes may
// raise a polkit prompt, so every write reports its own result.
QtObject {
    id: root
    property bool available: true
    property string timezone: ""
    property bool ntp: false
    property bool inSync: false
    property string error: ""
    property string notice: ""
    readonly property bool busy: reader.running || writer.running
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function run(args, message) {
        if (writer.running)
            return;
        error = "";
        notice = message || "";
        writer.command = ["prismctl", "datetime"].concat(args);
        writer.running = true;
    }
    function setTimezone(name) {
        run(["timezone", name], "Time zone changed");
    }
    function setAutomatic(on) {
        run(["ntp", on ? "yes" : "no"], on ? "Automatic time is on" : "Automatic time is off");
    }
    function set24h(on) {
        run(["24h", on ? "yes" : "no"], "");
    }
    function apply(data) {
        if (data.ok === false) {
            error = data.error;
            notice = "";
            return;
        }
        available = data.available !== false;
        timezone = data.timezone || "";
        ntp = data.ntp === true;
        inSync = data.synchronized === true;
        if (data.error)
            error = data.error;
    }
    property Process reader: Process {
        command: ["prismctl", "datetime", "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.apply(JSON.parse(text));
                } catch (e) {
                    root.error = "Could not read the date and time settings";
                }
            }
        }
    }
    property Process writer: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.apply(JSON.parse(text));
                } catch (e) {
                    root.error = "The change did not finish";
                }
                SystemBridge.refresh();
            }
        }
    }
}
