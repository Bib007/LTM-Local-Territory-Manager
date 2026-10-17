// Real editor methods, invented records and delayed local responses. No real account or database.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8'),nodes=new Map(),listeners={},writes=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,showModal(){this.open=true;},close(){this.open=false;},addEventListener(){}});return nodes.get(id);};
const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,writes,frontResizeObserver:null,DistrictMap:{dispose(){}},setTimeout(){},clearTimeout(){},window:{addEventListener(){},confirm:()=>true},document:{getElementById:get,querySelector:()=>({content:'FICTIONAL',disabled:false}),querySelectorAll:()=>[],addEventListener(k,fn){(listeners[k]??=[]).push(fn);}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const n of ['i18n.js','geo.js','main-boundary.js','boundary-import.js','road-search.js','address-source-ui.js'])vm.runInContext(read(n),c);let src=read('app.js');vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run('const realApi=api,realPreview=GeoUI.preview;');
run(`state={revision:'r1',today:'2026-10-17',cards:[{id:'c1',number:'101',area_id:'area',address_ids:['a1'],geo_polygon:[[10,55],[10.01,55],[10,55.01]]},{id:'c2',number:'102',address_ids:[],geo_polygon:[]}],areas:[{id:'area',name:'Vejnavn <invented>'}],ignored:[],settings:{}};
GeoUI.loaded=true;GeoUI.target='c1';GeoUI.ids=new Set(['a1']);GeoUI.polygon=state.cards[0].geo_polygon.map(p=>p.slice());GeoUI.data={addresses:[{id:'a1',road:'Vejnavn',number:'1',postcode:'9999',floor:'',door:'',label:'Adresse <invented>',type:'Hus',lng:10,lat:55,count:1},{id:'a2',road:'Vejnavn',number:'2',postcode:'9999',label:'B',type:'Kontor',lng:10.001,lat:55.001,count:1}],buildings:[],roads:[],info:{addresses:2},status:{a1:{card_id:'c1'}}};page='Kortopsætning';GeoUI.drawLayers=()=>{};GeoUI.drawBoundary=()=>{};render=()=>{};saved=()=>{};saving=()=>{};toast=()=>{};MapBackground={mode:'road',toolbar:()=>'',detach(){}};`);
const contract=html=>(html.match(/(?:data-geo|data-main|data-action|data-id|name|value)="[^"]*"/g)||[]).join('\n');
const contracts={};const initial=run('JSON.stringify(state)');
(async()=>{
 for(const language of ['da','en']){
  run(`I18n.set('${language}');GeoUI.whole=false;GeoUI.focus=['a1'];GeoUI.mode='choose'`);
  contracts[language]=[contract(run('GeoUI.page()'))];run('GeoUI.updatePanel()');contracts[language].push(contract(get('geoSelection').innerHTML));
  assert.match(get('geoHouse').innerHTML,/Adresse &lt;invented&gt;/);assert.doesNotMatch(get('geoHouse').innerHTML,/<invented>/);
  await run("GeoUI.handle('save')");assert.match(get('dialog').innerHTML,language==='en'?/Save address selection on card 101/:/Gem adressevalget på kort 101/);
  run("GeoUI.target='';");await run("GeoUI.handle('save')");contracts[language].push(contract(get('dialog').innerHTML));assert.match(get('dialog').innerHTML,/<option value="By" data-ui="By">/);assert.match(get('dialog').innerHTML,language==='en'?/>Urban<\//:/>By<\//);
  run("GeoUI.manualDialog()");contracts[language].push(contract(get('dialog').innerHTML));assert.match(get('dialog').innerHTML,/<option value="Hus" data-ui="Hus">/);
  run("GeoUI.target='c1';GeoUI.whole=true;MainBoundaryUI.panel()");contracts[language].push(contract(run('MainBoundaryUI.page()')));contracts[language].push(contract(get('geoSelection').innerHTML));
  run('BoundaryImportUI.open(true)');contracts[language].push(contract(get('dialog').innerHTML));assert.match(get('dialog').innerHTML,language==='en'?/Import overall territory boundary/:/Importér samlet distriktsgrænse/);
  assert.equal(run('JSON.stringify(state)'),initial);
 }
 assert.deepEqual(contracts.en,contracts.da);
 run("I18n.set('en');GeoUI.whole=false;GeoUI.target='c1';GeoUI.dirty=false");
 // A draft change, another editor session and a newer request each invalidate a late selection.
 let release;c.pending=new Promise(r=>release=r);run('GeoUI.preview=()=>pending');let pending=run("GeoUI.selectPreview({mode:'range'})");run("GeoUI.ids.add('a2');GeoUI.polygon.push([10.02,55.02]);GeoUI.dirty=true");release({addresses:[],ignored:[],conflicts:[],outline:[]});await pending;assert.equal(run('GeoUI.ids.size'),2);assert.equal(run('GeoUI.polygon.length'),4);
 c.pending=new Promise(r=>release=r);pending=run("GeoUI.selectPreview({mode:'range'})");run('GeoUI.session++');release({addresses:[],ignored:[],conflicts:[]});await pending;assert.equal(run('GeoUI.ids.size'),2);
 let first,second;c.first=new Promise(r=>first=r);c.second=new Promise(r=>second=r);run('let previews=0;GeoUI.preview=()=>++previews===1?first:second');const old=run("GeoUI.selectPreview({mode:'range'})"),recent=run("GeoUI.selectPreview({mode:'range'})");second({addresses:[{id:'a1'}],ignored:[],conflicts:[],outline:[[10,55],[10.01,55],[10,55.01]]});await recent;first({addresses:[],ignored:[],conflicts:[],outline:[]});await old;assert.equal(run('GeoUI.ids.size'),1);
 // Save validates an immutable draft; changed selection prevents the write entirely.
 c.pending=new Promise(r=>release=r);run('GeoUI.preview=()=>pending;api=async(url,data)=>{writes.push({url,data});return {json:async()=>({})}}');pending=run('GeoUI.save()');run("GeoUI.ids.add('a2')");release({retired:[],conflicts:[],ignored:[]});await assert.rejects(pending,/selection has changed/);assert.equal(writes.length,0);assert.equal(run('GeoUI.saveBusy'),false);
 // Closing the save confirmation while validation is pending cancels before writing.
 c.pending=new Promise(r=>release=r);run("GeoUI.preview=()=>pending;openDialog('<p>Confirm</p>')");pending=run('GeoUI.save()');run('closeDialog()');release({retired:[],conflicts:[],ignored:[]});await assert.rejects(pending,/selection has changed/);assert.equal(writes.length,0);
 // During an accepted write a newer drawing and dialog stay open; no second write is replayed.
 run("GeoUI.ids=new Set(['a1']);GeoUI.preview=async()=>({retired:[],conflicts:[],ignored:[]});openDialog('<p>Save</p>')");let assignRelease;c.assignPending=new Promise(r=>assignRelease=r);c.fresh=JSON.parse(run('JSON.stringify(state)'));run(`api=async(url,data)=>{if(data?.action==='geo.assign'){writes.push({url,data});return assignPending;}return {json:async()=>url==='/api/state'?fresh:GeoUI.data};}`);
 pending=run('GeoUI.save()');await new Promise(r=>setImmediate(r));await run('GeoUI.save()');assert.equal(writes.length,1);run("GeoUI.polygon.push([10.03,55.03]);GeoUI.dirty=true;openDialog('<form>NEWER DRAFT</form>')");assignRelease({json:async()=>({result:{id:'c1'}})});await pending;assert.equal(run('GeoUI.polygon.length'),4);assert.equal(run('GeoUI.dirty'),true);assert.match(get('dialog').innerHTML,/NEWER DRAFT/);assert.equal(writes[0].data.data.polygon.length,3);
 // Boundary-only saves also send a copy and preserve edits made while saving.
 let boundaryRelease;c.boundaryPending=new Promise(r=>boundaryRelease=r);run(`api=async(url,data)=>{if(data?.action==='geo.boundary'){writes.push({url,data});return boundaryPending;}return {json:async()=>url==='/api/state'?fresh:GeoUI.data};}`);pending=run('GeoUI.saveBoundary()');run('GeoUI.polygon[0][0]=10.04');boundaryRelease({json:async()=>({})});await pending;assert.equal(writes.at(-1).data.data.polygon[0][0],10);assert.equal(run('GeoUI.polygon[0][0]'),10.04);assert.equal(run('GeoUI.dirty'),true);
 // Showing an address never aliases the stored polygon before explicit save.
 run("GeoUI.dirty=false;GeoUI.dispose=()=>{}");await run("GeoUI.handle('show-address','a1')");run('GeoUI.polygon[0][0]=99');assert.equal(run('state.cards[0].geo_polygon[0][0]'),10);
 // A late cleanup preview cannot replace a newer modal or changed drawing.
 c.pending=new Promise(r=>release=r);run("GeoUI.whole=true;GeoUI.dirty=false;api=()=>pending");pending=run('MainBoundaryUI.preview()');run("openDialog('<form>NEWER REVIEW</form>')");release({json:async()=>({result:{}})});await pending;assert.match(get('dialog').innerHTML,/NEWER REVIEW/);assert.equal(run('MainBoundaryUI.pending'),null);
 // Closing/reopening a file chooser invalidates its delayed file read before any API call.
 run('BoundaryImportUI.open(true)');let fileRelease;c.file={size:10,name:'fictional.kml',text:()=>new Promise(r=>fileRelease=r)};pending=run('BoundaryImportUI.read(file)');run("openDialog('<form>OTHER DIALOG</form>')");fileRelease('<kml/>');await pending;assert.match(get('dialog').innerHTML,/OTHER DIALOG/);
 // The preview revision is the request revision, never a later revision seen on completion.
 run('BoundaryImportUI.open(true);BoundaryImportUI.show=()=>{};state.revision="before"');c.file={size:10,name:'fictional.kml',text:async()=>'<kml/>'};let importRelease;c.importPending=new Promise(r=>importRelease=r);run('api=()=>importPending');pending=run('BoundaryImportUI.read(file)');await new Promise(r=>setImmediate(r));run('state.revision="after"');importRelease({json:async()=>({result:{format:'KML',boundaries:[{name:'Vejnavn',points:[[10,55],[10.01,55],[10,55.01]]}]}})});await pending;assert.equal(run('BoundaryImportUI.revision'),'before');assert.throws(()=>run('BoundaryImportUI.apply()'),/Data has changed/);
 // Exercise the real API wrapper: an accepted mutation advances the client revision.
 // That server acknowledgement must not be mistaken for an edit to the drawing.
 c.serverState=JSON.parse(run('JSON.stringify(state)'));
 c.serverState.cards.push({id:'created',number:'103',address_ids:['a1'],geo_polygon:[[10,55],[10.01,55],[10,55.01]]});
 c.serverState.revision='before-real-save';let revision='before-real-save';const realRequests=[];
 c.fetch=async(url,options)=>{const body=options.body?JSON.parse(options.body):null;realRequests.push({url,body});let payload;
  if(url==='/api/mutate'){
   if(body.action==='geo.preview')payload={result:{retired:[],conflicts:[],ignored:[]},revision};
   else {revision=body.action==='geo.assign'?'after-real-save':'after-real-boundary';c.serverState.revision=revision;payload={result:{id:'created'},revision};}
  }else payload=url==='/api/state'?c.serverState:run('GeoUI.data');
  return {ok:true,json:async()=>payload,clone(){return {json:async()=>payload};}};
 };
 run("api=realApi;GeoUI.preview=realPreview;state.revision='before-real-save';GeoUI.whole=false;GeoUI.target='';GeoUI.ids=new Set(['a1']);GeoUI.polygon=[[10,55],[10.01,55],[10,55.01]];GeoUI.dirty=true;openDialog('<p>Real API confirmation</p>')");
 await run("GeoUI.save('103',{kind:'By'})");assert.equal(run('GeoUI.target'),'created');assert.equal(run('GeoUI.dirty'),false);assert.equal(run('state.revision'),'after-real-save');assert.equal(get('dialog').open,false);
 assert.equal(realRequests.find(r=>r.body?.action==='geo.assign').body.data._revision,'before-real-save');
 run('GeoUI.whole=true;GeoUI.dirty=true');await run('GeoUI.saveBoundary(true)');assert.equal(run('GeoUI.dirty'),false);assert.equal(run('state.revision'),'after-real-boundary');
 // A late download acknowledgement registers its job but cannot close a newer dialog; duplicate starts stop.
 let releaseDownload;c.pendingDownload=new Promise(r=>releaseDownload=r);run("GeoUI.busy=false;GeoUI.poll=()=>{};GeoUI.showJob=()=>{};api=()=>pendingDownload;openDialog('<form>DOWNLOAD FORM</form>')");const download=run("GeoUI.download('road',{road:'Fictional'})");await assert.rejects(run("GeoUI.download('road',{road:'Fictional'})"));run("openDialog('<form>NEWER DOWNLOAD DRAFT</form>')");releaseDownload({json:async()=>({job_id:'FICTIONAL_JOB'})});await download;assert.equal(run('GeoUI.job'),'FICTIONAL_JOB');assert.equal(get('dialog').open,true);assert.match(get('dialog').innerHTML,/NEWER DOWNLOAD DRAFT/);
 let releaseIgnore;c.pendingIgnore=new Promise(r=>releaseIgnore=r);run("mutate=()=>pendingIgnore;GeoUI.ids=new Set(['a1']);GeoUI.dirty=false");const ignored=run("GeoUI.confirmIgnore('a1','Fictional')");run("GeoUI.session++;GeoUI.ids=new Set(['a1','a2'])");releaseIgnore();await ignored;assert.equal(run('GeoUI.ids.size'),2);assert.equal(run('GeoUI.dirty'),false);
 // A failed old colour save cannot revert the colour of a newer editor/card.
 let rejectColor;c.colorPending=new Promise((r,j)=>rejectColor=j);const color=get('geoColor');color.id='geoColor';color.value='#112233';run("GeoUI.drawBoundary=()=>{};GeoUI.target='c1';GeoUI.drawColor='#000000';mutate=()=>colorPending");const change=listeners.change.find(f=>String(f).includes("e.target.id==='geoColor'")),colorWrite=change({target:color});run("GeoUI.session++;GeoUI.target='c2';GeoUI.drawColor='#abcdef'");rejectColor(Error('Invented old colour rejection'));await colorWrite;assert.equal(run('GeoUI.drawColor'),'#abcdef');
 let releasePrune;c.prunePending=new Promise(r=>releasePrune=r);run("mutate=()=>prunePending;MainBoundaryUI.pending={expected:'OLD'}");const prune=run("MainBoundaryUI.handle('confirm')");run("MainBoundaryUI.pending={expected:'NEWER'}");releasePrune();await prune;assert.equal(run('MainBoundaryUI.pending.expected'),'NEWER');
 console.log('Geographic workflows: bilingual contracts, immutable saves, stale draft/dialog guards, late downloads/ignore/colour/prune writes, file/revision guards and real API revision acknowledgements passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
