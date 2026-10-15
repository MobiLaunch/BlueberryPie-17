.pragma library

// When does the next enabled alarm ring? Days are 0 (Monday) to 6 (Sunday); an empty list means once.
function nextOccurrence(alarms, nowMs) {
    const now = new Date(nowMs);
    let best = null;
    for (const alarm of alarms || []) {
        if (!alarm.enabled || !/^\d\d:\d\d$/.test(alarm.time))
            continue;
        const hour = parseInt(alarm.time.slice(0, 2)), minute = parseInt(alarm.time.slice(3, 5));
        for (let ahead = 0; ahead <= 7; ahead++) {
            const when = new Date(now.getFullYear(), now.getMonth(), now.getDate() + ahead, hour, minute, 0, 0);
            const weekday = (when.getDay() + 6) % 7;
            if (when.getTime() <= nowMs || (alarm.days.length > 0 && alarm.days.indexOf(weekday) < 0))
                continue;
            if (best === null || when.getTime() < best.at)
                best = {id: alarm.id, at: when.getTime(), label: alarm.label || ""};
            break;
        }
    }
    return best;
}

// "07:30" today, "Tomorrow 07:30", or "Mon 07:30". `formatTime(date)` supplies the clock text.
function describe(occurrence, nowMs, formatTime) {
    if (!occurrence)
        return "";
    const when = new Date(occurrence.at), now = new Date(nowMs);
    const startOf = date => new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
    const days = Math.round((startOf(when) - startOf(now)) / 86400000);
    const time = formatTime(when);
    if (days === 0)
        return time;
    if (days === 1)
        return "Tomorrow " + time;
    return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][when.getDay()] + " " + time;
}
