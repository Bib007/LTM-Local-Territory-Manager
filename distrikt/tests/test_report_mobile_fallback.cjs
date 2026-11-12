// Entirely invented territory geometry and names. No user data or internet required.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const app=path.join(__dirname,'../app'),read=name=>fs.readFileSync(path.join(app,name),'utf8');
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,innerHTML:'',textContent:''});return nodes.get(id);};
const boundaries=[[10.0,55.0],[10.04,55.0],[10.04,55.03],[10.0,55.03]];
const cards=[{id:'invented-1',number:'F-101',geo_polygon:[[10.004,55.004],[10.023,55.004],[10.023,55.025],[10.004,55.025]],geo_addresses:[{road:'Opdigtet Vej',number:'7'}]}];
const c={console,Date,Math,Number,String,Array,Object,Set,Map,JSON,Promise,
 location:{origin:'https://fictional.example'},setTimeout:()=>0,clearTimeout:()=>{},
 GeoUI:{data:{main_boundary:{points:boundaries}}},state:{cards,today:'2026-11-11',settings:{congregation:'Opdigtet'}},
 I18n:{language:()=> 'da',text:key=>key,attribute:(key,value)=>key+'="'+value+'"'},
 el:node,eventsInYear:()=>[{card_id:'invented-1'}],cardColor:()=> '#477596',
 ui:key=>key,esc:value=>String(value??'').replace(/[&<>"]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x])),
 fmt:value=>value||'',yearLabel:()=> '2026/2027',year:2027};
vm.createContext(c);
for(const file of ['s13-template.js','report-map.js','report-print.js'])vm.runInContext(read(file),c);
const run=source=>vm.runInContext(source,c);
(async()=>{
 const stateBefore=JSON.stringify(cards);
 const s13=run("s13OriginalPages([{number:'F-101',previous:'2026-06-01',allocations:[{person:'Fiktiv Person',assigned:'2026-09-01',completed:'2026-10-01'}]}])");
 assert.match(s13,/class="report s13Original"/);
 assert.match(s13,/viewBox="0 0 595\.276 841\.89"/);
 assert.match(s13,/s13-background\.jpg/);
 assert.match(s13,/Fiktiv Person/);
 assert.doesNotMatch(s13,/<button|data-action="print"/);
 const css=read('style.css');
 assert.match(css,/@media screen\s*\{\s*\.report\.s13Original/);
 assert.match(css,/\.report\.s13Original svg\{[^}]*width:100%/);
 assert.match(css,/@page\{size:A4 portrait;margin:15mm\}/);
 const controls=run('ReportMap.html(true)');
 assert.match(controls,/data-action="retry-report-map"/);
 assert.match(controls,/data-action="report-without-map"/);
 assert.match(controls,/Generér uden baggrundskort/);
 const noTiles=await run('ReportMap.printable({withoutBackground:true})');
 assert.match(noTiles,/<svg/);
 assert.match(noTiles,/<polygon/);
 assert.match(noTiles,/F-101/);
 assert.doesNotMatch(noTiles,/tile\.openstreetmap|data:image|<image/);
 assert.equal(JSON.stringify(cards),stateBefore,'Offline export must never mutate addresses or cards');
 await assert.rejects(run('ReportMap.printable()'),/OpenStreetMap-kortet/);
 run("ReportMap.failed(Error('offline / simulated blocked requests'))");
 assert.equal(node('reportMapFailure').hidden,false);
 assert.match(node('reportMapFailureText').textContent,/OpenStreetMap/);
 assert.match(node('reportDistrictMap').innerHTML,/F-101/);
 const retryNoTiles=await run('ReportMap.printable({withoutBackground:true})');
 assert.match(retryNoTiles,/F-101/);
 assert.equal(JSON.stringify(cards),stateBefore);
 run('ReportMap.clearFailure()');
 assert.equal(node('reportMapFailure').hidden,true);
 console.log('S-13 screen template, preserved A4 print CSS, blocked/offline map failure actions, standalone SVG fallback and preserved fictional addresses passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
