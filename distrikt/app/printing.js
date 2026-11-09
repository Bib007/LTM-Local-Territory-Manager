'use strict';
let frontResizeObserver=null;
// Print profiles belong to local settings. Opening a print view never approves a revision.
function defaultPrintProfile(side){return {orientation:side==='back'?'portrait':'landscape',paper:'cut',mode:side==='back'?'full':'data',width:side==='back'?94:146,height:side==='back'?146:94,x:0,y:0};}
function printSettings(fields){
 const cfg={};if(fields.form_language!==undefined){if(!['da','en'].includes(fields.form_language))throw Error('Vælg dansk eller engelsk formular.');cfg.form_language=fields.form_language;}for(const key of ['orientation','paper','mode'])cfg[key]=fields[key];
 for(const [key,min,max] of [['width',50,190],['height',50,277],['x',-10,10],['y',-10,10]]){cfg[key]=Number(fields[key]);if(!Number.isFinite(cfg[key])||cfg[key]<min||cfg[key]>max)throw Error('Kontrollér mål og placering.');}
 if(!['portrait','landscape'].includes(cfg.orientation)||!['cut','a4'].includes(cfg.paper)||!['full','data'].includes(cfg.mode))throw Error('Kontrollér retning, papir og tryk.');
 if((cfg.orientation==='portrait')!==(cfg.height>=cfg.width))throw Error('Retning og kortmål stemmer ikke overens.');return cfg;
}
function configurePrintMode(side){if(!['front','back'].includes(side))return;const profile={...defaultPrintProfile(side),...(state.settings.print_profiles?.[side]||{})};openDialog(`<h2>${ui(side==='front'?'Kortets forside':'IB-bagside')} · ${ui('Indstil tryk')}</h2><p>${ui('Er papiret allerede fortrykt? Vælg kun oplysninger. På blankt papir vælger du med titler og linjer. Gemning ændrer ikke kortets godkendelse og åbner ikke print.')}</p><form id="profileModeForm" data-side="${side}"><label for="profileMode">${ui('Tryk')}</label><select id="profileMode" name="mode">${[['data','Fortrykt kort · kun oplysninger'],['full','Med titler og linjer']].map(([value,label])=>`<option value="${value}" data-ui="${esc(label)}" ${profile.mode===value?'selected':''}>${esc(I18n.text(label))}</option>`).join('')}</select>${formEnd('Gem printvalg')}</form>`,I18n.language());}
function printRevisions(side){const ids=state.cards.filter(c=>c[side+'_revision']).sort((a,b)=>cmp(a.number,b.number)).map(c=>c.id);if(!ids.length){toast('Ingen sider afventer genprint.');return;}printOptions(ids[0],side,ids);}
function printOptions(id,side,ids,defaults=false){
 const cards=(ids||[id]).map(card).filter(Boolean);if(!cards.length)return;
 const cfg=defaults?defaultPrintProfile(side):{...defaultPrintProfile(side),...(state.settings.print_profiles?.[side]||{})};
 const options=(items,value)=>items.map(([key,label])=>`<option value="${key}" data-ui="${esc(label)}" lang="${I18n.language()}" ${key===value?'selected':''}>${esc(I18n.text(label))}</option>`).join('');
 openDialog(`<h2>${ui(side==='front'?'Print forside':'Print IB-bagside')}</h2><p class="hint">${cards.length===1?ui('Kort')+' '+esc(cards[0].number):ui('{count} kort',{count:cards.length})+' · '+cards.map(c=>esc(c.number)).join(', ')} · ${ui(!defaults&&state.settings.print_profiles?.[side]?'din gemte printprofil':'standardmål')}</p><form id="printForm" data-id="${cards[0].id}" data-side="${side}" data-ids="${esc(JSON.stringify(cards.map(c=>c.id)))}"><div class="twocol"><div><label>${ui("Papir")}</label><select name="paper">${options([['cut','Forskåret kort'],['a4','A4 · prøve i rigtig størrelse']],cfg.paper)}</select></div><div><label>${ui("Tryk")}</label><select name="mode">${options([['full','Med titler og linjer'],['data','Fortrykt kort · kun oplysninger']],cfg.mode)}</select></div></div><label>${ui("Formularsprog")}</label><select name="form_language">${options([['en','English'],['da','Dansk']],cfg.form_language||I18n.language())}</select><details class="printAdjust"><summary>${ui("Mål og placering")}</summary><label>${ui("Retning")}</label><select name="orientation" id="printOrientation">${options([['portrait','Højkant · stående'],['landscape','Liggende']],cfg.orientation)}</select><div class="twocol">${[['width','Bredde, mm',50,190],['height','Højde, mm',50,277],['x','Flyt højre / venstre, mm',-10,10],['y','Flyt ned / op, mm',-10,10]].map(([key,label,min,max])=>`<div><label>${ui(label)}</label><input name="${key}" type="number" min="${min}" max="${max}" value="${cfg[key]}" step="0.1" required></div>`).join('')}</div><button type="button" data-action="print-defaults">${ui("Brug standardmål")}</button></details><label class="check"><input name="remember" type="checkbox" checked> ${ui(side==='front'?'Husk disse indstillinger til forsider':'Husk disse indstillinger til bagsider')}</label><p class="hint">${ui('Brug 100 % skalering uden sidehoved og sidefod. Prøv på A4 først.')} ${cards.length>1?ui('Der dannes én side pr. kort.'):''}</p><p class="hint">${ui('Originale engelske formularer')}: <a href="/forms/S-12-en.pdf" target="_blank" rel="noopener">S-12 · English PDF</a> · <a href="/forms/S-13-en.pdf" target="_blank" rel="noopener">S-13 · English PDF</a></p>${formEnd('Fremvis og print')}${PrintApprovals.entries.size?`<button type="button" data-action="approve-printed">${ui('Godkend printede sider')}</button>`:''}</form>`,I18n.language());
}
// The QR corner stays fixed; the road list uses the space to its left.
function fitFrontCard(front){
 const list=front?.querySelector('.streets');if(!list)return true;
 const scale=front.clientWidth/(146*96/25.4),qr=front.querySelector('.cardQR');
 list.style.width=qr?'74%':'86%';
 if(qr){const caption=qr.querySelector('span');caption.style.fontSize=(7.333*scale)+'px';caption.style.marginBottom=(3.78*scale)+'px';}
 const rows=Array.from(list.children),available=front.clientHeight*(front.dataset.formLanguage==='en'?.74:.76)-list.offsetTop;
 list.style.maxHeight=Math.max(0,available)+'px';list.style.overflow='hidden';
 let fits=false;
 for(let size=12;size>=9.3;size-=.2){
  list.style.fontSize=(size*scale)+'px';list.style.lineHeight='1.2';
  rows.forEach(row=>{row.style.padding=(Math.max(.5,(size-9.3)*1.35+.5)*scale)+'px 0';
   if(row.lastElementChild)row.lastElementChild.style.whiteSpace='nowrap';});
  fits=list.scrollHeight<=available+1&&rows.every(row=>row.scrollWidth<=list.clientWidth+1);
  if(fits)break;
 }
 front.dataset.textFits=String(fits);
 // Never paint over the original form footer, including in an unprintable preview.
 let warning=front.nextElementSibling;
 if(!warning?.classList.contains('frontOverflow'))warning=null;
 if(!fits&&!warning){warning=front.ownerDocument.createElement('div');warning.className='frontOverflow notice';warning.setAttribute('role','alert');front.after(warning);}
 if(warning){warning.hidden=fits;if(!fits){warning.textContent=I18n.text('Vejlisten eller QR-koden har ikke plads på kort:')+' '+I18n.text('Tilpas kortet før print.')+' '+rows.map(row=>row.textContent).join(' · ');}}
 return fits;
}
function cardQRCss(){return '.cardQR{position:absolute;right:2%;bottom:19%;width:14%;text-align:center;color:black;font-family:Arial,sans-serif}.cardQR span{display:block;font-size:5.5pt;line-height:1.15;margin:0 0 1mm;overflow-wrap:normal}.cardQR img{display:block;width:100%;height:auto;aspect-ratio:1;background:white}';}
// Lay out IB entries against the actual browser dimensions, not estimated row counts.
// This also protects the smaller pre-cut cards: each column is filled before continuing.
function paginateIBSheets(doc,cfg){
 const failures=[],twoColumns=cfg.paper==='a4',maxColumns=twoColumns?2:1;
 for(const original of [...doc.querySelectorAll('.sheet.ibSheet')]){
  const preview=original.querySelector('.ibPreview'),head=preview?.querySelector('.ibHead'),labels=preview?.querySelector('.ibCols');
  if(!head||!labels)continue;
  const entries=[];
  for(const section of preview.querySelectorAll('section')){
   const road=section.querySelector('h4');
   for(const row of section.querySelectorAll('.ibRow'))entries.push({road:road?.cloneNode(true),row:row.cloneNode(true)});
  }
  let lastSheet=null,currentSheet=null,column=null,lastSection=null,lastRoad=null,columnCount=0,rowCount=0,pageNo=0;
  function nextPage(){
   pageNo++;
   currentSheet=pageNo===1?original:original.cloneNode(true);
   if(pageNo>1)lastSheet.after(currentSheet);
   lastSheet=currentSheet;
   currentSheet.dataset.page=String(pageNo);
   const panel=currentSheet.querySelector('.ibPreview');
   panel.replaceChildren();
   const header=head.cloneNode(true);
   if(pageNo>1){panel.dataset.continuation='yes';header.querySelector('b')?.append(doc.createTextNode(' · '+(doc.documentElement.lang==='en'?'continued':'fortsat')));}
   else delete panel.dataset.continuation;
   panel.append(header);
   const body=doc.createElement('div');body.className='ibBody';panel.append(body);
   columnCount=0;nextColumn();
  }
  function nextColumn(){
   const body=currentSheet.querySelector('.ibBody');
   column=doc.createElement('div');column.className='ibPrintColumn';
   column.append(labels.cloneNode(true));body.append(column);
   columnCount++;lastSection=null;lastRoad=null;rowCount=0;
  }
  function fits(){
   const limit=column.getBoundingClientRect(),last=column.lastElementChild,box=last?.getBoundingClientRect();
   return column.clientHeight>0&&column.scrollHeight<=column.clientHeight+1&&column.scrollWidth<=column.clientWidth+1&&(!box||box.bottom<=limit.bottom+1);
  }
  nextPage();
  for(const entry of entries){
   let placed=false;
   // A single exceptionally long entry is never silently clipped.
   while(!placed){
    let addedSection=false;
    const roadText=entry.road?.textContent||'';
    if(!lastSection||lastRoad!==roadText){
     lastSection=doc.createElement('section');
     if(entry.road)lastSection.append(entry.road.cloneNode(true));
     column.append(lastSection);lastRoad=roadText;addedSection=true;
    }
    const row=entry.row.cloneNode(true);lastSection.append(row);
    if(fits()){rowCount++;placed=true;continue;}
    row.remove();
    if(addedSection){lastSection.remove();lastSection=null;lastRoad=null;}
    if(rowCount===0){
     failures.push(original.dataset.number||'?');
     break;
    }
    if(columnCount<maxColumns)nextColumn();else nextPage();
   }
   if(!placed)break;
  }
 }
 return failures;
}
function ibOverviewDocument(items){const language=I18n.language(),t=(key,params)=>esc(I18n.format(key,params));return `<!doctype html><html lang="${language}"><head><meta charset="utf-8"><title>${t('IB-overblik')}</title><style>body{margin:0;background:#eee;color:#182b38;font:12px Arial}.bar{background:white;padding:15px;position:sticky;top:0}.page{max-width:180mm;margin:20px auto;background:white;padding:12mm;box-sizing:border-box}.page h1{margin:0 0 3mm}.page p{color:#526976}table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #ccd8df;padding:2.5mm 2mm}th{background:#edf3f6;font-size:10px}@page{size:A4 portrait;margin:15mm}@media print{body{background:white}.bar{display:none}.page{max-width:none;margin:0;padding:0}thead{display:table-header-group}tr{break-inside:avoid}}</style></head><body><div class="bar"><button id="printIBOverview">${t('Udskriv / gem PDF')}</button><p>${t('A4 · 15 mm margener · listen indeholder private IB-oplysninger.')}</p></div><main class="page"><h1>${t('IB-overblik')}</h1><p>${t('{count} IB · kun lokal udskrift',{count:items.length})}</p><table><thead><tr><th>${t('Kort')}</th><th>${t('Vej, nr.')}</th><th>${t('Dato eller datotekst')}</th></tr></thead><tbody>${items.map(i=>`<tr><td>${esc(card(i.card_id)?.number||'—')}</td><td>${esc(i.road)} ${esc(i.number)}</td><td>${i.date_text?esc(i.date_text):fmt(i.date)}</td></tr>`).join('')}</tbody></table></main></body></html>`;}
async function printIBOverview(items){if(printIBOverview.busy)return;printIBOverview.busy=true;let win;try{win=window.open('','_blank');if(!win)throw Error('Tillad et nyt vindue til print.');win.document.open();win.document.write(ibOverviewDocument(items));win.document.close();win.document.getElementById('printIBOverview').addEventListener('click',()=>win.print());}catch(error){win?.close();throw error;}finally{printIBOverview.busy=false;}}
function printDocument(cards,side,cfg){
 const language=I18n.language(),t=key=>esc(I18n.text(key));
 const {width:w,height:h,x,y,mode,paper}=cfg,formLanguage=cfg.form_language||I18n.language(),ibA4=side==='back'&&paper==='a4',sheetW=ibA4?189:w,sheetH=ibA4?276:h;
 let css=`body{margin:0;background:#eee;font:13px Arial;color:black}.bar{background:white;padding:15px;position:sticky;top:0;z-index:10}.sheet{width:${sheetW}mm;height:${sheetH}mm;background:white;margin:20px auto;outline:1px solid #aaa;break-after:page}.sheet:last-child{break-after:auto}.content{transform:translate(${ibA4?0:x}mm,${ibA4?0:y}mm)}.cardPreview{position:relative;width:${w}mm;height:${h}mm}.cardPreview>img{position:absolute;inset:0;width:100%;height:100%}${cardQRCss()}.title{position:absolute;left:26%;top:calc(17% - 1mm);font-size:10pt}.number{position:absolute;left:81%;top:calc(17% - 1mm);font-size:10pt}.streets{position:absolute;left:7%;top:30%;width:86%;font-size:9pt}.streets>div{display:flex;justify-content:space-between;gap:2mm;padding:1.5mm 0}.cardPreview[data-form-language=en] .title{left:16.5%;top:17%}.cardPreview[data-form-language=en] .number{left:76.8%;top:17%}.cardPreview[data-form-language=en] .streets{top:25%}.ibPreview{width:${sheetW}mm;height:${sheetH}mm;overflow:hidden;padding:5mm;box-sizing:border-box;font:8pt Arial}.ibHead{display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:3mm;font-size:8pt}.ibCols,.ibRow{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #999;padding:1.15mm 0}.ibPreview h4{color:black;margin:2.2mm 0 .8mm}.ibPreview section{break-inside:avoid}${mode==='data'?'.cardPreview>img,.ibHead,.ibCols{visibility:hidden}.ibHead,.ibCols,.ibRow{border-color:transparent}':''}@page{size:${paper==='a4'?'A4 portrait':w+'mm '+h+'mm'};margin:${paper==='a4'?'10mm':'0'}}@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}body{background:white}.bar{display:none}.sheet{margin:0;outline:0}}`;
 if(side==='back')css+=`.sheet.ibSheet .content{width:100%;height:100%}.sheet.ibSheet .ibPreview{display:flex;flex-direction:column;overflow:hidden;padding:${ibA4?'6mm':'4mm'};font:8pt/1.25 Arial,sans-serif}.sheet.ibSheet .ibHead{flex:none;gap:2mm;align-items:center;padding-bottom:2mm;margin-bottom:1.5mm;font-size:8pt}.sheet.ibSheet .ibHead b{overflow-wrap:anywhere}.sheet.ibSheet .ibBody{display:flex;gap:7mm;flex:1 1 auto;min-height:0}.sheet.ibSheet .ibPrintColumn{flex:1 1 0;min-width:0;min-height:0;height:100%}.sheet.ibSheet .ibCols,.sheet.ibSheet .ibRow{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:2mm;line-height:1.2;padding:.55mm 0}.sheet.ibSheet .ibCols{flex:none;font-size:7.8pt;margin-bottom:.7mm}.sheet.ibSheet .ibRow{font-size:8pt;break-inside:avoid}.sheet.ibSheet .ibRow span,.sheet.ibSheet h4{min-width:0;white-space:normal;overflow-wrap:anywhere}.sheet.ibSheet h4{font-size:8pt;line-height:1.2;margin:1.4mm 0 .45mm}.sheet.ibSheet section{break-inside:auto}`;
 const sheets=cards.flatMap(c=>side==='front'?[`<section class="sheet" data-number="${esc(c.number)}"><div class="content">${frontHTML({...c,form_language:formLanguage})}</div></section>`]:[`<section class="sheet ibSheet" data-number="${esc(c.number)}" data-page="1"><div class="content">${backHTML({...c,form_language:formLanguage})}</div></section>`]);
 return `<!doctype html><html lang="${formLanguage}"><head><meta charset="utf-8"><title>${language==='en'?'Print territory card':'Print distriktskort'}</title><style>${css}</style></head><body><div class="bar" lang="${language}"><button id="print" disabled>${t('Udskriv / gem PDF')}</button> ${cards.length} ${t('kort')} · ${ibA4?'A4 · 2 spalter':w+' × '+h+' mm · '+t(h>w?'højkant':'liggende')} · 100 %<p id="tooLong" role="alert"></p><button id="approvePrinted" hidden>${t('Godkend printede sider i appen')}</button><p>${t('Godkend eventuelt genprint i appen, når de fysiske sider er kontrolleret.')}</p></div>${sheets.join('')}</body></html>`;
}
async function printCard(form){
 if(form.dataset.printing==='yes')return;form.dataset.printing='yes';
 try{
 const generation=openDialog.generation,origin=page,revision=state.revision,snapshot=state;
 const current=()=>!win.closed&&form.isConnected!==false&&el('printForm')===form&&openDialog.generation===generation&&page===origin&&state===snapshot&&state.revision===revision;
 const language=I18n.language(),t=key=>language==='en'?(I18n.english[key]||key):key;
 const fd=new FormData(form),signature=JSON.stringify([...fd]),cfg=printSettings(Object.fromEntries(fd)),side=form.dataset.side,ids=JSON.parse(form.dataset.ids||JSON.stringify([form.dataset.id])),cards=ids.map(card).filter(Boolean).map(c=>JSON.parse(JSON.stringify(c)));
 if(!cards.length)throw Error('Kortene findes ikke længere.');
 const win=window.open('','_blank');if(!win)throw Error('Tillad et nyt vindue til print.');
 let markup=printDocument(cards,side,cfg);
 // Embed print assets before opening the layout: the print view stays self-contained.
 try{
  const sources=[...new Set(Array.from(markup.matchAll(/<img[^>]+src="([^"]+)"/g),m=>m[1]))];
  for(const source of sources){
   if(source.startsWith('data:'))continue;
   const response=await fetch(source);if(!response.ok)throw Error('Kortets printbillede kunne ikke hentes. Genåbn kortet og prøv igen.');
   const blob=await response.blob(),data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});
   markup=markup.split('src="'+source+'"').join('src="'+data+'"');
  }
  if(!current()||JSON.stringify([...new FormData(form)])!==signature)throw Error('Printgrundlaget er ændret. Åbn print igen.');
 }catch(error){win.close();throw error;}

 const loaded=(results,ibErrors=[])=>{if(win.closed)return;const overflow=[],missingQR=[];for(const sheet of win.document.querySelectorAll('.sheet')){const content=sheet.querySelector('.content'),streets=sheet.querySelector('.streets'),qr=sheet.querySelector('.cardQR'),image=qr?.querySelector('img');let collision=false;const fits=fitFrontCard(sheet.querySelector('.cardPreview'));if(streets&&qr){const a=streets.getBoundingClientRect(),b=qr.getBoundingClientRect();collision=a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;}
   const ibOverflow=[...sheet.querySelectorAll('.ibPrintColumn')].some(col=>col.clientHeight===0||col.scrollHeight>col.clientHeight+1||col.scrollWidth>col.clientWidth+1);if(!fits||ibOverflow||content.scrollHeight>sheet.clientHeight+2||content.scrollWidth>sheet.clientWidth+2||(streets&&streets.offsetTop+streets.scrollHeight>sheet.clientHeight)||collision)overflow.push(sheet.dataset.number);
   if(image&&(!image.complete||!image.naturalWidth))missingQR.push(sheet.dataset.number);
  }
  const messages=[];if(ibErrors.length)messages.push((language==='en'?'IB entries do not fit on the printed page: ':'IB-posterne kan ikke være på udskriftssiden: ')+[...new Set(ibErrors)].join(', '));if(results.some(r=>r.status==='rejected'))messages.push(t('Printbilleder kunne ikke indlæses. Åbn print igen.'));if(overflow.length)messages.push(t('Vejlisten eller QR-koden har ikke plads på kort:')+' '+overflow.join(', ')+'. '+t('Tilpas kortet før print.'));if(missingQR.length)messages.push(t('QR-koden kunne ikke indlæses på kort:')+' '+missingQR.join(', ')+'. '+t('Genåbn kortet og kontrollér publiceringen.'));
  win.document.getElementById('tooLong').textContent=messages.join(' ');win.document.getElementById('print').disabled=messages.length>0;
 };
 win.document.write(markup);win.document.close();win.document.getElementById('print').addEventListener('click',()=>{if(win.document.getElementById('print').disabled)return;PrintApprovals.remember(cards,side);const approve=win.document.getElementById('approvePrinted');if(approve)approve.hidden=false;win.print();});
 const approve=win.document.getElementById('approvePrinted');if(approve)approve.addEventListener('click',()=>{window.focus();PrintApprovals.open();});
 const imageTasks=Array.from(win.document.images,img=>img.decode());if(win.document.fonts?.ready)imageTasks.push(win.document.fonts.ready);
 Promise.allSettled(imageTasks).then(results=>loaded(results,side==='back'?paginateIBSheets(win.document,cfg):[]));
 if(fd.has('remember')){try{await mutate('print.profile.save',{side,profile:cfg},{close:false,message:'Printprofil gemt lokalt'});}catch(error){toast('Printvisningen er åben. Kontrollér gemmestatus for printprofilen før et nyt forsøg.');return;}}
 if(generation===openDialog.generation&&page===origin&&el('printForm')===form)closeDialog();
 }finally{delete form.dataset.printing;}
}

