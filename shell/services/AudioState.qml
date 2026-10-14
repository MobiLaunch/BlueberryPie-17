pragma Singleton
import QtQuick
import Quickshell.Io
import "AudioEvents.js" as AudioEvents

QtObject {
    id: root
    property var devices: ({
            available: false,
            outputs: [],
            inputs: [],
            output: null,
            input: null
        })
    property string error: ""
    property string notice: ""
    property bool panelOpen: false
    property string tab: "output"
    property bool adjusting: false
    property bool needsRead: false
    property bool responded: false
    property string operation: ""
    property var eventStream: AudioEvents.createState()
    readonly property bool busy: reader.running || writer.running
    readonly property bool writing: writer.running

    function refresh(clearError = false) {
        if (busy || adjusting) {
            needsRead = true;
            return;
        }
        needsRead = false;
        if (clearError)
            error = "";
        reader.running = true;
    }
    function change(action, kind, device, value) {
        if (busy)
            return false;
        error = "";
        notice = "";
        responded = false;
        operation = action;
        const args = ["prismctl", "audio", action, "--kind", kind, "--serial", String(device.serial), "--node-name=" + device.name];
        if (value !== undefined)
            args.push("--value", String(Math.round(value)));
        writer.command = args;
        writer.running = true;
        return true;
    }
    onPanelOpenChanged: if (panelOpen) {
        notice = "";
        refresh(true);
    }
    onAdjustingChanged: if (!adjusting && needsRead)
        refreshLater.restart()

    property Process reader: Process {
        command: ["prismctl", "audio", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.outputs !== undefined && data.inputs !== undefined)
                        root.devices = data;
                    else
                        root.error = data.error || "Could not read sound devices";
                } catch (e) {
                    root.error = "Could not read sound devices";
                }
            }
        }
        onExited: if (root.needsRead)
            refreshLater.restart()
    }
    property Process writer: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                root.responded = true;
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.notice = root.operation === "select" ? "Device selected" : "Sound updated";
                } catch (e) {
                    root.error = "The sound action did not respond";
                }
            }
        }
        onExited: {
            if (!root.responded)
                root.error = "The sound action could not start";
            SystemBridge.refresh();
            refreshLater.restart();
        }
    }
    property Timer refreshLater: Timer {
        interval: 150
        onTriggered: root.refresh()
    }
    property Timer visiblePoll: Timer {
        interval: 5000
        repeat: true
        running: root.panelOpen
        onTriggered: root.refresh()
    }
    property Process events: Process {
        command: ["pw-dump", "--monitor", "--no-colors"]
        running: true
        onStarted: root.eventStream = AudioEvents.createState()
        stdout: SplitParser {
            onRead: data => {
                try {
                    if (AudioEvents.feed(root.eventStream, data + "\n"))
                        eventDebounce.restart();
                } catch (e) {
                    root.eventStream = AudioEvents.createState();
                    console.warn("PrismOS sound events:", e);
                    events.running = false;
                }
            }
        }
        onExited: {
            retryEvents.restart();
            eventDebounce.restart();
        }
    }
    property Timer eventDebounce: Timer {
        interval: 220
        onTriggered: {
            SystemBridge.refresh();
            if (root.panelOpen)
                root.refresh();
        }
    }
    property Timer retryEvents: Timer {
        interval: 30000
        onTriggered: events.running = true
    }
}
