pragma Singleton
import QtQuick

// Timer and stopwatch state. They keep running while the panel is closed; a finished
// timer raises a toast. Times use wall-clock deltas so a slow frame never drifts them.
QtObject {
    id: root
    property real now: Date.now()
    // Timer (milliseconds)
    property real timerTotal: 5 * 60000
    property real timerEnds: 0
    property real timerLeftWhenPaused: 5 * 60000
    property bool timerRunning: false
    property bool timerFinished: false
    readonly property real timerLeft: timerRunning ? Math.max(0, timerEnds - now) : timerLeftWhenPaused
    // Stopwatch
    property real watchBase: 0
    property real watchStarted: 0
    property bool watchRunning: false
    property var laps: []
    readonly property real watchElapsed: watchRunning ? watchBase + (now - watchStarted) : watchBase
    readonly property bool ticking: timerRunning || watchRunning
    // Alarms live in the user's settings and are checked twice a minute.
    readonly property var alarmList: SystemBridge.snapshot.settings.alarms || []
    property var fired: ({})
    onAlarmListChanged: checkAlarms(new Date())
    function checkAlarms(date) {
        checkSnoozed(date.getTime());
        const stamp = date.getFullYear() + "-" + (date.getMonth() + 1) + "-" + date.getDate();
        const hhmm = pad(date.getHours()) + ":" + pad(date.getMinutes());
        const weekday = (date.getDay() + 6) % 7;
        for (const alarm of alarmList) {
            if (!alarm.enabled || alarm.time !== hhmm || (alarm.days.length > 0 && alarm.days.indexOf(weekday) < 0))
                continue;
            const key = alarm.id + "|" + stamp + "|" + hhmm;
            if (fired[key])
                continue;
            fired[key] = true;
            ring(alarm);
        }
    }
    // What is ringing right now ({title, detail, kind, alarm}) or null, and snoozed alarms waiting to ring again.
    property var ringing: null
    property var snoozed: []
    property int plays: 0
    function startRinging(info) {
        ringing = info;
        plays = 1;
        SystemBridge.playSound("alarm");
    }
    function ring(alarm, resumed) {
        startRinging({
            title: alarm.label.length > 0 ? alarm.label : "Alarm",
            detail: alarm.time,
            kind: "alarm",
            alarm: alarm
        });
        if (alarm.days.length === 0 && !resumed)
            SystemBridge.toggleAlarm(alarm.id);
    }
    function dismiss() {
        ringing = null;
    }
    function snooze(minutes) {
        if (ringing && ringing.kind === "alarm")
            snoozed = snoozed.concat([
                {
                    at: Date.now() + minutes * 60000,
                    alarm: ringing.alarm
                }
            ]);
        ringing = null;
    }
    function checkSnoozed(stamp) {
        const due = snoozed.filter(item => item.at <= stamp);
        if (due.length === 0 || ringing !== null)
            return;
        snoozed = snoozed.filter(item => item.at > stamp).concat(due.slice(1));
        ring(due[0].alarm, true);
    }
    property Timer ringer: Timer {
        interval: 5000
        repeat: true
        running: root.ringing !== null
        onTriggered: {
            root.plays += 1;
            if (root.plays > 24)
                root.dismiss();
            else
                SystemBridge.playSound("alarm");
        }
    }

    function pad(value, digits) {
        let text = String(Math.floor(value));
        while (text.length < (digits || 2))
            text = "0" + text;
        return text;
    }
    function clock(ms, withHundredths) {
        const total = Math.max(0, Math.floor(ms / 10)) / 100;
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor(total % 3600 / 60);
        const seconds = Math.floor(total % 60);
        let text = (hours > 0 ? hours + ":" + pad(minutes) : minutes) + ":" + pad(seconds);
        if (withHundredths)
            text += "." + pad(Math.floor(total * 100 % 100));
        return text;
    }
    // Timer
    function setTimer(seconds) {
        timerRunning = false;
        timerFinished = false;
        timerTotal = Math.max(1, Math.min(seconds, 99 * 3600 + 59 * 60 + 59)) * 1000;
        timerLeftWhenPaused = timerTotal;
    }
    function adjustTimer(seconds) {
        if (timerRunning)
            return;
        setTimer(Math.max(1, timerTotal / 1000 + seconds));
    }
    function startTimer() {
        if (timerLeftWhenPaused <= 0)
            timerLeftWhenPaused = timerTotal;
        now = Date.now();
        timerEnds = now + timerLeftWhenPaused;
        timerFinished = false;
        timerRunning = true;
    }
    function pauseTimer() {
        timerLeftWhenPaused = timerLeft;
        timerRunning = false;
    }
    function resetTimer() {
        timerRunning = false;
        timerFinished = false;
        timerLeftWhenPaused = timerTotal;
    }
    // Stopwatch
    function startWatch() {
        now = Date.now();
        watchStarted = now;
        watchRunning = true;
    }
    function stopWatch() {
        watchBase = watchElapsed;
        watchRunning = false;
    }
    function resetWatch() {
        watchRunning = false;
        watchBase = 0;
        laps = [];
    }
    function lap() {
        if (!watchRunning)
            return;
        const total = watchElapsed;
        const previous = laps.length ? laps[0].total : 0;
        laps = [
            {
                number: laps.length + 1,
                total: total,
                split: total - previous
            }
        ].concat(laps).slice(0, 50);
    }
    property Timer ticker: Timer {
        interval: 50
        repeat: true
        running: root.ticking
        onTriggered: {
            root.now = Date.now();
            if (root.timerRunning && root.now >= root.timerEnds) {
                root.timerRunning = false;
                root.timerFinished = true;
                root.timerLeftWhenPaused = 0;
                root.startRinging({
                    title: "Timer",
                    detail: "Time's up",
                    kind: "timer",
                    alarm: null
                });
            }
        }
    }
    property Timer alarmClock: Timer {
        interval: 15000
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.checkAlarms(new Date())
    }
}
