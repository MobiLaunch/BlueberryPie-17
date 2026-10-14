pragma Singleton
import QtQuick

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
