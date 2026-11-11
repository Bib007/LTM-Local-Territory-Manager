// Synthetic publisher register only: do not read or include actual congregation data.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const nodes=new Map();
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',style:{},dataset:{},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});return nodes.get(id);};
const context={console,Date,Intl,Number,String,Math,Map,Set,JSON,Array,Object,Promise,WeakMap,
 setTimeout(){},clearTimeout(){},DistrictMap:{dispose(){}},AdminUI:{selected:new Set(),selection(){return '';}},
 window:{addEventListener(){}},document:{addEventListener(){},getElementById:get,querySelector(){return {content:'FICTIONAL_TOKEN'};},querySelectorAll(){return [];}},
 fetch(){throw Error('No network requests allowed for publisher view');}};
vm.createContext(context);
for(const name of ['i18n.js','workspace.js'])vm.runInContext(read(name),context);
const source=read('app.js');
vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),context);
const run=code=>vm.runInContext(code,context);
const count=(html,kind)=>Number(html.match(new RegExp('data-publisher-'+kind+'>(\\d+)<'))?.[1]);
run("I18n.set('da')");
run("state={today:'2026-11-11',settings:{},cards:[],loans:[],publishers:["
 +"{id:'a',name:'Anna Fiktiv',group:'Gruppe 01',group_role:'overseer',pioneer:false},"
 +"{id:'b',name:'Berta Eksempel',group:'Gruppe 01',group_role:'',pioneer:true},"
 +"{id:'c',name:'Charlie Test',group:'Gruppe 02',group_role:'',pioneer:false},"
 +"{id:'d',name:'Dina Uden Gruppe',group:'',group_role:'',pioneer:false}]};"
 +"publisherGroupFilter='';query='';");
const initial=run('publishersPage()');
assert.equal(count(initial,'total'),4);
assert.equal(count(initial,'visible'),4);
assert.match(initial,/data-publisher-group="group:gruppe 01"/);
assert.match(initial,/data-publisher-group="group:gruppe 02"/);
assert.match(initial,/data-publisher-group="__none__"/);
assert(initial.indexOf('Anna Fiktiv')<initial.indexOf('Berta Eksempel'),'Existing alphabetical sort must survive grouping');
assert.match(initial,/data-action="publisher-profile"/);
assert.match(initial,/data-action="publisher"/);
assert.match(initial,/data-publisher-import="open"/);
assert.match(initial,/id="publisherGroupFilter"/);
assert.match(initial,/id="search"/);
run("publisherGroupFilter='group:gruppe 01';query='anna'");
let html=run('publishersPage()');
assert.equal(count(html,'total'),4);
assert.equal(count(html,'visible'),1);
assert.match(html,/Anna Fiktiv/);
assert.doesNotMatch(html,/Berta Eksempel/);
assert.doesNotMatch(html,/Charlie Test/);
run("query='ingen match'");
html=run('publishersPage()');
assert.equal(count(html,'total'),4);
assert.equal(count(html,'visible'),0);
assert.match(html,/data-publisher-group="group:gruppe 01"/);
assert.match(html,/data-publisher-count="0"/);
assert.match(html,/Ingen forkyndere matcher søgningen/);
run("publisherGroupFilter='__none__';query=''");
html=run('publishersPage()');
assert.equal(count(html,'visible'),1);
assert.match(html,/Dina Uden Gruppe/);
assert.doesNotMatch(html,/Anna Fiktiv/);
run("publisherGroupFilter='';state.publishers.push({id:'e',name:'Erik Fiktiv',group:'Gruppe 02',group_role:'',pioneer:false})");
html=run('publishersPage()');
assert.equal(count(html,'total'),5,'New records update the total');
assert.equal(count(html,'visible'),5);
run("state.publishers.find(p=>p.id==='a').group='Gruppe 02';publisherGroupFilter='group:gruppe 01'");
html=run('publishersPage()');
assert.equal(count(html,'total'),5,'Group moves do not change the total');
assert.equal(count(html,'visible'),1,'Group moves change filtered counts');
run("state.publishers=state.publishers.filter(p=>p.id!=='b')");
html=run('publishersPage()');
assert.equal(count(html,'total'),4,'Deleting/deactivating a projected person updates count');
assert.equal(run('publisherGroupFilter'),'','A removed last group is cleared instead of silently hiding people');
assert.equal(count(html,'visible'),4);
run("state.publishers.push({id:'x',name:'<img onerror=attack()>',group:'<script>fictional</script>',group_role:'',pioneer:false})");
html=run('publishersPage()');
assert.equal(count(html,'total'),5);
assert.match(html,/&lt;img onerror=attack\(\)&gt;/);
assert.match(html,/&lt;script&gt;fictional&lt;\/script&gt;/);
assert.doesNotMatch(html,/<img onerror/);
assert.doesNotMatch(html,/<script>fictional/);
run("state.publishers=[];query='';publisherGroupFilter=''");
html=run('publishersPage()');
assert.equal(count(html,'total'),0);
assert.equal(count(html,'visible'),0);
assert.match(html,/Ingen forkyndere fundet/);
run("I18n.set('en');state.publishers=[{id:'z',name:'Fictional One',group:'',group_role:'',pioneer:false}]");
html=run('publishersPage()');
assert.match(html,/Total publishers/);
assert.match(html,/Publishers in current view/);
assert.match(html,/1 in group/);
assert.match(html,/No service group|Without a service group|No group|Unassigned/i);
const css=read('style.css');
assert.match(css,/\.publisherGroups\{display:grid/);
assert.match(css,/@media\(max-width:600px\)/);
assert.match(css,/\.publisherItemHeading\{flex-wrap:wrap\}/);
console.log('Publisher totals, filters, alphabetical groups, move, create, delete/deactivate, empty groups, responsive rules and escaping passed.');
