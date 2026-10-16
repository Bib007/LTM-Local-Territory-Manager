// Invented settings and backups; exercise real event handlers without network or disk.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),listeners={},nodes=new Map(),writes=[],requests=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,checked:false,addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});return nodes.get(id);};
class Fields{constructor(form){this.values=new Map(form.fields);}has(k){return this.values.has(k);}[Symbol.iterator](){return this.values[Symbol.iterator]();}}
const c={console,Date,Intl,Math,Number,String,Map,Set,Array,Object,JSON,Promise,FormData:Fields,writes,requests,
 setTimeout(){},clearTimeout(){},frontResizeObserver:null,DistrictMap:{dispose(){}},
 window:{addEventListener(){},confirm(){return true;}},document:{getElementById:get,querySelector(){return {content:'INVENTED_TOKEN'};},addEventListener(k,fn){(listeners[k]??=[]).push(fn);}},
 fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>({warning:'Servertekst <invented>',token:'INVENTED_RESTORE',counts:{cards:3,ib:2}})};}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','navigation.js','transfer-ui.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);
const run=s=>vm.runInContext(s,c);
run(`ShareUI={html:()=>''};GeoUI={load:async()=>{}};state={today:'2026-10-16',version:'1.12.0-beta.6',
 settings:{congregation:'Områder <invented> & Kort',folder_minimum:30,rural_mode:'manual',rural_minimum:7,require_revision:true,print_profiles:{back:{width:94,height:146,orientation:'portrait',x:1,y:-2}}},
 areas:[{id:'area-1',name:'Menighed og mappe <invented>'}],cards:[],publishers:[],loans:[],completions:[],ib:[],notes:[],recovery:[{label:'Gendan <invented>',batch:'batch-1',count:2,at:'2026-10-15T12:00:00Z'}]};
 mutate=async(action,data,options)=>writes.push({action,data,options});refresh=async()=>{};loadMap=async()=>{};`);
