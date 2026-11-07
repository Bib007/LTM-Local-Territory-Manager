// Exercise the actual Drive preview PNG pipeline with invented data and offline tiles.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
module.exports=async(browser,out)=>{
 const root=path.resolve(__dirname,'../distrikt/app'),points=[[10,55],[10.01,55],[10.01,55.01],[10,55.01]];
 const card={id:'c1',number:'F01',name:'Fiktivt kontrastkort',area_id:'a',kind:'By',address_ids:['a1','a2','a3','a4','a5','a6'],geo_polygon:points,map_color:'#477596',addresses:[],public_dates:{completed:'2026-10-01',assigned:'2026-10-10'}};
 const longRoad='Tæt prøvevej med en fiktiv, ekstra lang vejlinje til kontrol af hele printforsiden og læsbar ombrydning';
 const members=[
  {id:'a1',road:'Fiktiv vej',number:'17',lng:10.004,lat:55.005,count:1},
  {id:'a2',road:longRoad,number:'2',lng:10.007,lat:55.008,count:12},
  {id:'a3',road:longRoad,number:'2',lng:10.0070002,lat:55.008,count:5},
  {id:'a4',road:longRoad,number:'2A',lng:10.007,lat:55.008,count:4},
  {id:'a5',road:longRoad,number:'3',lng:10.00701,lat:55.00801,count:8},
  {id:'a6',road:'Fiktiv vej',number:'19',lng:10.0102,lat:55.0102,count:5},
 ];
 const visits=members.reduce((sum,a)=>sum+a.count,0);
 const excluded=[
  {id:'ignored',road:'IB_SKAL_IKKE_MED',number:'31',lng:10.003,lat:55.003,count:17},
  {id:'ib',road:'Fiktiv rød vej',number:'35',lng:10.003,lat:55.003,count:1},
  {id:'legacy-ib',road:'Fiktiv ældre vej',number:'41',floor:'2',door:'tv',lng:10.005,lat:55.004,count:1},
  {id:'retired',road:'IB_SKAL_IKKE_MED',number:'37',lng:10.003,lat:55.003,count:17},
 ];
 card.geo_addresses=[...members,...excluded];
 card.address_ids=card.geo_addresses.map(a=>a.id);
 const manualCard={id:'manual1',number:'F125',name:'Fiktivt manuelt kort',temporary:false,addresses:[{road:'Prøvevej',numbers:'2–8',count:0,count_unknown:true},{road:'Udeladt prøvevej',numbers:'99',count:2},{road:'Sikker sti',numbers:'hele vejen',count:3}]};
 const state={revision:'FICTIONAL_R1',today:'2026-10-21',version:'fictional',cards:[card,manualCard],areas:[{id:'a',name:'Fiktivt område'}],publishers:[],loans:[],completions:[],ib:[{id:'ib1',card_id:'c1',address_id:'ib',note:'PRIVAT_IB_NOTE'},{id:'ib2',card_id:'manual1',road:'Udeladt prøvevej',number:'99'},{id:'ib3',card_id:'c1',road:'Fiktiv ældre vej',number:'41, 2. tv'}],ignored:[{id:'ignored-row',address_id:'ignored'}],notes:[],tasks:[],visits:[],recovery:[],maps:[],settings:{congregation:'Fiktiv menighed',folder_minimum:30,rural_mode:'manual',rural_minimum:5,onboarding:{completed:true}}};
 const geo={addresses:card.geo_addresses.map(a=>a.id==='retired'?{...a,retired:true}:a),buildings:[],roads:[],dividers:[],info:{addresses:1,buildings:0,roads:0},status:{a1:{card_id:'c1',card_number:'F01'}},main_boundary:{points}};
 const fixture={cards:state.cards,addresses:geo.addresses,ignored:state.ignored,ib:state.ib};
 const backend=(stage,data)=>JSON.parse(execFileSync(process.env.PYTHON||'python3',[
  path.join(__dirname,'fixtures/render_public_dates.py'),stage
 ],{input:JSON.stringify({fixture,data}),maxBuffer:16*1024*1024}).toString());
 let serverPreview='',uploadedPdf='';
 const context=await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[],calls=[];
 try{
  page.on('pageerror',e=>errors.push(e.message));
  const tile=Buffer.from(await page.evaluate(()=>{const c=document.createElement('canvas');c.width=c.height=256;const g=c.getContext('2d');g.fillStyle='rgb(40,90,130)';g.fillRect(0,0,256,256);return c.toDataURL().split(',')[1];}),'base64');
  await context.route('**/*',async route=>{
   const u=new URL(route.request().url()),json=data=>route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
   if(u.hostname==='tile.openstreetmap.org')return route.fulfill({contentType:'image/png',body:tile});
   assert.equal(u.hostname,'ltm.image.test','All services are offline');
   if(u.pathname.startsWith('/api/')){
    calls.push(u.pathname);
    if(u.pathname==='/api/state')return json(state);
    if(u.pathname==='/api/geo')return json(geo);
    if(u.pathname==='/api/map')return json({image:''});
    if(u.pathname==='/api/geo/job')return json({status:'idle'});
    if(u.pathname==='/api/ping')return json({ok:true});
    if(u.pathname==='/api/connections/drive')return json({connected:false,account:''});if(u.pathname==='/api/share/status')return json({connected:true,account:'Fictional',cards:[]});
    if(u.pathname==='/api/share/prepare'){
     const request=route.request().postDataJSON(),recipe=backend('prepare',request);
     if(request.card_id==='c1')assert.deepEqual(recipe.members.map(a=>a.id),[...members.map(a=>a.id),'ib','legacy-ib']);
     return json(recipe);
    }
    if(u.pathname==='/api/share/date-preview'){
     const result=backend('date-preview',route.request().postDataJSON());
     serverPreview=result.png;return json(result);
    }
    if(u.pathname==='/api/share/publish'){
     const input=route.request().postDataJSON();
     assert.equal(input.png,serverPreview,'Approval submits the exact displayed image');
     assert.equal(input.front_png,await page.locator('.sharePreview').nth(1).getAttribute('src'));
     const {pdf,...result}=backend('publish',input);uploadedPdf=pdf;return json(result);
    }
    throw Error('Unexpected API request '+u.pathname);
   }
   if(u.pathname==='/s12-template.png')return route.fulfill({path:path.resolve(root,'../templates/S-12-source.png')});
   if(u.pathname==='/s12-template-en.png')return route.fulfill({path:path.resolve(root,'../templates/S-12-E-source.png')});
   const file=path.resolve(root,u.pathname==='/'?'index.html':'.'+u.pathname);
   assert.ok(file.startsWith(root+path.sep)&&fs.existsSync(file),'Unexpected asset '+u.pathname);return route.fulfill({path:file});
  });
  await context.addInitScript(()=>{if(!localStorage.getItem('ltm-language'))localStorage.setItem('ltm-language','da');});await page.goto('http://ltm.image.test/');await page.waitForFunction(()=>state!==null);
  await page.evaluate(geo=>{GeoUI.loaded=true;GeoUI.data=geo;closeDialog();page='Indstillinger';openDialog(DistrictMap.html('c1'));DistrictMap.mount('c1');const svg=MapExport.svg;MapExport.svg=function(...args){return window.actualPreviewSvg=svg.apply(this,args);};const raster=MapExport.raster;MapExport.raster=function(svg){if(svg.includes('<g transform="translate('))window.actualFrontSvg=svg;return raster.call(this,svg);};},geo);
  const privateVisits=visits+2;
  const privateMarkers=await page.evaluate(()=>DistrictMap.layer.getLayers()
   .filter(marker=>marker instanceof L.CircleMarker)
   .map(marker=>({color:marker.options.fillColor,tooltip:marker.getTooltip().getContent()})));
  assert.equal(privateMarkers.length,privateVisits,'The normal map keeps ordinary dots for linked and legacy IB addresses');
  assert.equal(privateMarkers.filter(m=>m.color==='#ca4c43'&&/35|41/.test(m.tooltip)).length,2);
  assert.match(await page.locator('#districtMapCount').textContent(),new RegExp(privateVisits+' besøg'));
  const overviewMarkers=await page.evaluate(async()=>{
   await OverviewMap.open('c1');
   return OverviewMap.layer.getLayers().filter(marker=>marker instanceof L.CircleMarker).map(marker=>marker.getTooltip().getContent());
  });
  assert.equal(overviewMarkers.length,privateVisits,'The focused overview uses the same private membership');
  assert.equal(overviewMarkers.filter(tooltip=>/35|41/.test(tooltip)).length,2);
  await page.evaluate(()=>{page='Indstillinger';openDialog(DistrictMap.html('c1'));DistrictMap.mount('c1');});
  for(const action of ['export-map','export-map-osm']){
   const [download]=await Promise.all([
    page.waitForEvent('download'),page.locator(`[data-geo="${action}"]`).click()
   ]);
   const result=await page.evaluate(async png=>{
    const svg=new DOMParser().parseFromString(window.actualPreviewSvg,'image/svg+xml');
    const image=new Image();image.src=png;await image.decode();
    const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
    const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
    const labels=[...svg.querySelectorAll('text[paint-order="stroke"]')].filter(label=>['35','41'].includes(label.textContent));
    const visible=labels.map(label=>[...ctx.getImageData(Math.round(+label.getAttribute('x')-11),Math.round(+label.getAttribute('y')+9),1,1).data].join());
    return {size:[canvas.width,canvas.height],visible,svg:window.actualPreviewSvg,circles:svg.querySelectorAll('circle').length};
   },'data:image/png;base64,'+fs.readFileSync(await download.path()).toString('base64'));
   assert.deepEqual(result.size,[2200,1560]);
   assert.deepEqual(result.visible,['202,76,67,255','202,76,67,255'],action+' contains both ordinary red IB-address dots in the downloaded PNG');
   assert.equal(result.circles,privateVisits);
   assert.doesNotMatch(result.svg,/>31<|>37<|PRIVAT_IB_NOTE|41, 2|>tv</);
  }
  await page.evaluate(()=>{
   DistrictMap.road='Fiktiv vej';DistrictMap.draw();
   DistrictMap.map.setZoom(DistrictMap.map.getZoom()+1);
   return ShareUI.prepare('c1');
  });
  assert.equal(await page.locator('#sharePublish').isDisabled(),true,'Approval remains mandatory');
  const result=await page.evaluate(async()=>{
   const pending=ShareUI.pending,doc=new DOMParser().parseFromString(window.actualPreviewSvg,'image/svg+xml');
   if(!pending||pending.render_revision!==12||pending.date_updates!==true)throw Error('Missing current preview');
   if(doc.querySelectorAll('[data-ltm-brand] svg').length!==1||doc.querySelector('[data-ltm-brand] text')?.textContent!=='Local Territory Manager')throw Error('Missing public project identity');
   const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=pending.png;});
   const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
   const pixel=(x,y)=>[...ctx.getImageData(Math.round(x),Math.round(y),1,1).data];
   const dots=[...doc.querySelectorAll('circle')].map(circle=>[+circle.getAttribute('cx'),+circle.getAttribute('cy')+80]);
   const mapPixels=ctx.getImageData(40,200,1540,1310).data;
   // Count separated red pixel regions, even when the SVG claims to draw more circles.
   const red=new Uint8Array(mapPixels.length/4);
   for(let i=0;i<red.length;i++)red[i]=Number(mapPixels[4*i]===198&&mapPixels[4*i+1]===40&&mapPixels[4*i+2]===40);
   let redRegions=0;
   for(let i=0;i<red.length;i++){
    if(!red[i])continue;
    redRegions++;red[i]=0;const pending=[i];
    while(pending.length){
     const j=pending.pop();
     const adjacent=[j-1540,j+1540];
     if(j%1540)adjacent.push(j-1);
     if(j%1540!==1539)adjacent.push(j+1);
     for(const k of adjacent)if(red[k]){red[k]=0;pending.push(k);}
    }
   }
   // A solid known tile at 30% over white gives RGB 191,206,218 (±1 rounding).
   let backgroundSamples=0;
   for(let y=300;y<1400;y+=40)for(let x=140;x<1500;x+=40){const p=pixel(x,y);if(p.slice(0,3).every((v,i)=>Math.abs(v-[191,206,218][i])<=1))backgroundSamples++;}
   const labels=[...doc.querySelectorAll('text[paint-order="stroke"]')].map(label=>{
    const x=+label.getAttribute('x'),y=+label.getAttribute('y')+80,number=label.textContent;
    const data=ctx.getImageData(Math.floor(x),Math.floor(y)-20,number.length*14+4,24).data;
    let darkPixels=0;
    for(let i=0;i<data.length;i+=4)if((data[i]===140&&data[i+1]===28&&data[i+2]===28))darkPixels++;
    return {number,x,y,darkPixels};
   });
   const leaders=[...doc.querySelectorAll('[data-number-leader]')].map(n=>n.getAttribute('d'));
   return {leaders,frontSvg:window.actualFrontSvg,png:pending.png.split(',')[1],width:canvas.width,height:canvas.height,dots,redRegions,redCenters:dots.filter(p=>pixel(...p).join()==='198,40,40,255').length,neutralCenters:dots.filter(p=>pixel(...p).join()==='101,120,136,255').length,backgroundSamples,labels,svg:window.actualPreviewSvg};
  });
  assert.doesNotMatch(result.svg,/Kortets printforside/,'Page one has no miniature front');
  assert.match(result.frontSvg,/Fiktiv rød vej/);
  assert.match(result.frontSvg,/læsbar/);assert.match(result.frontSvg,/ombrydning/);
  assert.ok((result.frontSvg.match(/<text /g)||[]).length>8,'The long street wraps to separate lines');
  assert.doesNotMatch(result.frontSvg,/textLength|PRIVAT_IB_NOTE/);
  assert.ok(result.leaders.length>0,'Crowded labels have a visible leader');
  for(const line of result.leaders){
   const [x,y]=line.slice(1).split('L')[0].split(' ').map(Number);
   assert.ok(result.dots.some(([cx,cy])=>cx===x&&Math.abs(cy-(y+80))<1e-8),'Leader starts at a rendered dot');
  }
  assert.equal('data:image/png;base64,'+result.png,serverPreview,'The browser shows the exact server-dated image');
  assert.doesNotMatch(result.svg,/IB_SKAL_IKKE_MED|PRIVAT_IB_NOTE/);assert.match(result.svg,/Senest gennemgået/);assert.match(result.svg,/Udleveret d\./);assert.ok(/0?1\.10\.2026/.test(result.svg),'SVG shows the registered completion date');
  assert.deepEqual([result.width,result.height],[2200,1560]);assert.equal(result.dots.length,visits+2,'SVG includes all regular and both IB address points even with a road filter before export');
  assert.doesNotMatch(result.svg,/resterende besøg|#657888|#455761/,'The public image cannot disclose marker status through its legend');
   assert.equal(result.redRegions,privateVisits,'The final dated PNG has one independently visible red region per visit');
  assert.equal(result.redCenters,privateVisits,'Each regular visit has an unobscured red center in the PNG');assert.equal(result.neutralCenters,0,'No IB-specific grey marker remains');
  assert.ok(result.backgroundSamples>100,'Actual prepared PNG contains 30%-opacity OSM tiles over white');
  assert.deepEqual(result.labels.map(label=>label.number).sort(),['17','19','2','2','2A','3','35','41']);
  assert.equal(new Set(result.labels.map(label=>[label.x,label.y].join())).size,result.labels.length,'Nearby numbers receive separate positions');
  assert.ok(result.labels.every(label=>label.darkPixels>15),`Expected visible ink for each house number: ${JSON.stringify(result.labels)}`);
  assert.match(result.svg,/<g data-map-background="muted" opacity=".3"><image /);assert.ok(!calls.includes('/api/share/publish'),'Preview never uploads');assert.deepEqual(errors,[]);
  if(out)fs.writeFileSync(path.join(out,'drive-actual-preview.png'),Buffer.from(result.png,'base64'));
  const manual=await page.evaluate(async()=>{
   closeDialog();page='Indstillinger';DistrictMap.map=null;DistrictMap.id='manual1';
   const original=MapExport.svg;MapExport.svg=function(...args){window.manualPreviewSvg=original.apply(this,args);return window.manualPreviewSvg;};
   await ShareUI.prepare('manual1');
   const pending=ShareUI.pending,doc=new DOMParser().parseFromString(window.manualPreviewSvg,'image/svg+xml'),image=new Image();
   await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=pending.png;});
   return {width:image.naturalWidth,height:image.naturalHeight,png:pending.png,svg:window.manualPreviewSvg,frontSvg:window.actualFrontSvg,dialog:document.querySelector('#dialog')?.innerHTML||document.body.innerHTML,approvedDisabled:document.querySelector('#sharePublish').disabled};
  });
  assert.deepEqual([manual.width,manual.height],[2200,1560]);assert.match(manual.svg,/Geografisk kortvisning mangler/);assert.doesNotMatch(manual.svg,/Kortets printforside/);assert.match(manual.frontSvg,/Prøvevej 2-8/);assert.match(manual.frontSvg,/ukendt/);assert.match(manual.frontSvg,/Sikker sti hele vejen/);assert.doesNotMatch(manual.frontSvg,/Udeladt prøvevej/);assert.doesNotMatch(manual.svg,/<circle\b/);assert.doesNotMatch(manual.svg,/0 besøg/);assert.match(manual.dialog,/Nogle manuelle vejlinjer er udeladt/);assert.equal(manual.approvedDisabled,true);assert.ok(!calls.includes('/api/share/publish'));
  await page.evaluate(async()=>{closeDialog();page='Indstillinger';openDialog(DistrictMap.html('c1'));DistrictMap.mount('c1');await ShareUI.prepare('c1');});
  await page.locator('#shareApproved').check();
  await page.locator('#sharePublish').click();
  await page.locator('#dialog').waitFor({state:'hidden'});
  assert.equal(calls.filter(call=>call==='/api/share/publish').length,1);
  assert.ok(Buffer.from(uploadedPdf,'base64').toString('ascii',0,8).startsWith('%PDF-1.4'));
  if(out)fs.writeFileSync(path.join(out,'drive-actual-published.pdf'),Buffer.from(uploadedPdf,'base64'));
  assert.deepEqual(errors,[]);
  if(out)fs.writeFileSync(path.join(out,'manual-only-preview.png'),Buffer.from(manual.png.split(',')[1],'base64'));
  const dense=await page.evaluate(async()=>{
   const members=Array.from({length:900},(_,i)=>({id:'dense-'+i,road:'Fiktiv tæt vej',number:String(i+1),lng:10.005,lat:55.005,count:1}));
   const svg=MapExport.svg('c1',{publicCard:{id:'dense',number:'F900',name:'Fiktivt tæt kort',geo_polygon:[[10,55],[10.01,55],[10.01,55.01],[10,55.01]]},publicMembers:members,sharedPdf:true});
   const doc=new DOMParser().parseFromString(svg,'image/svg+xml'),blob=await MapExport.raster(svg);
   return {dots:doc.querySelectorAll('circle[fill="#c62828"]').length,labels:[...doc.querySelectorAll('text')].filter(t=>/^\d+$/.test(t.textContent)).length,bytes:blob.size};
  });
  assert.equal(dense.dots,900);assert.ok(dense.labels<900);assert.ok(dense.bytes>10000,'A real PNG is generated even when crowded labels are omitted');
  console.log('Actual ShareUI → OSM snapshot → SVG → PNG: 37 identical red visit regions, including both IB addresses, both approved pages embedded losslessly in a PDF sent to offline Drive, private metadata exclusions and manual fallback passed.');
 }finally{await context.close();}
};
