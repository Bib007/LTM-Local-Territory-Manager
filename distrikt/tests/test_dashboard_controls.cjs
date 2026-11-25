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
 assert.match(html,/class="dashboardCoverageVisits"[\s\S]*?<strong>6<\/strong>/,'Two completed current territories contribute six visits only once');assert.match(html,/>67%<\/strong>/);
 assert.equal((html.match(/class="attentionCard"/g)||[]).length,0);assert.match(html,/data-work="followups"/);assert.doesNotMatch(html,/revisionSummary/);
 assert(!html.includes('<invented>'));
 assert.equal((html.match(/data-ui="[a-z]{3} \{year\}"/g)||[]).length,24);
 assert.match(html,/aria-hidden="true"/);assert.match(html,/class="srOnly"/);
 assert.doesNotMatch(html,/dashboardLead|dashboardVisits|data-ui="Gennemgange i tjenesteåret"/,'The dashboard no longer repeats titles or completion tiles');
 assert.doesNotMatch(html,/dashboardPeriod|Gennemgange og anslåede besøg:|Completions and estimated visits:/);
 assert.match(html,language==='en'?/View monthly figures as a table/:/Vis månedstallene som tabel/);
 assert.match(html,language==='en'?/Not enough history yet/:/Ikke nok historik endnu/,'Open loans and manually added completions cannot establish issue-to-return duration');
 assert.match(html,/data-dashboard-layout="compact"/);
 assert.match(html,/class="dashboardPrimary"/);
 assert.match(html,/class="dashboardAverageValue">/);
 assert.match(html,/role="progressbar"[^>]*aria-valuemin="0"[^>]*aria-valuemax="100"[^>]*aria-valuenow="67"/);
 assert.match(html,/style="width:67%"/);
 assert.match(html,language==='en'?/This year’s progress/:/Årets fremdrift/);
 assert.match(html,language==='en'?/1 card remaining/:/1 kort tilbage/);
 assert.doesNotMatch(html,/dashboardHero|dashboardRing|not a forecast|ikke en prognose|recorded intervals|kendte intervaller|Converted using 30 days per month|Omregnet med 30 dage pr. måned/);
 assert.ok(html.indexOf('dashboardPrimary')<html.indexOf('dashboardQuickFacts'),'Main metrics come first');
 assert.ok(html.indexOf('dashboardQuickFacts')<html.indexOf('dashboardLower'),'Actions precede the deep-dive chart');
 assert.ok(html.indexOf('dashboardLower')<html.indexOf('dashboardBelow'),'Background tasks do not obscure first-screen data');
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
run("state.completions.push({card_id:'c0',date:'2026-10-07',visits:0,visits_unknown:true})");
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').visits"),17,'Current card count applies even to historically unknown completions');
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').events.length"),5);
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').unknownVisits"),0);
assert.equal(run("Workspace.coverageVisitEstimate(Workspace.stats('2026-09-01','2026-10-16').events,state.cards).value"),6,'Repeated completions do not inflate the coverage visit total');
assert.doesNotMatch(run('Workspace.dashboard()'),/Territories with unknown visit counts are excluded/);
run("state.cards[0].addresses[0].count_unknown=true");
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').visits"),14,'Retain known historic snapshots when current card count is unknown');
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').unknownVisits"),1);
assert.equal(run("Workspace.coverageVisitEstimate(Workspace.stats('2026-09-01','2026-10-16').events,state.cards).unknown"),1);
assert.match(run('Workspace.dashboard()'),/Territories with unknown visit counts are excluded/);
run(`state=${original}`);
run("state.cards[0].addresses[0].count=35");
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').visits"),75,'Each of two completions of a 35-visit card contributes 35');
run("state.ib=[{card_id:'c0'},{card_id:'c0'},{card_id:'not-this-card'}]");
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').visits"),71,'Historical report still counts each completion');
assert.equal(run("Workspace.coverageVisitEstimate(Workspace.stats('2026-09-01','2026-10-16').events,state.cards).value"),35,'Coverage counts 35 minus 2 IB once, plus 2 for the other completed card');
run("state.ib=[]");
run("state.archived_cards[0].addresses=[{count:35}]");
assert.equal(run("Workspace.stats('2026-09-01','2026-10-16').visits"),107,'Archived territory totals count where known');
assert.equal(run("Workspace.coverageVisitEstimate(Workspace.stats('2026-09-01','2026-10-16').events,state.cards).value"),37,'Archived cards never increase current-year coverage visits');
run(`state=${original}`);
run("state.loans.push({card_id:'old',returned:null})");
assert.match(run('Workspace.dashboard()'),/data-ui="Udleveret nu"[\s\S]*?<\/span><\/span><strong>1<\/strong>/,'Archived territory loans do not inflate current placement');
run("state.settings.folder_enabled=false");
assert.doesNotMatch(run('Workspace.dashboard()'),/data-status="Kort i mappen"/);
assert.match(run('Workspace.dashboard()'),/data-status="Kort i kassen"/);
run(`state=${original}`);
run('state.cards=[];state.completions=[];state.archived_cards=[];state.loans=[];state.notes=[]');
assert.match(run('Workspace.dashboard()'),/Begin|Begynd|Start with/);assert(!run('Workspace.dashboard()').includes('NaN'));
assert.match(run('Workspace.dashboard()'),/role="progressbar"[^>]*aria-valuenow="0"/);
assert.match(run("Workspace.dashboardChart('2026-09-01','2027-08-31')"),/No completions recorded/);
run(`state=${original}`);
// The two prominent figures measure different facts: finished loan duration
// versus the age of the next currently issuable card.
run("I18n.set('da')");
run(`state.loans=[
 {id:'done-10',card_id:'c0',assigned:'2026-10-01',returned:'2026-10-11'},
 {id:'done-20',card_id:'c1',assigned:'2026-09-01',returned:'2026-09-21'},
 {id:'not-complete',card_id:'c2',assigned:'2026-09-01',returned:'2026-09-02'},
 {id:'retained-only',card_id:'c2',assigned:'2026-08-01',returned:'2026-10-01'},
 {id:'still-out',card_id:'c2',assigned:'2026-10-01',returned:null}
];
state.completions=[
 {loan_id:'done-10',card_id:'c0',date:'2026-10-11'},
 {loan_id:'done-20',card_id:'c1',date:'2026-09-21'},
 {loan_id:'retained-only',card_id:'c2',date:'2026-08-10'},
 {loan_id:'still-out',card_id:'c2',date:'2026-10-15'},
 {card_id:'c0',date:'2026-10-12'}
];`);
assert.equal(run('Workspace.completedReturnAverage()'),15,'Only matching completed returns contribute their full issue-to-return duration');
run(`state.loans.push(
 {id:'old-completed',card_id:'c0',assigned:'2024-01-01',returned:'2025-10-15'},
 {id:'boundary-completed',card_id:'c0',assigned:'2025-09-26',returned:'2025-10-16'},
 {id:'future-completed',card_id:'c0',assigned:'2026-10-01',returned:'2026-10-17'}
);state.completions.push(
 {loan_id:'old-completed',card_id:'c0',date:'2025-10-15'},
 {loan_id:'boundary-completed',card_id:'c0',date:'2025-10-16'},
 {loan_id:'future-completed',card_id:'c0',date:'2026-10-17'}
);`);
assert.equal(run('Workspace.completedReturnAverage()'),50/3,'Include cutoff date but exclude older and future completed returns');
assert.equal(run("Workspace.rollingCompletionStart('2028-02-29')"),'2027-02-28');
assert.equal(run("Workspace.serviceYearTarget('2026-09-01')"),0);
assert.equal(run("Workspace.serviceYearTarget('2027-03-01')"),50);
assert.equal(run("Workspace.serviceYearTarget('2027-08-31')"),100);
assert.equal(run("Workspace.serviceYearTarget('2027-09-01')"),0);
assert.equal(run("Workspace.serviceYearTarget('2028-03-01')"),50);
assert.match(run("Workspace.dashboardCoverage(32,100,null,false,'2026-11-24')"),/9 procentpoint foran årets mål/);
assert.match(run("Workspace.dashboardCoverage(10,100,null,false,'2026-11-24')"),/13 procentpoint bag årets mål/);
assert.match(run("Workspace.dashboardCoverage(23,100,null,false,'2026-11-24')"),/På niveau med årets mål/);
assert.doesNotMatch(run("Workspace.dashboardCoverage(0,0,null,false,'2026-11-24')"),/procentpoint bag årets mål/);
run("state.loans=state.loans.filter(l=>!['old-completed','boundary-completed','future-completed'].includes(l.id));state.completions=state.completions.filter(e=>!['old-completed','boundary-completed','future-completed'].includes(e.loan_id))");

