'use strict';
// Generated locally from public navigation data. No IB, people or history.
const MapExport={
  boundsPoints(id){const c=card(id);return c?.geo_polygon?.length?c.geo_polygon:(c?.geo_addresses?.length?c.geo_addresses:GeoUI.addresses().filter(a=>c?.address_ids?.includes(a.id))).map(a=>[a.lng,a.lat]);},
  isIB(a,id){const clean=s=>String(s||'').toLowerCase().replace(/[\s.,]+/g,'');return (state.ib||[]).filter(i=>i.card_id===id).some(i=>i.address_id?i.address_id===a.id:RoadSearch.normalize(i.road)===RoadSearch.normalize(a.road)&&(clean(i.number)===clean(a.number)||clean(i.number)===clean([a.number,a.floor,a.door].filter(Boolean).join(' '))));},
  members(id){
    const c=card(id);if(!c)return [];
    const ignored=GeoUI.ignored(),retired=new Set(GeoUI.addresses().filter(a=>a.retired).map(a=>a.id));
    const members=c.geo_addresses?.length?c.geo_addresses:GeoUI.addresses().filter(a=>c.address_ids?.includes(a.id));
    return members.filter(a=>!ignored.has(a.id)&&!a.retired&&!retired.has(a.id)&&!this.isIB(a,id));
  },
  coversViewport(rectangles,width,height){
    const bands=[...new Set([0,height,...rectangles.flatMap(r=>[Math.max(0,r.y),Math.min(height,r.y+r.height)])])].filter(y=>y>=0&&y<=height).sort((a,b)=>a-b);
    for(let i=0;i<bands.length-1;i++){if(bands[i+1]-bands[i]<.01)continue;const y=(bands[i]+bands[i+1])/2,intervals=rectangles.filter(r=>r.y<=y&&r.y+r.height>=y).map(r=>[Math.max(0,r.x),Math.min(width,r.x+r.width)]).sort((a,b)=>a[0]-b[0]);let covered=0;for(const [left,right] of intervals){if(left>covered+.5)return false;covered=Math.max(covered,right);}if(covered<width-.5)return false;}return bands.length>1;
  },
  exportPoints(id,options={}){return options.publicCard?[...(options.publicCard.geo_polygon||[]),...options.publicMembers.map(a=>[a.lng,a.lat])]:[...this.boundsPoints(id),...this.members(id).map(a=>[a.lng,a.lat])];},
  osmEntry(id){const key=DistrictMap.map&&DistrictMap.id===id?'districtMap':GeoUI.map&&!GeoUI.whole&&GeoUI.target===id?'geographicEditor':'';return MapBackground.instances.get(key);},
  exportPadding(id,map){const size=map.getSize(),members=this.members(id),visits=members.reduce((n,a)=>n+(a.count||0),0),label=Math.max(0,...members.map(a=>String(a.number).length*12+20)),margin=Math.max(label,18+Math.sqrt(visits)*5);return Math.ceil(Math.max(20,margin*Math.min(size.x/1540,size.y/1310)));},
  async prepareOSM(id,options={}){
    const entry=this.osmEntry(id),map=entry?.map,points=this.exportPoints(id,options);
    if(!map||MapBackground.mode!=='road')throw Error('Åbn kortet, og vælg Vejkort · OpenStreetMap først.');
    if(!points.length)throw Error('Gem kortets grænse eller adresser først.');
    if(DistrictMap.id===id&&DistrictMap.map===map){DistrictMap.road='';if(el('districtMapRoad'))el('districtMapRoad').value='';DistrictMap.draw(false);}
    const padding=this.exportPadding(id,map)+4;
    map.fitBounds(points.map(p=>[p[1],p[0]]),{padding:[padding,padding],maxZoom:19,animate:false});
    toast('Tilpasser kortet til distriktet og venter på vejkortet…');
    const deadline=Date.now()+20000;
    await new Promise(resolve=>setTimeout(resolve,200));
    while(entry.layer?.isLoading()||map._animatingZoom||map._panAnim?._inProgress){
      if(this.osmEntry(id)!==entry)throw Error('Kortvisningen er ændret. Åbn kortet og prøv igen.');
      if(Date.now()>=deadline)throw Error('Vejkortet er stadig ved at indlæse. Kontrollér forbindelsen og prøv igen.');
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    if(this.osmEntry(id)!==entry)throw Error('Kortvisningen er ændret. Åbn kortet og prøv igen.');
  },
  tightCrop(id,map,size,options={}){
    const points=this.exportPoints(id,options).map(p=>map.latLngToContainerPoint([p[1],p[0]]));
    const padding=this.exportPadding(id,map);
    const x=Math.floor(Math.min(...points.map(p=>p.x))-padding),y=Math.floor(Math.min(...points.map(p=>p.y))-padding);
    const right=Math.ceil(Math.max(...points.map(p=>p.x))+padding),bottom=Math.ceil(Math.max(...points.map(p=>p.y))+padding);
    if(x<0||y<0||right>size.x||bottom>size.y)throw Error('Hele distriktet er ikke synligt. Prøv at eksportere igen.');
    return {x,y,width:Math.max(1,right-x),height:Math.max(1,bottom-y)};
  },
  osmSnapshot(id,{tight=false,...options}={}){
    const mapId=DistrictMap.map&&DistrictMap.id===id?'districtMap':GeoUI.map&&!GeoUI.whole&&GeoUI.target===id?'geographicEditor':'';
    const entry=MapBackground.instances.get(mapId),map=entry?.map;
    if(!map||MapBackground.mode!=='road')throw Error('Åbn kortet, og vælg Vejkort · OpenStreetMap først.');
    return this.captureMap(map,entry.layer,tight?this.tightCrop(id,map,map.getSize(),options):null);
  },
  captureMap(map,layer,crop=null){
    if(layer?.isLoading()||map._animatingZoom||map._panAnim?._inProgress)throw Error('Vent, til kortet er færdigt med at indlæse og flytte, og prøv igen.');
    const node=map.getContainer(),size=map.getSize(),origin=node.getBoundingClientRect();
    if(!size.x||!size.y||size.x>4000||size.y>4000)throw Error('Kortvisningen er skjult eller for stor. Åbn kortet i normal størrelse.');
    const currentLevel=layer?._levels?.[layer._tileZoom]?.el;
    const tiles=[...(currentLevel||node).querySelectorAll(currentLevel?'img.leaflet-tile':'.leaflet-tile-pane img.leaflet-tile')].map(image=>{const r=image.getBoundingClientRect();return {image,x:r.left-origin.left,y:r.top-origin.top,width:r.width,height:r.height};}).filter(r=>r.width>0&&r.height>0&&r.x<size.x&&r.y<size.y&&r.x+r.width>0&&r.y+r.height>0);
    if(!tiles.length||tiles.some(t=>!t.image.complete||!t.image.naturalWidth)||!this.coversViewport(tiles,size.x,size.y))throw Error('Vejkortet er ikke helt indlæst. Vent eller kontrollér internetforbindelsen, og prøv igen.');
    crop=crop||{x:0,y:0,width:size.x,height:size.y};
    const canvas=document.createElement('canvas');canvas.width=crop.width;canvas.height=crop.height;const ctx=canvas.getContext('2d');if(!ctx)throw Error('Browseren understøtter ikke billedeksport.');
    try{for(const t of tiles)ctx.drawImage(t.image,t.x-crop.x,t.y-crop.y,t.width,t.height);const bounds=(crop.x||crop.y||crop.width!==size.x||crop.height!==size.y)?(()=>{const sw=map.containerPointToLatLng([crop.x,crop.y+crop.height]),ne=map.containerPointToLatLng([crop.x+crop.width,crop.y]);return {getWest:()=>sw.lng,getSouth:()=>sw.lat,getEast:()=>ne.lng,getNorth:()=>ne.lat};})():map.getBounds();return {backgroundImage:canvas.toDataURL('image/png'),viewBounds:[bounds.getWest(),bounds.getSouth(),bounds.getEast(),bounds.getNorth()]};}
    catch{throw Error('Browseren kunne ikke gemme vejkortet. Genindlæs appen, vælg Vejkort, og prøv igen.');}
  },
  svg(id,{backgroundImage='',viewBounds=null,publicCard=null,publicMembers=null,publicTemplate=''}={}){
    const c=publicCard||card(id);if(!c)throw Error('Kortet findes ikke.');
    const members=publicMembers||this.members(id);
    const boundaryPoints=publicCard?(publicCard.geo_polygon?.length?publicCard.geo_polygon:members.map(a=>[a.lng,a.lat])):this.boundsPoints(id);if(!boundaryPoints.length)throw Error('Gem et adressevalg på kortet først.');
    const project=p=>[p[0]*Math.PI/180,Math.log(Math.tan(Math.PI/4+p[1]*Math.PI/360))];
    const coords=[...boundaryPoints,...members.map(a=>[a.lng,a.lat])].map(project),xs=coords.map(p=>p[0]),ys=coords.map(p=>p[1]);
    let w=Math.min(...xs),s=Math.min(...ys),e=Math.max(...xs),n=Math.max(...ys);
    if(viewBounds){const lower=project([viewBounds[0],viewBounds[1]]),upper=project([viewBounds[2],viewBounds[3]]);[w,s]=lower;[e,n]=upper;if(!(e>w&&n>s))throw Error('Ugyldigt kortudsnit.');}
    else{const visits=members.reduce((sum,a)=>sum+(a.count||0),0),margin=Math.max(.035,(18+Math.sqrt(visits)*5)/1250);const padding=Math.max(e-w,n-s)*margin||.00002;w-=padding;s-=padding;e+=padding;n+=padding;}
    const scale=Math.min(1540/(e-w),1310/(n-s)),xoff=40+(1540-(e-w)*scale)/2,yoff=120+(1310-(n-s)*scale)/2;
    const to=p=>{const[x,y]=project(p);return [(x-w)*scale+xoff,(n-y)*scale+yoff];},path=p=>p.map(p=>to(p).map(x=>x.toFixed(1)).join(',')).join(' ');
    const visible=poly=>{const p=poly.map(project);return Math.min(...p.map(p=>p[0]))<=e&&Math.max(...p.map(p=>p[0]))>=w&&Math.min(...p.map(p=>p[1]))<=n&&Math.max(...p.map(p=>p[1]))>=s;};
    const groups=new Map();for(const a of members){const k=[a.postcode,a.road,a.number].join('|');if(!groups.has(k))groups.set(k,[]);groups.get(k).push(a);}
    const houses=[...groups.values()].sort((a,b)=>cmp(a[0].road,b[0].road)||cmp(a[0].number,b[0].number));
    const streets=new Map();for(const g of houses){const r=g[0].road;if(!streets.has(r))streets.set(r,[]);streets.get(r).push(g);}
    const labels=[];let line=0;
    for(const [road,groups] of streets){
      const numbers=groups.map(g=>g[0].number).sort(cmp),count=groups.flat().reduce((sum,a)=>sum+a.count,0),y=180+line*96;
      if(y>1350){labels.push(`<text x="1650" y="1410" font-size="22">Yderligere ${streets.size-line} veje på kortet</text>`);break;}
      const parts=road.length>30?[road.slice(0,30),road.slice(30)]:[road];
      labels.push(`<text x="1650" y="${y}" font-size="27" font-weight="bold">${parts.map((p,i)=>`<tspan x="1650" dy="${i?28:0}">${esc(p)}</tspan>`).join('')}</text><text x="1650" y="${y+(parts.length>1?54:35)}" font-size="22" fill="#647786">${esc(numbers[0])}${numbers.length>1?'-'+esc(numbers[numbers.length-1]):''} · ${count} besøg</text>`);line++;
    }
    const name=String(c.name||(!publicCard&&c.area_id?areaName(c.area_id):'')||''),nameSize=Math.max(16,Math.min(28,1450/Math.max(1,name.length*.6)));
    const total=members.reduce((sum,a)=>sum+a.count,0);
    const points=houses.map(g=>{const[x,y]=to([g[0].lng,g[0].lat]),count=g.reduce((sum,a)=>sum+a.count,0);return Array.from({length:count},(_,j)=>{const angle=j*2.39996,r=count>1?Math.sqrt(j)*5:0;return `<circle cx="${(x+Math.cos(angle)*r).toFixed(1)}" cy="${(y+Math.sin(angle)*r).toFixed(1)}" r="5" fill="#ca4c43" stroke="white" stroke-width="1.5"/>`;}).join('')+`<text x="${(x+11).toFixed(1)}" y="${(y-9).toFixed(1)}" font-size="20" font-weight="bold" fill="#873f39" stroke="white" stroke-width="4" paint-order="stroke">${esc(g[0].number)}</text>`;}).join('');
    const mapMarkup=`${backgroundImage?`<image href="${esc(backgroundImage)}" x="${xoff}" y="${yoff}" width="${(e-w)*scale}" height="${(n-s)*scale}"/>`:''}${(backgroundImage?[]:GeoUI.data.roads).filter(r=>visible(r.points)).map(r=>`<polyline points="${path(r.points)}" fill="none" stroke="#bbc5ca" stroke-width="7" stroke-linecap="round"/>`).join('')}${(backgroundImage?[]:GeoUI.data.buildings).filter(b=>visible(b.points)).map(b=>`<polygon points="${path(b.points)}" fill="#d1d8d1" stroke="#a7b5ae" stroke-width="1.5"/>`).join('')}<polygon points="${path(c.geo_polygon||[])}" fill="${cardColor(c)}" fill-opacity=".08" stroke="${cardColor(c)}" stroke-width="4" stroke-dasharray="12 7"/>${points}`;
    if(publicCard)return this.digitalSvg(c,members,houses,mapMarkup,publicTemplate,backgroundImage);
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2200" height="1560" viewBox="0 0 2200 1560"><defs><clipPath id="mapClip"><rect x="40" y="120" width="1540" height="1310" rx="18"/></clipPath></defs><rect width="2200" height="1560" fill="#fff"/><g font-family="Arial, sans-serif"><text x="42" y="69" font-size="43" font-weight="bold" fill="#263d4e">Distriktskort ${esc(c.number)}</text><text x="42" y="105" font-size="${nameSize}" fill="#263d4e">${esc(name)}</text><text x="2140" y="69" text-anchor="end" font-size="25" fill="#647786">${backgroundImage?'Kortudsnit · ':''}${total} besøg · ${houses.length} ${houses.length===1?'husnummer':'husnumre'}</text><rect x="40" y="120" width="1540" height="1310" rx="18" fill="#edf1ed"/><g clip-path="url(#mapClip)">${mapMarkup}</g><text x="1650" y="132" font-size="22" fill="#a74940">Rød prik = ét besøg</text>${labels.join('')}<rect x="40" y="1445" width="2118" height="40" rx="6" fill="#fff1ef"/><text x="56" y="1474" font-size="28" font-weight="bold" fill="#b3261e">Husk at tjekke efter IB på det fysiske distriktskort</text><text x="42" y="1505" font-size="20" fill="#647786">${backgroundImage?'Kort: © OpenStreetMap-bidragsydere · openstreetmap.org/copyright · Adresser: DAR':'Adresser / vejlinjer: DAR · øvrige veje / bygninger: © OpenStreetMap-bidragsydere, ODbL'}</text><text x="2140" y="1505" text-anchor="end" font-size="20" fill="#647786">${fmt(state.today)}</text></g></svg>`;
  },
  async frontTemplate(){
    if(!this.templatePromise)this.templatePromise=(async()=>{
      const response=await fetch('/s12-template.png');if(!response.ok)throw Error('Kortets blanke printforside kunne ikke hentes. Prøv igen.');
      const blob=await response.blob(),data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error('Printforsiden kunne ikke læses.'));reader.readAsDataURL(blob);});
      await new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>image.naturalWidth&&image.naturalHeight?resolve():reject(Error('Den blanke printforside er beskadiget.'));image.onerror=()=>reject(Error('Den blanke printforside er beskadiget.'));image.src=data;});return data;
    })().catch(error=>{this.templatePromise=null;throw error;});
    return this.templatePromise;
  },
  publicFront(c,members,template){
    if(!/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(template))throw Error('Den blanke printforside mangler. Dan kortbilledet igen.');
    const groups=new Map();for(const a of members){if(!groups.has(a.road))groups.set(a.road,[]);groups.get(a.road).push(a);}
    const addresses=[...groups].sort((a,b)=>cmp(a[0],b[0])).map(([road,rows])=>({road,numbers:[...new Set(rows.map(a=>a.number))].sort(cmp).join(', '),count:rows.reduce((n,a)=>n+a.count,0)}));
    // Share the physical front's row formatter, never its private card object.
    const rows=frontRows({addresses}),total=members.reduce((n,a)=>n+a.count,0),step=Math.min(6.65,42/(rows.length+1)),font=Math.min(3.175,step*.58);
    const texts=rows.map((r,i)=>`<text x="10.22" y="${32+i*step}" font-size="${Math.min(font,103/Math.max(1,r.label.length))}" textLength="${Math.min(103,r.label.length*font*.52)}" lengthAdjust="spacingAndGlyphs">${esc(r.label)}</text><text x="135.78" y="${32+i*step}" font-size="${font}" text-anchor="end">${r.count} besøg</text>`).join('');
    return `<svg x="1630" y="1040" width="520" height="335" viewBox="0 0 146 94" role="img" aria-label="Kortets printforside · offentlige adresser"><image href="${template}" width="146" height="94"/><g font-family="Arial, sans-serif" fill="#111"><text x="37.96" y="18.2" font-size="${Math.min(3.53,55/Math.max(1,String(c.name||'').length))}" textLength="${Math.min(55,String(c.name||'').length*1.8)}" lengthAdjust="spacingAndGlyphs">${esc(c.name||'')}</text><text x="118.26" y="18.2" font-size="${Math.min(3.53,16/Math.max(1,String(c.number).length))}" textLength="${Math.min(16,String(c.number).length*1.8)}" lengthAdjust="spacingAndGlyphs">${esc(c.number)}</text>${texts}<text x="10.22" y="${32+rows.length*step}" font-size="${font}" font-weight="bold">I alt</text><text x="135.78" y="${32+rows.length*step}" font-size="${font}" text-anchor="end" font-weight="bold">${total} besøg</text></g></svg>`;
  },
  digitalSvg(c,members,houses,mapMarkup,template,backgroundImage){
    const total=members.reduce((n,a)=>n+a.count,0),number=String(c.number),name=String(c.name||''),numberLines=number.match(/.{1,12}/gu)||[''],numberSize=Math.min(48,180/Math.max(1,Math.min(12,number.length))),nameSize=Math.min(43,1510/Math.max(1,name.length));
    return `<svg xmlns="http://www.w3.org/2000/svg" width="2200" height="1560" viewBox="0 0 2200 1560" role="img" aria-labelledby="digitalTitle"><title id="digitalTitle">Distriktskort ${esc(number)} · ${esc(name)}</title><defs><clipPath id="mapClip"><rect x="40" y="120" width="1540" height="1310" rx="22"/></clipPath></defs><rect width="2200" height="1560" fill="#eff4f8"/><g font-family="Arial, sans-serif"><path d="M0 0H2200V164H0Z" fill="#163c57"/><rect x="40" y="32" width="206" height="96" rx="24" fill="#fff" fill-opacity=".14"/><text x="143" text-anchor="middle" font-size="${numberSize}" font-weight="bold" fill="#fff">${numberLines.map((line,i)=>`<tspan x="143" y="${80+(i-(numberLines.length-1)/2)*numberSize*1.2+numberSize*.33}">${esc(line)}</tspan>`).join('')}</text><text x="280" y="48" font-size="18" letter-spacing="3" fill="#b8d6e8">DIGITALT DISTRIKTSKORT</text><text x="280" y="104" textLength="${Math.min(1510,name.length*nameSize*.57)}" lengthAdjust="spacingAndGlyphs" font-size="${nameSize}" font-weight="bold" fill="#fff">${esc(name)}</text><text x="2140" y="96" text-anchor="end" font-size="34" font-weight="bold" fill="#fff">LTM</text><rect x="26" y="190" width="1568" height="1336" rx="30" fill="#dbe5ed"/><rect x="24" y="184" width="1568" height="1336" rx="30" fill="#fff"/><g transform="translate(0 80)"><rect x="40" y="120" width="1540" height="1310" rx="22" fill="#eaf0ec"/><g clip-path="url(#mapClip)">${mapMarkup}</g></g><rect x="1620" y="200" width="540" height="180" rx="28" fill="#fff"/><text x="1652" y="279" font-size="49" font-weight="bold" fill="#163c57">${total}</text><text x="1652" y="330" font-size="23" fill="#5a7182">besøg</text><path d="M1874 236V344" stroke="#dce6ed" stroke-width="2"/><text x="1904" y="279" font-size="49" font-weight="bold" fill="#163c57">${houses.length}</text><text x="1904" y="330" font-size="23" fill="#5a7182">${houses.length===1?'husnummer':'husnumre'}</text><rect x="1620" y="410" width="540" height="240" rx="28" fill="#fff"/><text x="1652" y="464" font-size="27" font-weight="bold" fill="#163c57">Find rundt i distriktet</text><text x="1652" y="516" font-size="24" fill="#a33f39">Rød prik = ét besøg</text><text x="1652" y="564" font-size="22" fill="#5a7182">Husnumrene står ved adresserne.</text><text x="1652" y="604" font-size="22" fill="#5a7182">Vejoversigten er på kortet nedenfor.</text><rect x="1620" y="680" width="540" height="250" rx="28" fill="#fff1ed"/><text x="1652" y="734" font-size="25" font-weight="bold" fill="#b3261e">Husk det fysiske kort</text><text x="1652" y="788" font-size="24" fill="#b3261e" aria-label="Husk at tjekke efter IB på det fysiske distriktskort"><tspan x="1652">Husk at tjekke efter IB på</tspan><tspan x="1652" dy="38">det fysiske distriktskort</tspan></text><text x="1652" y="888" font-size="21" fill="#7c5b53">Det digitale kort viser ingen IB.</text><text x="1628" y="1000" font-size="25" font-weight="bold" fill="#163c57">Kortets printforside</text><rect x="1620" y="1030" width="540" height="355" rx="16" fill="#dbe5ed"/>${this.publicFront(c,members,template)}<text x="1628" y="1450" font-size="21" fill="#5a7182">Kortbillede · ${fmt(state.today)}</text><text x="42" y="1546" font-size="17" fill="#5a7182">${backgroundImage?'Kort: © OpenStreetMap-bidragsydere · openstreetmap.org/copyright · Adresser: DAR':'Adresser / vejlinjer: DAR · øvrige veje / bygninger: © OpenStreetMap-bidragsydere, ODbL'}</text></g></svg>`;
  },
  async blob(id,background='local',options={}){
    if(this.exporting)throw Error('En PNG-eksport kører allerede. Vent til den er færdig.');
    this.exporting=true;try{
    if(background==='osm')await this.prepareOSM(id,options);
    if(options.publicCard)options={...options,publicTemplate:await this.frontTemplate()};
    const snapshot=background==='osm'?this.osmSnapshot(id,{tight:true,...options}):{},svg=this.svg(id,{...snapshot,...options}),image=new Image();
    await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(Error('Kortbilledet kunne ikke dannes i browseren.'));image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);});
    const canvas=document.createElement('canvas');canvas.width=2200;canvas.height=1560;const ctx=canvas.getContext('2d');if(!ctx)throw Error('Browseren understøtter ikke billedeksport.');ctx.drawImage(image,0,0);
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('PNG-billedet kunne ikke gemmes.');
    return blob;
    }finally{this.exporting=false;}
  },
  async png(id,background='local'){
    const blob=await this.blob(id,background),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Distriktskort-'+String(card(id).number).replace(/[^0-9A-Za-z_-]/g,'_')+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);toast('Kortbilledet er hentet som PNG');
  }
};
