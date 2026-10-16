// Map presentation must preserve stored filters, membership and application state.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),nodes=new Map();
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',style:{},dataset:{},addEventListener(){}});return nodes.get(id);};
const shape=()=>({addTo(){return this;},bindTooltip(){return this;},on(){return this;}});
const c={console,Date,Intl,Math,Number,String,Map,Set,JSON,Array,Object,Promise,setTimeout(){},clearTimeout(){},frontResizeObserver:null,
 L:{polygon:shape,circleMarker:shape},window:{addEventListener(){}},document:{getElementById:get,querySelector(){return {content:'INVENTED'};},querySelectorAll(){return [];},addEventListener(){}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','basemaps.js','overview-map.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run(`GeoUI={data:{main_boundary:{points:[]}}};ReportMap={label:()=>({size:0})};MapExport={members:()=>[]};
state={today:'2026-10-16',cards:[{id:'folder',number:'101',name:'Farver <invented>',area_id:'a',kind:'Land',in_folder:true,last_completed:'2026-09-15',addresses:[{count:2}],geo_polygon:[[10,55],[10.01,55],[10.01,55.01]]},{id:'out',number:'102',name:'Kort',area_id:'a',kind:'By',addresses:[],last_completed:'2024-01-01'},{id:'box',number:'103',name:'Genprint',kind:'Ukendt',temporary:true,addresses:[]}],
areas:[{id:'a',name:'Område <invented>'}],publishers:[{id:'p',name:'Forkynder <invented>'}],loans:[{id:'l',card_id:'out',publisher_id:'p',assigned:'2026-09-01',cycle_start:'2026-09-01'}],completions:[{card_id:'folder',date:'2026-09-15'}]};
OverviewMap.map={latLngToLayerPoint:()=>({x:1,y:1}),fitBounds(){},layerPointToLatLng(){}};OverviewMap.layer={clearLayers(){}};`);
const original=run('JSON.stringify(state)'),contracts={},results={};
for(const language of ['da','en']){
 run(`I18n.set('${language}');OverviewMap.filters.search='';OverviewMap.filters.year=2027;OverviewMap.filters.kind='Alle';OverviewMap.filters.status='Alle';OverviewMap.focus='folder'`);
 const page=run('OverviewMap.page()');contracts[language]=(page.match(/(?:data-overview-field|data-overview|value|max)="[^"]*"/g)||[]).join('\n');
 assert.match(page,/option value="Land"/);assert.match(page,/option value="Ingen dato"/);assert.match(page,/Område &lt;invented&gt;/);
 assert.match(page,language==='en'?/>Reset filters<\//:/>Nulstil filtre<\//);
 run('OverviewMap.draw()');assert.match(get('overviewSelected').innerHTML,/<p>Farver &lt;invented&gt;<\/p>/);assert.match(get('overviewSelected').innerHTML,language==='en'?/>Open territory card<\//:/>Åbn distriktskort<\//);assert.match(get('overviewCount').innerHTML,/data-ui-params="\{&quot;matching&quot;:3,&quot;mapped&quot;:1,&quot;missing&quot;:2\}"/);
 results[language]=[];
 for(const [key,value] of [['kind','Land'],['kind','Alle'],['status','Udleverede distriktskort'],['status','Alle'],['completion','Gennemgået'],['completion','Alle'],['ageFilter','Ingen dato'],['ageFilter','Alle'],['publisher','p'],['publisher',''],['months',6]]){run(`OverviewMap.change(${JSON.stringify(key)},${JSON.stringify(value)})`);results[language].push(JSON.parse(run('JSON.stringify(OverviewMap.filtered().map(c=>c.id))')));}
 assert.equal(run('OverviewMap.filters.months'),6);assert.match(run('OverviewMap.legend()[0][0]'),language==='en'?/Under 3 months/:/Under 3 måneder/);
 run("OverviewMap.filters.color='year';OverviewMap.draw()");assert.match(get('overviewLegend').innerHTML,language==='en'?/Completed in 2026\/2027/:/Gennemgået i 2026\/2027/);run("OverviewMap.filters.color='age'");
 assert.equal(run('JSON.stringify(state)'),original);
}
assert.deepEqual(contracts.en,contracts.da);assert.deepEqual(results.en,results.da);assert.deepEqual(results.en[0],['folder']);assert.deepEqual(results.en[2],['out']);assert.deepEqual(results.en[4],['folder']);assert.deepEqual(results.en[6],['box']);
console.log('Map overview language preserves filter identifiers/results, numeric intervals, user text, counts, legend and read-only state.');
