// Real error/API/IB/backup rendering with invented diagnostics. No files or remote service.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8'),nodes=new Map();
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,showModal(){this.open=true;},addEventListener(){}});return nodes.get(id);};
let payload={};const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,setTimeout(){},clearTimeout(){},frontResizeObserver:null,DistrictMap:{dispose(){}},window:{addEventListener(){}},document:{getElementById:get,querySelector:()=>({content:'FICTIONAL_TOKEN'}),querySelectorAll:s=>s==='[data-ui]'?[...nodes.values()].filter(n=>n.dataset.ui):[],addEventListener(){}},fetch:async()=>({ok:false,status:400,json:async()=>payload})};
vm.createContext(c);for(const n of ['i18n.js','setup-ui.js','transfer-ui.js'])vm.runInContext(read(n),c);const src=read('app.js');vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run("state={revision:'r1',cards:[],areas:[],settings:{}};Workspace={connectionChanged(){}};SetupUI.ibDate='2026-10-17';saved()");
const capture=async p=>{try{await p;assert.fail('Expected rejection');}catch(e){return e;}};
(async()=>{
 const name='Historik <img src=x> {low} & "fictional"';payload={error:'Området '+name+' findes allerede. Vælg det fra listen.',ui_error:{key:'Området {name} findes allerede. Vælg det fra listen.',params:{name}}};
 const original=JSON.stringify(payload);const error=await capture(run("api('/api/mutate',{action:'setup.preview',data:{}})"));c.error=error;run("I18n.set('en');I18n.errorContent(el('formError'),error)");assert.equal(get('formError').textContent,'Area '+name+' already exists. Choose it from the list.');assert.equal(get('formError').lang,'en');assert.equal(JSON.parse(get('formError').dataset.uiParams).name,name);assert.equal(error.writing,false);assert.equal(run('WriteGuard.uncertain'),false);assert.equal(JSON.stringify(payload),original);
 const html=run('I18n.errorHTML(error)');assert.match(html,/&lt;img src=x&gt;/);assert.doesNotMatch(html,/<img/);assert.match(html,/Historik/);assert.doesNotMatch(html,/Area History/);
 run("I18n.set('da');I18n.applyShell()");assert.equal(get('formError').textContent,payload.error);run("I18n.set('en');I18n.applyShell()");assert.equal(get('formError').textContent,'Area '+name+' already exists. Choose it from the list.');
 for(const [key,params,expected] of [
  ['{field} skal være en gyldig dato.',{field:'Dato'},'Date must be a valid date.'],
  ['{field} må ikke ligge i fremtiden.',{field:'Dato'},'Date must not be in the future.'],
  ['{label} skal være mellem {low} og {high}.',{label:'Besøg pr. kort',low:1,high:1000},'Visits per card must be between 1 and 1000.'],
  ['{label} skal være et helt tal.',{label:'Områdets startnummer'},'Area starting number must be a whole number.'],
  ['{label} skal være et helt tal.',{label:'Historik'},'Historik must be a whole number.'],
  ['Ukendt databaseversion: {file}',{file:'notes'},'Unknown database version: notes']
 ]){c.body={error:'Original fictional diagnostic',ui_error:{key,params}};run('currentError=RequestError.fromResponse(body)');assert.equal(run('I18n.errorText(currentError)'),expected);assert.equal(JSON.stringify(c.body.ui_error.params),JSON.stringify(params));}
 // Unknown/incomplete/non-scalar metadata never hides the original diagnostic or becomes HTML.
 for(const metadata of [{key:'UNKNOWN TEMPLATE',params:{}},{key:'{field} skal være en gyldig dato.',params:{}},{key:'{field} skal være en gyldig dato.',params:{field:['Dato']}},{key:'{field} skal være en gyldig dato.',params:{field:{value:'Dato'}}},{key:'{field} skal være en gyldig dato.',params:null}]){
  c.body={error:'Original <fictional> {field}',ui_error:metadata};run('currentError=RequestError.fromResponse(body)');assert.equal(run('I18n.errorText(currentError)'),c.body.error);assert.match(run('I18n.errorHTML(currentError)'),/Original &lt;fictional&gt;/);
 }
 payload={error:'Kortnummeret findes allerede (evt. i 48-timers gendannelse).'};c.error=await capture(run("api('/api/mutate',{action:'card.save',data:{number:'fictional'}})"));run('failed(error)');assert.match(get('saveState').innerHTML,/The change was rejected/);assert.equal(run('WriteGuard.uncertain'),false);assert.equal(run('state.revision'),'r1');
 c.ib={errors:1,new:0,existing:0,rows:[{line:2,status:'error',error:'Dato skal være en gyldig dato.',ui_error:{key:'{field} skal være en gyldig dato.',params:{field:'Dato'}}}]};run('SetupUI.ib=ib');assert.match(run('SetupUI.ibPage()'),/Date must be a valid date/);assert.match(run('SetupUI.ibPage()'),/disabled/);
 payload={error:'Ugyldigt databaseformat: notes',ui_error:{key:'Ugyldigt databaseformat: {file}',params:{file:'notes'}}};const backupError=await capture(run('TransferUI.preview({size:1})'));c.error=backupError;assert.equal(run('I18n.errorText(error)'),'Invalid database format: notes');assert.equal(backupError.writing,false);
 console.log('Domain errors: bilingual static/parameterized diagnostics, unchanged names/bounds, language changes, escaping/fallback, rejected writes, IB rows and backup preview errors passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
