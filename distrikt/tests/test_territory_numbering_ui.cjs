// Fictional, offline VM contracts for the isolated numbering dialog.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app/territory-numbering-ui.js'), 'utf8');
const events = {}, calls = [], responses = [];
const dialog = {open:false, innerHTML:''};
const confirm = {value:''};
const form = {elements:{card_id:{value:''}}};
const get = id => id==='dialog'?dialog:id==='numberingConfirmation'?confirm:id==='numberingPlanForm'?form:null;
function openDialog(html) { dialog.open = true;dialog.innerHTML = html;openDialog.generation++; }
openDialog.generation = 0;
const context = {
  console, Promise, Object, Array, String, JSON, Date, Set,
  document: {addEventListener(type,fn){(events[type] ||= []).push(fn);}},
  state: {cards:[{id:'fake1',number:'25',internal_number:'T0025'}],archived_cards:[],areas:[{id:'a',name:'Fiktivt område'}]},
  selected:'fake1',
  ProfilesUI:{has(){return true;}},
  esc:s=>String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;'),
  el:get, openDialog,
  formEnd:label=>'<button type="submit">'+label+'</button>',
  toast:msg=>calls.push({toast:msg}),
  I18n:{errorContent(){throw Error('unexpected UI error');}},
  api:async(url,body)=>{calls.push({url,body});return {json:async()=>({result:responses.shift()})};},
  mutate:async(action,data)=>{calls.push({action,data});},
};
vm.createContext(context);
vm.runInContext(source,context,{filename:'territory-numbering-ui.js'});
const UI = vm.runInContext('TerritoryNumbersUI',context);
const change = {id:'fake1',before:{number:'25',internal_number:'T0025'},after:{number:'T0025',internal_number:'25'}};
(async()=>{
  UI.start();
  assert.match(dialog.innerHTML,/Offentlige og interne distriktsnumre/);
  assert.match(dialog.innerHTML,/type="submit"/);
  responses.push({changes:[change],conflicts:[],expected:'digest-fictional',selected:1});
  await UI.preview('card.numbering.preview',{scope:'card',mode:'swap',card_id:'fake1'});
  assert.match(dialog.innerHTML,/Offentligt før/);
  assert.match(dialog.innerHTML,/T0025/);
  assert.equal(calls.filter(x=>x.action).length,0,'preview never writes');
  confirm.value='WRONG';
  await assert.rejects(UI.apply(),/bekræftelsestekst/);
  assert.equal(calls.filter(x=>x.action).length,0);
  confirm.value='BYT NUMRE';
  await UI.apply();
  assert.equal(calls.filter(x=>x.action).length,1);
  const saved=calls.find(x=>x.action==='card.numbering.apply');
  assert.equal(saved.data.expected,'digest-fictional');
  assert.equal(saved.data.confirm,'BYT NUMRE');
  assert.equal(saved.data.scope,'card');

  responses.push({changes:[change],conflicts:['Nummeret er optaget'],expected:'blocked',selected:1});
  await UI.preview('card.numbering.preview',{scope:'card',mode:'swap',card_id:'fake1'});
  assert.match(dialog.innerHTML,/Nummeret er optaget/);
  assert.match(dialog.innerHTML,/disabled/);

  context.state.numbering_last_batch={id:'numbering-fictional',count:1};
  responses.push({changes:[change],conflicts:[],expected:'undo-digest'});
  await UI.undo();
  assert.match(dialog.innerHTML,/FORTRYD NUMRE/);
  assert.equal(UI.pending.action,'card.numbering.undo');
  confirm.value='FORTRYD NUMRE';
  await UI.apply();
  assert.equal(calls.filter(x=>x.action==='card.numbering.undo').length,1);
  assert.equal(calls.filter(x=>x.action==='card.numbering.undo')[0].data.batch_id,'numbering-fictional');

  console.log('Dual-numbering previews, typed confirmation, collisions and undo: OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
