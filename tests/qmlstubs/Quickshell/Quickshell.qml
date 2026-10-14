pragma Singleton
import QtQuick

// Stand-in for the Quickshell singleton. Only the surface PrismOS uses.
QtObject {
    id: root
    property var screens: Harness.screens
    function shellPath(relative) {
        return Qt.resolvedUrl(Harness.shellDir + "/" + relative);
    }
    function iconPath(name, fallback) {
        return Harness.iconPath(name, fallback || "");
    }
}
