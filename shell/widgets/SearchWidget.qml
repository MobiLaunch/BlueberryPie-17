import QtQuick
import "../components"
import "../services"

// Search pill: Enter opens the launcher with the query; the launcher offers the
// web as a fallback, so typing here never silently leaves the machine.
SearchField {
    id: root
    property var screen: null
    implicitWidth: 420
    placeholderText: "Search apps, then the web"
    onAccepted: {
        if (text.trim().length) {
            const query = text.trim();
            text = "";
            ShellState.openLauncher(root.screen, query);
        }
    }
    onEscaped: text = ""
    onDownPressed: ShellState.openLauncher(root.screen, text.trim())
}
