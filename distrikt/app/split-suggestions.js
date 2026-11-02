'use strict';
// Local planning only. Existing explicit preview/confirmation owns any later split.
Object.assign(I18n.english,{
 'Opdelingsforslag':'Split suggestions',
 'Se manuelle opdelingsforslag':'Review manual split suggestions',
 'Ca. besøg pr. kort':'Approximate visits per card',
 'Kun kort i kassen':'Only cards in the box',
 'Målet og filteret huskes i denne browser.':'The target and filter are remembered in this browser.',
 'Forslag ud fra indlæste besøgstal. Ingen kort, adresser, datoer eller udleveringer ændres.':'Suggestions use the loaded visit estimates. Cards, addresses, dates and assignments stay unchanged.',
 'Kort i mappen og udleverede kort er skjult, når kassefilteret er valgt. Modtagerkort skal altid være hjemme.':'The box filter excludes carry-folder and issued cards. Receiving cards must always be at home.',
 'Alternativerne skal vurderes hver for sig. Kontrollér geografien og genberegn efter en ændring.':'Review alternatives separately. Check the geography and recalculate after a change.',
 'Vælg et helt antal fra 1 til 1.000.':'Choose a whole number from 1 to 1,000.',
 'Viser {shown} af {total} kort over målet.':'Showing {shown} of {total} cards above the target.',
 'Ingen kort over målet i denne visning.':'No cards above the target in this view.',
 '{count} kort har ukendt eller ugyldigt besøgstal og bruges ikke i beregningen.':'{count} cards have unknown or invalid visit estimates and are excluded from the calculation.',
 'Besøgstal er skøn, ikke registrerede husbesøg.':'Visit totals are estimates, not recorded house-to-house visits.',
 'Forslag: cirka {parts} kort med {count} besøg pr. kort.':'Suggestion: about {parts} cards with {count} visits per card.',
 'Et ekstra kort alene vil give for små kort. Undersøg manuel omfordeling.':'One extra card would make the cards too small. Review manual redistribution.',
 'Udleveret kort · planlæg først ændringen, når kortet er afleveret.':'Issued card: make changes only after it is returned.',
 'Præcist adressevalg mangler eller stemmer ikke med besøgstallet. Intet adressevalg gættes.':'Exact address membership is missing or differs from the visit total. No membership is guessed.',
 'Dublerede adressevalg skal afklares før opdeling.':'Resolve duplicate address membership before splitting.',
 'Muligt nyt kort: {count} besøg · tilbage på kortet: {remaining}.':'Possible new card: {count} visits; remaining on this card: {remaining}.',
 'Gennemgå opdeling til nyt kort':'Review split into a new card',
 'Se foreslåede adresser':'View proposed addresses',
 'Mulig omfordeling til kort {number}: {count} besøg · forventede skøn {source} / {target}.':'Possible redistribution to card {number}: {count} visits; estimated totals {source} / {target}.',
 'Samme område, type og vejnavn. Det er ikke en kontrol af geografisk sammenhæng.':'Same area, type and street name. Geographic continuity has not been checked.',
 'Åbn modtagerkort':'Open receiving card',
 'Flytning til eksisterende kort samt valg af gennemgangsdato eller midlertidigt kort følger senere. Forslagene flytter intet.':'Moving to an existing card and choosing a completion-date policy or temporary card will follow later. These suggestions move nothing.',
 'Historik bevares på de oprindelige kort. Et nyt kort får ingen opdigtet gennemgang og skal kontrolleres og genprintes.':'History stays with the original cards. A new card gets no invented completion and must be reviewed and reprinted.',
 'Oversigten er ændret. Gennemgå de opdaterede forslag igen.':'The overview has changed. Review the updated suggestions again.',
 'Kontrollér besøgstal og mulige opdelinger · valgfrit':'Review visit estimates and possible splits · optional',
 'Se manuelle forslag; opdeling kræver fortsat særskilt kontrol og godkendelse.':'Review manual suggestions; splitting still requires separate review and approval.'
});

