pragma Singleton
import QtQuick
import Quickshell.Io

// Saved time zones and their local times via `prismctl worldclock`.
QtObject {
    id: root
    property var clocks: []
    property string error: ""
    readonly property bool busy: reader.running || writer.running
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function add(zone) {
        run(["add", zone]);
    }
    function remove(zone) {
        run(["remove", zone]);
    }
    function run(args) {
        if (writer.running)
            return;
        error = "";
        writer.command = ["prismctl", "worldclock"].concat(args);
        writer.running = true;
    }
    function dayText(delta) {
        return delta === 0 ? "Today" : delta === 1 ? "Tomorrow" : delta === -1 ? "Yesterday" : "";
    }
    function offsetText(minutes) {
        if (minutes === 0)
            return "Same time";
        const sign = minutes > 0 ? "+" : "−";
        const abs = Math.abs(minutes);
        const hours = Math.floor(abs / 60), rest = abs % 60;
        return sign + hours + " h" + (rest ? " " + rest + " min" : "");
    }
    function apply(data) {
        if (data.ok === false)
            error = data.error;
        else
            clocks = data.clocks || [];
    }
    property Process reader: Process {
        command: ["prismctl", "worldclock", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.apply(JSON.parse(text));
                } catch (e) {
                    root.error = "Could not read the world clocks";
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
            }
        }
    }
}
