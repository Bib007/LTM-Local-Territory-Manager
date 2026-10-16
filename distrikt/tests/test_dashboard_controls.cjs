// Synthetic data only. Dashboard presentation and connectivity must not mutate records.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const listeners={},windowListeners={},nodes=new Map(),classes=new Set(),requests=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',outerHTML:'',textContent:'',dataset:{},style:{},open:false,addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});return nodes.get(id);};
const menu={attrs:{},focus(){this.focused=true;},setAttribute(k,v){this.attrs[k]=v;}};
let network=true,answer=null;
const context={console,Date,Intl,Number,String,Math,Map,Set,JSON,Array,Object,Promise,
 setTimeout(){return 0;},clearTimeout(){},frontResizeObserver:null,DistrictMap:{dispose(){}},
 document:{addEventListener(k,f){(listeners[k]??=[]).push(f);},getElementById:get,querySelectorAll(){return [];},
  querySelector(selector){return selector==='.mobileMenu'?menu:{content:'INVENTED_TOKEN'};},
  body:{classList:{contains(k){return classes.has(k);},toggle(k,value){value?classes.add(k):classes.delete(k);}}}},
 window:{addEventListener(k,f){windowListeners[k]=f;},setInterval(){return 0;}},
 fetch:async(url,options)=>{requests.push({url,options});if(answer)return answer;if(!network)throw Error('Synthetic offline');return {ok:true};}};
vm.createContext(context);for(const file of ['i18n.js','workspace.js'])vm.runInContext(read(file),context);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),context);
const run=s=>vm.runInContext(s,context);
run(`state={today:'2026-10-16',cards:[
 {id:'c0',number:'101',name:'Kort <fictional>',kind:'By',addresses:[{count:4}],in_folder:true},
 {id:'c1',number:'102',name:'Noter',kind:'Land',addresses:[{count:2}],in_folder:false},
 {id:'c2',number:'103',name:'Tjenesteår',kind:'By',addresses:[],in_folder:false,front_revision:true}],
 archived_cards:[{id:'old',addresses:[]}],areas:[],publishers:[{id:'p',name:'Forkynder <invented>'}],
 loans:[{id:'l',card_id:'c2',publisher_id:'p',assigned:'2026-05-01',cycle_start:'2026-05-01',returned:null}],
 completions:[{card_id:'c0',date:'2026-09-03',visits:5},{card_id:'c0',date:'2026-10-03',visits:4},{card_id:'c1',date:'2026-10-05',visits:2},{card_id:'old',date:'2026-10-06',visits:3}],
 visits:[{date:'2026-09-20'}],notes:[{text:'Private invented note',task:true,resolved:false}],settings:{saved_views:[{id:'v',name:'Gemte visninger'}]}};`);
const original=run('JSON.stringify(state)');
for(const language of ['da','en']){
 run(`I18n.set('${language}')`);const html=run('Workspace.dashboard()');
 assert.match(html,/>4<\/strong>/);assert.match(html,/>14<\/strong>/);assert.match(html,/>67%<\/strong>/);
 assert.equal((html.match(/class="attentionCard"/g)||[]).length,1);
 assert.match(html,/Forkynder &lt;invented&gt;/);assert(!html.includes('<invented>'));
 assert.equal((html.match(/data-ui="[a-z]{3} \{year\}"/g)||[]).length,24);
 assert.match(html,/aria-hidden="true"/);assert.match(html,/class="srOnly"/);
 assert.match(html,language==='en'?/Service year 2026\/2027/:/Tjenesteår 2026\/2027/);
 assert.match(html,language==='en'?/View monthly figures as a table/:/Vis månedstallene som tabel/);
 run("Workspace.searchDialog('Kort <fictional>')");assert.match(get('workspaceSearchResults').innerHTML,/Kort &lt;fictional&gt;/);
 assert.equal(get('dialog').lang,language);assert.match(run('Workspace.filters()'),/>Gemte visninger<\/option>/);
 assert.equal(run('JSON.stringify(state)'),original);
}
run('state.cards=[];state.completions=[];state.archived_cards=[];state.loans=[];state.notes=[]');
assert.match(run('Workspace.dashboard()'),/Begin|Begynd|Start with/);assert(!run('Workspace.dashboard()').includes('NaN'));
assert.match(run("Workspace.dashboardChart('2026-09-01','2027-08-31')"),/No completions recorded/);
run(`state=${original}`);
run('Workspace.boot();saved()');windowListeners.offline();assert.equal(run('SaveStatus.kind'),'saved');
get('dialog').open=false;run("Workspace.menu(true)");assert.equal(menu.attrs['aria-expanded'],'true');
let prevented=false;listeners.keydown.at(-1)({key:'Escape',preventDefault(){prevented=true;}});assert(prevented);assert.equal(menu.attrs['aria-expanded'],'false');assert(menu.focused);
const keyboard=listeners.keydown.at(-1);get('dialog').open=false;
keyboard({key:'k',ctrlKey:true,target:{closest(){return {}; }},preventDefault(){throw Error('Do not hijack a text field');}});
keyboard({key:'k',ctrlKey:true,target:{closest(){return null;}},preventDefault(){}});assert.equal(get('dialog').open,true);
(async()=>{
 network=false;await assert.rejects(run("api('/api/state')"));assert.equal(run('SaveStatus.kind'),'saved','Read failure is not an unconfirmed write');
 await assert.rejects(run("api('/api/mutate',{action:'note.save',data:{text:'invented'}})"));assert.equal(run('SaveStatus.kind'),'error');
 const writeCount=requests.filter(r=>r.url==='/api/mutate').length,draft=get('dialog').innerHTML;
 network=true;await run('Workspace.checkConnection()');assert.equal(run('Workspace.connectionState'),'connected');
 assert.equal(run('SaveStatus.kind'),'error','A responding server does not prove an earlier write was saved');
 assert.equal(requests.filter(r=>r.url==='/api/mutate').length,writeCount,'Never replay a write');
 assert.equal(get('dialog').innerHTML,draft,'Probes do not rebuild an open form');
 assert.equal(run('JSON.stringify(state)'),original);
 let release;answer=new Promise(resolve=>release=resolve);const first=run('Workspace.checkConnection()'),count=requests.length;
 await run('Workspace.checkConnection()');assert.equal(requests.length,count,'Do not overlap probes');release({ok:false});await first;answer=null;
 assert.equal(run('Workspace.connectionState'),'offline');assert.equal(run('Workspace.checkingConnection'),false);
 run("failed('<script> & invented')");assert.match(get('saveState').innerHTML,/&lt;script&gt; &amp; invented/);
 run("I18n.set('en');SaveStatus.paint()");assert.match(get('saveState').innerHTML,/Saving is not confirmed/);
 run('GeoUI={dirty:false,loaded:false};readCount=0;refresh=async()=>readCount++');
 get('dialog').open=true;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),0,'Refresh must not interrupt an open edit');
 get('dialog').open=false;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),1);
 assert.equal(run('SaveStatus.kind'),'review','A refreshed snapshot does not prove an earlier write');
 assert.equal(requests.filter(r=>r.url==='/api/mutate').length,writeCount);
 console.log('Dashboard arithmetic, archived/repeat coverage, empty states, bilingual local search, keyboard/menu access and independent save/connectivity states passed; probes preserve drafts and never replay writes.');
})().catch(error=>{console.error(error);process.exitCode=1;});
