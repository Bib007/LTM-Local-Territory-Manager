'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/w124_server.py')],{env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},stdio:['pipe','pipe','inherit']});let browser;
 const commands=new Map();let sequence=0;
 const lines=createInterface({input:child.stdout});let ready;
 const fixtureReady=new Promise((resolve,reject)=>{ready=resolve;child.once('exit',code=>reject(Error('Fixture exited '+code)));});
 lines.on('line',line=>{const value=JSON.parse(line);if(value.origin)ready(value);else{const pending=commands.get(value.id);commands.delete(value.id);pending?.(value);}});
 const control=op=>new Promise(resolve=>{const id=++sequence;commands.set(id,resolve);child.stdin.write(JSON.stringify({id,op})+'\n');});
 try{
  const fixture=await fixtureReady;
  browser=await chromium.launch({executablePath:process.env.LTM_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox']});
  const context=await browser.newContext({viewport:{width:1280,height:900}}),errors=[],writes=[];
  await context.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,fixture.origin,'Local fictional server only');return route.continue();});
  async function page(){const p=await context.newPage();p.setDefaultTimeout(15000);p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(r.url()===fixture.origin+'/api/mutate')writes.push(r.postDataJSON());});return p;}
  const a=await page();a.on('dialog',dialog=>dialog.accept());await a.goto(fixture.origin);
  await a.locator('#loginName').fill('Fiktiv admin');await a.locator('#loginPassword').fill('Fiktiv-password-123');await a.locator('#loginForm button').click();
  await a.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
  if(await a.locator('[data-profile=welcome-done]').count())await a.locator('[data-profile=welcome-done]').click();
  const b=await page();await b.goto(fixture.origin);await b.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
  for(const p of [a,b])await p.evaluate(()=>{clearInterval(ProfilesUI.timer);});
  async function openCard(p){await p.evaluate(id=>editCard(id),fixture.card);await p.evaluate(()=>EditorBases.current.ready);}
  async function saved(p,field,value){await p.waitForFunction(({field,value})=>SaveStatus.kind==='saved'&&state.cards[0][field]===value,{field,value});}
  await openCard(a);await control('expire-editors');let count=writes.length;
  await a.locator('#cardForm button.primary').click();await a.waitForFunction(()=>!document.querySelector('#dialog').open);
  assert.equal(writes.length,count);assert.equal(await a.evaluate(()=>SaveStatus.message),'Ingen nye ændringer');
  console.log('PASS browser unchanged card after expiry: no mutation and no rejection');
  await openCard(a);const original=await a.locator('#cardForm input[name=name]').inputValue();
  await a.locator('#cardForm input[name=name]').fill('Fiktiv kort ændring');await a.locator('#cardForm input[name=name]').fill(original);
  await a.waitForFunction(()=>SaveStatus.kind==='unchanged');
  await a.locator('#cardForm [data-action=close]').click();assert.equal(writes.length,count);
  console.log('PASS browser edit-and-revert before autosave sends no mutation');
  for(const [name,expression,selector,id] of [
   ['publisher','editPublisher','#publisherForm',fixture.publisher],
   ['area','editArea','#areaForm',fixture.area],
   ['note','Workspace.noteForm','form[data-work-form=note]',fixture.note]
  ]){
   await a.evaluate(({expression,id})=>{if(expression==='editPublisher')editPublisher(id);else if(expression==='editArea')editArea(id);else Workspace.noteForm(id);},{expression,id});
   await a.evaluate(()=>EditorBases.current.ready);await control('expire-editors');
   await a.locator(selector+' button.primary').click();await a.waitForFunction(()=>!document.querySelector('#dialog').open);assert.equal(writes.length,count,name+' no-op');
  }
  await a.evaluate(()=>{page='Indstillinger';Navigation.settingsSection='general';render();});
  await a.locator('#settingsForm button.primary').click();assert.equal(writes.length,count,'settings no-op');
  console.log('PASS browser unchanged publisher, area, note and settings forms');
  await a.evaluate(()=>EditorBases.page.ready);
  await b.evaluate(async()=>{for(let i=0;i<20;i++)await refresh();});
  await a.locator('#settingsCongregation').fill('Fiktiv prøvemenighed');await a.locator('#settingsForm button.primary').click();
  await a.waitForFunction(()=>SaveStatus.kind==='saved'&&state.settings.congregation==='Fiktiv prøvemenighed');
  assert.equal(writes.length,count+1);console.log('PASS browser settings form base survives other-tab state reads');
  await openCard(a);
  const firstBase=await a.evaluate(()=>EditorBases.current.base);
  await b.evaluate(async()=>{for(let i=0;i<20;i++){await refresh();await(await api('/api/profiles/admin')).json();}});
  assert.equal(await a.evaluate(()=>EditorBases.current.base),firstBase);
  await b.evaluate(id=>mutate('card.save',{...card(id),name:'Fiktiv anden fane'},{close:false}),fixture.card);
  await a.locator('#cardForm select[name=kind]').selectOption('By');await saved(a,'kind','By');
  assert.equal(await a.evaluate(()=>state.cards[0].name),'Fiktiv anden fane');assert.equal(await a.evaluate(()=>state.profile.conflicts),0);
  await a.locator('#cardForm input[name=name]').fill('Fiktiv egen rettelse');await saved(a,'name','Fiktiv egen rettelse');
  assert.equal(await a.evaluate(()=>state.profile.conflicts),1);
  await a.locator('#cardForm [data-action=close]').click();
  console.log('PASS browser same-session reads and independent/conflicting edits preserve honest base');
  // Hold the first accepted HTTP reply while another editor is opened.
  await openCard(a);const before=writes.length;let started,release;
  const begun=new Promise(resolve=>started=resolve),held=new Promise(resolve=>release=resolve);let delay=true;
  await a.route('**/api/mutate',async route=>{if(delay){delay=false;const response=await route.fetch();started();await held;await route.fulfill({response});}else await route.continue();});
  await a.evaluate(id=>{window.queueFirst=mutate('card.save',{...card(id),name:'Fiktiv kø A'},{close:false});window.queueSecond=mutate('card.save',{...card(id),name:'Fiktiv kø B'},{close:false});},fixture.card);
  await begun;
  await a.evaluate(id=>editPublisher(id),fixture.publisher);await a.evaluate(()=>EditorBases.current.ready);
  const otherBase=await a.evaluate(()=>EditorBases.current.base);release();await a.evaluate(()=>Promise.all([queueFirst,queueSecond]));
  assert.equal(writes.length,before+2);assert.notEqual(writes[before+1].profile_snapshot,otherBase);
  assert.equal(await a.evaluate(()=>EditorBases.current.base),otherBase);assert.equal(await a.locator('#publisherForm input[name=name]').inputValue(),'Fiktiv person');
  await a.locator('.dialogClose').click();await a.unroute('**/api/mutate');
  console.log('PASS browser delayed queued write retains own base across newer dialog');
  // Autosave and a simultaneous manual save of identical fields share one request.
  await openCard(a);let startAuto,releaseAuto;const autoBegun=new Promise(resolve=>startAuto=resolve),autoHeld=new Promise(resolve=>releaseAuto=resolve);let autoDelay=true;
  await a.route('**/api/mutate',async route=>{if(autoDelay){autoDelay=false;const response=await route.fetch();startAuto();await autoHeld;await route.fulfill({response});}else await route.continue();});
  count=writes.length;await a.locator('#cardForm input[name=name]').fill('Fiktiv enkelt gemning');await autoBegun;
  await a.locator('#cardForm button.primary').click();releaseAuto();await a.waitForFunction(()=>!document.querySelector('#dialog').open);assert.equal(writes.length,count+1);
  await a.unroute('**/api/mutate');console.log('PASS browser autosave plus Gem nu coalesces identical draft');
  // A genuinely expired base keeps changed fields and explains that base problem.
  await openCard(a);await control('expire-editors');await a.locator('#cardForm input[name=name]').fill('Fiktiv bevaret ved udløb');
  await a.waitForFunction(()=>SaveStatus.message.includes('Kladden er bevaret'));
  assert.equal(await a.locator('#cardForm input[name=name]').inputValue(),'Fiktiv bevaret ved udløb');assert.doesNotMatch(await a.evaluate(()=>SaveStatus.message),/afvist/);
  await a.evaluate(()=>{dialogDirty=false;closeDialog();});await a.evaluate(()=>refresh());
  console.log('PASS browser expired changed draft remains visible with specific base feedback');
  // Once committed, failed state reads are known saved and a repeat is blocked.
  await openCard(a);await control('fail-read');count=writes.length;
  await a.locator('#cardForm input[name=name]').fill('Fiktiv gemt trods læsefejl');
  await a.waitForFunction(()=>WriteGuard.needsReview);
  assert.match(await a.evaluate(()=>SaveStatus.message),/gemt/);assert.doesNotMatch(await a.evaluate(()=>SaveStatus.message),/afvist/);
  assert.equal(await a.locator('#cardForm input[name=name]').inputValue(),'Fiktiv gemt trods læsefejl');
  await a.locator('#cardForm button.primary').click();assert.equal(writes.length,count+1);
  await b.evaluate(()=>refresh());assert.equal(await b.evaluate(()=>state.cards[0].name),'Fiktiv gemt trods læsefejl');
  await a.screenshot({path:process.env.LTM_W124_SCREENSHOT||'/tmp/ltm-save-rejections/implementation/w124-known-saved.png',fullPage:true});
  console.log('PASS browser committed read failure stays known saved, retains draft and blocks repeat');
  assert.deepEqual(errors,[]);console.log('W124 real Chrome/loopback browser checks passed; no external requests or page errors.');
 }finally{if(browser)await browser.close();child.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
