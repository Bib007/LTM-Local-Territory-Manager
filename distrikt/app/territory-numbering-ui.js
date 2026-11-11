/* Dual territory identifiers: explicit preview, confirmation, and safe reversal.
   The public number remains the only printed label; IDs never change. */
'use strict';
const TerritoryNumbersUI = {
 pending: null,
 allCards() { return [...(state.cards || []), ...(state.archived_cards || [])]; },
 options(items, value, label) {
   return items.map(item=>`<option value="${esc(item[value])}">${esc(item[label])}</option>`).join('');
 },
 start() {
   if(!ProfilesUI.has('cards.view','cards.edit'))return;
   this.pending=null;
   const cards=this.allCards();
   const areas=state.areas || [];
   if(!cards.length)return toast('Opret et kort først.');
   openDialog(`<h2>Offentlige og interne distriktsnumre</h2>
   <p class="hint">Det offentlige nummer står på det trykte kort. Det interne nummer er til administration. Kortets tekniske ID, adresser, forkyndere, QR og historik ændres aldrig.</p>
   <form id="numberingPlanForm">
   <label>Handling<select name="mode"><option value="swap">Byt offentligt og internt nummer</option><option value="assign">Tildel ledige interne numre fra områdeintervaller</option></select></label>
   <label>Omfang<select name="scope"><option value="card">Ét kort</option><option value="area">Et helt område</option><option value="all">Alle kort, også arkiverede</option></select></label>
   <label>Kort<select name="card_id">${this.options(cards,'id','number')}</select></label>
   <label>Område<select name="area_id">${this.options(areas,'id','name')}</select></label>
   <p class="notice">Et bytte eller en massetildeling udføres aldrig automatisk. Alle konflikter kontrolleres, før der kan bekræftes. Ændret offentligt nummer kræver genprint af begge sider.</p>
   ${formEnd('Vis forhåndsvisning')}
   </form>`);
   const selectedCard=el('numberingPlanForm')?.elements.card_id;
   if(selectedCard && cards.some(c=>c.id===selected)) selectedCard.value=selected;
 },
 scheme() {
   if(!ProfilesUI.has('settings.manage'))return;
   const areas=state.areas || [];
   if(!areas.length)return toast('Opret et område først.');
   this.pending=null;
   openDialog(`<h2>Interne nummerintervaller pr. område</h2><p class="hint">Opsætningen ændrer ingen eksisterende kort. Tildeling sker kun efter separat forhåndsvisning og bekræftelse.</p>
   <form id="numberingSchemeForm">
   <label>Område<select name="area_id">${this.options(areas,'id','name')}</select></label>
   <label>Præfiks (fx T, M eller D)<input name="prefix" maxlength="10" pattern="[A-Za-z]*" autocomplete="off"></label>
   <div class="twocol"><label>Start<input name="start" type="number" min="0" max="999999999" value="1" required></label><label>Slut<input name="end" type="number" min="0" max="999999999" value="999" required></label></div>
   <label>Antal cifre, inkl. foranstillede nuller<input name="width" type="number" min="1" max="20" value="4" required></label>
   <p class="hint">Eksempel: T + 25 med bredde 4 giver T0025. Eksisterende interne numre reserveres.</p>
   ${formEnd('Kontrollér interval')}
   </form>`);
   this.loadScheme();
 },
 loadScheme() {
   const f=el('numberingSchemeForm');if(!f)return;
   const cfg=state.areas.find(a=>a.id===f.elements.area_id.value)?.numbering || {};
   for(const k of ['prefix','start','end','width'])f.elements[k].value=cfg[k]??({prefix:'',start:1,end:999,width:4}[k]);
 },
 async preview(action, payload) {
   const generation=openDialog.generation;
   const response=await(await api('/api/mutate',{action,data:payload})).json();
   if(!el('dialog').open || generation!==openDialog.generation)return;
   const plan=response.result;
   const errors=plan.conflicts || [];
   const changes=plan.changes || [];
   const scheme=action==='area.numbering.preview';
   const undo=action==='card.numbering.undo.preview';
   const confirm=scheme?'GEM INTERVAL':undo?'FORTRYD NUMRE':payload.mode==='swap'?'BYT NUMRE':'TILDEL NUMRE';
   const nextAction=action.replace(/\.preview$/,scheme?'.save':undo?'':' .apply').replace(' .apply','.apply');
   const beforeAfter=scheme
     ?`<p>Område: ${esc(state.areas.find(a=>a.id===payload.area_id)?.name||'')}</p><p>Før: ${esc(JSON.stringify(plan.before))}</p><p>Efter: ${esc(JSON.stringify(plan.after))}</p>`
     :`<div class="tablewrap"><table><thead><tr><th>Kort-ID</th><th>Offentligt før</th><th>Internt før</th><th>Offentligt efter</th><th>Internt efter</th></tr></thead><tbody>${changes.slice(0,300).map(c=>`<tr><td><small>${esc(c.id.slice(0,12))}</small></td><td>${esc(undo?c.after.number:c.before.number)}</td><td>${esc(undo?c.after.internal_number:c.before.internal_number)}</td><td>${esc(undo?c.before.number:c.after.number)}</td><td>${esc(undo?c.before.internal_number:c.after.internal_number)}</td></tr>`).join('')}</tbody></table></div>${changes.length>300?'<p>Kun de første 300 kort vises. Alle ændringer kontrolleres af serveren.</p>':''}`;
   this.pending={action:nextAction,data:{...payload,expected:plan.expected,confirm},generation:null};
   const enabled=!errors.length && (scheme||changes.length>0);
   openDialog(`<h2>Kontrollér nummerændringen</h2><p>${scheme?'Områdeinterval':`${changes.length} ændringer ud af ${plan.selected||changes.length} valgte kort`}</p>
   ${beforeAfter}
   ${errors.length?`<div class="notice warning" role="alert"><b>Konflikter – intet kan gemmes:</b><ul>${errors.slice(0,50).map(e=>`<li>${esc(e)}</li>`).join('')}</ul></div>`:''}
   <p class="hint">Ændringer udføres i én transaktion. Historik og alle tekniske kort-ID’er bevares. Tjek eventuelle allerede udskrevne kort, før du fortsætter.</p>
   <label>Skriv ${esc(confirm)} for at bekræfte<input id="numberingConfirmation" autocomplete="off" placeholder="${esc(confirm)}" ${enabled?'':'disabled'}></label>
   <div id="formError" class="formError" role="alert"></div>
   <div class="actions"><button type="button" class="primary" data-numbering="apply" ${enabled?'':'disabled'}>Bekræft og gem</button><button type="button" data-action="close">Annuller</button></div>`);
   this.pending.generation=openDialog.generation;
 },
 async apply() {
   const pending=this.pending;
   if(!pending || pending.generation!==openDialog.generation)throw Error('Forhåndsvisningen er udløbet.');
   if(el('numberingConfirmation')?.value!==pending.data.confirm)throw Error('Skriv den viste bekræftelsestekst nøjagtigt.');
   this.pending=null;
   await mutate(pending.action,pending.data,{message:'Nummerændringen er gemt. Genprint ændrede offentlige kort.'});
 },
 undo() {
   const batch=state.numbering_last_batch;
   if(!batch)return toast('Ingen nummerændring kan fortrydes.');
   this.preview('card.numbering.undo.preview',{batch_id:batch.id});
 }
};
document.addEventListener('change',e=>{
 if(e.target.name==='area_id'&&e.target.closest('#numberingSchemeForm'))TerritoryNumbersUI.loadScheme();
});
document.addEventListener('click',async e=>{
 const target=e.target.closest('[data-numbering]');if(!target||target.disabled)return;
 e.preventDefault();
 try{
   if(target.dataset.numbering==='start')TerritoryNumbersUI.start();
   else if(target.dataset.numbering==='scheme')TerritoryNumbersUI.scheme();
   else if(target.dataset.numbering==='undo')await TerritoryNumbersUI.undo();
   else if(target.dataset.numbering==='apply')await TerritoryNumbersUI.apply();
 }catch(error){if(el('formError'))I18n.errorContent(el('formError'),error);else toast(error);}
});
document.addEventListener('submit',async e=>{
 const f=e.target;if(!['numberingPlanForm','numberingSchemeForm'].includes(f.id))return;
 e.preventDefault();if(!f.reportValidity())return;
 const b=f.querySelector('button[type="submit"],button:not([type])');if(b)b.disabled=true;
 try{
   const payload=Object.fromEntries(new FormData(f));
   await TerritoryNumbersUI.preview(f.id==='numberingSchemeForm'?'area.numbering.preview':'card.numbering.preview',payload);
 }catch(error){if(el('formError'))I18n.errorContent(el('formError'),error);else toast(error);}
 finally{if(b?.isConnected)b.disabled=false;}
});
