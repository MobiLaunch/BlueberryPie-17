pragma Singleton
import QtQuick
import Quickshell.Io

// Desktop widget selection, system stats and (opt-in) weather, all via prismctl.
QtObject {
    id: root
    readonly property var defaults: ["glance", "clock", "search", "calendar", "media"]
    readonly property var chosen: SystemBridge.snapshot.settings.widgets
    readonly property var enabled: Array.isArray(chosen) ? chosen : defaults
    readonly property var catalog: [
        {
            id: "glance",
            title: "At a glance",
            description: "Today's date with weather or battery",
            symbol: "calendar_today"
        },
        {
            id: "clock",
            title: "Clock",
            description: "Large digital clock",
            symbol: "recents"
        },
        {
            id: "search",
            title: "Search",
            description: "Search apps, then the web",
            symbol: "search"
        },
        {
            id: "calendar",
            title: "Calendar",
            description: "This month at a glance",
            symbol: "calendar"
        },
        {
            id: "media",
            title: "Now playing",
            description: "Appears while a player is active",
            symbol: "music"
        },
        {
            id: "weather",
            title: "Weather",
            description: "Temperature and conditions",
            symbol: "partly_cloudy"
        },
        {
            id: "system",
            title: "System",
            description: "Processor, memory and storage",
            symbol: "memory"
        },
        {
            id: "notes",
            title: "Notes",
            description: "A scratchpad that stays on your desktop",
            symbol: "document"
        },
        {
            id: "analog",
            title: "Analog clock",
            description: "A Material cookie-shaped clock",
            symbol: "sleep"
        }
    ]
    property var stats: ({})
    property var weather: ({
            configured: false
        })
    property var places: []
    property string searchError: ""
    readonly property var place: SystemBridge.snapshot.settings.weather || ({})
    readonly property bool weatherConfigured: place && place.label !== undefined
    readonly property var sizes: SystemBridge.snapshot.settings.widget_sizes || ({})
    readonly property var resizable: ["calendar", "weather", "system", "notes"]
    function sizeFactor(id) {
        const size = sizes[id];
        return size === "small" ? 0.85 : size === "large" ? 1.3 : 1;
    }
    function setSize(id, size) {
        if (writer.running)
            return;
        writer.command = ["prismctl", "widgets", "size", id, size];
        writer.running = true;
    }
    function has(id) {
        return enabled.indexOf(id) >= 0;
    }
    function set(id, on) {
        if (writer.running)
            return;
        const next = enabled.filter(item => item !== id);
        if (on)
            next.push(id);
        writer.command = ["prismctl", "widgets", "set"].concat(next);
        writer.running = true;
    }
    function refreshStats() {
        if (!statReader.running)
            statReader.running = true;
    }
    function refreshWeather() {
        if (!weatherReader.running)
            weatherReader.running = true;
    }
    function searchPlaces(name) {
        searchError = "";
        if (placeSearch.running)
            return;
        placeSearch.command = ["prismctl", "weather", "search", "--query", name];
        placeSearch.running = true;
    }
    function choosePlace(item, units) {
        if (weatherWriter.running)
            return;
        weatherWriter.command = ["prismctl", "weather", "set", "--lat", String(item.lat), "--lon", String(item.lon), "--label", item.label, "--units", units || "metric"];
        weatherWriter.running = true;
    }
    function setUnits(units) {
        if (weatherConfigured)
            choosePlace(place, units);
    }
    function disableWeather() {
        if (weatherWriter.running)
            return;
        weatherWriter.command = ["prismctl", "weather", "disable"];
        weatherWriter.running = true;
    }
    property Process writer: Process {
        onExited: SystemBridge.refresh()
    }
    property Process statReader: Process {
        command: ["prismctl", "stats"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.stats = JSON.parse(text);
                } catch (e) {
                    root.stats = ({});
                }
            }
        }
    }
    property Process weatherReader: Process {
        command: ["prismctl", "weather", "get"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.weather = JSON.parse(text);
                } catch (e) {
                    root.weather = ({
                            configured: false
                        });
                }
            }
        }
    }
    property Process placeSearch: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.places = data.ok ? data.places : [];
                    root.searchError = data.ok ? (data.places.length ? "" : "No places found") : data.error;
                } catch (e) {
                    root.searchError = "Could not search for places";
                }
            }
        }
    }
    property Process weatherWriter: Process {
        onExited: {
            root.places = [];
            SystemBridge.refresh();
            weatherSoon.restart();
        }
    }
    property Timer weatherSoon: Timer {
        interval: 600
        onTriggered: root.refreshWeather()
    }
    property Timer statsTimer: Timer {
        interval: 3000
        repeat: true
        running: root.has("system")
        triggeredOnStart: true
        onTriggered: root.refreshStats()
    }
    // The bridge caches for 15 minutes, so polling every 5 is cheap and prompt.
    property Timer weatherTimer: Timer {
        interval: 300000
        repeat: true
        running: root.weatherConfigured && (root.has("weather") || root.has("glance"))
        triggeredOnStart: true
        onTriggered: root.refreshWeather()
    }
}
