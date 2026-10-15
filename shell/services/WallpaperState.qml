pragma Singleton
import QtQuick
import Quickshell.Io

// Wallpaper choices from ~/Pictures. Choosing one also derives the accent color.
QtObject {
    id: root
    property var items: []
    property bool busy: reader.running || writer.running
    property string error: ""
    readonly property string current: SystemBridge.snapshot.settings.wallpaper || ""
    // file:// URL with each path segment percent-encoded (spaces, #, ? are safe).
    function fileUrl(path) {
        return path ? "file://" + path.split("/").map(part => encodeURIComponent(part)).join("/") : "";
    }
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function choose(path) {
        if (writer.running)
            return;
        error = "";
        writer.command = ["prismctl", "wallpaper", "set", path];
        writer.running = true;
    }
    function clear() {
        if (writer.running)
            return;
        error = "";
        writer.command = ["prismctl", "wallpaper", "clear"];
        writer.running = true;
    }
    property Process reader: Process {
        command: ["prismctl", "wallpaper", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.ok)
                        root.items = data.items || [];
                } catch (e) {
                    root.error = "Could not read your pictures";
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
                    root.error = "The wallpaper could not be changed";
                }
            }
        }
        onExited: SystemBridge.refresh()
    }
}
