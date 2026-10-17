// Real API/queue/refresh handlers and invented responses; no real server, files or accounts.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const nodes=new Map(),requests=[],timers=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',outerHTML:'',textContent:'',value:'',dataset:{},style:{},open:false,hasForm:false,showModal(){this.open=true;},close(){this.open=false;},querySelector(){return this.hasForm?{}:null;},addEventListener(){}});return nodes.get(id);};
const fixture={revision:'r1',today:'2026-10-17',cards:[],areas:[],notes:[],settings:{}};
const response=(payload,status=200,broken=false)=>({ok:status<400,status,json:async()=>{if(broken)throw Error('Invented broken JSON');return payload;},clone(){return {json:async()=>{if(broken)throw Error('Invented broken JSON');return payload;}};}});
let answer=async()=>response({ok:true}),confirmChoice=false;
const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,frontResizeObserver:null,DistrictMap:{dispose(){}},
 setTimeout(fn,delay){timers.push({fn,delay});return timers.length;},clearTimeout(id){if(timers[id-1])timers[id-1].cleared=true;},
 window:{addEventListener(){},confirm:()=>confirmChoice},
 document:{getElementById:get,querySelector:()=>({content:'FICTIONAL_TOKEN'}),querySelectorAll:()=>[],addEventListener(){}},
 fetch:async(url,options={})=>{const request={url,body:options.body?JSON.parse(options.body):null};requests.push(request);return answer(request,options);}};
