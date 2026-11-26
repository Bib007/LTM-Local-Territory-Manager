'use strict';
/* Quick assignments grid: existing store records only; no client-side shadow history. */
const HistoryGrid={
 query:'',filter:'all',limit:100,busy:false,
 canEdit(){return !state.profile || ProfilesUI.has('cards.view','loans.view','loans.manage','publishers.view','history.view','history.edit');},
 dateText(iso){if(!iso)return '';const parts=iso.split('-');return parts.length===3?parts[2]+'.'+parts[1]+'.'+parts[0]:iso;},
 parseDate(value,required){
  const v=String(value||'').trim();
  if(!v){if(required)throw Error('Udleveringsdatoen skal udfyldes.');return null;}
  let y,m,d,match;
  if((match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(v))){y=Number(match[1]);m=Number(match[2]);d=Number(match[3]);}
  else if((match=/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/.exec(v))){d=Number(match[1]);m=Number(match[2]);y=Number(match[3]);}
  else throw Error('Brug DD.MM.ÅÅÅÅ eller ÅÅÅÅ-MM-DD.');
  const stamp=String(y).padStart(4,'0')+'-'+String(m).padStart(2,'0')+'-'+String(d).padStart(2,'0');
  const candidate=new Date(Date.UTC(y,m-1,d));
  if(y<1900||candidate.toISOString().slice(0,10)!==stamp)throw Error('Datoen findes ikke.');
  if(stamp>state.today)throw Error('Datoen må ikke ligge i fremtiden.');
  return stamp;
 },
 datesFor(id){return state.completions.filter(e=>e.card_id===id).sort((a,b)=>a.date.localeCompare(b.date));},
 loansFor(id){return state.loans.filter(l=>l.card_id===id).sort((a,b)=>a.assigned.localeCompare(b.assigned)||a.id.localeCompare(b.id));},
 problem(c,loans){return loans.some(l=>l.returned&&l.returned<l.assigned)||loans.some((l,i)=>loans.some((other,j)=>i!==j&&l.assigned<(other.returned||'9999-12-31')&&other.assigned<(l.returned||'9999-12-31')))||Boolean(c.archived&&loans.some(l=>!l.returned));},
 visible(){
  const q=this.query.trim().toLocaleLowerCase('da-DK');
  return [...state.cards,...(state.archived_cards||[])].filter(c=>{
   const loans=this.loansFor(c.id),active=loans.find(l=>!l.returned);
   const issue=this.problem(c,loans),hay=[c.number,c.name,areaName(c.area_id),...loans.map(l=>publisherName(l.publisher_id,''))].join(' ').toLocaleLowerCase('da-DK');
   return (!q||hay.includes(q))&&(this.filter==='all'||this.filter==='active'&&active||this.filter==='empty'&&!loans.length||this.filter==='review'&&issue);
  }).sort((a,b)=>cmp(a.number,b.number));
 },
 dateCell(loan,field){
  if(!loan)return '<span class="hg-empty">—</span>';
  const raw=loan[field]||'',label=field==='assigned'?'Udleveret':'Indleveret',editable=this.canEdit();
  if(!editable)return '<span>'+esc(this.dateText(raw)||'—')+'</span>';
  const attrs=' data-hg-id="'+esc(loan.id)+'" data-hg-field="'+field+'"';
  return '<div class="hg-date"><input type="text" class="hg-date-text"'+attrs+' data-hg-date="text" aria-label="'+label+' · DD.MM.ÅÅÅÅ" placeholder="DD.MM.ÅÅÅÅ" value="'+esc(this.dateText(raw))+'" inputmode="numeric" autocomplete="off" maxlength="10" title="DD.MM.ÅÅÅÅ eller ÅÅÅÅ-MM-DD"><input type="date" class="hg-date-picker"'+attrs+' data-hg-date="picker" aria-label="Vælg '+label.toLocaleLowerCase('da-DK')+' i kalender" max="'+esc(state.today)+'" value="'+esc(raw)+'"></div>';
 },
 details(c,loans){
  const known=new Set(loans.map(l=>l.id)),unlinked=this.datesFor(c.id).filter(e=>!e.loan_id||!known.has(e.loan_id));
  const ordered=loans.slice().reverse(),older=ordered.slice(3);
  return '<details class="hg-details"><summary>Hele historikken ('+loans.length+' udleveringer · '+this.datesFor(c.id).length+' gennemgange)</summary><div class="hg-full">'+
    ordered.slice(0,3).map(l=>Workspace.loanLine(l)).join('')+
    (older.length?'<details><summary>'+ui('{count} tidligere udleveringer',{count:older.length})+'</summary>'+older.map(l=>Workspace.loanLine(l)).join('')+'</details>':'')+
    (unlinked.length?'<h4>Øvrige gennemgange</h4>'+unlinked.map(e=>'<p>'+esc(this.dateText(e.date))+' · '+(e.loan_id?'Udlevering ikke fundet':'Uden udlevering')+'</p>').join(''):'')+
    (!loans.length&&!unlinked.length?'<p>Ingen historik registreret</p>':'')+'</div></details>';
 },
 row(c){
  const loans=this.loansFor(c.id),latest=loans.slice(-2),active=loans.find(l=>!l.returned),issue=this.problem(c,loans);
  const placement=active?'Udleveret · '+publisherName(active.publisher_id):c.archived?'Arkiveret':c.in_folder?'I mappen':'I kassen';
  const edit=this.canEdit()&&!c.archived;
  const status=issue?'Kontrollér rækkefølge':placement;
  const statusClass=issue?'hg-status-warning':active?'hg-status-active':'hg-status-neutral';
  const history=latest.length?latest.map((l,i)=>{
   const title=latest.length===2&&i===0?'Forrige udlevering':'Seneste udlevering';
   return '<section class="hg-period" aria-label="'+title+'">'+
    '<div class="hg-period-heading"><strong>'+title+'</strong><span class="hg-period-state">'+(l.returned?'Afsluttet':'Aktiv')+'</span></div>'+
    '<p class="hg-period-publisher">'+esc(publisherName(l.publisher_id))+'</p>'+
    '<div class="hg-fields"><div class="hg-field"><span class="hg-field-label">Udleveret</span>'+this.dateCell(l,'assigned')+'</div>'+
    '<div class="hg-field"><span class="hg-field-label">Indleveret</span>'+this.dateCell(l,'returned')+'</div></div></section>';
  }).join(''):'<p class="hg-no-loans">Ingen udleveringer registreret endnu.</p>';
  return '<article class="hg-card'+(issue?' hg-warning':'')+'" data-hg-card="'+esc(c.id)+'">'+
   '<header class="hg-card-header"><div class="hg-card-identity"><strong class="hg-card-number">'+esc(c.number)+'</strong>'+
   '<div class="hg-card-description"><h3>'+esc(c.name||areaName(c.area_id))+'</h3><small>Senest gennemgået: '+esc(this.dateText(c.last_completed)||'ukendt')+'</small></div></div>'+
   '<div class="hg-card-actions"><span class="hg-status '+statusClass+'">'+esc(status)+'</span>'+
   (edit?'<button type="button" data-hg-add="'+esc(c.id)+'">+ Udlevering</button>':'')+'</div></header>'+
   '<div class="hg-periods">'+history+'</div>'+this.details(c,loans)+'</article>';
 },

 rows(){const cards=this.visible();return cards.slice(0,this.limit).map(c=>this.row(c)).join('')||'<p class="hg-empty-state" role="status">Ingen kort matcher søgningen.</p>';},

 render(){
  const total=this.visible().length,editable=this.canEdit();
  return '<section class="panel hg-panel"><div class="hg-intro"><h2>Gennemgange & historik</h2>'+
   '<p class="hint">Se kortenes seneste udleveringer og gennemgange samlet. Åbn hele historikken på det kort, du vil undersøge.</p></div>'+
   '<div class="hg-toolbar"><label class="hg-search-label">Søg kort, område eller forkynder <input id="hg-search" type="search" value="'+esc(this.query)+'" placeholder="Kortnummer, område eller navn" autocomplete="off"></label>'+
   '<label>Vis <select id="hg-filter"><option value="all"'+(this.filter==='all'?' selected':'')+'>Alle kort</option><option value="active"'+(this.filter==='active'?' selected':'')+'>Aktuelt udleverede</option><option value="empty"'+(this.filter==='empty'?' selected':'')+'>Uden historik</option><option value="review"'+(this.filter==='review'?' selected':'')+'>Ulogisk rækkefølge</option></select></label>'+
   '<button type="button" id="hg-reset"'+(this.query||this.filter!=='all'?'':' disabled')+'>'+ui('Nulstil filtre')+'</button>'+
   '<div class="hg-toolbar-actions"><button type="button" data-history-import="open">Importér CSV / S-13</button><button type="button" data-action="backup">Sikkerhedskopi</button>'+
   (state.undo_available&&editable?'<button type="button" data-work="undo">Fortryd sidste ændring</button>':'')+'</div></div>'+
   '<div class="hg-list" id="hg-body">'+this.rows()+'</div>'+
   '<div class="hg-footer"><p id="hg-count" class="hint" role="status">Viser '+Math.min(this.limit,total)+' af '+total+' kort</p>'+
   (total>this.limit?'<button type="button" data-hg-more>Vis 100 flere kort</button>':'')+'</div>'+
   '<details class="hg-help"><summary>Sådan bruger du historikken</summary>'+
   '<p>De seneste to udleveringer vises i datoorden, fra venstre mod højre på store skærme. En indlevering er ikke automatisk en gennemgang. Tom dato betyder ukendt eller stadig udleveret.</p>'+
   (editable?'<p>Ret en dato med DD.MM.ÅÅÅÅ og Enter/Tab, eller brug kalenderen. Hver ændring gemmes særskilt. Eksisterende gennemgange flyttes kun, når valideringen tillader det. Brug import til mange historiske rækker, og tag backup før større rettelser.</p>':'<p>Du har læseadgang. Redigering kræver særskilte rettigheder.</p>')+
   '</details></section>';
 },

 draw(){
  const body=document.getElementById('hg-body');if(!body)return;
  body.innerHTML=this.rows();
  const count=this.visible().length,status=document.getElementById('hg-count');
  if(status)status.textContent='Viser '+Math.min(count,this.limit)+' af '+count+' kort';
  const more=document.querySelector('[data-hg-more]');if(more)more.hidden=count<=this.limit;
  const reset=document.getElementById('hg-reset');if(reset)reset.disabled=!this.query&&this.filter==='all';
 },
 openAdd(id){
  if(!this.canEdit())throw Error('Du har ikke rettighed til at ændre historikken.');
  const c=[...state.cards].find(c=>c.id===id);
  if(!c)throw Error('Kortet er ikke tilgængeligt.');
  const publishers=state.publishers.slice().sort((a,b)=>cmp(a.name,b.name));
  if(!publishers.length)throw Error('Opret en forkynder under Forkyndere først.');
  openDialog('<h2>Registrér udlevering · kort '+esc(c.number)+'</h2>'+
   '<p>Tilføjer en ny registrering. Eksisterende udleveringer og gennemgange overskrives aldrig.</p>'+
   '<form data-hg-form data-hg-card="'+esc(c.id)+'"><label>Forkynder <select name="publisher_id" required><option value="">Vælg forkynder</option>'+
   publishers.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join('')+'</select></label>'+
   '<label>Udleveret <input name="assigned" required placeholder="DD.MM.ÅÅÅÅ" maxlength="10" inputmode="numeric" autocomplete="off"></label>'+
   '<label>Indleveret (valgfri) <input name="returned" placeholder="DD.MM.ÅÅÅÅ" maxlength="10" inputmode="numeric" autocomplete="off"></label>'+
   '<label class="check"><input type="checkbox" name="completed"> Kortet blev gennemgået ved indlevering (opretter eller knytter præcis én gennemgang, besøgstal ukendt)</label>'+
   '<p class="hint">Uden indleveringsdato bliver udleveringen aktiv. Uden markering oprettes ingen gennemgang.</p>'+
   '<div id="formError" class="formError" role="alert"></div><div class="actions"><button class="primary" type="submit">Gem udlevering</button><button type="button" data-action="close">Luk</button></div></form>',I18n.language());
 },
 async saveDate(input){
  if(!this.canEdit()||this.busy)return;
  const loan=state.loans.find(l=>l.id===input.dataset.hgId);
  if(!loan)return;
  const field=input.dataset.hgField,raw=input.dataset.hgDate==='picker'?input.value:input.value.trim();
  let stamp;try{stamp=this.parseDate(raw,field==='assigned');}catch(error){toast(error);input.focus();return;}
  if(stamp===(loan[field]||null))return;
  this.busy=true;
  try{await mutate('history.grid.edit',{id:loan.id,field,date:stamp,revision:state.revision},{close:false,message:'Historik rettet'});}
  catch(error){input.value=input.dataset.hgDate==='picker'?(loan[field]||''):this.dateText(loan[field]);}
  finally{this.busy=false;}
 },
 async submit(form){
  if(this.busy||!this.canEdit())return;
  const data=Object.fromEntries(new FormData(form));
  const assigned=this.parseDate(data.assigned,true),returned=this.parseDate(data.returned,false);
  if(returned&&returned<assigned)throw Error('Indlevering må ikke ligge før udlevering.');
  this.busy=true;
  try{await mutate('history.grid.add',{card_id:form.dataset.hgCard,publisher_id:data.publisher_id,assigned,returned,completed:form.querySelector('[name=completed]').checked,revision:state.revision},{message:'Udlevering registreret'});}
  finally{this.busy=false;}
 }
};
document.addEventListener('input',event=>{
 if(event.target.id==='hg-search'){HistoryGrid.query=event.target.value;HistoryGrid.limit=100;HistoryGrid.draw();}
});
document.addEventListener('change',event=>{
 const target=event.target;
 if(target.id==='hg-filter'){HistoryGrid.filter=target.value;HistoryGrid.limit=100;HistoryGrid.draw();return;}
 if(target.matches('[data-hg-date]'))HistoryGrid.saveDate(target);
});
document.addEventListener('keydown',event=>{
 const target=event.target;
 if(target.matches('[data-hg-date="text"]')&&event.key==='Enter'){event.preventDefault();target.blur();}
 if(target.matches('[data-hg-date="text"]')&&event.key==='Escape'){const loan=state.loans.find(l=>l.id===target.dataset.hgId);target.value=HistoryGrid.dateText(loan?.[target.dataset.hgField]);target.blur();}
});
document.addEventListener('click',event=>{
 const reset=event.target.closest('#hg-reset');
 if(reset){event.preventDefault();HistoryGrid.query='';HistoryGrid.filter='all';HistoryGrid.limit=100;const search=document.getElementById('hg-search'),filter=document.getElementById('hg-filter');if(search)search.value='';if(filter)filter.value='all';HistoryGrid.draw();search?.focus();return;}
 const add=event.target.closest('[data-hg-add]'),more=event.target.closest('[data-hg-more]');
 if(add){event.preventDefault();try{HistoryGrid.openAdd(add.dataset.hgAdd);}catch(e){toast(e);}}
 if(more){event.preventDefault();HistoryGrid.limit+=100;HistoryGrid.draw();}
});
document.addEventListener('submit',async event=>{
 const form=event.target.closest('[data-hg-form]');if(!form)return;
 event.preventDefault();event.stopImmediatePropagation();
 const button=form.querySelector('[type=submit]');if(button)button.disabled=true;
 try{await HistoryGrid.submit(form);}catch(e){const err=document.getElementById('formError');if(err)err.textContent=e.message;else toast(e);}
 finally{if(button?.isConnected)button.disabled=false;}
});
