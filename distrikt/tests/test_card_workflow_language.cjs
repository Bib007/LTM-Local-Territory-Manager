// Real render/form/correction paths, with invented records and no network or disk writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),listeners={},nodes=new Map(),writes=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,addEventListener(){},showModal(){this.open=true;},close(){this.open=false;},querySelector(){return null;}});return nodes.get(id);};
class Data{constructor(form){this.values=new Map(form.fields);}get(k){return this.values.get(k)??null;}has(k){return this.values.has(k);}[Symbol.iterator](){return this.values[Symbol.iterator]();}}
const c={console,Date,Intl,Map,Set,Number,String,Math,JSON,Array,Object,Promise,FormData:Data,writes,
 setTimeout(){return 0;},clearTimeout(){},frontResizeObserver:null,location:{origin:'http://127.0.0.1:9999'},
 window:{addEventListener(){}},document:{addEventListener(k,f){(listeners[k]??=[]).push(f);},getElementById:get,querySelector(){return {content:'INVENTED'};}},
 fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','road-search.js','admin.js','ib-ui.js','basemaps.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);
const run=s=>vm.runInContext(s,c);
run(`DistrictMap={dispose(){},html(){return '<div>UNTRANSLATED_PRINT_MAP</div>';},mount(){}};fitFrontCard=()=>{};
state={today:'2026-10-16',cards:[{id:'c',number:'101',name:'Kort <fictional>',area_id:'a',kind:'Land',in_folder:false,temporary:false,addresses:[{road:'Vejnavn',numbers:'1',count:2,type:'Lejlighed'}],geo_addresses:[{id:'u',road:'Vejnavn',number:'1',floor:'1',door:'tv',count:1},{id:'u2',road:'Vejnavn',number:'1',floor:'2',door:'tv',count:1}]}],
archived_cards:[{id:'old',number:'99',name:'Historik',archived:true,addresses:[]}],areas:[{id:'a',name:'Historik'}],publishers:[{id:'p',name:'Forkynder <fictional>'},{id:'p2',name:'Kort'}],
loans:[{id:'l',card_id:'c',publisher_id:'p',assigned:'2026-05-01',cycle_start:'2026-05-01',returned:null},{id:'old-loan',card_id:'old',publisher_id:'p2',assigned:'2026-09-01',returned:'2026-09-15'}],
completions:[{id:'e',card_id:'c',loan_id:'l',date:'2026-09-15'}],ib:[{id:'ib',card_id:'c',address_id:'u',road:'Vejnavn',number:'1, 1 tv',date:'2026-09-10'}],notes:[],ignored:[],settings:{},public_maps:[],visits:[]};
GeoUI={addresses:()=>state.cards[0].geo_addresses,ignored:()=>new Set()};mutate=async(action,data,options)=>writes.push({action,data,options});`);
const original=run('JSON.stringify(state)'),contracts={},payloads={};
const contract=html=>(html.match(/(?:name|data-field|data-tab|data-id|data-module|data-side|value|max|min|maxlength)="[^"]*"/g)||[]).join('\n');
for(const language of ['da','en']){
 run(`I18n.set('${language}');query='';year=2027;loanTab='Opfølgning'`);contracts[language]=[];
 const loans=run('loans()');assert.match(loans,/data-tab="Opfølgning"/);assert.match(loans,/Forkynder &lt;fictional&gt;/);contracts[language].push(contract(loans));
 const history=run('Workspace.history()');assert.match(history,/99 Historik/);assert.match(history,/old-loan/);contracts[language].push(contract(history));
 for(const tab of ['Noter','Historik','IB-bagside','Adresser']){
  run(`detail('c','${tab}')`);contracts[language].push(contract(get('dialog').innerHTML));
  if(tab==='IB-bagside')assert.match(get('dialog').innerHTML,/Vejnavn 1, 1 tv/);
 }
 run("editCard('c')");const html=get('dialog').innerHTML;
 assert.match(html,/name="kind"/);assert.match(html,/value="Land"[^>]*selected/);
 assert.match(html,/value="Lejlighed"[^>]*selected/);assert.match(html,/value="Kort &lt;fictional&gt;"/);
 contracts[language].push(contract(html));
 const background=run("MapBackground.toolbar('test-map')");assert.match(background,/option value="road"/);assert.match(background,/option value="local"/);assert.equal(run('MapBackground.mode'),'road');contracts[language].push(contract(background));
 const fields=[['number','101'],['map_color','#477596'],['name','Kort <fictional>'],['area_id','a'],['kind','Land']],row={querySelectorAll(){return [{dataset:{field:'road'},value:'Vejnavn'},{dataset:{field:'numbers'},value:'1'},{dataset:{field:'count'},value:'2'},{dataset:{field:'type'},value:'Lejlighed'}];}};
 nodes.set('cardForm',{dataset:{id:'c'},fields,querySelectorAll(){return [row];}});payloads[language]=JSON.parse(run('JSON.stringify(cardFormData())'));
 run("AdminUI.correct('l')");contracts[language].push(contract(get('dialog').innerHTML));
 assert.match(get('dialog').innerHTML,/value="p" selected/);assert.match(get('dialog').innerHTML,/name="assigned" value="2026-05-01"/);
 assert.equal(run('JSON.stringify(state)'),original);
}
assert.deepEqual(contracts.en,contracts.da,'Translations must not alter action/tab keys or stored option values');
assert.deepEqual(payloads.en,payloads.da);assert.equal(payloads.en.addresses[0].type,'Lejlighed');assert.equal(payloads.en.addresses[0].count,2);
(async()=>{
 const applied={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}');api=async()=>({json:async()=>({result:{card_number:'101',expected:{assigned:'2026-05-01'},before:{publisher_id:'p',assigned:'2026-05-01'},after:{publisher_id:'p2',assigned:'2026-05-02'},completions:1}})});`);
  const before=writes.length;await run("AdminUI.preview('loan.correct.preview',{id:'l',publisher_id:'p2',assigned:'2026-05-02'})");assert.equal(writes.length,before);
  await run('AdminUI.confirm()');applied[language]=JSON.parse(JSON.stringify(writes.at(-1)));
  assert.equal(run('AdminUI.pending'),null);assert.equal(run('JSON.stringify(state)'),original);
 }
 assert.deepEqual(applied.en.data,applied.da.data);assert.equal(applied.en.action,'loan.correct');assert.equal(applied.en.data.publisher_id,'p2');assert.equal(applied.en.data.expected.assigned,'2026-05-01');
 const bulk={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}');AdminUI.selected.add('c');AdminUI.bulk()`);
  assert.match(get('dialog').innerHTML,/option value="__keep__"/);assert.match(get('dialog').innerHTML,/option value="Land"/);
  run(`api=async()=>({json:async()=>({result:{selected:1,expected:{revision:5},changes:[{number:'101',before:{area_id:'a',kind:'Land'},after:{area_id:'a',kind:'By'}}]}})});`);
  const before=writes.length;await run("AdminUI.preview('card.bulk.edit.preview',{ids:['c'],area_id:'__keep__',kind:'By'})");assert.equal(writes.length,before);
  run('render=()=>{}');await run('AdminUI.confirm()');bulk[language]=JSON.parse(JSON.stringify(writes.at(-1)));
 }
 assert.deepEqual(bulk.en.data,bulk.da.data);assert.equal(bulk.en.action,'card.bulk.edit');assert.equal(bulk.en.data.area_id,'__keep__');assert.equal(bulk.en.data.kind,'By');
 let release;c.storageWait=new Promise(resolve=>release=resolve);run('api=async()=>({json:()=>storageWait})');
 const pending=run('AdminUI.storage()');run("openDialog('<form>UNSAVED NEW DIALOG</form>')");release({});await pending;
 assert.match(get('dialog').innerHTML,/UNSAVED NEW DIALOG/,'A late storage response must not replace a newer dialog');
 console.log('Card/history language keeps tabs, print paths, address/card types, user text, correction preview gates and actual form/confirmation payloads unchanged.');
})().catch(error=>{console.error(error);process.exitCode=1;});
