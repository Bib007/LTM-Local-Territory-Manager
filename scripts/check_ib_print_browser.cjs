// Test original-size IB card printouts on A4 proof paper and cut stock.
// Uses entirely invented data, no server, user records or external services.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const appDir=path.join(__dirname,'../distrikt/app');
const main=fs.readFileSync(path.join(appDir,'app.js'),'utf8');
const printing=fs.readFileSync(path.join(appDir,'printing.js'),'utf8');
const first=main.indexOf('function backHTML('),last=main.indexOf('\nfunction canChooseBackupLocation(',first);
assert(first>=0&&last>first,'Locate existing IB renderer');
const renderer=main.slice(first,last);
const setup=[
  "const I18n={language:()=> 'da',text:k=>k};",
  "let state={ib:[]};",
  "const cmp=(a,b)=>String(a).localeCompare(String(b),'da',{numeric:true});",
  "const esc=value=>String(value??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));",
  "const fmt=value=>value?String(value):'';"
].join('\n');

async function run(){
 const browser=await chromium.launch({headless:true});
 try{
  const creator=await browser.newPage();
  await creator.addScriptTag({content:setup+'\n'+renderer+'\n'+printing});
  for(const paper of ['cut','a4']){
   for(const [name,count] of [['few',4],['medium',19],['very-long',130],['long-fields',42]]){
    const fixture=await creator.evaluate(({paper,count,name})=>{
     const card={id:'fake-card',number:'9'};
     state.ib=Array.from({length:count},(_,index)=>({
      card_id:card.id,
      road:index<Math.ceil(count/2)?'Fiktiv Kløverbo':'Fiktiv Kragelundvænget',
      number:String(index+1).padStart(3,'0')+(name==='long-fields'&&index%3===0?' tv. etage':''),
      date_text:name==='long-fields'&&index%5===0?'cirka i efteråret 2024':'1.5.2026'
     }));
     const cfg={...defaultPrintProfile('back'),paper,mode:'full'};
     const source=document.createElement('div');source.innerHTML=backHTML(card);
     return {html:printDocument([card],'back',cfg),cfg,
      expected:[...source.querySelectorAll('.ibRow')].map(node=>node.textContent)};
    },{paper,count,name});
    const page=await browser.newPage();
    const pageErrors=[];page.on('pageerror',error=>pageErrors.push(error.message));
    await page.setContent(fixture.html);
    await page.addScriptTag({content:printing});
    const check=await page.evaluate(()=>{
     const failures=paginateIBSheets(document);
     const sheets=[...document.querySelectorAll('.sheet.ibSheet')];
     const actual=[],issues=[];
     for(const sheet of sheets){
      const bounds=sheet.getBoundingClientRect();
      if(Math.abs(bounds.width/3.779527559-94)>.6||Math.abs(bounds.height/3.779527559-146)>.6)issues.push('Incorrect physical card dimensions');
      for(const col of sheet.querySelectorAll('.ibPrintColumn')){
       if(col.scrollHeight>col.clientHeight+1||col.scrollWidth>col.clientWidth+1)issues.push('Clipped column');
       const limit=col.getBoundingClientRect();
       for(const row of col.querySelectorAll('.ibRow')){
        const box=row.getBoundingClientRect();
        if(box.top<limit.top-1||box.bottom>limit.bottom+1||box.left<limit.left-1||box.right>limit.right+1)issues.push('Row exceeds column');
        actual.push(row.textContent);
       }
      }
      if(sheet.querySelectorAll('.ibPrintColumn').length>2)issues.push('More than two columns');
     }
     return {failures,sheets:sheets.length,actual,issues,columns:sheets[0]?.querySelectorAll('.ibPrintColumn').length};
    });
    assert.deepEqual(check.failures,[],name+' '+paper+' must fit');
    assert.deepEqual(check.issues,[],name+' '+paper+' clipping');
    assert.deepEqual(check.actual,fixture.expected,name+' '+paper+' retains order and every value');
    assert.deepEqual(pageErrors,[],name+' '+paper+' browser exceptions');
    if(name==='few')assert.equal(check.columns,1,'Short IB lists use the full width');
    if(name==='medium')assert.equal(check.sheets,1,'19 ordinary IB entries fit on one physical card');
    if(name==='very-long')assert(check.sheets>1,'Very long IB list has continuation cards');
    const pdf=await page.pdf({preferCSSPageSize:true,printBackground:true});
    const pageCount=(pdf.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length;
    assert.equal(pageCount,check.sheets,name+' '+paper+' PDF pages');
    const media=pdf.toString('latin1').match(/\/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]/);
    assert(media,'PDF media box');
    const [width,height]=media.slice(1).map(Number);
    const expectedSize=paper==='a4'?[595,842]:[266.5,414];
    assert(Math.abs(width-expectedSize[0])<3&&Math.abs(height-expectedSize[1])<3,name+' '+paper+' PDF paper dimensions');
    console.log(name+' '+paper+': '+count+' IB entries, '+check.sheets+' card(s), correct PDF size and no clipping');
    await page.close();
   }
  }
  await creator.close();
 }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;});
