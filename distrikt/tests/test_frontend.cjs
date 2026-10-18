// Pure rendering and planning tests; no browser or user data is contacted.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
let src=fs.readFileSync(path.join(__dirname,'../app/app.js'),'utf8');src=src.slice(0,src.indexOf("document.addEventListener('input'"));
const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',className:'',style:{},dataset:{},classList:{toggle(){}},addEventListener(){},removeEventListener(){},setAttribute(){},showModal(){},close(){},querySelector(){return null}});return nodes.get(id);};
const context={console,Date,Intl,Map,Set,Number,String,Math,JSON,Array,Object,setTimeout,clearTimeout,location:{origin:'http://127.0.0.1:9999'},document:{addEventListener(){},querySelector:()=>({content:'TEST'}),getElementById:get},window:{addEventListener(){},removeEventListener(){}},fetch:()=>{throw Error('Network forbidden in test');}};vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/publisher-search.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/i18n.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/road-search.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/map-export.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/address-source-ui.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/geo.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/printing.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/admin.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/district-map.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/main-boundary.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/s13-template.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/report-map.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/report-print.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/basemaps.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/navigation.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/ib-ui.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/transfer-ui.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/share-ui.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/overview-map.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/workspace.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/setup-ui.js'),'utf8'),context);vm.runInContext(src,context);const run=s=>vm.runInContext(s,context);
run(`state={cards:[],areas:[],publishers:[],loans:[],completions:[],ib:[],visits:[],maps:[],recovery:[],settings:{folder_minimum:30,rural_mode:'manual',rural_minimum:5,require_revision:false,congregation:''},today:'2026-10-06',version:'1.2.0'}`);
for(const p of ['Udlevering','Distrikter','Udleverede distriktskort','Forkyndere','Rapporter','Adresser','Kortopsætning','Indstillinger']){run(`page='${p}';render()`);assert(get('app').innerHTML.length>150,p);}
run(`for(let i=0;i<40;i++)state.cards.push({id:'c'+i,number:String(i),temporary:true,kind:i<8?'Land':'By',in_folder:false,last_completed:i===0?null:'2026-01-01',addresses:[]});`);
assert.equal(run('folderPlan().picked.length'),30);assert.equal(run("folderPlan().picked.filter(c=>c.kind==='Land').length"),5);assert.equal(run('folderPlan().need'),30);
run("state.settings.rural_mode='auto'");assert.equal(run('folderPlan().rural'),6);
run("state.loans.push({id:'l',card_id:'c0',publisher_id:'p',assigned:'2026-01-01',cycle_start:'2026-01-01',returned:null})");assert(!run("folderPlan().picked.some(c=>c.id==='c0')"));
run("state.completions.push({id:'e',card_id:'c1',date:'2026-09-14'});state.visits.push({id:'v',date:'2026-09-21'});year=2027");assert.equal(run('eventsInYear().length'),1);assert(run("reports().includes('Sidste besøg')"));assert(run("reports().includes('2026/2027')"));
run("mapImage='data:image/png;base64,AA==';state.cards[1].polygon=[[1,1],[40,1],[40,30]]");assert(run("mapSvg(new Set(['c1'])).includes('#52aa82')"));
assert.equal(run("fourMonths('2026-10-31')"),'2027-02-28');assert.equal(run("serviceYear('2026-08-31')"),2026);assert.equal(run("serviceYear('2026-09-01')"),2027);
assert(run("esc('<img onerror=alert(1)>').includes('&lt;')"));assert(!run("table(state.cards).includes('onclick=')"));
assert(run("reports().includes('s13-background.jpg')"));assert(run("s13Appendix().includes('Register over distriktstildelinger')"));
run("state.publishers=[{id:'p',name:'Testperson'}];state.completions=[];state.loans=[{id:'l',card_id:'c1',publisher_id:'p',assigned:'2026-07-01',cycle_start:'2026-07-01',returned:'2026-10-01'}];state.completions=[{id:'e',card_id:'c1',loan_id:'l',assigned:'2026-07-01',date:'2026-10-01',previous_completed:'2025-05-01'}];year=2026");
assert.equal(run("allocationRows().find(r=>r.number==='1').allocations[0].completed"),null);assert.equal(run("allocationRows().find(r=>r.number==='1').previous"),'2025-05-01');
assert.equal(run('AdminUI.bytes(1024)'),'1.0 KiB');
run("AdminUI.quick()");assert(get('dialog').innerHTML.includes('adminQuick'));assert(get('dialog').innerHTML.includes('Kontrollér numre'));
run("AdminUI.selected.add('c1');AdminUI.bulk()");assert(get('dialog').innerHTML.includes('adminBulk'));assert(get('dialog').innerHTML.includes('Behold nuværende'));
assert(run("territories().includes('data-bulk-id')"));assert(!run("table(state.cards).includes('data-bulk-id')"));
run("AdminUI.correct('l')");assert(get('dialog').innerHTML.includes('adminLoan'));assert(get('dialog').innerHTML.includes('Vis rettelse'));
run("loanTab='Historik'");assert(run(`loans().includes('data-admin="correct"')`));run("loanTab='Aktive'");assert(run("settingsPage().includes('Pladsforbrug')"));
console.log('Frontend planning/rendering and administration tests passed.');
run(`state.publishers=[{id:'p1',name:'Eksempelperson'},{id:'p2',name:'Testperson 2'}];state.loans=[{id:'l1',card_id:'c1',publisher_id:'p1',assigned:'2026-01-01',cycle_start:'2026-01-01',returned:null},{id:'l2',card_id:'c2',publisher_id:'p1',assigned:'2026-01-02',cycle_start:'2026-01-02',returned:null}];query='';page='Forkyndere';render();`);
assert(get('app').innerHTML.includes('2 kort'));assert(get('app').innerHTML.includes('Tilføj forkynder'));
run("publisherProfile('p1')");assert(get('dialog').innerHTML.includes('2 udleverede distriktskort'));
run("detail('c1')");assert(get('dialog').innerHTML.includes('Print forside'));assert(get('dialog').innerHTML.includes('Tegn og vælg adresser'));
assert(!run("frontHTML(state.cards[1]).includes('0 besøg')"));
run(`GeoUI.data={addresses:[{id:'a1',road:'Eksempelvej',number:'1',postcode:'9999',floor:'',door:'',lng:10,lat:55,count:1,type:'Hus',label:'Eksempelvej 1'},{id:'a2',road:'Eksempelvej',number:'1',postcode:'9999',floor:'1',door:'tv',lng:10,lat:55,count:1,type:'Lejlighed',label:'Eksempelvej 1, 1. tv'}],roads:[],buildings:[],info:{addresses:2}};GeoUI.target='c3';GeoUI.ids=new Set();GeoUI.loaded=true;state.ignored=[];`);
run("GeoUI.toggleHouse(GeoUI.groups()[0])");assert.equal(run('GeoUI.ids.size'),2);assert(get('geoSelection').innerHTML.includes('2 adresser valgt'));
run("GeoUI.toggleHouse(GeoUI.groups()[0])");assert.equal(run('GeoUI.ids.size'),0);
assert(run("GeoUI.pointInside([10,55],[[9.99,54.99],[10.02,54.99],[10.02,55.02],[9.99,55.02]])"));
run("state.cards[3].geo_polygon=[[9.99,54.99],[10.02,54.99],[10.02,55.02],[9.99,55.02]]");assert(run("GeoUI.reportMap(new Set(['c3']),state.cards).includes('#52aa82')"));
console.log('Geographic selection, publisher profiles and front-print rendering tests passed.');
// New public-road search, classification, time labels, and export privacy.
assert.equal(run("RoadSearch.normalize('Gammel Fiktivvej')"),run("RoadSearch.normalize('Gl. Fiktivvej')"));
assert.equal(run("RoadSearch.local('gammel', '9999').length"),0);
run(`GeoUI.data.addresses.push({id:'miss',road:'Gl. Fiktivvej',number:'3',postcode:'9999',floor:'',door:'',lng:10.001,lat:55.001,count:1,type:'Hus',label:'Gl. Fiktivvej 3'});GeoUI.data.status={a1:{card_id:'c3',card_number:'3'},a2:{card_id:'c3',card_number:'3'},miss:{within:[{card_id:'c3',card_number:'3'}]}};`);
assert.equal(run("RoadSearch.local('gammel fiktivvej', '9999')[0].road"),'Gl. Fiktivvej');
assert.equal(run('missingAddresses().length'),1);
run("query='';addressTab='Mangler på kort';addressPostcode='';addressPage=0;");assert(run("addressesPage().includes('Tilføj til kort')"));assert(run("addressesPage().includes('Se bort fra')"));
run("addressTab='Inden for kortgrænse'");assert(run("addressesPage().includes('Grænse for kort 3')"));
run("addressTab='IB'");assert(run("addressesPage().includes('Tilføj IB')"));
run("addressTab='Genprint'");assert(run("addressesPage().includes('Kort til genprint')"));
assert.equal(run("elapsedSince('2026-01-31','2026-02-28')"),'1 måned og 0 dage siden');
assert.equal(run("elapsedSince('2025-09-06','2026-10-06')"),'13 måneder og 0 dage siden');
assert.equal(run("elapsedSince(null)"),'Ingen dato registreret');
assert(run("home().includes('Længst tid siden gennemgang')"));assert.equal(run("position(state.cards[1])"),'Udleverede distriktskort');
run(`state.cards[3].geo_addresses=GeoUI.data.addresses.slice(0,2);state.ib=[{card_id:'c3',road:'PRIVATE_IB_SENTINEL',number:'PRIVATE_NR'}];state.publishers.push({id:'private',name:'PRIVATE_PERSON_SENTINEL'});state.loans.push({card_id:'c3',publisher_id:'private',assigned:'PRIVATE_HISTORY_SENTINEL'});`);
const svg=run("MapExport.svg('c3')");assert(svg.includes('width="2200"'));assert(svg.includes('2 besøg'));assert.equal((svg.match(/<circle /g)||[]).length,2);assert(!svg.includes('PRIVATE_'));assert(!svg.includes('Gl. Fiktivvej 3'));
run("savedLabelAddresses=state.cards[3].geo_addresses;state.cards[3].geo_addresses=[{id:'label-test',road:'Testvej',number:'42B',postcode:'9999',lng:10,lat:55,count:1}]");
const labelSvg=run("MapExport.svg('c3')");assert(labelSvg.includes('>42B</text>'));assert(!labelSvg.includes('1 · 42B'));assert(!labelSvg.includes('pkt.'));assert.equal((labelSvg.match(/<circle /g)||[]).length,1);
run("state.cards[3].geo_addresses=savedLabelAddresses");
assert.equal(run("compactAddressNumbers('1k,3f,5h,7j')"),'1k-7j');assert.equal(run("compactAddressNumbers('12B,2A,4')"),'2A-12B');assert.equal(run("compactAddressNumbers('1–5 (ulige)')"),'1-5 (ulige)');
assert(run("frontHTML({...state.cards[3],addresses:[{road:'Testvej',numbers:'1k,3f,5h,7j',count:4}]}).includes('1k-7j')"));
run("detail('c3')");assert(get('dialog').innerHTML.includes('districtMapRoad'));assert(get('dialog').innerHTML.includes('Geografisk kort'));assert(!get('dialog').innerHTML.includes('PRIVATE_IB_SENTINEL'));
run("state.ignored=[{address_id:'a1'}]");assert.equal(run("MapExport.members('c3').length"),1);const filteredSvg=run("MapExport.svg('c3')");assert.equal((filteredSvg.match(/<circle /g)||[]).length,1);assert(filteredSvg.includes('1 besøg'));assert(run("DistrictMap.html('c3').includes('1 besøg')"));
run("state.ignored=[];state.cards[3].savedPolygon=state.cards[3].geo_polygon;state.cards[3].geo_polygon=[]");assert(run("MapExport.svg('c3').includes('2 besøg')"));run("state.cards[3].geo_polygon=state.cards[3].savedPolygon");
run(`testMarkers=[];testMapRemoved=false;L={map:()=>({fitBounds(){},remove(){testMapRemoved=true;}}),layerGroup:()=>({addTo(){return this;},clearLayers(){testMarkers=[];}}),polyline:()=>({addTo(){return this;},bindTooltip(){return this;}}),polygon:()=>({addTo(){return this;}}),circleMarker:(point)=>({addTo(){testMarkers.push(point);return this;},bindTooltip(){return this;}})};state.ignored=[{address_id:'a1'}];DistrictMap.mount('c3');`);
assert.equal(run('testMarkers.length'),1);assert.equal(get('districtMapCount').textContent,'1 besøg');
run("DistrictMap.road='Vej uden besøg';DistrictMap.draw()");assert.equal(run('testMarkers.length'),0);
run("DistrictMap.dispose();delete L;state.ignored=[]");assert.equal(run('testMapRemoved'),true);
console.log('Compact address text and shared navigation/export filtering tests passed.');
run("state.cards[3].addresses=[{road:'Eksempelvej',numbers:'1',count:2,type:'Hus'}];state.ib=[{card_id:'c3',road:'Eksempelvej',number:'1, 1. tv'}]");assert.equal(run("MapExport.members('c3').length"),1);assert.equal(run("visitsCount(state.cards[3])"),2);assert.equal((run("MapExport.svg('c3')").match(/<circle /g)||[]).length,1);
run("state.ib=[{card_id:'c3',road:'Eksempelvej',number:'1'}]");assert.equal(run("MapExport.members('c3').length"),0);assert(run("DistrictMap.html('c3').includes('Ingen besøg')"));
run("state.ib=[{card_id:'c3',road:'PRIVATE_IB_SENTINEL',number:'PRIVATE_NR'}];GeoUI.dirty=false;GeoUI.data.main_boundary={points:[[9.99,54.99],[10.01,54.99],[10.01,55.01],[9.99,55.01]]};MainBoundaryUI.open()");
assert.equal(run('GeoUI.whole'),true);assert.equal(run('GeoUI.polygon.length'),4);assert(get('app').innerHTML.includes('5.000'));run('MainBoundaryUI.panel()');assert(get('geoSelection').innerHTML.includes('data-main="prune"'));
run("GeoUI.polygon[0][0]=9.98");assert.equal(run('GeoUI.data.main_boundary.points[0][0]'),9.99);
run("GeoUI.dirty=false;GeoUI.openCard('c3')");assert.equal(run('GeoUI.whole'),false);
assert(run("GeoUI.page().includes('geoRangeRoad')"));run("GeoUI.dataDialog()");assert(get('dialog').innerHTML.includes('Hent hele postnummeret'));assert(get('dialog').innerHTML.includes('geoDownloadRoad'));
assert(!run("settingsPage().includes('Ingen database er pakket')"));assert(!run("legacyMapSetup().includes('kommer i en senere version')"));
console.log('Postcode/search/address-list/time-label/export-privacy tests passed.');
if(process.env.DISTRIKT_EXPORT_TEST_SVG)fs.writeFileSync(process.env.DISTRIKT_EXPORT_TEST_SVG,svg);
// Desk work, calendar-day correctness and printable profiles.
assert.equal(run("dayDiff('2026-03-29','2026-03-28')"),1);
assert.equal(run("elapsedSince('2026-09-14','2026-10-06')"),'0 måneder og 22 dage siden');
assert.equal(run("elapsedSince('2026-08-14','2026-10-06')"),'1 måned og 22 dage siden');
run("query='';deskTab='Aflever';");assert(run("home().includes('Aflever til kassen')"));assert(run("deskReturns().includes('Eksempelperson')"));
run("query='nonexistent-person'");assert(!run("deskReturns().includes('data-action=\"return\"')"));
run("query='';detail('c3')");assert(!get('dialog').innerHTML.includes('PRIVATE_IB_SENTINEL'));assert(get('dialog').innerHTML.includes('cardDisplay'));
run("detail('c3','IB-bagside')");assert(get('dialog').innerHTML.includes('PRIVATE_IB_SENTINEL'));
run("state.cards[1].temporary=true;printOptions('c1','front')");assert(get('dialog').innerHTML.includes('printForm'));assert(get('dialog').innerHTML.includes('Husk disse indstillinger'));
run("state.settings.print_profiles={front:{orientation:'landscape',paper:'a4',mode:'full',width:145,height:93,x:2,y:-1}};printOptions('c1','front')");assert(get('dialog').innerHTML.includes('value="145"'));assert(get('dialog').innerHTML.includes('din gemte printprofil'));
const printHTML=run("printDocument([state.cards[1],state.cards[2]],'front',defaultPrintProfile('front'))");
assert.equal((printHTML.match(/class="sheet"/g)||[]).length,2);assert(printHTML.includes('146mm 94mm'));assert(!printHTML.includes('PRIVATE_'));
assert(run("printDocument([state.cards[1]],'back',defaultPrintProfile('back')).includes('94mm 146mm')"));
assert.throws(()=>run("printSettings({...defaultPrintProfile('front'),x:'0; color:red'})"));
run("state.cards[1].front_revision=true;printRevisions('front')");assert(get('dialog').innerHTML.includes('data-ids='));
run("issue('c4',true)");assert(get('dialog').innerHTML.includes('data-publisher-search'));assert(!get('dialog').innerHTML.includes('name="new_publisher"'));
run("deskTab='Udlever';page='Udlevering';render()");assert(!get('app').innerHTML.includes('id="serviceYear"'));assert(get('nav').innerHTML.includes('Daglig brug'));
console.log('Desk, day-count, print-profile, batch-print and local person-search tests passed.');
run("editCard('c3')");assert(get('dialog').innerHTML.includes('Vejlisten følger de valgte huse'));assert(get('dialog').innerHTML.includes('<fieldset disabled>'));
run("GeoUI.map=null;GeoUI.dataDialog()");assert(get('dialog').innerHTML.includes('Åbn kortet, og vælg et udsnit først'));
assert.throws(()=>run('GeoUI.boundsForDownload()'),/Kortopsætning/);

