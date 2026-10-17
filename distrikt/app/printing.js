'use strict';
let frontResizeObserver=null;
// Print profiles belong to local settings. Opening a print view never approves a revision.
function defaultPrintProfile(side){return {orientation:side==='back'?'portrait':'landscape',paper:'cut',mode:side==='back'?'full':'data',width:side==='back'?94:146,height:side==='back'?146:94,x:0,y:0};}
function printSettings(fields){
 const cfg={};for(const key of ['orientation','paper','mode'])cfg[key]=fields[key];
 for(const [key,min,max] of [['width',50,190],['height',50,277],['x',-10,10],['y',-10,10]]){cfg[key]=Number(fields[key]);if(!Number.isFinite(cfg[key])||cfg[key]<min||cfg[key]>max)throw Error('Kontrollér mål og placering.');}
 if(!['portrait','landscape'].includes(cfg.orientation)||!['cut','a4'].includes(cfg.paper)||!['full','data'].includes(cfg.mode))throw Error('Kontrollér retning, papir og tryk.');
 if((cfg.orientation==='portrait')!==(cfg.height>=cfg.width))throw Error('Retning og kortmål stemmer ikke overens.');return cfg;
}
function printRevisions(side){const ids=state.cards.filter(c=>c[side+'_revision']).sort((a,b)=>cmp(a.number,b.number)).map(c=>c.id);if(!ids.length){toast('Ingen sider afventer genprint.');return;}printOptions(ids[0],side,ids);}
function printOptions(id,side,ids,defaults=false){
 const cards=(ids||[id]).map(card).filter(Boolean);if(!cards.length)return;
 const cfg=defaults?defaultPrintProfile(side):{...defaultPrintProfile(side),...(state.settings.print_profiles?.[side]||{})};
 const options=(items,value)=>items.map(([key,label])=>`<option value="${key}" data-ui="${esc(label)}" lang="${I18n.language()}" ${key===value?'selected':''}>${esc(I18n.text(label))}</option>`).join('');
 openDialog(`<h2>${ui(side==='front'?'Print forside':'Print IB-bagside')}</h2><p class="hint">${cards.length===1?ui('Kort')+' '+esc(cards[0].number):ui('{count} kort',{count:cards.length})+' · '+cards.map(c=>esc(c.number)).join(', ')} · ${ui(!defaults&&state.settings.print_profiles?.[side]?'din gemte printprofil':'standardmål')}</p><form id="printForm" data-id="${cards[0].id}" data-side="${side}" data-ids="${esc(JSON.stringify(cards.map(c=>c.id)))}"><div class="twocol"><div><label>${ui("Papir")}</label><select name="paper">${options([['cut','Forskåret kort'],['a4','A4 · prøve i rigtig størrelse']],cfg.paper)}</select></div><div><label>${ui("Tryk")}</label><select name="mode">${options([['full','Med titler og linjer'],['data','Fortrykt kort · kun oplysninger']],cfg.mode)}</select></div></div><details class="printAdjust"><summary>${ui("Mål og placering")}</summary><label>${ui("Retning")}</label><select name="orientation" id="printOrientation">${options([['portrait','Højkant · stående'],['landscape','Liggende']],cfg.orientation)}</select><div class="twocol">${[['width','Bredde, mm',50,190],['height','Højde, mm',50,277],['x','Flyt højre / venstre, mm',-10,10],['y','Flyt ned / op, mm',-10,10]].map(([key,label,min,max])=>`<div><label>${ui(label)}</label><input name="${key}" type="number" min="${min}" max="${max}" value="${cfg[key]}" step="0.1" required></div>`).join('')}</div><button type="button" data-action="print-defaults">${ui("Brug standardmål")}</button></details><label class="check"><input name="remember" type="checkbox" checked> ${ui(side==='front'?'Husk disse indstillinger til forsider':'Husk disse indstillinger til bagsider')}</label><p class="hint">${ui('Brug 100 % skalering uden sidehoved og sidefod. Prøv på A4 først.')} ${cards.length>1?ui('Der dannes én side pr. kort.'):''}</p>${formEnd('Fremvis og print')}</form>`,I18n.language());
}
// The QR corner stays fixed; the road list uses the space to its left.
function fitFrontCard(front){
 const list=front?.querySelector('.streets');if(!list)return true;
 const scale=front.clientWidth/(146*96/25.4),qr=front.querySelector('.cardQR');
 list.style.width=qr?'74%':'86%';
 if(qr){const caption=qr.querySelector('span');caption.style.fontSize=(7.333*scale)+'px';caption.style.marginBottom=(3.78*scale)+'px';}
 const rows=Array.from(list.children),available=front.clientHeight*.79-list.offsetTop;
 let fits=false;
 for(let size=12;size>=9.3;size-=.2){
  list.style.fontSize=(size*scale)+'px';list.style.lineHeight='1.2';
  rows.forEach(row=>{row.style.padding=(Math.max(2,(size-9.3)*1.35+2)*scale)+'px 0';
   if(row.lastElementChild)row.lastElementChild.style.whiteSpace='nowrap';});
  fits=list.scrollHeight<=available+1&&rows.every(row=>row.scrollWidth<=list.clientWidth+1);
  if(fits)break;
 }
 front.dataset.textFits=String(fits);return fits;
}
function cardQRCss(){return '.cardQR{position:absolute;right:2%;bottom:19%;width:14%;text-align:center;color:black;font-family:Arial,sans-serif}.cardQR span{display:block;font-size:5.5pt;line-height:1.15;margin:0 0 1mm;overflow-wrap:normal}.cardQR img{display:block;width:100%;height:auto;aspect-ratio:1;background:white}';}
function printDocument(cards,side,cfg){
 const language=I18n.language(),t=key=>esc(I18n.text(key));
 const {width:w,height:h,x,y,mode,paper}=cfg;
 const css=`body{margin:0;background:#eee;font:13px Arial;color:black}.bar{background:white;padding:15px;position:sticky;top:0;z-index:10}.sheet{width:${w}mm;height:${h}mm;background:white;margin:20px auto;outline:1px solid #aaa;break-after:page}.sheet:last-child{break-after:auto}.content{transform:translate(${x}mm,${y}mm)}.cardPreview{position:relative;width:${w}mm;height:${h}mm}.cardPreview>img{position:absolute;inset:0;width:100%;height:100%}${cardQRCss()}.title{position:absolute;left:26%;top:calc(17% - 1mm);font-size:10pt}.number{position:absolute;left:81%;top:calc(17% - 1mm);font-size:10pt}.streets{position:absolute;left:7%;top:30%;width:86%;font-size:9pt}.streets>div{display:flex;justify-content:space-between;gap:2mm;padding:1.5mm 0}.ibPreview{width:${w}mm;min-height:${h}mm;padding:5mm;box-sizing:border-box;font:9pt Arial}.ibHead{display:flex;justify-content:space-between;border-bottom:2px solid black;padding-bottom:3mm;font-size:8pt}.ibCols,.ibRow{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #999;padding:1.5mm 0}.ibPreview h4{color:black;margin:3mm 0 1mm}.ibPreview section{break-inside:avoid}${mode==='data'?'.cardPreview>img,.ibHead,.ibCols{visibility:hidden}.ibHead,.ibCols,.ibRow{border-color:transparent}':''}@page{size:${paper==='a4'?'A4 portrait':w+'mm '+h+'mm'};margin:${paper==='a4'?'10mm':'0'}}@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}body{background:white}.bar{display:none}.sheet{margin:0;outline:0}}`;
 return `<!doctype html><html lang="da"><head><meta charset="utf-8"><title>Print distriktskort</title><style>${css}</style></head><body><div class="bar" lang="${language}"><button id="print" disabled>${t('Udskriv / gem PDF')}</button> ${cards.length} ${t('kort')} · ${w} × ${h} mm · ${t(h>w?'højkant':'liggende')} · 100 %<p id="tooLong" role="alert"></p><p>${t('Godkend eventuelt genprint i appen, når de fysiske sider er kontrolleret.')}</p></div>${cards.map(c=>`<section class="sheet" data-number="${esc(c.number)}"><div class="content">${side==='front'?frontHTML(c):backHTML(c)}</div></section>`).join('')}</body></html>`;
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

 const loaded=results=>{if(win.closed)return;const overflow=[],missingQR=[];for(const sheet of win.document.querySelectorAll('.sheet')){const content=sheet.querySelector('.content'),streets=sheet.querySelector('.streets'),qr=sheet.querySelector('.cardQR'),image=qr?.querySelector('img');let collision=false;const fits=fitFrontCard(sheet.querySelector('.cardPreview'));if(streets&&qr){const a=streets.getBoundingClientRect(),b=qr.getBoundingClientRect();collision=a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;}
   if(!fits||content.scrollHeight>sheet.clientHeight+2||content.scrollWidth>sheet.clientWidth+2||(streets&&streets.offsetTop+streets.scrollHeight>sheet.clientHeight)||collision)overflow.push(sheet.dataset.number);
   if(image&&(!image.complete||!image.naturalWidth))missingQR.push(sheet.dataset.number);
  }
  const messages=[];if(results.some(r=>r.status==='rejected'))messages.push(t('Printbilleder kunne ikke indlæses. Åbn print igen.'));if(overflow.length)messages.push(t('Vejlisten eller QR-koden har ikke plads på kort:')+' '+overflow.join(', ')+'. '+t('Tilpas kortet før print.'));if(missingQR.length)messages.push(t('QR-koden kunne ikke indlæses på kort:')+' '+missingQR.join(', ')+'. '+t('Genåbn kortet og kontrollér publiceringen.'));
  win.document.getElementById('tooLong').textContent=messages.join(' ');win.document.getElementById('print').disabled=messages.length>0;
 };
 win.document.write(markup);win.document.close();win.document.getElementById('print').addEventListener('click',()=>win.print());
 Promise.allSettled(Array.from(win.document.images,img=>img.decode())).then(loaded);
 if(fd.has('remember')){try{await mutate('print.profile.save',{side,profile:cfg},{close:false,message:'Printprofil gemt lokalt'});}catch(error){toast('Printvisningen er åben. Kontrollér gemmestatus for printprofilen før et nyt forsøg.');return;}}
 if(generation===openDialog.generation&&page===origin&&el('printForm')===form)closeDialog();
 }finally{delete form.dataset.printing;}
}
