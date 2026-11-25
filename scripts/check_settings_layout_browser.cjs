'use strict';
// Real disposable LTM server, fictional data, both themes and browser engines.
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
module.exports=async(chromium,out)=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});
 let safari;
 try{
  const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Settings fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});child.once('exit',n=>{clearTimeout(timer);reject(Error('Settings fixture exit '+n));});});
  safari=await webkit.launch();
  for(const [engine,browser] of [['chromium',chromium],['webkit',safari]]){
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   try{
    await context.route('**/*',route=>new URL(route.request().url()).origin===fixture.origin?route.continue():route.abort());
    await context.addInitScript(()=>localStorage.setItem('ltm-language','da'));
    const tab=await context.newPage(),errors=[];tab.on('pageerror',e=>errors.push(e.message));
    await tab.goto(fixture.origin);await tab.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
    const keys=['general','areas','printing','usage','connections','import','data','sharing','users'];
    await tab.evaluate(()=>{page='Indstillinger';Navigation.settingsSection='general';render();});
    assert.deepEqual(await tab.locator('.settingsSectionTabs button').evaluateAll(nodes=>nodes.map(n=>n.dataset.value)),keys);
    for(const width of [390,768,1024,1440])for(const theme of ['light','dark']){
     await tab.setViewportSize({width,height:900});await tab.evaluate(theme=>Theme.set(theme),theme);
     for(const key of keys){
      await tab.evaluate(key=>{Navigation.settingsSection=key;render();},key);
      const heading=tab.locator('#settings-'+key);await heading.waitFor({state:'visible'});
      assert.equal(await tab.locator('.settingsSectionTabs [aria-current=page]').getAttribute('data-value'),key);
      const geometry=await heading.evaluate(n=>{const p=n.closest('.panel'),r=p.getBoundingClientRect(),main=document.getElementById('app').getBoundingClientRect();return {left:r.left,right:r.right,mainLeft:main.left,mainRight:main.right,overflow:p.scrollWidth-p.clientWidth};});
      assert.ok(geometry.left>=geometry.mainLeft-1&&geometry.right<=geometry.mainRight+1&&geometry.overflow<=2,engine+' '+width+' '+theme+' '+key+' '+JSON.stringify(geometry));
      if(key==='general'){
       const sms=await tab.locator('#overdueTemplate').evaluate(n=>({width:n.getBoundingClientRect().width,parent:n.parentElement.clientWidth,form:n.form.id}));
       assert.equal(sms.form,'settingsForm');assert.ok(sms.width>=sms.parent-2,'SMS template fills its section');
       assert.ok(await tab.locator('#saveState').isVisible());
       await tab.locator('#settingsCongregation').focus();await tab.keyboard.press('Tab');
       assert.equal(await tab.evaluate(()=>document.activeElement.id),'settingsFolderEnabled');
       if(out&&[390,768,1440].includes(width))await tab.locator('#settings-general').evaluate(n=>n.scrollIntoView());
       if(out&&[390,768,1440].includes(width))await tab.screenshot({path:path.join(out,'settings-'+engine+'-'+width+'-'+theme+'.png')});
      }
     }
    }
    await tab.evaluate(()=>{Navigation.settingsSection='general';render();});
    const limit=tab.locator('#splitVisitLimit'),initial=await limit.inputValue();
    await limit.fill('1001');assert.equal(await limit.evaluate(n=>n.validity.rangeOverflow),true);
    await limit.fill(initial);assert.equal(await limit.evaluate(n=>n.validity.valid),true);
    const folder=tab.locator('#settingsFolderEnabled'),checked=await folder.isChecked();
    await folder.setChecked(false);assert.equal(await tab.locator('#folderWorkflowOptions').isVisible(),false);
    assert.equal(await tab.locator('#settingsFolderMinimum').isDisabled(),true);
    await folder.setChecked(true);assert.equal(await tab.locator('#settingsFolderMinimum').isDisabled(),false);
    await folder.setChecked(checked);
    await tab.evaluate(()=>{Navigation.settingsSection='data';render();});
    const years=tab.locator('#historyYears'),old=Number(await years.inputValue()),next=old===7?8:7;
    await years.fill(String(next));await tab.locator('#historySettingsForm button.primary').click();
    await tab.waitForFunction(next=>state.settings.history_years===next&&SaveStatus.kind==='saved',next);
    assert.equal(await tab.locator('#historyYears').inputValue(),String(next));
    assert.ok(await tab.locator('#saveState').isVisible());
    assert.deepEqual(errors,[]);
    console.log('Settings layout '+engine+': nine tabs, four widths, both themes, keyboard order, range validation, folder visibility and real fictional history save passed.');
   }finally{await context.close();}
  }
 }finally{await safari?.close();child.kill();}
};
