// Real app with temporary fictional data; native AirPrint outcomes are simulated.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
// Same fictional PNG as the successful mobile report fixture; no live OSM.
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l6kAAAAASUVORK5CYII=','base64');
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
   let source,step='startup',tileRequests=0;
   try{
    const context=await browser.newContext({viewport:{width:820,height:1180},isMobile:true,hasTouch:true});
    await context.addCookies([fixture.cookie]);
    await context.addInitScript(()=>Object.defineProperty(navigator,'standalone',{value:true,configurable:true}));
    await context.route('**/*',route=>{
     const url=new URL(route.request().url());
     if(url.origin===fixture.origin)return route.continue();
     if(url.origin==='https://tile.openstreetmap.org'&&/^\/\d+\/\d+\/\d+\.png$/.test(url.pathname)){
      tileRequests++;
      return route.fulfill({status:200,contentType:'image/png',headers:{'access-control-allow-origin':'*','cache-control':'no-store'},body:tile});
     }
     return route.abort();
    });
    source=await context.newPage();const errors=[];let popups=0;
    source.on('pageerror',error=>errors.push(error.message));source.on('popup',()=>popups++);
    await source.goto(fixture.origin);
    await source.waitForFunction(()=>state!==null&&state.profile&&SaveStatus.kind==='saved'&&ProfilesUI.timer&&!ProfilesUI.polling);
    // The disposable authenticated account can start with a profile intro.
    // Dismiss startup UI as a user, before navigating or creating a draft.
    const startup=source.locator('#dialog');
    if(await startup.isVisible()){
     const heading=await startup.locator('h2').first().textContent();
     console.log(name+' startup dialog: '+heading);
     const welcome=startup.locator('[data-profile="welcome-done"]');
     if(await welcome.isVisible()){
      await welcome.click();
      await source.waitForFunction(()=>state.profile.user.onboarded&&SaveStatus.kind==='saved'&&!PendingSaves.count);
     }else await startup.locator('.dialogClose').click();
     await startup.waitFor({state:'hidden'});
    }
    assert.equal(await startup.evaluate(dialog=>dialog.open),false,'Startup dialog must be closed before report navigation');
    const overlay=source.locator('#ltmPrintPreview'),back=overlay.getByRole('button',{name:'← Tilbage til LTM',exact:true}),frame=source.frameLocator('#ltmPrintPreview iframe');
    async function printAndReturn(selector,completed){
     await frame.locator(selector).waitFor({state:'visible'});
     await source.waitForFunction(()=>PrintPreview.active&&!PrintPreview.active.closed);
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
     assert.equal(await source.evaluate(()=>PrintPreview.active),null);
    }
    // All real report entry points, including original service-year S-13, remain in the app.
    step='initial report render';
    await source.evaluate(()=>{I18n.set('da');page='Rapporter';reportTab='Rapport';Workspace.reportPeriod='service';Workspace.reportPreview=true;render();window.originalReport=el('app').firstElementChild;});
    assert.equal(await source.evaluate(()=>I18n.language()),'da');
    for(const mode of ['service','calendar','rolling']){
     step='S-13 '+mode+' render';
     await source.evaluate(mode=>{Workspace.reportPeriod=mode;Workspace.calendarYear=2026;render();window.originalReport=el('app').firstElementChild;},mode);
     // ReportMap is genuinely mounted. Wait for its local tile cycle, not
     // merely for a clickable button that may race a map failure dialog.
     await source.waitForFunction(()=>ReportMap.tileFailed||!ReportMap.map||(!ReportMap.tiles.isLoading()&&ReportMap.tileTimeout===null));
     assert.equal(await source.evaluate(()=>ReportMap.tileFailed),false,step+' basemap must load with the fictional tiles');
     assert.equal(await startup.evaluate(dialog=>dialog.open),false,step+' entry point must not sit behind another dialog');
     step='S-13 '+mode+' print and return';
     await source.locator('[data-action=s13]').click();
     await frame.locator('.s13Original').first().waitFor();
     await printAndReturn('#printReport',mode!=='calendar');
     await source.waitForFunction(()=>!printReport.busy);
     assert.equal(await source.evaluate(mode=>page==='Rapporter'&&Workspace.reportPeriod===mode&&window.originalReport===el('app').firstElementChild,mode),true);
    }
    assert.ok(tileRequests>0,'Real report renders must request the fictional OSM tiles');
    step='rolling full report without background';
    await source.evaluate(()=>{Workspace.reportPeriod='rolling';render();window.originalReport=el('app').firstElementChild;window.job=printReport({withoutBackground:true});});
    await printAndReturn('#printReport',true);
    await source.evaluate(()=>window.job);
    assert.equal(await source.evaluate(()=>Workspace.reportPeriod==='rolling'&&window.originalReport===el('app').firstElementChild),true);
    // Cancel while assets are pending; late work cannot resurrect the preview.
    step='cancel pending S-13 assets';
    await source.evaluate(()=>{window.originalInline=inlineReportAssets;inlineReportAssets=markup=>new Promise(resolve=>window.releaseAsset=()=>resolve(markup));window.job=printReport({s13Only:true});});
    await source.waitForFunction(()=>typeof window.releaseAsset==='function');
    await back.click();await overlay.waitFor({state:'detached'});await source.evaluate(()=>window.releaseAsset());await source.evaluate(()=>window.job);await source.waitForFunction(()=>!printReport.busy);
    assert.equal(await overlay.count(),0);assert.equal(await source.evaluate(()=>Workspace.reportPeriod),'rolling');
    await source.evaluate(()=>{inlineReportAssets=window.originalInline;});
    // The card form stays mounted, including uncommitted input and nested scroll.
    for(const side of ['front','back']){
     step='card '+side+' print and return';
     await source.evaluate(({id,side})=>{page='Distrikter';selected=id;render();printOptions(id,side);const form=el('printForm');form.elements.remember.checked=side==='front';window.originTerritory=el('app').firstElementChild;form.querySelector('details').open=true;form.elements.x.value='1.5';form.elements.x.focus();el('dialog').scrollTop=80;window.originForm=form;window.originScroll=el('dialog').scrollTop;window.originCard=selected;window.job=printCard(form);},{id:fixture.cards[0],side});
     await frame.locator('.sheet').first().waitFor();
     await source.evaluate(()=>window.job);
     await source.waitForFunction(()=>!el('printForm')?.dataset.printing);
     await printAndReturn('#print',side==='front');
     assert.equal(await source.evaluate(()=>el('printForm')===window.originForm&&el('printForm').elements.x.value==='1.5'&&el('dialog').open&&selected===window.originCard&&el('dialog').scrollTop===window.originScroll&&el('app').firstElementChild===window.originTerritory),true);
     await source.evaluate(()=>closeDialog());
    }
    step='IB print over unsent card draft';
    // Independent real card-editor context: opening a preview must not
    // discard an unsent draft, the active filter or selection. Assign the
    // draft directly so the autosave debounce cannot race this print test.
    await source.evaluate(id=>{
     page='Distrikter';selected=id;query=card(id).number;render();editCard(id);
     const form=el('cardForm'),input=form.elements.name;
     window.cardDraftBefore={form,input,selected,query,area,status,view,stored:card(id).name,app:el('app').firstElementChild};
     input.value='FIKTIV USENDT KORTKLADDE';dialogDirty=true;input.focus();input.setSelectionRange(2,8);
     window.cardDraftBefore.scroll=el('dialog').scrollTop;
     window.job=printIBOverview([{card_id:id,road:'Fiktiv vej',number:'9',date:'2026-10-01'}]);
    },fixture.cards[0]);
    await printAndReturn('#printIBOverview',true);
    await source.evaluate(()=>window.job);
    assert.equal(await source.evaluate(()=>{
     const b=window.cardDraftBefore;
     return page==='Distrikter'&&selected===b.selected&&query===b.query&&area===b.area&&status===b.status&&view===b.view&&
      el('app').firstElementChild===b.app&&el('dialog').open&&el('cardForm')===b.form&&
      b.input.value==='FIKTIV USENDT KORTKLADDE'&&card(selected).name===b.stored&&dialogDirty&&
      document.activeElement===b.input&&b.input.selectionStart===2&&b.input.selectionEnd===8&&el('dialog').scrollTop===b.scroll;
    }),true,'Returning from IB print preserves the real card editor and unsent draft');
    await source.evaluate(()=>{dialogDirty=false;closeDialog();});
    assert.equal(popups,0);assert.deepEqual(errors,[]);
    await context.close();
    console.log(name+' standalone return: report, three S-13 periods, front/back, IB, simulated completion/cancel and delayed assets.');
   }catch(error){
    let diagnostic={};
    if(source&&!source.isClosed()){
     try{diagnostic=await source.evaluate(()=>({
      page:typeof page==='undefined'?null:page,
      period:typeof Workspace==='undefined'?null:Workspace.reportPeriod,
      dialogOpen:document.getElementById('dialog')?.open,
      dialogHeading:document.querySelector('#dialog h2,#dialog h1,#dialog h3')?.textContent?.trim()||null,
      dialogGeneration:typeof openDialog==='undefined'?null:openDialog.generation,
      tileFailed:typeof ReportMap==='undefined'?null:ReportMap.tileFailed,
      tilesLoading:typeof ReportMap==='undefined'?null:ReportMap.tiles?.isLoading()??null,
      previewOpen:!!document.getElementById('ltmPrintPreview')?.open
     }));}catch(diagnosticError){diagnostic={diagnosticError:String(diagnosticError)};}
    }
    console.error(name+' standalone failure: '+JSON.stringify({step,tileRequests,...diagnostic}));
    throw error;
   }finally{await browser.close();}
  }
 }finally{child.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
