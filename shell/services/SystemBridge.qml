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
    property bool staleRead: false
    property string lastStatus: ""
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
    // A copy of the snapshot with a few keys changed per section, so a tile can answer
    // a click at once instead of waiting for the command and a full status read.
    function patched(changes) {
        const next = Object.assign({}, snapshot);
        for (const section in changes)
            next[section] = Object.assign({}, snapshot[section], changes[section]);
        return next;
    }
    function clamp(value, low) {
        return Math.max(low, Math.min(100, Math.round(value)));
    }
    // What the snapshot will say once `name` has run, for actions whose result is certain.
    // Anything not listed waits for the real state. A failed action is corrected by the
    // status read that always follows it.
    function predict(name, value) {
        const s = snapshot;
        switch (name) {
        case "dark":
        case "reduced_motion":
        case "dnd": {
            const change = {};
            change[name] = !s.settings[name];
            return patched({
                settings: change
            });
        }
        case "wifi":
            return s.wifi.available ? patched({
                wifi: {
                    enabled: !s.wifi.enabled
                }
            }) : null;
        case "bluetooth":
            return s.bluetooth.available ? patched({
                bluetooth: {
                    enabled: !s.bluetooth.enabled
                }
            }) : null;
        case "mute":
            return s.volume.available ? patched({
                volume: {
                    muted: !s.volume.muted
                }
            }) : null;
        case "microphone-mute":
            return s.microphone.available ? patched({
                microphone: {
                    muted: !s.microphone.muted
                }
            }) : null;
        case "airplane":
            return s.airplane.available ? patched({
                airplane: {
                    enabled: !s.airplane.enabled
                },
                wifi: {
                    enabled: s.airplane.enabled && s.wifi.available
                },
                bluetooth: {
                    enabled: s.airplane.enabled && s.bluetooth.available
                }
            }) : null;
        case "night-light":
            return s.night_light.available ? patched({
                night_light: {
                    enabled: !s.night_light.enabled
                },
                settings: {
                    night_light: !s.night_light.enabled
                }
            }) : null;
        case "battery-saver":
            return s.profile.available ? patched({
                profile: {
                    saver: !s.profile.saver
                }
            }) : null;
        case "volume":
            return s.volume.available && value !== undefined ? patched({
                volume: {
                    value: clamp(value, 0)
                }
            }) : null;
        case "brightness":
            return s.brightness.available && value !== undefined ? patched({
                brightness: {
                    value: clamp(value, 1)
                }
            }) : null;
        case "volume-up":
        case "volume-down":
            return s.volume.available ? patched({
                volume: {
                    value: clamp(s.volume.value + (name === "volume-up" ? 5 : -5), 0)
                }
            }) : null;
        case "brightness-up":
        case "brightness-down":
            return s.brightness.available ? patched({
                brightness: {
                    value: clamp(s.brightness.value + (name === "brightness-up" ? 5 : -5), 1)
                }
            }) : null;
        }
        return null;
    }
    function action(name, value) {
        const guess = predict(name, value);
        if (guess) {
            snapshot = guess;
            // The guess is not what was last read, so the next real answer must always replace it
            // (even when it equals the previous reading, as after a command that failed).
            lastStatus = "";
            // A status read already in flight predates this click; its answer would flip the tile back.
            if (reader.running)
                staleRead = true;
        }
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
    function setPreviews(on) {
        const queue = pending.filter(item => item[1] !== "thumbnails");
        queue.push(["prismctl", "thumbnails", "enable", on ? "yes" : "no"]);
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
    function setNotificationHistory(on) {
        const queue = pending.filter(item => item[1] !== "notifications" || item[2] !== "history");
        queue.push(["prismctl", "notifications", "history", on ? "yes" : "no"]);
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
                const stale = root.staleRead;
                root.staleRead = false;
                if (stale) {
                    // Read before the last click took effect: discard it and read again.
                    root.needsRefresh = true;
                    return;
                }
                // An unchanged answer would still re-run every binding in the shell.
                if (text === root.lastStatus)
                    return;
                try {
                    const data = JSON.parse(text);
                    if (data.settings) {
                        root.lastStatus = text;
                        root.snapshot = data;
                    }
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
                    // Reopening the launcher re-reads the list; keep the model (and its tiles) when nothing changed.
                    if (Array.isArray(data) && JSON.stringify(data) !== JSON.stringify(root.apps))
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
