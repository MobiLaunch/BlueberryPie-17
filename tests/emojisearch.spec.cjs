/* Exercise the emoji picker ranking module and the generated data imported by the QML shell. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const load = (file, extra = '') => readFileSync(path.join(__dirname, '../shell/services', file), 'utf8').replace(/^\.pragma library\s*/, '');
const context = vm.createContext({});
vm.runInContext(load('EmojiData.js') + load('EmojiSearch.js') + ';this.api={search,recents,score,groups,entries};', context);
const {search, recents, groups, entries} = context.api;
const emoji = list => Array.from(list, entry => entry[0]);
const of = label => entries.find(entry => entry[1] === label)[0];  // some carry a variation selector

assert.ok(entries.length > 1800, 'a full emoji set');
assert.deepEqual(Array.from(groups), ['Smileys', 'People', 'Nature', 'Food', 'Travel', 'Activities', 'Objects', 'Symbols', 'Flags']);
assert.ok(entries.every(entry => entry.length === 4 && entry[0] && entry[1] && entry[3] >= 0 && entry[3] < groups.length));
assert.equal(new Set(entries.map(entry => entry[0])).size, entries.length, 'no duplicates');
assert.equal(search(entries, '', -1).length, entries.length, 'no query lists everything');
assert.equal(search(entries, '', 0)[0][0], of('grinning face'), 'browse starts with the grinning face');
assert.ok(search(entries, '', 9).every(entry => entry[3] === 9), 'a group filter');
assert.equal(emoji(search(entries, 'grinning face', -1))[0], of('grinning face'), 'exact label first');
assert.ok(emoji(search(entries, 'thumbs up', -1)).includes(of('thumbs up')));
assert.ok(emoji(search(entries, 'THUMBS', -1)).includes(of('thumbs up')), 'case-insensitive');
assert.ok(emoji(search(entries, 'lol', -1)).includes(of('grinning face with smiling eyes')), 'matches tags too');
assert.ok(emoji(search(entries, 'heart', -1)).slice(0, 10).includes(of('red heart')), 'popular labels rank near the top');
assert.equal(emoji(search(entries, 'ok', -1))[0], of('OK hand'), 'labels are matched in lower case');
assert.equal(emoji(search(entries, 'cat', -1))[0], of('cat'), 'the plain word beats longer labels');
assert.equal(search(entries, 'zzzzqqq', -1).length, 0, 'no match');
assert.ok(search(entries, 'face', 3).length > 0, 'a query searches every group, not just the chosen one');
assert.deepEqual(emoji(recents(entries, [of('thumbs up'), 'not-an-emoji', of('grinning face')])), [of('thumbs up'), of('grinning face')], 'unknown recents are skipped, order kept');
console.log('PASS: emoji data and search ranking');
