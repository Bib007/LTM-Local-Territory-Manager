'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const lines=createInterface({input:child.stdout}),timer=setTimeout(()=>reject(Error('Fixture timed out')),15000);lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});child.once('exit',code=>reject(Error('Fixture exited '+code)));});
  const engine=process.env.LTM_BROWSER_ENGINE==='webkit'?webkit:chromium;
  browser=await engine.launch({...((engine===chromium)?{args:['--no-sandbox']}:{}),...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const errors=[];let watched;
  process.on('unhandledRejection',e=>console.error(e));
  async function newPage(width){const context=await browser.newContext({viewport:{width,height:900}});await context.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,fixture.origin,'Only the temporary local server is contacted');return route.continue();});const page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));return page;}
  async function ready(page){await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');}
  async function login(page,name,password){await page.goto(fixture.origin);await page.locator('#loginName').fill(name);await page.locator('#loginPassword').fill(password);await page.locator('#loginForm button').click();await ready(page);const intro=page.locator('[data-profile=welcome-done]');if(await intro.count())await intro.click();}
  const admin=await newPage(1440);watched=admin;await admin.goto(fixture.origin);await ready(admin);
  await admin.locator('[data-navigation="2:2"]').click();await admin.locator('[data-profile=activate]').click();
  await admin.locator('#profileActivate input[name=name]').fill('Fiktiv admin');await admin.locator('#profileActivate input[name=password]').fill('Fiktiv-password-123');await admin.locator('#profileActivate input[name=repeat]').fill('Fiktiv-password-123');await admin.locator('#profileActivate input[name=confirmation]').fill('AKTIVÉR PROFILER');await admin.locator('#profileActivate button').click();
  await admin.locator('#loginName').waitFor();await login(admin,'Fiktiv admin','Fiktiv-password-123');
  await admin.locator('#nav [data-profile=admin]').click();await admin.locator('#profileRole input[name=name]').fill('Kortredaktør');
  for(const right of ['cards.view','cards.edit','geo.view','notes.view','notes.edit','presence.view'])await admin.locator(`#profilePermissions input[value="${right}"]`).check();
  await admin.locator('#profileRole button').click();await admin.waitForFunction(()=>[...(document.querySelector('#profileRole select')?.options||[])].some(o=>o.text==='Kortredaktør'));
  const role=await admin.locator('#profileRole select option').filter({hasText:'Kortredaktør'}).getAttribute('value');
  await admin.locator('#profileUser input[name=name]').fill('Fiktiv redaktør');await admin.locator('#profileUser input[name=password]').fill('Fiktiv-password-456');await admin.locator(`#profileRoles input[value="${role}"]`).check();await admin.locator('#profileUser button').click();
  await admin.waitForFunction(()=>[...(document.querySelector('#profileUser select')?.options||[])].some(o=>o.text==='Fiktiv redaktør'));
  const editor=await newPage(390);await login(editor,'Fiktiv redaktør','Fiktiv-password-456');assert.equal(await editor.locator('#nav [data-profile=admin]').count(),0);
  // Open two real forms from the same observed card, then autosave different
  // fields. Production state, HTTP authorization and SQLite are all used.
  for(const p of [admin,editor]){if(p.viewportSize().width<800)await p.locator('.mobileMenu').click();await p.locator('[data-navigation="1:0"]').click();await p.locator(`[data-action=detail][data-id="${fixture.card}"]`).first().click();await p.locator(`[data-action=edit-card][data-id="${fixture.card}"]`).first().click();}
  await admin.locator('#cardForm input[name=name]').fill('Fiktiv rettelse A');await admin.waitForFunction(()=>state.cards[0].name==='Fiktiv rettelse A'&&SaveStatus.kind==='saved');
  await editor.locator('#cardForm select[name=kind]').selectOption('By');await editor.waitForFunction(()=>state.cards[0].kind==='By'&&SaveStatus.kind==='saved');
  assert.equal(await editor.evaluate(()=>state.cards[0].name),'Fiktiv rettelse A');assert.equal(await editor.evaluate(()=>state.profile.conflicts),0);
  // The editor's still-open form retains its honest observed base, rather
  // than silently adopting an external name that has not been shown there.
  await editor.locator('#cardForm input[name=name]').fill('Fiktiv rettelse B');await editor.waitForFunction(()=>state.cards[0].name==='Fiktiv rettelse B'&&SaveStatus.kind==='saved');
  assert.equal(await editor.evaluate(()=>state.profile.conflicts),1);
  await editor.locator('#cardForm [data-action=close]').click();await editor.locator('.mobileMenu').click();await editor.locator('#nav [data-navigation="0:0"]').click();await editor.locator('[data-profile=conflicts]').click();
  await editor.locator('.profileConflict').waitFor();assert.ok((await editor.locator('.profileConflict').innerText()).includes('Fiktiv rettelse A'));assert.ok((await editor.locator('.profileConflict').innerText()).includes('Fiktiv rettelse B'));
  assert.ok(await editor.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await editor.screenshot({path:process.env.LTM_PROFILE_SCREENSHOT||'/tmp/ltm-profiles-app-mobile.png',fullPage:true});
  await editor.locator('[data-profile=acknowledge]').click();await editor.waitForFunction(()=>!document.querySelector('.profileConflict'));
  await editor.locator('.dialogClose').click();
  let dropped=false;
  await editor.route('**/api/mutate',async route=>{if(!dropped&&route.request().postDataJSON().action==='note.save'){dropped=true;await route.fetch();await route.abort('failed');}else await route.continue();});
  await editor.evaluate(async()=>{try{await mutate('note.save',{text:'Fiktiv afbrudt kvittering'});}catch{}});
  assert.equal(await editor.evaluate(()=>WriteGuard.uncertain),true);
  await editor.evaluate(async()=>{try{await mutate('note.save',{text:'Må ikke sendes igen'});}catch{}});
  await editor.locator('[data-work=refresh]').click();
  await editor.waitForFunction(()=>!WriteGuard.uncertain);
  assert.equal(await editor.evaluate(()=>state.notes.filter(n=>n.text==='Fiktiv afbrudt kvittering').length),1);
  assert.equal(await editor.evaluate(()=>state.notes.some(n=>n.text==='Må ikke sendes igen')),false);
  await editor.locator('.mobileMenu').click();await editor.locator('[data-action=logout]').click();await editor.locator('#loginName').waitFor();assert.deepEqual(errors,[]);
  console.log('Normal app: activation, login, custom role/user, two independent sessions, merged autosaves, preserved conflict, review, unknown save result, logout, and 390 px layout passed.');
 }catch(e){for(const context of browser?.contexts()||[])for(const p of context.pages()){console.error('Browser state:',await p.locator('body').innerText());await p.screenshot({path:'/tmp/ltm-profiles-failure-'+(await p.viewportSize()).width+'.png',fullPage:true});}throw e;}finally{if(browser)await browser.close();child.kill('SIGTERM');await new Promise(resolve=>child.once('exit',resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;});
