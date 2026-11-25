// Playwright responsive regression using only fictitious territories and synthetic map tiles.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const appDir=path.join(__dirname,'../distrikt/app');
const read=name=>fs.readFileSync(path.join(appDir,name));
const tile=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l6kAAAAASUVORK5CYII=','base64');
const assets={'/style.css':['text/css',read('style.css')],'/vendor/leaflet.css':['text/css',read('vendor/leaflet.css')],'/s13-background.jpg':['image/jpeg',fs.readFileSync(path.join(__dirname,'../distrikt/templates/S-13-background.jpg'))]};
const fixture=`'use strict';
const I18n={language:()=> 'da',text:k=>k,attribute:(name,value)=>name+'="'+value+'"'};
const state={today:'2026-11-11',cards:[{id:'fiction-1',number:'F-101',geo_polygon:[[10.004,55.004],[10.023,55.004],[10.023,55.025],[10.004,55.025]],geo_addresses:[{road:'Opdigtet Vej',number:'7'}]}]};
const GeoUI={data:{main_boundary:{points:[[10,55],[10.04,55],[10.04,55.03],[10,55.03]]}}};
const year=2027,yearLabel=()=> '2026/2027',fmt=value=>value||'';
const esc=value=>String(value??'').replace(/[&<>"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
const ui=key=>key,cardColor=()=> '#477596',eventsInYear=()=>[{card_id:'fiction-1'}],el=id=>document.getElementById(id);
`;
const configurations=[
 {name:'iphone-portrait',width:390,height:844,touch:true,mobile:true},
 {name:'iphone-landscape',width:844,height:390,touch:true,mobile:true},
 {name:'android-phone',width:412,height:915,touch:true,mobile:true},
 {name:'ipad-portrait',width:820,height:1180,touch:true,mobile:true},
 {name:'ipad-landscape',width:1180,height:820,touch:true,mobile:true},
 {name:'desktop',width:1366,height:900,touch:false,mobile:false}
];
async function main(){
 const server=http.createServer((req,res)=>{
  const asset=assets[(req.url||'').split('?')[0]];
  if(asset){res.writeHead(200,{'content-type':asset[0],'cache-control':'no-store'});res.end(asset[1]);return;}
  res.writeHead(200,{'content-type':'text/html; charset=utf-8'});res.end('<!doctype html><html lang="da"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/vendor/leaflet.css"><style>body{background:#f3f5f7}.fixture{width:100%;max-width:900px;margin:auto;padding:10px}#reportDistrictMap{width:100%}</style><main class="fixture" id="fixture"></main></html>');
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin='http://127.0.0.1:'+server.address().port;
 try{
  for(const [engineName,engine] of [['chromium',chromium],['webkit',webkit]]){
   const browser=await engine.launch({headless:true});
   try{
    async function prepare(config,mode='success'){
     const context=await browser.newContext({viewport:{width:config.width,height:config.height},isMobile:config.mobile,hasTouch:config.touch,deviceScaleFactor:config.mobile?2:1});
     const page=await context.newPage(),errors=[];
     page.on('pageerror',e=>errors.push(e.message));
     await page.goto(origin,{waitUntil:'load'});
     if(mode==='offline')await context.setOffline(true);
     await page.route('https://tile.openstreetmap.org/**',async route=>{
      if(mode==='blocked')return route.abort('blockedbyclient');
      if(mode==='timeout')return new Promise(()=>{}); // Browser request deliberately never completes.
      if(mode==='offline')return route.abort('internetdisconnected');
      if(mode==='slow')await new Promise(resolve=>setTimeout(resolve,170));
      return route.fulfill({status:200,contentType:'image/png',headers:{'access-control-allow-origin':'*'},body:tile});
     });
     await page.addScriptTag({content:fixture});
     for(const js of ['vendor/leaflet.js','s13-template.js','map-export.js','report-map.js','report-print.js'])await page.addScriptTag({path:path.join(appDir,js)});
     await page.evaluate(mode=>{
      const rows=[{number:'F-101',previous:'2026-06-01',allocations:[{person:'Opdigtet Person',assigned:'2026-09-01',completed:'2026-10-01'}]}];
      document.getElementById('fixture').innerHTML=s13OriginalPages(rows)+'<section class="report reportScreenMap">'+ReportMap.html(true)+'</section>';
      ReportMap.tileTimeoutMs=mode==='timeout'?400:mode==='slow'?4000:mode==='success'?8000:2000;
      ReportMap.mount();
     },mode);
     return {context,page,errors};
    }
    for(const cfg of configurations){
     const {context,page,errors}=await prepare(cfg);
     try{
      await page.waitForFunction(()=>ReportMap.tiles&&!ReportMap.tiles.isLoading(),null,{timeout:7000});
      const sizes=await page.evaluate(()=>{
       const report=document.querySelector('.s13Original'),svg=report.querySelector('svg'),bounds=svg.getBoundingClientRect(),outer=report.getBoundingClientRect();
       return {left:bounds.left,right:bounds.right,width:bounds.width,height:bounds.height,outerWidth:outer.width,scroll:document.documentElement.scrollWidth,viewport:innerWidth,mapWidth:document.getElementById('reportDistrictMap').getBoundingClientRect().width,loaded:!ReportMap.tileFailed};
      });
      assert(sizes.width>0&&sizes.width<=sizes.viewport+1,cfg.name+' S-13 must fit viewport');
      assert(Math.abs(sizes.height/sizes.width-841.89/595.276)<.05,cfg.name+' S-13 keeps A4 proportions');
      assert(sizes.scroll<=sizes.viewport+2,cfg.name+' no horizontal page overflow: '+JSON.stringify(sizes));
      assert(sizes.mapWidth>0&&sizes.loaded,cfg.name+' map canvas is visible');
      const snapshot=await page.evaluate(()=>ReportMap.printable());
      assert.match(snapshot,/<image href="data:image\/png;base64,/);
      assert.match(snapshot,/F-101/);
      assert.match(snapshot,/<polygon/);
      assert.equal(errors.length,0,cfg.name+' page errors: '+errors.join('; '));
      if(engineName==='chromium'&&cfg.name==='desktop'){
       const pdf=await page.pdf({format:'A4',preferCSSPageSize:true,printBackground:true});
       const media=pdf.toString('latin1').match(/\/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]/);
       assert(media,'S-13 report PDF media box');
       assert(Math.abs(Number(media[1])-595)<3&&Math.abs(Number(media[2])-842)<3,'A4 PDF remains 595 × 842 pt');
      }
      if(process.env.LTM_BROWSER_OUTPUT){
       fs.mkdirSync(process.env.LTM_BROWSER_OUTPUT,{recursive:true});
       await page.screenshot({path:path.join(process.env.LTM_BROWSER_OUTPUT,'report-'+engineName+'-'+cfg.name+'.png')});
      }
      console.log(engineName+' '+cfg.name+': responsive S-13 and synthetic OSM tiles passed');
     }finally{await context.close();}
    }
    for(const [mode,config] of [['blocked',configurations[2]],['offline',configurations[0]],['timeout',configurations[4]],['slow',configurations[2]]]){
     const {context,page,errors}=await prepare(config,mode);
     try{
      if(mode==='slow'){
       await page.waitForFunction(()=>ReportMap.tiles&&!ReportMap.tiles.isLoading(),null,{timeout:7000});
       assert.equal(await page.evaluate(()=>ReportMap.tileFailed),false,'Slow synthetic tiles should eventually load');
      }else{
       await page.waitForFunction(()=>!document.getElementById('reportMapFailure').hidden,null,{timeout:7000});
       const actual=await page.evaluate(async()=>{
        const html=await ReportMap.printable({withoutBackground:true});
        return {html,notice:document.getElementById('reportMapFailureText').textContent,actions:[...document.querySelectorAll('#reportMapFailure button')].map(b=>b.dataset.action)};
       });
       assert.match(actual.notice,/OpenStreetMap/);
       assert.match(actual.html,/F-101/);
       assert.match(actual.html,/<polygon/);
       assert.deepEqual(actual.actions,['retry-report-map','report-without-map']);
       assert.doesNotMatch(actual.html,/<image|tile\.openstreetmap/);
      }
      assert.equal(errors.length,0,engineName+' '+mode+' page errors: '+errors.join('; '));
      console.log(engineName+' '+mode+': bounded loading and fictional map fallback passed');
     }finally{await context.close();}
    }
   }finally{await browser.close();}
  }
 }finally{await new Promise(resolve=>server.close(resolve));}
}

// Exercise the real application controls, not just ReportMap's isolated fixture.
// Standalone is simulated; Linux WebKit cannot exercise native iPadOS windows/printing.
async function checkAppControls(){
 const {spawn}=require('node:child_process'),{createInterface}=require('node:readline');
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')]);
 child.stderr.pipe(process.stderr);
 try{
  const fixture=await new Promise((resolve,reject)=>{
   const timeout=setTimeout(()=>reject(Error('Fictional app did not start')),20000);
   createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timeout);try{resolve(JSON.parse(line));}catch(error){reject(error);}});
   child.once('exit',code=>{clearTimeout(timeout);reject(Error('Fictional app exited: '+code));});
   child.once('error',error=>{clearTimeout(timeout);reject(error);});
  });
  const browser=await webkit.launch({headless:true});
  try{
   for(const standalone of [false,true]){
    const context=await browser.newContext({viewport:{width:820,height:1180},isMobile:true,hasTouch:true,deviceScaleFactor:2});
    try{
     await context.addCookies([fixture.cookie]);
     await context.addInitScript(value=>{
      Object.defineProperty(navigator,'standalone',{configurable:true,value});
      const original=window.matchMedia.bind(window);
      window.matchMedia=query=>{
       const result=original(query);
       if(query.trim()==='(display-mode: standalone)')Object.defineProperty(result,'matches',{configurable:true,value});
       return result;
      };
     },standalone);
     let mode='success';
     await context.route('https://tile.openstreetmap.org/**',route=>mode==='success'
      ?route.fulfill({status:200,contentType:'image/png',headers:{'access-control-allow-origin':'*'},body:tile})
      :route.abort(mode==='offline'?'internetdisconnected':'blockedbyclient'));
     const source=await context.newPage(),errors=[];
     source.on('pageerror',error=>errors.push(error.message));
     await source.goto(fixture.origin);
     await source.waitForFunction(()=>state!==null&&SaveStatus.kind==='saved'&&GeoUI.loaded);
     await source.evaluate(()=>{
      // Add invented client-side geometry to the isolated app state only.
      state.cards[0].geo_polygon=[[10.004,55.004],[10.023,55.004],[10.023,55.025],[10.004,55.025]];
      GeoUI.data.main_boundary={points:[[10,55],[10.04,55],[10.04,55.03],[10,55.03]]};
      I18n.set('da');page='Rapporter';reportTab='Rapport';render();
     });
     assert.equal(await source.evaluate(()=>navigator.standalone),standalone);
     assert.equal(await source.evaluate(()=>matchMedia('(display-mode: standalone)').matches),standalone);
     await source.locator('#reportPrintPeriod').selectOption('calendar');
     await source.locator('#calendarYear').selectOption({label:await source.locator('#calendarYear option').first().textContent()});
     await source.locator('#reportMapNumbers').uncheck();
     const snapshot=()=>source.evaluate(()=>JSON.stringify({
      cards:state.cards,settings:state.settings,period:Workspace.reportPeriod,calendarYear:Workspace.calendarYear,
      year,numbers:Workspace.reportShowNumbers,storedNumbers:localStorage.getItem('ltm-report-map-numbers'),
      selected:el('reportPrintPeriod').value,selectedCalendar:el('calendarYear').value,checked:el('reportMapNumbers').checked
     }));
     const before=await snapshot();
     const view=()=>source.locator('[data-work="report-view"]').click();
     const print=()=>source.locator('[data-action="print-report"]').click();
     const loaded=()=>source.waitForFunction(()=>ReportMap.tiles&&!ReportMap.tiles.isLoading()&&!ReportMap.tileFailed,null,{timeout:10000});
     const preview=async(click,withMap)=>{
      const [popup]=await Promise.all([context.waitForEvent('page'),click()]);
      try{
       popup.on('pageerror',error=>errors.push(error.message));
       await popup.waitForFunction(()=>document.querySelector('.printReports')&&document.getElementById('printReport')&&!document.getElementById('printReport').disabled,null,{timeout:20000});
       assert.equal(await popup.locator('.reportMapPage').count(),withMap?1:0);
       assert.equal(await popup.locator('.reportMapPage svg image[href^="data:image/png;base64,"]').count(),withMap?1:0);
       assert.equal(await popup.locator('.s13Original svg image[href^="data:image/"]').count(),1);
       assert.equal(await popup.locator('.reportchart').count(),1);
       if(withMap)assert.match(await popup.locator('.reportMapPage').textContent(),/OpenStreetMap/);
       // Assert the print command is wired; do not claim native print UI coverage.
       await popup.evaluate(()=>{window.print=()=>{window.__fictionalPrintCalled=true;};});
       await popup.locator('#printReport').click();
       assert.equal(await popup.evaluate(()=>window.__fictionalPrintCalled),true);
      }finally{await popup.close();}
      assert.equal(await snapshot(),before,'Print must preserve original cards, settings and report options');
     };
     await view();await loaded();
     assert.equal(await source.locator('#reportDistrictMap .leaflet-tile-loaded').count()>0,true);
     await preview(print,true);
     mode='blocked';await view();
     const viewFallback=source.locator('#dialog [data-action="report-view-without-map"]');
     await viewFallback.waitFor({state:'visible',timeout:10000});
     await viewFallback.click();
     assert.equal(await source.locator('.reportScreenMap').count(),0);
     assert.equal(await source.locator('.reportchart').count(),1);
     assert.equal(await source.locator('.s13Original').count(),1);
     assert.equal(await snapshot(),before,'Mapless view must preserve settings');
     // Reopen the report while the OSM endpoint is still inaccessible.
     await view();await viewFallback.waitFor({state:'visible',timeout:10000});
     await source.locator('#dialog [data-action="close"]').click();
     await print();
     const printFallback=source.locator('#dialog [data-action="report-print-without-map"]');
     await printFallback.waitFor({state:'visible',timeout:10000});
     await preview(()=>printFallback.click(),false);
     // Completely offline view: no tile or local network available.
     mode='offline';await context.setOffline(true);
     await view();await viewFallback.waitFor({state:'visible',timeout:15000});
     await viewFallback.click();
     assert.equal(await source.locator('.reportScreenMap').count(),0);
     assert.equal(await source.locator('.s13Original').count(),1);
     assert.equal(await snapshot(),before,'Offline view must preserve settings');
     // Restore LAN access for the local S-13/CSS assets, but keep OSM offline.
     await context.setOffline(false);
     await view();await viewFallback.waitFor({state:'visible',timeout:10000});
     await source.locator('#dialog [data-action="close"]').click();
     await print();await printFallback.waitFor({state:'visible',timeout:10000});
     await preview(()=>printFallback.click(),false);
     // Retry from the inline failure controls with the tile endpoint restored.
     await view();await viewFallback.waitFor({state:'visible',timeout:10000});
     await source.locator('#dialog [data-action="close"]').click();
     mode='success';
     await source.locator('[data-action="retry-report-map"]').click();
     await loaded();
     assert.equal(await snapshot(),before,'Retry must preserve settings');
     assert.deepEqual(errors,[]);
     console.log('PASS real app WebKit iPad '+(standalone?'simulated standalone':'browser')+': View, Print, mapless fallback, offline view, retry and unchanged options (synthetic tiles; native print not exercised).');
    }finally{await context.close();}
   }
  }finally{await browser.close();}
 }finally{child.kill();}
}

main().then(checkAppControls).catch(error=>{console.error(error);process.exitCode=1;});
