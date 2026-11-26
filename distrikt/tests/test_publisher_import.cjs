// Fictional names and local callbacks only; never sends a file to a service.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),nodes=new Map(),requests=[];
const el=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},open:true,addEventListener(){}});return nodes.get(id);};
const c={console,Map,Set,Array,Object,JSON,Number,String,Promise,el,document:{getElementById:el,addEventListener(){}},openDialog:Object.assign(()=>{},{generation:1}),publisherRoleLabels:{'':'Ingen gruppefunktion',overseer:'Gruppetilsynsmand',assistant:'Assistent'},setTimeout(){},URL};vm.createContext(c);
for(const name of ['i18n.js','publisher-import-ui.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),c);
const run=s=>vm.runInContext(s,c);run('esc=I18n.escape;ui=(v,p)=>I18n.label(v,p)');
c.plan={token:'FICTIONAL',new:0,update:1,existing:0,errors:[],invalid:0,rows:[{line:2,status:'update',before:{name:'Fiktiv <A>',group:'G & 1',group_role:'',pioneer:false},record:{name:'Fiktiv <A>',group:'G & 2',group_role:'assistant',pioneer:true}}]};
for(const language of ['da','en']){run(`I18n.set('${language}');PublisherImportUI.preview=plan;PublisherImportUI.paint()`);assert.match(el('publisherImportPreview').innerHTML,/Fiktiv &lt;A&gt;/);assert.match(el('publisherImportPreview').innerHTML,/G &amp; 2/);assert.ok(!el('publisherImportPreview').innerHTML.includes('<A>'));}
assert.match(el('publisherImportPreview').innerHTML,/0 new/);assert.match(el('publisherImportPreview').innerHTML,/Assistant/);assert.match(el('publisherImportPreview').innerHTML,/Approve group list/);
c.api=async(url,body)=>{requests.push(body);return {json:async()=>({result:{...c.plan,token:body.data.name}})};};
(async()=>{
 let release;c.old={name:'old.csv',size:10,text:()=>new Promise(r=>release=r)};c.next={name:'new.csv',size:10,text:async()=>'fictional'};
 const pending=run('PublisherImportUI.read(old)');await run('PublisherImportUI.read(next)');release('fictional old');await pending;
 assert.equal(requests.length,1);assert.equal(run('PublisherImportUI.preview.token'),'new.csv');
 c.large={name:'too-large.csv',size:2000001};await run('PublisherImportUI.read(large)');assert.equal(requests.length,1);assert.equal(run('PublisherImportUI.preview'),null);
 console.log('Group import: bilingual and escaped before/after review, no write while reading, bounded files and abandoned file reads passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
