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
     assert.equal(await width(),expected?104:205);
     assert.equal(await page.locator('#app').evaluate(n=>parseFloat(getComputedStyle(n).marginLeft)),expected?104:205);
    };
    await assertCompact(false);
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
     assert.equal(await nav.locator('[data-navigation="2:0"] .sidebarNavLabel').isVisible(),true);
     assert.equal(await page.locator('html').getAttribute('data-theme'),effective);
     if(touch)await page.setViewportSize({width:1366,height:1024});
     await assertCompact(true);
     if(touch)await page.setViewportSize({width:1024,height:1366});
     await assertCompact(true);
     if(touch)await toggle.tap();else await toggle.press('Space');
     await assertCompact(false);
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
    await activate(nav.locator('[data-navigation="1:2"]'));await page.waitForFunction(()=>page==='Forkyndere');
    assert.equal(await page.locator('.mobileMenu').getAttribute('aria-expanded'),'false');
    await page.setViewportSize(touch?{width:1024,height:1366}:{width:1440,height:1000});
    await assertCompact(true);
    assert.equal(await nav.locator('[aria-current="page"]').getAttribute('data-navigation'),'1:2');
    await activate(toggle);await assertCompact(false);
    await page.reload();await ready();await assertCompact(false);
    assert.deepEqual(writes,[]);assert.deepEqual(errors,[]);
    await context.close();
   }finally{await browser.close();}
  }
  console.log('Collapsible sidebar: desktop Chromium and touch WebKit, rotation, keyboard, themes, persistence and mobile drawer.');
 }finally{child.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
