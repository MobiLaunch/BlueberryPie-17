.pragma library

// Rank emoji for a picker query over the generated EmojiData entries
// ([emoji, label, tags, group]). A label that starts with the query beats a word
// that starts with it, which beats a substring of the label, which beats a tag.
// Ties go to the shorter label (the plain "red heart" before "heart with ribbon"), then
// keep the Unicode order, which is also the order people expect to browse in.
function score(entry, query) {
    if (!query)
        return 1;
    const label = entry[1].toLowerCase();
    if (label.startsWith(query))
        return 5;
    if (label.split(/[\s:,\-]+/).some(word => word.startsWith(query)))
        return 4;
    if (label.includes(query))
        return 3;
    const tags = entry[2].split(" ");
    if (tags.indexOf(query) >= 0)
        return 3;
    if (tags.some(tag => tag.startsWith(query)))
        return 2;
    return entry[2].includes(query) ? 1 : 0;
}

function search(entries, query, group) {
    const needle = String(query || "").trim().toLowerCase();
    const wanted = group === undefined || group === null || group < 0 ? -1 : group;
    const result = [];
    for (let i = 0; i < entries.length; i++) {
        const entry = entries[i];
        if (needle === "" && wanted >= 0 && entry[3] !== wanted)
            continue;
        const value = score(entry, needle);
        if (value > 0)
            result.push({entry: entry, score: value, position: i});
    }
    if (needle !== "")
        result.sort((a, b) => b.score - a.score || a.entry[1].length - b.entry[1].length || a.position - b.position);
    return result.map(item => item.entry);
}

// The entries for emoji strings the person used lately, newest first, skipping any
// that this list does not know (for example from a newer Unicode version).
function recents(entries, used) {
    const known = {};
    for (const entry of entries)
        known[entry[0]] = entry;
    return used.map(emoji => known[emoji]).filter(entry => entry !== undefined);
}
