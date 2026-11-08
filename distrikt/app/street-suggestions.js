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
  this.pending={target,session,stamp,postcodes,source_expected:plan.source_expected,roads:plan.roads.slice()};
  closeDialog();await this.next();
 },
 async next(){
  const p=this.pending;if(!p)return;
  if(p.target!==GeoUI.target||p.session!==GeoUI.session||p.stamp!==GeoUI.draftStamp(false)){this.pending=null;return;}
  const road=p.roads.shift();
  if(road){await GeoUI.download('road',{...road,include_osm:false});return;}
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
 async afterJob(job){if(job.status!=='done'||job.kind!=='road'){this.pending=null;return;}await this.next();}
};
document.addEventListener('submit',async e=>{if(e.target.id!=='streetSuggestionForm')return;e.preventDefault();const form=e.target;if(form.dataset.saving)return;form.dataset.saving='yes';try{await StreetSuggestions.start(form);}catch(error){StreetSuggestions.pending=null;toast(error);failed(error);}finally{delete form.dataset.saving;}});
