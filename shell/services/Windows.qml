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
    readonly property bool busy: actor.running
    readonly property var focused: list.find(window => window.focused) || null
    // Previews of windows ({address: file path}); captured just before Recents opens.
    property var thumbs: ({})
    signal captured
    function capture() {
        if (capturer.running)
            return false;
        capturer.running = true;
        return true;
    }
    function thumbFor(address) {
        const path = thumbs[address];
        return path ? "file://" + path : "";
    }
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
    function minimize(address) {
        return act("minimize", address);
    }
    function restore(address) {
        return act("restore", address);
    }
    function maximize(address) {
        return act("maximize", address);
    }
    function toggleFloat(address) {
        return act("float", address);
    }
    function snap(address, side) {
        return act("snap-" + side, address);
    }
    // Focus a window, bringing it back first if it was minimized.
    function show(window) {
        return window.minimized ? restore(window.address) : focus(window.address);
    }
    // Several windows to close, one request at a time (the actor runs a single command).
    property var closing: []
    function closeMany(addresses) {
        closing = closing.concat(addresses.filter(address => closing.indexOf(address) < 0));
        drainClosing();
    }
    function drainClosing() {
        if (actor.running || closing.length === 0)
            return;
        const next = closing[0];
        closing = closing.slice(1);
        act("close", next);
    }
    // Android's Home: tuck every window on this workspace away; again brings them back.
    function showDesktop() {
        return act("show-desktop");
    }
    // Two windows side by side, `first` on the left.
    function split(first, second) {
        return act("split", first, second);
    }
    function act(operation, address, second) {
        if (actor.running)
            return false;
        actor.command = ["prismctl", "windows", operation].concat(address ? [address] : [], second ? [second] : []);
        actor.running = true;
        return true;
    }
    property Process capturer: Process {
        command: ["prismctl", "thumbnails", "capture"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok !== false && data.thumbs)
                        root.thumbs = data.thumbs;
                } catch (e) {
                    // No previews is a fine fallback; Recents still shows icons.
                }
            }
        }
        onExited: root.captured()
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
        onExited: root.drainClosing()
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
