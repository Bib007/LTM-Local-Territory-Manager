// Synthetic report periods, current/archived coverage and original print contracts.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),nodes=new Map(),listeners={},writes=[];
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',dataset:{},style:{},open:false,addEventListener(){},showModal(){this.open=true;}});return nodes.get(id);};
class Fields{constructor(form){this.values=new Map(form.fields);}has(k){return this.values.has(k);}[Symbol.iterator](){return this.values[Symbol.iterator]();}}
const c={console,Date,Intl,Number,String,Math,Map,Set,Array,Object,JSON,Promise,FormData:Fields,writes,location:{origin:'http://127.0.0.1:9999'},
 setTimeout(){},clearTimeout(){},frontResizeObserver:null,DistrictMap:{dispose(){}},window:{addEventListener(){}},
 document:{getElementById:get,querySelector(){return {content:'INVENTED_TOKEN'};},addEventListener(k,fn){(listeners[k]??=[]).push(fn);}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','report-map.js','s13-template.js','report-print.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);
const run=s=>vm.runInContext(s,c);
run(`GeoUI={data:{main_boundary:{points:[]}}};state={today:'2026-10-16',settings:{congregation:'Tjenesteår <invented> & Kort'},
 cards:[{id:'c1',number:'101',name:'Fiktiv',area_id:'a',addresses:[{count:6}],geo_polygon:[]},{id:'c2',number:'102',area_id:'',addresses:[{count:4}],geo_polygon:[],temporary:true}],
 archived_cards:[{id:'archived',number:'99',addresses:[{count:9}],archived:true}],areas:[{id:'a',name:'Kort <invented>'}],publishers:[{id:'p',name:'Forkynder <invented>'}],
 loans:[{id:'l',card_id:'c1',publisher_id:'p',assigned:'2026-09-01',cycle_start:'2026-09-01',returned:null}],
 completions:[{id:'e1',card_id:'c1',date:'2026-09-01',visits:5},{id:'e2',card_id:'c1',date:'2026-09-15',visits:6},{id:'e3',card_id:'archived',date:'2026-10-01',visits:9},{id:'e4',card_id:'c2',date:'2025-10-15',visits:4},{id:'e5',card_id:'c2',date:'2025-10-16',visits:4}],
 visits:[{id:'v',date:'2026-09-10',note:'KTM-besøg <invented> & Kort'},{id:'v-old',date:'2025-09-01',note:'OLD'}],
 ib:[{card_id:'c1',road:'DO_NOT_INCLUDE_ROAD',number:'PRIVATE_NO'}]};year=2027;
 mutate=async(action,data,options)=>writes.push({action,data,options});`);
const original=run('JSON.stringify(state)'),print={},contracts={},submit=listeners.submit.find(fn=>String(fn).includes("case 'visitForm'"));
const counts=markup=>Array.from(markup.matchAll(/<td>(\d+)<\/td>/g),m=>Number(m[1]));
const formContract=markup=>(markup.match(/(?:name|value|type|max|maxlength|data-action|data-id|data-value)="[^"]*"/g)||[]).join('\n');
(async()=>{
 const submitted={};
 for(const language of ['da','en']){
  run(`I18n.set('${language}');Workspace.reportPeriod='service'`);print[language]=run("reportPrintDocument({service:'<div>FIXED_SERVICE_MAP</div>',rolling:'<div>FIXED_ROLLING_MAP</div>'})");
  assert.equal(run('Workspace.reportPeriod'),'service');assert.match(print[language],/<html lang="da">/);assert.match(print[language],/margin:15mm/);assert.match(print[language],/s13-background.jpg/);assert.match(print[language],/Hus til hus/);assert.doesNotMatch(print[language],/data-ui/);
  const summary=run("Workspace.reportSummary('service',true,true)");assert.match(summary,/Tjenesteår &lt;invented&gt; &amp; Kort/);assert.match(summary,/<strong>3<\/strong>/);assert.match(summary,/<strong>20<\/strong>/);assert.match(summary,/<strong>50%<\/strong>/);
  assert.match(summary,language==='en'?/>Coverage of current cards<\//:/>Dækning af aktuelle kort<\//);
  const service=counts(run("Workspace.reportChart('2026-09-01','2027-08-31')"));assert.equal(service.length,12);assert.equal(service.reduce((a,b)=>a+b,0),3);assert.equal(service[0],2);assert.equal(service[1],1);
  const current=counts(run('Workspace.reportChart(...Workspace.periodBounds("service"))'));assert.equal(current.length,2,'The current service-year report stops at today');assert.equal(current.reduce((a,b)=>a+b,0),3);
  const rolling=run("Workspace.periodBounds('rolling')");assert.equal(rolling[0],'2025-10-16');assert.equal(rolling[1],'2026-10-16');const monthly=counts(run('Workspace.reportChart(...Workspace.periodBounds("rolling"))'));assert.equal(monthly.length,13);assert.equal(monthly.reduce((a,b)=>a+b,0),4);
  run("reportTab='Rullende'");const screen=run('Workspace.reports()');assert.doesNotMatch(screen,/s13-background.jpg/);assert.match(screen,/<strong>24<\/strong>/);assert.match(screen,/<strong>100%<\/strong>/);assert.doesNotMatch(screen,/>The original S-13 is included as an appendix\.</);
  run("reportTab='Besøg'");const visits=run('Workspace.reports()');assert.match(visits,/KTM-besøg &lt;invented&gt; &amp; Kort/);assert.match(visits,/data-id="v"/);contracts[language]=[formContract(visits)];
  run("editVisit('v')");assert.equal(get('dialog').lang,language);assert.match(get('dialog').innerHTML,/value="KTM-besøg &lt;invented&gt; &amp; Kort"/);contracts[language].push(formContract(get('dialog').innerHTML));
  const fields=[['date','2026-09-11'],['note','KTM-besøg <invented> & Kort']];await submit({target:{id:'visitForm',dataset:{id:'v'},fields,reportValidity(){return true;},querySelector(){return {disabled:false};}},preventDefault(){}});submitted[language]=JSON.parse(JSON.stringify(writes.at(-1)));
  const details=run('reportDetails(true)');assert.doesNotMatch(details,/DO_NOT_INCLUDE_ROAD|PRIVATE_NO/);assert.match(details,/Kort &lt;invented&gt;/);assert.match(details,/class="tablewrap"/);
  assert.equal(run('JSON.stringify(state)'),original);
 }
 assert.equal(print.en,print.da,'Language switching must leave the complete original Danish print document unchanged');assert.deepEqual(contracts.en,contracts.da);assert.deepEqual(submitted.en.data,submitted.da.data);assert.equal(submitted.en.action,'visit.save');
 run("state.today='2024-02-29'");assert.equal(run("Workspace.periodBounds('rolling')[0]"),'2023-02-28');assert.equal(counts(run("Workspace.reportChart('2023-02-28','2024-02-29')")).length,13);
 const notices=[],tileErrors=[];c.notices=notices;c.L={map(){return {remove(){},attributionControl:{setPrefix(){}},on(){}};},tileLayer(){return {addTo(){return this;},on(name,fn){tileErrors.push(fn);}};},layerGroup(){return {addTo(){return this;}};}};
 run('toast=message=>notices.push(message);ReportMap.points=()=>[[10,55]];ReportMap.fit=()=>{};ReportMap.draw=()=>{};ReportMap.mount()');tileErrors[0]();tileErrors[0]();assert.equal(notices.length,1,'Repeated tile failures show one notice for the current map');run('ReportMap.mount()');tileErrors[0]();assert.equal(notices.length,1,'A removed map must not show a stale failure');tileErrors[1]();assert.equal(notices.length,2);
 console.log('Report language: service/rolling boundary counts, repeats, archived coverage, chart/table equality, private DNC omission, visit save payloads and unchanged original Danish print document passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
