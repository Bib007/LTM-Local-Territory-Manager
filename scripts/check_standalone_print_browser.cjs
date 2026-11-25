// Real app with temporary fictional data; native AirPrint outcomes are simulated.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path');
const {spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
// Same fictional PNG as the successful mobile report fixture; no live OSM.
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l6kAAAAASUVORK5CYII=','base64');
(async()=>{
 // Each browser needs its own disposable store: otherwise Chromium completes
 // the printing onboarding task before WebKit can exercise that transition.
 for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')]);
 child.stderr.pipe(process.stderr);
 try{
  const fixture=await new Promise((resolve,reject)=>{
   const timeout=setTimeout(()=>reject(Error('Fictional fixture did not start')),20000);
   createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timeout);resolve(JSON.parse(line));});
   child.once('exit',code=>{clearTimeout(timeout);reject(Error('Fixture exited: '+code));});
  });
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
    // Record actual receipt differences, without printing state contents.
    // Pure profile saves preserve the app root. The second saved side
    // completes the printing setup task and must refresh the overview,
    // without replacing the live print form or losing user input.
    await source.evaluate(()=>{
     const compare=PrintPreview.profileOnly;
     const changed=(a,b)=>[...new Set([...Object.keys(a||{}),...Object.keys(b||{})])].filter(k=>JSON.stringify(a?.[k])!==JSON.stringify(b?.[k]));
     PrintPreview.profileOnly=function(previous,fresh){
      const allowed=compare.call(this,previous,fresh);
      window.profileReceiptChecks.push({allowed,topLevel:changed(previous,fresh),settings:changed(previous.settings,fresh.settings),profile:changed(previous.profile,fresh.profile),
       dashboardSummary:changed(previous.dashboard_summary,fresh.dashboard_summary),reportSummary:changed(previous.report_summary,fresh.report_summary),
       runtimeChanged:JSON.stringify(previous.runtime_status)!==JSON.stringify(fresh.runtime_status),
       onboardingFields:changed(previous.settings.onboarding,fresh.settings.onboarding),
       onboardingTasks:changed(previous.settings.onboarding?.tasks,fresh.settings.onboarding?.tasks),
       printingBefore:previous.settings.onboarding?.tasks?.printing??null,printingAfter:fresh.settings.onboarding?.tasks?.printing??null});
      return allowed;
     };
    });
    const initialSetup=await source.evaluate(()=>({completed:state.settings.onboarding?.completed,printing:state.settings.onboarding?.tasks?.printing??null,sides:Object.keys(state.settings.print_profiles||{})}));
    assert.equal(initialSetup.completed,true,'Fixture setup guide already completed');
    assert.equal(initialSetup.printing,null,'Printing task must start unfinished in each browser');
    assert.deepEqual(initialSetup.sides,[],'Fixture starts without saved print profiles');
    for(const {side,remember,completesPrinting,x} of [
     {side:'front',remember:true,completesPrinting:false,x:'1.5'},
     {side:'back',remember:false,completesPrinting:false,x:'1.5'},
     {side:'back',remember:true,completesPrinting:true,x:'1.5'},
     {side:'back',remember:true,completesPrinting:false,x:'2.5'}
    ]){
     step='card '+side+' print and return (remember='+remember+', onboarding='+completesPrinting+')';
     const beforeOnboarding=await source.evaluate(()=>JSON.parse(JSON.stringify(state.settings.onboarding)));
     const expectedOnboarding=JSON.parse(JSON.stringify(beforeOnboarding));
     if(completesPrinting){
      assert.notEqual(beforeOnboarding.tasks?.printing,'done',step+' task must not already be complete');
      expectedOnboarding.tasks={...expectedOnboarding.tasks,printing:'done'};
     }
     await source.evaluate(({id,side,remember,x})=>{
      window.profileReceiptChecks=[];page='Distrikter';selected=id;render();printOptions(id,side);
      const form=el('printForm');form.elements.remember.checked=remember;window.originTerritory=el('app').firstElementChild;
      form.querySelector('details').open=true;form.elements.x.value=x;form.elements.x.focus();el('dialog').scrollTop=remember?80:0;
      window.originForm=form;window.originScroll=el('dialog').scrollTop;window.originCard=selected;window.job=printCard(form);
     },{id:fixture.cards[0],side,remember,x});
     await frame.locator('.sheet').first().waitFor();
     await source.evaluate(()=>window.job);
     await source.waitForFunction(()=>!el('printForm')?.dataset.printing);
     const receipt=await source.evaluate(({side,remember,x})=>({checks:window.profileReceiptChecks,saved:!remember||state.settings.print_profiles?.[side]?.x===Number(x)}),{side,remember,x});
     console.log(name+' '+step+' receipt: '+JSON.stringify(receipt));
     await printAndReturn('#print',side==='front');
     const restored=await source.evaluate(remember=>({
      sameForm:el('printForm')===window.originForm,
      inputX:el('printForm')?.elements.x.value,
      dialogOpen:el('dialog').open,
      selectedCard:selected===window.originCard,
      scroll:{before:window.originScroll,after:el('dialog').scrollTop},
      sameAppRoot:el('app').firstElementChild===window.originTerritory,
      detailsOpen:!!el('printForm')?.querySelector('details')?.open,
      remember:el('printForm')?.elements.remember.checked===remember,
      focus:document.activeElement===el('printForm')?.elements.x
     }),remember);
     console.log(name+' '+step+' restored: '+JSON.stringify(restored));
     assert.equal(receipt.checks.length,remember?1:0,step+' receipt count');
     if(remember){
      const check=receipt.checks[0];
      assert.equal(check.allowed,!completesPrinting,step+' profile-only classification');
      assert.deepEqual([...check.settings].sort(),completesPrinting?['onboarding','print_profiles']:['print_profiles'],step+' exact settings changes');
      assert.deepEqual(check.onboardingFields,completesPrinting?['tasks']:[],step+' onboarding fields');
      assert.deepEqual(check.onboardingTasks,completesPrinting?['printing']:[],step+' onboarding task changes');
      assert.equal(check.printingBefore,beforeOnboarding.tasks?.printing??null,step+' prior printing status');
      assert.equal(check.printingAfter,expectedOnboarding.tasks?.printing??null,step+' new printing status');
      assert.ok(check.topLevel.every(k=>['revision','settings','dashboard_summary','report_summary','profile'].includes(k)),step+' no unrelated state changes');
      assert.ok(check.profile.every(k=>k==='snapshot'),step+' no authorization changes');
      assert.ok(check.dashboardSummary.every(k=>k==='revision')&&check.reportSummary.every(k=>k==='revision'),step+' no aggregate changes');
      assert.equal(check.runtimeChanged,false,step+' no runtime status changes');
     }
     assert.equal(receipt.saved,true,step+' confirmed profile value');
     assert.equal(restored.sameAppRoot,!completesPrinting,step+' app root follows the actual state change');
     for(const key of ['sameForm','dialogOpen','selectedCard','detailsOpen','remember','focus'])assert.equal(restored[key],true,step+' '+key);
     assert.equal(restored.inputX,x,step+' input x');
     assert.equal(restored.scroll.after,restored.scroll.before,step+' scroll position');
     assert.deepEqual(await source.evaluate(()=>state.settings.onboarding),expectedOnboarding,step+' live onboarding status preserved');
     if(remember){
      const persisted=await source.evaluate(async side=>{const fresh=await(await api('/api/state')).json();return {onboarding:fresh.settings.onboarding,x:fresh.settings.print_profiles?.[side]?.x};},side);
      assert.deepEqual(persisted.onboarding,expectedOnboarding,step+' server onboarding status');
      assert.equal(persisted.x,Number(x),step+' server print profile');
     }
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
     el('dialog').scrollTop=0;window.cardDraftBefore.scroll=el('dialog').scrollTop;
     window.job=printIBOverview([{card_id:id,road:'Fiktiv vej',number:'9',date:'2026-10-01'}]);
    },fixture.cards[0]);
    await printAndReturn('#printIBOverview',true);
    await source.evaluate(()=>window.job);
    const ibRestored=await source.evaluate(()=>{
     const b=window.cardDraftBefore;
     return {page:page==='Distrikter',selected:selected===b.selected,query:query===b.query,area:area===b.area,status:status===b.status,view:view===b.view,
      sameAppRoot:el('app').firstElementChild===b.app,dialogOpen:el('dialog').open,sameForm:el('cardForm')===b.form,
      draft:b.input.value==='FIKTIV USENDT KORTKLADDE',stored:card(selected)?.name===b.stored,dirty:dialogDirty,
      focus:document.activeElement===b.input,selection:b.input.selectionStart===2&&b.input.selectionEnd===8,
      scroll:{before:b.scroll,after:el('dialog').scrollTop}};
    });
    console.log(name+' IB restored: '+JSON.stringify(ibRestored));
    for(const [key,value] of Object.entries(ibRestored))if(key!=='scroll')assert.equal(value,true,'IB draft restoration: '+key);
    assert.equal(ibRestored.scroll.after,ibRestored.scroll.before,'IB draft scroll');
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
 }finally{child.kill();}
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
