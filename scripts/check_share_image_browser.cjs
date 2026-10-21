// Exercise the actual Drive preview PNG pipeline with invented data and offline tiles.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
module.exports=async(browser,out)=>{
 const root=path.resolve(__dirname,'../distrikt/app'),points=[[10,55],[10.01,55],[10.01,55.01],[10,55.01]];
 const card={id:'c1',number:'F01',name:'Fiktivt kontrastkort',area_id:'a',kind:'By',address_ids:['a1'],geo_polygon:points,map_color:'#477596',addresses:[]};
 const members=[{id:'a1',road:'Fiktiv vej',number:'17',lng:10.004,lat:55.005,count:1,type:'Hus'}];
 const state={revision:'FICTIONAL_R1',today:'2026-10-21',version:'fictional',cards:[card],areas:[{id:'a',name:'Fiktivt område'}],publishers:[],loans:[],completions:[],ib:[],ignored:[],notes:[],tasks:[],visits:[],recovery:[],maps:[],settings:{congregation:'Fiktiv menighed',folder_minimum:30,rural_mode:'manual',rural_minimum:5,onboarding:{completed:true}}};
 const geo={addresses:members,buildings:[],roads:[],dividers:[],info:{addresses:1,buildings:0,roads:0},status:{a1:{card_id:'c1',card_number:'F01'}},main_boundary:{points}};
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[],calls=[];
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
    if(u.pathname==='/api/share/status')return json({connected:true,account:'Fictional',cards:[]});
    if(u.pathname==='/api/share/prepare')return json({card,members,fingerprint:'FICTIONAL_HASH',render_revision:4});
    throw Error('Unexpected API request '+u.pathname);
   }
   if(u.pathname==='/s12-template.png')return route.fulfill({path:path.resolve(root,'../templates/S-12-source.png')});
   const file=path.resolve(root,u.pathname==='/'?'index.html':'.'+u.pathname);
   assert.ok(file.startsWith(root+path.sep)&&fs.existsSync(file),'Unexpected asset '+u.pathname);return route.fulfill({path:file});
  });
  await page.goto('http://ltm.image.test/');await page.waitForFunction(()=>state!==null);
  await page.evaluate(geo=>{GeoUI.loaded=true;GeoUI.data=geo;closeDialog();page='Indstillinger';openDialog(DistrictMap.html('c1'));DistrictMap.mount('c1');const svg=MapExport.svg;MapExport.svg=function(...args){return window.actualPreviewSvg=svg.apply(this,args);};},geo);
  await page.evaluate(()=>ShareUI.prepare('c1'));
  assert.equal(await page.locator('#sharePublish').isDisabled(),true,'Approval remains mandatory');
  const result=await page.evaluate(async()=>{
   const pending=ShareUI.pending,doc=new DOMParser().parseFromString(window.actualPreviewSvg,'image/svg+xml');
   if(!pending||pending.render_revision!==4)throw Error('Missing current preview');
   const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=pending.png;});
   const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
   const pixel=(x,y)=>[...ctx.getImageData(Math.round(x),Math.round(y),1,1).data],circle=doc.querySelector('circle');
   const dot=pixel(+circle.getAttribute('cx'),+circle.getAttribute('cy')+80);
   // A solid known tile at 50% over white gives RGB 148,173,193 (±1 rounding).
   let backgroundSamples=0,labelPixels=0;
   for(let y=300;y<1400;y+=40)for(let x=140;x<1500;x+=40){const p=pixel(x,y);if(p.slice(0,3).every((v,i)=>Math.abs(v-[148,173,193][i])<=1))backgroundSamples++;}
   const data=ctx.getImageData(40,200,1540,1310).data;
   for(let i=0;i<data.length;i+=4)if(data[i]===140&&data[i+1]===28&&data[i+2]===28)labelPixels++;
   return {png:pending.png.split(',')[1],width:canvas.width,height:canvas.height,dot,backgroundSamples,labelPixels,svg:window.actualPreviewSvg};
  });
  assert.deepEqual([result.width,result.height],[2200,1560]);assert.deepEqual(result.dot,[198,40,40,255],'Visit dot remains full-strength red');
  assert.ok(result.backgroundSamples>100,'Actual prepared PNG contains half-opacity OSM tiles over white');assert.ok(result.labelPixels>20,'House number remains full-strength dark red');
  assert.match(result.svg,/<g data-map-background="muted" opacity=".5"><image /);assert.ok(!calls.includes('/api/share/publish'),'Preview never uploads');assert.deepEqual(errors,[]);
  if(out)fs.writeFileSync(path.join(out,'drive-actual-preview.png'),Buffer.from(result.png,'base64'));
  console.log('Actual ShareUI → OSM snapshot → SVG → PNG: 50% white-backed tiles, opaque red visits/labels and explicit upload approval passed.');
 }finally{await context.close();}
};
