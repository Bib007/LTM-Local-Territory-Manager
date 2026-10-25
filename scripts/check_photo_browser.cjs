// Real authenticated server + security headers, synthetic images and disposable data.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const server=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/photo_server.py')],{stdio:['ignore','pipe','inherit']});
 let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const lines=createInterface({input:server.stdout}),timer=setTimeout(()=>reject(Error('Fixture startup timed out')),15000);lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});server.once('exit',code=>reject(Error('Fixture stopped: '+code)));});
  const engine=process.env.LTM_BROWSER_ENGINE||'chromium';browser=await(engine==='webkit'?webkit:chromium).launch(engine==='webkit'?{}:{args:['--no-sandbox']});
  for(const width of [390,1440]){
   const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[],violations=[],writes=[];let releaseGeo;const firstGeo=new Promise(resolve=>releaseGeo=resolve);let geoRequests=0;
   page.on('pageerror',e=>errors.push(e.message));
   await context.addInitScript(()=>document.addEventListener('securitypolicyviolation',e=>{window.cspViolations??=[];window.cspViolations.push(e.violatedDirective+': '+e.blockedURI);}));
   await context.route('**/*',async route=>{const u=new URL(route.request().url());assert.ok(u.origin===fixture.origin||u.protocol==='blob:','No external image/OCR service: '+u.href);if(u.pathname==='/api/geo'&&geoRequests++===0)await firstGeo;if(u.pathname==='/api/mutate')writes.push(route.request().postDataJSON());return route.continue();});
   await page.goto(fixture.origin);await page.locator('#loginPassword').fill('Fictional-pass-123');await page.locator('#loginForm button').click();
   await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
   await page.evaluate(()=>{openDialog('<label>Fiktiv kladde<input id=fictionalDraft></label>');window.draftNode=document.getElementById('fictionalDraft');});await page.locator('#fictionalDraft').fill('Bevar min kladde');releaseGeo();
   await page.waitForFunction(()=>document.querySelector('.navFollowupCount'));
   assert.ok(await page.locator('#fictionalDraft').evaluate(n=>n===window.draftNode&&n===document.activeElement&&n.value==='Bevar min kladde'),'Background total preserves the open field and focus');
   const initialCount=await page.evaluate(()=>Workspace.followupItems().length);
   assert.equal(await page.locator('.navFollowupCount').innerText(),String(initialCount),'Follow-up total appears before visiting its page');
   await page.evaluate(()=>{closeDialog();page='Indstillinger';Navigation.settingsSection='import';render();});
   await page.locator('[data-photo=open]').click();await page.waitForFunction(()=>document.getElementById('photoFiles')?.disabled===false);
   const png=fs.readFileSync(path.join(__dirname,'fixtures/ocr-fiktiv.png'));
   const jpeg=Buffer.from(await page.evaluate(async bytes=>{const img=new Image();img.src='data:image/png;base64,'+bytes;await img.decode();const c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;c.getContext('2d').drawImage(img,0,0);return c.toDataURL('image/jpeg',.95).split(',')[1];},png.toString('base64')),'base64');
   await page.locator('#photoFiles').setInputFiles(['png','jpg','jpeg'].map(ext=>({name:'fictional.'+ext,mimeType:ext==='png'?'image/png':'image/jpeg',buffer:ext==='png'?png:jpeg})));
   for(let i=0;i<3;i++){
    await page.waitForFunction(()=>!PhotoImportUI.reading,null,{timeout:35000});
    assert.deepEqual(await page.evaluate(()=>window.cspViolations||[]),[],'Production CSP must allow its own local image');
    assert.match(await page.locator('#photoText').inputValue(),/Fiktivvej/);
    assert.equal(await page.locator('#formError').innerText(),'');assert.ok(await page.locator('#photoImage').evaluate(n=>n.naturalWidth>0));
    await page.locator('#photoCard').selectOption(fixture.card);await page.locator('[data-photo=parse]').click();
    assert.ok(await page.locator('.photoRow').count()>=1);assert.equal(await page.locator('[data-photo-field=address]').first().inputValue(),'fictional-a');
    for(const row of await page.locator('.photoRow').all())if(await row.locator('select').inputValue()==='')await row.locator('[data-photo=skip-row]').click();
    await page.locator('[data-photo=preview]').click();await page.locator('#photoConfirm').waitFor();
    assert.equal(writes.filter(w=>w.action==='setup.ib.apply').length,0,'No import without explicit approval');
    await page.locator('[data-photo=skip]').click();if(i<2)await page.locator('[data-photo=next]').click();
   }
   // A separate approved import proves the real CSV preview and confirmed write agree.
   await page.locator('#photoFiles').setInputFiles({name:'approved-fictional.png',mimeType:'image/png',buffer:png});
   await page.waitForFunction(()=>!PhotoImportUI.reading,null,{timeout:35000});await page.locator('#photoCard').selectOption(fixture.card);await page.locator('[data-photo=parse]').click();for(const row of await page.locator('.photoRow').all())if(await row.locator('select').inputValue()==='')await row.locator('[data-photo=skip-row]').click();await page.locator('[data-photo=preview]').click();await page.locator('#photoConfirm').fill('IMPORTÉR IB');await page.locator('[data-photo=apply]').click();
   await page.waitForFunction(()=>PhotoImportUI.index===1&&!PhotoImportUI.applying);
   assert.equal(writes.filter(w=>w.action==='setup.ib.apply').length,1);assert.equal(await page.evaluate(()=>state.ib.length),1);
   assert.equal(await page.locator('.navFollowupCount').innerText(),String(initialCount+1),'Confirmed IB import updates total on the import page');
   // Keep later viewport tests independent while still exercising the real mutation path.
   await page.evaluate(async()=>{await mutate('delete',{module:'ib',id:state.ib[0].id});await mutate('revision.approve',{card_id:state.cards[0].id,side:'back'});});
   violations.push(...await page.evaluate(()=>window.cspViolations||[]));assert.deepEqual(violations,[]);assert.deepEqual(errors,[]);
   await context.close();console.log(`${engine} ${width}px: real login/CSP, PNG/JPG/JPEG decoding, OCR, editable suggestions, explicit import, follow-up total and unchanged open draft passed.`);
  }
 }finally{if(browser)await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
