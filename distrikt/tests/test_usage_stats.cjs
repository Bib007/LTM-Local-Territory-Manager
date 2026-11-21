// Fictional usage-statistics rendering and escaping; no network or local data.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const listeners={};
const escape=value=>String(value??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const context={console,Date,Number,Math,Intl,Array,Object,String,Set,
 I18n:{language:()=> 'da',text:word=>word},
 ui:escape,esc:escape,state:{profile:{user:{id:'own-user'}}},
 document:{addEventListener:(type,handler)=>{listeners[type]=handler;}}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/usage-stats.js'),'utf8'),context);
const sample={
 actions:4,person_minutes:20,system_minutes:15,active_days:1,
 first_at:'2026-11-21T10:00:00+00:00',last_at:'2026-11-21T10:15:00+00:00',
 users:[
  {actor_id:'own-user',actor_name:'Own <script>alert(1)</script>',actions:2,minutes:10,active_days:1,last_at:'2026-11-21T10:10:00+00:00',months:[{month:'2026-11',minutes:10,actions:2}]},
  {actor_id:'other',actor_name:'Another user',actions:2,minutes:10,active_days:1,last_at:'2026-11-21T10:15:00+00:00',months:[{month:'2026-11',minutes:10,actions:2}]}],
 months:[{month:'2026-11',minutes:20,actions:4}]
};
context.sample=sample;
const html=vm.runInContext('UsageStatsUI.data=sample;UsageStatsUI.results()',context);
assert.match(html,/Systemet med registreret aktivitet/);
assert.match(html,/Din estimerede tid/);
assert.match(html,/2026-11/);
assert.match(html,/Own &lt;script&gt;alert\(1\)&lt;\/script&gt;/);
assert.doesNotMatch(html,/<script>alert\(1\)<\/script>/);
vm.runInContext("UsageStatsUI.selected='other'",context);
const filtered=vm.runInContext('UsageStatsUI.results()',context);
assert.match(filtered,/value="other" selected/);
assert.match(filtered,/2026-11/);
const empty=vm.runInContext("UsageStatsUI.data={actions:0};UsageStatsUI.results()",context);
assert.match(empty,/Ingen registrerede redigeringer/);
console.log('Usage statistics UI tests passed');
