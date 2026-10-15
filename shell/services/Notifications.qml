pragma Singleton
import QtQuick
import Quickshell.Services.Notifications

QtObject {
    id: root
    readonly property var items: server.trackedNotifications
    readonly property int limit: 50
    // Snoozed notifications leave the shade until their time is up; the sender's own notification
    // stays alive, so replies and actions keep working when it comes back.
    property var snoozed: ({})
    property real snoozeNow: Date.now()
    function isSnoozed(note) {
        const until = snoozed[note.id];
        return until !== undefined && until > snoozeNow;
    }
    readonly property var visibleItems: {
        const hidden = snoozed, stamp = snoozeNow;
        return items.values.filter(note => !(hidden[note.id] !== undefined && hidden[note.id] > stamp));
    }
    function snooze(note, minutes) {
        const next = Object.assign({}, snoozed);
        next[note.id] = Date.now() + minutes * 60000;
        snoozed = next;
        snoozeNow = Date.now();
        if (headsUp === note)
            headsUp = null;
    }
    property Timer snoozeClock: Timer {
        interval: 2000
        repeat: true
        running: Object.keys(root.snoozed).length > 0
        onTriggered: {
            root.snoozeNow = Date.now();
            const next = {};
            let due = null;
            for (const key in root.snoozed) {
                if (root.snoozed[key] > root.snoozeNow)
                    next[key] = root.snoozed[key];
                else
                    due = root.items.values.find(note => String(note.id) === key) || due;
            }
            root.snoozed = next;
            // Back again, like a new arrival: a banner unless Do Not Disturb is on.
            if (due && !root.quiet) {
                root.headsUp = due;
                headsUpTimer.interval = 6000;
                headsUpTimer.restart();
            }
        }
    }
    // Newest first, grouped by sending app. Rebuilt whenever the tracked set changes.
    readonly property var groups: {
        const byApp = {};
        const order = [];
        for (const note of visibleItems.slice().reverse()) {
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
    readonly property int count: visibleItems.length
    // The lock screen shows how many are waiting (a number only, never any text).
    onCountChanged: lockCountTimer.restart()
    Component.onCompleted: lockCountTimer.restart()
    property Timer lockCountTimer: Timer {
        interval: 400
        onTriggered: SystemBridge.setLockNotificationCount(root.count)
    }
    // Quiet hours: Do Not Disturb turns itself on between two times (may span midnight).
    readonly property var schedule: SystemBridge.snapshot.settings.dnd_schedule || {
        enabled: false,
        start: "22:00",
        end: "07:00"
    }
    property real minuteStamp: Date.now()
    function minutes(text) {
        return parseInt(text.slice(0, 2)) * 60 + parseInt(text.slice(3, 5));
    }
    readonly property bool quietHours: {
        const stamp = minuteStamp;
        if (!schedule.enabled)
            return false;
        const date = new Date(stamp);
        const now = date.getHours() * 60 + date.getMinutes();
        const from = minutes(schedule.start), to = minutes(schedule.end);
        return from === to ? false : from < to ? (now >= from && now < to) : (now >= from || now < to);
    }
    readonly property bool quiet: SystemBridge.snapshot.settings.dnd === true || quietHours
    property Timer quietClock: Timer {
        interval: 30000
        repeat: true
        running: root.schedule.enabled
        onTriggered: root.minuteStamp = Date.now()
    }
    // Opt-in notification history. Kept in memory only: it is never written to disk and
    // is dropped when the shell restarts or the setting is turned off.
    readonly property bool historyEnabled: SystemBridge.snapshot.settings.notification_history === true
    readonly property int historyLimit: 100
    property var history: []
    property int historySerial: 0
    onHistoryEnabledChanged: if (!historyEnabled)
        history = []
    function record(notification) {
        if (!historyEnabled)
            return;
        historySerial++;
        const entry = {
            id: historySerial,
            app: notification.appName || "Other",
            summary: String(notification.summary || "").slice(0, 200),
            body: String(notification.body || "").slice(0, 400),
            critical: notification.urgency === NotificationUrgency.Critical,
            time: Date.now()
        };
        history = [entry].concat(history).slice(0, historyLimit);
    }
    function clearHistory() {
        history = [];
    }
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
        inlineReplySupported: true
        onNotification: function (notification) {
            root.noteApp(notification.appName);
            // Muted apps are dropped; critical alerts still get through.
            if (root.isMuted(notification.appName) && notification.urgency !== NotificationUrgency.Critical) {
                notification.dismiss();
                return;
            }
            root.record(notification);
            notification.tracked = true;
            const current = Array.from(root.items.values);
            if (current.length > root.limit) {
                const oldest = current.find(item => item !== notification && item.urgency !== NotificationUrgency.Critical) || current[0];
                oldest.dismiss();
            }
            // Banner unless Do Not Disturb is on; important ones always break through.
            if (!root.quiet || notification.urgency === NotificationUrgency.Critical) {
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
        snoozed = ({});
        // Copy before dismissing: trackedNotifications changes during iteration.
        const items = server.trackedNotifications.values.slice();
        items.forEach(item => item.dismiss());
    }
}
