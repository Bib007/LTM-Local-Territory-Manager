// Real app with temporary fictional data; native AirPrint outcomes are simulated.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')]);
 child.stderr.pipe(process.stderr);
 try{
  const fixture=await new Promise((resolve,reject)=>{
   const timeout=setTimeout(()=>reject(Error('Fictional fixture did not start')),20000);
   createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timeout);resolve(JSON.parse(line));});
   child.once('exit',code=>{clearTimeout(timeout);reject(Error('Fixture exited: '+code));});
  });
  for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
   const browser=await engine.launch({headless:true});
   try{
    const context=await browser.newContext({viewport:{width:820,height:1180},isMobile:true,hasTouch:true});
    await context.addCookies([fixture.cookie]);
    await context.addInitScript(()=>Object.defineProperty(navigator,'standalone',{value:true,configurable:true}));
    await context.route('**/*',route=>route.request().url().startsWith(fixture.origin+'/')?route.continue():route.abort());
    const source=await context.newPage(),errors=[];let popups=0;
    source.on('pageerror',error=>errors.push(error.message));source.on('popup',()=>popups++);
    await source.goto(fixture.origin);
    await source.waitForFunction(()=>state!==null&&SaveStatus.kind==='saved');
    const overlay=source.locator('#ltmPrintPreview'),back=overlay.locator('button'),frame=source.frameLocator('#ltmPrintPreview iframe');
    async function printAndReturn(selector,completed){
     await frame.locator(selector).waitFor();
     await frame.locator(selector).evaluate(button=>{
      const win=button.ownerDocument.defaultView;win.print=()=>{win.testPrints=(win.testPrints||0)+1;};
     });
     await frame.locator(selector).click();
     assert.equal(await frame.locator(selector).evaluate(button=>button.ownerDocument.defaultView.testPrints),1);
     if(completed)await frame.locator(selector).evaluate(button=>button.ownerDocument.defaultView.dispatchEvent(new Event('afterprint')));
     // No afterprint is guaranteed when cancelled. Neither outcome closes the view.
     assert.equal(await overlay.isVisible(),true);
     assert.equal(await frame.locator('body').getByText('Tilbage til LTM',{exact:false}).count(),0);
     await source.emulateMedia({media:'print'});
     assert.equal(await overlay.isVisible(),false);
     assert.equal(await frame.locator(selector).evaluate(button=>getComputedStyle(button.closest('.bar')).display),'none');
     await source.emulateMedia({media:'screen'});
     await back.click();await overlay.waitFor({state:'detached'});
    }
    // All real report entry points, including original service-year S-13, remain in the app.
    await source.evaluate(()=>{I18n.set('da');page='Rapporter';reportTab='Rapport';Workspace.reportPeriod='service';Workspace.reportPreview=true;render();window.originalReport=el('app').firstElementChild;});
    for(const mode of ['service','calendar','rolling']){
     await source.evaluate(mode=>{Workspace.reportPeriod=mode;Workspace.calendarYear=2026;render();window.originalReport=el('app').firstElementChild;},mode);
     await source.locator('[data-action=s13]').click();
     await frame.locator('.s13Original').first().waitFor();
     await printAndReturn('#printReport',mode!=='calendar');
     assert.equal(await source.evaluate(mode=>page==='Rapporter'&&Workspace.reportPeriod===mode&&window.originalReport===el('app').firstElementChild,mode),true);
    }
    await source.evaluate(()=>{Workspace.reportPeriod='rolling';render();window.originalReport=el('app').firstElementChild;window.job=printReport({withoutBackground:true});});
    await printAndReturn('#printReport',true);
    assert.equal(await source.evaluate(()=>Workspace.reportPeriod==='rolling'&&window.originalReport===el('app').firstElementChild),true);
    // Cancel while assets are pending; late work cannot resurrect the preview.
    await source.evaluate(()=>{window.originalInline=inlineReportAssets;inlineReportAssets=markup=>new Promise(resolve=>window.releaseAsset=()=>resolve(markup));window.job=printReport({s13Only:true});});
    await source.waitForFunction(()=>typeof window.releaseAsset==='function');
    await back.click();await source.evaluate(()=>window.releaseAsset());await source.waitForFunction(()=>!printReport.busy);
    assert.equal(await overlay.count(),0);assert.equal(await source.evaluate(()=>Workspace.reportPeriod),'rolling');
    await source.evaluate(()=>{inlineReportAssets=window.originalInline;});
    // The card form stays mounted, including uncommitted input and nested scroll.
    for(const side of ['front','back']){
     await source.evaluate(({id,side})=>{page='Distrikter';selected=id;render();printOptions(id,side);const form=el('printForm');form.elements.remember.checked=side==='front';window.originTerritory=el('app').firstElementChild;form.querySelector('details').open=true;form.elements.x.value='1.5';form.elements.x.focus();el('dialog').scrollTop=80;window.originForm=form;window.originScroll=el('dialog').scrollTop;window.originCard=selected;window.job=printCard(form);},{id:fixture.cards[0],side});
     await frame.locator('.sheet').first().waitFor();
     await source.waitForFunction(()=>!el('printForm').dataset.printing);
     await printAndReturn('#print',side==='front');
     assert.equal(await source.evaluate(()=>el('printForm')===window.originForm&&el('printForm').elements.x.value==='1.5'&&el('dialog').open&&selected===window.originCard&&el('dialog').scrollTop===window.originScroll&&el('app').firstElementChild===window.originTerritory),true);
     await source.evaluate(()=>closeDialog());
    }
    await source.evaluate(()=>{window.job=printIBOverview([{card_id:state.cards[0].id,road:'Fiktiv vej',number:'9',date:'2026-10-01'}]);});
    await printAndReturn('#printIBOverview',true);
    assert.equal(popups,0);assert.deepEqual(errors,[]);
    await context.close();
    console.log(name+' standalone return: report, three S-13 periods, front/back, IB, simulated completion/cancel and delayed assets.');
   }finally{await browser.close();}
  }
 }finally{child.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
