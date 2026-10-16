'use strict';
const Navigation={
 groups:[
  ['',[['Forside','Forside'],['Daglig brug','Udlevering']]],
  ['Overblik',[['Distriktskort','Distrikter','Alle'],['Kortoversigt','Kortoversigt'],['Forkyndere','Forkyndere'],['Opgaver og noter','Opgaver']]],
  ['Administration',[['Rapporter og historik','Rapporter','Rapport'],['Kort og adresser','Adresser','Mangler på kort'],['Indstillinger','Indstillinger','general']]]
 ],opened:{},settingsSection:'general',
 active(item){return page==='Opstart'&&item[1]==='Indstillinger'||page===item[1]||page==='Kortopsætning'&&item[1]==='Adresser';},
 html(){const icons={Forside:'⌂',Udlevering:'⇄',Distrikter:'▤',Kortoversigt:'◇',Forkyndere:'♙',Opgaver:'☑',Rapporter:'▥',Adresser:'⌖',Indstillinger:'⚙'};return this.groups.map(([name,items],i)=>`${name?`<div class="navcaption">${esc(name.toUpperCase())}</div>`:''}${items.map((item,j)=>`<button data-navigation="${i}:${j}" class="${this.active(item)?'active':''}" ${this.active(item)?'aria-current="page"':''}><span aria-hidden="true" class="navIcon">${icons[item[1]]}</span>${esc(item[0])}</button>`).join('')}`).join('');},
 title(){return Workspace.title(page);},
 async go(index){const [i,j]=index.split(':').map(Number),item=this.groups[i]?.[1][j];if(!item)return;
  await closeRequested();if(el('dialog').open)return;
  if(page==='Kortopsætning'&&!GeoUI.canLeave())return;
  Workspace.remember();document.body?.classList.remove('menuOpen');
  if(item[1]==='Kortoversigt'){if(!GeoUI.loaded)await GeoUI.load();MapBackground.mode='road';page='Kortoversigt';render();return;}
  if(['Adresser','Rapporter'].includes(item[1])&&!GeoUI.loaded)await GeoUI.load();
  GeoUI.dirty=false;page=item[1];Workspace.restore(page);render();
 },
 selectRow(target,event){if(target.closest('button,input,select,textarea,a,label,[data-action]'))return false;const row=target.closest('[data-card-row]');if(!row)return false;if(event.type==='keydown'&&!['Enter',' '].includes(event.key))return false;if(event.type==='click'&&window.getSelection?.().toString())return false;event.preventDefault();selected=row.dataset.cardRow;render();if(event.type==='keydown')document.querySelector(`[data-card-row="${CSS.escape(selected)}"]`)?.focus();return true;}
};
document.addEventListener('toggle',e=>{if(e.target.dataset?.navGroup!==undefined)Navigation.opened[e.target.dataset.navGroup]=e.target.open;},true);
document.addEventListener('click',async e=>{const b=e.target.closest('[data-navigation]');if(b){e.preventDefault();try{await Navigation.go(b.dataset.navigation);}catch(err){toast(err.message);}return;}Navigation.selectRow(e.target,e);});
document.addEventListener('keydown',e=>Navigation.selectRow(e.target,e));
