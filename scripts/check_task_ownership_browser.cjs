'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const {spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/task_ownership_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const lines=createInterface({input:child.stdout}),timer=setTimeout(()=>reject(Error('Fixture timed out')),15000);lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});child.once('exit',code=>reject(Error('Fixture exited '+code)));});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const errors=[],out=process.env.LTM_BROWSER_OUTPUT||'/tmp/ltm-task-ownership';fs.mkdirSync(out,{recursive:true});
  async function page(cookie,width=1440){const context=await browser.newContext({viewport:{width,height:950}});await context.addCookies([cookie]);await context.route('**/*',r=>{assert.equal(new URL(r.request().url()).origin,fixture.origin);return r.continue();});const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(fixture.origin);await p.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');if(await p.locator('[data-profile=welcome-done]').count())await p.locator('[data-profile=welcome-done]').click();await p.waitForFunction(()=>PersonalGuide.data!==null);if(await p.locator('[data-personal-guide=later]').count())await p.locator('[data-personal-guide=later]').click();return p;}
  async function navigate(p,item){if(p.viewportSize().width<800)await p.locator('.mobileMenu').click();await p.locator(`[data-navigation="${item}"]`).click();}
  const admin=await page(fixture.admin);
  await navigate(admin,'1:3');await admin.locator('[data-work=new-task]').click();
  const form=admin.locator('[data-work-form=note]');await form.locator('[name=text]').fill('Fictional responsibility <safe>');await form.locator('[name=card_id]').selectOption(fixture.card);await form.locator('[name=assignee_id]').selectOption(fixture.reader_id);
  const imageBytes=await admin.evaluate(()=>{const canvas=document.createElement('canvas');canvas.width=16;canvas.height=16;const ctx=canvas.getContext('2d');ctx.fillStyle='#4488bb';ctx.fillRect(0,0,16,16);return canvas.toDataURL('image/png').split(',')[1];});
  await form.locator('[name=taskImages]').setInputFiles({name:'Fictional task image.png',mimeType:'image/png',buffer:Buffer.from(imageBytes,'base64')});
  await admin.locator('#navigationLanguage').selectOption('da');assert.equal(await form.locator('[name=assignee_id]').inputValue(),fixture.reader_id);assert.equal(await form.locator('[name=text]').inputValue(),'Fictional responsibility <safe>');assert.equal(await form.locator('label[for=taskAssignee]').innerText(),'Ansvarshavende (valgfri)');
  await admin.locator('#navigationLanguage').selectOption('en');assert.equal(await form.locator('label[for=taskAssignee]').innerText(),'Responsible person (optional)');await form.locator('button.primary').click();await admin.waitForFunction(()=>state.notes.some(n=>n.assigned)&&SaveStatus.kind==='saved');assert.ok((await admin.locator('.taskOwner').first().innerText()).includes('Fictional reader <test>'));assert.equal(await admin.locator('.taskOwner test').count(),0);
  const reader=await page(fixture.reader,390);await navigate(reader,'1:3');await reader.locator('[data-work=task-owner-filter][data-value=mine]').click();assert.equal(await reader.locator('.taskRow').count(),1);assert.ok((await reader.locator('.taskOwner').innerText()).includes('Assigned to you'));assert.equal(await reader.evaluate(()=>state.task_users),undefined);
  const thumbnail=reader.locator('.taskRow .taskImages img');
  await thumbnail.scrollIntoViewIfNeeded();
  await thumbnail.evaluate(img=>img.decode());
  assert.equal(await thumbnail.getAttribute('alt'),'Fictional task image.png');
  assert.equal(await thumbnail.evaluate(img=>img.naturalWidth),16);
  await reader.locator('[data-work=edit-note]').click();assert.equal(await reader.locator('[name=assignee_id]').count(),0);await reader.locator('[name=text]').fill('Fictional task edited by its owner');await reader.locator('[data-work-form=note] button.primary').click();await reader.waitForFunction(()=>state.notes.some(n=>n.text==='Fictional task edited by its owner')&&SaveStatus.kind==='saved');assert.equal(await reader.locator('.taskOwner').innerText(),'Assigned to you');
  await reader.locator('#navigationLanguage').selectOption('da');assert.equal(await reader.locator('.taskOwner').innerText(),'Du er ansvarshavende');assert.ok(await reader.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await reader.screenshot({path:path.join(out,'assigned-reader-da.png'),fullPage:false});
  await reader.locator('[data-work=task-owner-filter][data-value=unassigned]').click();assert.equal(await reader.locator('.taskRow').count(),0);
  await reader.locator('[data-work=task-owner-filter][data-value=mine]').click();
  await reader.locator('[data-work=edit-note]').click();
  const removal=reader.locator('[data-work-form=note]');
  await removal.locator('[name=removeImage]').check();
  await removal.locator('button.primary').click();
  await reader.waitForFunction(()=>state.notes.every(n=>!n.images?.length)&&SaveStatus.kind==='saved');
  assert.equal(await reader.locator('.taskRow .taskImages img').count(),0);
  await reader.locator('.taskRow [data-work=resolve]').click();
  const complete=reader.locator('[data-work-form=complete-task]');
  await complete.waitFor();
  assert.match(await complete.locator('label[for=taskReply]').innerText(),/Svar til Fictional admin/);
  assert.equal(await reader.evaluate(()=>state.notes[0].resolved),false);
  await complete.locator('textarea').fill('God idé <fiktivt svar>');
  await complete.locator('button.primary').click();
  await reader.waitForFunction(()=>state.notes[0].resolved&&SaveStatus.kind==='saved');
  await admin.evaluate(()=>refresh());
  await admin.locator('[data-work=task-filter][data-value=replies]').click();
  const history=admin.locator('.taskCompletionHistory');
  await history.locator('summary').click();
  assert.match(await history.innerText(),/God idé <fiktivt svar>/);
  assert.match(await history.innerText(),/Reply to you/);
  assert.match(await history.innerText(),/Fictional reader/);
  assert.equal(await history.locator('fiktivt').count(),0);
  admin.once('dialog',dialog=>dialog.accept());
  await history.locator('[data-work=delete-task-reply]').click();
  await admin.waitForFunction(()=>state.notes[0].resolved&&!state.notes[0].task_history.some(entry=>entry.reply)&&SaveStatus.kind==='saved');
  await admin.locator('[data-work=task-filter][data-value=done]').click();
  await admin.locator('.taskCompletionHistory summary').click();
  assert.doesNotMatch(await admin.locator('.taskCompletionHistory').innerText(),/fiktivt svar/);
  // Follow-up creates one linked task; revisiting opens that same record.
  await admin.reload();await admin.waitForFunction(()=>state&&SaveStatus.kind==='saved'&&PersonalGuide.data!==null);if(await admin.locator('[data-personal-guide=later]').count())await admin.locator('[data-personal-guide=later]').click();await navigate(admin,'1:4');await admin.locator('[data-work=followup-task]').first().click();const linked=admin.locator('[data-work-form=note]');assert.ok(await linked.locator('[name=followup_key]').inputValue());await linked.locator('[name=assignee_id]').selectOption(fixture.reader_id);await linked.locator('button.primary').click();await admin.waitForFunction(()=>state.notes.some(n=>n.followup_key)&&SaveStatus.kind==='saved');const count=await admin.evaluate(()=>state.notes.length);await admin.locator('[data-work=followup-task]').first().click();assert.ok(await admin.locator('[data-work-form=note]').getAttribute('data-id'));assert.equal(await admin.evaluate(()=>state.notes.length),count);await admin.screenshot({path:path.join(out,'linked-task-en.png'),fullPage:false});assert.deepEqual(errors,[]);
  console.log('PASS actual HTTP/SQLite UI: EN/DA draft retention, assignment, private self label, limited editing, filters, mobile fit and one linked follow-up task.');
 }finally{if(browser)await browser.close();child.kill('SIGTERM');}
})().catch(e=>{console.error(e);process.exitCode=1;});
