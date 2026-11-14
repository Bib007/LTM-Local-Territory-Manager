'use strict';
// Existing authenticated road downloads; the card changes only after normal review/save.
const StreetSuggestions={
 pending:null,
 open(){
  const c=card(GeoUI.target);if(!c?.addresses?.length||GeoUI.busy)return;
  openDialog(`<h2>${ui('Foreslå DAR-adresser fra vejlisten')}</h2><p>${ui('Bekræft postnummeret for hver vejlinje. Hele vejen hentes fra DAR, og nummerintervallet bruges til et forslag. Kontrollér alle adresser og den foreslåede grænse før Gem. Kortet ændres ikke ved hentning.')}</p><form id="streetSuggestionForm"><div class="tablewrap"><table><thead><tr><th>${ui('Vejnavn')}</th><th>${ui('Nummerinterval')}</th><th>${ui('Postnummer')}</th></tr></thead><tbody>${c.addresses.map((r,i)=>{const posts=[...new Set((c.geo_addresses||c.imported_addresses||[]).filter(a=>a.road===r.road).map(a=>a.postcode).filter(Boolean))];return `<tr><td>${esc(r.road)}</td><td>${esc(r.numbers)}</td><td><input name="postcode_${i}" aria-label="${esc(I18n.text('Postnummer')+' · '+r.road)}" required pattern="[0-9]{4}" maxlength="4" inputmode="numeric" value="${esc(posts.length===1?posts[0]:'')}"></td></tr>`;}).join('')}</tbody></table></div>${formEnd('Hent og foreslå adresser')}</form>`);
 },
 async start(form){
  if(this.pending||GeoUI.busy||!form.reportValidity())return;
  const c=card(GeoUI.target),target=GeoUI.target,session=GeoUI.session,stamp=GeoUI.draftStamp(false);
  const postcodes=c.addresses.map((r,i)=>form.elements['postcode_'+i].value);
  const plan=await GeoUI.preview({mode:'street_lines',postcodes,planning_only:true});
  if(target!==GeoUI.target||session!==GeoUI.session||stamp!==GeoUI.draftStamp(false)||!el('dialog').open)return;
  if(!GeoUI.canLeave())return;
  // Keep the original street-list number ranges only in the local browser.
  // A DAR road download knows a full street, not which house number caused a failure.
  const roads=plan.roads.map(road=>({
   ...road,
   numbers:c.addresses.filter((line,i)=>String(line.road||'').trim().toLowerCase()===road.road.toLowerCase()&&postcodes[i]===road.postcode).map(line=>String(line.numbers||'').trim()).filter(Boolean)
  }));
  this.pending={target,session,stamp,postcodes,source_expected:plan.source_expected,roads,card_number:c.number,currentRoad:null};
  closeDialog();await this.next();
 },
 async next(){
  const p=this.pending;if(!p)return;
  if(p.target!==GeoUI.target||p.session!==GeoUI.session||p.stamp!==GeoUI.draftStamp(false)){this.pending=null;return;}
  const road=p.roads.shift();
  if(road){
   p.currentRoad=road;
   try{await GeoUI.download('road',{road:road.road,postcode:road.postcode,include_osm:false});}
   catch(error){const message=this.failureMessage(error.message);this.pending=null;throw Error(message);}
   return;
  }
  const result=await GeoUI.preview({mode:'street_lines',postcodes:p.postcodes,source_expected:p.source_expected});
  if(this.pending!==p||p.stamp!==GeoUI.draftStamp(false)){this.pending=null;return;}
  this.pending=null;
  if(result.conflicts.length||result.ignored.length||result.retired.length)throw Error(I18n.text('Forslaget rammer optagne, fravalgte eller nedlagte adresser. Gennemgå kortkontrollen før du fortsætter.'));
  GeoUI.ids=new Set(result.addresses.map(a=>a.id));GeoUI.polygon=result.outline;GeoUI.mode='choose';GeoUI.dirty=true;
  GeoUI.streetApproval={street_expected:result.street_expected,source_expected:result.source_expected,postcodes:p.postcodes};
  GeoUI.setNotice('DAR-forslaget er klar. Sammenlign adresser og besøgstal med vejlisten, ret grænsen og vælg Gem for at ændre kortet.');
  const status=el('geoDownloadStatus');if(status)status.hidden=true;
  render();
  if(GeoUI.map&&result.addresses.length)GeoUI.map.fitBounds(result.addresses.map(a=>[a.lat,a.lng]),{padding:[40,40],maxZoom:18,animate:false});
 },
 failureMessage(reason){
  const pending=this.pending,road=pending?.currentRoad;
  if(!road)return reason;
  return I18n.format('DAR-adresseforslag stoppede ved kort {card}, vej "{road}", postnummer {postcode}, husnumre fra vejlisten: {numbers}. Årsag: {reason}. Kontrollér vejnavn og postnummer. Husnumrene er fra vejlisten; DAR har ikke udpeget et bestemt fejlagtigt husnummer.',{
   card:pending.card_number,road:road.road,postcode:road.postcode,numbers:road.numbers.join(', ')||I18n.text('Hele vejen'),reason:I18n.errorText(reason)
  });
 },
 async afterJob(job){if(job.status!=='done'||job.kind!=='road'){this.pending=null;return;}if(this.pending)this.pending.currentRoad=null;await this.next();}
};
document.addEventListener('submit',async e=>{if(e.target.id!=='streetSuggestionForm')return;e.preventDefault();const form=e.target;if(form.dataset.saving)return;form.dataset.saving='yes';try{await StreetSuggestions.start(form);}catch(error){StreetSuggestions.pending=null;toast(error);failed(error);}finally{delete form.dataset.saving;}});
