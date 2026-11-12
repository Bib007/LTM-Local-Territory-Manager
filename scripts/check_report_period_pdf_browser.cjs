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
  await context.addCookies([fixture.cookie]);
  const source=await context.newPage(),errors=[];
  source.on('pageerror',error=>errors.push(error.message));
  await source.goto(fixture.origin);
  await source.waitForFunction(()=>state!==null&&SaveStatus.kind==='saved');
  const names={calendar:'Kalenderår',service:'Tjenesteår',rolling:'Seneste 12 måneder'};
  for(const empty of [false,true]){
   for(const choice of ['calendar','service','rolling','all']){
    const html=await source.evaluate(async({choice,empty})=>{
     const snapshot={completions:state.completions,visits:state.visits,today:state.today,year,calendarYear:Workspace.calendarYear};
     try{
      state.today='2026-10-16';year=2027;Workspace.calendarYear=2026;I18n.set('da');
      const cardId=state.cards[0].id;
      state.completions=empty?[]:[{id:'fictional-print',card_id:cardId,date:'2026-10-01',visits:4}];
      state.visits=empty?[]:[{id:'fictional-co',date:'2026-10-02',note:'Fiktivt KTM-besøg'}];
      const maps=Object.fromEntries(['calendar','service','rolling'].map(mode=>[mode,
       '<div class="reportMapSnapshot"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100"><text x="5" y="30">FIKTIVT_KORT_'+mode.toUpperCase()+'</text></svg></div>']));
      return await inlineReportAssets(reportPrintDocument(maps,choice));
     }finally{
      state.completions=snapshot.completions;state.visits=snapshot.visits;state.today=snapshot.today;
      year=snapshot.year;Workspace.calendarYear=snapshot.calendarYear;
     }
    },{choice,empty});
    const printed=await context.newPage();
    try{
     printed.on('pageerror',error=>errors.push(error.message));
     await printed.setContent(html,{waitUntil:'load'});
     assert.equal(await printed.locator('.reportchart').count(),choice==='all'?3:1);
     assert.equal(await printed.locator('.reportMapPage').count(),choice==='all'?3:1);
     assert.equal(await printed.locator('.s13Original').count(),choice==='service'||choice==='all'?1:0);
     const marker=await printed.locator('svg text').filter({hasText:'Sidste KTM besøg'}).count();
     assert.equal(marker,empty?0:choice==='all'?3:1,'The yellow KTM timeline marker must match the selected periods');
     if(marker){
      const stroke=await printed.locator('.reportchart svg line[stroke="#c69a25"]').count();
      assert.equal(stroke,marker,'Each latest KTM visit must have a yellow guide line');
     }
     const pdf=await printed.pdf({format:'A4',preferCSSPageSize:true,printBackground:true});
     assert.equal(pdf.subarray(0,4).toString(),'%PDF');
     const result=spawnSync('pdftotext',['-','-'],{input:pdf,encoding:'utf8',maxBuffer:10000000});
     if(result.error)throw result.error;
     assert.equal(result.status,0,result.stderr);
     const text=result.stdout.replace(/\s+/g,' ');
     assert.match(text,/Gennemgange pr\. måned/);
     for(const [mode,label] of Object.entries(names)){
      assert.equal(text.includes(label),choice==='all'||choice===mode,'Unexpected period '+mode+' in PDF '+choice);
      assert.equal(text.includes('FIKTIVT_KORT_'+mode.toUpperCase()),choice==='all'||choice===mode,'Unexpected map '+mode+' in PDF '+choice);
     }
     assert.equal(text.includes('Sidste KTM besøg'),!empty);
     assert.doesNotMatch(text,/NaN|Infinity|undefined/);
    }finally{await printed.close();}
   }
  }
  assert.deepEqual(errors,[]);
  await context.close();
  console.log('PASS 8 real Chromium A4 PDF scenarios: 4 explicit period choices × populated/empty invented data, maps, month timelines, KTM markers and S-13 scope.');
 }finally{await browser?.close();child.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
