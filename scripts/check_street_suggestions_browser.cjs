'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')],{stdio:['ignore','pipe','inherit']});let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{const lines=createInterface({input:child.stdout}),timer=setTimeout(()=>reject(Error('Fixture timed out')),15000);lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});child.once('exit',code=>reject(Error('Fixture exited '+code)));});
  browser=await chromium.launch({args:['--no-sandbox'],...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{})});
  const out=process.env.LTM_BROWSER_OUTPUT||'/tmp/ltm-street-suggestions';fs.mkdirSync(out,{recursive:true});
  for(const [index,language,width]of [[0,'en',390],[1,'da',1440]]){
   const context=await browser.newContext({viewport:{width,height:1000}});await context.addCookies([fixture.cookie]);await context.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='tile.openstreetmap.org')return r.abort();assert.equal(u.origin,fixture.origin);return r.continue();});
   const p=await context.newPage(),errors=[],writes=[],downloads=[];p.setDefaultTimeout(15000);p.on('pageerror',e=>errors.push(e.stack||e.message));p.on('dialog',d=>d.accept());p.on('request',r=>{if(r.url().endsWith('/api/geo/download'))downloads.push(r.url());if(r.url().endsWith('/api/mutate')&&r.method()==='POST')writes.push(r.postDataJSON());});
   await p.goto(fixture.origin);await p.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved');
   if(await p.locator('[data-profile=welcome-done]').count())await p.locator('[data-profile=welcome-done]').click();
   await p.waitForFunction(()=>PersonalGuide.data!==null);if(await p.locator('[data-personal-guide=later]').count())await p.locator('[data-personal-guide=later]').click();
   console.log('Manual Excel flow',language);
   await p.evaluate(async language=>{I18n.set(language);closeDialog();await SetupUI.open(4);},language);
   await p.locator('[data-card-import=open]').click();
   let mappingRoot;
   async function file(selector,name,data){mappingRoot=selector==='#cardImportFile'?'#cardImportMapping':'#setupIBMapping';await p.locator(selector).setInputFiles({name,mimeType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',buffer:Buffer.from(data,'base64')});await p.locator(mappingRoot+' [data-column-change=sheet], '+mappingRoot+' [data-column-change=field]').first().waitFor();const sheets=p.locator(mappingRoot+' [data-column-change=sheet]');if(await sheets.count()&&!await sheets.inputValue())await sheets.selectOption('Import');await p.locator(mappingRoot+' [data-column-change=field]').first().waitFor();}
   async function fields(keys){for(let i=0;i<keys.length;i++)await p.locator(`${mappingRoot} [data-column-change=field][data-column-index="${i}"]`).selectOption(keys[i]);}
   await file('#cardImportFile','manual-front.xlsx',fixture.fronts[index]);await fields(['card','road','number','count']);
   await p.locator(mappingRoot+' [data-column-preview]').click();await p.locator('#cardImportConfirm').waitFor();
   assert.equal(await p.evaluate(()=>state.cards.some(c=>c.number.startsWith('M'))),index>0,'Front preview does not create a card');
   await p.locator('#cardImportConfirm').fill('IMPORTÉR KORT');await p.locator('[data-card-import=apply]').click();console.log('Front submitted',language);await p.waitForFunction(number=>state.cards.some(c=>c.number===number),'M'+index);
   await p.waitForFunction(()=>!document.querySelector('#dialog').open&&SaveStatus.kind==='saved');
   const manualId=await p.evaluate(number=>state.cards.find(c=>c.number===number).id,'M'+index);
   await p.evaluate(async()=>{closeDialog();await SetupUI.open(4);});assert.equal(await p.locator('#setupIBMode').inputValue(),'manual');
   await file('#setupIBFile','manual-back.xlsx',fixture.backs[index]);await fields(['card','road','number','date']);
   await p.locator(mappingRoot+' [data-column-preview]').click();await p.locator('#setupIBConfirm').waitFor();assert.equal(await p.evaluate(()=>SetupUI.ib.errors),0);
   // Changing the linking policy invalidates an already displayed approval.
   await p.locator('#setupIBMode').selectOption('local');assert.equal(await p.locator('#setupIBConfirm').count(),0);
   await p.locator('#setupIBMode').selectOption('manual');await p.locator(mappingRoot+' [data-column-preview]').click();await p.locator('#setupIBConfirm').waitFor();
   await p.locator('#setupIBWarnings').check();await p.locator('#setupIBConfirm').fill('IMPORTÉR IB');await p.locator('[data-setup=ib-apply]').click();console.log('Back submitted',language,await p.locator('#setupError').innerText());
   await p.waitForFunction(id=>state.ib.some(i=>i.card_id===id),manualId);
   const manual=await p.evaluate(id=>({card:card(id),ib:state.ib.find(i=>i.card_id===id),front:frontHTML(card(id)),back:backHTML(card(id))}),manualId);
   assert.ok(!manual.card.address_ids?.length&&!manual.card.geo_addresses?.length);assert.ok(!manual.ib.address_id);
   assert.equal(manual.card.addresses[0].numbers,index===0?'hele vejen':'23-25 & 24-26');assert.ok(manual.front.includes(index===0?'hele vejen':'23-25 &amp; 24-26'));
   assert.equal(manual.ib.date_text,index===0?'marts 2024':'2024');assert.ok(manual.back.includes(manual.ib.date_text));assert.equal(downloads.length,0,'Front/back import needs no DAR download');
   await p.evaluate(id=>{closeDialog();openDialog(frontHTML(card(id))+backHTML(card(id)));},manualId);await p.screenshot({path:path.join(out,`manual-front-back-${language}-${width}.png`),fullPage:true});await p.evaluate(()=>closeDialog());
   // An imported manual line can be linked later to one explicit address on this card.
   const linkId='later-link-'+index;
   await p.evaluate(async({id,linkId,index})=>{await mutate('geo.import',{records:[{id:linkId,entity:'address',road:'Manual road '+index,number:index===0?'1A':'23',postcode:'9999',lng:10,lat:55,count:1,type:'Hus'}],source:'Fictional local data',label:'Explicit later address'});await mutate('geo.assign',{card_id:id,address_ids:[linkId]});const i=state.ib.find(i=>i.card_id===id);IBUI.open(i.id,id);},{id:manualId,linkId,index});
   await p.locator('#ibAddressPick').selectOption(linkId);await p.locator('#ibForm button:not([type=button])').click();
   await p.waitForFunction(({id,linkId})=>state.ib.some(i=>i.id===id&&i.address_id===linkId),{id:manual.ib.id,linkId});
   assert.equal(await p.evaluate(id=>state.ib.find(i=>i.id===id).date_text,manual.ib.id),manual.ib.date_text);
   await p.evaluate(({id,language})=>{I18n.set(language);closeDialog();GeoUI.openCard(id);},{id:fixture.cards[index],language});
   const expected=index===0?['1','3','5','7']:['23','24','25','26'];

   await p.waitForSelector('[data-geo=street-lines]');const before=await p.evaluate(id=>JSON.stringify(card(id)),fixture.cards[index]);writes.length=0;
   await p.locator('[data-geo=street-lines]').click();await p.locator('[name=postcode_0]').fill('9999');
   await p.locator('#streetSuggestionForm button:not([type=button])').click();
   await p.waitForFunction(()=>GeoUI.ids.size===4&&GeoUI.dirty&&GeoUI.streetApproval!==null);
   assert.deepEqual(await p.evaluate(()=>GeoUI.chosen().map(a=>a.number).sort()),expected);
   assert.equal(await p.evaluate(id=>JSON.stringify(card(id)),fixture.cards[index]),before,'Download and preview do not modify the card');
   assert.equal(writes.filter(w=>w.action==='geo.assign').length,0);
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await p.screenshot({path:path.join(out,`street-preview-${language}-${width}.png`),fullPage:true});
   await p.locator('#geoSelection [data-geo=save]').click();await p.locator('[data-geo=confirm-save]').click();
   await p.waitForFunction(id=>card(id).address_ids?.length===4&&SaveStatus.kind==='saved',fixture.cards[index]);
   assert.equal(writes.filter(w=>w.action==='geo.assign').length,1);assert.equal(await p.evaluate(id=>card(id).front_revision,fixture.cards[index]),true);
   for(const wording of ['2024','marts 2024']){
    await p.evaluate(id=>{closeDialog();IBUI.open(null,id);},fixture.cards[index]);
    await p.locator('#ibForm [name=road]').fill('Fictional road '+index);await p.locator('#ibForm [name=number]').fill(wording==='2024'?expected[0]:expected[1]);
    await p.locator('#ibForm [name=date_text]').fill(wording);await p.locator('#ibForm button:not([type=button])').click();
    await p.waitForFunction(({id,wording})=>state.ib.some(i=>i.card_id===id&&i.date_text===wording&&i.date===''),{id:fixture.cards[index],wording});
   }
   const text=await p.evaluate(id=>backHTML(card(id)),fixture.cards[index]);assert.ok(text.includes('marts 2024')&&text.includes('2024'));
   // Compare all IB rows, then keep one manual line and apply only the other.
   const batch=await p.evaluate(async ({id,index,numbers})=>{
    const result=[];
    for(const number of numbers){
     await mutate('ib.save',{card_id:id,road:'fictional Road '+index,number,date_text:'2025'});
     result.push(state.ib.find(i=>i.card_id===id&&i.number===number).id);
    }
    detail(id,'IB-bagside');
    return result;
   },{id:fixture.cards[index],index,numbers:expected.slice(2)});
   await p.locator('[data-ib-bulk-suggest]').click();
   const bulk=p.locator('#ibBulkForm');
   assert.deepEqual(await bulk.locator('th').allTextContents(),language==='en'?['Current address','DAR suggestion']:['Nuværende adresse','DAR-forslag']);
   assert.equal(await bulk.locator('tbody tr').count(),4);
   assert.equal(await bulk.locator('input:checked').count(),2);
   assert.ok(await p.evaluate(()=>{const dialog=document.querySelector('#dialog');return dialog.scrollWidth<=dialog.clientWidth+1;}));
   await bulk.locator(`input[value="${batch[0]}"]`).uncheck();
   assert.equal(await bulk.locator('input:checked').count(),1);
   await bulk.locator('button.primary').click();
   await p.locator('[data-ib-bulk-suggest]').waitFor();
   assert.deepEqual(await p.evaluate(ids=>ids.map(id=>{const i=state.ib.find(row=>row.id===id);return [i.road,!!i.address_id,i.date_text];}),batch),
    [['fictional Road '+index,false,'2025'],['Fictional road '+index,true,'2025']]);
   assert.equal(writes.filter(w=>w.action==='ib.bulk.apply').length,1);
   // DAR text and both free-text supplements share the same S-12 print line.
   const id=fixture.cards[index];
   await p.evaluate(id=>{closeDialog();detail(id);},id);
   await p.locator('[data-action=edit-card]').click();
   const beforeLabels=await p.evaluate(id=>JSON.stringify(card(id).geo_addresses),id);
   await p.locator('#cardForm [data-action=front-labels]').click();
   const form=p.locator('#frontLabelsForm'),row=form.locator('.frontLabelRow').first();
   const street=row.locator('[data-key=road]'),numbers=row.locator('[data-key=numbers]');
   assert.match(await row.innerText(),/DAR · Fictional road/);
   assert.equal(await street.inputValue(),'');
   assert.equal(await numbers.inputValue(),'');
   await street.fill('Side entrance');
   await numbers.fill('Gate B');
   await form.locator('button.primary').click();
   const front=p.locator('#dialog .cardPreview .streets');
   await front.waitFor();
   assert.match(await front.innerText(),/Fictional road .* – Side entrance – Gate B/);
   const streetRows=await front.locator(':scope > div > span:first-child').allTextContents();
   assert.equal(streetRows.length,1);
   assert.match(streetRows[0],index===0?/1-7 \(odd\)/:/23-25 & 24-26/);
   const printed=await p.evaluate(id=>printDocument([card(id)],'front',{...defaultPrintProfile('front'),mode:'full',form_language:I18n.language()}),id);
   assert.match(printed,/Fictional road .* – Side entrance – Gate B/);
   const image=await p.evaluate(async id=>{
    const raster=MapExport.raster;
    let labels;
    MapExport.raster=svg=>{
     labels=[...new DOMParser().parseFromString(svg,'image/svg+xml').querySelectorAll('text')].map(n=>n.textContent);
     return raster.call(MapExport,svg);
    };
    try{
     const blob=await printFrontImage(card(id),{profile:{form_language:I18n.language()}});
     return {type:blob.type,labels:labels.join(' ')};
    }finally{MapExport.raster=raster;}
   },id);
   assert.equal(image.type,'image/png');
   assert.match(image.labels,/Fictional road .* – Side entrance – Gate B/);
   assert.equal(await p.evaluate(id=>JSON.stringify(card(id).geo_addresses),id),beforeLabels);
   await p.reload();
   await p.waitForFunction(id=>state?.cards?.some(c=>c.id===id&&c.front_addresses?.[0]?.extra_numbers==='Gate B'),id);
   await p.evaluate(id=>detail(id),id);
   await p.locator('#dialog [data-action=front-labels]').click();
   assert.equal(await street.inputValue(),'Side entrance');
   assert.equal(await numbers.inputValue(),'Gate B');
   await street.fill('');
   await form.locator('button.primary').click();
   await front.waitFor();
   assert.match(await front.innerText(),/Fictional road .* – Gate B/);
   assert.doesNotMatch(await front.innerText(),/Side entrance/);
   await p.locator('#dialog [data-action=front-labels]').click();
   await row.locator('[data-front-reset]').click();
   await form.locator('button.primary').click();
   await front.waitFor();
   assert.match(await front.innerText(),/Fictional road/);
   assert.doesNotMatch(await front.innerText(),/Gate B/);
   assert.deepEqual(errors,[]);await context.close();
  }
  console.log(JSON.stringify({ok:true,real_server:true,languages:['en','da'],widths:[390,1440],preview_without_card_write:true,one_confirmed_save:true,manual_excel_front_and_back_without_dar:true,explicit_later_link:true,manual_year_and_month_year_preserved:true}));
 }finally{if(browser)await browser.close();child.kill('SIGTERM');}
})().catch(error=>{console.error(error);process.exitCode=1;});
