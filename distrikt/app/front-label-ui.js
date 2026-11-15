'use strict';
// Front-only DAR label controls. This module intentionally never edits geo_addresses.
const FrontLabelsUI={
 canEdit(c){
  return !!c?.front_labels_token&&c.front_addresses?.some(row=>row.source_ids?.length)&&ProfilesUI.has('cards.view','cards.edit');
 },
 button(c){
  return this.canEdit(c)?`<button type="button" data-action="front-labels" data-id="${esc(c.id)}">${ui('Rediger forsidens vejlinjer')}</button>`:'';
 },
 open(id){
  const c=card(id);
  if(!this.canEdit(c))return;
  const field=(row,key,title,limit)=>{
   return `<div data-front-label-field>
    <p class="hint">DAR · ${esc(row[key])}</p>
    <label>${ui(title)}</label>
    <input data-front-label-text data-key="${key}" value="${esc(row['extra_'+key])}" maxlength="${limit}">
    </div>`;
  };
  const rows=(c.front_addresses||[]).filter(row=>row.source_ids?.length);
  openDialog(`<h2>${ui('Vejlinjer på kortets forside')} · ${esc(c.number)}</h2>
   <p class="hint">${ui('Forhåndsvisningen ændres, når du vælger et interval. Vælg Gem og fremvis kort for at bruge ændringen i print og eksport.')}</p>
   <p class="hint">${ui('Din tekst vises efter DAR-vejlinjen på forsiden. Begge felter kan stå tomme.')}</p>
   ${c.front_label_unmatched?`<p class="notice warning">${ui('Tidligere overstyringer er bevaret, men nogle kan ikke knyttes entydigt til de nye DAR-vejlinjer. Kontrollér dem i eksporten.')}</p>`:''}
   <section id="frontLabelPreview" class="cardDisplay" aria-label="${esc(I18n.text('Forhåndsvisning af forsiden'))}">${frontHTML(c)}</section>
   <form id="frontLabelsForm" data-id="${esc(id)}" data-token="${esc(c.front_labels_token)}">
   ${rows.map((row,i)=>`<fieldset class="frontLabelRow" data-source-ids="${esc(JSON.stringify(row.source_ids))}"><legend>${ui('Vejlinje')} ${i+1}</legend>
    <label for="frontNumberStyle${i}">${ui('Visning af husnumre på forsiden')}</label>
    <select id="frontNumberStyle${i}" data-front-number-style>
     <option value="exact" ${row.number_style!=='range'?'selected':''}>${ui('Vis de valgte numre')}</option>
     <option value="range" ${row.number_style==='range'?'selected':''} ${!row.short_numbers?'disabled':''}>${ui('Vis fra første til sidste')}${row.short_numbers?' · '+esc(row.short_numbers):''}</option>
    </select>
    <p class="hint" data-front-current aria-live="polite">${ui('Husnumre i denne vejlinje: {numbers}',{numbers:row.display_numbers||row.numbers})}</p>
    <p class="hint">${ui('Intervallet forkorter kun teksten. Mellemliggende husnumre bliver ikke tilføjet til distriktet.')}</p>
    <div class="twocol">${field(row,'road','Egen tekst til vejnavn',120)}${field(row,'numbers','Egen tekst til husnumre',100)}</div>
    <button type="button" data-front-reset>${ui('Nulstil vejlinjens visning og egen tekst')}</button></fieldset>`).join('')}
   ${c.front_label_unmatched?`<label class="check"><input type="checkbox" name="clear_unmatched"> ${ui('Nulstil uafklarede overstyringer til DAR')}</label>`:''}
   <p class="hint">${ui('Kontrollér kortets forhåndsvisning. For lange vejlinjer blokerer print og billedeksport.')}</p>
   ${formEnd('Gem og fremvis kort')}</form>`,I18n.language());
  const form=el('frontLabelsForm');
  if(!form)return;
  observeFrontCard(el('frontLabelPreview').querySelector('.cardPreview'));
  form.addEventListener('input',()=>this.preview(c,form));
 },
 preview(c,form){
  const draft=this.collect(form);
  let index=0;
  const rows=c.front_addresses.map(row=>{
   if(!row.source_ids?.length)return row;
   const entry=draft[index++];
   return {...row,number_style:entry.number_style,extra_road:entry.road,extra_numbers:entry.numbers};
  });
  const front=el('frontLabelPreview').querySelector('.cardPreview');
  front.querySelector('.streets').innerHTML=frontStreetMarkup({...c,front_addresses:rows},front.dataset.formLanguage==='en');
  const fields=[...form.querySelectorAll('[data-front-current]')];
  rows.filter(row=>row.source_ids?.length).forEach((row,index)=>{
   I18n.content(fields[index],'Husnumre i denne vejlinje: {numbers}',{
    numbers:row.number_style==='range'?row.short_numbers:row.numbers
   });
  });
  fitFrontCard(front);
 },
 collect(form){
  return [...form.querySelectorAll('.frontLabelRow')].map(row=>{
   const values={source_ids:JSON.parse(row.dataset.sourceIds),number_style:row.querySelector('[data-front-number-style]').value};
   for(const input of row.querySelectorAll('[data-front-label-text]')){
    values[input.dataset.key]=input.value.trim()?input.value:null;
   }
   return values;
  });
 }
};
document.addEventListener('click',async event=>{
 const target=event.target.closest('[data-action="front-labels"],[data-front-reset]');
 if(!target)return;
 event.preventDefault();
 if(target.hasAttribute('data-front-reset')){
  const row=target.closest('.frontLabelRow');
  for(const input of row.querySelectorAll('[data-front-label-text]')){
   input.value='';
  }
  const style=row.querySelector('[data-front-number-style]');
  style.value='exact';
  style.dispatchEvent(new Event('input',{bubbles:true}));
  return;
 }
 if(el('cardForm')){
  const generation=openDialog.generation;
  await closeRequested();
  if(openDialog.generation!==generation||el('dialog').open)return;
 }
 FrontLabelsUI.open(target.dataset.id);
});
document.addEventListener('submit',async event=>{
 const form=event.target;
 if(form.id!=='frontLabelsForm')return;
 event.preventDefault();
 if(form.dataset.saving==='yes'||!form.reportValidity())return;
 if(!ProfilesUI.has('cards.view','cards.edit'))return;
 form.dataset.saving='yes';
 const generation=openDialog.generation,id=form.dataset.id;
 const hadSharedFront=!!state.public_maps?.some(item=>item.card_id===id);
 const controls=[...form.querySelectorAll('input,select,button')].filter(control=>!control.disabled);
 controls.forEach(control=>{control.disabled=true;});
 try{
  const rows=FrontLabelsUI.collect(form);
  await mutate('card.front_labels.save',{card_id:id,expected_token:form.dataset.token,rows,
   clear_unmatched:!!form.querySelector('input[name="clear_unmatched"]:checked')},
   {close:false,message:I18n.text('Forsidens tekst er gemt')});
  if(openDialog.generation===generation&&el('dialog').open){
   const frontSharingOutdated=hadSharedFront&&!state.public_maps?.some(item=>item.card_id===id)
    &&ProfilesUI.has('sharing.manage','cards.view','geo.view','loans.view','history.view');
   detail(id,'Kort',{frontSharingOutdated});
  }
 }catch(error){const message=form.querySelector('#formError');if(message)I18n.errorContent(message,error);else toast(error);}
 finally{delete form.dataset.saving;controls.forEach(control=>{control.disabled=false;});}
});
