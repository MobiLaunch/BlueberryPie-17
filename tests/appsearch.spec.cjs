/* Exercise the launcher ranking module imported by the QML shell. */
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const source = readFileSync(path.join(__dirname,'../shell/services/AppSearch.js'),'utf8').replace(/^\.pragma library\s*/, '');
const context = vm.createContext({});vm.runInContext(source+';this.api={rank,categories,recents,score};',context);
const {rank,categories,recents} = context.api;
const apps = [
  {id:'firefox.desktop',name:'Firefox',description:'Web browser',keywords:'internet surf',category:'Internet'},
  {id:'calc.desktop',name:'GNOME Calculator',description:'Do math',keywords:'',category:'Utilities'},
  {id:'files.desktop',name:'Files',description:'Browse folders',keywords:'file manager',category:'Utilities'},
  {id:'ff.desktop',name:'Fast Forward',description:'',keywords:'',category:'Media'},
];
const names = list => Array.from(list, app => app.name);
assert.deepEqual(names(rank(apps,'','All')),['Fast Forward','Files','Firefox','GNOME Calculator']);
assert.deepEqual(names(rank(apps,'fi','All')),['Files','Firefox']);              // prefixes, alphabetical
assert.deepEqual(names(rank(apps,'calc','All')),['GNOME Calculator']);          // word prefix
assert.deepEqual(names(rank(apps,'surf','All')),['Firefox']);                    // keyword
assert.deepEqual(names(rank(apps,'FIREF','All')),['Firefox']);                   // case-insensitive
assert.deepEqual(names(rank(apps,'','Utilities')),['Files','GNOME Calculator']);
assert.deepEqual(names(rank(apps,'zzz','All')),[]);
assert.equal(rank(apps,'  fire ','All')[0].name,'Firefox');                      // trims
assert.deepEqual(Array.from(categories(apps)),['All','Internet','Media','Utilities']);
assert.deepEqual(names(recents(apps,['files.desktop','missing.desktop','firefox.desktop'],6)),['Files','Firefox']);
console.log('PASS: launcher ranking, categories and recents');
