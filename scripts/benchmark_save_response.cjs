// Synthetic JS-only response parsing cost, not Home Assistant or an HTTP/browser test.
'use strict';
const {performance}=require('node:perf_hooks');
const addresses=Number(process.env.LTM_ADDRESSES||50000),cards=Number(process.env.LTM_CARDS||180),history=Number(process.env.LTM_HISTORY||12000),runs=Number(process.env.LTM_REPEATS||7);
if(!Number.isInteger(addresses)||addresses<10||addresses>100000||!Number.isInteger(cards)||cards<1||cards>5000||!Number.isInteger(history)||history<0||history>100000||!Number.isInteger(runs)||runs<3||runs>40)throw Error('Invalid fictional sizes');
const state={revision:'synthetic-revision',cards:Array.from({length:cards},(_,i)=>({id:'fictional-c'+i,number:String(i+1),address_ids:[],map_color:'#477596'})),loans:Array.from({length:history},(_,i)=>({id:'fictional-loan'+i,card_id:'fictional-c'+(i%cards),assigned:'2026-01-01',returned:'2026-02-01',publisher_id:'fictional'})),addresses:Array.from({length:addresses},(_,i)=>({id:'fictional-a'+i,road:'Fiktivvej '+Math.floor(i/120),number:String(i%120+1),postcode:'7000',lat:55.5+(i%300)*.00005,lng:9.5+Math.floor(i/300)*.00005,status:'fictional-only'}))};
for(let i=0;i<addresses;i++)state.cards[i%cards].address_ids.push('fictional-a'+i);
const raw=JSON.stringify({ok:true,revision:state.revision,result:{id:'fictional-c0'},state});
const bytes=Buffer.byteLength(raw),modes={before:[],after:[]};
function parse(mode){const validated=JSON.parse(raw),consumed=mode==='before'?JSON.parse(raw):validated;if(consumed.state.revision!==validated.state.revision||consumed.state.addresses.length!==addresses)throw Error('Corrupted response');}
for(let i=0;i<3;i++){parse('before');parse('after');}
for(let i=0;i<runs;i++){for(const mode of (i%2?['after','before']:['before','after'])){const start=performance.now();parse(mode);modes[mode].push(Number((performance.now()-start).toFixed(3)));}}
const median=xs=>[...xs].sort((a,b)=>a-b)[Math.floor(xs.length/2)];
console.log(JSON.stringify({environment:{node:process.version,platform:process.platform,arch:process.arch},dataset:{addresses,cards,history,receipt_json_bytes:bytes},runs,before:{json_parse_count:2,median_ms:median(modes.before),repetitions_ms:modes.before},after:{json_parse_count:1,median_ms:median(modes.after),repetitions_ms:modes.after},scope:'Isolated JSON.parse cost only: no HTTP, SQLite, compression, Home Assistant, WebKit/Chromium, DOM or Leaflet'},null,2));
