.pragma library

function createState() {
    return {buffer: "", depth: 0, quoted: false, escaped: false, nodes: {}, metadata: {}};
}

function relevant(state, rows) {
    if (!Array.isArray(rows)) return false;
    let changed = false;
    for (const row of rows) {
        if (!row || typeof row !== "object" || !Number.isInteger(row.id)) continue;
        const id = String(row.id);
        if (row.info === null) {
            if (state.nodes[id] || state.metadata[id]) changed = true;
            delete state.nodes[id]; delete state.metadata[id];
            continue;
        }
        const props = row.info?.props || row.props || {};
        if (row.type === "PipeWire:Interface:Node") {
            const media = props["media.class"];
            if (media === "Audio/Sink" || media === "Audio/Source") {
                state.nodes[id] = true; changed = true;
            } else if (state.nodes[id]) {
                changed = true;
                if (media !== undefined) delete state.nodes[id];
            }
        }
        if (row.type === "PipeWire:Interface:Metadata") {
            if (props["metadata.name"] === "default") state.metadata[id] = true;
            if (state.metadata[id] && Array.isArray(row.metadata) && row.metadata.some(entry => entry &&
                (entry.key === "default.audio.sink" || entry.key === "default.audio.source"))) changed = true;
        }
    }
    return changed;
}

// pw-dump emits a sequence of formatted JSON arrays, not JSON Lines. Keep
// incremental framing across reads and ignore client/port churn from our queries.
function feed(state, chunk) {
    let changed = false;
    for (const char of String(chunk)) {
        if (state.depth === 0 && /\s/.test(char)) continue;
        if (state.depth === 0 && char !== "[") throw new Error("Invalid PipeWire event frame");
        state.buffer += char;
        if (state.buffer.length > 8 * 1024 * 1024) throw new Error("PipeWire event frame too large");
        if (state.quoted) {
            if (state.escaped) state.escaped = false;
            else if (char === "\\") state.escaped = true;
            else if (char === '"') state.quoted = false;
        } else if (char === '"') state.quoted = true;
        else if (char === "[" || char === "{") state.depth++;
        else if (char === "]" || char === "}") state.depth--;
        if (state.depth === 0) {
            changed = relevant(state, JSON.parse(state.buffer)) || changed;
            state.buffer = "";
        }
    }
    return changed;
}