assert.match(run('Workspace.dashboard()'),/Gennemsnitlig gennemgangstid/);
assert.match(run('Workspace.dashboard()'),/Fra udlevering til aflevering/);
assert.match(run('Workspace.dashboard()'),/Ældste kort i gennemgangskøen/);
assert.match(run('Workspace.dashboard()'),/Tid siden sidste gennemgang af det ældste ledige kort med kendt dato/);
run("state.completions=state.completions.filter(e=>e.loan_id!=='done-20'&&e.loan_id!=='done-10')");
assert.equal(run('Workspace.completedReturnAverage()'),null,'No completed returns should never turn into a misleading zero duration');
run(`state.cards=[
 {id:'q1',number:'1',in_folder:true,last_completed:'2026-09-20',addresses:[{count:5}]},
 {id:'q2',number:'2',in_folder:true,last_completed:'2026-04-10',addresses:[{count:7}]},
 {id:'q3',number:'3',in_folder:false,last_completed:'2025-01-01',addresses:[{count:5}]},
 {id:'q4',number:'4',in_folder:true,last_completed:'2025-01-01',addresses:[{count:5}]},
 {id:'q5',number:'5',in_folder:true,addresses:[{count:2}]}
];
state.settings.folder_enabled=true;
state.loans=[{id:'active',card_id:'q4',assigned:'2026-10-01',returned:null}];
state.completions=[];`);
assert.equal(run('Workspace.oldestQueueCard().card.id'),'q3','Known oldest available date includes the box even with folder mode enabled');
assert.equal(run('Workspace.oldestQueueCard().unknown'),1,'An undated card is reported separately');
assert.match(run('Workspace.dashboard()'),/1 ledigt kort uden kendt gennemgangsdato/);
assert.doesNotMatch(run('Workspace.dashboard()'),/dashboardQueueValue">[^<]*Ingen gennemgang registreret/);
run("state.cards[4].last_completed='2026-07-01'");
assert.equal(run('Workspace.oldestQueueCard().unknown'),0);
run("state.settings.folder_enabled=false");
assert.equal(run('Workspace.oldestQueueCard().card.id'),'q3','Folder setting cannot alter district-wide queue age');
run("state.loans.push({id:'active3',card_id:'q3',returned:null})");
assert.equal(run('Workspace.oldestQueueCard().card.id'),'q2','Active cards do not count toward the available queue');
run("state.cards[1].planning_date='2020-01-01'");
assert.equal(run('Workspace.oldestQueueCard().card.last_completed'),'2026-04-10','Planning dates must not masquerade as actual completions');
run("state.cards.forEach(c=>delete c.last_completed)");
assert.equal(run('Workspace.oldestQueueCard().card'),null);
assert.equal(run('Workspace.oldestQueueCard().unknown'),3);
run("state.cards=[]");
assert.equal(run('Workspace.oldestQueueCard().unknown'),0);
assert.equal(run('Workspace.oldestQueueCard().card'),null);
run(`state=${original}`);
// Snapshot actual browser-initialized input values and ignore button defaults.
run(`state.settings.folder_minimum_configured=true;
var settingsInputs=[{name:'congregation',type:'text',value:'Example',defaultValue:''},{name:'mode',type:'select-one',value:'auto'},{type:'submit',value:'Save',defaultValue:''}];
var settingsFormFixture={id:'settingsForm',dataset:{},querySelectorAll:()=>settingsInputs};
var settingsRootFixture={querySelectorAll:()=>[settingsFormFixture]};
SettingsViewDrafts.capture(settingsRootFixture);`);
assert.equal(run('SettingsViewDrafts.dirty(settingsRootFixture)'),false,'An untouched settings view must allow the statistics tab');
run("settingsInputs[2].value='Gem'");
assert.equal(run('SettingsViewDrafts.dirty(settingsRootFixture)'),false,'Button labels cannot mark a settings form dirty');
run("settingsInputs[0].value='Changed'");
assert.equal(run('SettingsViewDrafts.dirty(settingsRootFixture)'),true,'An actual unsaved edit remains protected');
run("settingsInputs[0].value='Example'");
assert.equal(run('SettingsViewDrafts.dirty(settingsRootFixture)'),false,'Reverting an edit allows the tab switch');
run("settingsInputs[1].value='manual';settingsFormFixture={id:'settingsForm',dataset:{},querySelectorAll:()=>settingsInputs};SettingsViewDrafts.capture(settingsRootFixture)");
assert.equal(run('SettingsViewDrafts.dirty(settingsRootFixture)'),false,'A newly rendered form after saving gets a fresh baseline');
run(`state=${original}`);
// The next return selection is derived from the actual visible list order,
// applied only after the returned loan appears in a confirmed snapshot.
run(`page='Udlevering';deskTab='Aflever';query='';area='';selected='c1';
state.loans=[{id:'r0',card_id:'c0'},{id:'r1',card_id:'c1'},{id:'r2',card_id:'c2'}];
var oldQuerySelectorAll=document.querySelectorAll;
document.querySelectorAll=()=>['c0','c1','c2'].map(id=>({dataset:{cardRow:id}}));
var returnPlan=ReturnSelection.capture('r1');`);
run('ReturnSelection.apply(returnPlan)');
assert.equal(run('selected'),'c1','Unconfirmed returns cannot move selection');
run("state.loans[1].returned='2026-10-16';ReturnSelection.apply(returnPlan)");
assert.equal(run('selected'),'c2','Follow the next row, not the first row');
run("deskTab='Forkyndere';returnPlan=ReturnSelection.capture('r2');state.loans[2].returned='2026-10-16';ReturnSelection.apply(returnPlan)");
assert.equal(run('selected'),'c0','Wrap to remaining earlier rows in publisher order');
run("returnPlan=ReturnSelection.capture('r0');state.loans[0].returned='2026-10-16';ReturnSelection.apply(returnPlan)");
assert.equal(run('selected'),'','No active row remains');
run(`state.loans.forEach(l=>delete l.returned);selected='c0';returnPlan=ReturnSelection.capture('r0');selected='c2';state.loans[0].returned='2026-10-16';ReturnSelection.apply(returnPlan);`);
assert.equal(run('selected'),'c2','Do not replace a newer manual selection');
run(`selected='c1';returnPlan=ReturnSelection.capture('r1');query='changed';state.loans[1].returned='2026-10-16';ReturnSelection.apply(returnPlan);`);
assert.equal(run('selected'),'c1','Do not move selection after the filter changes');
run(`document.querySelectorAll=oldQuerySelectorAll;page='Forside';deskTab='Udlever';query='';area='';selected='';state=${original}`);
run('Workspace.boot();saved()');windowListeners.offline();assert.equal(run('SaveStatus.kind'),'saved');assert.equal(get('saveState').dataset.saveKind,'offline');
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
 assert.equal(run('Workspace.connectionState'),'offline');assert.equal(run('Workspace.checkingConnection'),false);assert.equal(run('Workspace.connectionDelay'),4000);
 // Exercise rendering directly; a later failure must not replace the uncertain-write guard.
 run("SaveStatus.set('error','Gemning er ikke bekræftet','<script> & invented')");assert.match(get('saveState').innerHTML,/&lt;script&gt; &amp; invented/);
 run("I18n.set('en');SaveStatus.paint()");assert.match(get('saveState').innerHTML,/Saving is not confirmed/);
 run('GeoUI={dirty:false,loaded:false};readCount=0;refresh=async()=>readCount++');
 get('dialog').open=true;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),0,'Refresh must not interrupt an open edit');
 get('dialog').open=false;await run("Workspace.handle('refresh',{})");assert.equal(run('readCount'),1);
 assert.equal(run('SaveStatus.kind'),'review','A refreshed snapshot does not prove an earlier write');
 assert.equal(requests.filter(r=>r.url==='/api/mutate').length,writeCount);
 // The usage statistics are a dedicated settings tab, not a panel repeated on all settings screens.
 run("state.profile=null;ProfilesUI={has:()=>true,settings:()=>'',settingsAllowed:()=>true};Navigation={settingsSection:'usage'};UsageStatsUI={html:()=>'<section id=\\\"settings-usage\\\">Fictional activity</section>'};");
 const usage=run('settingsPage()');
 assert.match(run('Workspace.settingsNav()'),/data-work="settings-tab" data-value="usage"[^>]*aria-current="page"/);
 assert.match(usage,/Fictional activity/);
 assert.doesNotMatch(run('Workspace.settingsNav()'),/class="settingsAdvanced"/);
 assert.doesNotMatch(usage,/settings-general|settings-data|settingsForm/);
 assert(!source.includes('?UsageStatsUI.html():""'),'Usage statistics must not be embedded in the general settings grid');
 // Returns offer the same selected card details as the publisher view, plus
 // explicit marking. No group action silently completes a loan.
 run(`state={today:'2026-10-16',cards:[{id:'aa',number:'01',name:'Fictional street'},{id:'bb',number:'02',name:'Fictional lane'}],loans:[{id:'one',card_id:'aa',publisher_id:'p',assigned:'2026-10-01',returned:null},{id:'two',card_id:'bb',publisher_id:'p',assigned:'2026-10-02',returned:null}],publishers:[{id:'p',name:'Fictional publisher'}],areas:[],settings:{folder_enabled:true}};deskReturnSelected.clear();query='';selected='';details=c=>c?'<aside data-selected="'+c.id+'"></aside>':'';`);
 const returns=run('deskReturns()');
 assert.match(returns,/class="cardRow deskReturnRow selected" data-card-row="aa"/);
 assert.match(returns,/data-selected="aa"/,'The selected loan renders the sidebar card details');
 assert.match(returns,/data-return-mark="one"/);
 assert.match(returns,/data-action="desk-return-mark-visible"/);
 assert.match(returns,/data-action="desk-return-next" disabled/);
 run("deskReturnSelected.add('one')");
 assert.match(run('deskReturns()'),/data-return-mark="one" checked/);
 assert.doesNotMatch(run('deskReturns()'),/data-action="desk-return-next" disabled/);
 run("query='Fictional lane'");
 assert.match(run('deskReturns()'),/data-action="desk-return-next" disabled/,'Hidden marked loans are not returned by mistake');
 run("state.loans[0].returned='2026-10-15';query=''");
 assert.equal(run('deskReturns()').includes('data-return-mark="one"'),false);
 assert.equal(run('deskReturnSelected.size'),0,'A returned loan cannot remain marked');
 console.log('Dashboard arithmetic, archived/repeat coverage, empty states, bilingual local search, keyboard/menu access and independent save/connectivity states passed; probes preserve drafts and never replay writes.');
})().catch(error=>{console.error(error);process.exitCode=1;});
