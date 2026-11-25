'use strict';
// Real disposable server, fictional records, and held HTTP receipts. No user data.
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
(async()=>{
 for(const profiles of [false,true]){
  const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
  try{
   const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});});
   browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
   const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],writes=[];let hold;
   const waitForReceipt=async gate=>{let timer;try{await Promise.race([gate.arrived.promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('No '+gate.action+' receipt: '+errors.join('; '))),10000);})]);}finally{clearTimeout(timer);}};
   const holdNext=(action,mode='success')=>{assert.ok(!hold);hold={action,mode,arrived:deferred(),release:deferred()};return hold;};
   page.on('pageerror',e=>errors.push(e.message));page.on('dialog',dialog=>dialog.dismiss());
   await page.addInitScript(()=>localStorage.setItem('ltm-language','da'));
   await page.route('**/*',async route=>{
    const request=route.request(),url=new URL(request.url());
    if(url.origin!==fixture.origin){assert.equal(url.hostname,'tile.openstreetmap.org');return route.abort();}
    const body=request.method()==='POST'&&url.pathname==='/api/mutate'?request.postDataJSON():null;
    if(body)writes.push(body);
    if(body&&hold?.action===body.action){
     const gate=hold;hold=null;
     // Success/lost responses reach the real server first. Rejection does not.
     const response=['reject','login'].includes(gate.mode)?null:await route.fetch();gate.arrived.resolve();await gate.release.promise;
     if(gate.mode==='login')return route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({error:'Fiktivt udløbet login'})});
      if(gate.mode==='reject')return route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:'Fiktiv afvisning'})});
     if(gate.mode==='lost')return route.abort('connectionreset');
     if(gate.mode==='invalid')return route.fulfill({status:200,contentType:'application/json',body:'{}'});
     return route.fulfill({response});
    }
    return route.continue();
   });
   await page.goto(fixture.origin);await page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
   if(profiles){
    await page.evaluate(()=>api('/api/profiles/activate',{name:'Fiktiv admin',password:'Fiktiv-password-123',confirmation:'AKTIVÉR PROFILER'}));
    await page.reload();await page.locator('#loginName').fill('Fiktiv admin');await page.locator('#loginPassword').fill('Fiktiv-password-123');await page.locator('#loginForm button').click();
    await page.waitForFunction(()=>typeof state!=='undefined'&&state?.profile&&SaveStatus.kind==='saved');
    
   }
   const ids=await page.evaluate(async()=>{
    const person=await mutate('publisher.save',{name:'Fiktiv person',group:'Fiktiv gruppe'});
    const loan=await mutate('loan.issue',{card_id:state.cards[0].id,publisher_id:person.id,date:state.today,initial:true});
    await mutate('geo.manual',{road:'Fiktivvej',number:'1',postcode:'9999',lng:10.002,lat:55.002,count:1});
    await mutate('geo.manual',{road:'Fiktivvej',number:'2',postcode:'9999',lng:10.003,lat:55.003,count:1});
    return {card:state.cards[0].id,person:person.id,loan:loan.id,addresses:GeoUI.addresses().map(a=>a.id)};
   });
   // The modal releases on submit; navigation uses real clickable navigation.
   let gate=holdNext('loan.finish');await page.evaluate(id=>finish(id,false),ids.loan);
   assert.equal(await page.locator('#finishForm input[name=revise_ib]').isChecked(),false);await page.locator('#finishForm button.primary').click();await waitForReceipt(gate);
   assert.equal(await page.evaluate(()=>SaveStatus.kind),'saving');assert.equal(await page.locator('#dialog').evaluate(n=>n.matches(':modal')),false);
   await page.locator('#finishForm').evaluate(f=>f.requestSubmit());assert.equal(writes.filter(w=>w.action==='loan.finish').length,1);
   await page.locator('[data-navigation="1:2"]').click();await page.evaluate(()=>editPublisher(''));await page.locator('#publisherForm input[name=name]').fill('Ny fiktiv kladde');
   const generation=await page.evaluate(()=>openDialog.generation);gate.release.resolve();await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='saved');
   assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),'Ny fiktiv kladde');assert.equal(await page.evaluate(()=>openDialog.generation),generation);assert.equal(await page.locator('#dialog').evaluate(n=>n.matches(':modal')),true);
   assert.equal(await page.evaluate(id=>!!state.loans.find(l=>l.id===id).returned,ids.loan),true);await page.locator('#dialog .dialogClose').click();
   // LTM #25: add/edit/delete consecutively on the same card's IB back.
   await page.locator('[data-navigation="1:0"]').click();
   await page.evaluate(id=>detail(id,'IB-bagside'),ids.card);
   const backTab=page.locator('#dialog [data-action=card-tab][data-tab="IB-bagside"].active');
   const waitBack=async()=>{await backTab.waitFor();await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='saved');assert.equal(await backTab.getAttribute('data-id'),ids.card);};
   const addIB=async(number)=>{await page.locator('#dialog [data-action=ib][data-card]').click();await page.locator('#ibForm [name=road]').fill('Fiktiv IB vej');await page.locator('#ibForm [name=number]').fill(number);await page.locator('#ibForm button.primary').click();await waitBack();};
   await page.locator('#dialog .backPreview').evaluate(n=>{n.open=true;});
   await addIB('91');
   assert.equal(await page.locator('#dialog .backPreview').evaluate(n=>n.open),true);
   const ibId=await page.evaluate(id=>state.ib.find(i=>i.card_id===id&&i.number==='91').id,ids.card);
   const editIBRow=page.locator('#dialog [data-action=ib][data-id="'+ibId+'"]');
   await editIBRow.focus();await editIBRow.click();
   await page.locator('#ibForm [name=number]').fill('92');await page.locator('#ibForm button.primary').click();await waitBack();
   assert.equal(await page.evaluate(id=>state.ib.find(i=>i.id===id).number,ibId),'92');
   assert.equal(await editIBRow.evaluate(n=>n===document.activeElement),true,'return focus to the edited IB row');
   await page.locator('#dialog [data-action=delete][data-module=ib][data-id="'+ibId+'"]').click();
   await page.locator('#dialog [data-action=confirm-delete]').click();await waitBack();
   assert.equal(await page.evaluate(id=>state.ib.some(i=>i.id===id),ibId),false);
   assert.equal(await page.locator('#dialog [data-action=ib][data-id="'+ibId+'"]').count(),0);
   // No-op edit returns without sending a write; rejected and lost receipts retain the editor.
   await addIB('93');
   const retainedId=await page.evaluate(id=>state.ib.find(i=>i.card_id===id&&i.number==='93').id,ids.card);
   const openRetained=()=>page.locator('#dialog [data-action=ib][data-id="'+retainedId+'"]').click();
   await openRetained();let ibWrites=writes.length;
   await page.locator('#ibForm button.primary').click();await backTab.waitFor();
   assert.equal(writes.length,ibWrites);
   for(const mode of ['reject','lost']){
    await openRetained();gate=holdNext('ib.save',mode);
    await page.locator('#ibForm [name=number]').fill(mode==='reject'?'94':'95');
    await page.locator('#ibForm button.primary').click();await waitForReceipt(gate);gate.release.resolve();
    await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='error');
    assert.equal(await page.locator('#ibForm [name=number]').inputValue(),mode==='reject'?'94':'95');
    assert.equal(await page.evaluate(()=>WriteGuard.uncertain),mode==='lost');
    if(mode==='lost'){
     ibWrites=writes.length;await page.locator('#ibForm button.primary').click();
     await page.waitForFunction(()=>PendingSaves.count===0);assert.equal(writes.length,ibWrites,'unknown outcome must not replay');
    }
    await page.evaluate(()=>{closeDialog();});await page.evaluate(()=>Workspace.handle('refresh',{}));
    await page.waitForFunction(()=>!WriteGuard.uncertain&&!WriteGuard.needsReview);
    await page.evaluate(id=>detail(id,'IB-bagside'),ids.card);
   }
   // A successful receipt after navigation cannot reopen the old card or replace a newer form.
   await openRetained();gate=holdNext('ib.save');
   await page.locator('#ibForm [name=number]').fill('96');await page.locator('#ibForm button.primary').click();await waitForReceipt(gate);
   await page.locator('[data-navigation="1:2"]').click();await page.evaluate(()=>editPublisher(''));
   await page.locator('#publisherForm input[name=name]').fill('Fiktiv nyere IB navigation');
   const ibGeneration=await page.evaluate(()=>openDialog.generation);gate.release.resolve();
   await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='saved');
   assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),'Fiktiv nyere IB navigation');
   assert.equal(await page.evaluate(()=>openDialog.generation),ibGeneration);
   assert.equal(await page.evaluate(id=>state.ib.find(i=>i.id===id).number,retainedId),'96');
   await page.locator('#dialog .dialogClose').click();
   // A delete receipt must also respect explicit close, even without a replacement dialog.
   await page.evaluate(id=>detail(id,'IB-bagside'),ids.card);
   await page.locator('#dialog [data-action=delete][data-module=ib][data-id="'+retainedId+'"]').click();
   gate=holdNext('delete');await page.locator('#dialog [data-action=confirm-delete]').click();await waitForReceipt(gate);
   await page.locator('#dialog .dialogClose').click();gate.release.resolve();
   await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='saved');
   assert.equal(await page.evaluate(()=>el('dialog').open),false);
   assert.equal(await page.evaluate(id=>state.ib.some(i=>i.id===id),retainedId),false);
   console.log('PASS IB back: consecutive add/edit/delete, preview/focus, no-op, lost/rejected receipt, no replay, newer navigation and explicit close');
   // Autosave captures the latest edit on navigation, without waiting for receipt 1.
   gate=holdNext('card.save');await page.evaluate(id=>editCard(id),ids.card);
   await page.locator('#cardForm details').first().evaluate(details=>{details.open=true;});
   // Use the real manual street-line input: closing/reopening a dialog during
   // autosave used to move its caret to the district number at the top.
   await page.evaluate(()=>el('addressRows').insertAdjacentHTML('beforeend',addressRow({road:'Opdigtetvej',numbers:'1',count:1,count_unknown:false,type:'Hus'})));
   await page.locator('#cardForm input[name=name]').fill('Fiktiv første');
   const roadInput=page.locator('#cardForm [data-field="road"]').last();
   await roadInput.fill('Fiktivvej under redigering');
   const caretBefore=await roadInput.evaluate(node=>[node.selectionStart,node.selectionEnd]);
   // Releasing the modal during autosave must neither scroll the page nor
   // reset a long card editor's internal scroll position.
   const scrollBefore=await page.evaluate(()=>{
    document.body.style.minHeight='2400px';
    const dialog=el('dialog');
    dialog.scrollTop=Math.min(160,dialog.scrollHeight-dialog.clientHeight);
    window.scrollTo({left:0,top:0,behavior:'instant'});
    return [window.scrollY,dialog.scrollTop];
   });
   assert.ok(scrollBefore[1]>0,'test requires a scrollable card editor');
   await page.evaluate(()=>{void saveCard(false);});await waitForReceipt(gate);
   assert.deepEqual(await page.evaluate(()=>[window.scrollY,el('dialog').scrollTop]),scrollBefore,'background save must not jump either scroll position');
   assert.equal(await roadInput.evaluate(node=>document.activeElement===node),true,'the street-line field must retain focus during background save');
   assert.deepEqual(await roadInput.evaluate(node=>[node.selectionStart,node.selectionEnd]),caretBefore,'autosave must preserve the text caret');
   await page.locator('#cardForm input[name=name]').fill('Fiktiv nyeste');await page.locator('[data-navigation="1:2"]').click();
   assert.equal(await page.evaluate(()=>page),'Forkyndere');assert.equal(await page.evaluate(()=>PendingSaves.count),2);gate.release.resolve();
   await page.waitForFunction(()=>PendingSaves.count===0);assert.equal(await page.evaluate(id=>card(id).name,ids.card),'Fiktiv nyeste');
   // A late receipt must not replace a page-level settings draft or its base.
   gate=holdNext('card.save');await page.evaluate(id=>{void mutate('card.save',{...card(id),name:'Fiktiv baggrund'},{close:false});},ids.card);await waitForReceipt(gate);
   await page.locator('[data-navigation="2:2"]').click();await page.locator('#settingsForm input[name=congregation]').fill('Fiktiv NY KLADDE');
   await page.evaluate(()=>EditorBases.page?.ready);assert.equal(await page.evaluate(()=>EditorBases.page?.error?.message||null),null);
   const settingsBase=await page.evaluate(()=>EditorBases.page?.base);gate.release.resolve();await page.waitForFunction(()=>PendingSaves.count===0);
    const settingsDraftWrites=writes.length;await page.evaluate(()=>Workspace.handle('refresh',{}));assert.equal(await page.locator('#settingsForm input[name=congregation]').inputValue(),'Fiktiv NY KLADDE');assert.equal(writes.length,settingsDraftWrites);
   assert.equal(await page.locator('#settingsForm input[name=congregation]').inputValue(),'Fiktiv NY KLADDE');assert.equal(await page.evaluate(()=>EditorBases.page?.base),settingsBase);assert.equal(await page.evaluate(()=>SaveStatus.kind),'saved');
   // Geo preview gates stay intact; only an enqueued geographic write can leave.
   await page.evaluate(id=>{GeoUI.dirty=false;GeoUI.openCard(id);GeoUI.ids=new Set(GeoUI.addresses().map(a=>a.id));GeoUI.polygon=[[10,55],[10.01,55],[10.01,55.01],[10,55.01]];GeoUI.dirty=true;GeoUI.drawLayers();GeoUI.updatePanel();},ids.card);
   gate=holdNext('geo.assign');await page.evaluate(()=>{void GeoUI.save();});await waitForReceipt(gate);
   assert.equal(await page.evaluate(()=>GeoUI.canLeave()),true);await page.locator('[data-navigation="1:0"]').click();assert.equal(await page.evaluate(()=>page),'Distrikter');
   await page.evaluate(id=>{GeoUI.openCard(id);GeoUI.ids=new Set([GeoUI.addresses()[0].id]);GeoUI.dirty=true;},ids.card);
   const geoStamp=await page.evaluate(()=>GeoUI.draftStamp(false));gate.release.resolve();await page.waitForFunction(()=>PendingSaves.count===0&&!GeoUI.saveBusy);
   assert.equal(await page.evaluate(()=>GeoUI.draftStamp(false)),geoStamp);assert.equal(await page.evaluate(()=>GeoUI.dirty),true);assert.equal(await page.evaluate(id=>card(id).address_ids.length,ids.card),2);
   // Outdated geo check failures disappear when starting a fresh drawing or
   // changing the card, even if the previous request completes late.
   await page.evaluate(()=>{GeoUI.dirty=false;GeoUI.notice='Kontrollen tog for lang tid.';GeoUI.jobNoticeEpoch=GeoUI.noticeEpoch;GeoUI.showJob({status:'error',message:GeoUI.notice});GeoUI.updatePanel();});
   assert.equal(await page.locator('#geoDownloadStatus').isVisible(),true);
   await page.evaluate(()=>GeoUI.handle('draw'));
   assert.equal(await page.locator('#geoDownloadStatus').isVisible(),false);
   assert.equal(await page.evaluate(()=>GeoUI.notice),'');
   await page.evaluate(id=>{GeoUI.notice='Gammel kontrol';GeoUI.jobNoticeEpoch=GeoUI.noticeEpoch;GeoUI.showJob({status:'error',message:GeoUI.notice});GeoUI.dirty=false;GeoUI.openCard(id);},ids.card);
   assert.equal(await page.locator('#geoDownloadStatus').isVisible(),false);
   await page.evaluate(()=>{GeoUI.showJob({status:'error',message:'Forsinket gammelt svar'});});
   assert.equal(await page.locator('#geoDownloadStatus').isVisible(),false);
   // Unsubmitted new geographic edits still need the discard decision (dismissed).
   assert.equal(await page.evaluate(()=>GeoUI.canLeave()),true);await page.evaluate(()=>{GeoUI.dirty=false;page='Forkyndere';render();});
   // A real independently owned profile edit still conflicts with a stale form.
   if(profiles){
    await page.evaluate(id=>editPublisher(id),ids.person);await page.evaluate(()=>EditorBases.current.ready);
    await page.evaluate(async id=>{const fresh=await(await api('/api/state')).json();await api('/api/mutate',{action:'publisher.save',data:{id,name:'Fiktiv ekstern ændring'},profile_snapshot:fresh.profile.snapshot});},ids.person);
    await page.locator('#publisherForm input[name=name]').fill('Fiktiv gammel base');await page.locator('#publisherForm button.primary').click();await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='saved');
    const reviews=await page.evaluate(async()=>{const data=await(await api('/api/profiles/conflicts')).json();return Array.isArray(data)?data:data.rows;});
    const conflict=reviews.find(row=>row.module==='publishers'&&row.field==='name');
    assert.ok(conflict,'Concurrent changes must be recorded for review');assert.deepEqual([conflict.base.value,conflict.saved.value,conflict.incoming.value],['Fiktiv person','Fiktiv ekstern ændring','Fiktiv gammel base']);
   }
   for(const mode of ['reject','lost','invalid']){
    gate=holdNext('publisher.save',mode);await page.evaluate(()=>editPublisher(''));await page.locator('#publisherForm input[name=name]').fill('Fiktiv '+mode);await page.locator('#publisherForm button.primary').click();await waitForReceipt(gate);
    await page.locator('[data-navigation="1:0"]').click();await page.evaluate(()=>editPublisher(''));await page.locator('#publisherForm input[name=name]').fill('Bevar ny fiktiv kladde');
    gate.release.resolve();await page.waitForFunction(()=>PendingSaves.count===0&&SaveStatus.kind==='error');
    assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),'Bevar ny fiktiv kladde');
    assert.equal(await page.evaluate(()=>WriteGuard.uncertain),mode!=='reject');
    if(mode!=='reject'){
     const count=writes.length;await page.locator('#publisherForm button.primary').click();await page.waitForFunction(()=>PendingSaves.count===0);assert.equal(writes.length,count,'Uncertain writes cannot replay');
    }
    // Read-only connection check and refused refresh must preserve the draft and guard.
     const draftWrites=writes.length;await page.evaluate(()=>Workspace.checkConnection(true));await page.evaluate(()=>Workspace.handle('refresh',{}));assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),'Bevar ny fiktiv kladde');assert.equal(writes.length,draftWrites);assert.equal(await page.evaluate(()=>WriteGuard.uncertain),mode!=='reject');
     // Dismiss the explicit discard warning, then refresh after closing deliberately.
    await page.evaluate(()=>{dialogDirty=false;closeDialog();});await page.evaluate(()=>Workspace.handle('refresh',{}));
   }
   // Confirmed write / stale overview and expired login have different guidance.
    await page.evaluate(async()=>{try{await confirmedWrite('/api/mutate',{action:'publisher.save',data:{name:'Fiktiv bekræftet, forældet oversigt'}},async()=>{throw Error('Fiktiv opdateringsfejl');});}catch{}});
    assert.equal(await page.evaluate(()=>WriteGuard.needsReview),true);assert.equal(await page.evaluate(()=>WriteGuard.uncertain),false);assert.match(await page.evaluate(()=>SaveStatus.guidance),/Send den ikke igen/);
    await page.evaluate(()=>Workspace.handle('refresh',{}));assert.equal(await page.evaluate(()=>WriteGuard.needsReview),false);
    gate=holdNext('publisher.save','login');await page.evaluate(()=>editPublisher(''));await page.locator('#publisherForm input[name=name]').fill('Fiktiv loginkladde');await page.locator('#publisherForm button.primary').click();await waitForReceipt(gate);gate.release.resolve();
    await page.waitForFunction(()=>PendingSaves.count===0&&WriteGuard.loginExpired);assert.equal(await page.evaluate(()=>WriteGuard.uncertain),false);assert.match(await page.evaluate(()=>SaveStatus.guidance),/logger ind igen/);
    const loginWrites=writes.length;await page.evaluate(()=>Workspace.checkConnection(true));await page.evaluate(()=>Workspace.handle('refresh',{}));assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),'Fiktiv loginkladde');assert.equal(writes.length,loginWrites);assert.equal(await page.evaluate(()=>WriteGuard.loginExpired),true);
    await page.evaluate(()=>{dialogDirty=false;closeDialog();});await page.evaluate(()=>Workspace.handle('refresh',{}));assert.equal(await page.evaluate(()=>WriteGuard.loginExpired),false);
    // LTM #4: verify the actual dialog indicator against held write receipts.
   for(const [device,width,height] of [['mobile',390,844],['iPad',820,1180],['desktop',1440,1000]]){
    await page.setViewportSize({width,height});
    for(const mode of ['success','reject','lost','invalid']){
     await page.emulateMedia({reducedMotion:'no-preference'});
     const name='Fiktiv indikator '+device+' '+mode;
     gate=holdNext('publisher.save',mode);
     await page.evaluate(()=>editPublisher(''));
     await page.locator('#publisherForm input[name=name]').fill(name);
     await page.locator('#publisherForm button.primary').click();await waitForReceipt(gate);
     const progress=page.locator('#dialog [data-save-progress]');
     await progress.waitFor({state:'visible'});
     assert.equal(await progress.count(),1);
     assert.equal(await progress.getAttribute('role'),'status');
     assert.equal(await progress.textContent(),'Gemmer…');
     const measure=()=>progress.evaluate(node=>{
      const rect=node.getBoundingClientRect(),style=getComputedStyle(node),icon=getComputedStyle(node,'::before');
      return {x:rect.x+rect.width/2,y:rect.y+rect.height/2,width:rect.width,left:rect.left,right:rect.right,viewportWidth:innerWidth,viewportHeight:innerHeight,font:parseFloat(style.fontSize),icon:parseFloat(icon.width),animation:icon.animationName,pointerEvents:style.pointerEvents};
     });
     const view=await measure();
     assert.ok(Math.abs(view.x-view.viewportWidth/2)<=2&&Math.abs(view.y-view.viewportHeight/2)<=2,device+' indicator is not centered: '+JSON.stringify(view));
     assert.ok(view.left>=0&&view.right<=view.viewportWidth&&view.font>=20&&view.icon>=32,device+' indicator sizing');
     assert.equal(view.animation,'dialog-save-spinner');assert.equal(view.pointerEvents,'none');
     await page.emulateMedia({reducedMotion:'reduce'});
     assert.equal((await measure()).animation,'none');
     assert.equal(await progress.isVisible(),true,'reduced motion must keep the indicator visible');
     gate.release.resolve();
     await page.waitForFunction(mode=>PendingSaves.count===0&&SaveStatus.kind===(mode==='success'?'saved':'error'),mode);
     assert.equal(await progress.count(),0,device+' must remove completed indicator ('+mode+')');
     if(mode==='success'){
      assert.equal(await page.evaluate(()=>el('dialog').open),false);
      assert.equal(await page.evaluate(name=>state.publishers.some(p=>p.name===name),name),true);
     }else{
      assert.equal(await page.locator('#publisherForm input[name=name]').inputValue(),name);
      assert.equal(await page.evaluate(()=>SaveStatus.message),mode==='reject'?'Ændringen blev afvist':'Gemning er ikke bekræftet');
      assert.equal(await page.evaluate(()=>WriteGuard.uncertain),mode!=='reject');
      if(mode!=='reject'){
       const count=writes.length;
       await page.locator('#publisherForm button.primary').click();
       await page.waitForFunction(()=>PendingSaves.count===0);
       assert.equal(writes.length,count,'uncertain result must not replay');
      }
      await page.evaluate(()=>{dialogDirty=false;closeDialog();});
      await page.evaluate(()=>Workspace.handle('refresh',{}));
      await page.waitForFunction(()=>!WriteGuard.uncertain&&!WriteGuard.needsReview&&PendingSaves.count===0);
     }
    }
   }
   await page.emulateMedia({reducedMotion:'no-preference'});
   console.log('PASS save indicator: mobile, iPad and desktop sizes; success, rejection, lost/invalid receipt; reduced motion');
   assert.deepEqual(errors,[]);console.log('PASS delayed return, duplicate submit, navigation, newest autosave, settings/geo drafts, profile conflict evidence, rejection/lost/invalid receipts ('+(profiles?'profiles':'shared login')+')');
  }finally{if(browser)await browser.close();child.kill();}
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
