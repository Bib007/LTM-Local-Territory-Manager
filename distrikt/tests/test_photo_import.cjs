// Production photo-import state machine with invented local card/unit records.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',value:'',disabled:false,open:true,isConnected:true,hidden:false,removeAttribute(){},addEventListener(){}});return nodes.get(id);};
const member={id:'a',road:'Fiktivvej',number:'8',postcode:'9999',floor:'1',door:'tv'};
const calls=[],c={console,URL:{createObjectURL:()=> 'blob:fictional',revokeObjectURL(){}},window:{confirm:()=>true},document:{getElementById:get,addEventListener(){},querySelectorAll:()=>[]},setTimeout:(f)=>setImmediate(f),el:get,ui:(s)=>s,esc:s=>String(s||'').replace(/</g,'&lt;'),I18n:{text:s=>s,content:(n,s)=>n.textContent=s,applyShell(){},errorContent:(n,e)=>n.textContent=e.message},card:id=>id==='c'?{id:'c',number:'901',imported_addresses:[member]}:null,GeoUI:{addresses:()=>[]},state:{today:'2026-10-24'},openDialog:Object.assign(()=>{}, {generation:1}),api:async(path,body)=>{calls.push({path,body});throw Error('Unexpected API');}};
vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/photo-import-ui.js'),'utf8'),c);const ui=vm.runInContext('PhotoImportUI',c);
get('photoCard').value='c';get('photoText').value='Heading <fictional>\nFiktivvej 8, 1 tv - 24.10.2026';ui.parse();assert.equal(ui.rows.length,2);assert.equal(ui.rows[0].address,'');assert.equal(ui.rows[1].address,'a');assert.equal(ui.rows[1].date,'2026-10-24');assert.throws(()=>ui.csv());ui.rows[0].skipped=true;assert.match(ui.csv(),/"901";"Fiktivvej";"8";"9999";"1";"tv";"2026-10-24"/);assert.equal(calls.length,0,'Recognition parsing writes nothing');
for(const value of ['Fiktivvej 8, 1 tv - 2026-10-24','Fiktivvej 8, 1 tv – 24/10/2026'])assert.equal(ui.date(value).date,'2026-10-24');assert.equal(ui.date('Fiktivvej 8, 1 tv').date,'');
(async()=>{
 let resolve;c.api=async(path,body)=>{calls.push({path,body});return await new Promise(r=>resolve=r);};
 let check=ui.check();ui.rows[1].date='2026-10-23';resolve({json:async()=>({result:{token:'old',new:1,existing:0,errors:0,rows:[]}})});await check;assert.equal(ui.preview,null,'A late preview cannot approve edited rows');
 // A late OCR-start response after Skip is cancelled and cannot populate the next image.
 calls.length=0;let start;c.api=async(path,body)=>{calls.push({path,body});if(path==='/api/photo/read')return new Promise(r=>start=r);return {json:async()=>({ok:true})};};ui.png=async()=> 'FICTIONAL_PNG';ui.queue=[{name:'one.png'},{name:'two.png'}];ui.index=0;get('photoText').value='';const reading=ui.read();while(!start)await new Promise(r=>setImmediate(r));ui.finish(true);start({json:async()=>({id:'abandoned'})});await reading;assert.equal(ui.index,1);assert.equal(get('photoText').value,'');assert.ok(calls.some(r=>r.path==='/api/photo/cancel'&&r.body.id==='abandoned'));assert.equal(ui.reading,false);
 // Invalid type/count/total size must fail before reading anything.
 for(const files of [[{name:'bad.svg',type:'image/svg+xml',size:1}],Array.from({length:21},()=>({name:'x.png',size:1,type:'image/png'})),Array.from({length:6},()=>({name:'x.png',size:11000000,type:'image/png'}))])await assert.rejects(ui.choose(files));
 ui.reset();assert.equal(ui.queue.length,0);assert.equal(ui.rows.length,0);assert.equal(ui.preview,null);
 console.log('Photo import: exact local apartment matching, explicit skip/date, no parsing writes, late preview/start cancellation, queue limits and closing cleanup passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
