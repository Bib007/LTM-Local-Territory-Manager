// Real queue and receipt functions, fictional responses only. Browser coverage lives in scripts/.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
function fixture(){
 const nodes=new Map(),requests=[];const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,querySelector(){return null;},querySelectorAll(){return [];},showModal(){this.open=true;},show(){this.open=true;},close(){this.open=false;},addEventListener(){}});return nodes.get(id);};
 const complete={revision:'r0',today:'2026-11-01',cards:[],areas:[],notes:[],publishers:[],loans:[],completions:[],ib:[],ignored:[],visits:[],recovery:[],maps:[],settings:{},profile:{snapshot:'page-base'}};
 let answer;
 const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,WeakMap,frontResizeObserver:null,DistrictMap:{dispose(){}},ProfilesUI:{dialogBase:'',dialog(){},afterRender(){},canAction:()=>true},
  setTimeout:()=>0,clearTimeout(){},window:{addEventListener(){},confirm:()=>true},document:{getElementById:get,querySelector:()=>({content:'FICTIONAL'}),querySelectorAll:()=>[],addEventListener(){}},
  fetch:async(url,options={})=>{const request={url,body:options.body?JSON.parse(options.body):null};requests.push(request);return answer(request);}};
 vm.createContext(c);for(const file of ['i18n.js','geo.js','workspace.js'])vm.runInContext(read(file),c);
 const app=read('app.js');vm.runInContext(app.slice(0,app.indexOf('(async()=>{try{await refresh();')),c);
 const run=code=>vm.runInContext(code,c);c.complete=complete;
 run("state=structuredFixture=JSON.parse(JSON.stringify(complete));render=()=>{};saved()");
 return {c,get,requests,run,setAnswer:fn=>answer=fn,complete};
}
const response=(data,status=200)=>({ok:status<400,status,json:async()=>data,clone:()=>({json:async()=>data})});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 {
  const f=fixture();let fork=0,release;const writes=[];
  f.setAnswer(async request=>{
   if(request.url==='/api/profiles/edit-base')return response({snapshot:'editor-'+(++fork)});
   if(request.url==='/api/profiles/edit-base/release')return response({ok:true});
   writes.push(request.body);if(writes.length===1)await new Promise(resolve=>release=resolve);
   return response({revision:'r'+writes.length,profile_snapshot:'successor-'+writes.length,state:{...f.complete,revision:'r'+writes.length}});
  });
  f.run("openDialog('<form>A</form>')");await f.run('EditorBases.current.ready');
  const first=f.run("mutate('card.save',{id:'fictional',name:'A1'},{close:false})");
  const second=f.run("mutate('card.save',{id:'fictional',name:'A2'},{close:false})");await tick();
  f.run("openDialog('<form>B</form>')");await f.run('EditorBases.current.ready');release();await Promise.all([first,second]);await tick();
  assert.equal(writes[0].profile_snapshot,'editor-1');assert.equal(writes[1].profile_snapshot,'successor-1');
  assert.equal(f.run('EditorBases.current.base'),'editor-2');assert.equal(f.run('ProfilesUI.dialogBase'),'editor-2');
  assert.ok(f.requests.some(r=>r.url.endsWith('/release')&&r.body.snapshot==='successor-2'));
  assert.ok(!f.requests.some(r=>r.url.endsWith('/release')&&r.body.snapshot==='editor-2'));
  console.log('PASS own editor base, chained successor, newer dialog isolation, delayed release');
 }
 {
  const f=fixture();let writes=0;
  f.setAnswer(async request=>{writes++;return response({revision:'saved-revision',profile_snapshot:'next',state_unavailable:true});});
  await assert.rejects(f.run("mutate('card.save',{id:'fictional'},{close:false})"));
  assert.equal(f.run('WriteGuard.needsReview'),true);assert.equal(f.run('WriteGuard.uncertain'),false);
  assert.match(f.run('SaveStatus.message'),/gemt/);assert.doesNotMatch(f.run('SaveStatus.message'),/afvist/);
  await assert.rejects(f.run("mutate('card.save',{id:'fictional'},{close:false})"));assert.equal(writes,1);
  console.log('PASS known commit/read failure blocks repeat without false rejection or extra GET');
 }
 {
  const f=fixture();f.setAnswer(async()=>response({error:'Redigeringens udgangspunkt er udløbet.',code:'edit_base_unavailable'},400));
  await assert.rejects(f.run("mutate('card.save',{id:'fictional'},{close:false})"));
  assert.match(f.run('SaveStatus.message'),/Kladden er bevaret/);assert.doesNotMatch(f.run('SaveStatus.message'),/afvist/);
  console.log('PASS unverifiable base has concrete draft-preserving feedback');
 }
 {
  const f=fixture();let writes=0,release;
  f.setAnswer(async()=>{writes++;await new Promise(resolve=>release=resolve);return response({revision:'r1',state:{...f.complete,revision:'r1'}});});
  const input={name:'name',type:'text',dataset:{},value:'Fiktiv start'};
  const form=f.get('cardForm');form.dataset.id='fictional';form.reportValidity=()=>true;form.querySelectorAll=()=>[input];
  f.c.input=input;f.c.form=form;
  f.run("state.profile=null;FormDrafts.forms.set(form,{confirmed:FormDrafts.signature(form),pending:null});cardFormData=()=>({id:'fictional',name:input.value});dialogDirty=false;");
  await f.run('saveCard(false)');assert.equal(writes,0);assert.equal(f.run('SaveStatus.message'),'Ingen nye ændringer');
  input.value='Fiktiv ny';const first=f.run('saveCard(false)');await tick();const duplicate=f.run('saveCard(false)');await tick();assert.equal(writes,1);
  release();await Promise.all([first,duplicate]);await f.run('saveCard(false)');assert.equal(writes,1);
  input.value='Fiktiv mellem';const changed=f.run('saveCard(false)');await tick();
  input.value='Fiktiv nyeste';release();await changed;
  assert.equal(f.run('dialogDirty'),true);assert.equal(f.run('SaveStatus.kind'),'saving');
  const newest=f.run('saveCard(false)');await tick();release();await newest;
  assert.equal(f.run('dialogDirty'),false);assert.equal(writes,3);
  console.log('PASS unchanged card skips write and concurrent identical saves coalesce');
  console.log('PASS edits during in-flight save remain dirty until their own confirmation');
 }
 {
  const f=fixture();let release,write=0;
  f.run('state.profile=null');
  f.setAnswer(async request=>{write++;await new Promise(resolve=>release=resolve);return response({revision:'r'+write,state:{...f.complete,profile:null,revision:'r'+write}});});
  f.run("openDialog('<form>Fiktiv aflevering</form>')");
  const first=f.run("mutate('loan.finish',{id:'fictional-loan'})");await tick();
  const duplicate=f.run("mutate('loan.finish',{id:'fictional-loan'})");
  assert.equal(first,duplicate);assert.equal(write,1);assert.equal(f.get('dialog').dataset.backgroundSave,'yes');
  f.run("saved();FormDrafts.idle()");assert.equal(f.run('SaveStatus.kind'),'saving');
  const second=f.run("mutate('area.save',{name:'Fiktivt område'},{close:false})");
  release();await first;await tick();assert.equal(f.run('PendingSaves.count'),1);assert.equal(f.run('SaveStatus.kind'),'saving');
  release();await second;assert.equal(f.run('PendingSaves.count'),0);assert.equal(f.run('SaveStatus.kind'),'saved');
  console.log('PASS duplicate commands coalesce and progress remains pending until the whole queue settles');
 }
 {
  const f=fixture();let release,writes=0;
  f.run('state.profile=null');
  f.setAnswer(async()=>{writes++;await new Promise(resolve=>release=resolve);return response({revision:'committed',state_unavailable:true});});
  const first=f.run("mutate('card.save',{id:'fictional'})");
  const second=f.run("mutate('card.save',{id:'fictional',name:'later'})");
  const results=Promise.allSettled([first,second]);await tick();release();await results;
  assert.equal(writes,1);assert.equal(f.run('WriteGuard.needsReview'),true);
  console.log('PASS an accepted but unreadable receipt blocks already queued dependent commands');
 }
 {
  const f=fixture();let release,renders=0;
  f.run('state.profile=null');f.c.countRender=()=>renders++;f.run('render=countRender');
  f.setAnswer(async()=>{await new Promise(resolve=>release=resolve);return response({revision:'r1',state:{...f.complete,revision:'r1',profile:null}});});
  const pending=f.run("mutate('loan.finish',{id:'fictional'},{close:false})");await tick();
  const input={name:'congregation',type:'text',value:'Fiktiv start'},form={id:'settingsForm',dataset:{},querySelectorAll:()=>[input]};
  f.c.settings=form;f.get('app').querySelectorAll=()=>[form];
  f.run("page='Indstillinger';FormDrafts.forms.set(settings,{confirmed:FormDrafts.signature(settings),pending:null})");input.value='Fiktiv nyere kladde';
  release();await pending;assert.equal(renders,0);assert.equal(input.value,'Fiktiv nyere kladde');assert.equal(f.run('state.revision'),'r1');
  console.log('PASS state acknowledgement preserves a newer page form without repainting it');
 }
 {
  const f=fixture();f.run("state.profile=null;page='Kortopsætning';GeoUI.target='fictional';GeoUI.ids=new Set(['new-address']);GeoUI.dirty=true;window.confirm=()=>false");
  assert.equal(f.run('GeoUI.canLeave()'),false);
  f.run('GeoUI.pendingStamp=GeoUI.draftStamp(false)');assert.equal(f.run('GeoUI.canLeave()'),true);
  f.run("GeoUI.ids.add('newer-draft')");assert.equal(f.run('GeoUI.canLeave()'),false);
  console.log('PASS only the exact enqueued geographic draft may leave without discarding newer edits');
 }
 {
  const f=fixture();let release;const writes=[];
  f.run('state.profile=null');
  f.setAnswer(async request=>{writes.push(request.body);await new Promise(resolve=>release=resolve);return response({revision:'r1',state:{...f.complete,revision:'r1',profile:null}});});
  const input={name:'name',type:'text',value:'Fiktiv gammel'},form=f.get('cardForm');form.dataset.id='fictional';form.reportValidity=()=>true;form.querySelectorAll=()=>[input];f.c.input=input;f.c.form=form;
  f.run("openDialog('<form>Fiktivt kort</form>');FormDrafts.forms.set(form,{confirmed:FormDrafts.signature(form),pending:null});cardFormData=()=>({id:'fictional',name:input.value})");
  input.value='Fiktiv første';const first=f.run('saveCard(false)');await tick();
  input.value='Fiktiv nyere';f.run("dialogDirty=true;openDialog('<form>Ny fiktiv redigering</form>')");
  release();await first;await tick();assert.equal(writes[1].data.name,'Fiktiv nyere');
  release();await f.run('saveQueue');assert.match(f.get('dialog').innerHTML,/Ny fiktiv redigering/);assert.equal(f.get('dialog').open,true);
  console.log('PASS opening another editor captures the latest background card autosave');
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
