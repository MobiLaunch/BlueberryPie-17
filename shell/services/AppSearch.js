.pragma library

// Rank installed applications for a launcher query.
// Prefix of the name beats a word prefix, which beats a substring, which beats
// a match in the description or keywords. Ties sort alphabetically.
function score(app, query) {
    const name = String(app.name || "").toLowerCase();
    if (!query)
        return 1;
    if (name.startsWith(query))
        return 4;
    if (name.split(/[\s\-_.]+/).some(word => word.startsWith(query)))
        return 3;
    if (name.includes(query))
        return 2;
    const haystack = (String(app.description || "") + " " + String(app.keywords || "") + " " + String(app.id || "")).toLowerCase();
    return haystack.includes(query) ? 1 : 0;
}

function rank(apps, query, category) {
    const needle = String(query || "").trim().toLowerCase();
    return apps
        .filter(app => !category || category === "All" || app.category === category)
        .map(app => ({app: app, score: score(app, needle)}))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score || String(a.app.name).localeCompare(String(b.app.name), undefined, {sensitivity: "base"}))
        .map(item => item.app);
}

// Category chips in a stable, friendly order; only categories that have apps.
const ORDER = ["Internet", "Media", "Games", "Office", "Develop", "Education", "Utilities", "System", "Other"];

function categories(apps) {
    const present = new Set(apps.map(app => app.category || "Other"));
    return ["All"].concat(ORDER.filter(name => present.has(name)));
}

function recents(apps, ids, limit) {
    const byId = {};
    apps.forEach(app => byId[app.id] = app);
    return (ids || []).map(id => byId[id]).filter(app => app !== undefined).slice(0, limit || 6);
}
