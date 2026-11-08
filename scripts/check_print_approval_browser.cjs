// Canonical print and Drive snapshot parity, plus explicit multi-side approval.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
module.exports=async(browser,out)=>{
 const root=path.resolve(__dirname,'../distrikt/app'),state={revision:'fictional',today:'2026-11-07',cards:[101,102].map(n=>({id:'c'+n,number:String(n),name:'Fiktivt område',addresses:[{road:'Fiktiv prøvevej med ekstra lang vejtekst til kontrol af ombrydning',numbers:'2–8',count:4},{road:'Anden vej',numbers:'1, 3, 5',count:3}],front_revision:true,back_revision:true,front_print_token:'front'+n,back_print_token:'back'+n})),ib:[],areas:[],public_maps:[],settings:{onboarding:{completed:true}},publishers:[],loans:[],completions:[],ignored:[],notes:[],tasks:[],visits:[],maps:[],recovery:[]};
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
 try{
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url());assert.equal(u.hostname,'ltm.print.test');
   const json=v=>route.fulfill({contentType:'application/json',body:JSON.stringify(v)});
   if(u.pathname==='/api/state')return json(state);
   if(u.pathname==='/api/geo')return json({addresses:[],roads:[],buildings:[],info:{},status:{},main_boundary:{points:[]}});
   if(u.pathname==='/api/ping')return json({ok:true});
   if(u.pathname==='/api/share/status')return json({connected:false,cards:[]});
   if(u.pathname.startsWith('/api/'))return json({});
   if(u.pathname==='/s12-template.png')return route.fulfill({path:path.resolve(root,'../templates/S-12-source.png')});
   if(u.pathname==='/s12-template-en.png')return route.fulfill({path:path.resolve(root,'../templates/S-12-E-source.png')});
   const file=path.resolve(root,u.pathname==='/'?'index.html':'.'+u.pathname);assert.ok(file.startsWith(root+path.sep));
   if(fs.existsSync(file))return route.fulfill({path:file,headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}});
   return route.fulfill({status:404,body:''});
  });
  await page.goto('http://ltm.print.test/');await page.waitForFunction(()=>state!==null);
  for(const language of ['da','en']){
   // Draw the exact same card and profile in normal print and the Drive renderer.
   await page.evaluate(language=>{I18n.set(language);state.settings.print_profiles={front:{...defaultPrintProfile('front'),mode:'full',form_language:language}};window.lastFrontSvg='';const raster=MapExport.raster;MapExport.raster=function(svg){window.lastFrontSvg=svg;return raster.call(this,svg);};},language);
   const result=await page.evaluate(async()=>{
    const c=state.cards[0],cfg=state.settings.print_profiles.front;
    const blob=await printFrontImage(c),data=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(blob);});
    const svg=new DOMParser().parseFromString(window.lastFrontSvg,'image/svg+xml');
    return {data,text:[...svg.querySelectorAll('text')].map(n=>n.textContent),markup:printDocument([c],'front',cfg)};
   });
   const popup=await context.newPage();await popup.setContent(result.markup);await popup.waitForFunction(()=>[...document.images].every(i=>i.complete));
   // Normal print and snapshot must contain all row content; pixel QA artifacts use both renderings.
   await popup.evaluate(await page.evaluate(()=>`(${fitFrontCard.toString()})(document.querySelector('.cardPreview'))`));
   const text=await popup.locator('.streets').innerText();for(const line of result.text.filter(t=>/besøg|visits|Total|I alt/.test(t)))assert.ok(text.includes(line));
   assert.ok(result.text.some(t=>t.includes('Fiktiv prøvevej')));assert.ok(result.text.some(t=>t.includes('2-8')));assert.ok(result.text.some(t=>t.includes('1-5')));
   if(out){fs.writeFileSync(path.join(out,'canonical-front-'+language+'.png'),Buffer.from(result.data.split(',')[1],'base64'));await popup.locator('.cardPreview').screenshot({path:path.join(out,'normal-front-'+language+'.png')});}
   await popup.close();
  }
  const lettered=await page.evaluate(async()=>{
   await printFrontImage({...state.cards[0],addresses:[{road:'Bogstavvej',numbers:'8A, 8B, 8C, 8D',count:4}]});
   return [...new DOMParser().parseFromString(window.lastFrontSvg,'image/svg+xml').querySelectorAll('text')].map(n=>n.textContent).join(' ');
  });
  assert.match(lettered,/Bogstavvej 8A-8D/);assert.doesNotMatch(lettered,/&amp;|8A & 8B/);
  const encrypted=await page.evaluate(async()=>{
   if(globalThis.isSecureContext)throw Error('HTTP fixture must exercise browser fallback');
   const input={schema:1,connections:{adressevaelger:{token:'FIKTIVT'}}};
   const file=await ConnectionBackupUI.encrypt(input,'Fiktiv adgangskode 123');
   const output=await ConnectionBackupUI.decrypt(new File([JSON.stringify(file)],'fiktiv.json'),'Fiktiv adgangskode 123');
   return JSON.stringify(output)===JSON.stringify(input);
  });assert.equal(encrypted,true);
  await page.evaluate(()=>{closeDialog();page='Distrikter';window.approvalWrites=[];mutate=async(action,data)=>{window.approvalWrites.push({action,data});};});
  for(const side of ['front','back']){
   await page.evaluate(side=>printOptions(state.cards[0].id,side,state.cards.map(c=>c.id)),side);
   await page.locator('[name=remember]').uncheck();const promise=page.waitForEvent('popup');await page.locator('#printForm').evaluate(form=>printCard(form));const popup=await promise;
   await popup.waitForFunction(()=>document.getElementById('print')&&!document.getElementById('print').disabled);
   assert.equal(await page.evaluate(()=>PrintApprovals.entries.size),side==='front'?0:2,'Preview does not approve or register a print');
   assert.equal(await popup.locator('#approvePrinted').isHidden(),true);
   await popup.evaluate(()=>{window.print=()=>{};});await popup.locator('#print').click();
   assert.equal(await page.evaluate(()=>window.approvalWrites.length),0,'Clicking print never approves');
   if(side==='back')await popup.locator('#approvePrinted').click();
   await popup.close();
  }
  assert.equal(await page.locator('[data-printed-index]:checked').count(),4);
  await page.locator('[data-printed-index="3"]').uncheck();await page.locator('[data-action=confirm-printed]').click();
  const writes=await page.evaluate(()=>window.approvalWrites);assert.equal(writes.length,1);assert.equal(writes[0].action,'revision.approve_many');assert.equal(writes[0].data.entries.length,3);assert.equal(await page.evaluate(()=>PrintApprovals.entries.size),1);
  // Hold the real save promise while firing rapid repeat clicks on both paths.
  await page.evaluate(()=>{window.approvalWrites=[];window.releaseApproval=null;mutate=async(action,data)=>{window.approvalWrites.push({action,data});await new Promise(resolve=>window.releaseApproval=resolve);};});
  await page.evaluate(()=>PrintApprovals.open());
  await page.locator('[data-action=confirm-printed]').evaluate(button=>{button.dispatchEvent(new MouseEvent('click',{bubbles:true}));button.dispatchEvent(new MouseEvent('click',{bubbles:true}));});
  assert.equal(await page.locator('[data-action=confirm-printed]').isEnabled(),false);
  assert.equal(await page.evaluate(()=>window.approvalWrites.length),1);
  await page.evaluate(()=>window.releaseApproval());await page.waitForFunction(()=>!PrintApprovals.busy);
  await page.evaluate(()=>{window.approvalWrites=[];});
  await page.evaluate(()=>{const button=document.createElement('button');button.dataset.action='approve';button.dataset.id='c101';button.dataset.side='front';document.body.append(button);button.click();button.remove();});
  await page.locator('[data-action=confirm-approve]').evaluate(button=>{button.dispatchEvent(new MouseEvent('click',{bubbles:true}));button.dispatchEvent(new MouseEvent('click',{bubbles:true}));});
  assert.equal(await page.locator('[data-action=confirm-approve]').isEnabled(),false);
  assert.equal(await page.evaluate(()=>window.approvalWrites.length),1);
  await page.evaluate(()=>window.releaseApproval());await page.waitForFunction(()=>PrintApprovals.singleBusy.size===0);
  assert.deepEqual(errors,[]);console.log('Canonical DA/EN front snapshots, real print popups, four-side selection, explicit confirmation, rapid repeat-click guards and no approval on preview/print passed.');
 }finally{await context.close();}
};
