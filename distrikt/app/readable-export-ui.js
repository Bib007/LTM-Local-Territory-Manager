'use strict';
const ReadableExportUI={busy:false,
 open(){openDialog(`<h2>${ui('Eksportér læsearkiv')}</h2><p>${ui('Samlet ZIP med PDF-kort, KML, S-13-historik og CSV-tabeller. Arkivet indeholder også IB, navne og opgaver og skal opbevares privat.')}</p><p class="hint">${ui('Alle kort med gemt geografi dannes samlet ud fra lokale kortdata. Brug en lokal sikkerhedskopi til gendannelse.')}</p><div class="actions"><button class="primary" id="readableExportStart">${ui('Dan og hent læsearkiv')}</button>${canChooseBackupLocation()?`<button id="readableExportSave">${ui('Gem læsearkiv som…')}</button>`:''}<button data-action="close">${ui('Annuller')}</button></div><p id="readableExportProgress" role="status"></p>`,I18n.language());},
 async request(path,data,signal){const r=await fetch('/api/export/readable/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Distrikt-Token':token},body:JSON.stringify(data),signal});if(!r.ok){const error=await r.json();throw RequestError.fromResponse(error,'rejected',r.status,false);}return r;},
 async start(chooseLocation=false){
  if(this.busy)return;
  const buttons=[el('readableExportStart'),el('readableExportSave')].filter(Boolean),progress=el('readableExportProgress'),snapshot=state,revision=state.revision,origin=page,generation=openDialog.generation,controller=new AbortController();
  const name=archiveName('LTM-laesearkiv');
  let handle,job;
  const current=()=>{if(controller.signal.aborted||page!==origin||state!==snapshot||state.revision!==revision||openDialog.generation!==generation||el('readableExportProgress')!==progress||!el('dialog').open){controller.abort();throw Error(I18n.text('Eksportgrundlaget er ændret. Start igen.'));}};
  const message=(key,params={})=>{current();progress.dataset.ui=key;progress.dataset.uiParams=JSON.stringify(params);progress.textContent=I18n.format(key,params);};
  this.busy=true;for(const button of buttons)button.disabled=true;const watch=setInterval(()=>{try{current();}catch{controller.abort();}},100);const timer=setTimeout(()=>controller.abort(),3600000);
  try{
   if(chooseLocation){try{handle=await pickArchive(name);}catch(error){if(error.name==='AbortError')return;throw error;}}
   message('Forbereder læsearkiv…');if(!GeoUI.loaded)await GeoUI.load();current();
   job=await(await this.request('prepare',{},controller.signal)).json();current();if(job.revision!==revision)throw Error(I18n.text('Eksportgrundlaget er ændret. Start igen.'));
   for(let i=0;i<job.fronts.length;i++){
    const id=job.fronts[i],front=[...snapshot.cards,...(snapshot.archived_cards||[])].find(c=>c.id===id);if(!front)throw Error(I18n.text('Eksportgrundlaget er ændret. Start igen.'));
    message('Danner kort {index} af {total}…',{index:i+1,total:job.fronts.length});
    const blob=await printFrontImage(front);current();
    const png=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});current();
    await this.request('image',{token:job.token,card_id:id,side:'front',png},controller.signal);current();
    const backs=await printBackImages(front);current();
    for(let page=0;page<backs.length;page++){
     const backPng=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(backs[page]);});current();
     await this.request('image',{token:job.token,card_id:id,side:'back',page,pages:backs.length,png:backPng},controller.signal);current();
    }
   }
   for(let i=0;i<job.cards.length;i++){
    const item=job.cards[i],card={...item.card,name:item.name};message('Danner kort {index} af {total}…',{index:i+1,total:job.cards.length});
    const blob=await MapExport.blob(card.id,'local',{publicCard:card,publicMembers:item.members});current();
    const png=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});current();
    await this.request('image',{token:job.token,card_id:card.id,png},controller.signal);current();
   }
   message('Samler læsearkiv…');
   const response=await this.request('finish',{token:job.token},controller.signal);current();
   await saveDownload(response,name,handle,current);
   message(handle?'Læsearkivet er gemt i den valgte fil.':'Læsearkivet er sendt til browserens downloads. Kontrollér ZIP-filen.');
  }catch(error){if(el('readableExportProgress')===progress&&openDialog.generation===generation){delete progress.dataset.ui;delete progress.dataset.uiParams;progress.textContent=error.name==='AbortError'?I18n.text('Eksporten blev afbrudt. Start igen.'):I18n.text(error.message);}}
  finally{clearTimeout(timer);clearInterval(watch);if(job)this.request('cancel',{token:job.token},undefined).catch(()=>{});this.busy=false;for(const button of buttons)button.disabled=false;}
 }
};
document.addEventListener('click',event=>{if(event.target.closest('[data-action="readable-export"]'))ReadableExportUI.open();const start=event.target.closest('#readableExportStart,#readableExportSave');if(start)ReadableExportUI.start(start.id==='readableExportSave');});
