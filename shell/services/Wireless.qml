pragma Singleton
import QtQuick
import Quickshell.Io

QtObject {
    id: root
    property var wifi: ({
            available: false,
            enabled: false,
            networks: []
        })
    property var bluetooth: ({
            available: false,
            enabled: false,
            devices: []
        })
    property string error: ""
    property string notice: ""
    property string operation: ""
    property string operationKind: ""
    property string secret: ""
    property bool responded: false
    property string watchedKind: ""
    property bool editing: false
    property var pendingRead: null
    readonly property bool busy: wifiReader.running || bluetoothReader.running || writer.running

    function refresh(kind, scan = false, clearError = true) {
        if (busy || editing) {
            pendingRead = {
                kind: kind,
                scan: scan,
                clearError: clearError
            };
            return;
        }
        if (clearError)
            error = "";
        if (kind === "wifi") {
            wifiReader.command = ["prismctl", "wifi", scan ? "scan" : "list"];
            wifiReader.running = true;
        } else {
            bluetoothReader.command = ["prismctl", "bluetooth", scan ? "scan" : "list"];
            bluetoothReader.running = true;
        }
    }
    function execute(kind, name, args, password = "") {
        if (busy)
            return false;
        error = "";
        notice = "";
        operationKind = kind;
        operation = name;
        secret = password;
        responded = false;
        writer.command = args;
        writer.stdinEnabled = true;
        writer.running = true;
        return true;
    }
    function connectWifi(network, password) {
        return execute("wifi", "connect", ["prismctl", "wifi", "connect", "--bssid", network.bssid, "--interface", network.interface, "--password-stdin"], password);
    }
    function disconnectWifi(network) {
        return execute("wifi", "disconnect", ["prismctl", "wifi", "disconnect", "--interface", network.interface]);
    }
    function deviceAction(device) {
        const action = device.connected ? "disconnect" : "connect";
        return execute("bluetooth", action, ["prismctl", "bluetooth", action, device.address]);
    }
    property Process wifiReader: Process {
        onExited: readAgain.restart()
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.wifi = data;
                } catch (e) {
                    root.error = "Could not read available networks";
                }
            }
        }
    }
    property Process bluetoothReader: Process {
        onExited: readAgain.restart()
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.bluetooth = data;
                } catch (e) {
                    root.error = "Could not read Bluetooth devices";
                }
            }
        }
    }
    property Process writer: Process {
        onStarted: {
            // QProcess's private stdin pipe keeps passwords out of process argv.
            write(JSON.stringify({
                password: root.secret
            }) + "\n");
            root.secret = "";
            stdinEnabled = false;
        }
        stdout: StdioCollector {
            onStreamFinished: {
                root.responded = true;
                try {
                    const data = JSON.parse(text);
                    if (data.ok === false)
                        root.error = data.error;
                    else
                        root.notice = data.warning || (root.operation === "connect" ? "Connected" : "Disconnected");
                } catch (e) {
                    root.error = "The connection action did not respond";
                }
            }
        }
        onExited: {
            root.secret = "";
            if (!root.responded && !root.error)
                root.error = "The connection action could not start";
            SystemBridge.refresh();
            refreshAfterWrite.restart();
        }
    }
    property Timer refreshAfterWrite: Timer {
        interval: 100
        onTriggered: {
            root.refresh(root.operationKind, false, false);
        }
    }
    property Timer readAgain: Timer {
        interval: 100
        onTriggered: {
            if (!root.pendingRead)
                return;
            const request = root.pendingRead;
            root.pendingRead = null;
            root.refresh(request.kind, request.scan, request.clearError);
        }
    }
    onEditingChanged: if (!editing && pendingRead)
        readAgain.restart()
    property Timer refreshVisiblePanel: Timer {
        interval: 8000
        running: root.watchedKind.length > 0
        repeat: true
        onTriggered: root.refresh(root.watchedKind, false, false)
    }
}
