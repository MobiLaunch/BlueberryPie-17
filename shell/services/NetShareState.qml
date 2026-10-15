pragma Singleton
import QtQuick
import Quickshell.Io

// Hotspot details (network name and password) and VPN profiles, read from the bridge only
// while a details panel is open. The hotspot password is held here just long enough to
// show it and is cleared again when the panel closes.
QtObject {
    id: root
    property var hotspot: ({
            loaded: false,
            ssid: "",
            password: "",
            enabled: false
        })
    property bool revealed: false
    property var vpn: ({
            loaded: false,
            profiles: [],
            preferred: ""
        })
    property string notice: ""
    property string error: ""
    readonly property bool busy: hotspotReader.running || vpnReader.running || hotspotWriter.running || vpnWriter.running

    function refreshHotspot() {
        hotspotOpen = true;
        if (!hotspotReader.running)
            hotspotReader.running = true;
    }
    function refreshVpn() {
        if (!vpnReader.running)
            vpnReader.running = true;
    }
    property bool hotspotOpen: false
    function refreshHotspotIfOpen() {
        if (hotspotOpen)
            refreshHotspot();
    }
    // Forget the password the moment nothing is showing it.
    function closeHotspot() {
        hotspotOpen = false;
        revealed = false;
        hotspot = Object.assign({}, hotspot, {
            password: ""
        });
    }
    function setHotspot(change) {
        if (hotspotWriter.running)
            return;
        error = "";
        notice = "";
        pendingChange = change;
        hotspotWriter.command = ["prismctl", "hotspot", "set"];
        hotspotWriter.stdinEnabled = true;
        hotspotWriter.running = true;
    }
    property var pendingChange: ({})
    function regeneratePassword() {
        setHotspot({
            regenerate: true
        });
    }
    function copyPassword() {
        if (!copier.running) {
            copier.running = true;
            notice = "Password copied";
        }
    }
    function chooseVpn(uuid) {
        runVpn(["choose", uuid]);
    }
    function connectVpn(uuid) {
        runVpn(["connect", uuid]);
    }
    function disconnectVpn(uuid) {
        runVpn(["disconnect", uuid]);
    }
    function runVpn(args) {
        if (vpnWriter.running)
            return;
        error = "";
        vpnWriter.command = ["prismctl", "vpn"].concat(args);
        vpnWriter.running = true;
    }
    function parse(text, onOk) {
        try {
            const data = JSON.parse(text);
            if (data.ok === false)
                root.error = data.error;
            else
                onOk(data);
        } catch (e) {
            root.error = "The network service did not respond";
        }
    }
    property Process hotspotReader: Process {
        command: ["prismctl", "hotspot", "info"]
        stdout: StdioCollector {
            onStreamFinished: root.parse(text, data => {
                root.hotspot = {
                    loaded: true,
                    ssid: data.ssid,
                    // A reply that lands after the panel closed must not bring the password back.
                    password: root.hotspotOpen ? data.password : "",
                    enabled: data.enabled
                };
            })
        }
    }
    property Process hotspotWriter: Process {
        onStarted: {
            // The private pipe keeps names and passwords out of the process list.
            write(JSON.stringify(root.pendingChange) + "\n");
            stdinEnabled = false;
        }
        stdout: StdioCollector {
            onStreamFinished: root.parse(text, data => {
                root.hotspot = {
                    loaded: true,
                    ssid: data.ssid,
                    // A reply that lands after the panel closed must not bring the password back.
                    password: root.hotspotOpen ? data.password : "",
                    enabled: data.enabled
                };
                root.notice = data.restart_needed ? "Applies the next time the hotspot is turned on" : "Saved";
            })
        }
    }
    property Process copier: Process {
        command: ["prismctl", "hotspot", "copy-password"]
        stdout: StdioCollector {
            onStreamFinished: root.parse(text, () => {})
        }
    }
    property Process vpnReader: Process {
        command: ["prismctl", "vpn", "list"]
        stdout: StdioCollector {
            onStreamFinished: root.parse(text, data => {
                root.vpn = {
                    loaded: true,
                    profiles: data.profiles,
                    preferred: data.preferred
                };
            })
        }
    }
    property Process vpnWriter: Process {
        stdout: StdioCollector {
            onStreamFinished: root.parse(text, data => {
                root.refreshVpn();
                SystemBridge.refresh();
            })
        }
    }
}
