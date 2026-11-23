// All names and dates are fictional. No network requests or real territory files.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const nodes=new Map(),get=id=>{
 if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',value:'',dataset:{},showModal(){},addEventListener(){}});
 return nodes.get(id);
};
const copied=[],notifications=[];
const context={console,Date,Intl,Math,Map,Set,Array,Object,Number,String,JSON,Promise,
 navigator:{clipboard:{async writeText(v){copied.push(v);}}},
 document:{querySelector(){return {content:'FICTIONAL_TOKEN'};},getElementById:get,addEventListener(){}},
 window:{addEventListener(){}},setTimeout(){},clearTimeout(){},fetch(){throw Error('Network forbidden');}};
vm.createContext(context);
for(const file of ['i18n.js','overdue-loans.js'])vm.runInContext(read(file),context);
const source=read('app.js');
vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),context);
const run=code=>vm.runInContext(code,context);
run("I18n.set('da');toast=value=>{};");
run("state={today:'2026-11-23',settings:{},cards:[{id:'1',number:'11'},{id:'2',number:'12'},{id:'3',number:'13'},{id:'4',number:'14'},{id:'5',number:'15'}],publishers:[{id:'a',name:'Anna Fiktiv'},{id:'b',name:'Berta <Fiktiv>'}],loans:[{id:'a1',publisher_id:'a',card_id:'1',assigned:'2026-01-01',cycle_start:'2026-01-01'},{id:'a2',publisher_id:'a',card_id:'2',assigned:'2026-02-01',cycle_start:'2026-02-01'},{id:'b1',publisher_id:'b',card_id:'3',assigned:'2026-09-01',cycle_start:'2026-09-01'},{id:'returned',publisher_id:'a',card_id:'4',assigned:'2026-01-01',cycle_start:'2026-01-01',returned:'2026-06-01'},{id:'renewed',publisher_id:'b',card_id:'4',assigned:'2025-01-01',cycle_start:'2026-10-01'},{id:'b2',publisher_id:'b',card_id:'5',assigned:'2026-06-01',cycle_start:'2026-06-01'}]};");
const unchanged=run('JSON.stringify(state)');
assert.equal(run('OverdueLoans.count()'),3,'Only active loans with overdue current cycles count');
assert.match(run('OverdueLoans.badge()'),/navOverdueCount[^>]*>3<\/span>/);
let html=run("OverdueLoans.tab='overdue';OverdueLoans.sort='publisher';publishersPage()");
assert.match(html,/data-tab="overdue"/);
assert.match(html,/data-overdue="message" data-id="a"/);
assert.match(html,/data-overdue="message" data-id="b"/);
assert.equal((html.match(/data-overdue="message"/g)||[]).length,2,'One button per publisher in grouped mode');
assert.doesNotMatch(html,/<Fiktiv>/,'Names must be HTML escaped');
assert.match(html,/Berta &lt;Fiktiv&gt;/);
run("OverdueLoans.sort='oldest'");
html=run('OverdueLoans.render()');
assert.equal((html.match(/data-overdue="message"/g)||[]).length,3,'Each row in oldest-first mode can generate its publisher message');
assert(html.indexOf('Kort 11')<html.indexOf('Kort 12'));
assert(html.indexOf('Kort 12')<html.indexOf('Kort 15'));
const message=run("OverdueLoans.message('a')");
assert.match(message,/Hej Anna/);
assert.match(message,/Kort 11/);
assert.match(message,/Kort 12/);
assert.doesNotMatch(message,/Kort 15/);
assert.match(message,/2026/);
assert.match(message,/Kh $/);
run("state.settings.overdue_message_template='Kære {navn}\\n{kort}\\nKh {initialer}'");
assert.match(run("OverdueLoans.message('b')"),/Berta <Fiktiv>/);
assert.match(run("OverdueLoans.message('b')"),/Kort 15/);
assert.doesNotMatch(run("OverdueLoans.message('b')"),/Kort 13/);
run("openDialog=html=>{document.getElementById('dialog').innerHTML=html;}");
run("OverdueLoans.showMessage('b')");
assert.match(get('dialog').innerHTML,/Berta &lt;Fiktiv&gt;/);
assert.doesNotMatch(get('dialog').innerHTML,/<Fiktiv>/);
get('overdueMessage').value='Fiktiv SMS\nKh AB';
(async()=>{
 await run("OverdueLoans.copy()");
 assert.deepEqual(copied,['Fiktiv SMS\nKh AB'],'The editable text is copied unchanged');
 run("query='Anna';OverdueLoans.sort='publisher'");
 assert.equal((run('OverdueLoans.render()').match(/data-overdue="message"/g)||[]).length,1);
 run("query='';state.profile={permissions:['publishers.view']};ProfilesUI={has:(...rights)=>rights.every(r=>state.profile.permissions.includes(r))}");
 assert.equal(run('OverdueLoans.count()'),0,'Loan permission is required for counts and reminders');
 assert.doesNotMatch(run('OverdueLoans.render()'),/data-overdue="message"/);
 run("state.profile=null");
 assert.equal(run('JSON.stringify(state)').replace(/"profile":null,?/g,'' )===unchanged.replace(/"profile":null,?/g,'' ),false);
 console.log('Overdue count, sorting, grouping, safe text, templates, clipboard, and permissions passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
