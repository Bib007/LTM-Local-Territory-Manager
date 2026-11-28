'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const polygon=(left,right)=>[[left,55],[right,55],[right,55.02],[left,55.02]];
const cards=[
 {id:'one',number:'1',geo_polygon:polygon(10,10.02),address_ids:['old'],addresses:[]},
 {id:'two',number:'2',geo_polygon:polygon(10.01,10.03),address_ids:[],addresses:[]},
 {id:'three',number:'3',geo_polygon:[],address_ids:[],addresses:[]}
];
const addresses=[
 {id:'old',lng:10.005,lat:55.01},{id:'new-one',lng:10.006,lat:55.01},{id:'ambiguous',lng:10.015,lat:55.01},
 {id:'blocked',lng:10.007,lat:55.01},{id:'ignored',lng:10.008,lat:55.01},{id:'new-two',lng:10.025,lat:55.01}
];
const writes=[],notices=[];
const context={state:{cards},page:'Kortopsætning',document:{addEventListener(){}},window:{addEventListener(){},confirm:()=>true},cmp:(a,b)=>a.localeCompare(b),card:id=>cards.find(c=>c.id===id),render(){},I18n:{text:s=>s,format:s=>s},mutate:async(action,data)=>writes.push({action,data})};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/geo.js'),'utf8'),context);
const geo=vm.runInContext('GeoUI',context);
geo.preview=async(data)=>({addresses:addresses.filter(a=>geo.pointInside([a.lng,a.lat],data.polygon)),conflicts:[{id:'blocked'}],ignored:['ignored'],retired:[]});
geo.draftStamp=()=>'';geo.setNotice=(key,params)=>notices.push(params);
(async()=>{
 await geo.autoAll();
 assert.equal(writes.length,2);
 assert.deepEqual(JSON.parse(JSON.stringify(writes.map(w=>[w.action,w.data.card_id,w.data.address_ids]))),[['geo.assign','one',['old','new-one']],['geo.assign','two',['new-two']]]);
 assert.deepEqual(JSON.parse(JSON.stringify(writes[0].data.auto_expected.address_ids)),['old']);
 assert.deepEqual(JSON.parse(JSON.stringify(notices.at(-1))),{updated:2,skipped:0,remaining:0});
 assert.equal(geo.bulkAutoBusy,false);
 geo.dirty=true;await geo.autoAll();assert.equal(writes.length,2,'Unsaved editor draft blocks bulk writes');
 geo.dirty=false;writes.length=0;
 cards[0].imported_addresses=[{lng:10.005,lat:55.01}];
 cards[1].imported_addresses=[{lng:10.025,lat:55.01}];
 cards[2].imported_addresses=[{lng:10.04,lat:55.01}];
 const shared={id:'shared'},safe={id:'safe'};
 geo.preview=async(data,id)=>({addresses:id==='one'?[shared]:id==='two'?[shared]:[safe],conflicts:[],ignored:[],retired:[],unmatched_points:0});
 await geo.importedAll();
 assert.equal(writes.length,1,'Cross-card coordinate matches must not depend on card order');
 assert.equal(writes[0].data.card_id,'three');
 assert.deepEqual(JSON.parse(JSON.stringify(writes[0].data.address_ids)),['safe']);
 assert.deepEqual(JSON.parse(JSON.stringify(writes[0].data.polygon)),[],'A coordinate match does not draw a new boundary');
 assert.deepEqual(JSON.parse(JSON.stringify(notices.at(-1))),{updated:1,skipped:2,remaining:0});
 writes.length=0;
 geo.preview=async()=>({addresses:[safe],conflicts:[],ignored:[],retired:[],unmatched_points:1});
 await geo.importedAll();
 assert.equal(writes.length,0,'Incomplete matches must retain imported street lists');
 console.log('Bulk auto houses preserves selected addresses, excludes ambiguous/blocked/ignored addresses, and skips cards without boundaries.');
})().catch(error=>{console.error(error);process.exitCode=1;});
