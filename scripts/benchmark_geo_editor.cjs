// Run: node scripts/benchmark_geo_editor.cjs
// Optional: LTM_ADDRESSES=12000 LTM_CARDS=240 LTM_REPEATS=7 node scripts/benchmark_geo_editor.cjs
// Fictional data only. Measures the real GeoUI data/layer code with a stubbed
// Leaflet API, NOT browser canvas paint or the actual Python/SQLite backend.
// Legacy methods below are the exact pre-optimization owner()/groups() logic.
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const http=require('node:http'),{performance}=require('node:perf_hooks');
const N=Number(process.env.LTM_ADDRESSES||12000),C=Number(process.env.LTM_CARDS||240);
const R=Number(process.env.LTM_ROADS||900),B=Number(process.env.LTM_BUILDINGS||2800);
const repetitions=Number(process.env.LTM_REPEATS||7);
if(!Number.isInteger(N)||N<10||N>100000||!Number.isInteger(C)||C<1||C>5000||
   !Number.isInteger(R)||R<0||R>50000||!Number.isInteger(B)||B<0||B>50000||
   !Number.isInteger(repetitions)||repetitions<3||repetitions>40)throw Error('Invalid synthetic benchmark size.');
const addresses=Array.from({length:N},(_,i)=>({
  id:'fictional-a'+i,postcode:'7000',road:'Fiktivvej '+Math.floor(i/120),
  number:String(i%120+1),floor:'',door:'',lat:55.5+(i%300)*.00005,
  lng:9.5+Math.floor(i/300)*.00005,count:1
}));
const cards=Array.from({length:C},(_,i)=>({
  id:'fictional-c'+i,number:String(i+1),address_ids:[],geo_addresses:[],geo_polygon:[]
}));
for(let i=0;i<N;i++)if(i%5!==0)cards[i%C].address_ids.push(addresses[i].id);
const status={};
for(const c of cards)for(const id of c.address_ids)status[id]={card_id:c.id,card_number:c.number};
const roads=Array.from({length:R},(_,i)=>({id:'r'+i,name:'Fiktivvej '+i,
  road_type:'residential',points:[[9.5+i*.00001,55.5],[9.51+i*.00001,55.51]]}));
const buildings=Array.from({length:B},(_,i)=>({id:'b'+i,points:[
  [9.5+i*.000005,55.5],[9.50005+i*.000005,55.5],
  [9.50005+i*.000005,55.50005],[9.5+i*.000005,55.50005]
]}));
const ignored=addresses.filter((_,i)=>i%73===0).map(a=>({address_id:a.id}));
const geoData={addresses,status,roads,buildings,dividers:[],info:{},main_boundary:null};
const geoJson=JSON.stringify(geoData);
const stateData={cards,ignored,revision:'baseline',loans:Array.from({length:2000},(_,i)=>({
  id:'fictional-loan-'+i,card_id:cards[i%C].id,assigned:'2026-01-01',returned:'2026-02-01'
}))};
const stateJson=JSON.stringify(stateData),source=fs.readFileSync(path.join(__dirname,'../distrikt/app/geo.js'),'utf8');

function legacyOwner(a){
  const owner=this.data.status?.[a.id];
  return this._benchmarkState.cards.find(c=>c.id!==this.target&&
    (c.address_ids?.includes(a.id)||c.geo_addresses?.some(old=>this.key(old)===this.key(a))))||
    (owner?.card_id&&owner.card_id!==this.target?{id:owner.card_id,number:owner.card_number}:null);
}
function legacyGroups(){
  const groups=new Map();
  for(const a of this.addresses()){
    const key=[a.postcode,a.road.toLowerCase(),a.number.toUpperCase()].join('|');
    if(!groups.has(key))groups.set(key,[]);
    groups.get(key).push(a);
  }
  return [...groups.values()];
}
function timed(fn){
  const results=[];
  for(let i=0;i<repetitions;i++){const t=performance.now();fn(i);results.push(performance.now()-t);}
  const sorted=[...results].sort((a,b)=>a-b);
  return {median_ms:Number(sorted[Math.floor(sorted.length/2)].toFixed(2)),
    repetitions_ms:results.map(t=>Number(t.toFixed(2)))};
}
const parsed=timed(()=>JSON.parse(geoJson));

