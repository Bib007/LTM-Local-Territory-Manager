'use strict';
// Local planning only. Existing explicit preview/confirmation owns any later split.
Object.assign(I18n.english,{
 "Flyt adresser til kortet":"Move addresses to this card",
 "Afslut midlertidig flytning":"Finalize interim transfer",
 "Midlertidige flytninger":"Interim transfers",
 "Flytning fra kort {source} til kort {target}":"Move from card {source} to card {target}",
 "Vælg dato- og kortforløb":"Choose date and card workflow",
 "Vælg et forløb":"Choose a workflow",
 "Brug nyeste kendte dato til planlægning":"Use the latest known date for scheduling",
 "Opret et midlertidigt kort først":"Create an interim card first",
 "Datoen styrer kortets alder i planlægningen. Gennemgange og S-13-historik ændres ikke.":"The date controls card age in scheduling. Completion events and S-13 history stay unchanged.",
 "Midlertidigt kortnummer":"Interim card number",
 "Navn på det midlertidige kort (valgfrit)":"Interim card name (optional)",
 "Kortet får sit eget nummer og kan udleveres. Modtagerkortet ændres først efter aflevering og særskilt afslutning.":"The card gets its own number and can be issued. The receiving card changes only after return and explicit finalization.",
 "Kontrollér flytningen":"Preview the move",
 "Bekræft flytning":"Confirm address move",
 "Bekræft midlertidigt kort":"Confirm interim card",
 "Planlægningsdato: {date}":"Scheduling reference: {date}",
 "Ukendt planlægningsdato":"Unknown scheduling reference",
 "Besøg efter ændringen: {source} på kilden og {target} på modtageren.":"Visit estimates after the change: {source} on the source and {target} on the receiver.",
 "Gennemgangshistorikken bevares. Kontrollér grænserne og genprint begge ændrede sider.":"Completion history is retained. Review the boundaries and reprint both changed sides.",
 "Midlertidigt kort til kort {number}":"Interim card for card {number}",
 "Aflevér kortet og læg begge kort i kassen før afslutning. Genprint derefter modtagerkortet med dets eget nummer.":"Return the card and put both cards in the box before finalizing. Then reprint the receiver with its own number.",
 "Brug opdelingsforslag til at afslutte det midlertidige forløb.":"Use Split suggestions to finalize the interim workflow.",
 "Flytningen er gemt. Kontrollér grænserne og genprint de ændrede sider.":"The move is saved. Review the boundaries and reprint the changed sides.",
 "Vælg to forskellige kort til flytningen.":"Choose two different cards for the move.",
 "Begge kort skal være færdige, afleverede og ligge i kassen.":"Both cards must be complete, returned and in the box.",
 "Vælg kort med samme område og type.":"Choose cards with the same area and type.",
 "Afslut den midlertidige flytning først.":"Finalize the interim transfer first.",
 "Det midlertidige kort eller modtageren er ændret. Kontrollér forløbet igen.":"The interim card or receiver has changed. Review the workflow again.",
 "Kontrollér kortenes præcise adressevalg før flytning.":"Review exact address membership before moving.",
 "Adressedata er ændret. Opdater kortet i korteditoren før flytning.":"Address data has changed. Update the card in the map editor before moving.",
 "Vælg hele adresseenheder til flytningen.":"Select whole address units to move.",
 "Vælg nogle, men ikke alle, adresser. Et midlertidigt kort afsluttes samlet.":"Select some, but not all, addresses. An interim card is finalized as a whole.",
 "Adresserne findes på flere kort. Ret kortkontrollen først.":"The addresses belong to multiple cards. Resolve card checks first.",
 "Opdel distriktskort":"Split territory card",
 "Sammenlæg distriktskort":"Merge territory cards",
 "Ingen ændring foretages, før du har set en forhåndsvisning og skrevet en ekstra bekræftelse. Udleverede kort skal afleveres først.":"No change is made until you review a preview and type the confirmation. Issued cards must be returned first.",
 "Vælg 2–20 færdige kort":"Choose 2–20 complete cards",
 "Kort {number} · vælg adresser til det nye kort":"Card {number}: choose addresses for the new card",
 "Find vej eller husnummer":"Find street or house number",
 "Find adresse til opdeling":"Find an address to split off",
 "Nyt kortnummer":"New card number",
 "Navn på det nye kort":"New card name",
 "Vis ændringen først":"Preview the change",
 "Historik bevares på de oprindelige kort. Nye kort får ingen opdigtet gennemgang. Grænser er forslag og skal kontrolleres. Forsider og IB-bagsider skal genprintes.":"History stays with the original cards. New cards get no invented completion. Boundaries are suggestions and must be checked. Reprint fronts and do-not-call backs.",

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
 'Se manuelle forslag; opdeling kræver fortsat særskilt kontrol og godkendelse.':'Review manual suggestions; splitting still requires separate review and approval.',
 '{count} distriktskort overstiger den fastsatte grænse på {limit} besøg.':'{count} territory cards exceed the configured limit of {limit} visits.',
 '{count} forslag er skjult efter vurdering.':'{count} suggestions have been dismissed.',
 'Menighedens faste grænse indstilles under Indstillinger → Menighed og mappe. Dette tal kan ændres midlertidigt for at prøve andre forslag; kun kassefilteret huskes i browseren.':'Set the congregation limit in Settings → Congregation and carry folder. You may temporarily try another target here; only the box filter is saved in the browser.',
 'Se bort fra forslag':'Dismiss suggestion','Gendan forslag':'Restore suggestion','Skjulte forslag':'Dismissed suggestions',
 'Hvorfor skal dette forslag ignoreres?':'Why should this suggestion be dismissed?',
 'Kortet findes ikke længere.':'Card no longer exists.'
});

