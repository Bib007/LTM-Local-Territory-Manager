'use strict';
// Exercise the installed app, never real user data. Both engines use a disposable fixture.
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process'),{createInterface}=require('node:readline');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/profiles_server.py')],{stdio:['ignore','pipe','inherit']});
 try{
  const fixture=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Fixture timeout')),15000);createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line));});});
  for(const [engine,touch] of [[chromium,false],[webkit,true]]){
   const browser=await engine.launch(touch?{}:{args:['--no-sandbox']});
   try{
    const context=await browser.newContext({viewport:touch?{width:1024,height:1366}:{width:1440,height:1000},hasTouch:touch,isMobile:touch});
    const page=await context.newPage(),errors=[],writes=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>localStorage.setItem('ltm-language','da'));
    await page.route('**/*',route=>{const req=route.request();if(new URL(req.url()).origin!==fixture.origin)return route.abort();if(req.method()==='POST'&&new URL(req.url()).pathname==='/api/mutate')writes.push(req.url());return route.continue();});
    const ready=()=>page.waitForFunction(()=>typeof state!=='undefined'&&state&&SaveStatus.kind==='saved'&&document.querySelector('[data-sidebar-toggle]'));
    await page.goto(fixture.origin);await ready();
    const toggle=page.locator('[data-sidebar-toggle]'),sidebar=page.locator('#sidebar'),nav=page.locator('#nav');
    const activate=l=>touch?l.tap():l.click();
    const width=()=>sidebar.evaluate(n=>n.getBoundingClientRect().width);
    const order=()=>nav.locator('[data-navigation]').evaluateAll(nodes=>nodes.map(n=>n.dataset.navigation));
    const assertCompact=async expected=>{
     await page.waitForFunction(expected=>document.body.classList.contains('sidebarCompact')===expected,expected);
     assert.equal(await toggle.getAttribute('aria-expanded'),String(!expected));
     assert.equal(await width(),expected?64:205);
     if(expected){const hitArea=await toggle.boundingBox();assert.equal(hitArea.width,44);assert.ok(hitArea.height>=44);}
     assert.equal(await page.locator('#app').evaluate(n=>parseFloat(getComputedStyle(n).marginLeft)),expected?64:205);
    };
    const assertLabels=async compact=>{
     const labels=await nav.locator('.sidebarNavLabel,.navExternalLabel,.sidebarToggleLabel').evaluateAll(nodes=>nodes.map(n=>{
      const css=getComputedStyle(n),rect=n.getBoundingClientRect();
      return {text:n.textContent.trim(),position:css.position,width:rect.width,height:rect.height,clip:css.clip,clipPath:css.clipPath,overflow:css.overflow,ariaHidden:n.getAttribute('aria-hidden'),display:css.display,visibility:css.visibility};
     }));
     assert(labels.length>0);
     for(const label of labels){
      assert(label.text,'Navigation names must remain in the DOM');
      assert.notEqual(label.ariaHidden,'true');
      assert.notEqual(label.display,'none');
      assert.notEqual(label.visibility,'hidden');
      if(compact){
       assert.equal(label.position,'absolute');
       assert(label.width<=1&&label.height<=1,'Compact label must occupy at most one pixel');
       assert.equal(label.overflow,'hidden');
       assert(label.clipPath.startsWith('inset(50%')||label.clip!=='auto','Compact label must be clipped, not simply resized');
      }else{
       assert.notEqual(label.position,'absolute');
       assert.equal(label.clipPath,'none');
       assert.equal(label.clip,'auto');
      }
     }
     assert.equal(await nav.getByRole('button',{name:compact?'Fold menu ud':'Fold menu sammen',exact:true}).count(),compact||await toggle.isVisible()?1:0);
     assert.equal(await nav.getByRole('link',{name:'Trinvis LTM-guide',exact:true}).count(),1);
     assert.equal(await nav.getByRole('button',{name:'Forkyndere',exact:false}).count(),1);
    };
    await assertCompact(false);
    await assertLabels(false);
    const initialOrder=await order();
    await activate(nav.locator('[data-navigation="1:2"]'));await page.waitForFunction(()=>page==='Forkyndere');
    await activate(nav.locator('[data-nav-group="2"] summary'));
    assert.equal(await nav.locator('[data-nav-group="2"]').getAttribute('open'),null);
    for(const theme of ['light','dark','system']){
     await nav.locator('#appearanceChoice').selectOption(theme);
     const effective=await page.locator('html').getAttribute('data-theme');
     await page.evaluate(()=>{window.__sidebarContent=document.getElementById('app').firstElementChild;});
     if(touch)await toggle.tap();else{await toggle.focus();await toggle.press('Enter');assert.equal(await toggle.evaluate(n=>document.activeElement===n),true);}
     await assertCompact(true);
     assert.deepEqual(await order(),initialOrder);
     assert.equal(await page.evaluate(()=>document.getElementById('app').firstElementChild===window.__sidebarContent),true);
     assert.equal(await nav.locator('[aria-current="page"]').getAttribute('data-navigation'),'1:2');
     assert.equal(await nav.locator('[data-navigation="2:0"]').isVisible(),true);
     assert.equal(await nav.locator('[data-navigation="2:0"]').getAttribute('title'),'Rapporter og historik');
     await assertLabels(true);
     const report=nav.getByRole('button',{name:'Rapporter og historik',exact:true});
     assert.equal(await report.count(),1);
     assert.equal(await report.locator('.navIcon').isVisible(),true);
     assert.equal(await nav.getByRole('link',{name:'Trinvis LTM-guide',exact:true}).getAttribute('title'),'Trinvis LTM-guide');
     assert.equal(await nav.locator('[aria-current="page"]').evaluate(n=>n.classList.contains('active')),true);
     // Inject fictional counts only while rebuilding the navigation, without writing data.
     await page.evaluate(()=>{
      const tasks=Workspace.actionableTasks,followups=Workspace.followupItems,loaded=GeoUI.loaded,overdue=OverdueLoans.count;
      try{
       Workspace.actionableTasks=()=>[{},{}];Workspace.followupItems=()=>[{},{},{}];GeoUI.loaded=true;OverdueLoans.count=()=>4;
       Navigation.repaintSidebar();
      }finally{Workspace.actionableTasks=tasks;Workspace.followupItems=followups;GeoUI.loaded=loaded;OverdueLoans.count=overdue;}
     });
     for(const [selector,count] of [['.navTaskCount','2'],['[data-navigation="1:4"] .navFollowupCount','3'],['.navOverdueCount','4']]){
      const badge=nav.locator(selector);
      assert.equal(await badge.textContent(),count);
      assert.equal(await badge.isVisible(),true);
      assert(await badge.getAttribute('aria-label'),'Badge keeps its accessible name');
      assert.equal(await badge.evaluate(n=>getComputedStyle(n).position),'absolute');
     }
     await assertLabels(true);
     assert.equal(await page.locator('html').getAttribute('data-theme'),effective);
     if(touch)await page.setViewportSize({width:1366,height:1024});
     await assertCompact(true);
     if(touch)await page.setViewportSize({width:1024,height:1366});
     await assertCompact(true);
     if(touch)await toggle.tap();else await toggle.press('Space');
     await assertCompact(false);
     await assertLabels(false);
     assert.equal(await nav.locator('[data-navigation="1:2"] .sidebarNavLabel').isVisible(),true);
     assert.equal(await nav.locator('[data-nav-group="2"]').getAttribute('open'),null);
     assert.equal(await nav.locator('#appearanceChoice').inputValue(),theme);
    }
    await activate(toggle);await assertCompact(true);
    await page.reload();await ready();await assertCompact(true);
    await page.setViewportSize({width:700,height:900});
    await page.waitForFunction(()=>!document.body.classList.contains('sidebarCompact'));
    assert.equal(await toggle.isVisible(),false);
    await activate(page.locator('.mobileMenu'));
    assert.equal(await page.locator('.mobileMenu').getAttribute('aria-expanded'),'true');
    assert.equal(await nav.locator('[data-nav-group="1"] summary').isVisible(),true);
    await assertLabels(false);
    assert.equal(await nav.locator('[data-navigation="1:2"] .sidebarNavLabel').isVisible(),true);
    await activate(nav.locator('[data-navigation="1:2"]'));await page.waitForFunction(()=>page==='Forkyndere');
    assert.equal(await page.locator('.mobileMenu').getAttribute('aria-expanded'),'false');
    await page.setViewportSize(touch?{width:1024,height:1366}:{width:1440,height:1000});
    await assertCompact(true);
    await assertLabels(true);
    assert.equal(await nav.locator('[aria-current="page"]').getAttribute('data-navigation'),'1:2');
    await activate(toggle);await assertCompact(false);
    await page.reload();await ready();await assertCompact(false);
    assert.deepEqual(writes,[]);assert.deepEqual(errors,[]);
    await context.close();
   }finally{await browser.close();}
  }
  console.log('Collapsible icon-only sidebar: desktop Chromium and touch WebKit, accessible names, badges, rotation, keyboard, themes, persistence and mobile drawer.');
 }finally{child.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
