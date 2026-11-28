'use strict';
/* Public data stored locally; online backgrounds are optional. */
const GeoUI={
  data:{addresses:[],buildings:[],roads:[],dividers:[],info:{}},loaded:false,map:null,layers:null,markers:[],draftLayer:null,
  bulkAutoBusy:false,bulkAutoProgress:null,session:0,suggestedOutline:null,previewSequence:0,saveBusy:false,loadSequence:0,noticeEpoch:0,jobNoticeEpoch:0,
  drawColor:'#477596',whole:false,target:'',ids:new Set(),polygon:[],mode:'choose',dirty:false,focus:[],view:null,job:null,jobTimer:null,busy:false,notice:'',rangeRoad:'',rangePost:'',pendingRange:null,
  // Capture values, not references: a late response must never replace a newer draft.
  draftStamp(includeRevision=true){const form=el('geoRangeForm'),range=form?.elements?[...form.elements].filter(e=>e.name).map(e=>[e.name,e.value,e.checked]):null;return JSON.stringify([page,this.session,this.whole,this.target,[...this.ids].sort(),this.polygon,this.drawColor,this.mode,this.dirty,includeRevision?state.revision:null,range]);},
  async syncWrite(stamp,apply,dialogGeneration,snapshot,formContext){
    let fresh;try{[,fresh]=await Promise.all([this.load(),snapshot?Promise.resolve(snapshot):api('/api/state').then(r=>r.json())]);}catch(error){WriteGuard.requireRefresh(error);throw error;}
    // The accepted mutation advances state.revision; only compare the editor draft here.
    const unchanged=this.draftStamp(false)===stamp&&(!formContext||dialogGeneration!==openDialog.generation||!el('dialog').open||FormDrafts.signature(formContext.form)===formContext.signature);state=fresh;
    if(unchanged){apply();if(page==='Kortopsætning')render();if(dialogGeneration!==undefined&&openDialog.generation===dialogGeneration)closeDialog();}
    else if(page==='Kortopsætning'){this.drawLayers();this.drawBoundary();this.updatePanel();}
    else if(!PendingSaves.protectPage())render();
    saved();return unchanged;
  },
  async saveBoundary(whole=false){
    if(this.saveBusy)return;
    if(!whole&&this.outlineApproval())throw Error(I18n.text('Gem de valgte adresser sammen med den foreslåede grænse.'));
    this.saveBusy=true;const stamp=this.draftStamp(false),data=whole?{points:this.polygon.map(p=>p.slice())}:{card_id:this.target,polygon:this.polygon.map(p=>p.slice())};
    try{if(whole||!this.selectionDirty())this.pendingStamp=stamp;
      await mutate(whole?'geo.main.save':'geo.boundary',data,{close:false,autosave:true,synchronize:(_result,snapshot)=>this.syncWrite(stamp,()=>{this.dirty=!whole&&this.selectionDirty();},undefined,snapshot)});
      toast(I18n.text(whole?'Samlet grænse gemt':'Grænse gemt'));
    }finally{this.saveBusy=false;this.pendingStamp=null;}
  },
  clearStaleFeedback(){this.noticeEpoch++;this.notice='';this.noticeUI=null;if(!this.busy){const status=el('geoDownloadStatus');if(status)status.hidden=true;}},
  setNotice(key,params={},suffix=''){this.noticeUI={key,params,suffix};this.notice=I18n.format(key,params)+(suffix?' '+I18n.text(suffix):'');this.noticeUI.value=this.notice;},
  noticeHTML(){const n=this.noticeUI;return n&&n.value===this.notice?ui(n.key,n.params)+(n.suffix?' '+ui(n.suffix):''):esc(this.notice);},
  localize(){this.areaPostcode();const hint=el('geoModeHint');if(hint)hint.innerHTML=ui(this.modeHint());const n=this.noticeUI;if(n&&n.value===this.notice)this.setNotice(n.key,n.params,n.suffix);},
  async load(){const sequence=++this.loadSequence,data=await(await api('/api/geo')).json();if(sequence!==this.loadSequence)return;this.data=data;this.loaded=true;if(typeof Navigation!=='undefined')Navigation.paintFollowupCount();},
  dispose(){if(this.map){const c=this.map.getCenter();this.view={center:[c.lat,c.lng],zoom:this.map.getZoom()};MapBackground.detach('geographicEditor');this.map.remove();this.map=null;}},
  selectionDirty(){const saved=new Set(card(this.target)?.address_ids||[]);return this.ids.size!==saved.size||[...this.ids].some(id=>!saved.has(id));},
  canLeave(){return !this.dirty||this.pendingStamp===this.draftStamp(false)||window.confirm(I18n.text(this.whole?'Den samlede grænse er ikke gemt. Vil du forlade den og kassere tegningen?':'Dit adressevalg er ikke gemt på kortet endnu. Vil du forlade det og kassere valget?'));},
  openCard(id){if(!this.canLeave())return;this.session++;this.dispose();MapBackground.mode='road';this.whole=false;this.target=id||'';this.streetApproval=null;const c=card(id);this.drawColor=cardColor(c);this.ids=new Set(c?.address_ids||[]);this.polygon=(c?.geo_polygon||[]).map(p=>p.slice());this.mode='choose';this.focus=[];this.manualPoint=null;this.dirty=false;this.clearStaleFeedback();this.view=null;page='Kortopsætning';query='';render();},
  async resumeJob(){const job=await(await api('/api/geo/job')).json();if(job.status==='running'){this.jobNoticeEpoch=this.noticeEpoch;this.job=job.id;this.busy=true;this.showJob(job);this.poll();}},
  addresses(){return this.data.addresses;},
  chosen(){return this.addresses().filter(a=>this.ids.has(a.id));},
  ignored(){return new Set((state.ignored||[]).map(i=>i.address_id));},
  addressTracking(id){return this.data.status?.[id]?.tracking||'';},
  addressTrackingBadge(id){const label={construction:'Under opbygning',other:'Andet'}[this.addressTracking(id)];return label?`<span class="badge warning">${ui(label)}</span>`:'';},
  addressTrackingButton(id){
    return typeof ProfilesUI!=='undefined'&&!ProfilesUI.canAction('geo.address_tracking')?'':`<button type="button" data-geo="address-tracking" data-id="${esc(id)}">${ui(this.addressTracking(id)?'Redigér markering':'Markér adresse')}</button>`;
  },
  // The card list is replaced after confirmed writes. Build the lookup once per
  // revision instead of scanning every card for every visible address marker.
  // Keep the original card-order precedence when legacy and ID links overlap.
  owner(a){
    const owner=this.data.status?.[a.id],cards=state.cards;
    let lookup=this._ownerLookup;
    if(!lookup||lookup.cards!==cards||lookup.revision!==state.revision){
      const byId=new Map(),byKey=new Map();
      for(let i=0;i<cards.length;i++){
        const c=cards[i],entry={card:c,index:i};
        for(const id of c.address_ids||[]){
          if(!byId.has(id))byId.set(id,[]);
          byId.get(id).push(entry);
        }
        for(const old of c.geo_addresses||[]){
          const key=this.key(old);
          if(!byKey.has(key))byKey.set(key,[]);
          byKey.get(key).push(entry);
        }
      }
      lookup=this._ownerLookup={cards,revision:state.revision,byId,byKey};
    }
    let first=null;
    for(const match of lookup.byId.get(a.id)||[])if(match.card.id!==this.target&&(!first||match.index<first.index))first=match;
    for(const match of lookup.byKey.get(this.key(a))||[])if(match.card.id!==this.target&&(!first||match.index<first.index))first=match;
    return first?.card||(owner?.card_id&&owner.card_id!==this.target?{id:owner.card_id,number:owner.card_number}:null);
  },
  key(a){return ['postcode','road','number','floor','door'].map(k=>String(a[k]||'').trim().toLowerCase()).join('|');},
  available(a,ignored=this.ignored()){return !a.retired&&!ignored.has(a.id)&&!this.owner(a);},
  // A new /api/geo response supplies a new addresses array; pan/zoom and
  // switching cards can reuse the same group membership without dropping any
  // addresses outside the current viewport.
  groups(){
    const addresses=this.addresses(),cached=this._groupCache;
    if(cached?.addresses===addresses&&cached.length===addresses.length)return cached.groups;
    const grouped=new Map();
    for(const a of addresses){
      const key=[a.postcode,a.road.toLowerCase(),a.number.toUpperCase()].join('|');
      if(!grouped.has(key))grouped.set(key,[]);
      grouped.get(key).push(a);
    }
    const groups=[...grouped.values()];
    this._groupCache={addresses,length:addresses.length,groups};
    return groups;
  },
  numberKey(value){const m=String(value).match(/^(\d+)\s*(.*)$/);return m?[Number(m[1]),m[2].toUpperCase()]:[Infinity,String(value)];},
  pointInside(p,poly){if(poly.length<3)return false;const[x,y]=p;let inside=false;for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length],cross=(x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0]);if(Math.abs(cross)<1e-12&&x>=Math.min(a[0],b[0])-1e-10&&x<=Math.max(a[0],b[0])+1e-10&&y>=Math.min(a[1],b[1])-1e-10&&y<=Math.max(a[1],b[1])+1e-10)return true;if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;}return inside;},
  page(){if(this.whole)return MainBoundaryUI.page();
    const info=this.data.info||{},c=card(this.target),roads=[...new Set(this.addresses().map(a=>a.road))].sort(cmp);
    return `<section class="panel geoIntro"><div class="between"><div><h2>${ui("Tegn og vælg adresser")}</h2><p class="hint">${ui('{addresses} lokale adresser · {buildings} bygninger · {roads} vejstykker. Kortvalg og grænser gemmes på dit lokale system.',{addresses:info.addresses||0,buildings:info.buildings||0,roads:info.roads||0})}</p></div><button data-main="open">${ui("Samlet distriktsgrænse")}</button><button data-geo="data">${ui("Hent / importer kortdata")}</button></div><div class="toolbar"><label>${ui("Kort")} <select id="geoTarget"><option value="" data-ui="Opret et nyt kort fra valget">${esc(I18n.text("Opret et nyt kort fra valget"))}</option>${state.cards.slice().sort((a,b)=>cmp(a.number,b.number)).map(c=>`<option value="${c.id}" ${c.id===this.target?'selected':''}>${esc(c.number)} · ${esc(areaName(c.area_id))}</option>`).join('')}</select></label><label>${ui("Grænsefarve")} <input id="geoColor" type="color" value="${this.drawColor}"></label><span class="hint">${ui(c?'Farven gemmes automatisk.':'Farven gemmes med det nye kort.')}</span>${c?`<button data-action="detail" data-id="${c.id}">${ui('Kort {number} og print',{number:c.number})}</button>`:''}</div><div class="toolbar geoModes"><button data-geo="import-boundary">${ui("Importér KML / GeoJSON")}</button><button data-geo="auto">${ui("Auto huse inden for grænsen")}</button><button data-geo="auto-all" ${this.bulkAutoBusy||this.dirty||!state.cards.some(c=>!c.archived&&c.geo_polygon?.length>=3)?'disabled':''}>${ui("Auto huse inden for grænsen på alle kort")}</button>${this.bulkAutoProgress?`<span role="status">${ui("Kort behandlet: {done} / {total}",this.bulkAutoProgress)}</span>`:''}<button data-geo="manual">${ui("Tilføj adresse manuelt")}</button></div><div class="geoWorkspace"><div class="geoMapColumn">${MapBackground.toolbar('geographicEditor')}<div id="geographicEditor" class="geographicEditor" ${I18n.attribute('aria',"Interaktivt lokalt kort")}></div>${this.editorTools()}<p class="hint" id="geoModeHint">${ui(this.modeHint())}</p><p class="hint geoAttribution">${ui("Veje og bygninger: © OpenStreetMap-bidragsydere, ODbL. Adresser og officielle vejlinjer: DAR · øvrige veje og bygninger: OpenStreetMap. Kortbaggrunden vælges ovenfor. PNG kan gemmes med lokale kortdata eller det viste OpenStreetMap-udsnit.")}</p><div class="notice" id="geoNotice" ${!this.notice?'hidden':''}>${this.noticeHTML()}</div><details class="geoRange" open><summary>${ui("Vælg ud fra vej og husnumre")}</summary><form id="geoRangeForm"><div class="geoRangeFields"><div><label>${ui("Vejnavn")}</label>${RoadSearch.field('geoRangeRoad',this.rangeRoad)}</div><div><label>${ui("Postnummer")}</label><input name="postcode" value="${esc(this.rangePost)}" pattern="[0-9]{4}" maxlength="4" ${I18n.attribute('placeholder',"Postnummer")} required></div><div><label>${ui("Fra")}</label><input name="from" ${I18n.attribute('placeholder',"Fra")} required></div><div><label>${ui("Til")}</label><input name="to" ${I18n.attribute('placeholder',"Til")} required></div><div><label>${ui("Numre")}</label><select name="parity"><option value="all" data-ui="Alle">${esc(I18n.text("Alle"))}</option><option value="even" data-ui="Lige">${esc(I18n.text("Lige"))}</option><option value="odd" data-ui="Ulige">${esc(I18n.text("Ulige"))}</option></select></div></div><label class="check"><input type="checkbox" data-online-search ${RoadSearch.online?'checked':''}> ${ui("Online vejforslag fra DAR")}</label><div class="actions"><button class="primary">${ui("Vis og vælg adresserne")}</button><button type="button" data-geo="road">${ui("Hent en vej fra DAR")}</button></div><p class="hint">${ui("Valget omfatter alle kendte lejligheder.")} ${ui("Grænseforslaget holder andre indlæste adresseprikker udenfor og tager hensyn til nabodistrikter.")}</p></form></details></div><section class="geoChosen"><div id="geoSelection"></div><div id="geoHouse"></div></section></div></section><details class="panel"><summary>${ui("Eget baggrundskort")}</summary>${legacyMapSetup()}</details>`;
  },
  // Keep real buttons outside Leaflet so map gestures and keyboard focus stay independent.
  editorTools(whole=false){
    const tools=[
      ['move','Flyt hjørner','M8 3H3v5 M3 3l6 6 M16 3h5v5 M21 3l-6 6 M3 16v5h5 M3 21l6-6 M21 16v5h-5 M21 21l-6-6'],
      ['insert','Indsæt hjørne på kanten','M3 12h6 M15 12h6 M12 9v6 M9 3h6v6H9z M9 15h6v6H9z'],
      ['erase','Fjern prikker','M8 8l8 8 M16 8l-8 8 M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20'],
      ...(whole?[
        ['new','Tegn ny grænse','M4 20l4-1L20 7l-3-3L5 16z'],
        ['append','Tilføj flere hjørner','M4 4v16h16 M12 6v8 M8 10h8']
      ]:[
        ['choose','Vælg huse','M3 11l9-8 9 8 M5 9v12h14V9 M10 21v-7h4v7'],
        ['draw','Tegn grænse','M4 20l4-1L20 7l-3-3L5 16z']
      ]),
      ['undo',whole?'Fortryd sidste hjørne':'Fortryd hjørne','M9 4L3 10l6 6 M3 10h11a7 7 0 0 1 7 7v3']
    ];
    return `<div class="toolbar geoMapTools" role="group" ${I18n.attribute('aria',"Rediger grænsen · tegn, flyt og indsæt hjørner")}>${tools.map(([action,label,path])=>`<button type="button" data-${whole?'main':'geo'}="${action}" data-map-tool="${action}" ${['move','insert','erase','choose','draw','append'].includes(action)?`aria-pressed="${this.mode===(action==='append'?'draw':action)}"`:''}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="${path}"/></svg>${ui(label)}</button>`).join('')}</div>`;
  },
  syncEditorTools(){
    for(const b of document.querySelectorAll?.('[data-map-tool]')||[]){
      const action=b.dataset.mapTool,mode=action==='append'?'draw':action;
      if(b.hasAttribute('aria-pressed')){b.setAttribute('aria-pressed',String(this.mode===mode));b.classList.toggle('primary',this.mode===mode);}
      b.disabled=action==='insert'?this.polygon.length<3:['erase','undo'].includes(action)?!this.polygon.length:false;
    }
  },
  modeHint(){return this.mode==='erase'?'Klik på en prik for at fjerne hjørnet. Gem grænsen bagefter.':this.mode==='draw'?'Klik hjørnerne rundt om distriktet. Du kan zoome og flytte kortet imens. Vælg derefter Auto huse eller Gem grænse.':this.mode==='insert'?'Klik på grænselinjen for at indsætte et hjørne. Vælg Flyt hjørner bagefter, og gem grænsen.':this.mode==='move'?'Træk de orange hjørner til den ønskede placering. Gem bagefter.':'Klik et husnummer for at vælge eller fravælge alle ledige lejligheder i huset. Klik en bygning for at se de nærliggende adresser.';},
  mount(){
    const node=el('geographicEditor');if(!node||typeof L==='undefined')return;
    // A delayed Leaflet redraw must not touch an already destroyed canvas.
    const renderer=L.canvas(),redraw=renderer._redraw;renderer._redraw=function(){if(this._map&&this._ctx)return redraw.call(this);};
    this.map=L.map(node,{renderer,preferCanvas:true,zoomControl:true,minZoom:8,maxZoom:21,attributionControl:true}).setView(this.view?.center||[56,10],this.view?.zoom||8);
    this.layers=L.layerGroup().addTo(this.map);this.draftLayer=L.layerGroup().addTo(this.map);
    MapBackground.attach('geographicEditor',this.map,()=>this.drawLayers(),()=>{const points=this.polygon.length?this.polygon:this.addresses().map(a=>[a.lng,a.lat]);if(points.length)this.map.fitBounds(points.map(p=>[p[1],p[0]]),{padding:[35,35],maxZoom:18,animate:false});});
    this.drawBoundary();this.updatePanel();
    if(!this.view){let points=this.polygon.length?this.polygon:this.chosen().map(a=>[a.lng,a.lat]);if(!points.length)points=this.addresses().map(a=>[a.lng,a.lat]);if(points.length)this.map.fitBounds(points.map(p=>[p[1],p[0]]),{padding:[35,35],maxZoom:18,animate:false});}
    this.drawLayers();
    if(this.whole)this.drawBoundary();
    this.map.on('click',e=>{this.manualPoint=e.latlng;if(this.mode==='draw'){if(this.whole&&this.polygon.length>=5000){toast(I18n.text('Højst 5.000 hjørner.'));return;}this.clearStaleFeedback();this.polygon.push([Number(e.latlng.lng.toFixed(7)),Number(e.latlng.lat.toFixed(7))]);this.dirty=true;this.drawBoundary();this.updatePanel();}});
    this.map.on('tooltipopen',()=>I18n.applyShell());
    this.map.on('moveend',()=>{this.drawLayers();if(this.whole)this.drawBoundary();});
    if(!this.loaded){const session=this.session;this.load().then(()=>{if(page==='Kortopsætning'&&session===this.session){this.drawLayers();this.drawBoundary();this.updatePanel();}}).catch(e=>toast(e));}
  },
  drawDividers(layer){
    for(const item of this.data.dividers||[]){const rail=item.divider_type==='rail',underground=item.tunnel&&item.tunnel!=='no';L.polyline(item.points.map(([x,y])=>[y,x]),{className:'naturalDivider',color:rail?'#69737c':'#5598bf',weight:rail?3:4,opacity:.8,dashArray:underground?'3 5':rail?'9 5':undefined,interactive:false}).addTo(layer);}
  },
  drawLayers(){
    if(!this.map||!this.layers)return;this.layers.clearLayers();this.markers=[];if(!this.whole&&this.data.main_boundary?.points?.length>=3)L.polygon(this.data.main_boundary.points.map(p=>[p[1],p[0]]),{color:'#dc9d32',weight:2,fillOpacity:.025,dashArray:'8 6',interactive:false}).addTo(this.layers);
    const namedRoads=new Set();for(const r of MapBackground.roads()?this.data.roads:[]){const path=L.polyline(r.points.map(p=>[p[1],p[0]]),{color:r.road_type==='footway'?'#a6adb0':'#b4bdc4',weight:r.road_type==='primary'?7:4,opacity:.85}).addTo(this.layers);if(r.name&&!namedRoads.has(r.name)){namedRoads.add(r.name);path.bindTooltip(esc(r.name),{permanent:this.map.getZoom()>=17,direction:'center',className:'geoStreet'});}}
    if(MapBackground.roads())this.drawDividers(this.layers);
    for(const b of MapBackground.buildings()?this.data.buildings:[]){const shape=L.polygon(b.points.map(p=>[p[1],p[0]]),{color:'#8193a0',weight:1,fillColor:'#d9dedc',fillOpacity:.8}).addTo(this.layers);shape.on('click',e=>{if(this.mode!=='choose')return;L.DomEvent.stopPropagation(e.originalEvent||e);this.manualPoint=e.latlng;this.focus=this.groups().filter(g=>this.pointInside([g[0].lng,g[0].lat],b.points)||b.points.some(p=>this.map.distance([p[1],p[0]],[g[0].lat,g[0].lng])<9)).flat().map(a=>a.id);if(!this.focus.length)toast(I18n.text('Ingen hentet adresse ved bygningen. Hent DAR-adresser eller tilføj en adresse manuelt ved at klikke kortet.'));this.updatePanel();});}
    for(const c of state.cards.filter(c=>c.id!==this.target&&c.geo_polygon?.length>=3))L.polygon(c.geo_polygon.map(p=>[p[1],p[0]]),{color:cardColor(c),weight:1,fillOpacity:.04,dashArray:'5 4'}).bindTooltip(ui('kort {number}',{number:c.number})).addTo(this.layers);
    const ignored=this.ignored(),bounds=this.map.getBounds().pad(.2);
    for(const group of this.groups()){
      if(!bounds.contains([group[0].lat,group[0].lng]))continue;
      const a=group[0],selected=group.filter(a=>this.ids.has(a.id)).length,blocked=group.every(a=>ignored.has(a.id)||this.owner(a)),color=selected===group.length?'#248e5a':selected?'#cc962f':blocked?'#8995a0':'#416b93';
      const marker=L.circleMarker([a.lat,a.lng],{radius:7,color:'white',weight:2,fillColor:color,fillOpacity:1}).addTo(this.layers);
      marker.bindTooltip(`${esc(a.number)}${group.length>1?' · '+ui('{count} adresser',{count:group.length}):''}`,{permanent:this.map.getZoom()>=18,direction:'top',className:'geoNumber'});
      marker.on('click',e=>{L.DomEvent.stopPropagation(e.originalEvent||e);if(this.mode==='choose'){this.focus=group.map(a=>a.id);this.toggleHouse(group);}else if(this.whole&&this.mode==='view'){this.focus=group.map(a=>a.id);this.updateAddressPanel();}else if(this.mode==='draw'){if(this.whole&&this.polygon.length>=5000){toast(I18n.text('Højst 5.000 hjørner.'));return;}this.clearStaleFeedback();this.polygon.push([a.lng,a.lat]);this.dirty=true;this.drawBoundary();this.updatePanel();}});
      this.markers.push({marker,group});
    }
  },
 insertCorner(point){const poly=this.polygon;if(poly.length<2)return;let best=Infinity,index=0;const q=this.map.latLngToLayerPoint([point[1],point[0]]);for(let i=0;i<poly.length;i++){const a=this.map.latLngToLayerPoint([poly[i][1],poly[i][0]]),b=this.map.latLngToLayerPoint([poly[(i+1)%poly.length][1],poly[(i+1)%poly.length][0]]),dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((q.x-a.x)*dx+(q.y-a.y)*dy)/(dx*dx+dy*dy||1))),d=(q.x-a.x-t*dx)**2+(q.y-a.y-t*dy)**2;if(d<best){best=d;index=i;}}const limit=5000;if(poly.length>=limit)throw Error(I18n.format('Grænsen kan højst have {count} hjørner.',{count:limit}));poly.splice(index+1,0,point);this.dirty=true;this.drawBoundary();this.updatePanel();},
  removeCorner(index){
    if(!Number.isInteger(index)||index<0||index>=this.polygon.length)return;
    this.polygon.splice(index,1);
    this.dirty=true;
    this.drawBoundary();
    this.updatePanel();
  },
  cornerRemovalMarker(point,index){
    const marker=L.marker([point[1],point[0]],{
      keyboard:true,title:I18n.format('Fjern hjørne {number}',{number:index+1}),
      icon:L.divIcon({className:'geoCorner geoCornerRemove',html:'×',iconSize:[26,26],iconAnchor:[13,13]})
    }).addTo(this.draftLayer);
    marker.on('click',event=>{
      L.DomEvent.stopPropagation(event.originalEvent||event);
      this.removeCorner(index);
    });
    return marker;
  },
  drawBoundary(){if(this.whole){MainBoundaryUI.draw();return;}
    if(!this.draftLayer)return;this.draftLayer.clearLayers();
    for(const change of this.neighborChanges())L.polygon(change.polygon.map(p=>[p[1],p[0]]),{color:'#dc9d32',weight:3,dashArray:'8 5',fillOpacity:.06,interactive:false}).bindTooltip(ui('Ny grænse · kort {number}',{number:change.number})).addTo(this.draftLayer);
    if(this.polygon.length>=3){const line=L.polygon(this.polygon.map(p=>[p[1],p[0]]),{color:this.drawColor,weight:3,fillColor:this.drawColor,fillOpacity:.12,interactive:false}).addTo(this.draftLayer);if(this.mode==='insert'){const edge=L.polyline([...this.polygon,this.polygon[0]].map(p=>[p[1],p[0]]),{color:'#dc9d32',weight:14,opacity:0,interactive:true}).addTo(this.draftLayer);edge.on('click',e=>{L.DomEvent.stopPropagation(e.originalEvent||e);try{this.insertCorner([Number(e.latlng.lng.toFixed(7)),Number(e.latlng.lat.toFixed(7))]);}catch(err){toast(err);}});}}
    else if(this.polygon.length)L.polyline(this.polygon.map(p=>[p[1],p[0]]),{color:this.drawColor,weight:3,interactive:false}).addTo(this.draftLayer);
    this.polygon.forEach((p,i)=>{if(this.mode==='erase'){this.cornerRemovalMarker(p,i);}else if(this.mode==='move'){const marker=L.marker([p[1],p[0]],{draggable:true,icon:L.divIcon({className:'geoCorner',html:'',iconSize:[14,14],iconAnchor:[7,7]})}).addTo(this.draftLayer);marker.on('dragend',()=>{const n=marker.getLatLng();this.polygon[i]=[Number(n.lng.toFixed(7)),Number(n.lat.toFixed(7))];this.dirty=true;this.drawBoundary();this.updatePanel();});}else L.circleMarker([p[1],p[0]],{radius:4,color:'#b16e10',fillOpacity:1}).addTo(this.draftLayer);});
  },
  toggleHouse(group){this.clearStaleFeedback();const ignored=this.ignored(),eligible=group.filter(a=>this.available(a,ignored)),all=eligible.length&&eligible.every(a=>this.ids.has(a.id));for(const a of eligible)all?this.ids.delete(a.id):this.ids.add(a.id);this.dirty=true;this.drawLayers();this.updatePanel();if(!eligible.length)toast(I18n.text('Adresserne er allerede på et andet kort eller markeret Se bort fra.'));},
  updatePanel(){if(this.whole){MainBoundaryUI.panel();this.updateAddressPanel();return;}this.syncEditorTools();
    const node=el('geoSelection');if(!node)return;const chosen=this.chosen(),visits=chosen.reduce((n,a)=>n+a.count,0),c=card(this.target),outside=this.polygon.length>=3?chosen.filter(a=>!this.pointInside([a.lng,a.lat],this.polygon)).length:0;
    node.innerHTML=`<h2>${ui('{count} adresser valgt',{count:chosen.length})}</h2><div class="geoTotal">${visits}<small>${ui("besøg inkl. IB")}</small></div><p class="hint">${ui('{count} hjørner',{count:this.polygon.length})}${outside?' · '+ui('{count} valgte adresser uden for grænsen',{count:outside}):''} · ${ui(this.dirty?'valg endnu ikke gemt':'gemt valg / intet nyt valg')}</p><div class="actions"><button data-geo="save" class="primary" ${!chosen.length&&(c||this.polygon.length<3)?'disabled':''}>${c?ui('Gem adresser på kort {number}',{number:c.number}):ui(chosen.length?'Opret kort fra valget':'Opret kort under opbygning')}</button>${c?`<button data-geo="boundary" `+(this.polygon.length<3||this.outlineApproval()?'disabled':'')+`>${ui('Gem kun grænse')}</button>`:''}<button data-geo="suggest-outline" ${!chosen.length?'disabled':''}>${ui('Foreslå grænse')}</button><button data-geo="clear" ${!chosen.length?'disabled':''}>${ui("Ryd valget")}</button></div>${c?.addresses?.length||c?.imported_addresses?.some(a=>Number.isFinite(a.lat)&&Number.isFinite(a.lng))?`<div class="actions">${c?.addresses?.length?`<button data-geo="street-lines">${ui('Foreslå DAR-adresser fra vejlisten')}</button>`:''}${c?.imported_addresses?.some(a=>Number.isFinite(a.lat)&&Number.isFinite(a.lng))?`<button data-geo="imported-points">${ui('Foreslå DAR-adresser fra koordinater')}</button>`:''}</div>`:''}${c&&!c.temporary?`<div class="actions"><button data-action="print-options" data-id="${c.id}" data-side="front">${ui("Print forside")}</button><button data-action="print-options" data-id="${c.id}" data-side="back">${ui("Print IB-bagside")}</button><button data-geo="export-map-osm" data-osm-export data-id="${c.id}" ${MapBackground.mode!=='road'?'disabled':''}>${ui("Gem PNG · OpenStreetMap")}</button><button data-geo="export-map" data-id="${c.id}">${ui("Gem PNG · lokale kortdata")}</button></div>`:''}<div class="geoSelectedList">${chosen.slice().sort((a,b)=>cmp(a.road,b.road)||cmp(a.number,b.number)||cmp(a.floor,b.floor)).map(a=>`<div><button class="link" data-geo="focus" data-id="${esc(a.id)}">${esc(a.road)} ${esc(a.number)}${a.floor||a.door?' · '+esc([a.floor,a.door].filter(Boolean).join(' ')):''}</button><button data-geo="remove" data-id="${esc(a.id)}" ${I18n.attribute('aria',"Fravælg adresse")}>×</button></div>`).join('')||`<p class="hint">${ui("Hent en vej eller et mindre kortudsnit for at vælge huse.")}</p>`}</div>`;
    this.updateAddressPanel();
    const hint=el('geoModeHint');if(hint)hint.innerHTML=ui(this.modeHint());const notice=el('geoNotice');if(notice){notice.hidden=!this.notice;notice.innerHTML=this.noticeHTML();}
  },
  updateAddressPanel(){
    const ignoredIds=this.ignored(),detail=el('geoHouse'),focus=this.addresses().filter(a=>this.focus.includes(a.id));if(detail)detail.innerHTML=focus.length?`<hr><h3>${ui("Adresser ved det valgte hus")}</h3><p class="hint">${ui('Kontrollér indgang og husnummer, især ved sammenbyggede huse. {count} kendte adresser.',{count:focus.length})}</p>${focus.map(a=>{const owner=this.owner(a),ignored=ignoredIds.has(a.id),retired=a.retired;return `<div class="geoUnit">${this.whole?`<b>${esc(a.label)}</b>`:`<label class="check"><input type="checkbox" data-geo-check="${esc(a.id)}" ${this.ids.has(a.id)?'checked':''} ${owner||ignored||retired?'disabled':''}> ${esc(a.label)}</label>`}<small>${ui(a.type)} · ${ui('{count} besøg',{count:a.count})}${retired?' · '+ui('nedlagt hos DAR'):''}${owner?' · '+ui('kort {number}',{number:owner.number}):ignored?' · '+ui('Se bort fra'):''}</small><div class="actions"><button data-geo="type" data-id="${esc(a.id)}">${ui("Adressetype")}</button>${this.addressTrackingButton(a.id)}${!owner&&!ignored&&!retired&&(!this.data.status?.[a.id]?.card_id)&&(!state.profile||ProfilesUI.canAction('ignore.save'))?`<button type="button" data-geo="ignore" data-id="${esc(a.id)}">${ui("Se bort fra")}</button>`:''}</div>${this.addressTrackingBadge(a.id)}</div>`;}).join('')}`:'';
  },
  async preview(data,target=this.target){return (await(await api('/api/mutate',{action:'geo.preview',data:{...data,card_id:target||undefined}})).json()).result;},
  useSuggestedOutline(result){
    this.polygon=result.outline||[];
    this.suggestedOutline={session:this.session,ids:JSON.stringify([...this.ids].sort()),points:JSON.stringify(this.polygon),expected:result.outline_expected,status:result.outline_status,changes:result.outline_changes||[],reason:result.outline_reason,reasonNumber:result.outline_reason_number};
  },
  outlineApproval(){
    const suggestion=this.suggestedOutline;
    return suggestion?.session===this.session&&suggestion.ids===JSON.stringify([...this.ids].sort())&&suggestion.points===JSON.stringify(this.polygon)?suggestion.expected:null;
  },
  neighborChanges(){return this.outlineApproval()?(this.suggestedOutline.changes||[]):[];},
  neighborConsent(){const changes=this.neighborChanges();return changes.length?`<p class="notice warning">${ui('Forslaget kræver nye grænser på nabokort. Adresser, IB, udlån og historik flyttes ikke.')} ${changes.map(c=>esc(c.number)).join(', ')}</p><label class="check"><input id="geoNeighborApproval" type="checkbox" required> ${ui('Jeg godkender de viste nye grænser på nabokortene')}</label>`:'';},
  outlineNotice(result){
    if(result.outline_reason)return I18n.format(result.outline_reason,{number:result.outline_reason_number||''});
    if(result.outline_status==='neighbors')return 'Forslaget kræver ændringer af nabogrænser. De nye nabogrænser vises med orange streger. Godkend dem ved Gem.';
    if(result.outline_status==='crossing')return 'En valgt adresse ligger i et nabodistrikt. Forslaget overlapper derfor nabogrænsen. Kontrollér overlappet på kortet.';
    if(result.outline_status==='unavailable')return 'Der kunne ikke tegnes en sikker automatisk grænse. Tegn grænsen manuelt.';
    return '';
  },
  async selectPreview(data){
    const stamp=this.draftStamp(),sequence=++this.previewSequence,dialogGeneration=openDialog.generation,result=await this.preview(data);
    if(sequence!==this.previewSequence||stamp!==this.draftStamp()||dialogGeneration!==openDialog.generation)return false;
    const blocked=new Set([...result.ignored,...(result.retired||[]),...result.conflicts.map(c=>c.id)]);
    if(data.suggest_outline&&blocked.size)throw Error(I18n.text('Nogle valgte adresser er allerede brugt eller markeret Se bort fra. Ret valget først.'));
    if(data.suggest_outline&&result.outline_status==='unavailable'){
      this.setNotice(this.outlineNotice(result));this.updatePanel();return false;
    }
    const selected=result.addresses.filter(a=>!blocked.has(a.id));
    if(data.mode==='imported_points'){
      const params={count:selected.length, unmatched:result.unmatched_points, blocked:blocked.size};
      const notice='{count} DAR-adresser foreslået fra koordinater. {unmatched} uden entydigt match, {blocked} blokeret.';
      if(!selected.length){
        this.setNotice(notice,params,'Hent DAR-adresser for området, og prøv igen.');
        this.updatePanel();
        return false;
      }
      this.streetApproval=null;
      this.clearStaleFeedback();
      this.ids=new Set(selected.map(a=>a.id));
      this.dirty=true;this.mode='choose';
      this.setNotice(notice,params,'Kontrollér forslaget på kortet, og gem adressevalget.');
      this.drawLayers();this.updatePanel();
      return true;
    }
    this.ids=new Set(selected.map(a=>a.id));
    if(data.mode==='range'||data.suggest_outline)this.useSuggestedOutline(result);
    if(data.mode==='range')this.streetApproval=null;
    this.dirty=true;this.mode='choose';
    this.setNotice('{count} adresser valgt. {conflicts} findes på andre kort / i gendannelse, og {ignored} er markeret Se bort fra. Valget skal gemmes på et kort.',{count:this.ids.size,conflicts:result.conflicts.length,ignored:result.ignored.length},data.mode==='polygon'?'Valget dækker kun de lokalt hentede adresser.':this.outlineNotice(result));
    this.drawLayers();this.drawBoundary();this.updatePanel();
    if(this.ids.size&&data.mode==='range')this.map?.fitBounds(this.chosen().map(a=>[a.lat,a.lng]),{padding:[40,40],maxZoom:18});
    return true;
  },
  async save(number,extra={}){
    if(this.saveBusy)return;
    if(this.suggestedOutline?.session===this.session&&this.suggestedOutline.changes?.length&&!this.outlineApproval())throw Error(I18n.text('Adressevalget eller grænsen er ændret. Vælg Foreslå grænse igen.'));
    const approveNeighbors=this.neighborChanges().length>0;
    if(approveNeighbors&&!el('geoNeighborApproval')?.checked)throw Error(I18n.text('Godkend ændringerne af nabokortenes grænser, før du gemmer.'));
    this.saveBusy=true;
    const stamp=this.draftStamp(),dialogGeneration=openDialog.generation,dialogWasOpen=el('dialog').open,form=dialogWasOpen?el('dialog').querySelector?.('form'):null,formContext=form?{form,signature:FormDrafts.signature(form)}:null;
    const data={...extra,...(approveNeighbors?{approve_neighbors:true}:{}),...(this.streetApproval||{}),outline_expected:this.outlineApproval()||undefined,map_color:this.drawColor,card_id:this.target||undefined,number,address_ids:[...this.ids],polygon:this.polygon.length?this.polygon.map(p=>p.slice()):undefined};
    try{
      const boundaryOnly=!data.card_id&&data.planned===true&&!data.address_ids.length;
      const preview=boundaryOnly?{conflicts:[],ignored:[]}:await this.preview({address_ids:data.address_ids},data.card_id);
      if(stamp!==this.draftStamp()||dialogGeneration!==openDialog.generation||(dialogWasOpen&&!el('dialog').open)||(formContext&&FormDrafts.signature(form)!==formContext.signature))throw Error(I18n.text('Valget er ændret. Kontrollér det og gem igen.'));
      if(preview.retired?.length)throw Error(I18n.text('Nogle adresser er nedlagt hos DAR. Fjern dem fra valget først.'));
      if(preview.conflicts.length||preview.ignored.length)throw Error(I18n.text('Nogle valgte adresser er allerede brugt eller markeret Se bort fra. Ret valget først.'));
      const writeStamp=this.draftStamp(false);this.pendingStamp=writeStamp;
      // Capture the edit base and payload before dismissing the confirmation.
      // A modeless copy would otherwise reappear while the save is in flight.
      const write=mutate('geo.assign',data,{close:false,autosave:true,synchronize:(response,snapshot)=>this.syncWrite(writeStamp,()=>{this.target=response.result.id;const c=card(this.target);this.ids=new Set(c.address_ids||[]);this.polygon=c.geo_polygon.map(p=>p.slice());this.dirty=false;this.streetApproval=null;this.suggestedOutline=null;this.setNotice('Adresser, vejliste og grænse er gemt. Kortets udlånshistorik er bevaret.');},dialogGeneration,snapshot,formContext)});
      if(dialogWasOpen&&dialogGeneration===openDialog.generation&&el('dialog').open)closeDialog();
      await write;
      toast(I18n.text(card(this.target)?.planned?'Kort under opbygning gemt':'Kort gemt · forsiden kan nu printes'));
    }finally{this.saveBusy=false;this.pendingStamp=null;}
  },
  postcodeList(){return (this.data.info?.postcodes||[]).map(p=>{const done=p.roads.filter(r=>r.status==='done').length,missing=p.roads.filter(r=>r.status!=='done'),sourceDay=p.snapshot?.slice(0,10),old=sourceDay&&dayDiff(state.today,sourceDay)>=30;return `<div class="postcodeSaved"><div class="between"><span><b>${esc(p.postcode)} ${esc(p.name)}</b><br><small>${ui('{done} / {total} veje hentet · kildedato {date}',{done,total:p.roads.length,date:fmt(sourceDay||p.updated_at?.slice(0,10))})}</small>${old?`<br><span class="badge warning">${ui("Kortdata er mindst 30 dage gamle")}</span>`:''}</span><div class="actions"><button type="button" data-geo="resume-postcode" data-id="${esc(p.postcode)}" ${this.busy?'disabled':''}>${ui(missing.length?'Fortsæt / genprøv':'Vis adresser')}</button>${!missing.length?`<button type="button" data-geo="refresh-postcode" data-id="${esc(p.postcode)}" ${this.busy?'disabled':''}>${ui("Opdater postnummer")}</button>`:''}</div></div>${missing.length?`<details><summary>${ui('{count} veje mangler',{count:missing.length})}</summary><div class="postcodeErrors">${missing.map(r=>`<p>${esc(r.road)}<small>${r.error?esc(r.error):ui('Afventer hentning')}</small></p>`).join('')}</div></details>`:''}</div>`;}).join('');},
  areaSource(configured){const f=el('geoAreaForm');if(!f?.elements?.addresses)return;delete f.dataset.sourceError;f.dataset.areaAddressSource=configured?'graphql':'legacy';f.elements.addresses.disabled=false;this.areaPostcode();},
  areaSourceFailed(){const f=el('geoAreaForm');if(!f?.elements?.addresses)return;f.dataset.sourceError='yes';f.elements.addresses.disabled=true;this.areaPostcode();},
  areaPostcode(){const f=el('geoAreaForm');if(!f?.elements?.addresses)return;const known=!!f.dataset.areaAddressSource,need=f.elements.addresses.checked&&f.dataset.areaAddressSource==='legacy';const wrapper=el('geoAreaPostcodeField'),input=f.elements.postcode,hint=el('geoAreaSourceHint');if(wrapper)wrapper.hidden=!need;if(input){input.disabled=!need;input.required=need;}if(hint)I18n.content(hint,f.dataset.sourceError?'Adressekilden kunne ikke kontrolleres. Kortdata kan stadig hentes uden adresser. Åbn dialogen igen for at prøve.':!known?'Kortdata fra OpenStreetMap kræver intet postnummer. Kontrollerer adressekilden…':need?'Den ældre adressekilde kræver postnummer for DAR-adresser. Veje, bygninger, vandløb og jernbaner hentes uden postnummer.':f.elements.addresses.checked?'Datafordeleren henter adresser i alle postnumre i udsnittet. Du skal ikke angive postnummer.':'Veje, bygninger, vandløb og jernbaner fra OpenStreetMap kræver intet postnummer.');},
  dataDialog(){
    openDialog(`<h2>${ui("Kortdata")}</h2><form id="geoPostcodeForm"><fieldset><legend>${ui("Hent hele postnummeret")}</legend><label>${ui("Postnummer")}</label><input name="postcode" value="${esc(this.rangePost)}" pattern="[0-9]{4}" maxlength="4" ${I18n.attribute('placeholder',"Postnummer")} required><label class="check"><input name="refresh" type="checkbox"> ${ui("Opdater alle veje fra kilden igen")}</label><p class="hint">${ui("Henter officielle vejlinjer og adresser med lejligheder. Land og småbyer i samme postnummer medtages. Hver færdig vej gemmes; du kan sætte på pause og fortsætte senere.")}</p><div class="actions"><button class="primary" ${this.busy?'disabled':''}>${ui("Hent / fortsæt postnummer")}</button></div></fieldset></form>${this.postcodeList()}<details><summary>${ui("Hent én vej")}</summary><form id="geoRoadForm"><fieldset><label>${ui("Postnummer")}</label><input name="postcode" value="${esc(this.rangePost)}" pattern="[0-9]{4}" maxlength="4" ${I18n.attribute('placeholder',"Postnummer")} required><label>${ui("Vejnavn")}</label>${RoadSearch.field('geoDownloadRoad',this.rangeRoad)}<label class="check"><input type="checkbox" data-online-search ${RoadSearch.online?'checked':''}> ${ui("Online vejforslag fra DAR")}</label><p class="hint">${ui("Kun søgeteksten og postnummeret sendes til DAR. Kortvalg, IB og forkyndere bliver på dit lokale system.")}</p><label class="check"><input name="include_osm" type="checkbox" checked> ${ui("Hent også veje, bygninger, vandløb og jernbaner omkring adressen")}</label><div class="actions"><button ${this.busy?'disabled':''}>${ui("Hent vej")}</button></div></fieldset></form></details><details><summary>${ui("Hent veje, bygninger, vandløb og jernbaner i det viste udsnit")}</summary><form id="geoAreaForm"><fieldset><label class="check"><input name="addresses" type="checkbox" disabled> ${ui("Hent også DAR-adresser i udsnittet")}</label><div id="geoAreaPostcodeField" hidden><label for="geoAreaPostcode">${ui("Postnummer · til adresser fra den ældre kilde")}</label><input id="geoAreaPostcode" name="postcode" value="${esc(this.rangePost)}" pattern="[0-9]{4}" maxlength="4" disabled></div><p class="hint" id="geoAreaSourceHint">${ui("Kortdata fra OpenStreetMap kræver intet postnummer. Kontrollerer adressekilden…")}</p><p class="hint">${ui("Zoom ind på et mindre område. Med Datafordeleren hentes alle postnumre i udsnittet; adresser afhænger ikke af OSM-vejnavne. Kortbaggrunden gemmes separat.")}</p><button ${this.busy||!this.map?'disabled':''}>${ui("Hent vist udsnit")}</button>${!this.map?`<p class="hint">${ui("Åbn kortet, og vælg et udsnit først.")}</p><button type="button" data-geo="open-map">${ui("Åbn kortet")}</button>`:''}</fieldset></form></details><details><summary>${ui("Importer en adresseliste")}</summary><label>CSV / GeoJSON <input id="geoImport" type="file" accept=".csv,.json,.geojson"></label></details><p id="addressSourceStatus" role="status">${ui("Henter lokal status…")}</p><p><button type="button" data-work="connections">${ui("Administrer adresseforbindelsen")}</button></p>${AddressSourceUI.tokenHTML(!!this.data.info?.token_custom)}<div class="actions"><button data-action="close">${ui("Luk")}</button></div>`);AddressSourceUI.load();
  },
  async download(kind,data){if(this.busy)throw Error(I18n.text('Vent på den aktuelle hentning.'));const generation=openDialog.generation,origin=page;this.jobNoticeEpoch=this.noticeEpoch;this.busy=true;try{const result=await(await api('/api/geo/download',{kind,data})).json();this.job=result.job_id;if(generation===openDialog.generation&&page===origin)closeDialog();this.showJob({status:'running',message:'Henter offentlige data…'});this.poll();}catch(error){this.busy=false;throw error;}},
  showJob(job){let node=el('geoDownloadStatus');if(!node){node=document.createElement('div');node.id='geoDownloadStatus';node.className='geoDownloadStatus';document.body.appendChild(node);}const running=job.status==='running',activity=job.retry_delay!==undefined?ui('Venter på forbindelsen · prøver igen…'):esc(I18n.errorText(running&&job.activity?job.activity:job.message)),count=Number.isInteger(job.received_count)?ui(job.kind==='road'&&typeof StreetSuggestions!=='undefined'&&StreetSuggestions.pending?'{count} adresser modtaget fra hele vejen (før nummerfilteret)':'{count} adresser modtaget',{count:job.received_count}):'',waiting=running&&job.waiting?ui('Venter på svar fra adressekilden…'):'';node.innerHTML=`<span>${activity}${count?' · '+count:''}${waiting?' · '+waiting:''}</span>${running&&['postcode','boundary'].includes(job.kind)?`<button data-geo="pause">${ui("Sæt på pause")}</button>`:''}`;node.hidden=job.status!=='running'&&this.jobNoticeEpoch!==this.noticeEpoch;},
  async poll(){try{
    const job=await(await api('/api/geo/job?id='+encodeURIComponent(this.job))).json();this.showJob(job);
    if(job.status==='running'){this.jobTimer=setTimeout(()=>this.poll(),1200);return;}
    this.busy=false;await this.load();if(page==='Kortopsætning'){state=await(await api('/api/state')).json();this.drawLayers();this.drawBoundary();this.updatePanel();}else await refresh();
    if(job.status==='done'){
      const priorNotice=this.notice,priorNoticeUI=this.noticeUI;
      this.rangeRoad=job.result.road||this.rangeRoad;this.rangePost=job.result.postcode||this.rangePost;
      this.notice=job.result.note|| (job.result.road?'Adresserne er hentet. Vælg huse eller et nummerinterval.':'Kortdata gemt lokalt.');
      if(job.kind==='boundary'&&job.result.complete&&Number.isInteger(job.result.fetched_count))this.notice=I18n.format('{fetched} DAR-adresser fundet indenfor grænsen · {local} lokale aktive adresser. Kontrollér eventuelle adresseændringer.',{fetched:job.result.fetched_count,local:job.result.count});
      if(job.result.empty)this.notice=I18n.text('Ingen adresser fundet indenfor den gemte grænse. Kontrollér grænsen, og prøv en enkelt vej. En kontrolleret forbindelse er ikke en bekræftet adressehentning.');
      if(job.result.warnings?.length&&!job.result.empty)this.notice+=' '+job.result.warnings.length+' udsnit/opslag mangler. Se fejl og fortsæt under '+(job.kind==='boundary'?'Samlet distriktsgrænse.':'Kortdata.');
      if(this.jobNoticeEpoch!==this.noticeEpoch){this.notice=priorNotice;this.noticeUI=priorNoticeUI;}
      if(page==='Kortopsætning')this.updatePanel();else render();
      if(job.result.bbox&&this.map){const[w,s,e,n]=job.result.bbox;this.map.fitBounds([[s,w],[n,e]],{padding:[30,30],maxZoom:18});}
      if(typeof StreetSuggestions!=='undefined'&&StreetSuggestions.pending){await StreetSuggestions.afterJob(job);return;}
      if(this.pendingRange){const range=this.pendingRange;this.pendingRange=null;if(range.stamp===this.draftStamp(false))await this.selectPreview({mode:'range',...range.data});}
      this.showJob({...job,message:this.notice,total:0});
    }else{
      let message=job.message;
      if(typeof StreetSuggestions!=='undefined'&&StreetSuggestions.pending&&job.kind==='road'){
       message=StreetSuggestions.failureMessage(job.message);
       StreetSuggestions.pending=null;
      }else if(typeof StreetSuggestions!=='undefined')StreetSuggestions.pending=null;
      this.pendingRange=null;if(this.jobNoticeEpoch===this.noticeEpoch){this.notice=message;this.noticeUI=null;}this.updatePanel();this.showJob({...job,message});
    }
    // Keep failures visible until the user retries or leaves; 12 seconds is
    // not enough to read and locate a problem among many street lines.
    if(job.status==='done'&&!job.result?.warnings?.length)setTimeout(()=>{const n=el('geoDownloadStatus');if(n)n.hidden=true;},12000);
  }catch(e){
    const message=typeof StreetSuggestions!=='undefined'&&StreetSuggestions.pending?StreetSuggestions.failureMessage(e.message):e.message;
    if(typeof StreetSuggestions!=='undefined')StreetSuggestions.pending=null;
    this.busy=false;this.pendingRange=null;if(this.jobNoticeEpoch===this.noticeEpoch){this.notice=message;this.noticeUI=null;}this.showJob({message,status:'error'});
  }},
  boundsForDownload(){if(!this.map)throw Error(I18n.text('Åbn Kortopsætning, og vælg et kortudsnit først.'));return this.map.getBounds();},
  async confirmIgnore(id,reason){const stamp=this.draftStamp(false);await mutate('ignore.save',{address_id:id,reason});if(stamp!==this.draftStamp(false))return;if(this.ids.delete(id))this.dirty=true;render();},
  async autoAll(){
    if(this.bulkAutoBusy||this.dirty||this.saveBusy||this.busy)return;
    if(typeof ProfilesUI!=='undefined'&&!ProfilesUI.canAction('geo.assign'))throw Error(I18n.text('Du har ikke rettighed til denne handling.'));
    const cards=state.cards.filter(c=>!c.archived&&c.geo_polygon?.length>=3).sort((a,b)=>cmp(a.number,b.number));
    if(!cards.length)return;
    if(!window.confirm(I18n.format('Find adresser inden for grænsen på {count} kort? Vejlisterne opdateres, men gemte adressevalg, IB og historik beholdes. Kort uden entydige nye adresser springes over.',{count:cards.length})))return;
    const origin=page,session=this.session;
    this.bulkAutoBusy=true;this.bulkAutoProgress={done:0,total:cards.length};
    let updated=0,skipped=0;
    const expected=c=>({polygon:c.geo_polygon,address_ids:c.address_ids||[],addresses:c.addresses||[]});
    const active=()=>page===origin&&this.session===session&&!this.dirty;
    try{
      render();
      for(const original of cards){
        if(!active())break;
        const current=card(original.id);
        if(!current||JSON.stringify(expected(current))!==JSON.stringify(expected(original)))break;
        const preview=await this.preview({mode:'polygon',polygon:current.geo_polygon},current.id);
        if(!active()||!card(current.id)||JSON.stringify(expected(card(current.id)))!==JSON.stringify(expected(current)))break;
        const blocked=new Set([...preview.ignored,...(preview.retired||[]),...preview.conflicts.map(c=>c.id)]);
        const old=new Set(current.address_ids||[]);
        // Never give a new address in two boundaries to whichever card happens to run first.
        const neighbors=cards.filter(c=>c.id!==current.id);
        const additions=preview.addresses.filter(a=>!blocked.has(a.id)&&!old.has(a.id)&&!neighbors.some(c=>this.pointInside([a.lng,a.lat],c.geo_polygon))).map(a=>a.id);
        if(!additions.length){skipped++;}
        else{
          const stamp=this.draftStamp(false);
          await mutate('geo.assign',{card_id:current.id,address_ids:[...old,...additions],polygon:current.geo_polygon,auto_expected:expected(current)},{close:false,autosave:true,synchronize:(_response,snapshot)=>this.syncWrite(stamp,()=>{if(this.target===current.id){const saved=card(current.id);this.ids=new Set(saved.address_ids||[]);this.polygon=saved.geo_polygon.map(p=>p.slice());this.suggestedOutline=null;this.streetApproval=null;}},undefined,snapshot)});
          updated++;
        }
        this.bulkAutoProgress.done++;
        if(active())render();
      }
    }finally{
      const done=this.bulkAutoProgress.done;
      this.bulkAutoBusy=false;this.bulkAutoProgress=null;
      if(active()){this.setNotice('{updated} kort opdateret · {skipped} sprunget over · {remaining} ikke behandlet.',{updated,skipped,remaining:cards.length-done});render();}
    }
  },
  async handle(action,id){
    if(this.bulkAutoBusy)return;
    switch(action){
      case 'street-lines':StreetSuggestions.open();break;
      case 'imported-points':await this.selectPreview({mode:'imported_points'});break;
      case 'data':case 'road':{const f=el('geoRangeForm');if(f){this.rangeRoad=f.elements.road.value;this.rangePost=f.elements.postcode.value;}this.dataDialog();break;}
      case 'open-map':if(!this.canLeave())return;closeDialog();page='Kortopsætning';render();break;
      case 'pause':await api('/api/geo/pause',{job_id:this.job});break;
      case 'refresh-postcode':this.rangePost=id;await this.download('postcode',{postcode:id,refresh:true});break;
      case 'resume-postcode':{this.rangePost=id;const p=this.data.info.postcodes.find(p=>p.postcode===id);if(p?.status==='complete'){closeDialog();page='Adresser';addressTab='Mangler på kort';addressPostcode=id;query='';render();}else await this.download('postcode',{postcode:id});break;}
      case 'choose':case 'draw':case 'move':case 'insert':case 'erase':this.clearStaleFeedback();this.mode=action;if(action==='draw'&&this.polygon.length&&window.confirm(I18n.text('Vil du begynde en ny grænse? Vælg Annuller for at tilføje hjørner til den eksisterende.'))){this.polygon=[];this.dirty=true;}this.drawBoundary();this.updatePanel();break;
      case 'undo':this.clearStaleFeedback();this.polygon.pop();this.dirty=true;this.drawBoundary();this.updatePanel();break;
      case 'suggest-outline':await this.selectPreview({address_ids:[...this.ids],suggest_outline:true});break;
      case 'auto-all':await this.autoAll();break;
      case 'auto':if(this.polygon.length<3)throw Error(I18n.text('Tegn mindst tre hjørner først.'));await this.selectPreview({mode:'polygon',polygon:this.polygon});break;
      case 'clear':this.clearStaleFeedback();this.ids.clear();this.dirty=true;this.drawLayers();this.updatePanel();break;
      case 'remove':this.clearStaleFeedback();this.ids.delete(id);this.dirty=true;this.drawLayers();this.updatePanel();break;
      case 'focus':{const a=this.addresses().find(a=>a.id===id);if(a){this.focus=[id];this.map.setView([a.lat,a.lng],19);this.updatePanel();}break;}
      case 'save':{const notice=this.outlineApproval()&&this.outlineNotice({outline_status:this.suggestedOutline.status,outline_reason:this.suggestedOutline.reason,outline_reason_number:this.suggestedOutline.reasonNumber});if(this.target){const c=card(this.target);openDialog(`<h2>${ui('Gem adressevalget på kort {number}?',{number:c.number})}</h2><p>${ui('Vejlisten erstattes af {count} valgte adresser. Udlån og historik følger samme kort. IB-listen beholdes.',{count:this.chosen().length})}</p>${notice?`<p class="notice warning">${ui(notice)}</p>`:''}${this.neighborConsent()}<div class="actions"><button class="primary" data-geo="confirm-save" ${this.neighborChanges().length?'disabled':''}>${ui("Gem kort og vejliste")}</button><button data-action="close">${ui("Annuller")}</button></div>`);}else openDialog(`<h2>${ui("Opret kort fra adressevalget")}</h2><form id="geoNewCardForm">${this.neighborConsent()}${notice?`<p class="notice warning">${ui(notice)}</p>`:''}<label>${ui("Kortnummer")}</label><input name="number" required maxlength="30" autofocus><label>${ui("Område")}</label><select name="area_id">${areaOptions('')}</select><label>${ui("Distriktstype")}</label><select name="kind"><option value="Ukendt" data-ui="Ukendt">${esc(I18n.text("Ukendt"))}</option><option value="By" data-ui="By">${esc(I18n.text("By"))}</option><option value="Land" data-ui="Land">${esc(I18n.text("Land"))}</option></select><label>${ui("Navn · valgfrit")}</label><input name="name" maxlength="100"><label class="check"><input type="checkbox" name="planned" ${this.ids.size?'':'checked disabled'}> ${ui('Distriktskort under opbygning')}</label><p class="hint">${ui('Kortet kan tegnes og redigeres, mens det er under opbygning. Fjern markeringen, når det kan udleveres.')}</p>${formEnd('Opret kort')}</form>`);break;}
      case 'confirm-save':await this.save();break;
      case 'import-boundary':BoundaryImportUI.open(false);break;
      case 'boundary':await this.saveBoundary();break;
      case 'show-address':{const a=this.addresses().find(a=>a.id===id);if(!a)throw Error(I18n.text('Adressen findes ikke.'));if(!this.canLeave())return;this.session++;this.whole=false;this.mode='choose';this.streetApproval=null;this.suggestedOutline=null;this.target=this.data.status?.[id]?.card_id||'';const c=card(this.target);this.ids=new Set(c?.address_ids||[]);this.polygon=(c?.geo_polygon||[]).map(p=>p.slice());this.dirty=false;this.focus=[id];this.view={center:[a.lat,a.lng],zoom:19};closeDialog();page='Kortopsætning';render();break;}
      case 'assign-address':{const a=this.addresses().find(a=>a.id===id);if(!a)throw Error(I18n.text('Adressen findes ikke.'));openDialog(`<h2>${ui("Tilføj til distriktskort")}</h2><p>${esc(a.label)}</p><form id="geoAssignAddressForm" data-id="${esc(id)}"><label>${ui("Distriktskort")}</label><select name="card_id" required><option value="" data-ui="Vælg kort">${esc(I18n.text("Vælg kort"))}</option>${state.cards.slice().sort((a,b)=>cmp(a.number,b.number)).map(c=>`<option value="${c.id}">${esc(c.number)} · ${esc(areaName(c.area_id))}</option>`).join('')}</select><p class="hint">${ui("Adressen og kortets øvrige gemte adresser åbnes i korteditoren. Kontrollér valget og gem kortet.")}</p>${formEnd('Åbn adressevalg')}</form>`);break;}
      case 'manual':this.manualDialog();break;
      case 'export-map':await MapExport.png(id);break;
      case 'export-map-osm':await MapExport.png(id,'osm');break;
      case 'type':{const a=this.addresses().find(a=>a.id===id);openDialog(`<h2>${ui("Adressetype")}</h2><p>${esc(a.label)}</p><form id="geoTypeForm" data-id="${esc(id)}"><select name="type">${addressTypes.map(t=>`<option value="${esc(t)}" data-ui="${esc(t)}" ${a.type===t?'selected':''}>${esc(I18n.text(t))}</option>`).join('')}</select><p class="hint">${ui("Gem adressevalget på kortet igen for at opdatere vejlisten og dens type.")}</p>${formEnd()}</form>`);break;}
      case 'address-tracking':{
        const a=this.addresses().find(a=>a.id===id);
        if(!a)throw Error(I18n.text('Adressen findes ikke.'));
        const current=this.addressTracking(id);
        openDialog(`<h2>${ui('Markér adresse')}</h2><p>${esc(a.label)}</p><form id="geoTrackingForm" data-id="${esc(id)}"><label for="geoTrackingStatus">${ui('Markering')}</label><select name="status" id="geoTrackingStatus">${[['','Ingen markering'],['construction','Under opbygning'],['other','Andet']].map(([value,label])=>`<option value="${value}" ${current===value?'selected':''}>${esc(I18n.text(label))}</option>`).join('')}</select>${formEnd()}</form>`,I18n.language());
        break;
      }
      case 'ignore':{const a=this.addresses().find(a=>a.id===id);if(!a)throw Error(I18n.text('Adressen findes ikke længere.'));openDialog(`<h2>${ui("Se bort fra adressen")}</h2><p>${esc(a.label)}</p><form id="geoIgnoreForm" data-id="${esc(id)}"><label>${ui("Begrundelse")}</label><input name="reason" required maxlength="200" ${I18n.attribute('placeholder',"Fx transformerstation")}>${formEnd('Gem Se bort fra')}</form>`);break;}
    }
  },
  manualDialog(){const center=this.manualPoint||this.map?.getCenter()||{lng:10,lat:56};openDialog(`<h2>${ui("Tilføj en lokal adresse")}</h2><form id="geoManualForm"><label>${ui("Vejnavn")}</label><input name="road" required maxlength="120"><div class="twocol"><div><label>${ui("Husnummer")}</label><input name="number" required maxlength="30"></div><div><label>${ui("Postnummer")}</label><input name="postcode" pattern="[0-9]{4}" required maxlength="4"></div><div><label>${ui("Etage · valgfrit")}</label><input name="floor" maxlength="20"></div><div><label>${ui("Dør · valgfrit")}</label><input name="door" maxlength="30"></div><div><label>${ui("Længdegrad")}</label><input name="lng" type="number" step="0.0000001" value="${center.lng.toFixed(7)}" required></div><div><label>${ui("Breddegrad")}</label><input name="lat" type="number" step="0.0000001" value="${center.lat.toFixed(7)}" required></div></div><p class="hint">${ui("Placeringen er dit seneste klik på kortet eller kortets centrum, hvis du endnu ikke har klikket. Kontrollér koordinaterne. Tilføj én række pr. lejlighed, eller angiv et manuelt samlet besøgsantal.")}</p><div class="twocol"><div><label>${ui("Besøg")}</label><input name="count" type="number" min="1" max="10000" value="1" required></div><div><label>${ui("Type")}</label><select name="type">${addressTypes.map(t=>`<option value="${esc(t)}" data-ui="${esc(t)}">${esc(I18n.text(t))}</option>`).join('')}</select></div></div>${formEnd('Tilføj adresse')}</form>`);},
  reportMap(done,cards){
    const mapped=cards.filter(c=>c.geo_polygon?.length>=3);if(!mapped.length)return '';
    const project=p=>[p[0]*Math.PI/180,Math.log(Math.tan(Math.PI/4+p[1]*Math.PI/360))];const points=mapped.flatMap(c=>c.geo_polygon).map(project),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);let minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),pad=Math.max(maxX-minX,maxY-minY)*.06||.00002;minX-=pad;maxX+=pad;minY-=pad;maxY+=pad;const scale=Math.min(1000/(maxX-minX),650/(maxY-minY)),xoff=(1000-(maxX-minX)*scale)/2,yoff=(650-(maxY-minY)*scale)/2,to=p=>{const[x,y]=project(p);return [(x-minX)*scale+xoff,(maxY-y)*scale+yoff];},path=poly=>poly.map(p=>to(p).map(n=>n.toFixed(1)).join(',')).join(' '),visible=poly=>poly.some(p=>{const[x,y]=project(p);return x>=minX&&x<=maxX&&y>=minY&&y<=maxY;});
    return `<div class="mapframe"><svg viewBox="0 0 1000 680" role="img" ${I18n.attribute('aria',"Gennemgåede distrikter på geografisk kort")}><rect width="1000" height="680" fill="#f2f4f2"/>${this.data.roads.filter(r=>visible(r.points)).map(r=>`<polyline points="${path(r.points)}" fill="none" stroke="#c5ced1" stroke-width="3"/>`).join('')}${this.data.buildings.filter(b=>visible(b.points)).map(b=>`<polygon points="${path(b.points)}" fill="#d8ddda" stroke="#b6c2bc" stroke-width=".6"/>`).join('')}${mapped.map(c=>{const poly=c.geo_polygon.map(to),x=poly.reduce((n,p)=>n+p[0],0)/poly.length,y=poly.reduce((n,p)=>n+p[1],0)/poly.length;return `<g data-action="detail" data-id="${c.id}"><polygon points="${path(c.geo_polygon)}" fill="${done.has(c.id)?'#52aa82':cardColor(c)}" fill-opacity="${done.has(c.id)?'.55':'.15'}" stroke="${done.has(c.id)?'#187149':cardColor(c)}" stroke-width="2.5"/><text x="${x}" y="${y}" text-anchor="middle" font-size="18" font-weight="bold" fill="#183746" stroke="white" stroke-width="3" paint-order="stroke">${esc(c.number)}</text></g>`;}).join('')}<text x="12" y="670" fill="#637881" font-size="12" data-ui="Veje/bygninger © OpenStreetMap-bidragsydere · Adresser DAR / lokal import">${esc(I18n.text("Veje/bygninger © OpenStreetMap-bidragsydere · Adresser DAR / lokal import"))}</text></svg></div><p class="hint">${ui('{count} kort har endnu ingen geografisk grænse. Kortet viser den aktuelle grænse for de øvrige.',{count:cards.length-mapped.length})}</p>`;
  }
};
document.addEventListener('click',async e=>{const target=e.target.closest('[data-geo]');if(!target)return;e.preventDefault();try{await GeoUI.handle(target.dataset.geo,target.dataset.id);}catch(error){toast(error);failed(error);}});
document.addEventListener('change',async e=>{try{if(e.target.id==='geoColor'){const previous=GeoUI.drawColor,requested=e.target.value,originTarget=GeoUI.target,session=GeoUI.session;GeoUI.drawColor=requested;GeoUI.drawBoundary();try{if(GeoUI.target)await mutate('card.color',{card_id:GeoUI.target,map_color:GeoUI.drawColor},{close:false,message:'Kortfarve gemt'});}catch(error){if(GeoUI.target===originTarget&&GeoUI.session===session&&GeoUI.drawColor===requested&&el('geoColor')===e.target){GeoUI.drawColor=previous;e.target.value=previous;GeoUI.drawBoundary();}throw error;}}else if(e.target.id==='geoNeighborApproval'){const button=el('dialog').querySelector('[data-geo=confirm-save]');if(button)button.disabled=!e.target.checked;}else if(e.target.id==='geoTarget'){if(!GeoUI.canLeave()){e.target.value=GeoUI.target;return;}GeoUI.dirty=false;GeoUI.openCard(e.target.value);}else if(e.target.dataset.geoCheck){GeoUI.clearStaleFeedback();const id=e.target.dataset.geoCheck;e.target.checked?GeoUI.ids.add(id):GeoUI.ids.delete(id);GeoUI.dirty=true;GeoUI.drawLayers();GeoUI.updatePanel();}else if(e.target.id==='geoImport'){const file=e.target.files[0];if(!file)return;if(file.size>12000000)throw Error(I18n.text('Filen må højst være 12 MB.'));const content=await file.text();await mutate('geo.import_file',{content,name:file.name},{message:'Adresser importeret lokalt'});await GeoUI.load();render();}}catch(error){toast(error);failed(error);}});
document.addEventListener('submit',async e=>{const f=e.target;if(!f.id.startsWith('geo'))return;e.preventDefault();if(!f.reportValidity()||f.dataset.geoSaving==='yes')return;f.dataset.geoSaving='yes';const button=f.querySelector('button:not([type=button])');if(button)button.disabled=true;const data=Object.fromEntries(new FormData(f));try{switch(f.id){case 'geoRangeForm':{const matches=[...new Set(GeoUI.addresses().filter(a=>a.postcode===data.postcode&&RoadSearch.normalize(a.road)===RoadSearch.normalize(data.road)).map(a=>a.road))];if(matches.length===1)data.road=matches[0];GeoUI.rangeRoad=data.road;GeoUI.rangePost=data.postcode;if(!matches.length){GeoUI.pendingRange={data,stamp:GeoUI.draftStamp(false)};try{await GeoUI.download('road',{road:data.road,postcode:data.postcode,include_osm:false});}catch(error){GeoUI.pendingRange=null;throw error;}}else{await GeoUI.selectPreview({mode:'range',...data});if(!GeoUI.ids.size)toast(I18n.text('Ingen hentede adresser i dette nummerinterval.'));}break;}case 'geoAssignAddressForm':{if(!GeoUI.canLeave())break;const addressId=f.dataset.id;closeDialog();GeoUI.dirty=false;GeoUI.openCard(data.card_id);GeoUI.ids.add(addressId);GeoUI.focus=[addressId];GeoUI.dirty=true;GeoUI.drawLayers();GeoUI.updatePanel();break;}case 'geoPostcodeForm':GeoUI.rangePost=data.postcode;await GeoUI.download('postcode',{postcode:data.postcode,refresh:new FormData(f).has('refresh')});break;case 'geoRoadForm':GeoUI.rangeRoad=data.road;GeoUI.rangePost=data.postcode;await GeoUI.download('road',{...data,include_osm:new FormData(f).has('include_osm')});break;case 'geoAreaForm':{const b=GeoUI.boundsForDownload();await GeoUI.download(new FormData(f).has('addresses')?'area':'osm',{postcode:data.postcode,bbox:[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()]});break;}case 'geoNewCardForm':await GeoUI.save(data.number,{...data,planned:!GeoUI.ids.size||data.planned==='on'});break;case 'geoTokenForm':await mutate('geo.token',data);break;case 'geoTypeForm':await mutate('geo.type',{id:f.dataset.id,type:data.type});await GeoUI.load();render();break;case 'geoIgnoreForm':await GeoUI.confirmIgnore(f.dataset.id,data.reason);break;case 'geoTrackingForm':await mutate('geo.address_tracking',{address_id:f.dataset.id,status:data.status});if(page==='Kortopsætning')GeoUI.updateAddressPanel();break;case 'geoManualForm':await mutate('geo.manual',{...data,lng:Number(data.lng),lat:Number(data.lat),count:Number(data.count)});await GeoUI.load();render();break;}}catch(error){toast(error);failed(error);}finally{delete f.dataset.geoSaving;if(button)button.disabled=false;}});
window.addEventListener('beforeunload',e=>{if(GeoUI.dirty){e.preventDefault();e.returnValue='';}});

document.addEventListener('change',e=>{if(e.target.name==='addresses'&&e.target.closest('#geoAreaForm'))GeoUI.areaPostcode();});
