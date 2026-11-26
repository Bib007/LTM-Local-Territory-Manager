'use strict';
// Rendered area-colour contract and pre-submit confirmation; fictional records only.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const read = name => fs.readFileSync(path.join(__dirname, '../app', name), 'utf8');
const nodes = new Map(), listeners = {}, writes = [];
const get = id => {
  if (!nodes.has(id)) nodes.set(id, {
    innerHTML: '', dataset: {}, style: {}, open: false,
    addEventListener() {}, querySelector() { return null; },
    showModal() { this.open = true; }, close() { this.open = false; },
  });
  return nodes.get(id);
};
class FakeFormData {
  constructor(form) { this.rows = new Map(form.fields); }
  [Symbol.iterator]() { return this.rows[Symbol.iterator](); }
  get(key) { return this.rows.get(key) ?? null; }
  has(key) { return this.rows.has(key); }
}
let allowConfirm = false, confirmations = 0;
const context = {
  console, Date, Intl, Map, Set, Array, Object, JSON, Number, String, Math,
  Promise, FormData: FakeFormData, setTimeout() {}, clearTimeout() {},
  window: {addEventListener() {}, confirm() { confirmations++; return allowConfirm; }},
  document: {
    getElementById: get,
    addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
    querySelector() { return {content: 'FICTIONAL'}; },
  },
  fetch() { throw Error('Network is disabled in this contract test'); },
};
vm.createContext(context);
vm.runInContext(read('i18n.js'), context);
const app = read('app.js');
vm.runInContext(app.slice(0, app.indexOf('(async()=>{try{await refresh();')), context);
const run = source => vm.runInContext(source, context);
run(`state={today:'2026-11-23',cards:[{id:'c1',number:'F-01',area_id:'a1',map_color:'#ee9900',temporary:true,addresses:[]}],areas:[{id:'a1',name:'Fiktivt område',map_color:'#123456'}],settings:{},publishers:[],loans:[]};`);
run("ProfilesUI={has(){return false;}};openDialog=html=>{globalThis.dialogHTML=html};");
run("mutate=async(action,data)=>{globalThis.testResult={action,data}};");
for (const language of ['da', 'en']) {
  run("I18n.set('" + language + "')");
  run("editArea('a1')");
  const areaHtml = run('dialogHTML');
  assert.match(areaHtml, /name="map_color" type="color" value="#123456"/);
  assert.match(areaHtml, /data-original-color="#123456"/);
  assert.match(areaHtml, /id="areaColorWarning"/);
  assert.match(areaHtml, language === 'da' ? /Tidligere individuelle farvevalg/ : /Previous individual colour choices/);
  run("editCard('c1')");
  assert.match(run('dialogHTML'), /name="map_color" value="#ee9900"/);
  assert.equal(run("cardColor({area_id:'a1'})"), '#123456');
}
const note = {hidden: true};
const warningForm = {id: 'areaForm', dataset: {originalColor: '#123456'}, querySelector: () => note};
listeners.input[0]({target: {name: 'map_color', value: '#abcdef', form: warningForm}});
assert.equal(note.hidden, false);
listeners.input[0]({target: {name: 'map_color', value: '#123456', form: warningForm}});
assert.equal(note.hidden, true);
const picker = {value: '#abcdef'};
const button = {disabled: false};
const areaForm = {
  id: 'areaForm', dataset: {id: 'a1', originalColor: '#123456'},
  fields: [['name', 'Fiktivt område'], ['map_color', '#abcdef']],
  reportValidity() { return true; },
  querySelector(selector) {
    if (selector === '[name=map_color]') return picker;
    if (selector === 'button:not([type=button])') return button;
    return null;
  },
};
(async () => {
  const submit = () => listeners.submit[0]({target: areaForm, preventDefault() {}});
  await submit();
  assert.equal(confirmations, 1);
  assert.equal(run('typeof testResult'), 'undefined', 'Declined overwrite must not save');
  allowConfirm = true;
  await submit();
  assert.equal(confirmations, 2);
  const saved = JSON.parse(JSON.stringify(run('testResult')));
  assert.deepEqual(saved, {action:'area.save', data:{
    id:'a1', name:'Fiktivt område', map_color:'#abcdef', reset_card_colors:true,
  }});
  assert.equal(button.disabled, false);
  console.log('Area/card colour UI: bilingual warning, inherited colour, personal override and explicit bulk confirmation passed.');
})().catch(error => {console.error(error); process.exitCode = 1;});
