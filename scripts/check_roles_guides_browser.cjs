// Real HTTP, real DOM, only fictional temporary accounts from roles_guides_server.py.
'use strict';
const assert=require('node:assert/strict'),{chromium}=require(process.env.PLAYWRIGHT_MODULE||'/tmp/ltm-profile-browser/node_modules/playwright'),f=JSON.parse(process.env.LTM_ROLES_FIXTURE);
(async()=>{const browser=await chromium.launch({channel:'chrome'});try{
 const errors=[],responses=[];
 async function context(cookie){const c=await browser.newContext({viewport:{width:1100,height:900}});await c.addInitScript(()=>localStorage.setItem('ltm-language','da')); if(cookie)await c.addCookies([cookie]);await c.route('**/*',r=>new URL(r.request().url()).origin===f.url?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>{errors.push(e.message);console.log('PAGEERROR',e.message);});p.on('response',r=>{if(r.url().endsWith('/api/mutate'))responses.push(r.status());});return {c,p};}
 const {c:readerContext,p:r}=await context(f.reader);await r.goto(f.url);await r.locator('.dashboardHero').waitFor();
 assert.equal(await r.locator('#personalGuideTour').count(),0,'No personal or release-news tour at login');assert.equal(await r.evaluate(()=>typeof PersonalGuide),'undefined');
 await r.reload();await r.waitForFunction(()=>state!==null);
 const state=await r.evaluate(()=>({publishers:state.publishers,notes:state.notes,cards:state.cards,summary:state.dashboard_summary}));assert.deepEqual(state.publishers,[]);assert.deepEqual(state.notes,[]);assert.deepEqual(state.cards,[]);assert.equal(state.summary.periods.service.territories,1);
 for(const width of [390,1440]){await r.setViewportSize({width,height:900});assert.equal(await r.locator('.dashboardHero').count(),1,'Summary accounts keep the home layout');assert.equal(await r.locator('.dashboardRing').count(),2);assert.equal(await r.locator('.reportOverview').count(),0,'Home must not render the report');assert.doesNotMatch(await r.locator('#app').innerText(),/Fiktiv privat/);assert.ok(await r.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await r.screenshot({path:f.out+'/restored-home-reader-'+width+'.png',fullPage:true});}
 await r.locator('#navigationLanguage').selectOption('en');assert.match(await r.locator('.dashboardHero').innerText(),/Service year/);await r.locator('#navigationLanguage').selectOption('da');
 await r.evaluate(()=>{page='Rapporter';render();});assert.equal(await r.locator('[data-action=s13]').count(),0);assert.doesNotMatch(await r.locator('#app').innerText(),/Fiktiv privat|IB|besøgsskøn/i);
 assert.equal(await r.locator('[data-profile=print-summary]').count(),1);await r.screenshot({path:f.out+'/summary-reader.png',fullPage:true});
 const {c:adminContext,p:a}=await context(f.admin);await a.goto(f.url);await a.locator('.dashboardRing').first().waitFor();assert.equal(await a.locator('#personalGuideTour').count(),0);for(const width of [390,1440]){await a.setViewportSize({width,height:900});assert.equal(await a.locator('.dashboardRing').count(),2,'Full profile accounts keep the original home rings');assert.equal(await a.locator('.dashboardTrend').count(),1,'Monthly comparison remains on the original home');assert.equal(await a.locator('.dashboardShortcuts button').count(),3);assert.equal(await a.locator('.reportOverview').count(),0);assert.ok(await a.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await a.locator('.dashboardGrid').scrollIntoViewIfNeeded();await a.screenshot({path:f.out+'/restored-home-admin-'+width+'.png',fullPage:false});}await a.evaluate(()=>Onboarding.open(4));await a.locator('[data-onboarding=tour]').click();await a.locator('#ltmTour').waitFor();
 let guard=0;while(!/Afslut rundtur/.test(await a.locator('[data-ltm-tour=next]').innerText())){assert.ok(++guard<8);await a.locator('[data-ltm-tour=next]').click();}await a.locator('[data-ltm-tour=next]').click();await a.waitForFunction(()=>GuidedTour.index===-1);assert.equal(await a.evaluate(()=>state.settings.onboarding.completed),true);assert.deepEqual(responses,[200,200]);
 await a.locator('#nav [data-navigation="2:2"]').click();await a.locator('[data-work=settings-tab][data-value=users]').click();await a.locator('#profileUser').waitFor();assert.match(await a.locator('#profilePermissions').innerText(),/Overblik|Se forsidestatus|Kræver også/);
 await a.locator('#profileUser select[name=entityId]').selectOption(f.reader_id);await a.locator('#profileUser input[name=name]').fill('Fiktiv kladde der skal bevares');
 assert.equal(await a.locator('[data-profile=preview-guide], [data-profile=assign-guide], #profileGuideAssignment').count(),0,'No guide scheduling or preview controls');
 assert.equal(await a.locator('#profileUser input[name=name]').inputValue(),'Fiktiv kladde der skal bevares');
 for(const p of [a,r]){
  assert.equal(await p.locator('#nav [data-personal-guide=replay], #nav [data-profile=admin]').count(),0);
  const guide=p.locator('#nav [data-help-guide]');
  for(const lang of ['da','en']){
   await p.locator('#navigationLanguage').selectOption(lang);
   assert.equal(await guide.getAttribute('href'),'https://localterritorymanager.netlify.app/'+lang+'/guide/');
   assert.match(await guide.innerText(),lang==='da'?/Trinvis LTM-guide/:/Step-by-step LTM guide/);
  }
  await p.locator('#navigationLanguage').selectOption('da');
 }
 const {c:newContext,p:n}=await context();await n.goto(f.url);await n.locator('#loginName').fill('Fiktiv læser');await n.locator('#loginPassword').fill('Fiktiv-password-456');await n.locator('#loginForm button').click();
 await n.locator('.dashboardHero').waitFor();assert.equal(await n.locator('#personalGuideTour').count(),0,'New logins must not show an introductory tour');
 const publicGuide=n.locator('#nav [data-help-guide]');assert.equal(await publicGuide.getAttribute('href'),'https://localterritorymanager.netlify.app/da/guide/');
 assert.deepEqual(errors,[]);console.log('PASS real HTTP/browser: restored full/aggregate home layouts; no personal tour or release news; website guide for both languages and independent login; summary-only permissions; onboarding tour preserved.');await readerContext.close();await adminContext.close();await newContext.close();
 }finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
