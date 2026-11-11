'use strict';
// Front-only DAR label controls. This module intentionally never edits geo_addresses.
const FrontLabelsUI={
 open(id){
  const c=card(id);
  if(!c?.geo_addresses?.length||!ProfilesUI.has('cards.view','cards.edit'))return;
  const field=(row,key,title)=>{
   const original=String(row[key]||''),custom=!!row['manual_'+key];
   const current=custom?String(row['display_'+key]):original;
   return `<div data-front-label-field><label>${ui(title)} · ${ui('Kilde')}</label>
    <select data-front-label-mode data-key="${key}"><option value="dar" ${custom?'':'selected'}>${ui('Brug DAR-data')}</option><option value="custom" ${custom?'selected':''}>${ui('Brug egen tekst')}</option></select>
    <label>${ui('Original DAR-værdi')}</label><output class="hint">${esc(original)}</output>
    <label>${ui('Tekst på forsiden')}</label><input data-front-label-text data-dar="${esc(original)}" value="${esc(current)}" maxlength="${key==='road'?120:100}" ${custom?'':'disabled'}></div>`;
  };
  const rows=(c.front_addresses||[]).filter(row=>row.source_ids?.length);
  openDialog(`<h2>${ui('Vejlinjer på kortets forside')} · ${esc(c.number)}</h2>
   <p class="hint">${ui('Ændringerne gælder kun tekst på forsiden. DAR-adresser, kortgrænser og besøgsantal ændres ikke.')}</p>
   ${c.front_label_unmatched?`<p class="notice warning">${ui('Tidligere overstyringer er bevaret, men nogle kan ikke knyttes entydigt til de nye DAR-vejlinjer. Kontrollér dem i eksporten.')}</p>`:''}
   <form id="frontLabelsForm" data-id="${esc(id)}" data-token="${esc(c.front_labels_token)}">
   ${rows.map((row,i)=>`<fieldset class="frontLabelRow" data-source-ids="${esc(JSON.stringify(row.source_ids))}"><legend>${ui('Vejlinje')} ${i+1}</legend>
    <p class="hint">${esc(row.road)} ${esc(row.numbers)} · ${row.count} ${ui('besøg')}</p>
    <div class="twocol">${field(row,'road','Vejnavn')}${field(row,'numbers','Husnummer / husnummerrække')}</div>
    <button type="button" data-front-reset>${ui('Nulstil til DAR')}</button></fieldset>`).join('')}
   <p class="hint">${ui('Kontrollér kortets forhåndsvisning. For lange vejlinjer blokerer print og billedeksport.')}</p>
   ${formEnd('Gem forsidetekst')}</form>`,I18n.language());
 },
 collect(form){
  return [...form.querySelectorAll('.frontLabelRow')].map(row=>{
   const values={source_ids:JSON.parse(row.dataset.sourceIds)};
   for(const section of row.querySelectorAll('[data-front-label-field]')){
    const select=section.querySelector('[data-front-label-mode]'),text=section.querySelector('[data-front-label-text]');
    values[select.dataset.key]=select.value==='custom'?text.value:null;
   }
   return values;
  });
 }
};
document.addEventListener('click',event=>{
 const target=event.target.closest('[data-action="front-labels"],[data-front-reset]');
 if(!target)return;
 event.preventDefault();
 if(target.hasAttribute('data-front-reset')){
  for(const section of target.closest('.frontLabelRow').querySelectorAll('[data-front-label-field]')){
   section.querySelector('[data-front-label-mode]').value='dar';
   const input=section.querySelector('[data-front-label-text]');
   input.value=input.dataset.dar;input.disabled=true;
  }
 }else FrontLabelsUI.open(target.dataset.id);
});
document.addEventListener('change',event=>{
 const select=event.target.closest('[data-front-label-mode]');
 if(!select)return;
 const input=select.closest('[data-front-label-field]').querySelector('[data-front-label-text]');
 input.disabled=select.value!=='custom';
 if(input.disabled)input.value=input.dataset.dar;
 else{input.focus();input.select();}
});
document.addEventListener('submit',async event=>{
 const form=event.target;
 if(form.id!=='frontLabelsForm')return;
 event.preventDefault();
 if(form.dataset.saving==='yes'||!form.reportValidity())return;
 if(!ProfilesUI.has('cards.view','cards.edit'))return;
 form.dataset.saving='yes';
 try{
  const rows=FrontLabelsUI.collect(form);
  await mutate('card.front_labels.save',{card_id:form.dataset.id,expected_token:form.dataset.token,rows},
   {message:I18n.text('Forsidens tekst er gemt')});
 }catch(error){const message=form.querySelector('#formError');if(message)I18n.errorContent(message,error);else toast(error);}
 finally{delete form.dataset.saving;}
});
