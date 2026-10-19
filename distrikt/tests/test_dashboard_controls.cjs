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
run("state.settings.last_backup='2026-10-01T23:59:59Z';state.today='2026-10-15'");
assert.match(run('Workspace.backupReminder()'),/backupReminder/,'Exactly 14 calendar days is due');
run("state.today='2026-10-14'");assert.equal(run('Workspace.backupReminder()'),'');
run("state.today='2026-10-15';state.backup_last_day='2026-10-02'");assert.equal(run('Workspace.backupReminder()'),'','Use the server calendar day, not the UTC timestamp date');
run("state.today='2026-10-16'");assert.match(run('Workspace.backupReminder()'),/backupReminder/);run('delete state.backup_last_day');
run("state.today='2026-10-15';state.settings.backup_snoozed_until='2026-10-16'");assert.equal(run('Workspace.backupReminder()'),'');
run("state.today='2026-10-16'");assert.match(run('Workspace.backupReminder()'),/backup-snooze/,'Visible again tomorrow, not after 24 hours');
run("state.settings.last_backup='invalid';state.settings.backup_snoozed_until='';I18n.set('en')");assert.match(run('Workspace.backupReminder()'),/No backup transfer/);
run("state.settings.backup_history=[{id:'fictional',at:'2026-10-01T00:00:00Z',status:'file_saved'},{id:'fictional2',at:'2026-10-02T00:00:00Z',status:'created'}]");
assert.match(run('Workspace.backupHistory()'),/File write confirmed by the file picker/);assert.match(run('Workspace.backupHistory()'),/transfer not confirmed/);
run("state.notes=[{id:'due',text:'Fiktiv <ugentlig>',recurrence:{frequency:'weekly',weekday:4,next_due:'2026-10-16'}},{id:'future',text:'FIKTIV_FUTURE',recurrence:{frequency:'weekly',weekday:4,next_due:'2026-10-23'}}]");
assert.match(run('Workspace.recurringTasks()'),/Weekly tasks ready for action/);assert.match(run('Workspace.recurringTasks()'),/Fiktiv &lt;ugentlig&gt;/);assert.doesNotMatch(run('Workspace.recurringTasks()'),/FIKTIV_FUTURE/);
assert.match(run('Workspace.recurringTasks()'),/data-due="2026-10-16"/);assert.match(run('Workspace.taskButton(state.notes[1])'),/disabled/);
run(`state=${original};I18n.set('da')`);
for(const language of ['da','en']){
 run(`I18n.set('${language}')`);const html=run('Workspace.dashboard()');
 assert.match(html,/>4<\/strong>/);assert.match(html,/>14<\/strong>/);assert.match(html,/>67%<\/strong>/);
 assert.equal((html.match(/class="attentionCard"/g)||[]).length,1);
 assert.match(html,/Forkynder &lt;invented&gt;/);assert(!html.includes('<invented>'));
 assert.equal((html.match(/data-ui="[a-z]{3} \{year\}"/g)||[]).length,24);
 assert.match(html,/aria-hidden="true"/);assert.match(html,/class="srOnly"/);
 assert.match(html,language==='en'?/Service year 2026\/2027/:/Tjenesteår 2026\/2027/);
 assert.doesNotMatch(html,/dashboardPeriod|Gennemgange og anslåede besøg:|Completions and estimated visits:/);
 assert.match(html,language==='en'?/View monthly figures as a table/:/Vis månedstallene som tabel/);
 assert.match(html,language==='en'?/1 month and 0 days/:/1 måned og 0 dage/);
 assert.match(html,language==='en'?/Converted using 30 days per month/:/Omregnet med 30 dage pr. måned/);
 run("Workspace.searchDialog('Kort <fictional>')");assert.match(get('workspaceSearchResults').innerHTML,/Kort &lt;fictional&gt;/);
 assert.equal(get('dialog').lang,language);assert.match(run('Workspace.filters()'),/>Gemte visninger<\/option>/);
 assert.equal(run('JSON.stringify(state)'),original);
}
for(const language of ['da','en']){
 run(`I18n.set('${language}')`);
 for(const [days,months,remainder] of [[0,0,0],[1,0,1],[29,0,29],[30,1,0],[31,1,1],[59.5,2,0],[60,2,0],[365,12,5]]){
  const label=run(`Workspace.intervalLabel(${days})`).replace(/<[^>]*>/g,'');
  assert.equal(label,language==='en'?`${months} ${months===1?'month':'months'} and ${remainder} ${remainder===1?'day':'days'}`:`${months} ${months===1?'måned':'måneder'} og ${remainder} ${remainder===1?'dag':'dage'}`);
 }
 assert.doesNotMatch(run('Workspace.intervalLabel(NaN)'),/NaN/);
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
 // Exercise rendering directly; a later failure must not replace the uncertain-write guard.
 run("SaveStatus.set('error','Gemning er ikke bekræftet','<script> & invented')");assert.match(get('saveState').innerHTML,/&lt;script&gt; &amp; invented/);
 run("I18n.set('en');SaveStatus.paint()");assert.match(get('saveState').innerHTML,/Saving is not confirmed/);
 run('GeoUI={dirty:false,loaded:false};readCount=0;refresh=async()=>readCount++');
 get('dialog').open=true;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),0,'Refresh must not interrupt an open edit');
 get('dialog').open=false;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),1);
 assert.equal(run('SaveStatus.kind'),'review','A refreshed snapshot does not prove an earlier write');
 assert.equal(requests.filter(r=>r.url==='/api/mutate').length,writeCount);
 console.log('Dashboard arithmetic, archived/repeat coverage, empty states, bilingual local search, keyboard/menu access and independent save/connectivity states passed; probes preserve drafts and never replay writes.');
})().catch(error=>{console.error(error);process.exitCode=1;});
