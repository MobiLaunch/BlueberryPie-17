/* Exercise the calculator parser imported by the QML shell. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = readFileSync(path.join(__dirname, '../shell/services/Calculator.js'), 'utf8').replace(/^\.pragma library\s*/, '');
const context = vm.createContext({});
vm.runInContext(source + ';this.api={evaluate,format};', context);
const {evaluate, format} = context.api;
const value = (text, options) => { const r = evaluate(text, options); assert.ok(r.ok, `${text}: ${r.error}`); return r.value; };
const error = (text) => { const r = evaluate(text); assert.equal(r.ok, false, text); return r.error; };

assert.equal(value('1+2*3'), 7);
assert.equal(value('(1+2)*3'), 9);
assert.equal(value('2^3^2'), 512);                    // right associative
assert.equal(value('-2^2'), -4);                      // unary binds looser than ^
assert.equal(value('10/4'), 2.5);
assert.equal(value('0.1+0.2'), 0.3);                  // float noise removed
assert.equal(value('50%'), 0.5);
assert.equal(value('200*15%'), 30);
assert.equal(value('5!'), 120);
assert.equal(value('6×7'), 42);
assert.equal(value('9÷3−1'), 2);
assert.equal(value('2(3+4)'), 14);                    // implicit multiplication
assert.ok(Math.abs(value('2pi') - 2 * Math.PI) < 1e-12);
assert.equal(value('2*-3'), -6);
assert.equal(value('2^-1'), 0.5);
assert.equal(value('sqrt(16)'), 4);
assert.equal(value('√9'), 3);
assert.equal(value('abs(-3)+log(1000)'), 6);
assert.equal(value('ln(e)'), 1);
assert.equal(value('sin(90)', {degrees: true}), 1);
assert.equal(value('cos(180)', {degrees: true}), -1);
assert.equal(value('sin(180)', {degrees: true}), 0);
assert.equal(value('asin(1)', {degrees: true}), 90);
assert.equal(value('2*ans', {ans: 21}), 42);
assert.equal(value('1e3+1'), 1001);
assert.equal(value('.5+.5'), 1);
assert.equal(evaluate('').ok, false);
assert.equal(evaluate('').error, '');
assert.match(error('1/0'), /divide by zero/);
assert.match(error('2+'), /Unfinished/);
assert.match(error('(1+2'), /Missing \)/);
assert.match(error('1+2)'), /Unexpected/);
assert.match(error('foo(2)'), /Unknown/);
assert.match(error('3 $ 4'), /Unexpected/);
assert.match(error('(-1)!'), /whole number/);
assert.match(error('1.5!'), /whole number/);
assert.match(error('171!'), /large/);
assert.match(error('sqrt(-1)'), /real/);
assert.match(error('ln(0)'), /real/);
// Text is never executed.
for (const hostile of ['process.exit()', 'constructor', 'this', '__proto__', 'globalThis', 'require("fs")', '1;2', 'a=1']) {
  assert.equal(evaluate(hostile).ok, false, hostile);
}
assert.equal(format(0.5), '0.5');
assert.equal(format(1 / 3), '0.333333333333');
assert.equal(format(1e21), '1e21');
assert.equal(format(123456789012), '123456789012');
assert.equal(format(0), '0');
console.log('PASS: calculator parser, precedence, functions and error handling');
