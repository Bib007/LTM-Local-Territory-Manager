'use strict';
const Navigation={
 groups:[
  ['',[['Forside','Forside'],['Daglig brug','Udlevering']]],
  ['Overblik',[['Distriktskort','Distrikter','Alle'],['Kortoversigt','Kortoversigt'],['Forkyndere','Forkyndere'],['Opgaver og noter','Opgaver']]],
  ['Administration',[['Rapporter og historik','Rapporter','Rapport'],['Kort og adresser','Adresser','Mangler på kort'],['Indstillinger','Indstillinger','general']]],
  ['Hjælp',[['Idéer og feedback','Feedback']]]
 ],opened:{},settingsSection:'general',
 active(item){return page==='Opstart'&&item[1]==='Indstillinger'||page===item[1]||page==='Kortopsætning'&&item[1]==='Adresser';},
 html(){const icons={Forside:'⌂',Udlevering:'⇄',Distrikter:'▤',Kortoversigt:'◇',Forkyndere:'♙',Opgaver:'☑',Rapporter:'▥',Adresser:'⌖',Indstillinger:'⚙',Feedback:'✎'};return this.groups.map(([name,items],i)=>`${name?`<div class="navcaption">${esc(I18n.text(name).toUpperCase())}</div>`:''}${items.map((item,j)=>item[1]==='Feedback'?`<a class="navExternal" href="https://github.com/Bib007/LTM-Local-Territory-Manager/issues/new?template=idea.yml" target="_blank" rel="noopener noreferrer"><span aria-hidden="true" class="navIcon">${icons.Feedback}</span>${esc(I18n.text(item[0]))}<span class="navExternalMark" aria-hidden="true">↗</span></a>`:`<button data-navigation="${i}:${j}" class="${this.active(item)?'active':''}" ${this.active(item)?'aria-current="page"':''}><span aria-hidden="true" class="navIcon">${icons[item[1]]}</span>${esc(I18n.text(item[0]))}</button>`).join('')}`).join('')+`<label class="languageChoice" lang="${I18n.language()}">${esc(I18n.text('Appens og guidens sprog'))}<select id="navigationLanguage"><option value="da" ${I18n.language()==='da'?'selected':''}>Dansk</option><option value="en" ${I18n.language()==='en'?'selected':''}>English</option></select><small>${esc(I18n.text('Oversættelsen er delvis · noget indhold er stadig på dansk.'))}</small></label>`;},
 localize(){
  const restoreFocus=document.activeElement?.id==='navigationLanguage';
  if(typeof GeoUI!=='undefined'&&typeof GeoUI.localize==='function')GeoUI.localize();
  I18n.applyShell();
  if(typeof GuidedTour!=='undefined')GuidedTour.localize();
  if(typeof Onboarding!=='undefined')Onboarding.localizePanel();
  if(typeof BoundaryImportUI!=='undefined')BoundaryImportUI.localize();
  if(typeof PublisherSearch!=='undefined')PublisherSearch.localize();
  if(typeof SaveStatus!=='undefined')SaveStatus.paint();
  const nav=el('nav');if(nav){nav.innerHTML=this.html();nav.lang=I18n.language();}
  if(restoreFocus)el('navigationLanguage')?.focus();
  const title=document.querySelector('[data-ui-title]');if(title){title.textContent=this.title();title.lang=I18n.language();}
  const subtitle=document.querySelector('[data-ui-subtitle]');if(subtitle){subtitle.textContent=Workspace.subtitle(page);subtitle.lang=I18n.language();}
 },
 title(){return Workspace.title(page);},
 async go(index){const [i,j]=index.split(':').map(Number),item=this.groups[i]?.[1][j];if(!item)return;
  await closeRequested();if(el('dialog').open)return;
  if(page==='Kortopsætning'&&!GeoUI.canLeave())return;
  Workspace.remember();Workspace.menu(false,document.body?.classList.contains('menuOpen'));
  if(item[1]==='Kortoversigt'){if(!GeoUI.loaded)await GeoUI.load();MapBackground.mode='road';page='Kortoversigt';render();return;}
  if(['Adresser','Rapporter'].includes(item[1])&&!GeoUI.loaded)await GeoUI.load();
  GeoUI.dirty=false;page=item[1];Workspace.restore(page);render();
 },
 selectRow(target,event){if(target.closest('button,input,select,textarea,a,label,[data-action]'))return false;const row=target.closest('[data-card-row]');if(!row)return false;if(event.type==='keydown'&&!['Enter',' '].includes(event.key))return false;if(event.type==='click'&&window.getSelection?.().toString())return false;event.preventDefault();selected=row.dataset.cardRow;render();if(event.type==='keydown')document.querySelector(`[data-card-row="${CSS.escape(selected)}"]`)?.focus();return true;}
};
document.addEventListener('toggle',e=>{if(e.target.dataset?.navGroup!==undefined)Navigation.opened[e.target.dataset.navGroup]=e.target.open;},true);
document.addEventListener('click',async e=>{const b=e.target.closest('[data-navigation]');if(b){e.preventDefault();try{await Navigation.go(b.dataset.navigation);}catch(err){toast(err);}return;}Navigation.selectRow(e.target,e);});
document.addEventListener('keydown',e=>Navigation.selectRow(e.target,e));
