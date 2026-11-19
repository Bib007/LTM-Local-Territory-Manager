'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/outline_review_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  for(const width of [1440,390]){
   const page=await browser.newPage({viewport:{width,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(()=>localStorage.setItem('ltm-language','da'));
   await page.route('**/*',route=>{if(new URL(route.request().url()).hostname==='tile.openstreetmap.org')return route.abort();assert.equal(new URL(route.request().url()).origin,fixture.origin);return route.continue();});
   await page.goto(fixture.origin);await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
   // Restore the fictional broad neighbour on the second viewport only.
   if(width===390)await page.evaluate(async id=>{const scale=111320*Math.cos(55*Math.PI/180),p=(x,y)=>[Number((10+x/scale).toFixed(7)),Number((55+y/111320).toFixed(7))];await api('/api/mutate',{action:'geo.boundary',data:{card_id:id,polygon:[p(-10,-500),p(10,-500),p(10,500),p(-10,500)]}});await refresh();},fixture.neighbor);
   const before=await page.evaluate(id=>JSON.stringify(card(id)),fixture.neighbor);
   await page.evaluate(async id=>{GeoUI.dirty=false;GeoUI.openCard(id);await GeoUI.load();await GeoUI.selectPreview({address_ids:['1','3'],suggest_outline:true});},fixture.target);
   assert.equal(await page.evaluate(()=>GeoUI.neighborChanges().length),1);
   assert(await page.locator('#geographicEditor path[stroke="#dc9d32"]').count()>0||await page.evaluate(()=>GeoUI.draftLayer.getLayers().some(l=>l.options?.color==='#dc9d32')));
   await page.locator('[data-geo=save]').click();
   await page.locator('#geoNeighborApproval').waitFor();assert.match(await page.locator('#dialog').innerText(),/F002/);
   assert.equal(await page.locator('[data-geo=confirm-save]').isDisabled(),true);
   assert.equal(await page.evaluate(id=>JSON.stringify(card(id)),fixture.neighbor),before,'No neighbour mutation without consent');
   await page.locator('#geoNeighborApproval').check();
   if(process.env.LTM_OUTLINE_SCREENSHOT&&width===1440)await page.screenshot({path:process.env.LTM_OUTLINE_SCREENSHOT});
   await page.locator('[data-geo=confirm-save]').click();
   await page.waitForFunction(()=>SaveStatus.kind==='saved'&&!document.getElementById('dialog').open);
   const after=await page.evaluate(id=>card(id),fixture.neighbor);assert.notEqual(JSON.stringify(after),before);assert.deepEqual(after.address_ids,['2']);
   assert.equal(await page.evaluate(()=>GeoUI.polygon.length>=3),true);assert.deepEqual(errors,[]);await page.close();
  }
  console.log('Fictional desktop/mobile boundary proposal, visible neighbour geometry, required consent and atomic save passed.');
 }finally{if(browser)await browser.close();child.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
