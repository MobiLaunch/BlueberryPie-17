/* Exercise the same class/event matcher imported by the QML shell. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = readFileSync(path.join(__dirname,'../shell/services/LaunchTracking.js'),'utf8').replace(/^\.pragma library\s*/, '');
const tracker = vm.createContext({});vm.runInContext(source,tracker);
const app = {id:'org.mozilla.firefox.desktop',startupClass:'Navigator'};
assert(tracker.matches(app,'Navigator'));
assert(tracker.matches(app,'firefox'));
assert(tracker.matches(app,'org.mozilla.firefox'));
assert(!tracker.matches(app,'not-firefox'));
assert(!tracker.matches(null,'firefox'));
assert(!tracker.matches(app,''));
assert.equal(tracker.eventClass('openwindow','abc,1,firefox,A title, with commas'),'firefox');
assert.equal(tracker.eventClass('activewindow','Navigator,A title, with commas'),'Navigator');
assert.equal(tracker.eventClass('openwindow','malformed'),'');
assert.equal(tracker.eventClass('closewindow','abc'),'');
console.log('PASS: launch class matching, active-window reuse and comma-containing titles');
