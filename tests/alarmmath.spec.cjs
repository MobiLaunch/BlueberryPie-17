/* Exercise the next-alarm arithmetic used by the desktop glance widget. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = readFileSync(path.join(__dirname, '../shell/services/AlarmMath.js'), 'utf8').replace(/^\.pragma library\s*/, '');
const context = vm.createContext({});
vm.runInContext(source + ';this.api={nextOccurrence,describe};', context);
const {nextOccurrence, describe} = context.api;
const at = (y, m, d, h, min) => new Date(y, m - 1, d, h, min, 0, 0).getTime();
const alarm = (id, time, days = [], enabled = true, label = '') => ({id, time, days, enabled, label});
const clock = date => `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;

// Thursday 15 Oct 2026, 06:00 (weekday 3).
const now = at(2026, 10, 15, 6, 0);
assert.equal(nextOccurrence([], now), null);
assert.equal(nextOccurrence([alarm(1, '07:30', [], false)], now), null);                        // disabled
assert.equal(nextOccurrence([alarm(1, '07:30')], now).at, at(2026, 10, 15, 7, 30));            // later today
assert.equal(nextOccurrence([alarm(1, '05:00')], now).at, at(2026, 10, 16, 5, 0));             // already passed: tomorrow
assert.equal(nextOccurrence([alarm(1, '06:00')], now).at, at(2026, 10, 16, 6, 0));             // exactly now has rung
assert.equal(nextOccurrence([alarm(1, '07:00', [0, 1, 2, 3, 4])], now).at, at(2026, 10, 15, 7, 0));  // Thu is a weekday
assert.equal(nextOccurrence([alarm(1, '07:00', [5, 6])], now).at, at(2026, 10, 17, 7, 0));    // weekend: Saturday
assert.equal(nextOccurrence([alarm(1, '05:00', [3])], now).at, at(2026, 10, 22, 5, 0));        // Thursday only, passed: next week
const both = nextOccurrence([alarm(1, '09:00'), alarm(2, '07:00', [], true, 'Gym'), alarm(3, '06:30', [], false)], now);
assert.deepEqual([both.id, both.label], [2, 'Gym']);
assert.equal(nextOccurrence([alarm(1, '7:30')], now), null);                                    // malformed time ignored
assert.equal(nextOccurrence([alarm(1, '00:30', [0])], at(2026, 12, 31, 23, 0)).at, at(2027, 1, 4, 0, 30));  // month/year rollover

assert.equal(describe(null, now, clock), '');
assert.equal(describe({at: at(2026, 10, 15, 7, 30)}, now, clock), '07:30');
assert.equal(describe({at: at(2026, 10, 16, 7, 30)}, now, clock), 'Tomorrow 07:30');
assert.equal(describe({at: at(2026, 10, 19, 7, 30)}, now, clock), 'Mon 07:30');
console.log('PASS: next alarm arithmetic and descriptions');
