// Real Chromium PDFs using only fictional, isolated local territory data.
'use strict';
const assert=require('node:assert/strict');
const path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const {createInterface}=require('node:readline');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
 const child=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'fixtures/street_suggestions_server.py')]);
 child.stderr.pipe(process.stderr);
 let browser;
 try{
  const fixture=await new Promise((resolve,reject)=>{
   const timeout=setTimeout(()=>reject(Error('Fictional fixture did not start')),20000);
   createInterface({input:child.stdout}).once('line',line=>{clearTimeout(timeout);resolve(JSON.parse(line));});
   child.once('exit',code=>{clearTimeout(timeout);reject(Error('Fixture exited: '+code));});
  });
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1100}});
  await context.route('**/*',route=>route.request().url().startsWith(fixture.origin+'/')?route.continue():route.abort());
  await context.addCookies([fixture.cookie]);
  const source=await context.newPage(),errors=[];
  source.on('pageerror',error=>errors.push(error.message));
  await source.goto(fixture.origin);
  await source.waitForFunction(()=>state!==null&&SaveStatus.kind==='saved');
  const names={calendar:'Kalenderår',service:'Tjenesteår',rolling:'Seneste 12 måneder'};
  for(const empty of [false,true]){
   for(const choice of ['calendar','service','rolling','all']){
    const html=await source.evaluate(async({choice,empty})=>{
     const snapshot={completions:state.completions,visits:state.visits,today:state.today,year,calendarYear:Workspace.calendarYear,points:ReportMap.points,aspectRatio:ReportMap.aspectRatio};
     try{
      state.today='2026-10-16';year=2027;Workspace.calendarYear=2026;I18n.set('da');
      const cardId=state.cards[0].id;
      state.completions=empty?[]:[{id:'fictional-print',card_id:cardId,date:'2026-10-01',visits:4}];
      state.visits=empty?[]:[{id:'fictional-co',date:'2026-10-02',note:'Fiktivt KTM-besøg'}];
      // Force both named A4 page orientations using fictional view dimensions.
      ReportMap.points=()=>[[10,55],[11,56]];ReportMap.aspectRatio=()=>empty?1.7:0.8;
      const maps=Object.fromEntries(['calendar','service','rolling'].map(mode=>[mode,
       '<div class="reportMapSnapshot"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100"><text x="5" y="12" font-size="6">FIKTIVT_KORT_'+mode.toUpperCase()+'</text><text x="5" y="96" font-size="6">KORT_NEDERST_'+mode.toUpperCase()+'</text></svg></div><p class="hint">© OpenStreetMap-bidragsydere · openstreetmap.org/copyright · FIKTIV_KILDE_'+mode.toUpperCase()+'</p><p class="hint">'+('Fiktive kortnumre uden plads 123, 456, 789. '.repeat(8))+'</p>']));
      return await inlineReportAssets(reportPrintDocument(maps,choice));
     }finally{
      state.completions=snapshot.completions;state.visits=snapshot.visits;state.today=snapshot.today;
      year=snapshot.year;Workspace.calendarYear=snapshot.calendarYear;ReportMap.points=snapshot.points;ReportMap.aspectRatio=snapshot.aspectRatio;
     }
    },{choice,empty});
    const printed=await context.newPage();
    try{
     printed.on('pageerror',error=>errors.push(error.message));
     await printed.setContent(html,{waitUntil:'load'});
     assert.equal(await printed.locator('.reportchart').count(),choice==='all'?3:1);
     assert.equal(await printed.locator('.reportMapPage').count(),choice==='all'?3:1);
     assert.equal(await printed.locator('.s13Original').count(),choice==='all'?3:1,'All periods use the actual original S-13 form');
     assert.equal(await printed.locator('.s13Period').count(),choice==='all'?2:choice==='service'?0:1,'Non-service periods use the S-13 image with an explicit period caption');
     assert.equal(await printed.locator('.s13Original svg image[href^="data:image/"]').count(),choice==='all'?3:1,'Every period must embed the supplied S-13 background image');
     assert.equal(await printed.locator('.s13Period table').count(),0,'The custom replacement table must not return');
     assert.equal(await printed.locator('.s13Original svg').count(),choice==='all'?3:1);
     assert.equal(await printed.locator('.s13Original svg image').evaluateAll(images=>images.every(img=>img.getAttribute('href')?.startsWith('data:image/'))),true,'Every actual S-13 form background must be inlined in the PDF');
     const marker=await printed.locator('svg text').filter({hasText:'Sidste KTM besøg'}).count();
     assert.equal(marker,empty?0:choice==='all'?3:1,'The yellow KTM timeline marker must match the selected periods');
     if(marker){
      const stroke=await printed.locator('.reportchart svg line[stroke="#c69a25"]').count();
      assert.equal(stroke,marker,'Each latest KTM visit must have a yellow guide line');
     }
     const pdf=await printed.pdf({format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
     assert.equal(pdf.subarray(0,4).toString(),'%PDF');
     const result=spawnSync('pdftotext',['-','-'],{input:pdf,encoding:'utf8',maxBuffer:10000000});
     if(result.error)throw result.error;
     assert.equal(result.status,0,result.stderr);
     const pages=result.stdout.split('\f').map(p=>p.replace(/\s+/g,' ').trim()).filter(Boolean),text=pages.join(' ');
     assert(!text.includes(fixture.origin),'Installation URL must not be printed by LTM');
     assert.match(text,/Gennemgange pr\. måned/);
     for(const [mode,label] of Object.entries(names)){
      assert.equal(text.includes(label),choice==='all'||choice===mode,'Unexpected period '+mode+' in PDF '+choice);
      assert.equal(text.includes('FIKTIVT_KORT_'+mode.toUpperCase()),choice==='all'||choice===mode,'Unexpected map '+mode+' in PDF '+choice);
      if(choice==='all'||choice===mode){const mapPages=pages.filter(p=>p.includes('FIKTIVT_KORT_'+mode.toUpperCase()));assert.equal(mapPages.length,1);assert(mapPages[0].includes('KORT_NEDERST_'+mode.toUpperCase()),'Whole map fits one rendered page');assert(mapPages[0].includes('FIKTIV_KILDE_'+mode.toUpperCase()),'Attribution must stay with the map');assert.match(mapPages[0],/openstreetmap\.org\/copyright/);}
     }
     assert.equal(text.includes('Sidste KTM besøg'),!empty);
     assert.equal(text.includes('S-13-periodeudtræk'),choice!=='service');
     assert.equal(text.includes('S-13-formular med periodedata'),choice!=='service');
     if(!empty&&choice!=='service')assert.match(text,/0?1\.10\.2026/,'The extract uses the selected period completion date');
     assert.doesNotMatch(text,/NaN|Infinity|undefined/);
    }finally{await printed.close();}
   }
  }
  // Three real original-form pages per period: first banner only, no extra cover.
  for(const mode of ['calendar','rolling','service']){
   const html=await source.evaluate(async mode=>{
    const before={cards:state.cards,today:state.today,year,calendarYear:Workspace.calendarYear};
    try{
     state.today='2026-10-16';year=2027;Workspace.calendarYear=2026;I18n.set('da');
     state.cards=Array.from({length:45},(_,i)=>({...before.cards[0],id:'fictional-s13-'+i,number:'TEST-'+String(i+1).padStart(2,'0')}));
     return await inlineReportAssets(reportPrintDocument(null,mode,{s13Only:true}));
    }finally{state.cards=before.cards;state.today=before.today;year=before.year;Workspace.calendarYear=before.calendarYear;}
   },mode);
   const printed=await context.newPage();
   try{
    await context.setOffline(true);await printed.setContent(html,{waitUntil:'load'});
    assert.equal(await printed.locator('.s13Original').count(),3);
    assert.equal(await printed.locator('.s13PeriodBanner').count(),mode==='service'?0:1);
    assert.equal(await printed.locator('.reportCover').count(),0);
    const pdf=await printed.pdf({format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
    const result=spawnSync('pdftotext',['-','-'],{input:pdf,encoding:'utf8',maxBuffer:10000000});assert.equal(result.status,0,result.stderr);
    const pages=result.stdout.split('\f');if(!pages[pages.length-1].trim())pages.pop();
    assert.equal(pages.length,3,'Exactly three physical A4 form pages');
    for(let i=0;i<3;i++){
     const first=String(i*20+1).padStart(2,'0'),last=String(Math.min(45,(i+1)*20)).padStart(2,'0');
     assert(pages[i].includes('TEST-'+first)&&pages[i].includes('TEST-'+last),'First and last rows must stay on the same page');
     assert.equal((pages[i].match(/S-13-periodeudtræk/g)||[]).length,i===0&&mode!=='service'?1:0);
     assert(!pages[i].includes(fixture.origin));
    }
   }finally{await context.setOffline(false);await printed.close();}
  }
  // The real vector fallback must print without requesting OSM tiles.
  const fallback=await source.evaluate(async()=>{
   const before={cards:state.cards,points:ReportMap.points};
   try{
    state.cards=[{...before.cards[0],number:'OFFLINE-101',geo_polygon:[[10,55],[10.01,55],[10.01,55.02],[10,55.02]]}];
    const map=await ReportMap.printable({withoutBackground:true});
    return await inlineReportAssets(reportPrintDocument(map,'calendar'));
   }finally{state.cards=before.cards;ReportMap.points=before.points;}
  });
  const offline=await context.newPage();
  try{
   await context.setOffline(true);await offline.setContent(fallback,{waitUntil:'load'});
   assert.equal(await offline.locator('.reportMapSnapshot polygon').count()>0,true);
   const pdf=await offline.pdf({format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
   const result=spawnSync('pdftotext',['-','-'],{input:pdf,encoding:'utf8'});assert.equal(result.status,0,result.stderr);
   assert(result.stdout.split('\f').some(p=>p.includes('OFFLINE-101')&&p.includes('Uden baggrundskort')));
  }finally{await context.setOffline(false);await offline.close();}
  assert.deepEqual(errors,[]);
  await context.close();
  console.log('PASS 12 real Chromium A4 PDF scenarios: portrait/landscape maps with attribution, period scope, multi-page S-13 and offline rendering.');
 }finally{await browser?.close();child.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
