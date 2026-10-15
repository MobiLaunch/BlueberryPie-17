pragma Singleton
import QtQuick

// Quick Settings tile catalog, the user's order, and each tile's live state.
QtObject {
    id: root
    readonly property var catalog: [
        {
            id: "wifi",
            title: "Wi-Fi",
            large: true
        },
        {
            id: "bluetooth",
            title: "Bluetooth",
            large: true
        },
        {
            id: "sound",
            title: "Sound",
            large: true
        },
        {
            id: "microphone",
            title: "Microphone",
            large: true
        },
        {
            id: "dnd",
            title: "Do Not Disturb",
            large: false
        },
        {
            id: "dark",
            title: "Dark theme",
            large: false
        },
        {
            id: "reduced_motion",
            title: "Reduced motion",
            large: false
        },
        {
            id: "audio_devices",
            title: "Audio devices",
            large: false
        },
        {
            id: "airplane",
            title: "Airplane mode",
            large: false
        },
        {
            id: "battery_saver",
            title: "Battery Saver",
            large: false
        },
        {
            id: "night_light",
            title: "Night Light",
            large: false
        },
        {
            id: "screenshot",
            title: "Screenshot",
            large: false
        },
        {
            id: "lock",
            title: "Lock screen",
            large: false
        },
        {
            id: "hotspot",
            title: "Hotspot",
            large: false
        },
        {
            id: "vpn",
            title: "VPN",
            large: false
        },
        {
            id: "screen_record",
            title: "Screen record",
            large: false
        },
        {
            id: "focus",
            title: "Focus mode",
            large: false
        }
    ]
    readonly property var defaults: ["wifi", "bluetooth", "sound", "microphone", "dnd", "dark", "reduced_motion", "audio_devices"]
    readonly property var chosen: SystemBridge.snapshot.settings.tiles
    readonly property var enabled: Array.isArray(chosen) && chosen.length > 0 ? chosen : defaults
    // Shown tiles in the saved order, then the hidden ones in catalog order (for the editor).
    readonly property var arranged: enabled.concat(catalog.map(item => item.id).filter(id => enabled.indexOf(id) < 0))

    // Compact tiles that open an inline details panel (long-press or right-click).
    readonly property var detailTiles: ["night_light", "battery_saver", "screenshot", "dnd", "dark", "hotspot", "vpn", "screen_record"]
    function entry(id) {
        return catalog.find(item => item.id === id) || {
            id: id,
            title: id,
            large: false
        };
    }
    function describe(id) {
        const s = SystemBridge.snapshot;
        const base = entry(id);
        const off = {
            enabled: true,
            subtitle: "",
            activated: false,
            hasDetails: false
        };
        switch (id) {
        case "wifi":
            return {
                title: base.title,
                large: true,
                subtitle: s.wifi.available ? s.wifi.label : "Unavailable",
                symbol: s.wifi.enabled ? "wifi" : "wifi_off",
                activated: s.wifi.enabled,
                enabled: s.wifi.available,
                hasDetails: true
            };
        case "bluetooth":
            return {
                title: base.title,
                large: true,
                subtitle: s.bluetooth.available ? (s.bluetooth.enabled ? "On" : "Off") : "Unavailable",
                symbol: s.bluetooth.enabled ? "bluetooth" : "bluetooth_off",
                activated: s.bluetooth.enabled,
                enabled: s.bluetooth.available,
                hasDetails: true
            };
        case "sound":
            return {
                title: base.title,
                large: true,
                subtitle: !s.volume.available ? "Unavailable" : s.volume.muted ? "Muted" : s.volume.value + "%",
                symbol: s.volume.muted ? "volume_off" : "volume",
                activated: !s.volume.muted,
                enabled: s.volume.available && !AudioState.writing,
                hasDetails: true
            };
        case "microphone":
            return {
                title: base.title,
                large: true,
                subtitle: s.microphone.available ? (s.microphone.muted ? "Muted" : "On") : "Unavailable",
                symbol: s.microphone.muted ? "microphone_off" : "microphone",
                activated: s.microphone.available && !s.microphone.muted,
                enabled: s.microphone.available && !AudioState.writing,
                hasDetails: true
            };
        case "dnd":
            return {
                title: base.title,
                large: false,
                subtitle: s.settings.dnd ? "On" : Notifications.quietHours ? "Until " + Notifications.schedule.end : "Off",
                symbol: Notifications.quiet ? "notifications_off" : "dnd",
                activated: Notifications.quiet,
                enabled: true,
                hasDetails: true
            };
        case "dark":
            return {
                title: base.title,
                large: false,
                subtitle: Theme.dark ? "On" : "Off",
                symbol: "moon",
                activated: Theme.dark,
                enabled: true,
                hasDetails: true
            };
        case "reduced_motion":
            return {
                title: base.title,
                large: false,
                subtitle: Theme.reducedMotion ? "On" : "Off",
                symbol: "motion",
                activated: Theme.reducedMotion,
                enabled: true,
                hasDetails: false
            };
        case "audio_devices":
            return {
                title: base.title,
                large: false,
                subtitle: "",
                symbol: "headphones",
                activated: false,
                enabled: true,
                hasDetails: false
            };
        case "airplane":
            return {
                title: base.title,
                large: false,
                subtitle: s.airplane.enabled ? "On" : "Off",
                symbol: "airplane",
                activated: s.airplane.enabled,
                enabled: s.airplane.available,
                hasDetails: false
            };
        case "battery_saver":
            return {
                title: base.title,
                large: false,
                subtitle: !s.profile.available ? "Unavailable" : s.profile.saver ? "On" : "Off",
                symbol: "battery",
                activated: s.profile.saver === true,
                enabled: s.profile.available,
                hasDetails: true
            };
        case "night_light":
            return {
                title: base.title,
                large: false,
                subtitle: !s.night_light.available ? "Needs hyprsunset" : s.night_light.enabled ? "On" : "Off",
                symbol: "night_light",
                activated: s.night_light.enabled,
                enabled: s.night_light.available,
                hasDetails: true
            };
        case "screenshot":
            return {
                title: base.title,
                large: false,
                subtitle: "",
                symbol: "screenshot",
                activated: false,
                enabled: true,
                hasDetails: true
            };
        case "hotspot":
            return {
                title: base.title,
                large: false,
                subtitle: !s.hotspot.available ? "Unavailable" : s.hotspot.enabled ? (s.hotspot.ssid || "On") : "Off",
                symbol: "hotspot",
                activated: s.hotspot.enabled === true,
                enabled: s.hotspot.available === true,
                hasDetails: true
            };
        case "vpn":
            return {
                title: base.title,
                large: false,
                subtitle: !s.vpn.available ? "None set up" : s.vpn.enabled ? s.vpn.label : "Off",
                symbol: "vpn",
                activated: s.vpn.enabled === true,
                // Without a profile the tile stays tappable: its details explain how to add one.
                enabled: true,
                hasDetails: true
            };
        case "screen_record":
            return {
                title: base.title,
                large: false,
                subtitle: !s.recording.available ? "Needs wf-recorder" : s.recording.recording ? "Recording" : "Off",
                symbol: s.recording.recording ? "stop" : "record",
                activated: s.recording.recording === true,
                enabled: s.recording.available === true,
                hasDetails: true
            };
        case "focus":
            return {
                title: base.title,
                large: false,
                subtitle: s.settings.focus ? Notifications.focusApps.length + (Notifications.focusApps.length === 1 ? " app paused" : " apps paused") : Notifications.focusApps.length === 0 ? "Choose apps" : "Off",
                symbol: "focus",
                activated: s.settings.focus === true,
                enabled: true,
                hasDetails: false
            };
        case "lock":
            return {
                title: base.title,
                large: false,
                subtitle: "",
                symbol: "lock",
                activated: false,
                enabled: s.power.lock,
                hasDetails: false
            };
        default:
            return {
                title: base.title,
                large: false,
                subtitle: "",
                symbol: "spark",
                activated: false,
                enabled: false,
                hasDetails: false
            };
        }
    }
    function symbolFor(id) {
        return describe(id).symbol;
    }
    function save(ids) {
        SystemBridge.setTiles(ids);
    }
    function show(id, visible) {
        const current = enabled.slice();
        const index = current.indexOf(id);
        if (visible && index < 0)
            current.push(id);
        else if (!visible && index >= 0 && current.length > 1)
            current.splice(index, 1);
        else
            return;
        save(current);
    }
    function move(id, delta) {
        const current = enabled.slice();
        const index = current.indexOf(id);
        const target = index + delta;
        if (index < 0 || target < 0 || target >= current.length)
            return;
        current.splice(index, 1);
        current.splice(target, 0, id);
        save(current);
    }
    function reset() {
        SystemBridge.resetTiles();
    }
}