const SplitSuggestions={
 target:50,boxOnly:true,revision:null,current:null,
 available(){return !state?.profile||ProfilesUI.has('cards.view','loans.view','geo.view');},
 count(c){
  const rows=c.addresses;
  if(!Array.isArray(rows)||!rows.length||rows.some(r=>r.count_unknown||!Number.isSafeInteger(r.count)||r.count<0))return null;
  const count=rows.reduce((sum,r)=>sum+r.count,0);return Number.isSafeInteger(count)?count:null;
 },
 fingerprint(c,target){return JSON.stringify([c.id,c.number,this.count(c),target,[...(c.address_ids||[])].sort()]);},
 ignored(){return state?.settings?.split_suggestion_ignored||{};},
 visitLimit(){const n=state?.settings?.split_visit_limit;return Number.isInteger(n)&&n>=1&&n<=1000?n:50;},
 plan(cards,loans,target,boxOnly=true,ignored={}){
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
  const pool=[...metadata.values()].filter(m=>!m.c.interim_transfer&&(!boxOnly||inBox(m.c)));
  const candidates=pool.filter(m=>m.count!==null&&m.count>target);
  const oversized=candidates.filter(m=>ignored[m.c.id]?.fingerprint!==this.fingerprint(m.c,target)).sort((a,b)=>b.count-a.count||cmp(a.c.number,b.c.number));
  const choose=(units,limit)=>{
   const chosen=[];let count=0;
   for(const a of [...units].sort((a,b)=>cmp(a.road,b.road)||cmp(a.number,b.number)||cmp(a.id,b.id)))if(a.count>0&&count+a.count<=limit){chosen.push(a);count+=a.count;}
   return {units:chosen,count};
  };
  const suggestions=oversized.slice(0,100).map(m=>{
   const parts=Math.max(1,Math.round(m.count/target)),issued=active.has(m.c.id),result={...m,parts,issued,moves:[],split:null};
   if(issued||m.c.in_folder||!m.exact||m.duplicate||m.c.temporary)return result;
   if(parts>1){const selected=choose(m.units,Math.round(m.count/parts));if(selected.count&&selected.units.length<m.units.length)result.split=selected;}
   const targets=pool.filter(t=>t.c.id!==m.c.id&&!active.has(t.c.id)&&!t.c.in_folder&&!t.c.temporary&&t.count!==null&&t.count<target&&t.exact&&!t.duplicate&&
    m.c.area_id&&t.c.area_id===m.c.area_id&&t.c.kind===m.c.kind&&[...m.roads].some(r=>t.roads.has(r)))
    .sort((a,b)=>b.count-a.count||cmp(a.c.number,b.c.number)).slice(0,10);
   for(const t of targets){
    const selected=choose(m.units.filter(a=>t.roads.has(JSON.stringify([a.road,a.postcode]))),Math.min(m.count-target,target-t.count));
    if(selected.count&&selected.units.length<m.units.length)result.moves.push({target:t.c,...selected,sourceCount:m.count-selected.count,targetCount:t.count+selected.count});
    if(result.moves.length===3)break;
   }
   return result;
  });
  return {suggestions,total:oversized.length,ignored:candidates.length-oversized.length,unknown:pool.filter(m=>m.count===null).length};
 },
 entry(){
  if(!this.available())return '';
  const limit=this.visitLimit(),report=this.plan(state.cards||[],state.loans||[],limit,false,this.ignored());
  return `<div class="notice" role="status"><h3>${ui('Opdelingsforslag')}</h3><p>${ui('{count} distriktskort overstiger den fastsatte grænse på {limit} besøg.',{count:report.total,limit})} ${report.ignored?ui('{count} forslag er skjult efter vurdering.',{count:report.ignored}):''}</p><button data-split-suggestions="open">${ui('Se manuelle opdelingsforslag')}</button></div>`;
 },
 async open(){
  if(!this.available())return;await closeRequested();if(el('dialog').open)return;
  this.target=this.visitLimit();
  try{const options=JSON.parse(localStorage.getItem('ltm-split-suggestions'));if(typeof options?.boxOnly==='boolean')this.boxOnly=options.boxOnly;}catch{}
  openDialog(`<h2>${ui('Opdelingsforslag')}</h2><p>${ui('Forslag ud fra indlæste besøgstal. Ingen kort, adresser, datoer eller udleveringer ændres.')}</p><label for="splitTarget">${ui('Ca. besøg pr. kort')}</label><input id="splitTarget" type="number" min="1" max="1000" step="any" value="${this.target}"><label class="check"><input id="splitBoxOnly" type="checkbox" ${this.boxOnly?'checked':''}>${ui('Kun kort i kassen')}</label><p class="hint">${ui('Menighedens faste grænse indstilles under Indstillinger → Menighed og mappe. Dette tal kan ændres midlertidigt for at prøve andre forslag; kun kassefilteret huskes i browseren.')}</p><p class="hint">${ui('Kort i mappen og udleverede kort er skjult, når kassefilteret er valgt. Modtagerkort skal altid være hjemme.')}</p><div id="splitSuggestionResults" aria-live="polite"></div><p class="hint">${ui('Alternativerne skal vurderes hver for sig. Kontrollér geografien og genberegn efter en ændring.')}</p><p class="notice">${ui('Datoen styrer kortets alder i planlægningen. Gennemgange og S-13-historik ændres ikke.')}</p><p class="hint">${ui('Historik bevares på de oprindelige kort. Et nyt kort får ingen opdigtet gennemgang og skal kontrolleres og genprintes.')}</p><button data-action="close">${ui('Luk')}</button>`,I18n.language());
  this.paint();
 },
 addresses(units){return `<details><summary>${ui('Se foreslåede adresser')}</summary><ul>${units.map(a=>`<li style="overflow-wrap:anywhere">${esc(a.label||[a.road,a.number,a.floor,a.door].filter(Boolean).join(' '))} · ${esc(a.count)}</li>`).join('')}</ul></details>`;},
 paint(){
  const node=el('splitSuggestionResults');if(!node||!this.available())return;
  const value=el('splitTarget').value;this.target=value.trim()?Number(value):NaN;this.boxOnly=el('splitBoxOnly').checked;
  try{this.current=this.plan(state.cards||[],state.loans||[],this.target,this.boxOnly,this.ignored());}catch{this.current=null;node.innerHTML=`<p role="alert">${ui('Vælg et helt antal fra 1 til 1.000.')}</p>`;return;}
  try{localStorage.setItem('ltm-split-suggestions',JSON.stringify({boxOnly:this.boxOnly}));}catch{}
  this.revision=state.revision;
  const list=this.current.suggestions;
  node.innerHTML=`${this.pendingHTML()}${this.ignoredHTML()}<p>${ui('Viser {shown} af {total} kort over målet.',{shown:list.length,total:this.current.total})}</p><p class="hint">${ui('{count} kort har ukendt eller ugyldigt besøgstal og bruges ikke i beregningen.',{count:this.current.unknown})} ${ui('Besøgstal er skøn, ikke registrerede husbesøg.')}</p>${list.map(m=>`<section class="panel" data-split-card="${esc(m.c.id)}"><h3>${ui('Kort')} ${esc(m.c.number)} · ${esc(m.count)}</h3><p style="overflow-wrap:anywhere">${esc(m.c.name||'')}</p><p>${m.parts>1?ui('Forslag: cirka {parts} kort med {count} besøg pr. kort.',{parts:m.parts,count:Math.round(m.count/m.parts)}):ui('Et ekstra kort alene vil give for små kort. Undersøg manuel omfordeling.')}</p>${m.issued||m.c.in_folder?`<p class="notice">${ui(m.issued?'Udleveret kort · planlæg først ændringen, når kortet er afleveret.':'Begge kort skal være færdige, afleverede og ligge i kassen.')}</p>`:m.duplicate?`<p class="notice">${ui('Dublerede adressevalg skal afklares før opdeling.')}</p>`:!m.exact||m.c.temporary?`<p class="hint">${ui('Præcist adressevalg mangler eller stemmer ikke med besøgstallet. Intet adressevalg gættes.')}</p>`:''}${m.split?`<p>${ui('Muligt nyt kort: {count} besøg · tilbage på kortet: {remaining}.',{count:m.split.count,remaining:m.count-m.split.count})}</p>${this.addresses(m.split.units)}${!state.profile||ProfilesUI.canAction('card.restructure.preview')?`<button data-split-suggestions="split" data-id="${esc(m.c.id)}">${ui('Gennemgå opdeling til nyt kort')}</button>`:''}`:''}${m.moves.map(move=>`<div class="notice"><p>${ui('Mulig omfordeling til kort {number}: {count} besøg · forventede skøn {source} / {target}.',{number:move.target.number,count:move.count,source:move.sourceCount,target:move.targetCount})}</p><p class="hint">${ui('Samme område, type og vejnavn. Det er ikke en kontrol af geografisk sammenhæng.')}</p>${this.addresses(move.units)}${!state.profile||ProfilesUI.canAction('card.restructure.preview')?`<button data-split-suggestions="transfer" data-id="${esc(m.c.id)}" data-target="${esc(move.target.id)}">${ui('Flyt adresser til kortet')}</button>`:''}<button data-split-suggestions="card" data-id="${esc(move.target.id)}">${ui('Åbn modtagerkort')}</button></div>`).join('')}${!state.profile||ProfilesUI.canAction('split.suggestion.ignore')?`<button data-split-suggestions="ignore" data-id="${esc(m.c.id)}">${ui('Se bort fra forslag')}</button>`:''}<button data-split-suggestions="card" data-id="${esc(m.c.id)}">${ui('Åbn kort')}</button></section>`).join('')||`<p>${ui('Ingen kort over målet i denne visning.')}</p>`}`;
 },
 ignoredHTML(){
  if(state.profile&&!ProfilesUI.canAction('split.suggestion.restore'))return '';
  const records=Object.entries(this.ignored());
  if(!records.length)return '';
  return `<details><summary>${ui('Skjulte forslag')} (${records.length})</summary>${records.map(([id,record])=>{
   const c=card(id);
   return `<div class="line"><div><strong>${ui('Kort')} ${esc(c?.number||'—')}</strong><p class="hint">${esc(record.reason||'')}${!c?' · '+ui('Kortet findes ikke længere.'):''}</p></div>${!state.profile||ProfilesUI.canAction('split.suggestion.restore')?`<button data-split-suggestions="restore" data-id="${esc(id)}">${ui('Gendan forslag')}</button>`:''}</div>`;
  }).join('')}</details>`;
 },
 effectiveDate(c){
  if(typeof c.planning_date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(c.planning_date))return c.planning_date;
  const ref=c.planning_reference,ids=[...(c.address_ids||[])].sort();
  const inherited=ref&&Array.isArray(ref.membership)&&JSON.stringify(ref.membership)===JSON.stringify(ids)?ref.date:null;
  return [c.last_completed,inherited].filter(d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)).sort().at(-1)||null;
 },
 cardNotice(c){
  if(c.interim_transfer?.status==='pending')return `<section class="notice"><strong>${ui('Midlertidigt kort til kort {number}',{number:card(c.interim_transfer.target_id)?.number||c.interim_transfer.target_number})}</strong><p>${ui('Aflevér kortet og læg begge kort i kassen før afslutning. Genprint derefter modtagerkortet med dets eget nummer.')}</p><p>${ui('Brug opdelingsforslag til at afslutte det midlertidige forløb.')}</p></section>`;
  if(!c.planning_reference?.date||this.effectiveDate(c)!==c.planning_reference.date)return '';
  return `<section class="notice">${ui('Planlægningsdato: {date}',{date:fmt(this.effectiveDate(c))})}<p>${ui('Datoen styrer kortets alder i planlægningen. Gennemgange og S-13-historik ændres ikke.')}</p></section>`;
 },
 pendingHTML(){
  const pending=(state.cards||[]).filter(c=>c.interim_transfer?.status==='pending');if(!pending.length)return '';
  return `<section class="panel"><h3>${ui('Midlertidige flytninger')}</h3>${pending.map(c=>{const target=card(c.interim_transfer.target_id),ready=target&&!loanFor(c.id)&&!loanFor(target.id)&&!c.in_folder&&!target.in_folder;return `<article class="line"><div><strong>${ui('Kort')} ${esc(c.number)} → ${esc(target?.number||c.interim_transfer.target_number)}</strong><p>${ui('Aflevér kortet og læg begge kort i kassen før afslutning. Genprint derefter modtagerkortet med dets eget nummer.')}</p></div>${!state.profile||ProfilesUI.canAction('card.restructure.preview')?`<button data-split-suggestions="finalize" data-id="${esc(c.id)}" ${ready?'':'disabled'}>${ui('Afslut midlertidig flytning')}</button>`:''}</article>`;}).join('')}</section>`;
 },
 transferForm(source,target,units,finalize=false){
  if(!source||!target||loanFor(source.id)||loanFor(target.id)||source.in_folder||target.in_folder)throw Error('Begge kort skal være færdige, afleverede og ligge i kassen.');
  const hidden=(name,value)=>`<input type="hidden" name="${name}" value="${esc(value)}">`;
  openDialog(`<h2>${ui(finalize?'Afslut midlertidig flytning':'Flytning fra kort {source} til kort {target}',{source:source.number,target:target.number})}</h2><form data-work-form="redistribute">${hidden('ids',source.id)}${hidden('ids',target.id)}${hidden('target_number',target.number)}${units.map(a=>hidden('address_ids',a.id)).join('')}${this.addresses(units)}${finalize?hidden('policy','finalize'):`<label for="transferPolicy">${ui('Vælg dato- og kortforløb')}</label><select name="policy" id="transferPolicy" required><option value="" data-ui="Vælg et forløb">${esc(I18n.text('Vælg et forløb'))}</option><option value="latest" data-ui="Brug nyeste kendte dato til planlægning">${esc(I18n.text('Brug nyeste kendte dato til planlægning'))}</option><option value="interim" data-ui="Opret et midlertidigt kort først">${esc(I18n.text('Opret et midlertidigt kort først'))}</option></select><p class="hint">${ui('Datoen styrer kortets alder i planlægningen. Gennemgange og S-13-historik ændres ikke.')}</p><div id="interimTransferFields" hidden><label for="interimNumber">${ui('Midlertidigt kortnummer')}</label><input name="interim_number" id="interimNumber" maxlength="30"><label for="interimName">${ui('Navn på det midlertidige kort (valgfrit)')}</label><input name="interim_name" id="interimName" maxlength="50"><p class="hint">${ui('Kortet får sit eget nummer og kan udleveres. Modtagerkortet ændres først efter aflevering og særskilt afslutning.')}</p></div>`}<p class="notice">${ui('Gennemgangshistorikken bevares. Kontrollér grænserne og genprint begge ændrede sider.')}</p>${formEnd('Kontrollér flytningen')}</form>`,I18n.language());
 },
 async handle(action,id,targetId){
  if(action==='open')return this.open();if(!this.available()||!el('splitSuggestionResults'))return;
  if(this.revision!==state.revision){this.paint();toast('Oversigten er ændret. Gennemgå de opdaterede forslag igen.');return;}
  if(action==='card'){if(card(id))detail(id);return;}
  if(action==='restore'){
   if(state.profile&&!ProfilesUI.canAction('split.suggestion.restore'))return;
   await mutate('split.suggestion.restore',{card_id:id},{message:'Opdelingsforslag gendannet'});
   return;
  }
  if(action==='ignore'){
   if(state.profile&&!ProfilesUI.canAction('split.suggestion.ignore'))return;
   if(this.target!==this.visitLimit())throw Error('Se bort fra kræver menighedens faste besøgsgrænse. Nulstil prøvegrænsen først.');
   const proposal=this.current?.suggestions.find(m=>m.c.id===id);if(!proposal)return;
   const reason=window.prompt(I18n.text('Hvorfor skal dette forslag ignoreres?'), '');
   if(reason===null)return;
   if(!reason.trim()||reason.trim().length>300)throw Error('Skriv en begrundelse på 1–300 tegn.');
   await mutate('split.suggestion.ignore',{card_id:id,reason:reason.trim(),fingerprint:this.fingerprint(proposal.c,this.target)},{message:'Forslag markeret Se bort fra'});
   return;
  }
  if(action==='finalize'){const source=card(id),target=card(source?.interim_transfer?.target_id);if(!state.profile||ProfilesUI.canAction('card.restructure.preview'))this.transferForm(source,target,source?.geo_addresses||[],true);return;}
  const proposal=this.current?.suggestions.find(m=>m.c.id===id);
  if(action==='transfer'){const move=proposal?.moves.find(m=>m.target.id===targetId);if(move&&(!state.profile||ProfilesUI.canAction('card.restructure.preview')))this.transferForm(proposal.c,move.target,move.units);return;}
  if(action!=='split'||!proposal?.split||loanFor(id)||card(id)?.in_folder||state.profile&&!ProfilesUI.canAction('card.restructure.preview'))return;
  Workspace.restructureForm('split',id);
  const chosen=new Set(proposal.split.units.map(a=>a.id)),form=el('dialog').querySelector('[data-work-form=restructure]');
  for(const input of form.querySelectorAll('input[name=address_ids]'))input.checked=chosen.has(input.value);
  if(typeof FormDrafts!=='undefined')FormDrafts.capture(form);
 }
};
document.addEventListener('click',event=>{const b=event.target.closest('[data-split-suggestions]');if(!b)return;event.preventDefault();SplitSuggestions.handle(b.dataset.splitSuggestions,b.dataset.id,b.dataset.target).catch(error=>toast(error));});
document.addEventListener('input',event=>{if(event.target.id==='splitTarget')SplitSuggestions.paint();});
document.addEventListener('change',event=>{if(event.target.id==='splitBoxOnly')SplitSuggestions.paint();});

document.addEventListener('change',event=>{const f=event.target.form;if(event.target.id!=='transferPolicy'||f?.dataset.workForm!=='redistribute')return;const interim=event.target.value==='interim';f.querySelector('#interimTransferFields').hidden=!interim;f.elements.interim_number.required=interim;});
