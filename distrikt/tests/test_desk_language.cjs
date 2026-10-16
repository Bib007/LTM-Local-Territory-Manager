// Exercise rendered form contracts and the real submit handler with invented data.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const listeners={},nodes=new Map(),get=id=>{
 if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',style:{},dataset:{},open:false,
  addEventListener(){},showModal(){this.open=true;},close(){this.open=false;}});
 return nodes.get(id);
};
class TestFormData{
 constructor(form){this.values=new Map(form.fields);}
 has(key){return this.values.has(key);}
 [Symbol.iterator](){return this.values[Symbol.iterator]();}
}
const context={console,Date,Intl,Number,String,Math,Map,Set,JSON,Array,Object,Promise,FormData:TestFormData,
 setTimeout(){return 0;},clearTimeout(){},calls:[],frontResizeObserver:null,DistrictMap:{dispose(){}},
 document:{addEventListener(kind,fn){(listeners[kind]??=[]).push(fn);},querySelector(){return {content:'FICTIONAL_TOKEN'};},getElementById:get},
 window:{addEventListener(){}},fetch(){throw Error('Network forbidden in language test');}};
vm.createContext(context);vm.runInContext(read('i18n.js'),context);
const source=read('app.js'),boot=source.indexOf('(async()=>{try{await refresh();');assert(boot>0);
vm.runInContext(source.slice(0,boot),context);const run=s=>vm.runInContext(s,context);
run(`state={today:'2026-10-16',cards:[
 {id:'available',number:'120<test>',name:'Kort',in_folder:true,area_id:'a'},
 {id:'stored',number:'220',name:'Forkynder',in_folder:false,area_id:'a'},
 {id:'assigned',number:'320',in_folder:false,area_id:'a'}],
 areas:[{id:'a',name:'Kort'}],publishers:[{id:'p',name:'Forkynder <fictional>'}],
 loans:[{id:'loan',card_id:'assigned',publisher_id:'p',assigned:'2026-08-01',cycle_start:'2026-09-12',returned:null}]};
 mutate=async(action,data,options)=>calls.push({action,data,options});`);
const original=run('JSON.stringify(state)'),forms={};
function html(){return get('dialog').innerHTML;}
function contract(markup){return (markup.match(/(?:id|name|data-id|data-retain|value|min|max|maxlength|required|autocomplete)=(?:"[^"]*"|'[^']*')|\brequired\b/g)||[]).join('\n');}
for(const language of ['da','en']){
 run(`I18n.set('${language}');issue('available')`);
 assert.equal(get('dialog').lang,language);assert.match(html(),/id="issueForm"/);
 assert.match(html(),/name="publisher_name"/);assert.match(html(),/120&lt;test&gt;/);
 assert.match(html(),/>120&lt;test&gt; · Kort<\/option>/);assert.match(html(),/value="Forkynder &lt;fictional&gt;"/);
 assert.match(html(),/name="date" type="date" value="2026-10-16" max="2026-10-16" required/);
 assert(!html().includes('value="assigned"'));
 assert.match(html(),language==='en'?/Assign card 120&lt;test&gt;/:/Udlever kort 120&lt;test&gt;/);
 forms[language]=[contract(html())];
 run("issue('stored')");assert.match(html(),/name="initial" type="checkbox" checked/);
 assert.match(html(),language==='en'?/Record an existing assignment/:/Registrer eksisterende udlån/);
 forms[language].push(contract(html()));
 for(const retain of [false,true]){
  run(`finish('loan',${retain})`);assert.equal(get('dialog').lang,language);
  assert.match(html(),new RegExp('data-retain="'+(retain?'yes':'no')+'"'));
  assert.match(html(),/min="2026-09-12" max="2026-10-16" required/);
  assert.match(html(),/name="note" maxlength="1000"/);
  if(!retain){assert.match(html(),/option value="yes"/);assert.match(html(),/option value="no"/);}
  else assert(!html().includes('name="complete"'));
  if(language==='en')assert.match(html(),retain?/publisher keeps the card/:/return without completion/);
  forms[language].push(contract(html()));
 }
 run("recordCompletion('available')");assert.match(html(),/id="completionForm" data-id="available"/);
 assert.match(html(),language==='en'?/Known completion · card/:/Kendt gennemgang · kort/);
 forms[language].push(contract(html()));
 run("recordCompletion('assigned')");assert.match(html(),/id="finishForm" data-id="loan" data-retain="yes"/);
 assert.equal(run('JSON.stringify(state)'),original);
}
assert.deepEqual(forms.en,forms.da,'Translated labels must keep form keys, values and date constraints');
run("I18n.set('en');openDialog('<p>Uoversat indhold</p>')");assert.equal(get('dialog').lang,'da');
assert.match(html(),/aria-label="Close"/);assert.match(run("formEnd('Uoversat handling <fiktiv>')"),/lang="da">Uoversat handling &lt;fiktiv&gt;/);
assert.match(run("formEnd('Gem indstillinger')"),/lang="en">Save settings/);
assert.match(run("formEnd('Gem gennemgang')"),/lang="en">Save completion/);

async function submit(id,fields,dataset={},valid=true){
 const button={disabled:false},form={id,fields,dataset:{...dataset},reportValidity(){return valid;},querySelector(){return button;}};
 await listeners.submit[0]({target:form,preventDefault(){}});
 assert.equal(form.dataset.saving,undefined);assert.equal(button.disabled,false);
 return context.calls.at(-1);
}
(async()=>{
 const note='Fiktiv note: Kort & <test> — æøå',payloads={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}')`);const start=context.calls.length;
  await submit('issueForm',[['card_id','available'],['publisher_name','Forkynder'],['date','2026-10-15']]);
  await submit('issueForm',[['card_id','stored'],['publisher_name','Forkynder'],['date','2026-08-01'],['initial','on']]);
  await submit('finishForm',[['date','2026-10-15'],['complete','no'],['note',note]],{id:'loan',retain:'no'});
  await submit('finishForm',[['date','2026-10-15'],['complete','yes'],['note',note]],{id:'loan',retain:'no'});
  await submit('finishForm',[['date','2026-10-15'],['note',note]],{id:'loan',retain:'yes'});
  await submit('completionForm',[['date','2026-09-20'],['note',note]],{id:'available'});
  payloads[language]=JSON.parse(JSON.stringify(context.calls.slice(start)));
 }
 assert.deepEqual(payloads.en.map(({action,data})=>({action,data})),payloads.da.map(({action,data})=>({action,data})));
 assert.deepEqual(payloads.en.map(x=>x.action),['loan.issue','loan.issue','loan.finish','loan.finish','loan.finish','completion.record']);
 assert.equal(payloads.en[0].data.initial,false);assert.equal(payloads.en[1].data.initial,true);
 assert.equal(payloads.en[2].data.complete,false);assert.equal(payloads.en[2].data.retain,false);
 assert.equal(payloads.en[3].data.complete,true);assert.equal(payloads.en[3].data.retain,false);
 assert.equal(payloads.en[4].data.complete,true);assert.equal(payloads.en[4].data.retain,true);
 assert.equal(payloads.en[5].data.note,note);assert.equal(payloads.en[0].options.message,'Assignment saved');
 const before=context.calls.length;await submit('issueForm',[],{},false);assert.equal(context.calls.length,before);
 assert.equal(run('JSON.stringify(state)'),original);
 console.log('Bilingual assignment/return/completion forms preserve field contracts, dates, notes, record keys and submit payloads.');
})().catch(error=>{console.error(error);process.exitCode=1;});
