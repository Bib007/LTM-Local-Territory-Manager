'use strict';
// Road mode uses public OSM tiles; local mode uses downloaded map data.
const MapBackground={
 mode:'road',instances:new Map(),
 toolbar(id){return `<div class="toolbar mapBackground"><label>${ui('Kortbaggrund')} <select data-basemap="${id}"><option value="road" ${this.mode==='road'?'selected':''} data-ui="Vejkort · OpenStreetMap">Vejkort · OpenStreetMap</option><option value="local" ${this.mode==='local'?'selected':''} data-ui="Lokale kortdata">Lokale kortdata</option></select></label><button data-map-fit="${id}">${ui('Vis hele området')}</button><button data-map-expand="${id}" aria-pressed="false" data-ui="Større kort">${esc(I18n.text('Større kort'))}</button></div><p class="hint" id="${id}BackgroundStatus" role="status" data-ui="${this.descriptionKey()}">${esc(this.description())}</p>`;},
 descriptionKey(){return this.mode==='road'?'Online vejkort · kortudsnittet hentes hos OpenStreetMap.':'Lokale kortdata. Zoom med + / − eller rul med musen.';},
 description(){return I18n.text(this.descriptionKey());},
 roads(){return this.mode==='local';},buildings(){return this.mode==='local';},
 attach(id,map,redraw,fit){this.detach(id);const entry={map,redraw,fit,layer:null};this.instances.set(id,entry);if(typeof L.tileLayer==='function'){L.control?.scale?.({imperial:false}).addTo(map);this.apply(id);}},
 detach(id){const entry=this.instances.get(id);if(entry?.layer)entry.map.removeLayer?.(entry.layer);this.instances.delete(id);},
 apply(id){if(!['local','road'].includes(this.mode))this.mode='road';for(const button of document.querySelectorAll?.('[data-osm-export]')||[])button.disabled=this.mode!=='road';const selector=document.querySelector(`[data-basemap="${id}"]`);if(selector)selector.value=this.mode;const entry=this.instances.get(id);if(!entry)return;if(entry.layer){entry.map.removeLayer(entry.layer);entry.layer=null;}const note=el(id+'BackgroundStatus');if(note){note.dataset.ui=this.descriptionKey();note.lang=I18n.language();note.textContent=this.description();}if(this.mode==='local')return;
  entry.layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxNativeZoom:19,maxZoom:21,minZoom:8,crossOrigin:'anonymous',referrerPolicy:'strict-origin-when-cross-origin',attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap-bidragsydere</a>'});
  entry.layer.on('tileerror',()=>{if(note){const key='Vejkortet kunne ikke hentes. Kontrollér internet, eller vælg Lokale kortdata.';note.dataset.ui=key;note.lang=I18n.language();note.textContent=I18n.text(key);}});entry.layer.addTo(entry.map);
 },
 async change(id,mode){if(!['local','road'].includes(mode))return;this.mode=mode;for(const [key,entry] of this.instances){this.apply(key);entry.redraw();}}
};
document.addEventListener('change',async e=>{if(!e.target.dataset.basemap)return;try{await MapBackground.change(e.target.dataset.basemap,e.target.value);}catch(err){e.target.value=MapBackground.mode;toast(err);}});
document.addEventListener('click',e=>{const fit=e.target.closest('[data-map-fit]'),expand=e.target.closest('[data-map-expand]');if(fit){MapBackground.instances.get(fit.dataset.mapFit)?.fit();return;}if(expand){const entry=MapBackground.instances.get(expand.dataset.mapExpand),node=el(expand.dataset.mapExpand);const enlarged=node.classList.toggle('mapExpanded');const key=enlarged?'Normal størrelse':'Større kort';expand.dataset.ui=key;expand.lang=I18n.language();expand.textContent=I18n.text(key);expand.setAttribute('aria-pressed',String(enlarged));entry?.map.invalidateSize();}});
