/* Exercise the unit converter module imported by the QML shell. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = readFileSync(path.join(__dirname, '../shell/services/Units.js'), 'utf8').replace(/^\.pragma library\s*/, '');
const context = vm.createContext({});
vm.runInContext(source + ';this.api={convert,format,unitNames,CATEGORIES};', context);
const {convert, format, unitNames, CATEGORIES} = context.api;
const close = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) <= eps * Math.max(1, Math.abs(b)), `${a} !~ ${b}`);

close(convert('length', 1, 'km', 'm'), 1000);
close(convert('length', 1, 'mi', 'km'), 1.609344);
close(convert('length', 12, 'in', 'ft'), 1);
close(convert('mass', 1, 'lb', 'kg'), 0.45359237);
close(convert('mass', 1000, 'g', 'kg'), 1);
close(convert('volume', 1, 'gal', 'l'), 3.785411784);
close(convert('speed', 36, 'km/h', 'm/s'), 10);
close(convert('data', 1, 'GiB', 'MiB'), 1024);
close(convert('data', 1, 'GB', 'MB'), 1000);
close(convert('temperature', 100, '°C', '°F'), 212);
close(convert('temperature', 32, '°F', '°C'), 0);
close(convert('temperature', 0, '°C', 'K'), 273.15);
close(convert('temperature', -40, '°C', '°F'), -40);
close(convert('length', '2,5', 'm', 'cm'), 250);                // decimal comma
assert.ok(Number.isNaN(convert('length', 'abc', 'm', 'cm')));
assert.ok(Number.isNaN(convert('length', 1, 'm', 'lb')));       // wrong category
assert.ok(Number.isNaN(convert('length', 1, 'constructor', 'm')));
assert.ok(Number.isNaN(convert('temperature', -1, 'K', '°C')));  // below absolute zero
assert.ok(Number.isNaN(convert('temperature', -300, '°C', 'K')));
assert.equal(format(0), '0');
assert.equal(format(1 / 3), '0.33333333');
assert.equal(format(NaN), '');
assert.equal(format(1e15), '1e15');
for (const group of CATEGORIES) {
  const names = unitNames(group.id);
  assert.ok(names.length >= 3, group.id);
  for (const a of names) for (const b of names) close(convert(group.id, convert(group.id, 5, a, b), b, a), 5, 1e-9);  // round trip
}
console.log('PASS: unit conversion, temperature and validation');