function prepare(legacy){
  let markers=0,layers=0;
  const layer=()=>({addTo(){layers++;return this;},bindTooltip(){return this;},on(){return this;}});
  const context={console,document:{addEventListener(){}},window:{addEventListener(){}},
    L:{polyline:()=>layer(),polygon:()=>layer(),circleMarker:()=>{markers++;return layer();}},
    MapBackground:{roads:()=>true,buildings:()=>true},esc:x=>String(x),ui:x=>String(x),cardColor:()=> '#477596',
    state:stateData};
  vm.createContext(context);vm.runInContext(source,context);
  const geo=vm.runInContext('GeoUI',context);
  geo.data=geoData;geo.loaded=true;geo.target='';geo.ids=new Set();geo.whole=false;
  geo.layers={clearLayers(){markers=0;layers=0;}};
  geo.map={getZoom:()=>17,getBounds:()=>({pad:()=>({contains:()=>true})})};
  if(legacy){geo._benchmarkState=context.state;geo.owner=legacyOwner;geo.groups=legacyGroups;}
  return {geo,context,counts:()=>({markers,layers})};
}
function run(legacy){
  const {geo,context,counts}=prepare(legacy);
  const cold=timed(i=>{
    geo._groupCache=null;geo._ownerLookup=null;geo.data=JSON.parse(geoJson);
    geo.target='';geo.ids=new Set();geo.drawLayers();
  });
  const expected=counts();
  const warm=timed(()=>geo.drawLayers());
  const transition=timed(i=>{
    geo.target=cards[i%C].id;geo.ids=new Set(cards[i%C].address_ids);
    geo.drawLayers();
  });
  const postSaveClientRefresh=timed(i=>{
    // Only the frontend refresh path: no real write or conflict handling is mocked.
    context.state={...context.state,revision:'fictional-save-'+i,
      cards:cards.map(c=>({...c}))};
    geo._benchmarkState=context.state;
    geo.data=JSON.parse(geoJson);
    geo.drawLayers();
  });
  return {cold,warm,transition,post_save_client_refresh:postSaveClientRefresh,counts:expected};
}
async function loopback(){
  const server=http.createServer((request,response)=>{
    response.setHeader('Content-Type','application/json');
    response.end(geoJson);
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;
  try{
    const times=[];
    for(let i=0;i<repetitions;i++){
      const t=performance.now();
      const response=await fetch('http://127.0.0.1:'+port+'/api/geo');
      const ttfb=performance.now()-t;
      const body=await response.text(),received=performance.now()-t;
      JSON.parse(body);
      times.push({ttfb_ms:Number(ttfb.toFixed(2)),receive_ms:Number(received.toFixed(2))});
    }
    return times;
  }finally{await new Promise(resolve=>server.close(resolve));}
}
(async()=>{
  const before=run(true),after=run(false);
  if(JSON.stringify(before.counts)!==JSON.stringify(after.counts))throw Error('Layer/marker parity regression.');
  const output={environment:{node:process.version,platform:process.platform,arch:process.arch},
    dataset:{addresses:N,cards:C,roads:R,buildings:B,ignored:ignored.length,
      geo_payload_bytes:Buffer.byteLength(geoJson),synthetic_state_payload_bytes:Buffer.byteLength(stateJson)},
    method:'Same real geo.js drawLayers, stubbed Leaflet layers; old owner/groups replaced by original methods. Synthetic loopback only.',
    repetitions,parse_geo:parsed,loopback_http:await loopback(),before,after,
    unmeasured:['Python/SQLite transaction and /api/state generation',
      'actual browser DOM/Leaflet canvas paint', 'profile permissions/conflict validation',
      'end-to-end confirmed save including retries']};
  console.log(JSON.stringify(output,null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
