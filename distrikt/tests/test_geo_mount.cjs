// Synthetic Leaflet regression for the editor's initial viewport and subsequent pan.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'../app/geo.js'),'utf8');
const near={id:'near',postcode:'9999',road:'Fiktivvej',number:'1',lat:55.01,lng:9.01};
const far={id:'far',postcode:'9999',road:'Fiktivvej',number:'2',lat:57.01,lng:12.01};
const data={addresses:[near,far],roads:[],buildings:[],dividers:[],info:{},status:{}};
const card={id:'fictional-card',number:'1',address_ids:['near'],geo_polygon:[]};
let respond;
const context={document:{addEventListener(){}},window:{addEventListener(){}},
  el:id=>id==='geographicEditor'?{}:null,api:()=>new Promise(resolve=>respond=resolve),
  page:'Kortopsætning',state:{cards:[card],ignored:[],revision:'fictional-1'},
  MapBackground:{attach(){},roads:()=>false,buildings:()=>false},
  MainBoundaryUI:{draw(){}},esc:x=>x,ui:x=>x,cardColor:()=> '#477596'};
const fakeLayer=()=>({addTo(){return this;},bindTooltip(){return this;},on(){return this;}});
let activeMarkers=[],map;
const L={canvas:()=>({_redraw(){}}),layerGroup:()=>({addTo(){return this;},clearLayers(){activeMarkers=[];}}),
  polygon:fakeLayer,polyline:fakeLayer,circleMarker(point){activeMarkers.push(point);return fakeLayer();},
  map(){let center=[56,10],zoom=8;const events={};const instance={fitCalls:0,
    setView(value,z){center=[...value];zoom=z;return this;},getCenter(){return {lat:center[0],lng:center[1]};},
    getZoom(){return zoom;},getBounds(){return {pad:()=>({contains:([lat,lng])=>Math.abs(lat-center[0])<(zoom>=17?.1:10)&&Math.abs(lng-center[1])<(zoom>=17?.1:10)})};},
    fitBounds(points){this.fitCalls++;center=[(Math.min(...points.map(p=>p[0]))+Math.max(...points.map(p=>p[0])))/2,(Math.min(...points.map(p=>p[1]))+Math.max(...points.map(p=>p[1])))/2];zoom=18;return this;},
    on(event,handler){events[event]=handler;return this;},
    panTo(value){center=[...value];events.moveend?.();return this;},remove(){}};
    map=instance;return instance;}};
context.L=L;
vm.createContext(context);vm.runInContext(source,context);
const geo=vm.runInContext('GeoUI',context);
geo.updatePanel=()=>{}; // The DOM panel is independent of viewport drawing.
const actualDraw=geo.drawLayers.bind(geo);let drawTimes=[];
geo.drawLayers=function(){drawTimes.push(this.map.fitCalls);actualDraw();};
function setup({whole=false,view=null,loaded=true}={}){
  geo.map=null;geo.layers=null;geo.draftLayer=null;geo.data=loaded?data:{addresses:[],buildings:[],roads:[],dividers:[],info:{}};
  geo.loaded=loaded;geo.ids=new Set(['near']);geo.target='fictional-card';geo.polygon=whole?[[9,55],[9.02,55],[9.02,55.02]]:[];
  geo.whole=whole;geo.view=view;geo.dirty=true;geo.session++;drawTimes=[];activeMarkers=[];
  geo.mount();
}
(async()=>{
 setup();
 assert.deepEqual(drawTimes,[1],'first address drawing must run after initial fitBounds');
 assert.equal(geo.markers.length,1,'off-viewport addresses must not get markers at mount');
 assert.equal(geo.markers[0].group[0].id,'near');
 map.panTo([57.01,12.01]);
 assert.equal(geo.markers.length,1,'pan rebuilds the viewport');
 assert.equal(geo.markers[0].group[0].id,'far','far-off address becomes visible on pan');
 assert.equal(geo.ids.has('near'),true,'pan does not lose unsaved selections');
 assert.equal(geo.dirty,true,'pan does not clear unsaved draft');

 setup({view:{center:[57.01,12.01],zoom:18}});
 assert.deepEqual(drawTimes,[0],'a saved viewport must not be refitted');
 assert.equal(geo.markers[0].group[0].id,'far');
 assert.equal(map.getZoom(),18);

 setup({whole:true});
 assert.deepEqual(drawTimes,[1],'whole-boundary mode must fit before its first drawing');
 assert.equal(geo.whole,true);
 assert.deepEqual(geo.polygon,[[9,55],[9.02,55],[9.02,55.02]]);

 setup({loaded:false,view:{center:[57.01,12.01],zoom:18}});
 assert.deepEqual(drawTimes,[0],'pending geodata still mounts at the saved viewport');
 assert.equal(geo.markers.length,0);
 respond({json:async()=>data});
 await new Promise(resolve=>setImmediate(resolve));
 assert.deepEqual(drawTimes,[0,0],'late geodata draws without resetting the viewport');
 assert.equal(geo.markers[0].group[0].id,'far');
 assert.equal(map.getZoom(),18);
 assert.equal(geo.ids.has('near'),true);
 assert.equal(geo.dirty,true);
 console.log('Geo mount: initial fit-before-draw, viewport buffer, pan, selection, saved view, whole boundary and delayed load OK.');
})().catch(error=>{console.error(error);process.exitCode=1;});
