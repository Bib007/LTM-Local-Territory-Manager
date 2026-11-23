'use strict';
// UI contract for the actual return form and follow-up collector. Fictional data only.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const read = name => fs.readFileSync(path.join(__dirname, '../app', name), 'utf8');
const nodes = new Map(), calls = [];
const get = id => {
  if (!nodes.has(id)) nodes.set(id, {
    innerHTML: '', open: false, style: {}, dataset: {},
    addEventListener() {}, querySelector() { return null; },
    showModal() { this.open = true; }, close() { this.open = false; }
  });
  return nodes.get(id);
};
const c = {
  console, Date, Intl, Map, Set, Array, Object, JSON, Number, String, Math,
  Promise, calls, setTimeout() {}, clearTimeout() {},
  window: {addEventListener() {}, confirm: () => true},
  document: {getElementById: get, addEventListener() {}, querySelector: () => ({content: 'FICTIONAL'})},
  fetch() { throw Error('No external requests permitted'); }
};
vm.createContext(c);
for (const file of ['i18n.js', 'workspace.js']) vm.runInContext(read(file), c);
const app = read('app.js');
vm.runInContext(app.slice(0, app.indexOf('(async()=>{try{await refresh();')), c);
const run = source => vm.runInContext(source, c);

run("state={today:'2026-11-17',cards:[{id:'c1',number:'F-101',name:'Fiktivt kort',area_id:'a',geo_polygon:[[10,55],[10.01,55],[10,55.01]]}],loans:[{id:'l1',card_id:'c1',publisher_id:'p1',assigned:'2026-11-15',cycle_start:'2026-11-15',returned:'2026-11-17'}],publishers:[{id:'p1',name:'Fiktiv person'}],notes:[],ib:[],settings:{},ib_reviews:[{id:'ib-review:l1',card_id:'c1',date:'2026-11-17',resolved:false}],areas:[]};");
run("ProfilesUI={has(...rights){return !state.profile||rights.every(r=>state.profile.permissions.includes(r));},canAction(action){return action==='loan.finish'||action==='ib.review.resolve'&&this.has('cards.view','ib.view','ib.edit');},pageAllowed(){return true;}};");
run("state.profile={desk_only:false,permissions:['cards.view','ib.view','ib.edit']};");
run("GeoUI={loaded:false,data:{changes:[]},addresses:()=>[],load:async()=>{throw Error('Geo access not needed for IB role')}};");
run("openDialog=html=>{globalThis.renderedReturn=html};");

for (const lang of ['da', 'en']) {
  run("I18n.set('" + lang + "')");
  run("finish('l1',false)");
  const html = run('renderedReturn');
  assert.match(html, /<label class="return-ib-checkbox">/);
  assert.match(html, /<input type="checkbox" name="revise_ib" value="yes">/);
  assert.doesNotMatch(html, /<input[^>]*name="revise_ib"[^>]*checked/); // Default is no.
  assert.doesNotMatch(html, /<select name="revise_ib"/);
  assert.match(html, lang === 'da' ? /Skal IB på det fysiske kort revideres/ : /Does the physical card’s DNC need revision/);
  run("finish('l1',true)");
  assert.doesNotMatch(run('renderedReturn'), /name="revise_ib"/, 'Retained cards do not create a return follow-up');

  const rows = run('Workspace.followupItems()');
  assert.equal(rows.length, 1, 'IB-only access must not load geographical checks');
  assert.equal(rows[0].category, 'ib-review');
  const followupHTML = run("Workspace.followupFilter='ib-review';Workspace.followupQuery='';Workspace.followupLimit=100;Workspace.followups()");
  assert.match(followupHTML, /data-work="ib-review-open"/);
  assert.match(followupHTML, /data-work="ib-review-resolve"/);
  assert.match(followupHTML, lang === 'da' ? /Revidér IB/ : /Review DNC/);
}

run("state.profile.permissions=['cards.view','ib.view']");
assert.equal(run('Workspace.followupItems().length'), 1);
assert.doesNotMatch(run('Workspace.followups()'), /data-work="ib-review-resolve"/, 'Read-only IB cannot close follow-ups');

run("state.profile.permissions=['cards.view','ib.view','ib.edit']");
run("mutate=async(action,data)=>{calls.push(JSON.parse(JSON.stringify({action,data})));state.ib_reviews[0].resolved=true;};");
(async () => {
  run("detail=(id,tab)=>{globalThis.openedIb={id,tab}};");
  await run("Workspace.handle('ib-review-open',{id:'c1'})");
  assert.deepEqual(JSON.parse(JSON.stringify(run('openedIb'))),{id:'c1',tab:'IB-bagside'});
  await run("Workspace.handle('ib-review-resolve',{id:'ib-review:l1'})");
  assert.deepEqual(calls, [{action:'ib.review.resolve',data:{id:'ib-review:l1'}}]);
  assert.equal(run('Workspace.followupItems().length'), 0, 'Completed follow-up disappears from the list');
  run("state.ib_reviews[0].resolved=false;state.profile={desk_only:true,permissions:['cards.view','loans.view','loans.manage','publishers.view']}");
  assert.equal(run('Workspace.followupItems().length'), 0, 'Desk-only accounts never see IB follow-up details');
  console.log('IB review UI: required Yes/No on return, separate bilingual list, IB-only access, completion and desk isolation passed.');
})().catch(error => {console.error(error); process.exitCode = 1;});