run("GeoUI.data.info.postcodes=[{postcode:'9999',name:'Testby',snapshot:'2026-08-01T00:00:00Z',roads:[{status:'done',road:'Eksempelvej'}]}]");
assert(run("GeoUI.postcodeList().includes('mindst 30 dage gamle')"));assert(run("GeoUI.postcodeList().includes('Opdater postnummer')"));
(async()=>{
 run("originalApi=api;adminWrites=[];originalAdminMutate=mutate;mutate=async(action,data)=>{adminWrites.push({action,data});};api=async()=>({json:async()=>({result:{count:2,numbers:['1','2'],duplicates:[]}})})");
 try{
  await run("AdminUI.preview('card.bulk.preview',{numbers:'1 2',kind:'By',area_id:''})");assert.equal(run('adminWrites.length'),0);assert(get('dialog').innerHTML.includes('Bekræft og gem'));
  await run('AdminUI.confirm()');assert.equal(run("adminWrites[0].action"),'card.bulk.create');
  run("api=async()=>({json:async()=>({result:{count:2,numbers:['1','1'],duplicates:['1']}})})");
  await run("AdminUI.preview('card.bulk.preview',{numbers:'1 1'})");assert(get('dialog').innerHTML.includes('data-admin="confirm" disabled'));assert.equal(run('adminWrites.length'),1);
  run("api=async()=>({json:async()=>({result:{changes:[{number:'1',before:{kind:'By'},after:{kind:'Land'}}],selected:1,expected:'fingerprint'}})})");
  await run("AdminUI.preview('card.bulk.edit.preview',{ids:['c1'],kind:'Land'})");await run('AdminUI.confirm()');assert.equal(run("adminWrites[1].data.expected"),'fingerprint');
 }finally{run('api=originalApi;mutate=originalAdminMutate');}
 console.log('Administrative preview/confirmation tests passed.');
 run("GeoUI.whole=true;GeoUI.polygon=[[10,55],[10.01,55],[10.01,55.01],[10,55.01]];GeoUI.draftLayer=null;GeoUI.dirty=false;el('mainCorner').value='1'");
 await run("MainBoundaryUI.handle('midpoint')");assert.equal(run('GeoUI.polygon.length'),5);assert.equal(run('GeoUI.dirty'),true);assert.equal(run('GeoUI.polygon[1][0]'),10.004999999999999);
 await run("MainBoundaryUI.handle('remove')");assert.equal(run('GeoUI.polygon.length'),4);
 await run("MainBoundaryUI.handle('undo')");assert.equal(run('GeoUI.polygon.length'),3);
 run("GeoUI.dirty=false;api=async()=>({json:async()=>({result:{count:1,roads:[{road:'Fiktiv vej',count:1}],protected:[{label:'Fiktiv vej 1',reason:'Kort 120'}],expected:'boundary-fingerprint'}})});mutate=async(action,data)=>{boundaryWrite={action,data};}");
 try{await run('MainBoundaryUI.preview()');assert(get('dialog').innerHTML.includes('Kort 120'));assert.equal(run("typeof boundaryWrite"),'undefined');await run("MainBoundaryUI.handle('confirm')");assert.equal(run("boundaryWrite.action"),'geo.main.prune');assert.equal(run("boundaryWrite.data.expected"),'boundary-fingerprint');}
 finally{run("api=originalApi;mutate=originalAdminMutate;GeoUI.whole=false;GeoUI.dirty=false");}
 console.log('Main boundary editing and cleanup confirmation tests passed.');
 run("GeoUI.ids=new Set(['miss']);GeoUI.dirty=false");
 await run("GeoUI.handle('ignore','miss')");assert.equal(run("GeoUI.ids.has('miss')"),true);assert.equal(run('GeoUI.dirty'),false);
 run("closeDialog();originalMutate=mutate;mutate=async()=>{throw Error('Fiktiv skrivefejl');}");
 try{await assert.rejects(run("GeoUI.confirmIgnore('miss','Fiktiv begrundelse')"));assert.equal(run("GeoUI.ids.has('miss')"),true);assert.equal(run('GeoUI.dirty'),false);}
 finally{run("mutate=originalMutate");}
 run("mutate=async()=>{}");
 try{await run("GeoUI.confirmIgnore('miss','Fiktiv begrundelse')");assert.equal(run("GeoUI.ids.has('miss')"),false);assert.equal(run('GeoUI.dirty'),true);}
 finally{run("mutate=originalMutate;GeoUI.dirty=false");}
 run("GeoUI.originalDownload=GeoUI.download;GeoUI.download=async (kind,data)=>{GeoUI.testDownload={kind,data};}");
 try{await run("GeoUI.handle('refresh-postcode','9999')");assert.equal(run("GeoUI.testDownload.data.postcode"),'9999');assert.equal(run("GeoUI.testDownload.data.refresh"),true);}
 finally{run("GeoUI.download=GeoUI.originalDownload");}
 console.log('Postcode refresh handler test passed.');
 run("state.recovery=[{batch:'test-batch',label:'Testkort',count:1,at:'2026-10-06T12:00:00Z'}]");assert(run("settingsPage().includes('Slet permanent')"));
 const report=run('reportPrintDocument()');assert(report.includes('s13-background.jpg'));assert(report.includes('margin:15mm'));assert(report.includes('color-scheme:light'));assert(report.includes('<small>Besøg</small>'));assert(!report.includes('Planlagte besøg'));assert(!report.includes('s13Print'));assert.equal(run('reportTab'),'Rapport');
 run("page='Kortopsætning';GeoUI.whole=true;GeoUI.dirty=false;GeoUI.map=null;api=async()=>({json:async()=>({result:{points:[[10,55],[10.01,55],[10.01,55.01],[10,55.01]]}})});mutate=async()=>{throw Error('Preview must not save');}");
 try{await run("MainBoundaryUI.importContent('{}','Testimport')");assert.equal(run('GeoUI.dirty'),true);assert.equal(run('GeoUI.polygon.length'),4);assert(get('app').innerHTML.includes('endnu ikke ændret'));await assert.rejects(run("MainBoundaryUI.handle('download')"),/Gem grænsen/);}
 finally{run("api=originalApi;mutate=originalAdminMutate;GeoUI.dirty=false;GeoUI.whole=false");}
 run("GeoUI.whole=true;GeoUI.download=async(kind,data)=>{GeoUI.testDownload={kind,data};}");
 try{await run("MainBoundaryUI.handle('refresh')");assert.equal(run('GeoUI.testDownload.kind'),'boundary');assert.equal(run('GeoUI.testDownload.data.refresh'),true);}
 finally{run("GeoUI.download=GeoUI.originalDownload;GeoUI.whole=false");}
 console.log('Boundary import review, download guards, original S-13 report and permanent-deletion controls passed.');
 // Navigation preserves draft cancellation and targets the expected list/filter.
 run("GeoUI.dirty=false;page='Udlevering';el('dialog').open=false");
 await run("Navigation.go('1:0')");assert.equal(run('page'),'Distrikter');assert.equal(run('status'),'Alle');assert.equal(run('Navigation.title()'),'Distriktskort');
 await run("Navigation.go('2:0')");assert.equal(run('page'),'Rapporter');assert.equal(run('reportTab'),'Rapport');
 await run("Navigation.go('2:0')");assert.equal(run('reportTab'),'Rapport');
 run("page='Kortopsætning';GeoUI.dirty=true;window.confirm=()=>false");await run("Navigation.go('1:0')");assert.equal(run('page'),'Kortopsætning');assert.equal(run('GeoUI.dirty'),true);
 run("window.confirm=()=>true;GeoUI.dirty=false;page='Distrikter';status='Alle';render()");
 assert(!get('nav').innerHTML.includes('<details'));assert(get('nav').innerHTML.includes('Forside'));assert(get('nav').innerHTML.includes('Idéer og feedback'));assert(get('nav').innerHTML.includes('issues/new?template=idea.yml'));assert(get('nav').innerHTML.includes('rel="noopener noreferrer"'));assert(get('nav').innerHTML.includes('Distriktskort'));assert(!get('nav').innerHTML.includes('Printprofiler'));assert(run("table(state.cards).includes('tabindex=\"0\"')"));
 run("rowEvent={type:'click',preventDefault(){this.prevented=true;}};rowTarget={closest(selector){return selector==='[data-card-row]'?{dataset:{cardRow:'c4'}}:null;}};Navigation.selectRow(rowTarget,rowEvent)");assert.equal(run('selected'),'c4');assert.equal(run('rowEvent.prevented'),true);
 run("rowEvent.prevented=false;buttonTarget={closest(){return {}}};Navigation.selectRow(buttonTarget,rowEvent)");assert.equal(run('rowEvent.prevented'),false);
 // The header logo uses the same guarded home navigation as the sidebar.
 const shell=fs.readFileSync(path.join(__dirname,'../app/index.html'),'utf8');assert(/<button class="brand" data-navigation="0:0"/.test(shell));
 run("page='Kortopsætning';GeoUI.dirty=true;window.confirm=()=>false");await run("Navigation.go('0:0')");assert.equal(run('page'),'Kortopsætning');
 run("window.confirm=()=>true;state.notes=[]");await run("Navigation.go('0:0')");assert.equal(run('page'),'Forside');
 // An ordinary local mount cannot cause a tile request; road mode preserves zoom.
 run("MapBackground.mode='local';tileCalls=[];fitCalls=0;L={tileLayer:(url,options)=>{tileCalls.push({url,options});return {on(){return this;},addTo(){return this;}}}};fakeMap={removeLayer(){}};MapBackground.attach('testMap',fakeMap,()=>{},()=>{fitCalls++})");assert.equal(run('tileCalls.length'),0);
 await run("MapBackground.change('testMap','road')");assert.equal(run('tileCalls.length'),1);assert.equal(run('fitCalls'),0);assert(run("tileCalls[0].url.startsWith('https://tile.openstreetmap.org/')"));assert(!run("tileCalls[0].url.includes('TEST')"));
 await run("MapBackground.change('testMap','satellite')");assert.equal(run('MapBackground.mode'),'road');assert.equal(run('tileCalls.length'),1);assert(!run("MapBackground.toolbar('testMap').includes('data-map-key')"));assert(!run("MapBackground.toolbar('testMap').includes('value=\"hybrid\"')"));
 run("MapBackground.detach('testMap');MapBackground.mode='local';delete L;api=originalApi");
 assert(run("MainBoundaryUI.page().includes('data-main=\"import\"')"));
 console.log('Grouped navigation, draft protection, whole-row selection and explicit online-map choice passed.');
 // Card-specific corner insertion, including the closing edge, leaves the main boundary alone.
 run("mainBefore=JSON.stringify(GeoUI.data.main_boundary);GeoUI.whole=false;GeoUI.draftLayer=null;GeoUI.polygon=[[10,55],[10.02,55],[10.02,55.02],[10,55.02]];GeoUI.map={latLngToLayerPoint(p){return {x:p[1],y:p[0]};}};GeoUI.insertCorner([10.01,55]);");
 assert.equal(run('GeoUI.polygon.length'),5);assert.equal(run('GeoUI.polygon[1][0]'),10.01);assert.equal(run('GeoUI.dirty'),true);
 run("GeoUI.insertCorner([10,55.01])");assert.equal(run('GeoUI.polygon.length'),6);assert.equal(run('GeoUI.polygon[5][1]'),55.01);assert.equal(run('JSON.stringify(GeoUI.data.main_boundary)'),run('mainBefore'));
 run("GeoUI.polygon=Array.from({length:5000},(_,i)=>[10+i*.000001,55]);");assert.throws(()=>run("GeoUI.insertCorner([10,55])"),/5000/);run("GeoUI.map=null;GeoUI.dirty=false");
 assert(run("GeoUI.page().includes('Indsæt hjørne på kanten')"));
 // Local IB suggestions only contain this card's precise units; no neighborhood search.
 run("state.ib=[];editIB('','c3')");assert(get('dialog').innerHTML.includes('ibLocalRoads'));assert(get('dialog').innerHTML.includes('ibAddressPick'));assert(!get('dialog').innerHTML.includes('Gl. Fiktivvej'));assert(!get('dialog').innerHTML.includes('data-road-search'));
 assert.equal(run("IBUI.addresses('c3').length"),2);assert(run("IBUI.list('c3').includes('Markér IB')"));
 run("ibTestForm={elements:{card_id:{value:'c3'},road:{value:'Eksempelvej'},number:{value:'1'},address_id:{value:''}}};IBUI.matchFields(ibTestForm)");assert.equal(run('ibTestForm.elements.address_id.value'),'');
 run("IBUI.pick(ibTestForm,'a1')");assert.equal(run('ibTestForm.elements.address_id.value'),'a1');
 run("ibTestForm.elements.number.value='1, 1 tv';IBUI.matchFields(ibTestForm)");assert.equal(run('ibTestForm.elements.address_id.value'),'a2');
 run("state.ib=[{id:'exact',card_id:'c3',address_id:'a2',road:'Eksempelvej',number:'1, 1 tv',date:state.today}]");assert.equal(run("IBUI.find(IBUI.addresses('c3')[0],'c3')"),undefined);assert.equal(run("IBUI.find(IBUI.addresses('c3')[1],'c3').id"),'exact');assert.equal(run("MapExport.members('c3').length"),1);
 run("detail('c3','Adresser')");assert(get('dialog').innerHTML.includes('Rediger IB'));assert(get('dialog').innerHTML.includes('1, 1 tv'));
 // Screenshot export reuses displayed tiles. Coverage checks reject holes/failed tiles.
 assert(run("MapExport.coversViewport([{x:0,y:0,width:50,height:100},{x:50,y:0,width:50,height:100}],100,100)"));
 assert(!run("MapExport.coversViewport([{x:0,y:0,width:40,height:100},{x:50,y:0,width:50,height:100}],100,100)"));
 assert(!run("MapExport.coversViewport([{x:0,y:0,width:100,height:90}],100,100)"));
 run("originalCreateElement=document.createElement;drawnTiles=[];document.createElement=()=>({getContext:()=>({drawImage(...a){drawnTiles.push(a);}}),toDataURL:()=> 'data:image/png;base64,AAAA'});tileImage={complete:true,naturalWidth:256,getBoundingClientRect:()=>({left:10,top:20,width:100,height:100})};fakeContainer={getBoundingClientRect:()=>({left:10,top:20}),querySelectorAll:()=>[tileImage]};captureMap={getContainer:()=>fakeContainer,getSize:()=>({x:100,y:100}),getBounds:()=>({getWest:()=>9.99,getSouth:()=>54.99,getEast:()=>10.02,getNorth:()=>55.02})};DistrictMap.map=captureMap;DistrictMap.id='c3';MapBackground.mode='road';MapBackground.instances.set('districtMap',{map:captureMap,layer:{isLoading:()=>false}});snapshot=MapExport.osmSnapshot('c3')");
 assert.equal(run('drawnTiles.length'),1);assert.equal(run('snapshot.viewBounds[0]'),9.99);
 const osmSvg=run("MapExport.svg('c3',snapshot)");assert(osmSvg.includes('<image href="data:image/png'));assert(osmSvg.includes('openstreetmap.org/copyright'));assert(!osmSvg.includes('PRIVATE_'));assert.equal((osmSvg.match(/<circle /g)||[]).length,1);
 run("tileImage.complete=false");assert.throws(()=>run("MapExport.osmSnapshot('c3')"),/indlæst/);
 run("tileImage.complete=true;MapBackground.mode='local'");assert.throws(()=>run("MapExport.osmSnapshot('c3')"),/Vejkort/);
 // Export automatically fits all roads and crops excess viewport around the complete boundary.
 run("originalExportPoints=MapExport.exportPoints;MapExport.exportPoints=()=>[[10,55],[10.01,55.01]];originalDistrictDraw=DistrictMap.draw;DistrictMap.draw=()=>{};DistrictMap.road='Eksempelvej';fitArgs=null;captureMap.fitBounds=(bounds,options)=>{fitArgs={bounds,options};};captureMap.latLngToContainerPoint=p=>({x:30+(p[1]-10)*4000,y:70-(p[0]-55)*4000});captureMap.containerPointToLatLng=p=>({lng:10+(p[0]-30)/4000,lat:55+(70-p[1])/4000});MapBackground.mode='road'");
 await run("MapExport.prepareOSM('c3')");assert.equal(run('DistrictMap.road'),'');assert.equal(run('fitArgs.bounds.length'),2);assert.equal(run('fitArgs.options.animate'),false);
 const crop=JSON.parse(run("JSON.stringify(MapExport.tightCrop('c3',captureMap,{x:100,y:100}))"));assert(crop.width>=80&&crop.width<=82);assert(crop.height>=80&&crop.height<=82);assert(crop.x<30&&crop.y<30);
 run("tightSnapshot=MapExport.osmSnapshot('c3',{tight:true})");assert(run('tightSnapshot.viewBounds[0] < 10'));assert(run('tightSnapshot.viewBounds[2] > 10.01'));assert.equal(run('drawnTiles.length'),2);
 run("MapExport.exportPoints=()=>[[11,56]]");assert.throws(()=>run("MapExport.tightCrop('c3',captureMap,{x:100,y:100})"),/ikke synligt/);
 run("MapExport.exportPoints=originalExportPoints;DistrictMap.draw=originalDistrictDraw");
 run("DistrictMap.map=null;MapBackground.detach('districtMap');document.createElement=originalCreateElement;state.ib=[]");
 // Return notes are local reminders, safely rendered and excluded from public exports.
 run("state.notes=[{id:'note-test',card_id:'c3',date:state.today,created:'2026-01-01',text:'PRIVATE_NOTE <script>bad</script>',resolved:false}];detail('c3','Noter')");
 assert(get('dialog').innerHTML.includes('Opgaver · 1'));assert(get('dialog').innerHTML.includes('&lt;script&gt;'));assert(!get('dialog').innerHTML.includes('<script>bad'));
 assert(!run("MapExport.svg('c3').includes('PRIVATE_NOTE')"));assert(run("notesList().includes('Markér udført')"));
 run("state.loans.push({id:'note-loan',card_id:'c3',publisher_id:'p1',cycle_start:'2026-01-01'});finish('note-loan')");assert(get('dialog').innerHTML.includes('name="note"'));assert(get('dialog').innerHTML.includes('Tilføj IB')||get('dialog').innerHTML.includes('tilføj IB'));
 assert(run("printDocument([card('c3')],'front',{paper:'cut',mode:'data',width:146,height:94,x:0,y:0}).includes('top:calc(17% - 1mm)')"));
 // Report labels fit polygon area/width and OSM snapshot is embedded in print without private notes.
 assert(run("ReportMap.label([[0,0],[100,0],[100,100],[0,100]],'120').size")<=13);
 assert(run("ReportMap.label([[0,0],[30,0],[30,30],[0,30]],'120').size")<run("ReportMap.label([[0,0],[100,0],[100,100],[0,100]],'120').size"));
 assert.equal(run("ReportMap.label([[0,0],[2,0],[2,100],[0,100]],'120').size"),11);
 run("savedReportCards=state.cards;savedReportCompletions=state.completions;savedReportYear=year;state.cards=[{id:'report-test',number:'120',geo_polygon:[[10,55],[10.015,55],[10.015,55.015],[10,55.015]]}];state.completions=[{card_id:'report-test',date:state.today}];year=serviceYear(state.today);ReportMap.map=captureMap;ReportMap.tiles={isLoading:()=>false};document.createElement=()=>({getContext:()=>({drawImage(){}}),toDataURL:()=> 'data:image/png;base64,AAAA'})");
 run("savedMainBoundary=GeoUI.data.main_boundary;GeoUI.data.main_boundary={points:[[9.995,54.995],[10.019,54.995],[10.019,55.019],[9.995,55.019]]};ReportMap.fit()");
 assert.equal(run('fitArgs.bounds.length'),8);assert.equal(run('fitArgs.bounds[0][1]'),9.995);
 assert.equal(run("cardColor({map_color:'#cc33aa'})"),'#cc33aa');assert.equal(run("cardColor({map_color:'red'})"),'#477596');
 assert(run("GeoUI.page().includes('id=\"geoColor\"')"));
 const css=fs.readFileSync(path.join(__dirname,'../app/style.css'),'utf8');assert(!css.includes('.report svg{'));assert(css.includes('svg.leaflet-attribution-flag{display:inline;width:1em;height:.6667em'));
 const reportSnapshot=await run('ReportMap.printable()');assert(reportSnapshot.includes('data:image/png;base64,AAAA'));assert(reportSnapshot.includes('#52aa82'));assert(reportSnapshot.includes('stroke="#b83b35"'));assert(reportSnapshot.includes('stroke-dasharray="8 5"'));assert(reportSnapshot.includes('samlet distriktsgrænse'));assert(reportSnapshot.includes('openstreetmap.org/copyright'));assert(!reportSnapshot.includes('PRIVATE_NOTE'));
 context.reportSnapshotFixture=reportSnapshot;const reportWithMap=run('reportPrintDocument(reportSnapshotFixture)');assert(reportWithMap.includes('data:image/png;base64,AAAA'));assert(!reportWithMap.includes('id="reportDistrictMap"'));assert(reportWithMap.includes('s13-background.jpg'));assert(!reportWithMap.includes('PRIVATE_NOTE'));
 run("GeoUI.data.main_boundary=savedMainBoundary;ReportMap.map=null;ReportMap.tiles=null;document.createElement=originalCreateElement;state.cards=savedReportCards;state.completions=savedReportCompletions;year=savedReportYear");
 run("L={map(node,options){reportOptions=options;return {attributionControl:{setPrefix(value){reportAttributionPrefix=value;}},remove(){},on(){},fitBounds(){}};},tileLayer(){return {addTo(){return this;},on(){return this;}};},layerGroup(){return {addTo(){return this;}};}};savedReportDraw=ReportMap.draw;ReportMap.draw=()=>{};savedReportCards=state.cards;state.cards=[{id:'test',geo_polygon:[[10,55],[11,55],[11,56]]}];ReportMap.mount()");
 assert.equal(run('reportAttributionPrefix'),'Leaflet');
 for(const option of ['zoomControl','scrollWheelZoom','doubleClickZoom','touchZoom','boxZoom','keyboard','dragging'])assert.equal(run('reportOptions.'+option),false,option);
 run("ReportMap.dispose();ReportMap.draw=savedReportDraw;state.cards=savedReportCards;delete L");

 // Public renderer takes only the server-provided recipe, never private local notes or extra units.
 run("publicRecipe={publicCard:{id:'c3',number:'PUBLIC120',name:'Offentligt navn & <test>',geo_polygon:[[10,55],[10.02,55],[10.02,55.02]],map_color:'#123abc'},publicMembers:[{id:'public-one',road:'Offentlig testvej',number:'42',lng:10.005,lat:55.005,count:1}]}");
 const publicSvg=run("MapExport.svg('c3',{...publicRecipe,publicTemplate:'data:image/png;base64,AAAA'})");assert(publicSvg.includes('PUBLIC120'));assert(publicSvg.includes('Offentligt navn &amp; &lt;test&gt;'));assert(publicSvg.includes('Husk at tjekke efter IB på det fysiske distriktskort'));assert(publicSvg.includes('fill="#b3261e"')); assert(publicSvg.includes('Offentlig testvej'));assert(publicSvg.includes('42'));assert(!publicSvg.includes('PRIVATE_'));assert(!publicSvg.includes('Eksempelvej'));assert.equal((publicSvg.match(/<circle /g)||[]).length,1);
 assert(run("TransferUI.html().includes('backupImport')"));assert(run("ShareUI.html().includes('Deling og QR')"));assert(run("Navigation.groups[2][1].some(item=>item[1]==='Indstillinger')"));
 run("ShareUI.data={connected:true,account:'fake@example.invalid',cards:[{card_id:'c3',number:'120',error:'<script>',status:'queued'}]}");
 assert(run("ShareUI.content().includes('Venter på upload')"));assert(run("ShareUI.content().includes('&lt;script&gt;')"));assert(!run("ShareUI.content().includes('<script>')"));
 assert(!run("reportPrintDocument().includes('Områder og resterende kort')"));assert(!run("reportPrintDocument().includes('Endnu ikke registreret gennemgået · næste gennemgang først')"));assert(!run("reportPrintDocument().includes('Planlagte besøg')"));assert(run("reportDetails().includes('<small>Besøg</small>')"));

 run("state.public_maps=[]");assert(!run("frontHTML(card('c3')).includes('data-card-qr')"));
 run("state.public_maps=[{card_id:'c3',url:'https://drive.google.com/file/d/TEST_QR/view'}]");
 const qrFront=run("frontHTML(card('c3'))");assert(qrFront.includes('Scan for at se et kort over distriktet'));assert(qrFront.includes('/card-qr.svg?card_id=c3'));assert(!qrFront.includes('PRIVATE_'));assert(!run("backHTML(card('c3')).includes('data-card-qr')"));
 for(const mode of ['full','data']){
  context.qrPrintMode=mode;
  const html=run("printDocument([card('c3')],'front',{paper:'cut',mode:qrPrintMode,width:146,height:94,x:0,y:0})");
  assert(html.includes('data-card-qr'));assert(html.includes('right:2%;bottom:19%;width:14%'));assert(html.includes('Scan for at se et kort over distriktet'));assert(!html.includes('.cardQR img{visibility:hidden'));
 }
 run("openDialog('<h2>Test</h2>')");assert(get('dialog').innerHTML.includes('class="dialogClose"'));assert(get('dialog').innerHTML.includes('aria-label="Luk"'));assert(get('dialog').innerHTML.includes('data-action="close"'));
 run("state.public_maps=[]");

 run("overviewSavedState=state;state={...state,today:'2026-10-14',cards:[{id:'ov-new',number:'1',kind:'By',area_id:'a',in_folder:true,last_completed:'2026-10-01',addresses:[],geo_polygon:[[10,55],[10.01,55],[10.01,55.01]]},{id:'ov-old',number:'2',kind:'Land',area_id:'b',last_completed:'2024-01-01',addresses:[]},{id:'ov-none',number:'3',kind:'By',area_id:'a',last_completed:null,addresses:[]}],loans:[{id:'ol',card_id:'ov-old',publisher_id:'p1',returned:null}],completions:[{card_id:'ov-new',date:'2026-10-01'}]};OverviewMap.filters={status:'Alle',area:'',kind:'Alle',completion:'Alle',ageFilter:'Alle',after:'',before:'',publisher:'',revision:'Alle',color:'age',months:12,year:2027,search:''}");
 assert.equal(run('OverviewMap.filtered().length'),3);assert.equal(run("OverviewMap.color(card('ov-new'))"),'#258454');assert.equal(run("OverviewMap.color(card('ov-old'))"),'#bd4a43');assert.equal(run("OverviewMap.color(card('ov-none'))"),'#8b79ac');
 run("OverviewMap.filters.status='Kort i mappen'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-new');
 run("OverviewMap.filters.status='Udleverede distriktskort'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-old');
 run("OverviewMap.filters.status='Alle';OverviewMap.filters.completion='Gennemgået'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-new');
 run("OverviewMap.filters.completion='Alle';OverviewMap.filters.ageFilter='Ingen dato'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-none');
 run("OverviewMap.filters.ageFilter='Mindst intervallet'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-old');
 run("OverviewMap.filters.ageFilter='Alle';OverviewMap.filters.after='2026-01-01'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-new');
 run("OverviewMap.filters.after='';OverviewMap.filters.publisher='p1'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-old');
 run("OverviewMap.filters.publisher='';OverviewMap.filters.kind='Land'");assert.equal(run('OverviewMap.filtered()[0].id'),'ov-old');
 assert(run("table(state.cards).includes('Se på kort')"));assert(run("OverviewMap.page().includes('Tid siden gennemgang')"));assert(run("Navigation.groups[1][1].some(v=>v[1]==='Kortoversigt')"));
 run("state=overviewSavedState;OverviewMap.filters={status:'Alle',area:'',kind:'Alle',completion:'Alle',ageFilter:'Alle',after:'',before:'',publisher:'',revision:'Alle',color:'age',months:12,year:0,search:''}");
 console.log('Overview status/area/type/age/year/assignee filters, date limits and quick-map links passed.');
 console.log('Front QR in full/preprinted modes, private back separation and accessible close control passed.');
 console.log('Public-only map recipe, escaped sharing UI and transfer controls passed.');
 console.log('Report OSM print snapshot, adaptive labels and privacy passed.');
 console.log('Automatic PNG fitting/crop, front baseline spacing and local return-note UI passed.');
 console.log('Card corner insertion, local IB unit selection and OSM screenshot coverage/privacy passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});

// Hidden one-time setup, escaped user labels and explicit confirmations.
setImmediate(()=>{
 run("SetupUI.options={numbering:'prefix',start:101,block:100,target:50};SetupUI.areas=[{id:'',name:'<test>',prefix:'F',kind:'By'}];SetupUI.ibDate='2026-10-15'");
 assert(run("SetupUI.advanced().includes('Kortinddeling og nummerering')"));
 assert(!run("Navigation.html().includes('Opsæt distrikter')"));
 assert(run("SetupUI.areasPage().includes('&lt;test&gt;')"));
 assert(run(`SetupUI.areasPage().includes('value="101"')`));
 run("SetupUI.plan={cards:[{key:'0',number:'F101',name:'<test>',area_name:'Fiktiv by',kind:'By',address_ids:['x'],visits:1,polygon:[]}],excluded:{},visits:1,uncovered:0}");
 assert(run("SetupUI.planPage().includes('OPRET KORT')"));
 assert(run("SetupUI.planPage().includes('&lt;test&gt;')"));
 run("SetupUI.ib={new:1,existing:0,errors:0,rows:[{line:2,status:'new',label:'<test>',card_number:'F101',date:'2026-10-15'}]}");
 assert(run("SetupUI.ibPage().includes('IMPORTÉR IB')"));assert(!run("SetupUI.ibPage().includes('<test>')"));
 console.log('Hidden setup, number standards, escaped previews and typed creation/IB confirmations passed.');
});

// Closed maps keep a printable QR; pending Google requests must never look closed.
{
 const snapshot=run('JSON.stringify(state)');
 run("state.cards=[{id:'shared-test',number:'120',name:'Fiktivt kort',geo_polygon:[[10,55],[10.1,55],[10.1,55.1]]}];ShareUI.data={connected:true,account:'fictional@example.invalid',cards:[{card_id:'shared-test',status:'ready',front_url:'https://drive.google.com/file/d/FICTIONAL/view',url:'',issued:false,access_pending:false}]}");
 let content=run('ShareUI.content()');assert(content.includes('QR-kode'));assert(!content.includes('Åbn preview'));assert(content.includes('Lukket · kortet er ikke udleveret'));
 run("ShareUI.data.cards[0]={...ShareUI.data.cards[0],status:'access_retry',url:ShareUI.data.cards[0].front_url,access_pending:true,error:'SIMULATED <failure>'}");
 content=run('ShareUI.content()');assert(content.includes('Afventer lukning hos Google'));assert(content.includes('billedet kan stadig være offentligt'));assert(content.includes('Prøv adgangsændring igen'));assert(content.includes('SIMULATED &lt;failure&gt;'));assert(!content.includes('Åbn preview'));assert(!content.includes('Lukket · kortet er ikke udleveret'));
 run("ShareUI.data.cards[0].status='access_failed'");assert(run('ShareUI.content()').includes('Adgangsændring stoppet'));
 context.shareStateSnapshot=snapshot;run('state=JSON.parse(shareStateSnapshot);ShareUI.data=null');
 console.log('Loan-driven sharing: closed/pending/failed access labels, stable QR and escaped errors passed.');
}
