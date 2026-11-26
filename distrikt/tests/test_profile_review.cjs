// Server-authorized fictional evidence rendered as human fields, never JSON.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const c={document:{addEventListener(){},querySelectorAll(){return [];}},console,Intl,Map,Set,Array,Object,Number,String,JSON,state:{areas:[{id:'a',name:'Land'}]},card:()=>({number:'F101'}),fmt:s=>s.split('-').reverse().join('.'),publisherRoleLabels:{overseer:'Gruppetilsynsmand'},ProfilesUI:{labels:{'cards.view':'Se kort'},admin:{roles:[{id:'r',name:'Land'}]}}};vm.createContext(c);
for(const name of ['i18n.js','profile-review-ui.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),c);
const run=s=>vm.runInContext(s,c);run('esc=I18n.escape;ui=(v,p)=>I18n.label(v,p)');
c.envelope={present:true,value:[{road:'Fiktiv <vej>',numbers:'1–19',count:0,count_unknown:true,type:'Hus'}]};
const html=run("ProfileReview.shown(envelope,'addresses')");assert.match(html,/<dl/);assert.match(html,/Vejnavn/);assert.match(html,/Fiktiv &lt;vej&gt;/);assert.match(html,/1–19/);assert.match(html,/Ukendt/);assert.doesNotMatch(html,/"road"|count_unknown|<pre>|<vej>/);
assert.doesNotMatch(run("ProfileReview.shown({present:true,value:{salt:'DO_NOT_DISPLAY',hash:'SECRET'}},'credential')"),/SECRET|DO_NOT_DISPLAY/);
assert.match(run("ProfileReview.value([[10,55],[10.1,55],[10.1,55.1]],'geo_polygon')"),/<svg/);
assert.doesNotMatch(run("ProfileReview.value([[10,55],['<script>',55]],'geo_polygon')"),/<script>/);
run("I18n.set('en')");assert.match(run("ProfileReview.value('Hus','type')"),/House/);
assert.match(run("ProfileReview.value('Land','name')"),/>Land</,'User-entered names must not be translated');
assert.match(run("ProfileReview.value('a','area_id')"),/>Land</,'User-entered area names must not be translated');
assert.match(run("ProfileReview.value(['r'],'roles')"),/>Land</,'Custom role names must not be translated');
console.log('Profile review: labelled street fields, honest unknown counts, local boundary graphic, escaped text, credential masking and preserved user names passed.');
