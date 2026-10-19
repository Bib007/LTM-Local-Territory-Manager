// Fictional registrations; no record coverage is inferred from missing months.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const context={console,Date,Math,Map,Set,JSON,Intl,document:{addEventListener(){},getElementById(){return null;},querySelectorAll(){return [];}},window:{addEventListener(){}}};
vm.createContext(context);
for(const file of ['i18n.js','workspace.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',file),'utf8'),context);
const run=s=>vm.runInContext(s,context),plain=x=>JSON.parse(JSON.stringify(x));
run(`const esc=v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;'),ui=(key,p)=>esc(I18n.format(key,p)),fmt=v=>v,cmp=(a,b)=>a.localeCompare(b),serviceYear=d=>Number(d.slice(0,4))+(Number(d.slice(5,7))>=9),yearLabel=y=>(y-1)+'/'+y;
 let state={today:'2026-10-19',visits:[],completions:[
 {card_id:'fictional',date:'2026-09-01'},{card_id:'fictional',date:'2026-09-30'},
 {card_id:'fictional',date:'2026-10-19'},{card_id:'fictional',date:'2026-10-20'},
 {card_id:'archived-fictional',date:'2025-09-30'},{card_id:'fictional',date:'2025-10-19'},
 {card_id:'fictional',date:'2025-10-20'},{card_id:'fictional',date:'2025-08-31'}]};`);
const original=run('JSON.stringify(state)');
let months=plain(run("Workspace.monthlyComparison('2026-09-01','2027-08-31')"));
assert.equal(months.length,12);assert.deepEqual(months.slice(0,2).map(m=>[m.count,m.previousCount]),[[2,1],[1,1]]);
assert.equal(months[1].to,'2026-10-19');assert.equal(months[1].previousTo,'2025-10-19');assert.equal(months[2].future,true);assert.equal(months[2].count,null);assert.equal(months[2].previousCount,null);
run("state.today='2024-02-29';state.completions=[{date:'2024-02-29'},{date:'2023-02-28'},{date:'2023-03-01'}]");
months=plain(run("Workspace.monthlyComparison('2024-02-01','2024-02-29')"));assert.equal(months[0].previousTo,'2023-02-28');assert.equal(months[0].previousCount,1);
run("state.today='2025-02-28';state.completions=[{date:'2024-02-28'},{date:'2024-02-29'}]");
months=plain(run("Workspace.monthlyComparison('2025-02-01','2025-02-28')"));assert.equal(months[0].previousTo,'2024-02-28');assert.equal(months[0].previousCount,1);
run("state.today='2025-03-01'");months=plain(run("Workspace.monthlyComparison('2025-02-01','2025-02-28')"));assert.equal(months[0].previousTo,'2024-02-29');assert.equal(months[0].previousCount,2);
run("state.today='2026-01-15';state.completions=[{date:'2025-12-31'},{date:'2024-12-31'},{date:'2025-01-15'},{date:'2025-01-16'}]");
months=plain(run("Workspace.monthlyComparison('2025-12-01','2026-01-31')"));assert.equal(months[1].previousTo,'2025-01-15');assert.deepEqual(months.map(m=>[m.count,m.previousCount]),[[1,1],[0,1]]);
run("state.today='2026-10-19';state.completions=[]");
months=plain(run("Workspace.monthlyComparison('2026-09-01','2027-08-31')"));assert.equal(months[0].count,0);assert.equal(months[0].previousCount,null);
for(const language of ['da','en']){
 run(`I18n.set('${language}')`);const html=run("Workspace.dashboardChart('2026-09-01','2027-08-31')");
 assert.match(html,language==='en'?/Same month last year/:/Samme måned sidste år/);assert.match(html,language==='en'?/History may be missing/:/Historik kan mangle/);
 assert.match(html,language==='en'?/Not started/:/Ikke begyndt/);assert.doesNotMatch(html,/data-comparison="previous"/);assert.doesNotMatch(html,/NaN|Infinity|undefined/);
}
run(`state=${original}`);const snapshot=run('JSON.stringify(state)');run("Workspace.dashboardChart('2026-09-01','2027-08-31')");assert.equal(run('JSON.stringify(state)'),snapshot);
console.log('Monthly comparison: same-day limits, full completed months, both leap transitions, year boundary, repeated/archived registrations, missing history, future months, bilingual labels and read-only state passed.');