const original=run('JSON.stringify(state)'),contracts={};
const contract=html=>(html.match(/(?:name|value|type|min|max|maxlength|data-action|data-id|data-value)="[^"]*"/g)||[]).join('\n');
const submit=listeners.submit.find(fn=>String(fn).includes("case 'settingsForm'"));
const click=listeners.click.find(fn=>String(fn).includes("case 'cleanup'"));
const action=name=>({target:{dataset:{action:name},isConnected:true,closest(selector){return selector==='[data-action]'?this:null;}},preventDefault(){}});
const form=(id,fields,dataset={})=>({id,dataset,fields,reportValidity(){return true;},querySelector(){return {disabled:false};}});
(async()=>{
 const payloads={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}');Workspace.activityData=[{action:'settings.save',fields:['name','Kort'],cards:['101 <invented>'],at:'2026-10-15T12:00:00Z',count:1},{action:'Gem',at:'2026-10-15T12:00:00Z',count:1}]`);const html=run('settingsPage()');contracts[language]=[contract(html),contract(run('Workspace.settingsNav()'))];
  const activity=run('Workspace.activity()');assert.match(activity,language==='en'?/>Settings changed<\//:/>Indstillinger ændret<\//);assert.match(activity,/101 &lt;invented&gt;/);assert.match(activity,/>Gem</,'Unknown action identifiers stay unchanged');assert.match(activity,/, Kort</,'Unknown field identifiers stay unchanged');
  assert.match(html,/Områder &lt;invented&gt; &amp; Kort/);assert.match(html,/Menighed og mappe &lt;invented&gt;/);assert.match(html,/Gendan &lt;invented&gt;/);
  assert.match(html,/value="manual" selected/);assert.match(html,/name="rural_minimum"[^>]*max="30"/);assert.match(html,language==='en'?/>Save settings<\//:/>Gem indstillinger<\//);
  assert.match(html,language==='en'?/>Card front<\//:/>Kortets forside<\//,'A print-profile front is distinct from the Home navigation label');
  run("editArea('area-1')");contracts[language].push(contract(get('dialog').innerHTML));assert.equal(get('dialog').lang,language);
  assert.match(get('dialog').innerHTML,/value="Menighed og mappe &lt;invented&gt;"/);
  const start=writes.length;
  await submit({target:form('settingsForm',[['congregation','Områder <invented> & Kort'],['folder_minimum','30'],['rural_mode','manual'],['rural_minimum','7'],['require_revision','on']]),preventDefault(){}});
  await submit({target:form('settingsForm',[['congregation','Områder <invented> & Kort'],['folder_minimum','0'],['rural_mode','auto'],['rural_minimum','0']]),preventDefault(){}});
  await submit({target:form('areaForm',[['name','Menighed og mappe <invented>']],{id:'area-1'}),preventDefault(){}});
  payloads[language]=JSON.parse(JSON.stringify(writes.slice(start).map(({action,data})=>({action,data}))));
  const before=writes.length;await run('TransferUI.preview({size:12})');assert.equal(writes.length,before,'Preview must never import data');
  contracts[language].push(contract(get('dialog').innerHTML));assert.match(get('dialog').innerHTML,/id="restoreApply"[^>]*disabled/);assert.match(get('dialog').innerHTML,/Servertekst &lt;invented&gt;/);
  assert.match(get('dialog').innerHTML,language==='en'?/>Replace data and import<\//:/>Erstat data og importer<\//);
  assert.equal(requests.at(-1).url,'/api/restore/preview');assert.equal(requests.at(-1).options.headers['X-Distrikt-Token'],'INVENTED_TOKEN');
 }
 assert.deepEqual(contracts.en,contracts.da,'Translated labels must keep values, keys, limits and confirmation actions');
 assert.deepEqual(payloads.en,payloads.da);assert.equal(payloads.en[0].data.folder_minimum,30);assert.equal(payloads.en[0].data.require_revision,true);assert.equal(payloads.en[1].data.require_revision,false);assert.equal(payloads.en[1].data.rural_mode,'auto');
 c.fetch=async()=>({ok:true,json:async()=>({token:'VISIBLE_COUNTS',counts:{cards:99,notes:12},visible_counts:{cards:2,notes:1}})});await run('TransferUI.preview({size:12})');assert.match(get('dialog').innerHTML,/<td>0<\/td><td>2<\/td>/);assert.doesNotMatch(get('dialog').innerHTML,/<td>99<\/td>|<td>12<\/td>/,'The comparison must use the restored app-list counts');
 c.fetch=async()=>({ok:true,json:async()=>({token:'LEGACY_COUNTS',counts:{cards:99}})});await run('TransferUI.preview({size:12})');assert.match(get('dialog').innerHTML,/<td>99<\/td>/,'An older server response remains supported');
 const applyRequests=[];c.applyRequests=applyRequests;
 run(`api=async(url,payload)=>{applyRequests.push({url,payload});return {json:async()=>({safety_backup:'FICTIONAL-backup.zip'})};}`);
 const button={disabled:true,dataset:{restoreToken:'INVENTED_RESTORE'}};
 await run('TransferUI.apply')(button);assert.equal(applyRequests.length,0,'Unchecked consent must block import');
 get('restoreUnderstood').checked=true;button.id='restoreApply';const transferClick=listeners.click.find(fn=>String(fn).includes("#restoreApply,#downloadSafety"));await transferClick({target:{closest(){return button;}},preventDefault(){}});assert.equal(applyRequests.length,1);assert.equal(applyRequests[0].url,'/api/restore/apply');assert.equal(applyRequests[0].payload.token,'INVENTED_RESTORE');assert.match(get('dialog').innerHTML,/FICTIONAL-backup.zip/);
 let release;c.pendingPreview=new Promise(resolve=>release=resolve);c.fetch=async()=>({ok:true,json:()=>c.pendingPreview});
 const pending=run('TransferUI.preview({size:12})');run("openDialog('<form>NEWER UNSAVED AREA</form>')");release({token:'STALE',counts:{}});await pending;
 assert.match(get('dialog').innerHTML,/NEWER UNSAVED AREA/);
 c.pendingPreview=new Promise(resolve=>release=resolve);const abandoned=run('TransferUI.preview({size:12})');nodes.delete('transferProgress');release({token:'LEFT-PAGE',counts:{}});await abandoned;assert.match(get('dialog').innerHTML,/NEWER UNSAVED AREA/);
 let releaseFirst,releaseSecond;const first=new Promise(r=>releaseFirst=r),second=new Promise(r=>releaseSecond=r);let count=0;c.fetch=async()=>({ok:true,json:()=>++count===1?first:second});
 const firstPreview=run('TransferUI.preview({size:12})'),secondPreview=run('TransferUI.preview({size:14})');
 releaseSecond({token:'LATEST',counts:{}});await secondPreview;assert.match(get('dialog').innerHTML,/LATEST/);releaseFirst({token:'OLDER',counts:{}});await firstPreview;assert.match(get('dialog').innerHTML,/LATEST/);
 let releaseCleanup;c.pendingCleanup=new Promise(resolve=>releaseCleanup=resolve);run('api=async()=>({json:()=>pendingCleanup})');
 const cleanup=click(action('cleanup'));run("openDialog('<form>NEWER UNSAVED NOTE</form>')");releaseCleanup({cutoff:'2024-10-16'});await cleanup;assert.match(get('dialog').innerHTML,/NEWER UNSAVED NOTE/);
 let releaseActivity;c.pendingActivity=new Promise(resolve=>releaseActivity=resolve);run('api=async()=>({json:()=>pendingActivity})');const activity=run("Workspace.handle('activity',{})");run("openDialog('<form>NEWER UNSAVED VISIT</form>')");releaseActivity({items:[]});await activity;assert.match(get('dialog').innerHTML,/NEWER UNSAVED VISIT/);
 assert.equal(run('JSON.stringify(state)'),original);
 // Real beta UI gates and request payload; only invented records and backup names.
 assert.equal(run('TransferUI.betaHTML()'),'');run('TransferUI.resetOpen()');assert.match(get('dialog').innerHTML,/NEWER UNSAVED VISIT/);
 run("state.beta=true;state.revision='FICTIONAL-REVISION';Onboarding={answers:{mode:'map'}}");
 assert.match(run('TransferUI.betaHTML()'),/betaResetOpen/);run('TransferUI.resetOpen()');assert.match(get('dialog').innerHTML,/NULSTIL BETA/);
 const resetButton={disabled:false},resetForm={dataset:{revision:'FICTIONAL-REVISION'},reportValidity(){return false;},querySelector(){return resetButton;}};
 c.removedKeys=[];c.localStorage={removeItem:key=>c.removedKeys.push(key)};
 run(`api=async(url,payload)=>{applyRequests.push({url,payload});return {json:async()=>({safety_backup:'foer-beta-nulstilling-FAKE.zip'})};}`);
 const beforeReset=applyRequests.length;await run('TransferUI.reset').call(run('TransferUI'),resetForm);assert.equal(applyRequests.length,beforeReset);
 resetForm.reportValidity=()=>true;get('betaResetConfirmation').value='NULSTIL BETA';await run('TransferUI.reset').call(run('TransferUI'),resetForm);
 assert.equal(applyRequests.at(-1).url,'/api/beta/reset');assert.equal(applyRequests.at(-1).payload.revision,'FICTIONAL-REVISION');assert.equal(applyRequests.at(-1).payload.confirmation,'NULSTIL BETA');
 assert.equal(get('betaResetError').textContent,'');assert.match(get('dialog').innerHTML,/foer-beta-nulstilling-FAKE.zip/);assert.match(get('dialog').innerHTML,/betaResetRestart/);
 assert.deepEqual(c.removedKeys,['ltm-welcome-seen','ltm-onboarding-draft']);assert.equal(run('Onboarding.answers'),null);
 console.log('Settings language: equal real save payloads, stable options/limits, escaped names, backup consent/token gates and abandoned/out-of-order preview protection passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
