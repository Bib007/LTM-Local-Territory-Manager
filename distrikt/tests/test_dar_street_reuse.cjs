'use strict';
// Invented roads and addresses only. No private data or network is accessed.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const dialog={open:true},road={road:'Fictional Søvej',postcode:'9999'};
const full={entity:'download',source:'DAR / Datafordeleren',
 complete_road:{road:'FICTIONAL SØVEJ',postcode:'9999'}};
const address={entity:'address',road:'Fictional Søvej',postcode:'9999',number:'3',retired:false};
let loads=0,steps=0,closes=0;
const geo={
 target:'f-card',session:1,busy:false,data:{addresses:[address],info:{downloads:[full]}},
 draftStamp:()=> 'untouched-draft',canLeave:()=>true,
 preview:async data=>{assert.equal(data.mode,'street_lines');assert.equal(data.planning_only,true);
  return {roads:[road],source_expected:'unmodified-street-line'};},
 load:async()=>{loads++;},
};
const cardData={id:'f-card',number:'F1',addresses:[{road:'Fictional Søvej',numbers:'1-9'}]};
const form={reportValidity:()=>true,elements:{postcode_0:{value:'9999'},refresh_roads:{checked:false}}};
const c={document:{addEventListener(){}},GeoUI:geo,card:id=>id==='f-card'?cardData:null,
 openDialog:{generation:0},el:id=>id==='dialog'?dialog:null,closeDialog(){closes++;dialog.open=false;},form};
vm.createContext(c);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/street-suggestions.js'),'utf8'),c);
vm.runInContext('StreetSuggestions.next=async function(){this.nextCalls=(this.nextCalls||0)+1;}',c);
const pending=()=>JSON.parse(vm.runInContext('JSON.stringify(StreetSuggestions.pending)',c));
async function start({downloads=[full],addresses=[address],refresh=false}={}){
 geo.data={addresses,info:{downloads}};
 form.elements.refresh_roads.checked=refresh;
 dialog.open=true;
 vm.runInContext('StreetSuggestions.pending=null',c);
 await vm.runInContext('StreetSuggestions.start(form)',c);
 return pending();
}
(async()=>{
 let p=await start();
 assert.equal(p.roads.length,0,'Complete full roads should be reused with no new DAR download');
 assert.equal(p.postcodes[0],'9999');
 assert.equal(p.source_expected,'unmodified-street-line');
 p=await start({refresh:true});
 assert.equal(p.roads.length,1,'Explicit refresh downloads the entire road again');
 p=await start({downloads:[]});
 assert.equal(p.roads.length,1,'Missing road marker requires a new complete download');
 p=await start({addresses:[]});
 assert.equal(p.roads.length,1,'A marker with no usable address cannot bypass the download');
 p=await start({downloads:[{...full,source:'Local import'}]});
 assert.equal(p.roads.length,1,'Local imports do not qualify as official complete-road evidence');
 p=await start({addresses:[{...address,retired:true}]});
 assert.equal(p.roads.length,1,'Only retired addresses require a fresh source lookup');
 p=await start({addresses:[{...address,postcode:'9998'}]});
 assert.equal(p.roads.length,1,'The postcode must match for cache reuse');
 assert.equal(loads,7,'Every attempt validates against fresh local geographic status');
 assert.equal(closes,7);
 assert.equal(vm.runInContext('StreetSuggestions.nextCalls',c),7);
 console.log('DAR street suggestions reuse complete local roads; refresh, partial/missing data and postcode guards passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
