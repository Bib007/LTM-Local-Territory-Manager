'use strict';
// Overdue loans stay on the local device. Generating a reminder never changes a loan.
const OverdueLoans={
 tab:'all',
 sort:'publisher',
 defaultTemplate(){
  return I18n.language()==='en'
   ?'Hi {fornavn}\n\nI hope you are well. I am writing about these territory cards that you have had for a while:\n{kort}\n\nCould you please return them when you have an opportunity? If you have completed them and would like to keep them for another round, please let me know so we can record the completion and the new assignment.\n\nThank you very much for your help!\n\nKind regards, {initialer}'
   :'Hej {fornavn}\n\nJeg håber, du har det godt. Jeg skriver lige om de distriktskort, du har haft udleveret i noget tid:\n{kort}\n\nVil du være sød at aflevere dem, når du har mulighed for det? Hvis de er gennemgået, og du gerne vil beholde dem til en ny omgang, må du også meget gerne sige til, så vi kan registrere gennemgangen og den nye udlevering.\n\nPå forhånd mange tak for hjælpen!\n\nKh {initialer}';
 },
 allowed(){return !!state&&(!state.profile||typeof ProfilesUI==='undefined'||ProfilesUI.has('publishers.view','loans.view'));},
 items(){
  if(!this.allowed())return [];
  const cards=new Map((state.cards||[]).map(c=>[c.id,c]));
  return (state.loans||[]).filter(l=>!l.returned&&l.cycle_start&&cards.has(l.card_id)&&fourMonths(l.cycle_start)<state.today)
   .map(loan=>({loan,card:cards.get(loan.card_id),name:publisherName(loan.publisher_id)}));
 },
 count(){return this.items().length;},
 badge(){const n=this.count();return n?'<span class="navFollowupCount navOverdueCount" '+I18n.attribute('aria','{count} distrikter udleveret for længe',{count:n})+'>'+n+'</span>':'';},
 groups(rows){
  const groups=new Map();
  for(const row of rows){const id=row.loan.publisher_id;if(!groups.has(id))groups.set(id,{id,name:row.name,rows:[]});groups.get(id).rows.push(row);}
  return [...groups.values()].sort((a,b)=>cmp(a.name,b.name)||cmp(a.id,b.id));
 },
 loanAge(loan){return elapsedLabel(loan.assigned||loan.cycle_start);},
 row(row,showPublisher=false){
  const {loan,card:c}=row;
  return '<tr>'+(showPublisher?'<td>'+esc(row.name)+'</td>':'')+'<td><button class="link" data-action="detail" data-id="'+esc(c.id)+'">'+ui('Kort')+' '+esc(c.number)+'</button></td><td>'+fmt(loan.assigned)+'</td><td>'+this.loanAge(loan)+'</td>'+(showPublisher?'<td><button data-overdue="message" data-id="'+esc(loan.publisher_id)+'">'+ui('Generer besked')+'</button></td>':'')+'</tr>';
 },
 render(){
  if(!this.allowed())return '<section class="panel"><p class="hint">'+ui('Du har ikke adgang til udleveringsoplysninger.')+'</p></section>';
  const rows=this.items().filter(r=>[r.name,r.card.number,r.card.name,r.card.internal_number].join(' ').toLocaleLowerCase('da-DK').includes(query.toLocaleLowerCase('da-DK').trim()));
  const table=(items,withPublisher)=>{
   const headings=(withPublisher?'<thead><tr><th>'+ui('Forkynder')+'</th>':'<thead><tr>')+'<th>'+ui('Kort')+'</th><th>'+ui('Udleveret')+'</th><th>'+ui('Hvor længe')+'</th>';
   return '<div class="tablewrap"><table>'+headings+(withPublisher?'<th>'+ui('Handling')+'</th>':'')+'</tr></thead><tbody>'+items.map(r=>this.row(r,withPublisher)).join('')+'</tbody></table></div>';
  };
  const ordered=rows.slice().sort((a,b)=>cmp(a.loan.assigned||a.loan.cycle_start,b.loan.assigned||b.loan.cycle_start)||cmp(a.card.number,b.card.number));
  const groups=this.groups(rows),sorted=this.sort==='oldest';
  return '<section class="panel overdueLoans"><div class="between"><div><h2>'+ui('Distrikter udleveret for længe')+'</h2><p class="hint">'+ui('Opfølgning efter fire kalendermåneder uden registreret gennemgang. Ingen ændringer sker automatisk.')+'</p></div><strong class="publisherGroupCount">'+ui('{count} distrikter udleveret for længe',{count:rows.length})+'</strong></div>'
   +'<div class="toolbar"><label for="search">'+ui('Søg forkynder eller kortnummer')+'</label><input id="search" aria-label="'+esc(I18n.text('Søg forkynder eller kortnummer'))+'" '+I18n.attribute('placeholder','Søg forkynder eller kortnummer')+' value="'+esc(query)+'">'
   +'<label for="overdueSort">'+ui('Vis efter')+'</label><select id="overdueSort" data-overdue="sort"><option value="publisher" '+(sorted?'':'selected')+'>'+ui('Forkynder')+'</option><option value="oldest" '+(sorted?'selected':'')+'>'+ui('Ældste udlevering først')+'</option></select></div>'
   +(sorted?(ordered.length?table(ordered,true):'<p class="hint">'+ui('Ingen distrikter udleveret for længe.')+'</p>')
    :(groups.length?'<div class="publisherGroups">'+groups.map(g=>'<section class="publisherGroup"><div class="publisherGroupHeading"><h3>'+esc(g.name)+'</h3><span>'+ui('{count} kort',{count:g.rows.length})+'</span><button data-overdue="message" data-id="'+esc(g.id)+'">'+ui('Generer besked')+'</button></div>'+table(g.rows.slice().sort((a,b)=>cmp(a.loan.assigned,b.loan.assigned)),false)+'</section>').join('')+'</div>':'<p class="hint">'+ui('Ingen distrikter udleveret for længe.')+'</p>'))
   +'<p class="hint">'+ui('Beskeden oprettes lokalt og sendes ikke automatisk. Kontrollér oplysningerne, før du sender en SMS.')+'</p></section>';
 },
 message(id){
  const person=state.publishers.find(p=>p.id===id),rows=this.items().filter(r=>r.loan.publisher_id===id).sort((a,b)=>cmp(a.loan.assigned,b.loan.assigned));
  if(!person||!rows.length)return null;
  const first=person.name.trim().split(/\s+/)[0]||person.name;
  const list=rows.map(r=>'• '+I18n.text('Kort')+' '+r.card.number+' – '+this.loanAge(r.loan)+' ('+I18n.text('udleveret')+' '+fmt(r.loan.assigned)+')').join('\n');
  const template=state.settings?.overdue_message_template||this.defaultTemplate();
  return template.replace(/\{(fornavn|navn|kort|initialer)\}/g,(_,key)=>({fornavn:first,navn:person.name,kort:list,initialer:''})[key]);
 },
 showMessage(id){
  if(!this.allowed())return;
  const message=this.message(id);if(message===null)return;
  const p=state.publishers.find(person=>person.id===id);
  openDialog('<h2>'+ui('Besked til')+' '+esc(p.name)+'</h2><p class="hint">'+ui('Du kan rette beskeden her, skrive dine initialer efter Kh og kopiere den til en SMS.')+'</p><label for="overdueMessage">'+ui('SMS-besked')+'</label><textarea id="overdueMessage" rows="13" spellcheck="true">'+esc(message)+'</textarea><div class="actions"><button class="primary" data-overdue="copy">'+ui('Kopiér besked')+'</button><button data-action="close">'+ui('Luk')+'</button></div>',I18n.language());
 },
 async copy(){
  const field=el('overdueMessage');if(!field)return;
  const value=field.value;
  try{
   if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(value);}
   else{field.focus();field.select();if(!document.execCommand('copy'))throw Error('Clipboard unavailable');}
   toast(I18n.text('Beskeden er kopieret'));
  }catch(_){field.focus();field.select();toast(I18n.text('Markér og kopiér teksten manuelt.'));}
 }
};
document.addEventListener('click',e=>{
 const target=e.target.closest('[data-overdue]');if(!target||target.dataset.overdue==='sort')return;
 e.preventDefault();
 switch(target.dataset.overdue){
  case 'tab':OverdueLoans.tab=target.dataset.tab;query='';render();break;
  case 'message':OverdueLoans.showMessage(target.dataset.id);break;
  case 'copy':OverdueLoans.copy();break;
 }
});
document.addEventListener('change',e=>{if(e.target.dataset?.overdue==='sort'){OverdueLoans.sort=e.target.value==='oldest'?'oldest':'publisher';render();}});
