'use strict';
const ReadableExportUI={busy:false,
 open(){openDialog(`<h2>${ui('Eksportér læsearkiv')}</h2><p>${ui('Samlet ZIP med fire PDF-filer, fuld S-13-historik og CSV-tabeller. Indeholder også IB, navne og opgaver og skal opbevares privat.')}</p><p class="hint">${ui('OpenStreetMap hentes under dannelsen. Den færdige pakke kan læses uden LTM og internet. Den erstatter ikke en sikkerhedskopi til gendannelse.')}</p><div class="actions"><button class="primary" id="readableExportStart">${ui('Dan og hent læsearkiv')}</button><button data-action="close">${ui('Annuller')}</button></div><p id="readableExportProgress" role="status"></p><div id="readableExportPreview"></div>`,I18n.language());},
 async request(path,data,signal){const r=await fetch('/api/export/readable/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Distrikt-Token':token},body:JSON.stringify(data),signal});if(!r.ok){const error=await r.json();throw RequestError.fromResponse(error,'rejected',r.status,false);}return r;},
 async background(card,members,current){
  const preview=el('readableExportPreview');preview.innerHTML=`<h3>${ui('Kort')} ${esc(card.number)}</h3><p class="hint">${ui('Se kortet igennem og medtag det. Næste kort hentes først, når du fortsætter.')}</p><div id="readableExportMap" style="height:360px;width:100%"></div><button type="button" id="readableExportInclude" disabled>${ui('Medtag kort og fortsæt')}</button>`;
  const node=el('readableExportMap');let map;
  try{
   map=L.map(node,{zoomControl:false,attributionControl:true,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false,scrollWheelZoom:false,dragging:false,doubleClickZoom:false,touchZoom:false,boxZoom:false,keyboard:false});
   const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxNativeZoom:19,maxZoom:21,crossOrigin:'anonymous',referrerPolicy:'strict-origin-when-cross-origin',attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap-bidragsydere</a>'});let failed=false;layer.on('tileerror',()=>failed=true);layer.addTo(map);
   const points=[...(card.geo_polygon||[]),...members.map(a=>[a.lng,a.lat])];map.fitBounds(points.map(p=>[p[1],p[0]]),{padding:[60,60],maxZoom:18,animate:false});
   const deadline=Date.now()+30000;await new Promise(resolve=>setTimeout(resolve,250));
   while(layer.isLoading()){current();if(failed||Date.now()>deadline)throw Error(I18n.text('Kortbaggrunden kunne ikke hentes. Ingen eksportpakke er hentet.'));await new Promise(resolve=>setTimeout(resolve,100));}
   current();if(failed)throw Error(I18n.text('Kortbaggrunden kunne ikke hentes. Ingen eksportpakke er hentet.'));
   const include=el('readableExportInclude');include.disabled=false;include.focus();
   await new Promise((resolve,reject)=>{const poll=setInterval(()=>{try{current();}catch(error){clearInterval(poll);reject(error);}},100);include.addEventListener('click',()=>{clearInterval(poll);resolve();},{once:true});});
   current();return MapExport.captureMap(map,layer);
  }finally{map?.remove();if(el('readableExportPreview')===preview)preview.innerHTML='';}
 },
 async start(){
  if(this.busy)return;const button=el('readableExportStart'),progress=el('readableExportProgress'),snapshot=state,revision=state.revision,origin=page,generation=openDialog.generation,controller=new AbortController();
  const current=()=>{if(controller.signal.aborted||page!==origin||state!==snapshot||state.revision!==revision||openDialog.generation!==generation||el('readableExportProgress')!==progress||!el('dialog').open){controller.abort();throw Error(I18n.text('Eksportgrundlaget er ændret. Start igen.'));}};
  const message=(key,params={})=>{current();progress.dataset.ui=key;progress.dataset.uiParams=JSON.stringify(params);progress.textContent=I18n.format(key,params);};
  this.busy=true;button.disabled=true;const watch=setInterval(()=>{try{current();}catch{controller.abort();}},100);let timer=setTimeout(()=>controller.abort(),3600000);
  try{
   message('Forbereder læsearkiv…');const job=await(await this.request('prepare',{},controller.signal)).json();current();if(job.revision!==revision)throw Error(I18n.text('Eksportgrundlaget er ændret. Start igen.'));
   for(let i=0;i<job.cards.length;i++){
    const item=job.cards[i],card={...item.card,name:item.name};message('Danner kort {index} af {total}…',{index:i+1,total:job.cards.length});
    const background=await this.background(card,item.members,current);current();
    const blob=await MapExport.blob(card.id,'local',{...background,publicCard:card,publicMembers:item.members});current();
    const png=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});current();
    await this.request('image',{token:job.token,card_id:card.id,png},controller.signal);current();
   }
   message('Samler PDF og CSV…');const response=await this.request('finish',{token:job.token},controller.signal),blob=await response.blob();current();
   const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='LTM-laesearkiv-'+state.today+'.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);message('Læsearkivet er sendt til browserens downloads. Kontrollér ZIP-filen.');
  }catch(error){if(el('readableExportProgress')===progress&&openDialog.generation===generation){delete progress.dataset.ui;delete progress.dataset.uiParams;progress.textContent=error.name==='AbortError'?I18n.text('Eksporten blev afbrudt. Start igen.'):I18n.text(error.message);}}
  finally{clearTimeout(timer);clearInterval(watch);this.busy=false;button.disabled=false;}
 }
};
document.addEventListener('click',event=>{if(event.target.closest('[data-action="readable-export"]'))ReadableExportUI.open();if(event.target.closest('#readableExportStart'))ReadableExportUI.start();});