// Rasterize the measured canonical print DOM, rather than inventing a second layout.
async function printFrontImage(c,options={}){
 const cfg={...defaultPrintProfile('front'),...(state.settings.print_profiles?.front||{}),mode:'full',paper:'cut',x:0,y:0,...options.profile};
 let markup=printDocument([c],'front',cfg);
 for(const source of new Set(Array.from(markup.matchAll(/<img[^>]+src="([^"]+)"/g),m=>m[1]))){
  const response=await fetch(source);if(!response.ok)throw Error('Printbilleder kunne ikke indlæses. Åbn print igen.');
  const blob=await response.blob(),data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(blob);});
  markup=markup.split('src="'+source+'"').join('src="'+data+'"');
 }
 const frame=document.createElement('iframe');frame.setAttribute('aria-hidden','true');frame.style.cssText='position:fixed;left:-20000px;top:0;width:1200px;height:1000px;border:0;pointer-events:none';document.body.append(frame);
 try{
  const doc=frame.contentDocument;doc.open();doc.write(markup);doc.close();
  await Promise.all(Array.from(doc.images,image=>image.decode()));await doc.fonts.ready;
  const front=doc.querySelector('.cardPreview');if(!fitFrontCard(front))throw Error('Vejlisten eller QR-koden har ikke plads på kort:');
  const bounds=front.getBoundingClientRect(),parts=[];
  for(const image of front.querySelectorAll('img')){
   const r=image.getBoundingClientRect();parts.push(`<image href="${esc(image.src)}" x="${r.left-bounds.left}" y="${r.top-bounds.top}" width="${r.width}" height="${r.height}"/>`);
  }
  const walker=doc.createTreeWalker(front,NodeFilter.SHOW_TEXT),measure=document.createElement('canvas').getContext('2d');
  while(walker.nextNode()){
   const node=walker.currentNode,style=frame.contentWindow.getComputedStyle(node.parentElement);if(style.visibility==='hidden')continue;
   measure.font=`${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
   const ascent=measure.measureText('Mg').fontBoundingBoxAscent;if(!Number.isFinite(ascent))throw Error('Browseren understøtter ikke billedeksport.');
   const range=doc.createRange();let line='',box=null;
   const flush=()=>{if(line.trim())parts.push(`<text x="${box.left-bounds.left}" y="${box.top-bounds.top+ascent}" font-family="${esc(style.fontFamily)}" font-size="${style.fontSize}" font-weight="${style.fontWeight}" fill="${style.color}" xml:space="preserve">${esc(line)}</text>`);};
   for(let i=0;i<node.length;i++){
    range.setStart(node,i);range.setEnd(node,i+1);const r=range.getBoundingClientRect();
    if(!r.width)continue;
    if(box&&Math.abs(r.top-box.top)>.5){flush();line='';box=null;}
    if(!box)box=r;line+=node.textContent[i];
   }
   flush();
  }
  const scale=Math.min(2112/bounds.width,1472/bounds.height),x=(2200-bounds.width*scale)/2,y=(1560-bounds.height*scale)/2;
  return await MapExport.raster(`<svg xmlns="http://www.w3.org/2000/svg" width="2200" height="1560"><rect width="2200" height="1560" fill="white"/><g transform="translate(${x} ${y}) scale(${scale})">${parts.join('')}</g></svg>`);
 }finally{frame.remove();}
}

const PrintApprovals={
 entries:new Map(),pending:null,busy:false,singleBusy:new Set(),
 async confirmSingle(id,side,button){
  const key=id+':'+side;if(this.singleBusy.has(key))return;this.singleBusy.add(key);button.disabled=true;
  try{await mutate('revision.approve',{card_id:id,side},{message:I18n.text('Siden er godkendt')});}
  finally{this.singleBusy.delete(key);if(button.isConnected!==false)button.disabled=false;}
 },
 remember(cards,side){for(const c of cards){const token=c[side+'_print_token'];if(token)this.entries.set(c.id+':'+side,{card_id:c.id,side,token,number:c.number});}},
 open(){
  const entries=[...this.entries.values()].filter(e=>card(e.card_id));if(!entries.length){toast(I18n.text('Ingen printede sider afventer godkendelse.'));return;}
  this.pending=entries;
  openDialog(`<h2>${ui('Godkend printede sider')}</h2><p>${ui('Bekræft, at de valgte sider er kontrolleret og printet til de fysiske kort.')}</p><p>${ui('{count} sider',{count:entries.length})}</p><div style="max-height:45vh;overflow:auto">${entries.map((e,i)=>`<label class="check"><input type="checkbox" data-printed-index="${i}" checked> ${ui('Kort')} ${esc(e.number)} · ${ui(e.side==='front'?'Kortets forside':'IB-bagside')}</label>`).join('')}</div><div class="actions"><button class="primary" data-action="confirm-printed">${ui('Kontrolleret og printet')}</button><button data-action="close">${ui('Annuller')}</button></div>`);
 },
 async confirm(){
  if(this.busy||!this.pending)return;
  const entries=[...el('dialog').querySelectorAll('[data-printed-index]:checked')].map(input=>this.pending[Number(input.dataset.printedIndex)]).filter(Boolean);
  if(!entries.length){toast(I18n.text('Vælg de printede sider, der skal godkendes.'));return;}
  const pending=this.pending,button=el('dialog').querySelector('[data-action=confirm-printed]');this.busy=true;if(button)button.disabled=true;try{await mutate('revision.approve_many',{entries:entries.map(({number,...e})=>e)},{message:I18n.text('De printede sider er godkendt')});for(const e of entries){const key=e.card_id+':'+e.side;if(this.entries.get(key)?.token===e.token)this.entries.delete(key);}if(this.pending===pending)this.pending=null;}finally{this.busy=false;if(button?.isConnected)button.disabled=false;}
 }
};
