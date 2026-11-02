'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const lines=createInterface({input:child.stdout}),timer=setTimeout(()=>reject(Error('Fixture timed out')),15000);lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});child.once('exit',code=>reject(Error('Fixture exited '+code)));});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const out=process.env.LTM_BROWSER_OUTPUT||'/tmp/ltm-street-suggestions';fs.mkdirSync(out,{recursive:true});
  for(const [index,language,width]of [[0,'en',390],[1,'da',1440]]){
   const context=await browser.newContext({viewport:{width,height:1000}});await context.addCookies([fixture.cookie]);await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='tile.openstreetmap.org')return r.abort();assert.equal(u.origin,fixture.origin);return r.continue();});
   const p=await context.newPage(),errors=[],writes=[];p.on('pageerror',e=>errors.push(e.message));p.on('dialog',d=>d.accept());p.on('request',r=>{if(r.url().endsWith('/api/mutate')&&r.method()==='POST')writes.push(r.postDataJSON());});
   await p.goto(fixture.origin);await p.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
   if(await p.locator('[data-profile=welcome-done]').count())await p.locator('[data-profile=welcome-done]').click();
   await p.waitForFunction(()=>PersonalGuide.data!==null);if(await p.locator('[data-personal-guide=later]').count())await p.locator('[data-personal-guide=later]').click();
   await p.evaluate(({id,language})=>{I18n.set(language);closeDialog();GeoUI.openCard(id);},{id:fixture.cards[index],language});
   await p.waitForSelector('[data-geo=street-lines]');const before=await p.evaluate(id=>JSON.stringify(card(id)),fixture.cards[index]);writes.length=0;
   await p.locator('[data-geo=street-lines]').click();await p.locator('[name=postcode_0]').fill('9999');
   await p.locator('#streetSuggestionForm button:not([type=button])').click();
   await p.waitForFunction(()=>GeoUI.ids.size===3&&GeoUI.dirty&&GeoUI.streetApproval!==null);
   assert.deepEqual(await p.evaluate(()=>GeoUI.chosen().map(a=>a.number).sort()),['1','3','5']);
   assert.equal(await p.evaluate(id=>JSON.stringify(card(id)),fixture.cards[index]),before,'Download and preview do not modify the card');
   assert.equal(writes.filter(w=>w.action==='geo.assign').length,0);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await p.screenshot({path:path.join(out,`street-preview-${language}-${width}.png`),fullPage:true});
   await p.locator('#geoSelection [data-geo=save]').click();await p.locator('[data-geo=confirm-save]').click();
   await p.waitForFunction(id=>card(id).address_ids?.length===3&&SaveStatus.kind==='saved',fixture.cards[index]);
   assert.equal(writes.filter(w=>w.action==='geo.assign').length,1);assert.equal(await p.evaluate(id=>card(id).front_revision,fixture.cards[index]),true);
   for(const wording of ['2024','marts 2024']){
    await p.evaluate(id=>{closeDialog();IBUI.open(null,id);},fixture.cards[index]);
    await p.locator('#ibForm [name=road]').fill('Fictional road '+index);await p.locator('#ibForm [name=number]').fill(wording==='2024'?'1':'3');
    await p.locator('#ibForm [name=date_text]').fill(wording);await p.locator('#ibForm button:not([type=button])').click();
    await p.waitForFunction(({id,wording})=>state.ib.some(i=>i.card_id===id&&i.date_text===wording&&i.date===''),{id:fixture.cards[index],wording});
   }
   const text=await p.evaluate(id=>backHTML(card(id)),fixture.cards[index]);assert.ok(text.includes('marts 2024')&&text.includes('2024'));
   assert.deepEqual(errors,[]);await context.close();
  }
  console.log(JSON.stringify({ok:true,real_server:true,languages:['en','da'],widths:[390,1440],preview_without_card_write:true,one_confirmed_save:true,manual_year_and_month_year_preserved:true}));
 }finally{if(browser)await browser.close();child.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
