// Map presentation must preserve stored filters, membership and application state.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8'),nodes=new Map();
const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',style:{},dataset:{},addEventListener(){}});return nodes.get(id);};
const points=[],polygons=[],shape=()=>({addTo(){return this;},bindTooltip(){return this;},on(){return this;}});
const c={console,Date,Intl,Math,Number,String,Map,Set,JSON,Array,Object,Promise,setTimeout(){},clearTimeout(){},frontResizeObserver:null,
 L:{polygon:(point,options)=>{polygons.push(options);return shape();},circleMarker:point=>{points.push(point);return shape();}},window:{addEventListener(){}},document:{getElementById:get,querySelector(){return {content:'INVENTED'};},querySelectorAll(){return [];},addEventListener(){}},fetch(){throw Error('Network forbidden');}};
vm.createContext(c);for(const name of ['i18n.js','workspace.js','basemaps.js','overview-map.js'])vm.runInContext(read(name),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);const run=s=>vm.runInContext(s,c);
run(`GeoUI={data:{main_boundary:{points:[]}}};ReportMap={label:()=>({size:0})};MapExport={members:()=>[]};
state={today:'2026-10-16',cards:[{id:'folder',number:'101',name:'Farver <invented>',area_id:'a',kind:'Land',in_folder:true,last_completed:'2026-09-15',addresses:[{count:2}],geo_polygon:[[10,55],[10.01,55],[10.01,55.01]]},{id:'out',number:'102',name:'Kort',area_id:'a',kind:'By',addresses:[],last_completed:'2024-01-01'},{id:'box',number:'103',name:'Genprint',kind:'Ukendt',temporary:true,addresses:[]}],
areas:[{id:'a',name:'Område <invented>'}],publishers:[{id:'p',name:'Forkynder <invented>'}],loans:[{id:'l',card_id:'out',publisher_id:'p',assigned:'2026-09-01',cycle_start:'2026-09-01'}],completions:[{card_id:'folder',date:'2026-09-15'}]};
OverviewMap.map={latLngToLayerPoint:()=>({x:1,y:1}),fitBounds(){},layerPointToLatLng(){}};OverviewMap.layer={clearLayers(){}};`);
// Track only the current layers, as Leaflet does after clearLayers().
c.clearOverviewLayers=()=>{points.length=0;polygons.length=0;};
run('OverviewMap.layer.clearLayers=clearOverviewLayers');
const original=run('JSON.stringify(state)'),contracts={},results={};
for(const language of ['da','en']){
 run(`I18n.set('${language}');OverviewMap.filters.search='';OverviewMap.filters.year=2027;OverviewMap.filters.kind='Alle';OverviewMap.filters.status='Alle';OverviewMap.filters.recentMonths=6;OverviewMap.filters.months=12;OverviewMap.focus='folder'`);
 const page=run('OverviewMap.page()');
 const controls=page.slice(page.indexOf('class="toolbar mapBackground"'),page.indexOf('id="overviewMapBackgroundStatus"'));
 for(const action of ['boundary','fit','focus-fit','unfocus']){assert.match(controls,new RegExp('data-overview="'+action+'"'));assert.equal((page.match(new RegExp('data-overview="'+action+'"','g'))||[]).length,1);}
 assert.match(controls,/data-basemap="overviewMap"/);assert.match(controls,/data-map-expand="overviewMap"/);assert.doesNotMatch(controls,/data-map-fit=/);
 assert(controls.includes(run("I18n.text('Vis hele distriktet')")));
 contracts[language]=(page.match(/(?:data-overview-field|data-overview|value|max)="[^"]*"/g)||[]).join('\n');
 assert.match(page,/option value="Land"/);assert.match(page,/option value="Ingen dato"/);assert.match(page,/Område &lt;invented&gt;/);
 assert.match(page,language==='en'?/>Reset filters<\//:/>Nulstil filtre<\//);
  assert.match(page,/data-overview-field="recentMonths" min="1"/,'Green threshold is editable');
  assert.match(page,/data-overview-field="months" min="2"/,'Red threshold is editable independently');
  assert.match(page,language==='en'?/Green below/:/Grøn under/);
 run('OverviewMap.draw()');assert.match(get('overviewSelected').innerHTML,/<p>Farver &lt;invented&gt;<\/p>/);assert.match(get('overviewSelected').innerHTML,language==='en'?/>Open territory card<\//:/>Åbn distriktskort<\//);assert.match(get('overviewCount').innerHTML,/data-ui-params="\{&quot;matching&quot;:3,&quot;mapped&quot;:1,&quot;missing&quot;:2\}"/);
 results[language]=[];
 for(const [key,value] of [['kind','Land'],['kind','Alle'],['status','Udleverede distriktskort'],['status','Alle'],['completion','Gennemgået'],['completion','Alle'],['ageFilter','Ingen dato'],['ageFilter','Alle'],['publisher','p'],['publisher',''],['recentMonths',3],['months',6]]){run(`OverviewMap.change(${JSON.stringify(key)},${JSON.stringify(value)})`);results[language].push(JSON.parse(run('JSON.stringify(OverviewMap.filtered().map(c=>c.id))')));}
 assert.equal(run('OverviewMap.filters.recentMonths'),3);assert.equal(run('OverviewMap.filters.months'),6);
  assert.match(run('OverviewMap.legend()[0][0]'),language==='en'?/Under 3 months/:/Under 3 måneder/);
  assert.match(run('OverviewMap.legend()[1][0]'),language==='en'?/3–6 months/:/3–6 måneder/);
 run("OverviewMap.filters.color='year';OverviewMap.draw()");assert.match(get('overviewLegend').innerHTML,language==='en'?/Completed in 2026\/2027/:/Gennemgået i 2026\/2027/);run("OverviewMap.filters.color='age'");
 assert.equal(run('JSON.stringify(state)'),original);
}
// Whole-territory view clears temporary focus, not filters or stored territory data.
run(`OverviewMap.map.fitBounds=(points)=>{OverviewMap.testBounds=points};GeoUI.data.main_boundary={points:[[9,54],[11,56],[11,54]]};OverviewMap.focus='folder';OverviewMap.filters.kind='Land';`);
const viewFilters=run('JSON.stringify(OverviewMap.filters)');
run("OverviewMap.handle('focus-fit')");assert.equal(run('JSON.stringify(OverviewMap.testBounds)'),JSON.stringify([[55,10],[55,10.01],[55.01,10.01]]));
run("OverviewMap.handle('fit')");assert.equal(run('OverviewMap.testBounds.length'),3);assert.equal(run('OverviewMap.focus'),'folder');
run("OverviewMap.handle('boundary')");assert.equal(run('JSON.stringify(OverviewMap.testBounds)'),JSON.stringify([[54,9],[56,11],[54,11]]));assert.equal(run('OverviewMap.focus'),'');
assert.equal(run('JSON.stringify(OverviewMap.filters)'),viewFilters);assert.equal(run('JSON.stringify(state)'),original);
run(`state.cards[1].geo_polygon=[[10.02,55],[10.03,55],[10.03,55.01]];
state.cards[2].geo_polygon=[[10.5,55.5],[10.6,55.5],[10.6,55.6]];
OverviewMap.filters.kind='Alle';OverviewMap.change('area','a');OverviewMap.change('color','age');
MapExport.members=()=>[{road:'Fiktiv Vej',number:'1',lng:10.005,lat:55.005,count:2}];OverviewMap.focus='folder';OverviewMap.draw();`);
assert.equal(polygons[0].color,'#173d55');assert.equal(polygons[1].fillOpacity,.08);assert.equal(points.length,2);
const areaFilters=run('JSON.stringify(OverviewMap.filters)'),areaState=run('JSON.stringify(state)');
for(let i=0;i<2;i++){
 run("OverviewMap.handle('boundary')");
 assert.equal(run('OverviewMap.focus'),'');
 assert.equal(run('JSON.stringify(OverviewMap.testBounds)'),JSON.stringify([[54,9],[56,11],[54,11]]));
 assert.equal(points.length,0);assert.equal(polygons.length,3,'Two filtered cards and the main boundary');
 for(const [index,id] of ['folder','out'].entries()){
  assert.equal(polygons[index].color,run("OverviewMap.color(card('"+id+"'))"));
  assert.equal(polygons[index].weight,2);assert.equal(polygons[index].opacity,1);assert.equal(polygons[index].fillOpacity,.25);
 }
 assert.doesNotMatch(get('overviewSelected').innerHTML,/Farver &lt;invented&gt;/);
 assert.equal(run('JSON.stringify(OverviewMap.filters)'),areaFilters);assert.equal(run('JSON.stringify(state)'),areaState);
}
// Without a main boundary, fit all mapped cards, including those hidden by the area filter.
run("GeoUI.data.main_boundary={points:[]};OverviewMap.focus='folder';OverviewMap.handle('boundary')");
assert.equal(run('OverviewMap.focus'),'');assert.equal(run('OverviewMap.testBounds.length'),9);
assert.equal(run('JSON.stringify(OverviewMap.testBounds.at(-1))'),JSON.stringify([55.6,10.6]));
assert.equal(polygons.length,2);assert.equal(points.length,0);assert.equal(run('JSON.stringify(OverviewMap.filters)'),areaFilters);assert.equal(run('JSON.stringify(state)'),areaState);
run("delete state.cards[1].geo_polygon;delete state.cards[2].geo_polygon;OverviewMap.filters.area='';MapExport.members=()=>[]");
assert.equal(run('JSON.stringify(state)'),original);
// Colour bands and the advanced age filter share the upper threshold, not a fixed 2:1 ratio.
run("I18n.set('da');OverviewMap.filters.color='age';OverviewMap.change('recentMonths',4);OverviewMap.change('months',10)");
assert.equal(run("OverviewMap.color({last_completed:'2026-09-20'})"),'#258454');
assert.equal(run("OverviewMap.color({last_completed:'2026-05-10'})"),'#d49a25');
assert.equal(run("OverviewMap.color({last_completed:'2025-12-01'})"),'#bd4a43');
assert.equal(run("OverviewMap.color({last_completed:null})"),'#8b79ac');
assert.match(run('OverviewMap.legend()[1][0]'),/4–10 måneder/);
run("OverviewMap.change('recentMonths',12)");
assert.equal(run('OverviewMap.filters.months'),13,'Raising green threshold moves red threshold forward');
run("OverviewMap.change('months',5)");
assert.equal(run('OverviewMap.filters.recentMonths'),4,'Lowering red threshold moves green back');
run("OverviewMap.change('months',0);OverviewMap.change('recentMonths','invalid')");
assert.equal(run('OverviewMap.filters.months'),5);assert.equal(run('OverviewMap.filters.recentMonths'),4,'Invalid values cannot corrupt thresholds');
run("OverviewMap.change('color','status')");assert.equal(get('overviewIntervals').hidden,true);
run("OverviewMap.change('color','age')");assert.equal(get('overviewIntervals').hidden,false);
assert.deepEqual(contracts.en,contracts.da);assert.deepEqual(results.en,results.da);assert.deepEqual(results.en[0],['folder']);assert.deepEqual(results.en[2],['out']);assert.deepEqual(results.en[4],['folder']);assert.deepEqual(results.en[6],['box']);
run(`MapExport={members:()=>[{road:'Fiktiv Vej',number:'1',lng:10.005,lat:55.005,count:2},{road:'Fiktiv Vej',number:'1',lng:10.015,lat:55.015,count:1}]};OverviewMap.focus='folder';`);points.length=0;run('OverviewMap.draw()');assert.equal(points.length,3,'Overview map shows one red visit dot for each visit, including separate coordinates for the same house number');
console.log('Map overview language preserves filter identifiers/results, numeric intervals, user text, counts, legend and read-only state.');
