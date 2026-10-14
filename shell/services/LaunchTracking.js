.pragma library

function normalize(value) { return String(value || "").trim().toLowerCase(); }

function matches(app, windowClass) {
    const candidate = normalize(windowClass);
    if (!app || !candidate) return false;
    const id = normalize(app.id).replace(/\.desktop$/, "");
    const classes = [normalize(app.startupClass), id];
    // Reverse-DNS desktop IDs often use their last segment as the Wayland app ID.
    if (id.includes(".")) classes.push(id.split(".").pop());
    return classes.filter(Boolean).includes(candidate);
}

function eventClass(name, data) {
    // Limit parsing to fields before the window title, which may contain commas.
    const values = String(data).split(",");
    if (name === "openwindow" && values.length >= 4) return values[2];
    if (name === "activewindow" && values.length >= 2) return values[0];
    return "";
}
