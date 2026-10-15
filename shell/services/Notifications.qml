pragma Singleton
import QtQuick
import Quickshell.Services.Notifications

QtObject {
    id: root
    readonly property var items: server.trackedNotifications
    readonly property int limit: 50
    // Newest first, grouped by sending app. Rebuilt whenever the tracked set changes.
    readonly property var groups: {
        const byApp = {};
        const order = [];
        for (const note of items.values.slice().reverse()) {
            const key = note.appName || "Other";
            if (!byApp[key]) {
                byApp[key] = {
                    app: key,
                    items: []
                };
                order.push(key);
            }
            byApp[key].items.push(note);
        }
        return order.map(key => byApp[key]);
    }
    readonly property int count: items.values.length
    // Apps that have sent something this session (for the per-app switches in Settings).
    property var seenApps: []
    readonly property var mutedApps: SystemBridge.snapshot.settings.muted_apps || []
    function noteApp(name) {
        if (name && seenApps.indexOf(name) < 0)
            seenApps = seenApps.concat([name]).slice(-30);
    }
    function isMuted(name) {
        return mutedApps.indexOf(name || "Other") >= 0;
    }
    property NotificationServer server: NotificationServer {
        bodySupported: true
        bodyMarkupSupported: false
        actionsSupported: true
        persistenceSupported: true
        onNotification: function (notification) {
            root.noteApp(notification.appName);
            // Muted apps are dropped; critical alerts still get through.
            if (root.isMuted(notification.appName) && notification.urgency !== NotificationUrgency.Critical) {
                notification.dismiss();
                return;
            }
            notification.tracked = true;
            const current = Array.from(root.items.values);
            if (current.length > root.limit) {
                const oldest = current.find(item => item !== notification && item.urgency !== NotificationUrgency.Critical) || current[0];
                oldest.dismiss();
            }
            // Banner unless Do Not Disturb is on; important ones always break through.
            if (!SystemBridge.snapshot.settings.dnd || notification.urgency === NotificationUrgency.Critical) {
                root.headsUp = notification;
                headsUpTimer.interval = notification.urgency === NotificationUrgency.Critical ? 12000 : 6000;
                headsUpTimer.restart();
            }
        }
    }
    // The notification currently shown as a banner, or null.
    property var headsUp: null
    property Timer headsUpTimer: Timer {
        onTriggered: root.headsUp = null
    }
    property Connections headsUpWatch: Connections {
        target: root.headsUp
        ignoreUnknownSignals: true
        function onClosed() {
            root.headsUp = null;
        }
    }
    function clear() {
        headsUp = null;
        // Copy before dismissing: trackedNotifications changes during iteration.
        const items = server.trackedNotifications.values.slice();
        items.forEach(item => item.dismiss());
    }
}
