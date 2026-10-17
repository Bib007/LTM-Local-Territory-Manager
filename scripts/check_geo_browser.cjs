// Offline Chromium verification. Install Playwright as a development tool, never in the app.
// PLAYWRIGHT_MODULE=/path/to/playwright node scripts/check_geo_browser.cjs
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'../distrikt/app'),out=process.env.LTM_BROWSER_OUTPUT;
const points=[[10,55],[10.01,55],[10.01,55.01],[10,55.01]];
const state={revision:'fictional-r1',today:'2026-10-17',version:'fictional',cards:[{id:'c1',number:'101',area_id:'a',kind:'By',name:'Vejnavn <fictional>',address_ids:['a1'],geo_polygon:points,addresses:[{road:'Vejnavn',from:'1',count:1,type:'Hus'}],temporary:false,map_color:'#477596'}],areas:[{id:'a',name:'Vejnavn <fictional>'}],publishers:[],loans:[],completions:[],ib:[],ignored:[],notes:[],tasks:[],visits:[],recovery:[],maps:[],settings:{congregation:'Fiktiv menighed',folder_minimum:30,rural_mode:'manual',rural_minimum:5,onboarding:{completed:true}}};
const geo={addresses:[{id:'a1',road:'Vejnavn',number:'1',postcode:'9999',label:'Vejnavn 1',type:'Hus',count:1,lng:10.002,lat:55.002},{id:'a2',road:'Vejnavn',number:'2',postcode:'9999',label:'Vejnavn 2',type:'Hus',count:1,lng:10.004,lat:55.004}],buildings:[],roads:[],info:{addresses:2,buildings:0,roads:0},status:{a1:{card_id:'c1',card_number:'101'}},main_boundary:{points}};
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=','base64');
(async()=>{
 const browser=await chromium.launch({args:['--no-sandbox']});try{
 for(const width of [320,390,768,1440]){
  const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[],writes=[];page.on('pageerror',e=>errors.push(e.message));page.on('dialog',dialog=>dialog.accept());
  await context.route('**/*',async route=>{const u=new URL(route.request().url());if(u.hostname==='tile.openstreetmap.org')return route.fulfill({contentType:'image/png',body:png});assert.equal(u.hostname,'ltm.test','No external requests');
   const json=data=>route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
   if(u.pathname==='/api/state')return json(state);if(u.pathname==='/api/geo')return json(geo);if(u.pathname==='/api/map')return json({image:''});if(u.pathname==='/api/geo/job')return json({status:'idle'});
   if(u.pathname==='/api/geo/suggest')return json({suggestions:[]});
   if(u.pathname==='/api/address-source/status')return json({configured:false});
   if(u.pathname==='/api/mutate'){const body=route.request().postDataJSON();writes.push(body);assert.equal(body.action,'geo.main.import.preview');return json({result:{format:'KML',boundaries:[{name:'Vejnavn <fictional>',points},{name:'Other',points:points.map(([x,y])=>[x+.001,y])},{name:'Invalid',error:'Fictional error'}],skipped:1}});}
   const file=path.resolve(root,'.'+(u.pathname==='/'?'/index.html':u.pathname));assert.ok(file.startsWith(root+path.sep));assert.ok(fs.existsSync(file),'Unexpected request '+u.pathname);return route.fulfill({path:file});
  });
  await page.goto('http://ltm.test/');await page.waitForFunction(()=>state!==null&&GeoUI.busy===false);
  await page.evaluate(g=>{GeoUI.loaded=true;GeoUI.data=g;GeoUI.openCard('c1');},geo);
  await page.locator('#geoRangeForm [name=road]').fill('Vejnavn');await page.locator('#geoRangeForm [name=postcode]').fill('9999');await page.locator('#geoRangeForm [name=from]').fill('1');await page.locator('#geoRangeForm [name=to]').fill('8');await page.locator('#geoRangeForm [name=parity]').selectOption('even');
  await page.evaluate(()=>{window.mapBefore=GeoUI.map;window.inputBefore=el('geoRangeRoad');window.polyBefore=JSON.stringify(GeoUI.polygon);window.idsBefore=[...GeoUI.ids].join();GeoUI.mode='move';GeoUI.dirty=true;GeoUI.drawBoundary();GeoUI.updatePanel();el('geoRangeRoad').focus();I18n.set('en');Navigation.localize();});
  assert.ok(await page.evaluate(()=>GeoUI.map===window.mapBefore&&el('geoRangeRoad')===window.inputBefore&&document.activeElement===window.inputBefore&&JSON.stringify(GeoUI.polygon)===window.polyBefore&&[...GeoUI.ids].join()===window.idsBefore&&GeoUI.dirty));
  assert.equal(await page.locator('#geoRangeForm [name=parity]').inputValue(),'even');assert.equal(await page.locator('#geoRangeForm [name=to]').inputValue(),'8');assert.match(await page.locator('#geoSelection').innerText(),/1 addresses selected/);assert.match(await page.locator('#geoModeHint').innerText(),/Drag the orange corners/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal overflow at '+width);assert.ok(await page.locator('#geoTarget').evaluate(n=>n.getBoundingClientRect().right<=innerWidth),'Card selection stays inside viewport');
  if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`editor-${width}.png`),fullPage:true});}
  // Import with real file input, Leaflet map and options. Switching language preserves all three.
  await page.evaluate(()=>BoundaryImportUI.open(false));await page.locator('#boundaryImportFile').setInputFiles({name:'fictional.kml',mimeType:'application/vnd.google-earth.kml+xml',buffer:Buffer.from('<kml/>')});await page.locator('#boundaryImportChoice').waitFor();await page.locator('#boundaryImportChoice').selectOption('1');
  await page.evaluate(()=>{window.importMapBefore=BoundaryImportUI.map;window.fileBefore=el('boundaryImportFile');window.choiceBefore=el('boundaryImportChoice');el('boundaryImportChoice').focus();I18n.set('da');Navigation.localize();});
  assert.ok(await page.evaluate(()=>BoundaryImportUI.map===window.importMapBefore&&el('boundaryImportFile')===window.fileBefore&&el('boundaryImportChoice')===window.choiceBefore&&el('boundaryImportChoice').value==='1'&&el('boundaryImportFile').files.length===1&&document.activeElement===window.choiceBefore));assert.match(await page.locator('#boundaryImportChoice option:checked').innerText(),/4 hjørner/);
  assert.match(await page.locator('#boundaryImportBody').innerText(),/Vejnavn <fictional>/);assert.equal(await page.locator('#boundaryImportBody fictional').count(),0);
  await page.getByRole('button',{name:'Brug grænsen i tegningen'}).click();assert.ok(await page.evaluate(()=>GeoUI.dirty&&!el('dialog').open&&GeoUI.polygon[0][0]===10.001));assert.equal(writes.length,1,'Preview alone never saves');
  // Overall boundary language switch preserves corner input, map, zoom and unsaved geometry.
  await page.evaluate(()=>MainBoundaryUI.open());await page.locator('#mainCorner').fill('3');await page.evaluate(()=>{window.wholeMapBefore=GeoUI.map;window.cornerBefore=el('mainCorner');GeoUI.dirty=true;window.zoomBefore=GeoUI.map.getZoom();I18n.set('en');Navigation.localize();});assert.ok(await page.evaluate(()=>GeoUI.map===window.wholeMapBefore&&el('mainCorner')===window.cornerBefore&&el('mainCorner').value==='3'&&GeoUI.map.getZoom()===window.zoomBefore&&GeoUI.dirty));assert.match(await page.locator('#geoSelection').innerText(),/Save overall boundary/);
  if(out)await page.screenshot({path:path.join(out,`overall-${width}.png`),fullPage:true});
  assert.deepEqual(errors,[]);await context.close();console.log(`Chromium ${width}px: editor/map/focus/input draft, bilingual import/file/choice, escaped data and overall boundary passed.`);
 }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
