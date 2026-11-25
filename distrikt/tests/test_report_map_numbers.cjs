// Invented geography and report sessions only: no user data or internet requests.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const number='F-314',card={id:'fictional-1',number,geo_polygon:[[10.005,55.005],[10.025,55.005],[10.025,55.025],[10.005,55.025]]};
const state={cards:[card],today:'2026-11-17',revision:'fictional-r1',settings:{congregation:'Fiktiv menighed'},completions:[{card_id:card.id,date:'2026-10-01'}],loans:[]};
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,innerHTML:'',textContent:''});return nodes.get(id);};
const drawn={polygons:[],tooltips:[],markers:[],leaders:[]},reset=()=>Object.values(drawn).forEach(list=>list.length=0);
const layer=()=>({addTo(){return this;},bindTooltip(fn){drawn.tooltips.push(fn());return this;}});
const map={getSize:()=>({x:720,y:480}),fitBounds(){},latLngToContainerPoint:p=>({x:(p[1]-10)*7200,y:(p[0]-55)*9000}),containerPointToLatLng:p=>({lng:p[0]/7200+10,lat:p[1]/9000+55})};
const prefs=new Map(),localStorage={getItem:key=>prefs.get(key)??null,setItem:(key,value)=>prefs.set(key,String(value))};
const c={document:{addEventListener(){}},window:{addEventListener(){}},localStorage,console,Date,Math,Number,String,Array,Object,Set,Map,JSON,Promise,
 state,GeoUI:{data:{main_boundary:{points:[[10,55],[10.04,55],[10.04,55.04],[10,55.04]]}}},
 location:{origin:'https://fictional.invalid'},setTimeout:fn=>{fn();return 1;},clearTimeout:()=>{},
 I18n:{language:()=> 'da',text:key=>key,attribute:(kind,value)=>kind+'="'+value+'"'},
 el:node,eventsInYear:()=>[{card_id:card.id}],cardColor:()=> '#477596',
 ui:key=>key,esc:value=>String(value??'').replace(/[&<>"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x])),
 fmt:value=>value||'',yearLabel:()=> '2026/2027',year:2027,page:'Rapporter',
 s13Appendix:()=>'',mapMock:map,
 L:{polygon(points,opts){drawn.polygons.push({points,opts});return layer();},polyline(points){drawn.leaders.push(points);return layer();},marker(at,opts){drawn.markers.push({at,opts});return layer();},divIcon:opts=>opts},
 MapExport:{captureMap:()=>({backgroundImage:'data:image/png;base64,RklDVElPTkFM',viewBounds:[10,55,10.04,55.04]})}};
vm.createContext(c);
for(const file of ['workspace.js','report-map.js','report-print.js'])vm.runInContext(read(file),c);
const run=source=>vm.runInContext(source,c);
run("Workspace.boundaryReport=()=>'';Workspace.reportSummary=()=>'<section class=\"report\"></section>';Workspace.reportTitle=()=> 'Fiktiv periode';Workspace.periodBounds=()=>['2026-09-01','2027-08-31'];Workspace.reportInventory=()=>({total:1,assigned:0,home:1,missing:0,missingAssigned:0,missingHome:0,completedIds:new Set([state.cards[0].id])});Workspace.reportExplanation=()=>'';");
(async()=>{
 const before=JSON.stringify(state),toolbar=run('Workspace.reportPreview=true;Workspace.detailedReports()');
 assert.match(toolbar,/id="reportPrintPeriod"/);
 assert.match(toolbar,/id="reportMapNumbers" type="checkbox" checked/);
 assert.match(toolbar,/id="reportDistrictMap"/);
 assert.equal(prefs.size,0,'The default does not write a browser preference');
 assert.match(read('app.js'),/Workspace\.setReportShowNumbers\(e\.target\.checked\)/,'The checkbox handler must persist changes');
 const restartedPreference=()=>{const fresh={...c};vm.createContext(fresh);vm.runInContext(read('workspace.js'),fresh);return vm.runInContext('Workspace.reportShowNumbers',fresh);};
 run('ReportMap.map=mapMock;ReportMap.layer={clearLayers(){}};ReportMap.tiles={isLoading:()=>false};ReportMap.fit=()=>{};');
 reset();run('ReportMap.draw()');
 assert.equal(drawn.markers.length,1,'Preview should initially show the number marker');
 assert.match(drawn.markers[0].opts.icon.html,/>F-314</);
 assert.match(drawn.tooltips[0],/F-314/);
 const onFallback=await run('ReportMap.printable({withoutBackground:true})');
 const onTiles=await run('ReportMap.printable()');
 for(const html of [onFallback,onTiles]){assert.match(html,/<polygon/);assert.match(html,/F-314/);}
 c.printedMap=onTiles;assert.match(run("reportPrintDocument({service:printedMap},'service')"),/F-314/);
 run('Workspace.setReportShowNumbers(false)');
 assert.equal(prefs.get('ltm-report-map-numbers'),'false');
 assert.equal(restartedPreference(),false,'A disabled switch must stay disabled after restart');
 assert.doesNotMatch(run('Workspace.detailedReports()'),/id="reportMapNumbers" type="checkbox" checked/);
 reset();run('ReportMap.draw()');
 assert.equal(drawn.markers.length,0,'Preview must remove all number markers');
 assert.equal(drawn.leaders.length,0,'Preview must remove number callouts');
 assert(drawn.polygons.length>=2,'District polygons and the outer boundary remain visible');
 assert.doesNotMatch(drawn.tooltips.join(' '),/F-314/,'Hover labels must also respect hiding');
 assert.equal(node('reportMapLabelNotice').hidden,true,'No number overflow notice when numbers are hidden');
 const offFallback=await run('ReportMap.printable({withoutBackground:true})');
 const offTiles=await run('ReportMap.printable()');
 for(const html of [offFallback,offTiles]){assert.match(html,/<polygon/);assert.doesNotMatch(html,/F-314/);}
 assert.match(offTiles,/<image/,'Printed basemap remains when numbers are hidden');
 assert.doesNotMatch(offFallback,/og numre er bevaret/,'Offline explanation follows the switch');
 c.printedMap=offTiles;assert.doesNotMatch(run("reportPrintDocument({service:printedMap},'service')"),/F-314/);
 run('Workspace.setReportShowNumbers(true)');
 assert.equal(prefs.get('ltm-report-map-numbers'),'true');
 assert.equal(restartedPreference(),true,'Re-enabling must survive restart');
 reset();run('ReportMap.draw()');assert.equal(drawn.markers.length,1,'Re-enabling restores number markers');
 assert.equal(JSON.stringify(state),before,'Report preference must not change stored territory data');
 // A changed selection during asynchronous print preparation must invalidate that PDF.
 let releasePrint,popup;
 c.pendingPrint=new Promise(resolve=>{releasePrint=resolve;});
 c.window={open(){popup={closed:false,close(){this.closed=true;},document:{write(){},open(){},close(){}}};return popup;}};
 run('ReportMap.printable=async()=>pendingPrint');
 const job=run('printReport({withoutBackground:true})');
 run('Workspace.setReportShowNumbers(false)');
 releasePrint('<svg>F-314</svg>');
 await assert.rejects(job,/Printgrundlaget er ændret/);
 assert.equal(popup.closed,true,'Stale print popup closes instead of enabling an outdated PDF');
 assert.equal(run('printReport.busy'),false);
 assert.equal(JSON.stringify(state),before);
 c.localStorage.setItem=()=>{throw Error('storage is blocked');};
 run('Workspace.setReportShowNumbers(true)');
 assert.equal(run('Workspace.reportShowNumbers'),true,'Blocked writes must not break the switch');
 c.localStorage.getItem=()=>{throw Error('storage is blocked');};
 assert.equal(restartedPreference(),true,'Blocked reads use the original enabled default');
 console.log('Report map numbers: switch persistence, restart, blocked storage, live map, PDF and stale-print guard passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
