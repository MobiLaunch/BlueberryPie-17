pragma Singleton
import QtQuick
import Quickshell.Io

QtObject {
    id: root
    property var values: ({
        natural_scroll: true,
        tap_to_click: true,
        pointer_speed: 0,
        repeat_rate: 25
    })
    property string error: ""
    readonly property bool busy: reader.running || writer.running
    function refresh() {
        if (!reader.running && !writer.running)
            reader.running = true;
    }
    function setValue(name, value) {
        if (busy)
            return false;
        error = "";
        writer.command = ["prismctl", "input", "set", name, String(value)];
        writer.running = true;
        return true;
    }
    property Process reader: Process {
        command: ["prismctl", "input", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const payload = JSON.parse(text);
                    if (payload.ok === false)
                        root.error = payload.error;
                    else if (payload.settings)
                        root.values = payload.settings;
                } catch (e) { root.error = "Could not read input settings"; }
            }
        }
    }
    property Process writer: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const payload = JSON.parse(text);
                    if (payload.ok === false)
                        root.error = payload.error;
                    else if (payload.settings)
                        root.values = payload.settings;
                } catch (e) { root.error = "Could not save the input change"; }
            }
        }
        onExited: readAgain.restart()
    }
    property Timer readAgain: Timer {
        interval: 80
        onTriggered: root.refresh()
    }
    property Connections settingsConnection: Connections {
        target: ShellState
        function onSettingsOpenChanged() {
            if (ShellState.settingsOpen)
                root.refresh();
        }
    }
}
