// Invented local print sessions; never loads user data or contacts a service.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const nodes=new Map(),writes=[],messages=[];let pendingAsset,pendingSave,blockPopup=false,decodeFails=false,popupCount=0;
const button=()=>({disabled:true,textContent:'',addEventListener(){}});
function popup(){popupCount++;const controls={print:button(),tooLong:button(),printReport:button(),printAssetError:button()};return {closed:false,close(){this.closed=true;},print(){},document:{markup:'',images:[],write(s){this.markup=s;},open(){},close(){},getElementById:id=>controls[id],querySelectorAll:()=>[]},controls};}
let win;
class Fields{constructor(f){this.fields=f.fields;}has(k){return this.fields.some(([key])=>key===k);}[Symbol.iterator](){return this.fields[Symbol.iterator]();}}
const c={console,Map,Set,Promise,FormData:Fields,location:{origin:'http://fictional.test'},document:{getElementById:id=>nodes.get(id),addEventListener(){},querySelectorAll:()=>[]},window:{open(){return blockPopup?null:(win=popup());}},
 FileReader:class{readAsDataURL(){this.result='data:image/png;base64,FICTIONAL';this.onload();}},Image:class{decode(){return decodeFails?Promise.reject(Error('bad image')):Promise.resolve();}},fetch:async()=>{if(pendingAsset)await pendingAsset;return {ok:true,blob:async()=>({})};},writes,messages};
vm.createContext(c);for(const n of ['i18n.js','printing.js','report-print.js'])vm.runInContext(read(n),c);
const run=s=>vm.runInContext(s,c);c.nodes=nodes;
run(`let state={revision:'r1',settings:{},cards:[{id:'c1',number:'101',name:'PRINT <invented>',front_revision:true}]},page='Distrikter',year=2027;const esc=v=>I18n.escape(v),ui=(key,p)=>I18n.label(key,p),el=id=>nodes.get(id),card=id=>state.cards.find(c=>c.id===id),cmp=(a,b)=>a.localeCompare(b);
function openDialog(html,language){openDialog.generation=(openDialog.generation||0)+1;nodes.set('dialog',{innerHTML:html,lang:language});}openDialog.generation=1;
let closeCount=0;function closeDialog(){closeCount++;}function formEnd(key){return ui(key);}function toast(s){messages.push(s);}
const frontHTML=c=>'<div class="cardPreview"><img src="/original.png"><span>'+esc(c.name)+'</span></div>',backHTML=c=>'<div class="ibPreview">IB <invented></div>';
let Workspace={reportPeriod:'service'},ReportMap={map:{},draw(){},printable:async()=>'<svg>fictional</svg>'};`);
c.mutate=async(action,data)=>{writes.push({action,data:JSON.parse(JSON.stringify(data))});if(pendingSave)await pendingSave;};
const form=(remember=true)=>{const f={dataset:{id:'c1',side:'front',ids:'["c1"]'},isConnected:true,fields:Object.entries({orientation:'landscape',paper:'a4',mode:'full',width:'146',height:'94',x:'1',y:'-1',...(remember?{remember:'on'}:{})})};nodes.set('printForm',f);return f;};
(async()=>{
 const docs={},contracts={};for(const language of ['da','en']){run(`I18n.set('${language}');printOptions('c1','front')`);const html=nodes.get('dialog').innerHTML;contracts[language]=html.match(/(?:name|value|data-side|data-ids)="[^"]*"/g);assert.match(html,/printForm/);assert.match(html,language==='en'?/Preview and print/:/Fremvis og print/);assert.equal(nodes.get('dialog').lang,language);docs[language]=run("printDocument(state.cards,'front',defaultPrintProfile('front'))");}
 assert.deepEqual(contracts.da,contracts.en);assert.equal(docs.da.split('<section class="sheet"')[1],docs.en.split('<section class="sheet"')[1]);assert.match(docs.en,/Print \/ save PDF/);assert.match(docs.en,/PRINT &lt;invented&gt;/);
 // A profile write can finish after a new dialog opens without closing it.
 let release;pendingSave=new Promise(r=>release=r);const f=form(),job=run('printCard')(f);while(!writes.length)await new Promise(r=>setImmediate(r));await run('printCard')(f);assert.equal(writes.length,1);assert.equal(popupCount,1);run("openDialog('NEWER DRAFT','en')");release();await job;pendingSave=null;assert.equal(run('closeCount'),0);assert.equal(nodes.get('dialog').innerHTML,'NEWER DRAFT');assert.deepEqual(writes[0],{action:'print.profile.save',data:{side:'front',profile:{orientation:'landscape',paper:'a4',mode:'full',width:146,height:94,x:1,y:-1}}});assert.equal(run('state.cards[0].front_revision'),true);
 // Closed/replaced print forms and changed revisions discard pending assets without saving.
 for(const change of ['revision','dialog','navigation','closed','fields']){let release;pendingAsset=new Promise(r=>release=r);const f=form(),before=writes.length,job=run('printCard')(f);if(change==='revision')run("state.revision+='-changed'");if(change==='dialog')run("openDialog('NEWER DRAFT','en')");if(change==='navigation')run("page='Forside'");if(change==='closed')win.close();if(change==='fields')f.fields.find(([key])=>key==='width')[1]='150';release();await assert.rejects(job,/Printgrundlaget er ændret/);assert.equal(win.closed,true);assert.equal(writes.length,before);assert.equal(f.dataset.printing,undefined);pendingAsset=null;run("page='Distrikter'");}
 blockPopup=true;await assert.rejects(run('printCard')(form()),/Tillad et nyt vindue/);blockPopup=false;
 // Broken decoded images must keep the card print button disabled.
 c.window.open=()=>{win=popup();win.document.images=[{decode:async()=>{throw Error('corrupt original');}}];return win;};await run('printCard')(form(false));await new Promise(r=>setImmediate(r));assert.equal(win.controls.print.disabled,true);assert.match(win.controls.tooLong.textContent,/Print images could not load/);
 c.window.open=()=>win=popup();
 // Report navigation during an awaited map must preserve the newer page and period.
 let releaseMap;c.mapWait=new Promise(r=>releaseMap=r);run("ReportMap.printable=async()=>mapWait");const jobReport=run('printReport()');await run('printReport()');run("page='Forside';Workspace.reportPeriod='rolling';ReportMap.map={}");releaseMap('<svg>fictional</svg>');await assert.rejects(jobReport,/Printgrundlaget er ændret/);assert.equal(run('Workspace.reportPeriod'),'rolling');assert.equal(win.closed,true);assert.equal(run('printReport.busy'),false);
 // Missing report images fail closed after the document is assembled.
 run("page='Rapporter';Workspace.reportPeriod='service';ReportMap.printable=async()=>'<svg>fictional</svg>';reportPrintDocument=()=>'<p>FICTIONAL REPORT</p>';inlineReportAssets=async s=>s");
 c.window.open=()=>{win=popup();win.document.querySelectorAll=()=>[{getAttribute:()=>'/corrupt.jpg'}];return win;};decodeFails=true;await run('printReport()');assert.equal(win.controls.printReport.disabled,true);assert.match(win.controls.printAssetError.textContent,/Print images could not load/);assert.equal(run('Workspace.reportPeriod'),'service');
 console.log('Print: bilingual controls, unchanged originals and payloads, blocked popups, duplicate guards, stale assets/dialogs, revisions and failed image decoding passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
