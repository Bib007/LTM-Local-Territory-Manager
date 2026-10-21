'use strict';
// View-only gesture gate. It never changes card membership, extent or approval.
const DistrictMapGesture={
 attach(map,node,button,hint){
  const handlers=['dragging','scrollWheelZoom','doubleClickZoom','touchZoom','boxZoom','keyboard','tapHold'];
  let latched=false,enabled=false,disposed=false,prompt=false;
  const listeners=[],listen=(target,type,fn,options)=>{target.addEventListener(type,fn,options);listeners.push(()=>target.removeEventListener(type,fn,options));};
  const apply=value=>{
   if(disposed)return;enabled=!!value;
   for(const key of handlers)map[key]?.[enabled?'enable':'disable']();
   node.classList.toggle('mapGestureLocked',!enabled);
   button.setAttribute('aria-pressed',String(latched));
   I18n.content(button,latched?'Lås kortet igen':'Aktivér kort · touch og tastatur');
   I18n.content(hint,latched?'Kortet er aktivt. Flyt eller zoom med touch, mus eller piletaster og +/−. Vælg Lås kortet igen for almindelig rulning.':prompt?'Kortet er låst. Hold Ctrl/Command nede for at flytte eller zoome, eller vælg Aktivér kort.':'Hold Ctrl/Command nede for at flytte eller zoome. På touch eller med tastatur: vælg Aktivér kort. Uden aktivering ruller dialogen normalt.');
  };
  const gesture=event=>{const allowed=latched||!!(event.ctrlKey||event.metaKey);prompt=!allowed;apply(allowed);};
  // Capture runs before Leaflet's mouse/wheel listeners; locked events stay scrollable.
  for(const type of ['mousedown','pointerdown','touchstart','wheel','dblclick'])listen(node,type,gesture,{capture:true,passive:true});
  listen(window,'keydown',event=>{if(node===document.activeElement||node.contains(document.activeElement))apply(latched||!!(event.ctrlKey||event.metaKey));});
  listen(window,'keyup',event=>{if(!event.ctrlKey&&!event.metaKey)apply(latched);});
  listen(window,'blur',()=>{latched=false;apply(false);});
  listen(button,'click',()=>{latched=!latched;prompt=false;apply(latched);if(latched)node.focus({preventScroll:true});});
  node.tabIndex=0;node.setAttribute('aria-describedby',hint.id);apply(false);
  return {dispose(){if(disposed)return;apply(false);disposed=true;for(const remove of listeners)remove();},enabled:()=>enabled};
 }
};
// The card viewer and PNG export share the exact same visible membership.
const DistrictMap={map:null,layer:null,id:'',road:'',gesture:null,
 dispose(){this.gesture?.dispose();this.gesture=null;MapBackground.detach('districtMap');if(this.map){this.map.remove();this.map=null;}this.layer=null;},
 html(id){const c=card(id),members=MapExport.members(id);if(!MapExport.boundsPoints(id).length)return `<section class="panel"><h3><span data-ui="Geografisk kort">Geografisk kort</span></h3><p class="hint"><span data-ui="Tilføj og gem kortets adressevalg for at se husenes placering.">Tilføj og gem kortets adressevalg for at se husenes placering.</span></p><button data-action="geo-card" data-id="${id}"><span data-ui="Tegn og vælg adresser">Tegn og vælg adresser</span></button></section>`;
  const roads=[...new Set(members.map(a=>a.road))].sort(cmp);
  return `<section class="districtNavigation"><h3><span data-ui="Geografisk kort · besøgspunkter">Geografisk kort · besøgspunkter</span></h3>${!members.length?'<p class="hint"><span data-ui="Ingen besøg at vise efter udeladelser.">Ingen besøg at vise efter udeladelser.</span></p>':''}<div class="toolbar"><label>${ui('Vis vej')} <select id="districtMapRoad"><option value="" data-ui="Alle veje">Alle veje</option>${roads.map(r=>`<option value="${esc(r)}">${esc(r)}</option>`).join('')}</select></label><span class="hint" id="districtMapCount">${ui('{count} besøg',{count:members.reduce((s,a)=>s+a.count,0)})}</span></div>${MapBackground.toolbar('districtMap')}<div class="mapGestureControls"><button type="button" id="districtMapActivate" aria-pressed="false" aria-controls="districtMap">${ui('Aktivér kort · touch og tastatur')}</button></div><p id="districtMapGestureHint" class="hint mapGestureHint" role="status"></p><div id="districtMap" class="districtMap" data-ui-aria="Geografisk kort med besøgspunkter" aria-label="Geografisk kort med besøgspunkter"><div class="districtFallback">${MapExport.svg(id)}</div></div><p class="hint"><span data-ui="Rød prik = ét besøg. Adresser markeret IB, Se bort fra eller nedlagt hos kilden vises ikke som besøg. Veje og bygninger vises fra de lokalt hentede kortdata.">Rød prik = ét besøg. Adresser markeret IB, Se bort fra eller nedlagt hos kilden vises ikke som besøg. Veje og bygninger vises fra de lokalt hentede kortdata.</span></p><div class="actions"><button data-geo="export-map-osm" data-osm-export data-id="${id}" ${MapBackground.mode!=='road'?'disabled':''}><span data-ui="Gem PNG · OpenStreetMap">Gem PNG · OpenStreetMap</span></button><button data-geo="export-map" data-id="${id}"><span data-ui="Gem PNG · lokale kortdata">Gem PNG · lokale kortdata</span></button><button data-share="prepare" data-id="${id}"><span data-ui="Publicér / opdater på Google Drive">Publicér / opdater på Google Drive</span></button></div><p class="hint"><span data-ui="Vælg Vejkort ovenfor, og vent på indlæsning før OpenStreetMap-eksport. PNG’en zoomer automatisk til hele distriktsgrænsen og alle besøg, også hvis du har valgt én vej.">Vælg Vejkort ovenfor, og vent på indlæsning før OpenStreetMap-eksport. PNG’en zoomer automatisk til hele distriktsgrænsen og alle besøg, også hvis du har valgt én vej.</span></p></section>`;
 },
 mount(id){this.dispose();MapBackground.mode='road';this.id=id;this.road='';const node=el('districtMap');if(!node||typeof L==='undefined')return;node.innerHTML='';this.map=L.map(node,{preferCanvas:true,minZoom:8,maxZoom:21,attributionControl:true});this.layer=L.layerGroup().addTo(this.map);MapBackground.attach('districtMap',this.map,()=>this.draw(false),()=>{this.road='';if(el('districtMapRoad'))el('districtMapRoad').value='';this.draw(true);});this.draw();this.gesture=DistrictMapGesture.attach(this.map,node,el('districtMapActivate'),el('districtMapGestureHint'));},
 draw(fit=true){if(!this.map)return;this.layer.clearLayers();const c=card(this.id),all=MapExport.members(this.id),members=all.filter(a=>!this.road||a.road===this.road),points=MapExport.boundsPoints(this.id);
  for(const r of MapBackground.roads()?GeoUI.data.roads:[])L.polyline(r.points.map(p=>[p[1],p[0]]),{color:'#adb8bf',weight:4}).addTo(this.layer).bindTooltip(String(r.name||r.road||''));
  if(MapBackground.roads())GeoUI.drawDividers?.(this.layer);
  for(const b of MapBackground.buildings()?GeoUI.data.buildings:[])L.polygon(b.points.map(p=>[p[1],p[0]]),{color:'#9daba4',weight:1,fillColor:'#d1d8d1',fillOpacity:.8}).addTo(this.layer);
  if(c.geo_polygon?.length)L.polygon(c.geo_polygon.map(p=>[p[1],p[0]]),{color:cardColor(c),weight:2,fillOpacity:.05,dashArray:'6 4'}).addTo(this.layer);
  const counts=new Map();for(const a of members){const key=a.lng+'|'+a.lat;for(let j=0;j<a.count;j++){const i=counts.get(key)||0;counts.set(key,i+1);const angle=i*2.39996,r=Math.sqrt(i)*.000008;L.circleMarker([a.lat+Math.sin(angle)*r,a.lng+Math.cos(angle)*r/Math.cos(a.lat*Math.PI/180)],{radius:5,color:'white',weight:1,fillColor:'#ca4c43',fillOpacity:1}).addTo(this.layer).bindTooltip(esc(a.label||[a.road,a.number,a.floor,a.door].filter(Boolean).join(' ')));}}
  const bounds=this.road?members.map(a=>[a.lng,a.lat]):points;if(fit&&bounds.length)this.map.fitBounds(bounds.map(p=>[p[1],p[0]]),{padding:[30,30],maxZoom:18});
  const countNode=el('districtMapCount');if(countNode){const params={count:members.reduce((s,a)=>s+a.count,0)};countNode.dataset.ui='{count} besøg';countNode.dataset.uiParams=JSON.stringify(params);countNode.lang=I18n.language();countNode.textContent=I18n.format('{count} besøg',params);}
 }
};
document.addEventListener('change',e=>{if(e.target.id==='districtMapRoad'){DistrictMap.road=e.target.value;DistrictMap.draw();}});
