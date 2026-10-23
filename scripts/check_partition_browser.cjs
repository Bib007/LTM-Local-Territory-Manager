// Used by check_visual_browser.cjs; real Python preview, production UI, no services.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
module.exports=async(browser,out)=>{
 const root=path.resolve(__dirname,'../distrikt/app');
 const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=','base64');
 for(const kind of ['road','river','rail']){
 const fixture=JSON.parse(execFileSync(process.env.LTM_TEST_PYTHON||'python3',[path.join(__dirname,'partition_browser_fixture.py'),kind],{encoding:'utf8'}));
 for(const width of [320,390,768,1440]){
  const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[],requests=[];
  page.on('pageerror',error=>errors.push(error.message));
  await context.route('**/*',route=>{const u=new URL(route.request().url());if(u.hostname==='tile.openstreetmap.org')return route.fulfill({contentType:'image/png',body:png});assert.equal(u.hostname,'ltm.partition.test','No real services');const json=data=>route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
   if(u.pathname==='/api/state')return json(fixture.state);
   if(u.pathname==='/api/geo')return json(fixture.geo);
   if(u.pathname==='/api/map')return json({image:''});
   if(u.pathname==='/api/ping')return json({ok:true});
   if(u.pathname==='/api/geo/job')return json({status:'idle'});
   if(u.pathname==='/api/setup/job')return json({status:'done',response:{result:fixture.plan,revision:fixture.state.revision}});
   if(u.pathname==='/api/share/status')return json({connected:false,cards:[]});
   if(u.pathname==='/api/mutate'){const body=route.request().postDataJSON();assert.equal(body.action,'setup.preview','Never create or modify cards in browser fixture');assert.equal(Object.hasOwn(body.data,'_revision'),false);assert.equal(Number(body.data.target),40);assert.equal(body.data.areas[0].name,'Fiktivt prøveområde');assert.equal(body.data._async,true);requests.push(body);return json({result:{job_id:'fictional-preview'},revision:fixture.state.revision});}
   const file=path.resolve(root,'.'+(u.pathname==='/'?'/index.html':u.pathname));assert.ok(file.startsWith(root+path.sep));assert.ok(fs.existsSync(file),'Unexpected asset '+u.pathname);return route.fulfill({path:file});
  });
  await page.goto('http://ltm.partition.test/');await page.waitForFunction(()=>state!==null&&!GeoUI.busy);
  await page.evaluate(()=>{SetupUI.autoDivisionEnabled=true;return SetupUI.open(2);}); // Archived generator fixture only.
  await page.locator('[data-setup-option=target]').fill('40');await page.locator('[data-setup-area-field=name]').fill('Fiktivt prøveområde');
  assert.match(await page.locator('.setupBody').innerText(),/enkle forgreninger/);
  await page.locator('[data-setup=preview]').click();await page.locator('#setupConfirm').waitFor();
  assert.equal(await page.locator('[data-setup-card-row]').count(),2);assert.equal(requests.length,1);
  assert.equal(await page.evaluate(()=>SetupUI.shapes.size),2);
  assert.equal(await page.evaluate(()=>state.cards.length),0);
  const before=await page.evaluate(()=>JSON.stringify(SetupUI.plan));
  for(const language of ['en','da']){
   await page.evaluate(language=>{I18n.set(language);Navigation.localize();},language);
   assert.equal(await page.evaluate(()=>JSON.stringify(SetupUI.plan)),before,'Language switch preserves actual branching polygons');
   if(kind!=='road'){assert.match(await page.locator('.setupCardTable .warning').first().innerText(),language==='en'?(kind==='rail'?/railway/:/waterway/):(kind==='rail'?/jernbanen/:/vandløbet/));assert.equal(await page.locator('.setupCardTable .warning vandløb,.setupCardTable .warning jernbane').count(),0,'Public feature names remain escaped text');}
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Preview fits viewport');
  }
  if(width<600){const cells=await page.locator('.setupCardTable tbody td').evaluateAll(nodes=>nodes.map(n=>({left:n.getBoundingClientRect().left,right:n.getBoundingClientRect().right,width:innerWidth})));assert.ok(cells.every(n=>n.left>=0&&n.right<=n.width+1),'All card review fields fit without horizontal scrolling');}
  await page.locator('[data-setup=edit-boundaries]').click();assert.ok(await page.locator('.setupCorner').count()>4,'Actual bent boundary remains editable');
  assert.equal(await page.locator('[data-setup=apply]').count(),1);assert.equal(await page.locator('#setupConfirm').inputValue(),'');assert.equal(requests.length,1,'Opening editor never applies proposal');
  // Mock tiles are deliberately blank. Draw only the same fictional downloaded
  // road geometry behind the real proposal so the shared curve can be inspected.
  await page.evaluate(()=>{for(const road of GeoUI.data.roads)L.polyline(road.points.map(([x,y])=>[y,x]),{color:'#a6adb1',weight:7,opacity:.65,interactive:false}).addTo(SetupUI.map).bringToBack();});
  const dividerCount=await page.evaluate(()=>{let count=0;SetupUI.map.eachLayer(l=>{if(l.options?.className==='naturalDivider')count++;});return count;});assert.equal(dividerCount,kind==='road'?0:1,'Downloaded natural context is visible in actual editor');
  if(out){await page.screenshot({animations:'disabled',path:path.join(out,`partition-${kind}-${width}.png`),fullPage:true});await page.locator('#setupMap').screenshot({animations:'disabled',path:path.join(out,`partition-map-${kind}-${width}.png`)});}
  assert.deepEqual(errors,[]);await context.close();
 }
 }
 console.log('Actual fictional Python road/waterway/railway previews: 80 addresses, two editable cards, translated and escaped source warnings, four widths, no apply or external services passed.');
};
