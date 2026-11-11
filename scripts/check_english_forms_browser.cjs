'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')]);child.stderr.pipe(process.stderr);let browser;
try{const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',l=>{clearTimeout(timer);resolve(JSON.parse(l));});child.once('exit',n=>{clearTimeout(timer);reject(Error('Fixture exit '+n));});});browser=await chromium.launch({headless:true,...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
const context=await browser.newContext({viewport:{width:1440,height:1100}});await context.addCookies([fixture.cookie]);const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));page.setDefaultTimeout(15000);await page.goto(fixture.origin);await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');const out=process.env.LTM_BROWSER_OUTPUT||'/tmp/ltm-english-forms';fs.mkdirSync(out,{recursive:true});
for(const language of ['en','da']){
 await page.evaluate(language=>{closeDialog();I18n.set(language);state.cards[0].name='Fictional locality';detail(state.cards[0].id);},language);await page.locator('.cardPreview>img').evaluate(i=>i.decode());assert.equal(await page.locator('.cardPreview').getAttribute('data-form-language'),language);assert.ok((await page.locator('.cardPreview>img').getAttribute('src')).endsWith(language==='en'?'s12-template-en.png':'s12-template.png'));await page.locator('.cardDisplay').screenshot({path:path.join(out,'S12-'+language+'.png')});
 await page.evaluate(()=>printOptions(state.cards[0].id,'front'));await page.locator('#printForm [name=form_language]').selectOption(language);await page.locator('#printForm [name=mode]').selectOption('full');await page.locator('#printForm [name=remember]').uncheck();const pending=context.waitForEvent('page');await page.locator('#printForm button:not([type=button])').click();const print=await pending;await print.waitForFunction(()=>document.getElementById('print')&&!document.getElementById('print').disabled);assert.equal(await print.locator('.cardPreview').getAttribute('data-form-language'),language);assert.equal(await print.locator('html').getAttribute('lang'),language);assert.ok((await print.locator('.cardPreview>img').getAttribute('src')).startsWith('data:image/png;base64,'));assert.equal(await print.locator('#tooLong').innerText(),'');await print.locator('.sheet').screenshot({path:path.join(out,'S12-print-'+language+'.png')});await print.close();
 await page.evaluate(language=>{I18n.set(language);openDialog(s13OriginalPages(allocationRows()),language);},language);await page.locator('.s13Original image').first().evaluate(i=>new Promise((resolve,reject)=>{const img=new Image();img.onload=resolve;img.onerror=reject;img.src=i.getAttribute('href');}));assert.ok((await page.locator('.s13Original image').first().getAttribute('href')).endsWith(language==='en'?'s13-background-en.jpg':'s13-background.jpg'));await page.locator('.s13Original').first().screenshot({path:path.join(out,'S13-browser-'+language+'.png')});
 const pdf=await page.evaluate(async language=>{const response=await api('/api/export/s13?year=2027&language='+language);return (await response.text()).slice(0,4);},language);assert.equal(pdf,'%PDF');
}
for(const [file,original] of [['S-12-en.pdf','S-12-E.pdf'],['S-13-en.pdf','S-13-E.pdf']]){const r=await context.request.get(fixture.origin+'/forms/'+file);assert.equal(r.status(),200);assert.deepEqual(await r.body(),fs.readFileSync(path.join(__dirname,'../distrikt/templates',original)));}
await page.evaluate(()=>{closeDialog();I18n.set('da');page='Distrikter';render();});
const cardId=fixture.cards[0],row=page.locator('[data-card-row="'+cardId+'"]');
await row.getByRole('checkbox').check();
await page.getByRole('button',{name:'Læg 1 i mappen',exact:true}).click();
await page.getByRole('button',{name:'Bekræft og læg 1 i mappen',exact:true}).click();
await page.waitForFunction(id=>card(id).in_folder,cardId);
await page.locator('#dialog [data-action="close"]').last().click();
await row.getByRole('checkbox').check();
await page.getByRole('button',{name:'Flyt 1 til kassen',exact:true}).click();
await page.waitForFunction(id=>!card(id).in_folder,cardId);
await row.getByRole('button',{name:'Udlever fra kassen',exact:true}).click();
assert.equal(await page.locator('#issueForm [name=initial]').isChecked(),false);
await page.locator('#issueForm [name=publisher_name]').fill('Fictional publisher');
await page.locator('#issueForm button:not([type=button])').click();
await page.waitForFunction(id=>loanFor(id)?.initial===false,cardId);
console.log('Manual folder moves in both directions and a new loan directly from the storage box passed.');
assert.deepEqual(errors,[]);console.log('English/Danish S-12 preview and actual print windows, own S-13 backgrounds and PDF exports, original download bytes passed.');await context.close();
}finally{await browser?.close();child.kill();}})().catch(e=>{console.error(e);process.exitCode=1;});
