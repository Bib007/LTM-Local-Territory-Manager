// Synthetic geographic lookup regression. No network, credentials or real data.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../app/geo.js'),'utf8');
const markers=[];
const layer=()=>({addTo(){return this},bindTooltip(){return this},on(){return this}});
const context={console,document:{addEventListener(){}},window:{addEventListener(){}},
  MapBackground:{roads:()=>false,buildings:()=>false},
  L:{circleMarker(point,options){markers.push({point,options});return layer();},polyline:()=>layer(),polygon:()=>layer()},
  esc:x=>String(x),ui:x=>x};
vm.createContext(context);vm.runInContext(source,context);
const geo=vm.runInContext('GeoUI',context);
const a=(id,lat,road='Fiktivvej',number=id)=>({id,postcode:'9999',road,number,floor:'',door:'',lat,lng:10,count:1});
const addresses=[a('a0',55),a('a1',55),a('a2',56),a('a3',56)];
const c=(id,address_ids=[],geo_addresses=[])=>({id,number:id,address_ids,geo_addresses,geo_polygon:[]});
const other=c('older',['a0']);const legacy=c('legacy',[],[addresses[0]]);const current=c('current',['a1']);
let cards=[other,legacy,current];
context.state={revision:'rev-1',cards,ignored:[{address_id:'a2'}]};
geo.data={addresses,buildings:[],roads:[],dividers:[],info:{},status:{
  a0:{card_id:'older',card_number:'older'},
  a1:{card_id:'current',card_number:'current'},
  a3:{card_id:'archived',card_number:'old'}
}};
geo.target='';geo.ids=new Set();geo.whole=false;
const legacyOwner=a=>{
  const owner=geo.data.status?.[a.id];
  return context.state.cards.find(c=>c.id!==geo.target&&(c.address_ids?.includes(a.id)||c.geo_addresses?.some(old=>geo.key(old)===geo.key(a))))||
    (owner?.card_id&&owner.card_id!==geo.target?{id:owner.card_id,number:owner.card_number}:null);
};
for(const target of ['', 'older', 'legacy', 'current', 'archived']){
  geo.target=target;
  for(const address of addresses){
    assert.equal(geo.owner(address)?.id||null,legacyOwner(address)?.id||null,
      'the owner must match prior first-card precedence, excluding the current card');
  }
}
assert.equal(geo.owner(addresses[3]).id,'archived','server status fallback preserved');
assert(!geo.available(addresses[2]),'ignored address not selectable');
assert(!geo.available(addresses[0]),'other-card address not selectable');
geo.target='older';
assert(!geo.owner(addresses[0])||geo.owner(addresses[0]).id==='legacy','legacy link still blocks');
const oldGroups=geo.groups();assert.equal(oldGroups.flat().length,4);
assert.strictEqual(geo.groups(),oldGroups,'reuse address groups on warm pan');
const next=[...addresses,a('a4',57)];
geo.data={...geo.data,addresses:next};
assert.equal(geo.groups().flat().length,5,'new response exposes new addresses');
context.state={...context.state,cards:[c('replacement',['a4'])],revision:'rev-2'};
geo.target='';
assert.equal(geo.owner(next[4]).id,'replacement','new cards/revision invalidate lookup');
context.state={...context.state,cards:[c('another',['a3'])]};
assert.equal(geo.owner(next[3]).id,'another','new cards without revision change invalidate lookup');
context.state={...context.state,cards:[],revision:'rev-3'};
assert.equal(geo.owner(next[3]).id,'archived','fallback after card deletion');

// Paint separate viewports. Unseen address groups must remain available on pan.
geo.layers={clearLayers(){markers.length=0;}};
geo.data={...geo.data,addresses:next};
geo.target='';geo.ids=new Set(['a4']);geo.whole=false;
let low=54.5,high=55.5;
geo.map={getZoom:()=>17,getBounds:()=>({pad:()=>({contains:([lat])=>lat>=low&&lat<=high})})};
geo.drawLayers();assert.equal(markers.length,2,'first viewport renders both first addresses');
low=55.5;high=56.5;geo.drawLayers();assert.equal(markers.length,2,'panning reveals both addresses previously off screen');
low=56.5;high=57.5;geo.drawLayers();assert.equal(markers.length,1);
assert.equal(markers[0].options.fillColor,'#248e5a','selected address remains selected after pan');
assert.equal(geo.groups().flat().length,5,'pan does not prune stored addresses');

console.log('Geo index: card order, legacy ownership, ignored addresses, stale fallback, revision invalidation, cached groups, viewport pan and selection OK.');