vm.createContext(c);for(const file of ['i18n.js','geo.js','workspace.js'])vm.runInContext(read(file),c);
const app=read('app.js');vm.runInContext(app.slice(0,app.indexOf('(async()=>{try{await refresh();')),c);
const run=code=>vm.runInContext(code,c);c.fixture=fixture;
run("state=JSON.parse(JSON.stringify(fixture));page='Indstillinger';render=()=>{};GeoUI.loaded=false;GeoUI.dirty=false;I18n.set('en');saved()");
const capture=async promise=>{try{await promise;assert.fail('Expected a rejection');}catch(error){return error;}};
const reset=()=>run("WriteGuard.reviewed();state=JSON.parse(JSON.stringify(fixture));saved();el('dialog').open=false;el('dialog').hasForm=false");
(async()=>{
 // A POST preview is a read: failures preserve drafts and do not claim an uncertain write.
 answer=async()=>{throw Error('Invented offline');};
 for(const code of ["api('/api/state')","api('/api/mutate',{action:'geo.preview',data:{}})","api('/api/share/prepare',{card_id:'fictional'})"]){
  const error=await capture(run(code));c.lastError=error;run('failed(lastError)');assert.equal(error.writing,false);assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('SaveStatus.kind'),'saved');
 }
 // Known rejections and expired sessions differ from an unknown write outcome.
 answer=async()=>response({error:'Data er ændret fra en anden fane eller enhed. Genindlæs data før du gemmer; dine felter er ikke overskrevet.'},400);
 c.lastError=await capture(run("api('/api/mutate',{action:'note.save',data:{text:'Invented'}})"));run('failed(lastError)');assert.equal(run('WriteGuard.uncertain'),false);assert.match(get('saveState').innerHTML,/The change was rejected/);
 run("I18n.errorContent(el('formError'),lastError)");assert.match(get('formError').textContent,/another tab or device/);run("I18n.set('da');I18n.errorContent(el('formError'),lastError)");assert.match(get('formError').textContent,/anden fane/);run("I18n.set('en')");
 answer=async()=>response({},401);await capture(run("api('/api/state')"));assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('WriteGuard.loginExpired'),true);assert.match(get('saveState').innerHTML,/session has expired/);
 get('dialog').open=true;get('dialog').hasForm=true;const beforeExpiredClose=requests.length;confirmChoice=false;await run('closeRequested()');assert.equal(get('dialog').open,true);confirmChoice=true;await run('closeRequested()');assert.equal(get('dialog').open,false);assert.equal(requests.length,beforeExpiredClose,'Expired login never triggers autosave on close');
 reset();
 // An ambiguous first write cancels the queued second write and blocks any explicit resend.
 let rejectWrite;answer=()=>new Promise((resolve,reject)=>{rejectWrite=reject;});
 const first=run("mutate('note.save',{text:'FIRST INVENTED NOTE'})");const firstResult=capture(first);
 const second=run("mutate('note.save',{text:'SECOND INVENTED NOTE'})");const secondResult=capture(second);
 await new Promise(resolve=>setImmediate(resolve));const sent=requests.length;rejectWrite(Error('Invented lost response'));
 assert.equal((await firstResult).kind,'uncertain');assert.equal((await secondResult).kind,'blocked');assert.equal(requests.length,sent);assert.equal(run('WriteGuard.uncertain'),true);
 const beforeBlocked=requests.length;await capture(run("api('/api/share/publish',{fixture:true})"));assert.equal(requests.length,beforeBlocked);
 answer=async()=>response({ok:true});await run('Workspace.checkConnection()');run('saved()');assert.equal(run('WriteGuard.uncertain'),true);assert.equal(run('SaveStatus.kind'),'error');
 await run("api('/api/geo/pause',{})");await run("api('/api/logout',{})");assert.equal(run('WriteGuard.uncertain'),true,'Control actions do not prove the earlier write');
 get('cardForm').dataset.id='fictional';const autosaves=timers.filter(t=>t.delay===700).length;run('scheduleCardSave()');assert.equal(timers.filter(t=>t.delay===700).length,autosaves);
 // Declining close preserves the form. Accepting close never invokes autosave or repeats a POST.
 get('dialog').open=true;get('dialog').hasForm=true;get('dialog').innerHTML='INVENTED UNSAVED FORM';get('cardForm').value='INVENTED VALUE';
 const beforeClose=requests.length;confirmChoice=false;await run('closeRequested()');assert.equal(get('dialog').open,true);assert.equal(get('cardForm').value,'INVENTED VALUE');
 confirmChoice=true;await run('closeRequested()');assert.equal(get('dialog').open,false);assert.equal(requests.length,beforeClose);
 // An old manual refresh must not discard a newer edit or release the guard.
 let releaseReview;answer=()=>new Promise(resolve=>releaseReview=resolve);const staleReview=run("Workspace.handle('refresh',{})");await new Promise(resolve=>setImmediate(resolve));run("openDialog('<form>NEWER REVIEW DRAFT</form>')");releaseReview(response({...fixture,revision:'ignored-old-read'}));await staleReview;assert.equal(run('WriteGuard.uncertain'),true);assert.equal(run('state.revision'),'r1');assert.match(get('dialog').innerHTML,/NEWER REVIEW DRAFT/);await run('closeRequested()');
 // Only an explicit fresh snapshot releases the guard; it is still labelled for review.
 answer=async request=>response(request.url==='/api/state'?{...fixture,revision:'r2',notes:[{id:'server-note',text:'FIRST INVENTED NOTE'}]}:{ok:true});
 const beforeReview=requests.length;await run("Workspace.handle('refresh',{})");assert.equal(requests.slice(beforeReview).filter(r=>r.body).length,0);assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('state.revision'),'r2');assert.equal(run('SaveStatus.kind'),'review');
 // Broken acknowledgements and server errors are uncertain, even when HTTP headers arrived.
 for(const mode of ['broken','empty-revision','missing-revision','server-error']){
  reset();answer=async()=>mode==='server-error'?response({error:'Invented server failure'},500):mode==='empty-revision'?response({result:{},revision:''}):mode==='missing-revision'?response({result:{}}):response({},200,true);
  const error=await capture(run("api('/api/mutate',{action:'note.save',data:{text:'Invented'}})"));assert.equal(error.kind,'uncertain');assert.equal(run('WriteGuard.uncertain'),true);
 }
 reset();answer=async()=>response({},200,true);const brokenPreview=await capture(run("api('/api/mutate',{action:'setup.preview',data:{}})"));assert.equal(brokenPreview.kind,'response');assert.equal(run('WriteGuard.uncertain'),false);
 // A confirmed mutation followed by a failed refresh is saved, but requires a fresh snapshot.
 reset();answer=async request=>{if(request.url==='/api/mutate')return response({result:{id:'known'},revision:'r-confirmed'});throw Error('Invented refresh failure');};
 await capture(run("mutate('note.save',{id:'known',text:'Invented confirmed note'})"));assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('WriteGuard.needsReview'),true);assert.equal(run('SaveStatus.kind'),'review');assert.match(get('saveState').innerHTML,/The change is saved/);run('saved()');assert.equal(run('SaveStatus.kind'),'review');
 // Queue data is a snapshot. A later success cannot close or clear a newer dialog.
 reset();get('cardForm').dataset.id='';let releaseFirst,revision='r1';const queued=[];
 answer=async request=>{if(request.url==='/api/state')return response({...fixture,revision});queued.push(request.body);if(queued.length===1)return new Promise(resolve=>{releaseFirst=()=>{revision='r3';resolve(response({result:{},revision}));};});revision='r4';return response({result:{},revision});};
 run("openDialog('<form>OLDER FORM</form>');queuedData={text:'ORIGINAL QUEUED VALUE'}");
 const oldSave=run("mutate('note.save',{text:'FIRST'})"),queuedSave=run("mutate('note.save',queuedData)");await new Promise(resolve=>setImmediate(resolve));
 run("queuedData.text='CHANGED AFTER QUEUEING';openDialog('<form>NEWER FORM</form>')");get('formError').textContent='NEWER ERROR';releaseFirst();await Promise.all([oldSave,queuedSave]);
 assert.equal(queued[1].data.text,'ORIGINAL QUEUED VALUE');assert.equal(get('dialog').open,true);assert.match(get('dialog').innerHTML,/NEWER FORM/);assert.equal(get('formError').textContent,'NEWER ERROR');
 assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('WriteGuard.needsReview'),false);
 // A late card save cannot clear or close a newer form, even for a newly created card.
 reset();get('cardForm').reportValidity=()=>true;get('cardForm').dataset.id='';let releaseCard;
 c.cardWrite=new Promise(resolve=>releaseCard=resolve);run("const realMutate=mutate;cardFormData=()=>({name:'INVENTED'});mutate=()=>cardWrite;openDialog('<form>OLDER CARD</form>')");
 const cardSave=run('saveCard(true)');run("openDialog('<form>NEWER CARD</form>');dialogDirty=true");releaseCard();await cardSave;assert.equal(get('dialog').open,true);assert.equal(run('dialogDirty'),true);assert.match(get('dialog').innerHTML,/NEWER CARD/);run('mutate=realMutate');
 // A timed-out write is not replayed, and its timeout is always cleaned up.
 reset();c.AbortController=class{constructor(){this.signal={addEventListener:(name,fn)=>this.listener=fn};}abort(){this.signal.aborted=true;this.listener?.();}};
 answer=(request,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Error('Invented timeout'))));
 const timeoutWrite=capture(run("api('/api/mutate',{action:'note.save',data:{text:'Invented timeout'}})"));const timeout=timers.at(-1);assert.equal(timeout.delay,60000);timeout.fn();assert.equal((await timeoutWrite).kind,'uncertain');assert.equal(timeout.cleared,true);assert.equal(run('WriteGuard.uncertain'),true);
 reset();const timeoutRead=capture(run("api('/api/state')")),readTimer=timers.at(-1);assert.equal(readTimer.delay,30000);readTimer.fn();assert.equal((await timeoutRead).writing,false);assert.equal(readTimer.cleared,true);assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('SaveStatus.kind'),'saved');
 // A GET timeout also covers a JSON body that stalls after successful HTTP headers.
 reset();answer=async(request,options)=>({ok:true,status:200,headers:{get:()=> 'application/json'},clone:()=>({json:()=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(Error('Invented stalled body'))))})});
 const stalledBody=capture(run("api('/api/state')"));await new Promise(resolve=>setImmediate(resolve));const bodyTimer=timers.at(-1);bodyTimer.fn();assert.equal((await stalledBody).kind,'response');assert.equal(bodyTimer.cleared,true);assert.equal(run('WriteGuard.uncertain'),false);
 console.log('Request safety: read-only previews, rejection/login distinction, unknown/invalid acknowledgements, cancelled queued writes, paused autosave, explicit snapshot review, known-save refresh failures and preserved newer dialogs passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
