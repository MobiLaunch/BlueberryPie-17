pragma Singleton
import QtQuick
import "LaunchTracking.js" as LaunchTracking

QtObject {
    readonly property var installed: SystemBridge.apps
    readonly property var favoriteIds: {
        const saved = SystemBridge.snapshot.settings.favorites;
        if (Array.isArray(saved))
            return saved;
        const selected = [];
        const groups = [["firefox", "chromium"], ["thunar", "files", "dolphin"], ["foot", "terminal", "konsole"]];
        groups.forEach(names => {
            let match = null;
            for (const name of names) {
                match = installed.find(app => app.name.toLowerCase() === name || app.name.toLowerCase().startsWith(name + " ") || app.id.toLowerCase() === name + ".desktop" || app.id.toLowerCase().endsWith("." + name + ".desktop"));
                if (match)
                    break;
            }
            if (match && !selected.includes(match.id))
                selected.push(match.id);
        });
        return selected;
    }
    readonly property var dockApps: favoriteIds.map(id => installed.find(app => app.id === id)).filter(app => app !== undefined)
    // Windows whose app is not pinned, grouped per app, for the dock's running section.
    readonly property var extraRunning: {
        const seen = {};
        const result = [];
        for (const window of Windows.list) {
            if (dockApps.some(app => LaunchTracking.matches(app, window.class)))
                continue;
            if (seen[window.class]) {
                seen[window.class].windows.push(window);
                continue;
            }
            const match = installed.find(app => LaunchTracking.matches(app, window.class));
            const entry = {
                id: match ? match.id : "",
                name: match ? match.name : window.class,
                icon: match ? match.icon : window.class.toLowerCase(),
                startupClass: match ? match.startupClass : window.class,
                windows: [window]
            };
            seen[window.class] = entry;
            result.push(entry);
        }
        return result;
    }
    function isPinned(id) {
        return favoriteIds.includes(id);
    }
    function togglePin(id) {
        SystemBridge.favorite(isPinned(id) ? "unpin" : "pin", id);
    }
    function badgeCount(id) {
        const base = id.replace(/\.desktop$/, "");
        return Notifications.items.values.filter(note => note.desktopEntry.replace(/\.desktop$/, "") === base).length;
    }
}
