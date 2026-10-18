// Invented records only: translated presentation must preserve stored filters and edits.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const listeners={},nodes=new Map(),tagged=[],aria=[],placeholders=[],calls=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',style:{},dataset:{},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});return nodes.get(id);};
class TestFormData{constructor(form){this.values=new Map(form.fields);}has(k){return this.values.has(k);}[Symbol.iterator](){return this.values[Symbol.iterator]();}}
const c={console,Date,Intl,Number,String,Math,Map,Set,JSON,Array,Object,Promise,FormData:TestFormData,calls,
 setTimeout(){},clearTimeout(){},frontResizeObserver:null,DistrictMap:{dispose(){}},AdminUI:{selected:new Set(),selection(){return '';}},
 window:{addEventListener(){}},document:{addEventListener(k,f){(listeners[k]??=[]).push(f);},getElementById:get,
  querySelector(){return {content:'FICTIONAL_TOKEN'};},querySelectorAll(selector){return selector==='[data-ui]'?tagged:selector==='[data-ui-aria]'?aria:selector==='[data-ui-placeholder]'?placeholders:[];}},
 fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);
const run=s=>vm.runInContext(s,c);
run(`state={today:'2026-10-16',cards:[
 {id:'folder',number:'101',name:'Forkynder <fictional>',area_id:'a',in_folder:true,kind:'By',addresses:[],last_completed:'2026-09-15'},
 {id:'box',number:'102',name:'Kort',area_id:'a',in_folder:false,kind:'Land',addresses:[]},
 {id:'assigned',number:'103',name:'Noter',area_id:'a',in_folder:false,kind:'By',addresses:[]}],
 areas:[{id:'a',name:'Kort'}],publishers:[{id:'p',name:'Forkynder <fictional>'}],
 loans:[{id:'l',card_id:'assigned',publisher_id:'p',assigned:'2026-10-01',cycle_start:'2026-10-01',returned:null}],
 notes:[{id:'n',text:'Noter <fictional> & Kort',card_id:'folder',task:true,resolved:false,date:'2026-10-15'}],
 settings:{folder_minimum:3,rural_mode:'manual',rural_minimum:1,require_revision:false}};
 mutate=async(action,data,options)=>calls.push({action,data,options});`);