const SplitSuggestions={
 target:50,boxOnly:true,revision:null,current:null,
 available(){return !state?.profile||ProfilesUI.has('cards.view','loans.view','geo.view');},
 count(c){
  const rows=c.addresses;
  if(!Array.isArray(rows)||!rows.length||rows.some(r=>r.count_unknown||!Number.isSafeInteger(r.count)||r.count<0))return null;
  const count=rows.reduce((sum,r)=>sum+r.count,0);return Number.isSafeInteger(count)?count:null;
 },
 plan(cards,loans,target,boxOnly=true){
  if(!Number.isInteger(target)||target<1||target>1000)throw Error('Vælg et helt antal fra 1 til 1.000.');
  const active=new Set(loans.filter(l=>!l.returned).map(l=>l.card_id));
  const live=cards.filter(c=>!c.archived),ownership=new Map();
  for(const c of live)for(const id of new Set(c.address_ids||[]))ownership.set(id,(ownership.get(id)||0)+1);
  const inBox=c=>!active.has(c.id)&&!c.in_folder;
  const metadata=new Map(live.map(c=>{
   const count=this.count(c),units=Array.isArray(c.geo_addresses)?c.geo_addresses:[],ids=new Set(units.map(a=>a.id));
   const duplicate=units.some(a=>ownership.get(a.id)>1);
   const exact=units.length>0&&ids.size===units.length&&units.every(a=>typeof a.id==='string'&&a.id&&Number.isSafeInteger(a.count)&&a.count>=0&&!a.count_unknown&&!a.retired)&&
    Array.isArray(c.address_ids)&&c.address_ids.length===ids.size&&c.address_ids.every(id=>ids.has(id))&&units.reduce((sum,a)=>sum+a.count,0)===count;
   return [c.id,{c,count,units,duplicate,exact,roads:new Set(units.filter(a=>typeof a.road==='string'&&a.road.trim()&&typeof a.postcode==='string'&&a.postcode.trim()).map(a=>JSON.stringify([a.road,a.postcode])))}];
  }));
  const pool=[...metadata.values()].filter(m=>!boxOnly||inBox(m.c));
  const oversized=pool.filter(m=>m.count!==null&&m.count>target).sort((a,b)=>b.count-a.count||cmp(a.c.number,b.c.number));
  const choose=(units,limit)=>{
   const chosen=[];let count=0;
   for(const a of [...units].sort((a,b)=>cmp(a.road,b.road)||cmp(a.number,b.number)||cmp(a.id,b.id)))if(a.count>0&&count+a.count<=limit){chosen.push(a);count+=a.count;}
   return {units:chosen,count};
  };
  const suggestions=oversized.slice(0,100).map(m=>{
   const parts=Math.max(1,Math.round(m.count/target)),issued=active.has(m.c.id),result={...m,parts,issued,moves:[],split:null};
   if(issued||!m.exact||m.duplicate||m.c.temporary)return result;
   if(parts>1){const selected=choose(m.units,Math.round(m.count/parts));if(selected.count&&selected.units.length<m.units.length)result.split=selected;}
   const targets=pool.filter(t=>t.c.id!==m.c.id&&!active.has(t.c.id)&&!t.c.temporary&&t.count!==null&&t.count<target&&t.exact&&!t.duplicate&&
    m.c.area_id&&t.c.area_id===m.c.area_id&&t.c.kind===m.c.kind&&[...m.roads].some(r=>t.roads.has(r)))
    .sort((a,b)=>b.count-a.count||cmp(a.c.number,b.c.number)).slice(0,10);
   for(const t of targets){
    const selected=choose(m.units.filter(a=>t.roads.has(JSON.stringify([a.road,a.postcode]))),Math.min(m.count-target,target-t.count));
    if(selected.count&&selected.units.length<m.units.length)result.moves.push({target:t.c,...selected,sourceCount:m.count-selected.count,targetCount:t.count+selected.count});
    if(result.moves.length===3)break;
   }
   return result;
  });
  return {suggestions,total:oversized.length,unknown:pool.filter(m=>m.count===null).length};
 },
 entry(){return this.available()?`<div class="notice"><h3>${ui('Opdelingsforslag')}</h3><p>${ui('Forslag ud fra indlæste besøgstal. Ingen kort, adresser, datoer eller udleveringer ændres.')}</p><button data-split-suggestions="open">${ui('Se manuelle opdelingsforslag')}</button></div>`:'';},
 async open(){
  if(!this.available())return;await closeRequested();if(el('dialog').open)return;
  try{const options=JSON.parse(localStorage.getItem('ltm-split-suggestions'));if(Number.isInteger(options?.target)&&options.target>=1&&options.target<=1000)this.target=options.target;if(typeof options?.boxOnly==='boolean')this.boxOnly=options.boxOnly;}catch{}
  openDialog(`<h2>${ui('Opdelingsforslag')}</h2><p>${ui('Forslag ud fra indlæste besøgstal. Ingen kort, adresser, datoer eller udleveringer ændres.')}</p><label for="splitTarget">${ui('Ca. besøg pr. kort')}</label><input id="splitTarget" type="number" min="1" max="1000" step="1" value="${this.target}"><label class="check"><input id="splitBoxOnly" type="checkbox" ${this.boxOnly?'checked':''}>${ui('Kun kort i kassen')}</label><p class="hint">${ui('Målet og filteret huskes i denne browser.')}</p><p class="hint">${ui('Kort i mappen og udleverede kort er skjult, når kassefilteret er valgt. Modtagerkort skal altid være hjemme.')}</p><div id="splitSuggestionResults" aria-live="polite"></div><p class="hint">${ui('Alternativerne skal vurderes hver for sig. Kontrollér geografien og genberegn efter en ændring.')}</p><p class="notice">${ui('Flytning til eksisterende kort samt valg af gennemgangsdato eller midlertidigt kort følger senere. Forslagene flytter intet.')}</p><p class="hint">${ui('Historik bevares på de oprindelige kort. Et nyt kort får ingen opdigtet gennemgang og skal kontrolleres og genprintes.')}</p><button data-action="close">${ui('Luk')}</button>`,I18n.language());
  this.paint();
 },
 addresses(units){return `<details><summary>${ui('Se foreslåede adresser')}</summary><ul>${units.map(a=>`<li style="overflow-wrap:anywhere">${esc(a.label||[a.road,a.number,a.floor,a.door].filter(Boolean).join(' '))} · ${esc(a.count)}</li>`).join('')}</ul></details>`;},
 paint(){
  const node=el('splitSuggestionResults');if(!node||!this.available())return;
  const value=el('splitTarget').value;this.target=value.trim()?Number(value):NaN;this.boxOnly=el('splitBoxOnly').checked;
  try{this.current=this.plan(state.cards||[],state.loans||[],this.target,this.boxOnly);}catch{this.current=null;node.innerHTML=`<p role="alert">${ui('Vælg et helt antal fra 1 til 1.000.')}</p>`;return;}
  try{localStorage.setItem('ltm-split-suggestions',JSON.stringify({target:this.target,boxOnly:this.boxOnly}));}catch{}
  this.revision=state.revision;
  const list=this.current.suggestions;
  node.innerHTML=`<p>${ui('Viser {shown} af {total} kort over målet.',{shown:list.length,total:this.current.total})}</p><p class="hint">${ui('{count} kort har ukendt eller ugyldigt besøgstal og bruges ikke i beregningen.',{count:this.current.unknown})} ${ui('Besøgstal er skøn, ikke registrerede husbesøg.')}</p>${list.map(m=>`<section class="panel" data-split-card="${esc(m.c.id)}"><h3>${ui('Kort')} ${esc(m.c.number)} · ${esc(m.count)}</h3><p style="overflow-wrap:anywhere">${esc(m.c.name||'')}</p><p>${m.parts>1?ui('Forslag: cirka {parts} kort med {count} besøg pr. kort.',{parts:m.parts,count:Math.round(m.count/m.parts)}):ui('Et ekstra kort alene vil give for små kort. Undersøg manuel omfordeling.')}</p>${m.issued?`<p class="notice">${ui('Udleveret kort · planlæg først ændringen, når kortet er afleveret.')}</p>`:m.duplicate?`<p class="notice">${ui('Dublerede adressevalg skal afklares før opdeling.')}</p>`:!m.exact||m.c.temporary?`<p class="hint">${ui('Præcist adressevalg mangler eller stemmer ikke med besøgstallet. Intet adressevalg gættes.')}</p>`:''}${m.split?`<p>${ui('Muligt nyt kort: {count} besøg · tilbage på kortet: {remaining}.',{count:m.split.count,remaining:m.count-m.split.count})}</p>${this.addresses(m.split.units)}${!state.profile||ProfilesUI.canAction('card.restructure.preview')?`<button data-split-suggestions="split" data-id="${esc(m.c.id)}">${ui('Gennemgå opdeling til nyt kort')}</button>`:''}`:''}${m.moves.map(move=>`<div class="notice"><p>${ui('Mulig omfordeling til kort {number}: {count} besøg · forventede skøn {source} / {target}.',{number:move.target.number,count:move.count,source:move.sourceCount,target:move.targetCount})}</p><p class="hint">${ui('Samme område, type og vejnavn. Det er ikke en kontrol af geografisk sammenhæng.')}</p>${this.addresses(move.units)}<button data-split-suggestions="card" data-id="${esc(move.target.id)}">${ui('Åbn modtagerkort')}</button></div>`).join('')}<button data-split-suggestions="card" data-id="${esc(m.c.id)}">${ui('Åbn kort')}</button></section>`).join('')||`<p>${ui('Ingen kort over målet i denne visning.')}</p>`}`;
 },
 async handle(action,id){
  if(action==='open')return this.open();if(!this.available()||!el('splitSuggestionResults'))return;
  if(this.revision!==state.revision){this.paint();toast('Oversigten er ændret. Gennemgå de opdaterede forslag igen.');return;}
  if(action==='card'){if(card(id))detail(id);return;}
  const proposal=this.current?.suggestions.find(m=>m.c.id===id);
  if(action!=='split'||!proposal?.split||loanFor(id)||state.profile&&!ProfilesUI.canAction('card.restructure.preview'))return;
  Workspace.restructureForm('split',id);
  const chosen=new Set(proposal.split.units.map(a=>a.id)),form=el('dialog').querySelector('[data-work-form=restructure]');
  for(const input of form.querySelectorAll('input[name=address_ids]'))input.checked=chosen.has(input.value);
  if(typeof FormDrafts!=='undefined')FormDrafts.capture(form);
 }
};
document.addEventListener('click',event=>{const b=event.target.closest('[data-split-suggestions]');if(!b)return;event.preventDefault();SplitSuggestions.handle(b.dataset.splitSuggestions,b.dataset.id).catch(error=>toast(error));});
document.addEventListener('input',event=>{if(event.target.id==='splitTarget')SplitSuggestions.paint();});
document.addEventListener('change',event=>{if(event.target.id==='splitBoxOnly')SplitSuggestions.paint();});
