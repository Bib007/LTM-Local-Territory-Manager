'use strict';
// VM-only UI tests; fictional cards and zero network requests.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../app/admin.js'),'utf8').split("document.addEventListener('change'")[0];
const cards=[
 {id:'a',number:'F101',name:'Fiktiv A',in_folder:false},
 {id:'b',number:'F102',name:'Fiktiv B',in_folder:true},
 {id:'c',number:'F103',name:'Fiktiv C',in_folder:false},
 {id:'d',number:'F104',name:'Fiktiv D',in_folder:false},
 {id:'e',number:'F105',name:'Fiktiv E',in_folder:false},
];
const c={console,Map,Set,JSON,Array,Object,Date,Math,Number,String,Promise,
 state:{cards,loans:[{card_id:'c',returned:null}]},dialogHtml:'',renderCount:0,
 I18n:{text:s=>s,language:()=> 'da'},
 ui:(s,values={})=>s.replace(/\\{(\\w+)\\}/g,(_,k)=>values[k]??''),
 esc:s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
 openDialog(html){c.dialogHtml=html;},
 render(){c.renderCount++;},
};
c.card=id=>c.state.cards.find(x=>x.id===id);
c.loanFor=id=>c.state.loans.find(l=>l.card_id===id&&!l.returned);
let calls=[];
c.mutate=async(action,data,options)=>{
 calls.push({action,data,options});
 for(const id of ['a','d'])c.card(id).in_folder=true;
 c.card('e').in_folder=true; // other user's concurrent move
 return {count:2,updated:['a','d'],skipped:[{id:'e',reason:'Kortet er allerede flyttet. Opdater siden og vælg igen.'}]};
};
vm.createContext(c);vm.runInContext(source,c);
const run=code=>vm.runInContext(code,c);
(async()=>{
 // 0 cards: disabled action and no destructive API request.
 const empty=run('AdminUI.selection([state.cards[0]])');
 assert.match(empty,/0 kort valgt på tværs af filtre/);
 assert.match(empty,/data-action="folder-selection" disabled/);
 run('AdminUI.folderPreview()');
 assert.match(c.dialogHtml,/Ingen kort kan flyttes/);
 assert.match(c.dialogHtml,/data-admin="folder-confirm" disabled/);
 assert.equal(calls.length,0);

 // Selected IDs are independent of current search, area and status filters.
 run("AdminUI.selected=new Set(['a','b','c','d','e'])");
 const html=run('AdminUI.selection([state.cards[0]])');
 assert.match(html,/5 kort valgt på tværs af filtre/);
 assert.match(html,/Læg 3 i mappen/);
 assert.match(html,/2 springes over/);
 assert.match(html,/F105/);
 run('AdminUI.folderPreview()');
 const ids=run('AdminUI.folderPending.ids.slice()');
 assert.deepEqual(Array.from(ids),['a','d','e']);
 assert.match(c.dialogHtml,/F102/);
 assert.match(c.dialogHtml,/F103/);
 assert.match(c.dialogHtml,/Kort der springes over/);

 const response=await run('AdminUI.folderConfirm()');
 assert.deepEqual(Array.from(response.updated),['a','d']);
 assert.equal(calls.length,1);
 assert.equal(calls[0].action,'folder.set_many');
 assert.deepEqual(Array.from(calls[0].data.ids),['a','d','e']);
 assert.equal(calls[0].data.expected_in_folder,false);
 assert.equal(calls[0].options.close,false);
 assert.match(c.dialogHtml,/2 kort lagt i mappen/);
 assert.match(c.dialogHtml,/3 kort ikke ændret/);
 assert.match(c.dialogHtml,/F105/);
 assert.deepEqual(Array.from(run('[...AdminUI.selected]')),['b','c','e']);
 assert.ok(c.renderCount>=1);

 // One-card selection with a pending response: second click cannot resend.
 run("AdminUI.selected=new Set(['e']);state.cards.find(c=>c.id==='e').in_folder=false");
 run("AdminUI.folderPreview()");
 let release,attempts=0;
 c.mutate=()=>{attempts++;return new Promise(resolve=>{release=resolve;});};
 const pending=run('AdminUI.folderConfirm()');
 const duplicate=run('AdminUI.folderConfirm()');
 assert.equal(attempts,1);
 release({count:1,updated:['e'],skipped:[]});
 await Promise.all([pending,duplicate]);
 assert.equal(attempts,1);
 assert.equal(run('AdminUI.selected.size'),0);
 console.log('Fictional bulk-folder UI: zero/one/many, filtering, mixed statuses, partial failures, and repeat clicks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
