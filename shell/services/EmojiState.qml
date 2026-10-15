pragma Singleton
import QtQuick
import Quickshell.Io
import "EmojiData.js" as EmojiData
import "EmojiSearch.js" as EmojiSearch

// Emoji picker state: the recently used list (kept by the bridge) and copying one to the clipboard.
QtObject {
    id: root
    property var used: SystemBridge.snapshot.settings.recent_emoji || []
    readonly property var recents: EmojiSearch.recents(EmojiData.entries, used)
    property string pending: ""

    function copy(text) {
        if (copier.running)
            return false;
        pending = text;
        copier.command = ["prismctl", "emoji", "copy", text];
        copier.running = true;
        return true;
    }
    property Process copier: Process {
        stdout: StdioCollector {
            onStreamFinished: {
                const emoji = root.pending;
                root.pending = "";
                try {
                    const result = JSON.parse(text);
                    if (result.ok) {
                        ShellState.close();
                        ShellState.showToast("Copied " + emoji + " — paste it with Ctrl+V");
                        SystemBridge.refresh();
                    } else {
                        ShellState.showToast(result.error || "Could not copy the emoji");
                    }
                } catch (e) {
                    ShellState.showToast("Could not copy the emoji");
                }
            }
        }
    }
}
