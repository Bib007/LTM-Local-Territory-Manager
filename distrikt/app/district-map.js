'use strict';
// View-only gesture gate. It never changes card membership, extent or approval.
const DistrictMapGesture={
 attach(map,node,button,hint,notice,label,icon){
  const handlers=['dragging','scrollWheelZoom','doubleClickZoom','touchZoom','boxZoom','keyboard','tapHold'];
  let latched=false,enabled=null,disposed=false,timer=null,cooling=false;
  const listeners=[],listen=(target,type,fn,options)=>{target.addEventListener(type,fn,options);listeners.push(()=>target.removeEventListener(type,fn,options));};
  const hideNotice=()=>{notice.classList.toggle('mapGestureNoticeVisible',false);notice.textContent='';delete notice.dataset.ui;delete notice.dataset.uiParams;};
  const clearNotice=()=>{if(timer!==null)clearTimeout(timer);timer=null;cooling=false;hideNotice();};
  const showNotice=()=>{
   if(cooling||disposed)return;cooling=true;
   I18n.content(notice,'Kortet er låst. Hold Ctrl/Command nede for at flytte eller zoome, eller vælg Aktivér kort.');
   notice.classList.toggle('mapGestureNoticeVisible',true);
   timer=setTimeout(()=>{hideNotice();timer=setTimeout(()=>{cooling=false;timer=null;},3000);},1800);
  };
  const apply=value=>{
   if(disposed||enabled===!!value)return;enabled=!!value;
   for(const key of handlers)map[key]?.[enabled?'enable':'disable']();
   node.classList.toggle('mapGestureLocked',!enabled);
   if(enabled)clearNotice();
  };
  const syncButton=()=>{
   button.setAttribute('aria-pressed',String(latched));
   I18n.content(label,latched?'Aktivt · Lås kortet igen':'Låst · Aktivér kort');
   icon.textContent=latched?'🔓':'🔒';
   I18n.content(hint,latched?'Kortet er aktivt. Flyt eller zoom med touch, mus eller piletaster og +/−. Vælg Lås kortet igen for almindelig rulning.':'Hold Ctrl/Command nede for at flytte eller zoome. På touch eller med tastatur: vælg Aktivér kort. Uden aktivering ruller dialogen normalt.');
  };
  const gesture=event=>{
   const allowed=latched||!!(event.ctrlKey||event.metaKey);apply(allowed);
   if(!allowed&&(event.type==='wheel'||event.type==='dblclick'||event.type==='touchmove'||((event.type==='pointermove'||event.type==='mousemove')&&event.buttons)))showNotice();
  };
  // Capture runs before Leaflet. Locked gestures remain passive so the dialog scrolls normally.
  for(const type of ['mousedown','pointerdown','touchstart','wheel','dblclick','pointermove','mousemove','touchmove'])listen(node,type,gesture,{capture:true,passive:true});
  listen(window,'keydown',event=>{
   if(node===document.activeElement||node.contains(document.activeElement)){
    apply(latched||!!(event.ctrlKey||event.metaKey));
    if(!enabled&&['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','+','-','=','Add','Subtract'].includes(event.key))showNotice();
   }
  });
  listen(window,'keyup',event=>{if(!event.ctrlKey&&!event.metaKey)apply(latched);});
  listen(window,'blur',()=>{latched=false;apply(false);clearNotice();syncButton();});
  listen(button,'click',()=>{latched=!latched;clearNotice();apply(latched);syncButton();if(latched)node.focus({preventScroll:true});});
  node.tabIndex=0;node.setAttribute('aria-describedby',hint.id);apply(false);syncButton();
  return {dispose(){if(disposed)return;apply(false);clearNotice();disposed=true;for(const remove of listeners)remove();},enabled:()=>enabled};
 }
};
// The private card viewer and local PNG export share the same membership.
const DistrictMap={map:null,layer:null,id:'',road:'',gesture:null,
 dispose(){this.gesture?.dispose();this.gesture=null;MapBackground.detach('districtMap');if(this.map){this.map.remove();this.map=null;}this.layer=null;},
 html(id){const c=card(id),members=MapExport.members(id);if(!MapExport.boundsPoints(id).length)return `<section class="panel"><h3><span data-ui="Geografisk kort">Geografisk kort</span></h3><p class="hint"><span data-ui="Tilføj og gem kortets adressevalg for at se husenes placering.">Tilføj og gem kortets adressevalg for at se husenes placering.</span></p><button data-action="geo-card" data-id="${id}"><span data-ui="Tegn og vælg adresser">Tegn og vælg adresser</span></button></section>`;
  const roads=[...new Set(members.map(a=>a.road))].sort(cmp);
  return `<section class="districtNavigation"><h3><span data-ui="Geografisk kort · besøgspunkter">Geografisk kort · besøgspunkter</span></h3>${!members.length?'<p class="hint"><span data-ui="Ingen besøg at vise efter udeladelser.">Ingen besøg at vise efter udeladelser.</span></p>':''}<div class="toolbar"><label>${ui('Vis vej')} <select id="districtMapRoad"><option value="" data-ui="Alle veje">Alle veje</option>${roads.map(r=>`<option value="${esc(r)}">${esc(r)}</option>`).join('')}</select></label><span class="hint" id="districtMapCount">${ui('{count} besøg',{count:members.reduce((s,a)=>s+a.count,0)})}</span></div>${MapBackground.toolbar('districtMap')}<div class="mapGestureControls"><button type="button" id="districtMapActivate" aria-pressed="false" aria-controls="districtMap"><span id="districtMapGestureIcon" aria-hidden="true">🔒</span><span id="districtMapGestureLabel">${ui('Låst · Aktivér kort')}</span></button></div><p id="districtMapGestureHint" class="hint mapGestureHint"></p><div class="districtMapFrame"><div id="districtMap" class="districtMap" data-ui-aria="Geografisk kort med besøgspunkter" aria-label="Geografisk kort med besøgspunkter"><div class="districtFallback">${MapExport.svg(id)}</div></div><div id="districtMapGestureNotice" class="mapGestureNotice" role="status" aria-atomic="true"></div></div><p class="hint"><span data-ui="Rød prik = ét gemt besøgspunkt. Tjek IB på kortets IB-liste. Adresser markeret Se bort fra eller nedlagt hos kilden vises ikke som besøg.">Rød prik = ét gemt besøgspunkt. Tjek IB på kortets IB-liste. Adresser markeret Se bort fra eller nedlagt hos kilden vises ikke som besøg.</span></p><div class="actions"><button data-geo="export-map-osm" data-osm-export data-id="${id}" ${MapBackground.mode!=='road'?'disabled':''}><span data-ui="Gem PNG · OpenStreetMap">Gem PNG · OpenStreetMap</span></button><button data-geo="export-map" data-id="${id}"><span data-ui="Gem PNG · lokale kortdata">Gem PNG · lokale kortdata</span></button><button data-share="prepare" data-id="${id}"><span data-ui="Publicér / opdater på Google Drive">Publicér / opdater på Google Drive</span></button></div><p class="hint"><span data-ui="Vælg Vejkort ovenfor, og vent på indlæsning før OpenStreetMap-eksport. PNG’en zoomer automatisk til hele distriktsgrænsen og alle besøg, også hvis du har valgt én vej.">Vælg Vejkort ovenfor, og vent på indlæsning før OpenStreetMap-eksport. PNG’en zoomer automatisk til hele distriktsgrænsen og alle besøg, også hvis du har valgt én vej.</span></p></section>`;
 },
 mount(id){this.dispose();MapBackground.mode='road';this.id=id;this.road='';const node=el('districtMap');if(!node||typeof L==='undefined')return;node.innerHTML='';this.map=L.map(node,{preferCanvas:true,minZoom:8,maxZoom:21,attributionControl:true});this.layer=L.layerGroup().addTo(this.map);MapBackground.attach('districtMap',this.map,()=>this.draw(false),()=>{this.road='';if(el('districtMapRoad'))el('districtMapRoad').value='';this.draw(true);});this.draw();this.gesture=DistrictMapGesture.attach(this.map,node,el('districtMapActivate'),el('districtMapGestureHint'),el('districtMapGestureNotice'),el('districtMapGestureLabel'),el('districtMapGestureIcon'));},
 draw(fit=true){if(!this.map)return;this.layer.clearLayers();const c=card(this.id),all=MapExport.members(this.id),members=all.filter(a=>!this.road||a.road===this.road),points=MapExport.boundsPoints(this.id);
  for(const r of MapBackground.roads()?GeoUI.data.roads:[])L.polyline(r.points.map(p=>[p[1],p[0]]),{color:'#adb8bf',weight:4}).addTo(this.layer).bindTooltip(esc(String(r.name||r.road||'')));
  if(MapBackground.roads())GeoUI.drawDividers?.(this.layer);
  for(const b of MapBackground.buildings()?GeoUI.data.buildings:[])L.polygon(b.points.map(p=>[p[1],p[0]]),{color:'#9daba4',weight:1,fillColor:'#d1d8d1',fillOpacity:.8}).addTo(this.layer);
  if(c.geo_polygon?.length)L.polygon(c.geo_polygon.map(p=>[p[1],p[0]]),{color:cardColor(c),weight:2,fillOpacity:.05,dashArray:'6 4'}).addTo(this.layer);
  const counts=new Map();for(const a of members){const key=a.lng+'|'+a.lat;for(let j=0;j<a.count;j++){const i=counts.get(key)||0;counts.set(key,i+1);const angle=i*2.39996,r=Math.sqrt(i)*.000008;L.circleMarker([a.lat+Math.sin(angle)*r,a.lng+Math.cos(angle)*r/Math.cos(a.lat*Math.PI/180)],{radius:5,color:'white',weight:1,fillColor:'#ca4c43',fillOpacity:1}).addTo(this.layer).bindTooltip(esc(a.label||[a.road,a.number,a.floor,a.door].filter(Boolean).join(' ')));}}
  const bounds=this.road?members.map(a=>[a.lng,a.lat]):points;if(fit&&bounds.length)this.map.fitBounds(bounds.map(p=>[p[1],p[0]]),{padding:[30,30],maxZoom:18});
  const countNode=el('districtMapCount');if(countNode){const params={count:members.reduce((s,a)=>s+a.count,0)};countNode.dataset.ui='{count} besøg';countNode.dataset.uiParams=JSON.stringify(params);countNode.lang=I18n.language();countNode.textContent=I18n.format('{count} besøg',params);}
 }
};
document.addEventListener('change',e=>{if(e.target.id==='districtMapRoad'){DistrictMap.road=e.target.value;DistrictMap.draw();}});
