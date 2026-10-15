pragma Singleton
import QtQuick
import Quickshell.Io

QtObject {
    id: root
    property var snapshot: ({
            wifi: {
                available: false,
                enabled: false,
                label: "Reading network…"
            },
            bluetooth: {
                available: false,
                enabled: false
            },
            volume: {
                available: false,
                value: 0,
                muted: false
            },
            microphone: {
                available: false,
                value: 0,
                muted: false
            },
            brightness: {
                available: false,
                value: 0
            },
            battery: {
                available: false,
                value: 0
            },
            airplane: {
                available: false,
                enabled: false
            },
            profile: {
                available: false,
                saver: false
            },
            night_light: {
                available: false,
                enabled: false
            },
            settings: {
                dark: false,
                reduced_motion: false,
                dnd: false,
                favorites: null
            },
            power: {
                lock: false,
                logout: false,
                shutdown: false,
                restart: false,
                suspend: false
            }
        })
    property var apps: []
    property string error: ""
    property var pending: []
    property bool busy: writer.running
    property bool needsRefresh: false
    signal launchFinished(bool success, string message)

    function refresh() {
        if (reader.running)
            needsRefresh = true;
        else
            reader.running = true;
    }
    function refreshApps() {
        if (!appReader.running)
            appReader.running = true;
    }
    function action(name, value) {
        let args = ["prismctl", "action", name];
        if (value !== undefined)
            args.push(String(Math.round(value)));
        // Sliders coalesce pending writes. Commands are arrays, never shell text.
        let queue = pending.filter(item => item[2] !== name);
        queue.push(args);
        pending = queue;
        drain();
    }
    function drain() {
        if (writer.running || pending.length === 0)
            return;
        const queue = pending.slice();
        writer.command = queue.shift();
        pending = queue;
        error = "";
        writer.running = true;
    }
    function setSeed(seed) {
        const queue = pending.slice();
        queue.push(["prismctl", "theme", "--seed", seed]);
        pending = queue;
        drain();
    }
    function setTiles(ids) {
        const queue = pending.filter(item => item[1] !== "tiles");
        queue.push(["prismctl", "tiles", "set"].concat(ids));
        pending = queue;
        drain();
    }
    function resetTiles() {
        const queue = pending.filter(item => item[1] !== "tiles");
        queue.push(["prismctl", "tiles", "reset"]);
        pending = queue;
        drain();
    }
    function addAlarm(time, days, label) {
        const queue = pending.slice();
        queue.push(["prismctl", "alarms", "add", "--time", time, "--days", days.join(","), "--label", label]);
        pending = queue;
        drain();
    }
    function toggleAlarm(id) {
        const queue = pending.slice();
        queue.push(["prismctl", "alarms", "toggle", String(id)]);
        pending = queue;
        drain();
    }
    function removeAlarm(id) {
        const queue = pending.slice();
        queue.push(["prismctl", "alarms", "remove", String(id)]);
        pending = queue;
        drain();
    }
    function setQuietHours(enabled, start, end) {
        const queue = pending.filter(item => item[1] !== "quiet-hours");
        queue.push(["prismctl", "quiet-hours", "set", "--enabled", enabled ? "yes" : "no", "--start", start, "--end", end]);
        pending = queue;
        drain();
    }
    function playSound(name) {
        if (!sounder.running) {
            sounder.command = ["prismctl", "sound", name];
            sounder.running = true;
        }
    }
    property Process sounder: Process {}
    function muteApp(name, muted) {
        const queue = pending.slice();
        queue.push(["prismctl", "notifications", muted ? "mute" : "unmute", name]);
        pending = queue;
        drain();
    }
    function screenshot(mode) {
        if (shooter.running)
            return;
        shooter.command = ["prismctl", "screenshot", mode];
        shooter.running = true;
    }
    signal screenshotFinished(bool success, string message)
    property Process shooter: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.screenshotFinished(false, data.error);
                    else
                        root.screenshotFinished(true, data.copied ? "Screenshot copied and saved to Pictures" : "Screenshot saved to Pictures");
                } catch (e) {
                    root.screenshotFinished(false, "The screenshot did not finish");
                }
            }
        }
    }
    function setScheme(scheme) {
        const queue = pending.slice();
        queue.push(["prismctl", "theme", "--scheme", scheme]);
        pending = queue;
        drain();
    }
    function setFontScale(scale) {
        const queue = pending.slice();
        queue.push(["prismctl", "theme", "--font-scale", String(scale)]);
        pending = queue;
        drain();
    }
    function favorite(operation, id) {
        const queue = pending.slice();
        queue.push(["prismctl", "favorites", operation, id]);
        pending = queue;
        drain();
    }
    function webSearch(query) {
        if (webSearcher.running)
            return;
        webSearcher.command = ["prismctl", "websearch", query];
        webSearcher.running = true;
    }
    property Process webSearcher: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                } catch (e) {
                    root.error = "Could not open the browser";
                }
            }
        }
    }
    function launch(id) {
        if (launcher.running)
            return false;
        error = "";
        launcher.command = ["prismctl", "launch", id];
        launcher.running = true;
        return true;
    }
    property Process reader: Process {
        command: ["prismctl", "status"]
        onExited: if (root.needsRefresh) {
            root.needsRefresh = false;
            refreshAgain.restart();
        }
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.settings)
                        root.snapshot = data;
                } catch (e) {
                    root.error = "Could not read system state";
                }
            }
        }
    }
    property Timer refreshAgain: Timer {
        interval: 1
        onTriggered: root.refresh()
    }
    property Process appReader: Process {
        command: ["prismctl", "apps"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (Array.isArray(data))
                        root.apps = data;
                } catch (e) {
                    root.error = "Could not read installed applications";
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
                } catch (e) {
                    root.error = "System action did not respond";
                }
            }
        }
        onExited: {
            root.refresh();
            if (Wireless.watchedKind)
                Wireless.refresh(Wireless.watchedKind, false, false);
            if (AudioState.panelOpen)
                AudioState.refresh();
            nextWrite.restart();
        }
    }
    property Timer nextWrite: Timer {
        interval: 60
        onTriggered: root.drain()
    }
    property Process launcher: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.launchFinished(data.ok === true, data.error || "");
                    if (data.ok === false)
                        root.error = data.error;
                } catch (e) {
                    root.launchFinished(false, "Application launch failed");
                }
            }
        }
    }
    property Timer poll: Timer {
        interval: 5000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.refresh()
    }
    property Timer initialApps: Timer {
        interval: 1
        running: true
        onTriggered: root.refreshApps()
    }
    property Process networkEvents: Process {
        command: ["nmcli", "monitor"]
        running: true
        stdout: SplitParser {
            onRead: networkDebounce.restart()
        }
        // Retry service restarts without a rapid respawn loop when nmcli is absent.
        onExited: networkRetry.restart()
    }
    property Timer networkRetry: Timer {
        interval: 30000
        onTriggered: networkEvents.running = true
    }
    property Timer networkDebounce: Timer {
        interval: 300
        onTriggered: {
            root.refresh();
            if (Wireless.watchedKind === "wifi")
                Wireless.refresh("wifi", false, false);
        }
    }
}
