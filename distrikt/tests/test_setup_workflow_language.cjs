// Setup/import contracts with fictional data only. No filesystem, credentials or remote service access.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8'),nodes=new Map(),writes=[],listeners={};
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',value:'',dataset:{},style:{},open:false,disabled:false,showModal(){this.open=true;},close(){this.open=false;},addEventListener(){}});return nodes.get(id);};
const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,writes,frontResizeObserver:null,DistrictMap:{dispose(){}},setTimeout(){},clearTimeout(){},window:{confirm:()=>true,addEventListener(){}},document:{getElementById:get,querySelector:()=>({content:'FICTIONAL',disabled:false}),querySelectorAll:()=>[],addEventListener(k,fn){(listeners[k]??=[]).push(fn);}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const n of ['i18n.js','setup-ui.js'])vm.runInContext(read(n),c);let src=read('app.js');vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run(`state={revision:'fictional-r1',today:'2026-10-17',cards:[],areas:[{id:'a',name:'Områdenavn <fictional>'}],settings:{}};page='Opstart';GeoUI={loaded:true,addresses:()=>[],load:async()=>{},dispose(){},data:{main_boundary:{points:[[10,55],[10.01,55],[10,55.01]]}}};render=()=>{};refresh=async()=>{};toast=()=>{};SetupUI.options={numbering:'hundreds',start:100,block:100,target:50};SetupUI.areas=[{id:'',name:'Områdenavn <fictional>',kind:'By',prefix:'F',start:'',target:'',polygon:null}];SetupUI.ibDate='2026-10-17';`);
const plan={token:'FICTIONAL_PLAN',cards:[{key:'new1',number:'F101',name:'Navn <fictional>',area_name:'Områdenavn <fictional>',kind:'By',visits:2,address_ids:['a1','a2'],polygon:[[10,55],[10.01,55],[10,55.01]],warning:'Fictional warning'}],visits:2,uncovered:1,excluded:{assigned:1,ignored:1,outside:0,retired:0}};
const ib={token:'FICTIONAL_IB',new:1,existing:1,errors:1,rows:[{line:2,status:'new',card_number:'F101',label:'Private <fictional>',date:'2026-10-17'},{line:3,status:'error',error:'Error <fictional>'}]};c.plan=plan;c.ib=ib;
const contract=html=>(html.match(/(?:data-setup|data-setup-option|data-setup-area-field|data-setup-card-field|data-key|data-index|value|name|placeholder)="[^"]*"/g)||[]).filter(v=>!v.startsWith('placeholder=')).join('\n');
(async()=>{
 assert.equal(run('SetupUI.autoDivisionEnabled'),false);
 assert.doesNotMatch(run('SetupUI.advanced()'),/data-setup="open"/);
 assert.match(run('SetupUI.advanced()'),/data-setup="ib-open"/);
 assert.match(run('SetupUI.advanced()'),/data-card-import="open"/);
 for(const step of [1,2,3,4]){run('SetupUI.step='+step);assert.doesNotMatch(run('SetupUI.page()'),/setupSteps|setup-option|setupConfirm|setupMap/);assert.match(run('SetupUI.page()'),/setupIBFile/);}
 const initialWrites=writes.length;
 for(const action of ['preview','apply','step','return','save-defaults'])await run(`SetupUI.handle('${action}',{step:2})`);
 await run("SetupUI.applyReviewed('setup.apply',{})");assert.equal(writes.length,initialWrites);
 // Exercise archived code only with this explicit test opt-in.
 run('SetupUI.autoDivisionEnabled=true');
 const contracts={},payloads={};for(const lang of ['da','en']){
  run(`SetupUI.autoDivisionEnabled=true;I18n.set('${lang}');SetupUI.plan=JSON.parse(JSON.stringify(plan));SetupUI.ib=JSON.parse(JSON.stringify(ib))`);contracts[lang]=[];
  for(const numbering of ['hundreds','continuous','prefix']){run(`SetupUI.options.numbering='${numbering}';SetupUI.step=2`);const html=run('SetupUI.page()');contracts[lang].push(contract(html));assert.match(html,/<option value="By" data-ui="By" selected>/);assert.match(html,/Områdenavn &lt;fictional&gt;/);assert.doesNotMatch(html,/<fictional>/);}
  for(const step of [1,3,4]){run(`SetupUI.step=${step}`);const html=run('SetupUI.page()');contracts[lang].push(contract(html));assert.doesNotMatch(html,/<fictional>/);if(step===3){assert.match(html,/Navn &lt;fictional&gt;/);assert.match(html,/placeholder="OPRET KORT"/);}if(step===4){assert.match(html,/Private &lt;fictional&gt;/);assert.match(html,/placeholder="IMPORTÉR IB"/);assert.match(html,lang==='en'?/new do-not-call entries/:/nye IB/);}}
  // Real handlers retain the exact confirmation tokens and mutation payloads on both languages.
  run('api=async(url,data)=>{writes.push({url,data});return {json:async()=>({result:{count:1}})}};SetupUI.step=3;SetupUI.busy=false;SetupUI.boundaryDirty=false');get('setupConfirm').value='OPRET KORT';const start=writes.length;await run("SetupUI.handle('apply',{})");run('SetupUI.autoDivisionEnabled=false;SetupUI.ib={...ib,errors:0};SetupUI.busy=false');get('setupIBConfirm').value='IMPORTÉR IB';await run("SetupUI.handle('ib-apply',{})");payloads[lang]=JSON.parse(JSON.stringify(writes.slice(start)));
 }
 assert.deepEqual(contracts.en,contracts.da);assert.deepEqual(payloads.en,payloads.da);assert.equal(payloads.en[0].data.data.confirm,'OPRET KORT');assert.equal(payloads.en[1].data.data.confirm,'IMPORTÉR IB');
 run('SetupUI.autoDivisionEnabled=true;SetupUI.plan=JSON.parse(JSON.stringify(plan));SetupUI.ib={...ib,errors:0};SetupUI.busy=false');get('setupConfirm').value='CREATE CARDS';get('setupIBConfirm').value='IMPORT DNC';const count=writes.length;await assert.rejects(run("SetupUI.handle('apply',{})"),/OPRET KORT/);await assert.rejects(run("SetupUI.handle('ib-apply',{})"),/IMPORTÉR IB/);assert.equal(writes.length,count);
 run('SetupUI.invalidateIB()');get('setupIBConfirm').value='IMPORTÉR IB';await assert.rejects(run("SetupUI.handle('ib-apply',{})"),/Check the do-not-call file/);assert.equal(writes.length,count);
 // A late geographic proposal never replaces changed defaults/area drafts.
 let release;c.pending=new Promise(r=>release=r);run("page='Opstart';SetupUI.plan=null;SetupUI.step=2;api=()=>pending");let pending=run("SetupUI.handle('preview',{})");run("SetupUI.options.target=60;SetupUI.areas[0].name='NEWER AREA'");release({json:async()=>({result:plan})});await pending;assert.equal(run('SetupUI.plan'),null);assert.equal(run('SetupUI.areas[0].name'),'NEWER AREA');assert.equal(run('SetupUI.busy'),false);
 // Out-of-order file.text() completion: only the newest file reaches the local preview endpoint.
 run("SetupUI.step=4;SetupUI.ibContent='old';SetupUI.ib={...ib,errors:0}");let oldFile,newFile;c.old={size:10,text:()=>new Promise(r=>oldFile=r)};c.newer={size:10,text:()=>new Promise(r=>newFile=r)};const node=get('setupIBFile');c.fileNode=node;get('setupIBDate').value='2026-10-17';run('api=async(url,data)=>{writes.push({url,data});return {json:async()=>({result:{...ib,errors:0}})}}');const start=writes.length;const older=run('SetupUI.readIB(old,fileNode)'),newer=run('SetupUI.readIB(newer,fileNode)');newFile('NEWEST FICTIONAL CSV');await newer;oldFile('OLDER FICTIONAL CSV');await older;assert.equal(writes.length,start+1);assert.equal(writes.at(-1).data.data.content,'NEWEST FICTIONAL CSV');assert.equal(run('SetupUI.ibContent'),'NEWEST FICTIONAL CSV');
 // Changed date invalidates an outstanding preview and its old approval token.
 c.pending=new Promise(r=>release=r);run('api=()=>pending');pending=run('SetupUI.previewIB()');run("SetupUI.ibDate='2026-10-16';SetupUI.invalidateIB()");release({json:async()=>({result:ib})});await pending;assert.equal(run('SetupUI.ib'),null);assert.equal(run('SetupUI.busy'),false);
 // Leaving while a preview is pending never navigates back into setup or accepts the result.
 c.pending=new Promise(r=>release=r);run('api=()=>pending');pending=run('SetupUI.previewIB()');run("page='Indstillinger'");release({json:async()=>({result:ib})});await pending;assert.equal(run('SetupUI.ib'),null);assert.equal(run('page'),'Indstillinger');
 // Failed/oversize files cannot leave an earlier valid token or invisible old CSV available for approval.
 run("page='Opstart';SetupUI.ib={...ib,errors:0};SetupUI.ibContent='OLD FILE'");c.large={size:2000001,text(){throw Error('Must not read oversized file');}};await run('SetupUI.readIB(large,fileNode)');assert.equal(run('SetupUI.ib'),null);assert.equal(run('SetupUI.ibContent'),'');assert.match(get('setupError').textContent,/2 MB/);
 run("api=async()=>{throw Error('FICTIONAL FAILURE')};SetupUI.ibContent='FICTIONAL CSV'");await run('SetupUI.previewIB()');assert.equal(run('SetupUI.ib'),null);assert.match(get('setupError').textContent,/FICTIONAL FAILURE/);
 // A preview may observe current server data after another user has saved.
 // A different, newer client state arriving during that request still wins.
 run("SetupUI.ibContent='FICTIONAL CSV';state.revision='old';api=async()=>{state.revision='server-observed';return {json:async()=>({result:ib,revision:'server-observed'})};}");
 await run('SetupUI.previewIB()');assert.ok(run('SetupUI.ib'));
 c.pending=new Promise(r=>release=r);run("SetupUI.ib=null;api=()=>pending");pending=run('SetupUI.previewIB()');run("state.revision='newer-state'");release({json:async()=>({result:ib,revision:'older-response'})});await pending;
 assert.equal(run('SetupUI.ib'),null);assert.match(get('setupError').textContent,/changed during the check/);
 console.log('Advanced setup/IB: bilingual forms, canonical types/numbering/confirmation payloads, escaped private samples, stale proposals, current preview basis, out-of-order files, date/navigation invalidation and failed-file approval guards passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