const original=run('JSON.stringify(state)');
for(const lang of ['da','en']){
 run(`I18n.set('${lang}');query='';status='Kort i kassen';selected='folder'`);
 const list=run('territories()');
 assert.match(list,lang==='en'?/>Cards in the storage box<\//:/>Kort i kassen<\//);
 assert.match(list,/<option value="Kort i kassen"[^>]*selected/);
 assert.match(list,/data-status|data-card-row/);
 assert.equal(run('status'),'Kort i kassen');assert.equal(run('position(card("box"))'),'Kort i kassen');
 assert.match(run('publishersPage()'),/Forkynder &lt;fictional&gt;/);
 assert.match(run('Workspace.tasks()'),/Noter &lt;fictional&gt; &amp; Kort/);
 assert.match(run('home()'),/data-status="Kort i mappen"/);
 run("publisherProfile('p')");assert.equal(get('dialog').lang,lang);
 run("editPublisher('p')");assert.match(get('dialog').innerHTML,/name="name" value="Forkynder &lt;fictional&gt;"/);
 run("Workspace.noteForm('n')");assert.equal(get('dialog').lang,lang);
 assert.match(get('dialog').innerHTML,/Noter &lt;fictional&gt; &amp; Kort<\/textarea>/);
 assert.match(get('dialog').innerHTML,/option value="folder" selected/);
 assert.equal(run('JSON.stringify(state)'),original);
}
assert.match(run("I18n.label('{count} kort',{count:'<script> & test'})"),/&lt;script&gt; &amp; test cards/);
assert.equal(run("I18n.format('Unknown <fictional>')"),'Unknown <fictional>');
assert.equal(run("elapsedSince('2026-09-15')"),'1 måned og 1 dag siden');
assert.match(run("elapsedLabel('2026-09-15')"),/>1 month and 1 day ago<\//);
// Reuse tagged nodes when switching language, without touching their neighbours or form values.
const label={dataset:{ui:'{count} kort',uiParams:'{"count":2}'},textContent:'',lang:''};tagged.push(label);
const input={dataset:{uiAria:'Søg opgaver',uiPlaceholder:'Søg opgave, note eller kortnummer'},value:'UNSAVED <fictional>',attrs:{},setAttribute(k,v){this.attrs[k]=v;}};
aria.push(input);placeholders.push(input);
run("I18n.set('en');I18n.applyShell()");assert.equal(label.textContent,'2 cards');assert.equal(input.attrs.placeholder,'Search task, note or card number');
run("I18n.set('da');I18n.applyShell()");assert.equal(label.textContent,'2 kort');assert.equal(input.value,'UNSAVED <fictional>');assert.equal(input.attrs['aria-label'],'Søg opgaver');
tagged.push({dataset:{ui:'Kort',uiParams:'broken-json'},textContent:''});assert.doesNotThrow(()=>run('I18n.applyShell()'));
(async()=>{
 const payloads={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}')`);const start=calls.length;
  await run('Workspace.submit')({dataset:{workForm:'note',id:'n'},fields:[['card_id','folder'],['text','Noter <fictional> & Kort'],['task','on']]});
  await run('Workspace.submit')({dataset:{workForm:'note',id:''},fields:[['card_id',''],['text','UNSAVED <fictional>']]});
  const form={id:'publisherForm',dataset:{id:'p'},fields:[['name','Forkynder <fictional>']],reportValidity(){return true;},querySelector(){return {disabled:false};}};
  await listeners.submit.find(fn=>!String(fn).includes('workForm'))({target:form,preventDefault(){}});
  payloads[language]=JSON.parse(JSON.stringify(calls.slice(start)));
 }
 assert.deepEqual(payloads.en,payloads.da);
 assert.equal(payloads.en[0].action,'note.save');assert.equal(payloads.en[0].data.task,true);assert.equal(payloads.en[1].data.card_id,null);
 assert.equal(payloads.en[2].action,'publisher.save');assert.equal(payloads.en[2].data.name,'Forkynder <fictional>');
 assert.equal(run('JSON.stringify(state)'),original);
 run("I18n.set('en');Workspace.taskFilter='all'");assert.match(run('Workspace.tasks()'),/marks a task as done/);assert.match(run('Workspace.tasks()'),/data-ui-title="Markér udført"/);assert.match(run('Workspace.tasks()'),/aria-pressed="false"/);
 // Legacy non-task records are shown immediately, and completed records never inflate alerts.
 vm.runInContext(read('navigation.js'),c);
 run(`state.notes.push({id:'old',text:'Fiktiv gammel <opfølgning>',card_id:'folder',task:false,resolved:false,date:'2026-10-01'},
  {id:'done',text:'FIKTIV_DONE_TASK',card_id:'folder',task:false,resolved:true,date:'2026-10-01'},
  {id:'general',text:'Fiktiv generel opgave',card_id:null,resolved:false,date:'2026-10-01'});Workspace.taskFilter='open';`);
 let html=run('Workspace.tasks()');assert.match(html,/Fiktiv gammel &lt;opfølgning&gt;/);assert.match(html,/Fiktiv generel opgave/);assert.doesNotMatch(html,/FIKTIV_DONE_TASK|data-value="notes"|data-work="make-task"/);
 assert.match(run('Navigation.html()'),/class="navTaskCount"[^>]*>3<\/span>/);
 assert.match(run("taskBadge('folder')"),/2 open tasks/);assert.equal(run("taskBadge('box')"),'');
 run("Workspace.taskFilter='done'");assert.match(run('Workspace.tasks()'),/FIKTIV_DONE_TASK/);assert.doesNotMatch(run('Workspace.tasks()'),/Fiktiv generel opgave/);
 run("Workspace.noteForm('old')");assert.doesNotMatch(get('dialog').innerHTML,/name="task"|New task \/ note/);assert.match(get('dialog').innerHTML,/Fiktiv gammel &lt;opfølgning&gt;/);
 run(`state.archived_cards=[{id:'archive',number:'FIKTIV-ARKIV',name:'Fiktiv arkiveret'}];state.notes.push({id:'archived-task',card_id:'archive',text:'Fiktiv bevaret opgave',resolved:true});Workspace.noteForm('archived-task');`);
 assert.match(get('dialog').innerHTML,/option value="archive" selected/,'Editing an archived-card task must preserve its link');
 c.PublisherSearch={field:()=>'',attach(){}};run("issue('folder')");assert.match(get('dialog').innerHTML,/issueTaskAlert/);assert.match(get('dialog').innerHTML,/Fiktiv gammel &lt;opfølgning&gt;/);assert.doesNotMatch(get('dialog').innerHTML,/FIKTIV_DONE_TASK/);assert.match(get('dialog').innerHTML,/do not.*block assignment/);
 const beforeChange=run('JSON.stringify(state)');await listeners.change.find(fn=>String(fn).includes('issueTaskWarning'))({target:{name:'card_id',value:'box',form:{id:'issueForm'}}});assert.equal(get('issueTaskWarning').innerHTML,'');assert.equal(run('JSON.stringify(state)'),beforeChange);
console.log('Bilingual work lists preserve filter values, user text, calendar counts, drafts and note/publisher payloads; labels and attributes switch without rebuilding forms.');
})().catch(error=>{console.error(error);process.exitCode=1;});
