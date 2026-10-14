pragma Singleton
import QtQuick
import Quickshell.Services.Notifications

QtObject {
    id: root
    readonly property var items: server.trackedNotifications
    readonly property int limit: 50
    property NotificationServer server: NotificationServer {
        bodySupported: true
        bodyMarkupSupported: false
        actionsSupported: true
        persistenceSupported: true
        onNotification: function (notification) {
            notification.tracked = true;
            const current = Array.from(root.items.values);
            if (current.length > root.limit) {
                const oldest = current.find(item => item !== notification && item.urgency !== NotificationUrgency.Critical) || current[0];
                oldest.dismiss();
            }
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
