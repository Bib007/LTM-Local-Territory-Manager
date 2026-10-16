'use strict';
// Public OSM road tiles are displayed only after an explicit online choice.
const MapBackground={
 mode:'road',instances:new Map(),
 toolbar(id){return `<div class="toolbar mapBackground"><label>Kortbaggrund <select data-basemap="${id}"><option value="road" ${this.mode==='road'?'selected':''}>Vejkort · OpenStreetMap</option><option value="local" ${this.mode==='local'?'selected':''}>Lokale kortdata</option></select></label><button data-map-fit="${id}">Vis hele området</button><button data-map-expand="${id}" aria-pressed="false">Større kort</button></div><p class="hint" id="${id}BackgroundStatus" role="status">${this.description()}</p>`;},
 description(){return this.mode==='road'?'Online vejkort · kortudsnittet hentes hos OpenStreetMap.':'Lokale kortdata. Zoom med + / − eller rul med musen.';},
 roads(){return this.mode==='local';},buildings(){return this.mode==='local';},
 attach(id,map,redraw,fit){this.detach(id);const entry={map,redraw,fit,layer:null};this.instances.set(id,entry);if(typeof L.tileLayer==='function'){L.control?.scale?.({imperial:false}).addTo(map);this.apply(id);}},
 detach(id){const entry=this.instances.get(id);if(entry?.layer)entry.map.removeLayer?.(entry.layer);this.instances.delete(id);},
 apply(id){if(!['local','road'].includes(this.mode))this.mode='road';for(const button of document.querySelectorAll?.('[data-osm-export]')||[])button.disabled=this.mode!=='road';const selector=document.querySelector(`[data-basemap="${id}"]`);if(selector)selector.value=this.mode;const entry=this.instances.get(id);if(!entry)return;if(entry.layer){entry.map.removeLayer(entry.layer);entry.layer=null;}const note=el(id+'BackgroundStatus');if(note)note.textContent=this.description();if(this.mode==='local')return;
  entry.layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxNativeZoom:19,maxZoom:21,minZoom:8,crossOrigin:'anonymous',referrerPolicy:'strict-origin-when-cross-origin',attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap-bidragsydere</a>'});
  entry.layer.on('tileerror',()=>{if(note)note.textContent='Vejkortet kunne ikke hentes. Kontrollér internet, eller vælg Lokale kortdata.';});entry.layer.addTo(entry.map);
 },
 async change(id,mode){if(!['local','road'].includes(mode))return;this.mode=mode;for(const [key,entry] of this.instances){this.apply(key);entry.redraw();}}
};
document.addEventListener('change',async e=>{if(!e.target.dataset.basemap)return;try{await MapBackground.change(e.target.dataset.basemap,e.target.value);}catch(err){e.target.value=MapBackground.mode;toast(err.message);}});
document.addEventListener('click',e=>{const fit=e.target.closest('[data-map-fit]'),expand=e.target.closest('[data-map-expand]');if(fit){MapBackground.instances.get(fit.dataset.mapFit)?.fit();return;}if(expand){const entry=MapBackground.instances.get(expand.dataset.mapExpand),node=el(expand.dataset.mapExpand);const enlarged=node.classList.toggle('mapExpanded');expand.textContent=enlarged?'Normal størrelse':'Større kort';expand.setAttribute('aria-pressed',String(enlarged));entry?.map.invalidateSize();}});
