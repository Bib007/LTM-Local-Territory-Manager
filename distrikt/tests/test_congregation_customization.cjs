// Fictional congregation terminology uses display labels only, never status IDs.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ctx={console,JSON,Array,Object,String,Number,Promise,
 localStorage:{getItem(){return null;},setItem(){}},
 document:{addEventListener(){},querySelectorAll(){return [];},documentElement:{lang:'da'}},
 location:{search:''},URLSearchParams};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/i18n.js'),'utf8'),ctx);
const run=source=>vm.runInContext(source,ctx);
run("var state={settings:{}};I18n.current='da'");
assert.equal(run("I18n.text('Kort i kassen')"),'Kort i kassen','Legacy defaults are unchanged');
assert.equal(run("I18n.text('Kort i mappen')"),'Kort i mappen');
run("state.settings={folder_enabled:false,location_labels:{}}");
assert.equal(run("I18n.text('Kort i kassen')"),'Hjemme');
assert.equal(run("I18n.text('Udleverede distriktskort')"),'Ude');
assert.equal(run("I18n.text('Aflever til kassen')"),'Aflever → Hjemme');
assert.equal(run("I18n.format('{home} hjemme · {folder} i mappen · {total} kort i alt',{home:5,folder:3,total:9})"),'5 ledige kort hjemme · 9 kort i alt');
run("state.settings={folder_enabled:true,location_labels:{home:'Hjemme <script>alert(1)</script>',folder:'I min lange transportmappe',issued:'Ude i arbejde'}}");
assert.equal(run("I18n.text('Kort i kassen')"),'Hjemme <script>alert(1)</script>');
assert.match(run("I18n.label('Kort i kassen')"),/Hjemme &lt;script&gt;alert\(1\)&lt;\/script&gt;/);
assert.match(run("I18n.text('Læg i mappen')"),/I min lange transportmappe/);
assert.equal(run("I18n.text('Kort i mappen')"),'I min lange transportmappe');
assert.equal(run("I18n.text('Udleverede distriktskort')"),'Ude i arbejde');
assert.equal(run("I18n.text('Udleveret')"),'Udleveret','The historical assignment-date header must not become a location label');
assert.equal(run("I18n.text('Kort i kassen')").startsWith('Hjemme'),true);
run("I18n.current='en'");
assert.equal(run("I18n.text('Kort i mappen')"),'I min lange transportmappe','Custom names survive language switching');
assert.equal(run("I18n.text('Udlever fra kassen')"),'Assign from → Hjemme <script>alert(1)</script>');
assert.equal(run("I18n.text('Kort')"),'Card','Other app vocabulary still translates normally');
console.log('Congregation UI: legacy terms, two-location mode, customizable labels, safe escaping and language switching passed.');
