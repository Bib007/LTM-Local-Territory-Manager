// Real read/review handlers, fictional addresses and no network/storage writes.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),nodes=new Map(),listeners={},writes=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',dataset:{},style:{},open:false,showModal(){this.open=true;},addEventListener(){}});return nodes.get(id);};
const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,writes,frontResizeObserver:null,DistrictMap:{dispose(){}},setTimeout(){},clearTimeout(){},window:{addEventListener(){},confirm:()=>true},document:{getElementById:get,querySelector:()=>({content:'INVENTED'}),addEventListener(k,fn){(listeners[k]??=[]).push(fn);}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js'])vm.runInContext(read(name),c);const src=read('app.js');vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run(`state={today:'2026-10-16',cards:[{id:'c1',number:'101',area_id:'a',front_revision:true,back_revision:true,address_ids:['a1'],addresses:[],geo_polygon:[[10,55],[10.01,55],[10.01,55.01]]},{id:'c2',number:'102',temporary:true,back_revision:true,address_ids:['a1','old'],addresses:[]}],
areas:[{id:'a',name:'Kort <fictional>'}],loans:[{id:'l',card_id:'c2',publisher_id:'p'}],publishers:[{id:'p',name:'Forkynder <fictional>'}],ib:[{id:'ib1',card_id:'c1',road:'IB <fictional>',number:'1',date:'2026-09-15'}],ignored:[{id:'ignored',address_id:'a3',reason:'Se bort fra <fictional>',date:'2026-09-15'}]};
GeoUI={loaded:true,load:async()=>{},data:{status:{a1:{card_id:'c1',card_number:'101',reserved:true},a2:{within:[{card_id:'c1',card_number:'101'}]}},changes:[{id:'change',kind:'changed',at:'2026-10-15',before:{label:'Adresse <before>',count:1},after:{label:'Adresse <after>',count:2}}]},addresses:()=>[{id:'a1',road:'Vejnavn <fictional>',number:'1',label:'Adresse <duplicate>',postcode:'9999',type:'Hus',count:1},{id:'a2',road:'Se bort fra',number:'2',postcode:'9999',type:'Kontor',count:1},{id:'a3',road:'IB <fictional>',number:'3',postcode:'9999',type:'Lejlighed',count:1},{id:'old',retired:true,road:'Old',number:'4',postcode:'9999',type:'Hus',count:1}]};mutate=async(action,data,options)=>writes.push({action,data,options});`);
const original=run('JSON.stringify(state)'),contracts={},payloads={};
const contract=html=>(html.match(/(?:data-action|data-tab|data-module|data-id|data-side|data-work|value)="[^"]*"/g)||[]).join('\n');
const click=listeners.click.find(fn=>String(fn).includes("case 'confirm-approve'"));
(async()=>{
 for(const language of ['da','en']){
  run(`I18n.set('${language}');query='';addressPostcode='';addressPage=0`);contracts[language]=[];
  for(const tab of ['Mangler på kort','Inden for kortgrænse','På kort','Se bort fra','IB','Genprint']){run('addressTab='+JSON.stringify(tab));const html=run('addressesPage()');contracts[language].push(contract(html));assert.doesNotMatch(html,/<fictional>/);if(tab==='IB')assert.match(html,/IB &lt;fictional&gt;/);}
  run("addressTab='På kort'");assert.match(run('addressesPage()'),language==='en'?/Reserved for card 101/:/Reserveret til kort 101/);
  assert.match(run('Workspace.checks()'),/Adresse &lt;duplicate&gt;/);assert.match(run('Workspace.addressChanges()'),/Adresse &lt;after&gt;/);assert.match(run('Workspace.checks()'),language==='en'?/>Missing area<\//:/>Mangler område<\//);
  const start=writes.length;await run("Workspace.handle('accept-address',{id:'change'})");await run("Workspace.handle('reject-address',{id:'change'})");
  const button={dataset:{action:'confirm-approve',id:'c1',side:'front'},closest(selector){return selector==='[data-action]'?this:null;}};await click({target:button,preventDefault(){}});payloads[language]=JSON.parse(JSON.stringify(writes.slice(start).map(({action,data})=>({action,data}))));
  assert.equal(run('JSON.stringify(state)'),original);
 }
 assert.deepEqual(contracts.en,contracts.da);assert.deepEqual(payloads.en,payloads.da);assert.equal(payloads.en[0].data.decision,'accept');assert.equal(payloads.en[1].data.decision,'reject');assert.equal(payloads.en[2].data.side,'front');
 c.window.confirm=()=>false;const before=writes.length;await run("Workspace.handle('accept-address',{id:'change'})");assert.equal(writes.length,before);
 let release;c.pendingLoad=new Promise(r=>release=r);run('GeoUI.load=()=>pendingLoad');const pending=run("Workspace.inspect('addressChanges')");run("openDialog('<form>NEWER UNSAVED DRAFT</form>')");release();await pending;assert.match(get('dialog').innerHTML,/NEWER UNSAVED DRAFT/);
 console.log('Address workflows: bilingual tabs/values, escaped private/user text, card-check findings, equal review/reprint payloads, cancellation and delayed inspection draft protection passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
