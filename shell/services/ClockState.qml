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
                ShellState.toast = "Timer finished";
                ShellState.toastTimer.restart();
            }
        }
    }
}
