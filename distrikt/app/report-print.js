'use strict';
function s13OriginalPages(rows){
 const english=I18n.language()==='en',t=english&&typeof S13TemplateEn!=='undefined'?S13TemplateEn:S13Template,pages=[];for(let offset=0;offset<Math.max(1,rows.length);offset+=20){const values={service_year:yearLabel(year),territory_type:'Hus til hus'};
  rows.slice(offset,offset+20).forEach((r,i)=>{const prefix='row_'+String(i+1).padStart(2,'0')+'.';values[prefix+'number']=r.number;values[prefix+'previous_completed']=r.previous?fmt(r.previous):'';r.allocations.forEach((a,j)=>{for(const k of ['person','assigned','completed'])values[prefix+'assignment_'+(j+1)+'.'+k]=k==='person'?a[k]:(a[k]?fmt(a[k]):'');});});
  const labels=Object.entries(values).filter(([name])=>t.fields[name]).map(([name,value])=>{const [x,y,right,bottom]=t.fields[name],base=['service_year','territory_type'].includes(name)?9:7,font=Math.min(base,(right-x-2)/Math.max(1,String(value).length*.8));return `<text x="${x+1}" y="${y+Math.min(bottom-y-2,10)}" font-family="Arial,Helvetica,sans-serif" font-size="${font}" fill="black">${esc(value)}</text>`;}).join('');
  pages.push(`<section class="report s13Original" lang="${english?'en':'da'}"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${t.width} ${t.height}" role="img" aria-label="Register over distriktstildelinger · udfyldt original S-13, side ${pages.length+1}"><image href="${location.origin}/${english?'s13-background-en.jpg':'s13-background.jpg'}" x="0" y="${t.background_y??20.452}" width="${t.width}" height="${t.background_height??800.986}"/>${labels}</svg></section>`);
 }return pages.join('');
}
// Calendar-year and rolling periods are S-13-style extracts, not official service-year forms.
function s13PeriodPages(rows,mode,start,end){
 if(!['calendar','rolling'].includes(mode))throw Error('Ugyldig S-13-periode.');
 const t=key=>esc(ui(key)),inventory=Workspace.reportInventory(start,end),parts=[];
 for(let offset=0;offset<Math.max(1,rows.length);offset+=12){
  const cells=rows.slice(offset,offset+12).map(r=>{
   const allocations=Array.from({length:4},(_,i)=>{
    const a=r.allocations[i];
    return '<td>'+(a?'<div class="s13Record"><b>'+esc(a.person||'—')+'</b>'+
     (a.assigned?'<small>'+t('Udleveret')+' '+esc(fmt(a.assigned))+'</small>':'')+
     (a.completed?'<small>'+t('Gennemgået')+' '+esc(fmt(a.completed))+'</small>':'')+'</div>':'')+'</td>';
   }).join('');
   return '<tr><th scope="row">'+esc(r.number)+'</th><td>'+(r.previous?esc(fmt(r.previous)):'—')+'</td>'+allocations+'</tr>';
  }).join('');
  const headers=Array.from({length:4},(_,i)=>'<th>'+t('Udlevering')+' '+(i+1)+'</th>').join('');
  parts.push('<section class="report s13Period" data-s13-period="'+mode+'" lang="'+I18n.language()+'">'+
   '<div class="eyebrow">'+t('S-13-periodeudtræk')+'</div><h2>'+esc(Workspace.reportTitle(mode,true))+'</h2>'+
   '<p>'+esc(fmt(start))+' – '+esc(fmt(end))+'</p>'+
   '<p class="hint">'+t('Ikke en original S-13. Tidligere udleveringer vises, hvis de berører perioden; kun gennemgange i perioden tælles.')+'</p>'+
   '<p>'+t('Gennemgange i perioden')+': <strong>'+inventory.events+'</strong> · '+
   t('Gennemgåede aktuelle distrikter')+': <strong>'+inventory.covered+' / '+inventory.total+'</strong></p>'+
   '<div class="tablewrap"><table><thead><tr><th>'+t('Kort')+'</th><th>'+t('Sidst gennemgået før perioden')+'</th>'+headers+'</tr></thead>'+
   '<tbody>'+cells+'</tbody></table></div></section>');
 }
 return parts.join('');
}
function reportDetails(localized=false){const t=key=>localized?ui(key):key,[start,end]=Workspace.periodBounds(),s=Workspace.reportInventory(start,end);return `<section class="report"><h1>${t('Aktuelle distrikter og udlevering')}</h1><p>${t('Status den')} ${fmt(state.today)}</p><div class="tablewrap"><table><thead><tr><th>${t('Distrikter')}</th><th>${t('I alt')}</th><th>${t('Udleveret nu')}</th><th>${t('Hjemme nu')}</th></tr></thead><tbody><tr><th>${t('Aktuelle distrikter')}</th><td>${s.total}</td><td>${s.assigned}</td><td>${s.home}</td></tr><tr><th>${t('Ikke registreret gennemgået i perioden')}</th><td>${s.missing}</td><td>${s.missingAssigned}</td><td>${s.missingHome}</td></tr></tbody></table></div><p>${t('Periode:')} ${fmt(start)}–${fmt(end)}.</p><p class="hint">${Workspace.reportExplanation(localized)}</p></section>`;}
function reportCover(){
 const name=state.report_congregation||state.settings?.congregation;
 return `<section class="reportCover" lang="${I18n.language()}"><p class="reportCoverBrand">Local Territory Manager</p><h1>${esc(name||I18n.text('Distriktsrapport'))}</h1>${name?`<p class="reportCoverSubtitle">${esc(I18n.text('Distriktsrapport'))}</p>`:''}<p>${esc(I18n.text('Rapport udarbejdet den'))} ${fmt(state.today)}</p></section>`;
}
function reportPrintDocument(mapMarkup=null,selection=Workspace.reportPeriod,{s13Only=false}={}){
 const language=I18n.language(),t=key=>esc(I18n.text(key));
 const modes=selection==='all'?['calendar','service','rolling']:[selection];if(!modes.every(mode=>['calendar','service','rolling'].includes(mode)))throw Error('Ugyldigt rapportperiodevalg.');
 const before=Workspace.reportPeriod;let markup;try{
  const period=mode=>{Workspace.reportPeriod=mode;const [start,end]=Workspace.periodBounds(mode),title=Workspace.reportTitle(mode),snapshot=mapMarkup?.[mode]??(typeof mapMarkup==='string'?mapMarkup:'<p>Kortbillede ikke forberedt.</p>');
   return `<section class="report reportMapPage${ReportMap.points().length&&ReportMap.aspectRatio()>1.25?' reportMapLandscape':''}"><div class="eyebrow">${esc(state.settings.congregation||'DISTRIKT')}</div><h2>Gennemgåede distrikter · ${title}</h2><p>${fmt(start)} – ${fmt(end)}</p>${snapshot}</section>`;
  };markup=reportCover()+(s13Only?'':Workspace.boundaryReport(true));
  for(const mode of modes){Workspace.reportPeriod=mode;if(!s13Only)markup+=Workspace.reportSummary(mode,false)+period(mode);markup+=s13Appendix(mode);}
 }finally{Workspace.reportPeriod=before;}
 return `<!doctype html><html lang="da"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${language==='en'?'Territory report':'Distriktsrapport'} ${esc(selection==='all'?I18n.text('Alle tre perioder'):Workspace.reportTitle(selection))}</title><link rel="stylesheet" href="${location.origin}/style.css"><style>:root{color-scheme:light}body{margin:0;background:white;color:#2c475b;font:12px Arial}.bar{padding:15px;background:white;border-bottom:1px solid #ddd}.printReports{max-width:180mm;margin:20px auto}.printReports>.tabs,.printReports>.toolbar{display:none}.report{border:0;border-radius:0;box-shadow:none;padding:0;margin:0 0 10mm;width:100%;background:white}.report table{table-layout:fixed}.report td,.report th{overflow-wrap:anywhere;padding:7px 4px}.report .metrics{gap:8px}.report .metrics strong{font-size:25px}.s13Original{padding:0!important}.s13Original svg{display:block;width:100%;height:auto}.reportMapPage{break-inside:avoid}.reportMapPage .reportMapSnapshot svg{width:100%;height:225mm}.reportMapLandscape{page:reportMapLandscape}.reportMapLandscape .reportMapSnapshot svg{height:135mm}.reportMapPage h2{font-size:20px;margin:0 0 3mm}.reportMapPage .hint{font-size:9px}.reportOverview .reportPeriod{border-top:1px solid #dfe8ee;padding-top:2mm;margin-top:2mm;break-inside:avoid}.reportOverview h1{font-size:22px}.reportOverview h2{font-size:17px;margin:0}.reportOverview p{margin:2mm 0}.reportOverview .metrics{margin:2mm 0;gap:6px}.reportOverview .metrics>div{padding:4px}.reportOverview .metrics strong{font-size:23px;margin-top:2px}.reportOverview .reportchart{padding:3px;margin:1mm 0}.reportOverview .reportchart h3{font-size:12px;margin:0}.reportOverview .reportchart svg{width:100%;height:27mm}.reportOverview .metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr))}.reportOverview .metrics small{font-size:9px}.reportOverview .metrics strong{font-size:19px}.reportOverview .reportPeriod{break-inside:avoid}.reportOverview .hint{font-size:9px;line-height:1.4}.reportchart{break-inside:avoid} .s13Original{break-inside:avoid}.s13Period{break-inside:avoid}.s13Period h2{font-size:20px;margin:2mm 0}.s13Period table{table-layout:fixed;width:100%;border-collapse:collapse}.s13Period th,.s13Period td{font-size:8px;vertical-align:top;padding:4px 3px;overflow-wrap:anywhere;border-bottom:1px solid #d9e3e9}.s13Period th:nth-child(1){width:9%}.s13Period th:nth-child(2){width:15%}.s13Period .s13Record small{display:block;margin-top:2px}.s13Period tr{break-inside:avoid}@page{size:A4 portrait;margin:15mm}@page reportMapLandscape{size:A4 landscape;margin:15mm}@media print{body{background:white}.bar{display:none}.printReports{width:auto;max-width:none;margin:0}.report{break-after:page;margin-bottom:0}.report:last-child,.boundaryReport{break-after:auto}.boundaryReport{break-inside:avoid;margin-bottom:4mm}.report th,.report td{font-size:9px}.report h1{font-size:24px}.report-context{font-size:9px}.report table tr{break-inside:avoid}.s13Original{break-before:page}}</style></head><body><div class="bar" lang="${language}"><button id="printReport">${t('Udskriv / gem PDF')}</button><p>${t('A4 · 15 mm margener. Vælg 100 % og slå browserens sidehoved og sidefod fra.')}</p><p id="printAssetError" role="alert"></p></div><div class="printReports">${markup}</div></body></html>`;
}
async function inlineReportAssets(markup){
 const css=await(await api('/style.css')).text(),source=I18n.language()==='en'?'/s13-background-en.jpg':'/s13-background.jpg',url=location.origin+source;
 const document=markup.replace(`<link rel="stylesheet" href="${location.origin}/style.css">`,`<style>${css}</style>`);
 if(!document.includes(url))return document;
 const blob=await(await api(source)).blob();
 const image=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});
 return document.split(url).join(image);
}
async function printReport({withoutBackground=false,s13Only=false}={}){
 if(printReport.busy)return;printReport.busy=true;
 const origin=page,originalState=state,revision=state.revision,originalYear=year,originalCalendarYear=Workspace.calendarYear,map=ReportMap.map,before=Workspace.reportPeriod,language=I18n.language(),picker=el('reportPrintPeriod'),selection=s13Only?before:(picker?.value||before),showNumbers=Workspace.reportShowNumbers!==false;let owned=before,win,buildingMap=false;
 const current=()=>page===origin&&state===originalState&&state.revision===revision&&year===originalYear&&Workspace.calendarYear===originalCalendarYear&&ReportMap.map===map&&Workspace.reportPeriod===owned&&((Workspace.reportShowNumbers!==false)===showNumbers)&&(!picker?.value||(picker.isConnected!==false&&picker.value===selection))&&!win.closed;
 const check=()=>{if(!current())throw Error('Printgrundlaget er ændret. Åbn print igen.');};
 try{
  const modes=selection==='all'?['calendar','service','rolling']:[selection];if(!modes.every(mode=>['calendar','service','rolling'].includes(mode)))throw Error('Ugyldigt rapportperiodevalg.');
  win=window.open('','_blank');if(!win)throw Error('Tillad et nyt vindue til rapportprint.');
  win.document.write('<p>'+esc(I18n.text('Forbereder den valgte rapport…'))+'</p>');
  const maps={};if(!s13Only){buildingMap=true;for(const mode of modes){owned=Workspace.reportPeriod=mode;ReportMap.draw();maps[mode]=await ReportMap.printable({withoutBackground});check();}buildingMap=false;}
  const markup=await inlineReportAssets(reportPrintDocument(maps,selection,{s13Only}));check();
  win.document.open();win.document.write(markup);win.document.close();const button=win.document.getElementById('printReport');button.disabled=true;
  const results=await Promise.allSettled(Array.from(win.document.querySelectorAll('svg image'),img=>{const test=new Image();test.src=img.getAttribute('href');return test.decode();}));
  if(win.closed)return;
  if(results.some(r=>r.status==='rejected')){win.document.getElementById('printAssetError').textContent=language==='en'?I18n.english['Printbilleder kunne ikke indlæses. Åbn print igen.']:'Printbilleder kunne ikke indlæses. Åbn print igen.';return;}
  button.disabled=false;button.addEventListener('click',()=>win.print());
 }catch(error){win?.close();if(buildingMap&&!withoutBackground&&page===origin&&state===originalState&&state.revision===revision&&typeof ReportMap.failed==='function')ReportMap.failed(error);throw error;}
 finally{printReport.busy=false;if(page===origin&&ReportMap.map===map&&year===originalYear&&Workspace.reportPeriod===owned){Workspace.reportPeriod=before;ReportMap.draw();}}
}
