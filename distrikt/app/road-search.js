'use strict';
// Only the public road-name fields opt in. Never attach to IB or person inputs.
const RoadSearch={
  online:true,widgets:new WeakMap(),
  normalize(s){return String(s).toLocaleLowerCase('da').replace(/\bgammel\b/g,'gl').replace(/[.,]/g,'').replace(/\s+/g,' ').trim();},
  field(id,value=''){return `<div class="roadSearch"><input id="${id}" name="road" data-road-search autocomplete="off" maxlength="40" value="${esc(value)}" placeholder="Vejnavn" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="${id}List" required><div id="${id}List" class="roadSuggestions" role="listbox" hidden></div><small class="hint roadSearchHint" aria-live="polite">Vælg et forslag for korrekt navn og postnummer.</small></div>`;},
  local(q,post){
    const result=new Map(),add=(road,postcode,city='')=>{const key=road+'|'+postcode;if((!post||postcode===post)&&this.normalize(road).includes(this.normalize(q)))result.set(key,{road,postcode,city,local:true,label:road+' · '+postcode+(city?' '+city:'')});};
    for(const a of GeoUI.data.addresses||[])if(!a.retired)add(a.road,a.postcode);
    for(const p of GeoUI.data.info?.postcodes||[])for(const r of p.roads)add(r.road,p.postcode,p.name);
    return [...result.values()].sort((a,b)=>Number(!this.normalize(a.road).startsWith(this.normalize(q)))-Number(!this.normalize(b.road).startsWith(this.normalize(q)))||cmp(a.label,b.label)).slice(0,12);
  },
  state(input){if(!this.widgets.has(input))this.widgets.set(input,{sequence:0,items:[],index:-1,timer:null});return this.widgets.get(input);},
  draw(input,items,message){
    const widget=this.state(input);widget.items=items;widget.index=-1;
    const parent=input.closest('.roadSearch'),list=parent.querySelector('[role=listbox]');
    list.innerHTML=items.map((s,i)=>`<button type="button" role="option" id="${input.id}Option${i}" aria-selected="false" data-road-option="${i}">${esc(s.label)}<small>${s.local?'Lokale data':'Officielt vejnavn fra DAR'}</small></button>`).join('');
    list.hidden=!items.length;input.setAttribute('aria-expanded',String(!!items.length));input.removeAttribute('aria-activedescendant');parent.querySelector('.roadSearchHint').textContent=message;
  },
  search(input){
    const widget=this.state(input);clearTimeout(widget.timer);const sequence=++widget.sequence;
    const q=input.value.trim(),post=input.form.elements.postcode.value.trim();
    if(q.length<2){this.draw(input,[],'Skriv mindst to tegn for vejforslag.');return;}
    const local=this.local(q,post);this.draw(input,local,this.online?'Søger officielle vejnavne…':'Forslag fra dine lokale kortdata.');
    if(!this.online)return;
    if(post&&!/^\d{4}$/.test(post)){this.draw(input,local,'Udfyld fire cifre i postnummeret, eller lad feltet være tomt.');return;}
    widget.timer=setTimeout(async()=>{
      try{
        const data=await(await api('/api/geo/suggest?road='+encodeURIComponent(q)+'&postcode='+encodeURIComponent(post))).json();
        if(sequence!==widget.sequence||!input.isConnected)return;
        const result=new Map();for(const s of local)result.set(s.road+'|'+s.postcode,s);for(const s of data.suggestions)result.set(s.road+'|'+s.postcode,s);
        const items=[...result.values()].slice(0,16);this.draw(input,items,items.length?'Vælg vejnavnet fra listen.':'Ingen forslag. Prøv et kortere vejnavn eller et andet postnummer.');
      }catch(e){if(sequence===widget.sequence&&input.isConnected)this.draw(input,local,local.length?'Online søgning er utilgængelig. Lokale forslag kan stadig bruges.':e.message);}
    },350);
  },
  pick(input,index){
    const widget=this.state(input),item=widget.items[index];if(!item)return;
    ++widget.sequence;clearTimeout(widget.timer);input.value=item.road;input.form.elements.postcode.value=item.postcode;
    GeoUI.rangeRoad=item.road;GeoUI.rangePost=item.postcode;this.draw(input,[],item.label+' · valgt');input.focus();
  },
  hide(input){const w=this.state(input);++w.sequence;clearTimeout(w.timer);this.draw(input,[],'Vælg et forslag for korrekt navn og postnummer.');},
  key(input,e){
    const w=this.state(input);if(e.key==='Escape'){this.hide(input);return;}
    if(!w.items.length)return;
    if(e.key==='Enter'&&w.index>=0){e.preventDefault();this.pick(input,w.index);return;}
    if(!['ArrowDown','ArrowUp'].includes(e.key))return;e.preventDefault();
    w.index=(w.index+(e.key==='ArrowDown'?1:-1)+w.items.length)%w.items.length;
    const options=input.closest('.roadSearch').querySelectorAll('[role=option]');options.forEach((b,i)=>b.setAttribute('aria-selected',String(i===w.index)));input.setAttribute('aria-activedescendant',options[w.index].id);options[w.index].scrollIntoView({block:'nearest'});
  }
};
document.addEventListener('input',e=>{if(e.target.matches('[data-road-search]'))RoadSearch.search(e.target);else if(e.target.name==='postcode'&&e.target.form?.querySelector('[data-road-search]'))RoadSearch.search(e.target.form.querySelector('[data-road-search]'));});
document.addEventListener('keydown',e=>{if(e.target.matches('[data-road-search]'))RoadSearch.key(e.target,e);});
document.addEventListener('click',e=>{const option=e.target.closest('[data-road-option]');if(option){e.preventDefault();RoadSearch.pick(option.closest('.roadSearch').querySelector('input'),Number(option.dataset.roadOption));}else if(!e.target.closest('.roadSearch'))document.querySelectorAll('[data-road-search]').forEach(input=>RoadSearch.hide(input));});
document.addEventListener('change',e=>{if(e.target.matches('[data-online-search]')){RoadSearch.online=e.target.checked;document.querySelectorAll('[data-road-search]').forEach(input=>RoadSearch.search(input));}});
