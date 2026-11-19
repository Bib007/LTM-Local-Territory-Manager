'use strict';
// Real temporary server and fictional publishers only.
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('ltm-language','da'));
  await page.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,fixture.origin);return route.continue();});
  await page.goto(fixture.origin);await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
  const ids=await page.evaluate(async()=>{
   const a=await(await api('/api/mutate',{action:'publisher.save',data:{name:'Fiktiv Person',group:'Fiktiv gruppe'}})).json();
   const b=await(await api('/api/mutate',{action:'publisher.save',data:{name:'fiktiv p'}})).json();
   await api('/api/mutate',{action:'loan.issue',data:{card_id:state.cards[0].id,publisher_id:b.result.id,date:state.today,initial:true}});
   await refresh();page='Forkyndere';render();publisherProfile(a.result.id);return {a:a.result.id,b:b.result.id};
  });
  await page.locator('[data-action=publisher-merge]').click();
  await page.locator('#publisherMergeForm select').selectOption(ids.b);
  await page.locator('#publisherMergeForm input[name=name]').fill('Samlet Fiktiv Person');
  await page.locator('#publisherMergeForm button.primary').click();
  await page.locator('[data-action=publisher-merge-apply]').waitFor();
  assert.match(await page.locator('#dialog').innerText(),/Samlet Fiktiv Person/);
  await page.locator('[data-action=publisher-merge-apply]').click();
  await page.waitForFunction(()=>state.publishers.length===1&&SaveStatus.kind==='saved');
  const result=await page.evaluate(()=>({people:state.publishers,loans:state.loans}));
  assert.equal(result.people[0].name,'Samlet Fiktiv Person');assert.equal(result.people[0].group,'Fiktiv gruppe');
  assert.equal(result.loans[0].publisher_id,ids.a);assert.deepEqual(result.people[0].aliases,['Fiktiv Person','fiktiv p']);assert.deepEqual(errors,[]);
  if(process.env.LTM_MERGE_SCREENSHOT){await page.evaluate(id=>publisherProfile(id),ids.a);await page.screenshot({path:process.env.LTM_MERGE_SCREENSHOT});}
  console.log('Fictional publisher merge form, preview, real server save, aliases and loan identity passed.');
 }finally{if(browser)await browser.close();child.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
