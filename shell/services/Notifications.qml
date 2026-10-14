pragma Singleton
import QtQuick
import Quickshell.Services.Notifications

QtObject {
    id: root
    readonly property var items: server.trackedNotifications
    property NotificationServer server: NotificationServer {
        bodySupported: true
        bodyMarkupSupported: false
        persistenceSupported: true
        onNotification: function (notification) {
            notification.tracked = true;
            if (!SystemBridge.snapshot.settings.dnd) {
                ShellState.toast = notification.summary;
                clearToast.restart();
            }
        }
    }
    property Timer clearToast: Timer {
        interval: 5000
        onTriggered: ShellState.toast = ""
    }
    function clear() {
        // Copy before dismissing: trackedNotifications changes during iteration.
        const items = server.trackedNotifications.values.slice();
        items.forEach(item => item.dismiss());
    }
}
