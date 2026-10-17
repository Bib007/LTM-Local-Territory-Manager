'use strict';
// Opt-in, local-only assignment field. No requests, persistence or record creation.
const PublisherSearch={
 widgets:new WeakMap(),limit:8,
 normalize(value){return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('da').replace(/æ/g,'ae').replace(/ø/g,'o').replace(/\s+/g,' ').trim();},
 matches(records,query){
  const q=this.normalize(query),tokens=q.split(' ').filter(Boolean);
  const rank=name=>name===q?0:name.startsWith(q)?1:tokens.every(t=>name.split(/[\s-]+/).some(w=>w.startsWith(t)))?2:3;
  return records.filter(p=>tokens.every(t=>this.normalize(p.name).includes(t))).sort((a,b)=>rank(this.normalize(a.name))-rank(this.normalize(b.name))||a.name.localeCompare(b.name,'da',{numeric:true}));
 },
 field(){return `<label for="issuePublisherName">${I18n.label('Forkynder')}</label><div class="publisherSearch"><input id="issuePublisherName" name="publisher_name" data-publisher-search role="combobox" aria-autocomplete="list" aria-haspopup="listbox" aria-expanded="false" aria-controls="issuePublisherNames" aria-describedby="issuePublisherHint" ${I18n.attribute('placeholder','Find en forkynder eller skriv et nyt navn')} maxlength="100" required autocomplete="off"><div id="issuePublisherNames" class="publisherSuggestions" role="listbox" ${I18n.attribute('aria','Forkyndere')} hidden></div><p id="issuePublisherHint" class="hint publisherSearchHint" role="status" aria-live="polite">${I18n.label('Søgningen sker kun i din lokale forkynderliste.')}</p><p class="hint">${I18n.label('Et nyt navn oprettes automatisk i din lokale forkynderliste.')}</p></div>`;},
 attach(input,records){if(!input?.closest)return;this.widgets.set(input,{records:records.map(p=>({name:p.name})),items:[],index:-1});},
 parts(input){const parent=input.closest('.publisherSearch');return {list:parent.querySelector('[role="listbox"]'),hint:parent.querySelector('.publisherSearchHint')};},
 close(input){if(!this.widgets.has(input))return;const w=this.widgets.get(input),{list}=this.parts(input);w.index=-1;list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');},
 draw(input){
  const w=this.widgets.get(input);if(!w)return;
  const matches=this.matches(w.records,input.value),{list,hint}=this.parts(input);
  w.items=matches.slice(0,this.limit);w.index=-1;
  list.innerHTML=w.items.map((p,i)=>`<button type="button" role="option" tabindex="-1" id="${input.id}Option${i}" aria-selected="false" data-publisher-option="${i}">${esc(p.name)}</button>`).join('');
  list.hidden=!w.items.length;input.setAttribute('aria-expanded',String(!!w.items.length));input.removeAttribute('aria-activedescendant');
  this.message(input,matches.length>this.limit?'Viser {count} af {total} forslag. Skriv mere for at begrænse listen.':matches.length?'{count} forslag. Brug piletasterne og Enter til at vælge.':'Ingen forslag. Et nyt navn oprettes først, når du registrerer udleveringen.',{count:w.items.length,total:matches.length});
 },
 move(input,step){const w=this.widgets.get(input),{list}=this.parts(input);if(list.hidden)this.draw(input);if(!w.items.length)return;w.index=w.index<0?(step>0?0:w.items.length-1):(w.index+step+w.items.length)%w.items.length;
  const options=list.querySelectorAll('[role="option"]');options.forEach((node,i)=>node.setAttribute('aria-selected',String(i===w.index)));const selected=options[w.index];input.setAttribute('aria-activedescendant',selected.id);selected.scrollIntoView({block:'nearest'});
 },
 choose(input,index){const w=this.widgets.get(input),item=w?.items[index];if(!item)return;input.value=item.name;input.focus();this.close(input);this.message(input,'Navnet er valgt. Registrer udleveringen for at gemme.');},
 message(input,key,params={}){const w=this.widgets.get(input);w.message={key,params};this.parts(input).hint.textContent=I18n.format(key,params);},
 localize(){document.querySelectorAll?.('[data-publisher-search]').forEach(input=>{const w=this.widgets.get(input);if(!w)return;if(input.getAttribute('aria-expanded')==='true')this.draw(input);else if(w.message)this.message(input,w.message.key,w.message.params);});}
};
document.addEventListener('focusin',event=>{if(event.target.matches?.('[data-publisher-search]'))PublisherSearch.draw(event.target);});
document.addEventListener('input',event=>{if(event.target.matches?.('[data-publisher-search]')&&!event.isComposing)PublisherSearch.draw(event.target);});
document.addEventListener('compositionend',event=>{if(event.target.matches?.('[data-publisher-search]'))PublisherSearch.draw(event.target);});
document.addEventListener('keydown',event=>{
 const input=event.target;if(!input.matches?.('[data-publisher-search]')||event.isComposing||event.keyCode===229||!PublisherSearch.widgets.has(input))return;
 const w=PublisherSearch.widgets.get(input),expanded=input.getAttribute('aria-expanded')==='true';
 if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();PublisherSearch.move(input,event.key==='ArrowDown'?1:-1);}
 else if(event.key==='Enter'&&expanded){event.preventDefault();if(w.index>=0)PublisherSearch.choose(input,w.index);else PublisherSearch.close(input);}
 else if(event.key==='Escape'&&expanded){event.preventDefault();event.stopPropagation();PublisherSearch.close(input);}
 else if(event.key==='Tab')PublisherSearch.close(input);
});
document.addEventListener('pointerdown',event=>{if(event.pointerType==='mouse'&&event.target.closest?.('[data-publisher-option]'))event.preventDefault();});
document.addEventListener('click',event=>{
 if(event.target.matches?.('[data-publisher-search]')){if(event.target.getAttribute('aria-expanded')!=='true')PublisherSearch.draw(event.target);return;}
 const option=event.target.closest?.('[data-publisher-option]');if(!option){document.querySelectorAll?.('[data-publisher-search]').forEach(input=>{if(!input.closest('.publisherSearch').contains(event.target))PublisherSearch.close(input);});return;}
 const input=option.closest('.publisherSearch')?.querySelector('[data-publisher-search]');if(input&&PublisherSearch.widgets.has(input))PublisherSearch.choose(input,Number(option.dataset.publisherOption));
});
document.addEventListener('focusout',event=>{
 const parent=event.target.closest?.('.publisherSearch');if(!parent||parent.contains(event.relatedTarget))return;
 const input=parent.querySelector('[data-publisher-search]');if(input)PublisherSearch.close(input);
});
