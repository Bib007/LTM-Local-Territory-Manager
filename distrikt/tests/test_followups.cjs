// Production collectors and handlers with invented local records. No network or user files.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),nodes=new Map(),writes=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',style:{},dataset:{},open:false,querySelector(){return null;},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});return nodes.get(id);};
const c={console,Date,Intl,Math,Map,Set,Array,Object,Number,String,JSON,Promise,writes,setTimeout(){},clearTimeout(){},
 document:{getElementById:get,querySelector:()=>({content:'FICTIONAL_TOKEN'}),addEventListener(){}},window:{addEventListener(){},confirm:()=>true},fetch(){throw Error('Network forbidden');},frontResizeObserver:null,DistrictMap:{dispose(){}}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','setup-ui.js','navigation.js'])vm.runInContext(read(name),c);
const src=read('app.js');vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run(`state={today:'2026-10-23',cards:[
 {id:'one',number:'101',name:'Name <fictional>',temporary:true,front_revision:true,back_revision:true,address_ids:['shared','shared','retired']},
 {id:'two',number:'102',area_id:'area',geo_polygon:[[10,55],[10.01,55],[10,55.01]],address_ids:['shared']}],
 loans:[{id:'loan',card_id:'one',publisher_id:'person',cycle_start:'2026-01-01',assigned:'2026-01-01'}],publishers:[{id:'person',name:'Person <fictional>'}],ignored:[{id:'i',address_id:'shared'}],areas:[],settings:{},recovery:[]};
 GeoUI={loaded:true,dirty:false,addresses:()=>[{id:'shared',label:'Street <fictional>'},{id:'retired',label:'Old street',retired:true}],data:{changes:[{id:'change',kind:'changed',before:{label:'Before <fictional>',count:1},after:{label:'After <fictional>',count:2}}]},load:async()=>{}};
 render=()=>{};Workspace.menu=()=>{};page='Opfølgninger';`);
(async()=>{
 const before=run('JSON.stringify(state)');
 assert.equal(run('Workspace.followupItems().length'),11);
 assert.equal(run("Workspace.followupItems().filter(r=>r.category==='checks').length"),7);
 assert.equal(run("Workspace.followupItems().filter(r=>r.side).length"),2);
 assert.equal(run("Workspace.followupItems().filter(r=>r.text==='Udleveret fysisk kort · IB-bagsiden skal ajourføres').length"),1,'An assigned changed back is one reprint item, not a second check');
 assert.equal(run('new Set(Workspace.followupItems().map(r=>r.key)).size'),11);
 assert.equal(run('JSON.stringify(state)'),before,'Collecting follow-ups never writes task/card records');
 const contracts=[];
 for(const lang of ['da','en']){
  run(`I18n.set('${lang}');Workspace.followupFilter='all';Workspace.followupQuery=''`);
  const html=run('Workspace.followups()');assert.equal((html.match(/data-followup=/g)||[]).length,11);assert.doesNotMatch(html,/<fictional>/);assert.match(html,/Person &lt;fictional&gt;/);
  contracts.push(html.match(/(?:data-work|data-action|data-side|data-id|data-followup)="[^"]*"/g));
  assert.match(html,lang==='en'?/Follow-up items: 11/:/Til opfølgning: 11/);
  run("Workspace.followupQuery='Street <fictional>'");assert.equal((run('Workspace.followups()').match(/data-followup=/g)||[]).length,4);
  run("Workspace.followupQuery='';Workspace.followupFilter='reprint'");assert.equal((run('Workspace.followups()').match(/data-followup=/g)||[]).length,2);
  const imports=run('SetupUI.imports()');assert.equal((imports.match(/data-history-import="open"/g)||[]).length,1);assert.equal((imports.match(/data-card-import="open"/g)||[]).length,1);assert.equal((imports.match(/data-setup="ib-open"/g)||[]).length,1);assert.doesNotMatch(imports,/data-setup="open"/);
 }
 assert.deepEqual(contracts[0],contracts[1]);
 run('state.cards[0].front_revision=false');assert.equal(run('Workspace.followupItems().length'),10);assert.equal(run("Workspace.followupItems().filter(r=>r.side==='back').length"),1,'Approving a front leaves its changed back pending');
 run("mutate=async(action,data)=>{writes.push({action,data});GeoUI.data.changes=[];};");await run("Workspace.handle('accept-address',{id:'change'})");assert.equal(writes.length,1);assert.deepEqual(JSON.parse(JSON.stringify(writes[0])),{action:'address.change.review',data:{id:'change',decision:'accept'}});assert.equal(get('dialog').open,false,'Review on the page stays on the page');
 // One issue per overlapping pair, with independent duplicate-address checks.
 run("state.cards[0].geo_polygon=[[10,55],[10.01,55],[10,55.01]];state.cards[1].name='Related <fictional>';Workspace.followupFilter='checks';Workspace.followupQuery='';");
 assert.equal(run('Workspace.followupItems().filter(r=>r.relatedCard).length'),1);
 assert.equal(run("Workspace.followupItems().filter(r=>r.text==='Adresse valgt på flere kort: {address}').length"),2);
 const overlapHTML=run('Workspace.followupItems().filter(r=>r.relatedCard).map(r=>Workspace.followupRow(r)).join("")');
 assert.match(overlapHTML,/data-id="one"/);assert.match(overlapHTML,/data-id="two"/);assert.doesNotMatch(overlapHTML,/data-action="approve"/);
 for(const lang of ['da','en']){run(`I18n.set('${lang}');Workspace.followupQuery='Related <fictional>'`);assert.match(run('Workspace.followups()'),/Grænsen overlapper|The boundary overlaps/);}
 // Only explicitly selected, non-critical overlaps can be dismissed.
 const overlapKey=run('Workspace.followupItems().find(r=>r.relatedCard).key');
 const initial=run('Workspace.followupItems().length');
 const criticalHTML=run("Workspace.followupItems().filter(r=>r.side||r.change||r.loan).map(r=>Workspace.followupRow(r)).join('')");
 assert.doesNotMatch(criticalHTML,/data-work="followup-ignore"/,'Critical reprint, loan and address items cannot be dismissed');
 await run(`Workspace.handle('followup-ignore',{key:${JSON.stringify(overlapKey)},value:'ignore'})`);
 assert.equal(writes.at(-1).action,'followup.ignore');
 assert.deepEqual(JSON.parse(JSON.stringify(writes.at(-1).data)),{key:overlapKey,ignored:true,expected_token:''});
 run(`state.followup_ignores=[{key:${JSON.stringify(overlapKey)},ignored:true,token:'fake-token',history:[{ignored:true,at:'2026-10-23T12:00:00Z',actor_name:'Fiktiv bruger'}]}]`);
 assert.equal(run('Workspace.followupItems().length'),initial-1);
 assert.equal(run('Workspace.followupItems(true).filter(r=>r.ignored).length'),1);
 run("Workspace.followupFilter='ignored';Workspace.followupQuery=''");
 const ignoredHTML=run('Workspace.followups()');
 assert.equal((ignoredHTML.match(/data-followup=/g)||[]).length,1);
 assert.match(ignoredHTML,/data-work="followup-ignore"/);
 assert.match(ignoredHTML,/Fiktiv bruger/);
 assert.match(ignoredHTML,/fake-token/);
 assert.match(run('Navigation.html()'),new RegExp('navFollowupCount[^>]*>'+String(initial-1)+'</span>'));
 await run(`Workspace.handle('followup-ignore',{key:${JSON.stringify(overlapKey)},value:'activate'})`);
 assert.deepEqual(JSON.parse(JSON.stringify(writes.at(-1).data)),{key:overlapKey,ignored:false,expected_token:'fake-token'});
 run("state.followup_ignores[0].ignored=false;Workspace.followupFilter='checks'");
 assert.equal(run('Workspace.followupItems().length'),initial,'Reactivated overlap returns to active list and badge');
 run("state.cards[0].geo_polygon=[[11,55],[11.01,55],[11,55.01]]");assert.equal(run('Workspace.followupItems().filter(r=>r.relatedCard).length'),0);
 // A late geographic load cannot navigate away from a newer page or dialog.
 let release;c.pending=new Promise(r=>release=r);run("GeoUI.load=()=>pending;page='Forside'");let waiting=run("Workspace.openFollowups('checks')");await new Promise(r=>setImmediate(r));run("page='Opgaver'");release();await waiting;assert.equal(run('page'),'Opgaver');
 c.pending=new Promise(r=>release=r);run("page='Forside'");waiting=run('Workspace.openFollowups()');await new Promise(r=>setImmediate(r));run("openDialog('<form>NEWER DRAFT</form>')");release();await waiting;assert.equal(run('page'),'Forside');assert.match(get('dialog').innerHTML,/NEWER DRAFT/);
 // Opening local IB import must not override a newer settings tab.
 get('dialog').open=false;c.pending=new Promise(r=>release=r);run("page='Indstillinger';Navigation.settingsSection='import';GeoUI.loaded=false;closeRequested=async()=>{};");waiting=run('SetupUI.open(4)');await new Promise(r=>setImmediate(r));run("Navigation.settingsSection='data'");release();await waiting;assert.equal(run('page'),'Indstillinger');assert.equal(run('Navigation.settingsSection'),'data');
 console.log('Follow-ups: independent issues/sides, duplicate ownership, exact counts, escaped bilingual rows, read-only collection, unchanged approvals and late navigation/import guards passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
