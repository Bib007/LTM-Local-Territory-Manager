'use strict';
const Navigation={
 groups:[
  ['',[['Forside','Forside'],['Daglig brug','Udlevering']]],
  ['Overblik',[['Distriktskort','Distrikter','Alle'],['Kortoversigt','Kortoversigt'],['Forkyndere','Forkyndere'],['Opgaver','Opgaver'],['Opfølgninger','Opfølgninger']]],
  ['Administration',[['Rapporter og historik','Rapporter','Rapport'],['Kort og adresser','Adresser','Mangler på kort'],['Indstillinger','Indstillinger','general']]],
  ['Hjælp',[]]
 ],opened:{},settingsSection:'general',
 sidebarKey:'ltm-sidebar-collapsed',sidebarCollapsed:false,sidebarMedia:null,
 compact(){return this.sidebarCollapsed&&!!this.sidebarMedia?.matches;},
 initSidebar(){
  if(typeof window==='undefined'||typeof window.matchMedia!=='function')return;
  this.sidebarMedia=window.matchMedia('(min-width:751px)');
  try{this.sidebarCollapsed=localStorage.getItem(this.sidebarKey)==='1';}catch{}
  document.body?.classList.toggle('sidebarCompact',this.compact());
  const change=()=>{if(this.sidebarCollapsed)this.repaintSidebar();};
  if(this.sidebarMedia.addEventListener)this.sidebarMedia.addEventListener('change',change);
  else this.sidebarMedia.addListener?.(change);
 },
 toggleSidebar(){
  if(!this.sidebarMedia?.matches)return;
  this.sidebarCollapsed=!this.sidebarCollapsed;
  try{localStorage.setItem(this.sidebarKey,this.sidebarCollapsed?'1':'0');}catch{}
  this.repaintSidebar(true);
  // Leaflet listens for viewport changes, but the main column also changes
  // width when the sidebar changes without a browser resize.
  window.dispatchEvent(new Event('resize'));
 },
 repaintSidebar(focusToggle=false){
  document.body?.classList.toggle('sidebarCompact',this.compact());
  const nav=document.getElementById('nav');if(!nav||!nav.childElementCount)return;
  const focused=document.activeElement,inside=nav.contains(focused),index=focused?.dataset?.navigation;
  nav.innerHTML=this.html();nav.lang=I18n.language();
  if(focusToggle)nav.querySelector('[data-sidebar-toggle]')?.focus({preventScroll:true});
  else if(inside){
   if(!this.sidebarMedia.matches&&!document.body.classList.contains('menuOpen'))document.querySelector('.mobileMenu')?.focus({preventScroll:true});
   else if(index)nav.querySelector('[data-navigation="'+index+'"]')?.focus({preventScroll:true});
   else if(this.sidebarMedia.matches)nav.querySelector('[data-sidebar-toggle]')?.focus({preventScroll:true});
  }
 },
 sidebarToggle(){
  const compact=this.compact(),label=compact?'Fold menu ud':'Fold menu sammen';
  return `<button type="button" class="sidebarToggle" data-sidebar-toggle aria-controls="sidebar" aria-expanded="${!compact}" title="${I18n.escape(I18n.text(label))}"><span class="navIcon" aria-hidden="true">${compact?'›':'‹'}</span><span class="sidebarToggleLabel">${esc(I18n.text(label))}</span></button>`;
 },
 guideLink(){
  const lang=I18n.language();
  return `<a class="navExternal" data-help-guide ${I18n.attribute('title','Trinvis LTM-guide')} href="https://localterritorymanager.netlify.app/${lang}/guide/" target="_blank" rel="noopener noreferrer"><span aria-hidden="true" class="navIcon">?</span><span class="navExternalLabel">${esc(I18n.text('Trinvis LTM-guide'))}</span><span class="navExternalMark" aria-hidden="true">↗</span></a>`;
 },
 active(item){return page==='Opstart'&&item[1]==='Indstillinger'||page===item[1]||page==='Kortopsætning'&&item[1]==='Adresser';},
 html(){
  const desk=typeof state!=='undefined'&&state?.profile?.desk_only,compact=this.compact();
  const icons={
   Forside:'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
   Udlevering:'<path d="M3 7h17m-4-4 4 4-4 4M21 17H4m4-4-4 4 4 4"/>',
   Distrikter:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/>',
   Kortoversigt:'<path d="m3 5 6-2 6 3 6-2v15l-6 2-6-3-6 2zM9 3v15M15 6v15"/>',
   Forkyndere:'<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
   Opgaver:'<rect x="4" y="4" width="16" height="16" rx="2"/><path d="m8 12 3 3 5-6"/>',
   Opfølgninger:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5m0 4h.01"/>',
   Rapporter:'<path d="M4 20h16M6 16v-6m6 6V4m6 12V8"/>',
   Adresser:'<path d="M20 10c0 6-8 11-8 11S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
   Indstillinger:'<circle cx="12" cy="12" r="3"/><path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2 2m8.8 8.8 2 2m0-12.8-2 2M7.6 16.4l-2 2"/>'
  };
  const icon=key=>'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'+icons[key]+'</svg>';
  const allowed=name=>typeof ProfilesUI==='undefined'||ProfilesUI.pageAllowed(name);
  const groups=this.groups.map(([name,items],i)=>{
   if(name==='Hjælp')return `<div class="navcaption">${esc(I18n.text(name).toUpperCase())}</div>${this.guideLink()}`;
   const buttons=items.map((item,j)=>{
    if(!allowed(item[1]))return '';
    const count=item[1]==='Opfølgninger'&&typeof GeoUI!=='undefined'&&GeoUI.loaded?Workspace.followupItems().length:null;
    const followups=!count?'':`<span class="navFollowupCount" ${I18n.attribute('aria','Til opfølgning: {count}',{count})}>${count}</span>`;
    const taskCount=item[1]==='Opgaver'?Workspace.actionableTasks().length:0;
    const tasks=taskCount?`<span class="navTaskCount" ${I18n.attribute('aria','{count} åbne opgaver',{count:taskCount})}>${taskCount}</span>`:'';
    const label=desk&&item[1]==='Udlevering'?'Ind/udlevering':item[0];
    return `<button data-navigation="${i}:${j}" class="${this.active(item)?'active':''}" ${this.active(item)?'aria-current="page"':''} ${I18n.attribute('title',label)}><span aria-hidden="true" class="navIcon">${icon(item[1])}</span><span class="sidebarNavLabel">${esc(I18n.text(label))}</span>${followups}${tasks}${item[1]==='Forkyndere'&&typeof OverdueLoans!=='undefined'?OverdueLoans.badge():''}</button>`;
   }).join('');
   if(compact&&name&&buttons)return `<div class="navGroup" role="group" aria-label="${I18n.escape(I18n.text(name))}">${buttons}</div>`;
   return buttons?(name?`<details class="navGroup" data-nav-group="${i}" ${this.opened[i]!==false||items.some(item=>this.active(item))?'open':''}><summary>${esc(I18n.text(name))}</summary><div>${buttons}</div></details>`:buttons):'';
  }).join('');
  const language=I18n.language();
  const choice=I18n.fixedLanguage()?'':`<label class="languageChoice" lang="${language}">${esc(I18n.text('Appens og guidens sprog'))}<select id="navigationLanguage"><option value="da" ${language==='da'?'selected':''}>Dansk</option><option value="en" ${language==='en'?'selected':''}>English</option></select><small>${esc(I18n.text('Originale printformularer og gemt brugerindhold bevarer deres sprog.'))}</small></label>`;
  return this.sidebarToggle()+groups+choice+(!desk&&typeof Theme!=='undefined'?Theme.html(language):'');
 },
 paintFollowupCount(){
  const button=document.querySelector('#nav [data-navigation="1:4"]');if(!button||!GeoUI.loaded)return;
  button.querySelector('.navFollowupCount')?.remove();const count=Workspace.followupItems().length;
  if(count)button.insertAdjacentHTML('beforeend',`<span class="navFollowupCount" ${I18n.attribute('aria','Til opfølgning: {count}',{count})}>${count}</span>`);
 },
 localize(){
  const restoreFocus=document.activeElement?.id==='navigationLanguage';
  if(typeof GeoUI!=='undefined'&&typeof GeoUI.localize==='function')GeoUI.localize();
  I18n.applyShell();
  if(typeof ProfilesUI!=='undefined')ProfilesUI.localize();
  
  if(typeof GuidedTour!=='undefined')GuidedTour.localize();
  if(typeof Onboarding!=='undefined')Onboarding.localizePanel();
  if(typeof BoundaryImportUI!=='undefined')BoundaryImportUI.localize();
  if(typeof PublisherSearch!=='undefined')PublisherSearch.localize();
  if(typeof SaveStatus!=='undefined')SaveStatus.paint();
  const nav=el('nav');if(nav){nav.innerHTML=this.html();nav.lang=I18n.language();}
  if(restoreFocus)el('navigationLanguage')?.focus();
  const title=document.querySelector('#app h1[data-ui-title]');if(title){title.textContent=this.title();title.lang=I18n.language();}
  const subtitle=document.querySelector('[data-ui-subtitle]');if(subtitle){subtitle.textContent=Workspace.subtitle(page);subtitle.lang=I18n.language();}
 },
 title(){return Workspace.title(page);},
 async go(index){const [i,j]=index.split(':').map(Number),item=this.groups[i]?.[1][j];if(!item||(typeof ProfilesUI!=='undefined'&&!ProfilesUI.pageAllowed(item[1])))return;
  await closeRequested();if(el('dialog').open)return;
  if(page==='Kortopsætning'&&!GeoUI.canLeave())return;
  Workspace.remember();Workspace.menu(false,document.body?.classList.contains('menuOpen'));
  if(item[1]==='Opfølgninger'){await Workspace.openFollowups();return;}
  if(item[1]==='Kortoversigt'){if(!GeoUI.loaded)await GeoUI.load();MapBackground.mode='road';page='Kortoversigt';render();return;}
  if((item[1]==='Adresser'||item[1]==='Rapporter'&&(typeof ProfilesUI==='undefined'||ProfilesUI.has('cards.view','geo.view')))&&!GeoUI.loaded)await GeoUI.load();
  GeoUI.dirty=false;page=item[1];Workspace.restore(page);render();
 },
 selectRow(target,event){if(target.closest('button,input,select,textarea,a,label,summary,details,[data-action]'))return false;const row=target.closest('[data-card-row]');if(!row)return false;if(event.type==='keydown'&&!['Enter',' '].includes(event.key))return false;if(event.type==='click'&&window.getSelection?.().toString())return false;event.preventDefault();selected=row.dataset.cardRow;render();if(event.type==='keydown')document.querySelector(`[data-card-row="${CSS.escape(selected)}"]`)?.focus();return true;}
};
Navigation.initSidebar();
document.addEventListener('toggle',e=>{if(e.target.isConnected&&e.target.dataset?.navGroup!==undefined)Navigation.opened[e.target.dataset.navGroup]=e.target.open;},true);
document.addEventListener('click',async e=>{if(e.target.closest('[data-sidebar-toggle]')){Navigation.toggleSidebar();return;}const b=e.target.closest('[data-navigation]');if(b){e.preventDefault();try{await Navigation.go(b.dataset.navigation);}catch(err){toast(err);}return;}Navigation.selectRow(e.target,e);});
document.addEventListener('keydown',e=>Navigation.selectRow(e.target,e));
