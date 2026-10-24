// Invented local files and responses; never contacts a service or writes user data.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),nodes=new Map(),requests=[];
const el=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},value:'',disabled:false,isConnected:true,open:true,addEventListener(){}});return nodes.get(id);};
const c={console,Map,Set,Array,Object,JSON,Number,String,Promise,el,requests,document:{getElementById:el,addEventListener(){},querySelector(){return null;}},page:'Indstillinger',openDialog:Object.assign(()=>{},{generation:1}),closeDialog(){el('dialog').open=false;},closeRequested:async()=>{},render(){},toast(){},setTimeout(){},URL,refresh:async()=>true};vm.createContext(c);
for(const name of ['i18n.js','card-import-ui.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),c);
const run=s=>vm.runInContext(s,c);run("esc=I18n.escape;ui=(v,p)=>I18n.label(v,p);confirmedWrite=async(path,body,after)=>{requests.push(body);return after({json:async()=>({result:{count:1}})});};api=async(path,body)=>{requests.push(body);return {json:async()=>({result:{token:body.data.name,cards:[],areas:[],errors:[],addresses:0,visits:0}})}}");
const file=name=>({name,size:10,text:async()=>name});
(async()=>{
 c.files=[file('one <fictional>.csv'),file('two.csv')];await run('CardImportUI.choose(files)');assert.equal(requests.length,1);assert.match(el('cardImportQueue').innerHTML,/one &lt;fictional&gt;/);
 el('cardImportConfirm').value='IMPORTÉR KORT';await run('CardImportUI.apply()');assert.equal(requests.length,2);assert.equal(run('CardImportUI.queueIndex'),1);assert.equal(el('dialog').open,true);assert.equal(run('CardImportUI.preview'),null);await run('CardImportUI.apply()');assert.equal(requests.length,2,'No replay without a new reviewed file');
 await run('CardImportUI.next()');assert.equal(requests[2].data.name,'two.csv');run('CardImportUI.skip()');assert.equal(run('CardImportUI.queueIndex'),2);assert.equal(requests.length,3,'Skipping never applies a file');assert.equal(run('CardImportUI.queue.every(f=>f===null)'),true);
 c.files=Array.from({length:21},()=>file('file.csv'));await run('CardImportUI.choose(files)');assert.equal(requests.length,3);assert.equal(run('CardImportUI.preview'),null);assert.equal(run('CardImportUI.queue.length'),0);
 c.files=[{...file('big.csv'),size:2000001}];await run('CardImportUI.choose(files)');assert.equal(requests.length,3);
 c.files=Array.from({length:11},()=>({...file('file.csv'),size:2000000}));await run('CardImportUI.choose(files)');assert.equal(requests.length,3);
 let release;c.files=[{...file('slow.csv'),text:()=>new Promise(r=>release=r)},file('next.csv')];const pending=run('CardImportUI.choose(files)');run('CardImportUI.skip()');release('fictional');await pending;assert.equal(requests.length,3,'An abandoned read cannot overwrite the next file');assert.equal(run('CardImportUI.preview'),null);
 console.log('Card import queue: bounds, escaped filenames, separate approvals, no automatic write/replay, skip, released file references and abandoned reads passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
