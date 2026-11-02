// Deterministic manual planning against production helpers; no network or writes.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const c={console,Date,Intl,Math,Map,Set,Array,Object,Number,String,JSON,Promise,document:{querySelector:()=>({content:'fictional'}),getElementById(){},addEventListener(){}},window:{addEventListener(){}}};
vm.createContext(c);vm.runInContext(read('i18n.js'),c);const app=read('app.js');vm.runInContext(app.slice(0,app.indexOf('const SaveStatus=')),c);vm.runInContext(read('split-suggestions.js'),c);const run=s=>vm.runInContext(s,c);
run(`function unit(id,number,count=1,road='Fictional road',postcode='9999'){return {id,number:String(number),count,road,postcode,label:road+' '+number};}
function record(id,size,extra={}){const units=Array.from({length:size},(_,i)=>unit(id+'-'+i,i));return {id,number:id,name:'Fictional <name>',area_id:'area',kind:'By',temporary:false,in_folder:false,address_ids:units.map(a=>a.id),geo_addresses:units,addresses:[{road:'Fictional road',count:size}],...extra};}
const source=record('101',8),target=record('102',2),unknown=record('unknown',0,{addresses:[{count:0,count_unknown:true}]});
state={revision:'before',cards:[source,target,unknown],loans:[],settings:{}};`);
const before=run('JSON.stringify(state)');let result=run('SplitSuggestions.plan(state.cards,state.loans,4)');
assert.equal(result.total,1);assert.equal(result.unknown,1);assert.equal(result.suggestions[0].parts,2);assert.equal(result.suggestions[0].split.count,4);assert.equal(result.suggestions[0].moves[0].count,2);assert.equal(result.suggestions[0].moves[0].targetCount,4);assert.equal(run('JSON.stringify(state)'),before);
assert.equal(new Set(result.suggestions[0].split.units.map(a=>a.id)).size,4);
run("state.cards.push(record('folder',10,{in_folder:true}),record('issued',12));state.loans=[{card_id:'issued',returned:null}]");
assert.equal(run('SplitSuggestions.plan(state.cards,state.loans,4).total'),1);
result=run('SplitSuggestions.plan(state.cards,state.loans,4,false)');assert.equal(result.total,3);const issued=result.suggestions.find(x=>x.c.id==='issued');assert.equal(issued.issued,true);assert.equal(issued.split,null);assert.equal(issued.moves.length,0);
run("state.cards.push(record('low-issued',1));state.loans.push({card_id:'low-issued',returned:null})");assert.ok(run("SplitSuggestions.plan(state.cards,state.loans,4,false).suggestions.every(m=>m.moves.every(x=>x.target.id!=='low-issued'))"));
for(const change of ["area_id:'other'","kind:'Land'","geo_addresses:target.geo_addresses.map(a=>({...a,road:'Elsewhere'}))","geo_addresses:target.geo_addresses.map(a=>({...a,postcode:'1111'}))"]){assert.equal(run(`SplitSuggestions.plan([source,{...target,${change}}],[],4).suggestions[0].moves.length`),0);}
run("const duplicate=record('duplicate',2);duplicate.address_ids[0]=source.address_ids[0];duplicate.geo_addresses[0]={...source.geo_addresses[0]};");result=run('SplitSuggestions.plan([source,target,duplicate],[],4)');assert.equal(result.suggestions[0].duplicate,true);assert.equal(result.suggestions[0].split,null);assert.equal(result.suggestions[0].moves.length,0);
for(const change of ["addresses:[{count:8,count_unknown:true}]","addresses:[{count:'8'}]","addresses:[{count:NaN}]","addresses:[{count:-1}]"]){assert.equal(run(`SplitSuggestions.plan([{...source,${change}}],[],4).total`),0);}
assert.equal(run("SplitSuggestions.plan([{...source,geo_addresses:source.geo_addresses.slice(1)}],[],4).suggestions[0].split"),null);
assert.equal(run("SplitSuggestions.plan([{...source,geo_addresses:source.geo_addresses.map((a,i)=>i? a:{...a,retired:true})}],[],4).suggestions[0].split"),null);
for(const target of ['0','1001','1.5','NaN'])assert.throws(()=>run(`SplitSuggestions.plan([source],[],${target})`));
run("state.profile={};ProfilesUI={has:()=>false};");assert.equal(run('SplitSuggestions.available()'),false);assert.equal(run('SplitSuggestions.entry()'),'');
run("state.profile=null;const called=[];let painted=0;document.getElementById=()=>({});SplitSuggestions.revision='old';SplitSuggestions.paint=()=>painted++;toast=s=>called.push(s);Workspace={restructureForm(){throw Error('Stale split opened');}};");
(async()=>{await run("SplitSuggestions.handle('split','101')");assert.equal(run('painted'),1);assert.match(run('called[0]'),/Oversigten/);console.log('Split suggestions: read-only counts, box/loan exclusions, exact membership, duplicates, unknowns, same-area/street targets, indivisible units, limits, permission gate and stale review passed.');})().catch(e=>{console.error(e);process.exitCode=1});
