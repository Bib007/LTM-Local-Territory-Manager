'use strict';
// Real temporary server and fictional publishers only.
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 for(const profiles of [false,true]){
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('ltm-language','da'));
  await page.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,fixture.origin);return route.continue();});
  await page.goto(fixture.origin);await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
  if(profiles){
   await page.evaluate(()=>api('/api/profiles/activate',{name:'Fiktiv admin',password:'Fiktiv-password-123',confirmation:'AKTIVÉR PROFILER'}));
   await page.reload();await page.locator('#loginName').fill('Fiktiv admin');await page.locator('#loginPassword').fill('Fiktiv-password-123');await page.locator('#loginForm button').click();
   await page.waitForFunction(()=>typeof state!=='undefined'&&state?.profile&&SaveStatus.kind==='saved');
   await page.locator('[data-profile=welcome-done]').click();
   await page.waitForFunction(()=>PersonalGuide.data!==null);
   const later=page.locator('[data-personal-guide=later]');if(await later.count())await later.click();
  }
  const ids=await page.evaluate(async()=>{
   const a=await mutate('publisher.save',{name:'Fiktiv Person',group:'Fiktiv gruppe',group_role:'assistant',pioneer:false});
   const b=await mutate('publisher.save',{name:'fiktiv p',group:'Anden gruppe',group_role:'overseer',pioneer:true});
   await mutate('loan.issue',{card_id:state.cards[0].id,publisher_id:b.id,date:state.today,initial:true});
   let recovery;
   for(let index=0;index<2;index++){
    const c=await mutate('card.save',{number:'F-CLOSED-'+index,temporary:true});
    const l=await mutate('loan.issue',{card_id:c.id,publisher_id:b.id,date:state.today,initial:true});
    await mutate('loan.finish',{id:l.id,date:state.today,complete:true});
    if(index)recovery=await mutate('delete',{module:'loans',id:l.id,history_revision:state.revision});
   }
   page='Forkyndere';render();publisherProfile(a.id);return {a:a.id,b:b.id,recovery};
  });
  const before=await page.evaluate(()=>({loans:state.loans,completions:state.completions}));
  await page.locator('[data-action=publisher-merge]').click();
  await page.locator('#publisherMergeForm select').selectOption(ids.b);
  await page.locator('#publisherMergeForm input[name=name]').fill('Samlet Fiktiv Person');
  await page.locator('#publisherMergeForm button.primary').click();
  await page.locator('[data-action=publisher-merge-apply]').waitFor();
  assert.match(await page.locator('#dialog').innerText(),/Gruppefunktion: Assistent[\s\S]*Pioner: Nej/);
  // A concurrent save after preview must reject the command without absorbing anyone.
  await page.evaluate(id=>api('/api/mutate',{action:'publisher.save',data:{id,name:'Fiktiv aktuel kilde'}}),ids.b);
  await page.locator('[data-action=publisher-merge-apply]').click();
  await page.waitForFunction(()=>SaveStatus.kind==='error');
  assert.match(await page.locator('#dialog').innerText(),/ændret/);
  assert.equal(await page.evaluate(()=>state.publishers.length),2);
  await page.locator('[data-action=publisher-merge]').click();
  await page.locator('#publisherMergeForm select').selectOption(ids.b);
  await page.locator('#publisherMergeForm input[name=name]').fill('Samlet Fiktiv Person');
  await page.locator('#publisherMergeForm button.primary').click();
  await page.locator('[data-action=publisher-merge-apply]').waitFor();
  assert.match(await page.locator('#dialog').innerText(),/Fiktiv aktuel kilde/,'Preview names must come from the server, not stale page state');
  await page.locator('[data-action=publisher-merge-apply]').click();
  await page.waitForFunction(()=>state.publishers.length===1&&SaveStatus.kind==='saved');
  const result=await page.evaluate(()=>({people:state.publishers,loans:state.loans}));
  assert.equal(result.people[0].name,'Samlet Fiktiv Person');assert.equal(result.people[0].group,'Fiktiv gruppe');
  assert.ok(result.loans.every(l=>l.publisher_id===ids.a));assert.deepEqual(result.people[0].aliases,['Fiktiv Person','Fiktiv aktuel kilde']);
  assert.equal(result.people[0].group_role,'assistant');assert.equal(result.people[0].pioneer,false);
  assert.deepEqual(await page.evaluate(()=>state.completions),before.completions);
  page.once('dialog',dialog=>dialog.accept());await page.locator('[data-work=undo]').click();
  await page.waitForFunction(()=>state.publishers.length===2&&SaveStatus.kind==='saved');
  assert.deepEqual(await page.evaluate(()=>state.loans),before.loans);
  await page.evaluate(id=>publisherProfile(id),ids.a);
  await page.locator('[data-action=publisher-merge]').click();await page.locator('#publisherMergeForm select').selectOption(ids.b);
  await page.locator('#publisherMergeForm input[name=name]').fill('Samlet Fiktiv Person');await page.locator('#publisherMergeForm button.primary').click();
  await page.locator('[data-action=publisher-merge-apply]').click();await page.waitForFunction(()=>state.publishers.length===1&&SaveStatus.kind==='saved');
  await page.evaluate(batch=>mutate('restore',batch),ids.recovery);
  assert.equal(await page.evaluate(()=>state.loans.length),3);
  assert.ok(await page.evaluate(id=>state.loans.every(l=>l.publisher_id===id),ids.a));
  await page.reload();await page.waitForFunction(()=>typeof state!=='undefined'&&state?.publishers?.length===1&&SaveStatus.kind==='saved');
  assert.deepEqual(await page.evaluate(()=>state.publishers[0].aliases),['Fiktiv Person','Fiktiv aktuel kilde']);assert.deepEqual(errors,[]);
  if(process.env.LTM_MERGE_SCREENSHOT){await page.evaluate(id=>publisherProfile(id),ids.a);await page.screenshot({path:process.env.LTM_MERGE_SCREENSHOT});}
  console.log('Fictional merge, live preview names, stale rejection, retained group/role/pioneer, active/returned/recoverable loans, completions, Undo and reload passed ('+(profiles?'profiles':'shared login')+').');
 }finally{if(browser)await browser.close();child.kill();}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
