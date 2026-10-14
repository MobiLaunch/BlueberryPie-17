pragma Singleton
import QtQuick
import Quickshell.Hyprland
import Quickshell.Io
import "LaunchTracking.js" as LaunchTracking

// Open windows from the prismos bridge (hyprctl). Hyprland events trigger a
// debounced refresh; a slow poll recovers from missed events.
QtObject {
    id: root
    property var list: []
    property bool available: false
    readonly property var focused: list.find(window => window.focused) || null
    function refresh() {
        if (reader.running)
            return;
        reader.running = true;
    }
    function forApp(app) {
        return app ? list.filter(window => LaunchTracking.matches(app, window.class)) : [];
    }
    function focus(address) {
        return act("focus", address);
    }
    function close(address) {
        return act("close", address);
    }
    function act(operation, address) {
        if (actor.running)
            return false;
        actor.command = ["prismctl", "windows", operation, address];
        actor.running = true;
        return true;
    }
    property Process reader: Process {
        command: ["prismctl", "windows", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.available = data.ok === true;
                    root.list = data.windows || [];
                } catch (e) {
                    root.available = false;
                }
            }
        }
    }
    property Process actor: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        SystemBridge.error = data.error;
                } catch (e) {
                    SystemBridge.error = "Window action did not respond";
                }
                debounce.restart();
            }
        }
    }
    property Timer debounce: Timer {
        interval: 150
        onTriggered: root.refresh()
    }
    property Timer poll: Timer {
        interval: 10000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.refresh()
    }
    property Connections events: Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (["openwindow", "closewindow", "movewindow", "windowtitle", "activewindow"].includes(event.name))
                debounce.restart();
        }
    }
}
