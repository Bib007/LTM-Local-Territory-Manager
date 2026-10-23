// Production styles and renderer; exclusively fictional, offline visual fixtures.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'../distrikt/app'),read=name=>fs.readFileSync(path.join(root,name),'utf8'),out=process.env.LTM_BROWSER_OUTPUT;
if(out)fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({args:['--no-sandbox']});try{
 for(const width of [320,390,768,1440])for(const beta of [false,true]){
  const context=await browser.newContext({viewport:{width,height:240}}),page=await context.newPage();
  await context.route('**/*',route=>{const u=new URL(route.request().url());assert.equal(u.origin,'https://ltm.visual.test','No real service or map request');const file=u.pathname.slice(1);assert.ok(['style.css','workspace.css','brand-logo.svg','brand-mark.svg'].includes(file));return route.fulfill({path:path.join(root,file)});});
  const header=read('index.html').match(/<header>[\s\S]*?<\/header>/)[0];
  await page.setContent(`<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="https://ltm.visual.test/style.css"><link rel="stylesheet" href="https://ltm.visual.test/workspace.css"></head><body class="${beta?'betaChannel':''}">${header.replaceAll('src="/','src="https://ltm.visual.test/').replace('<b>LTM</b>',`<b>LTM${beta?' Beta':''}</b>`)}</body></html>`);
  await page.locator('.brandWordmark').evaluate(n=>n.decode());await page.locator('.brandCompact').evaluate(n=>n.decode());
  await page.locator('#saveState').evaluate(n=>{n.textContent='Alle ændringer er gemt';n.dataset.saveKind='saved';});
  assert.equal(await page.locator('#headerCongregation').count(),0);
  assert.equal(await page.locator('.brand').getAttribute('aria-describedby'),null);
  const geometry=await page.evaluate(()=>{const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,right:r.right,width:r.width,height:r.height};};return {brand:box('.brand'),logo:box('.brandWordmark'),save:box('#saveState'),overflow:document.documentElement.scrollWidth>innerWidth};});
  assert.equal(geometry.overflow,false,`Header overflow ${width}/${beta}`);
  assert.ok(geometry.brand.right<=geometry.save.x+1);assert.ok(geometry.save.width>=65);
  if(width>750){assert.equal(geometry.logo.width,360);assert.equal(geometry.logo.height,66);}
  if(out)await page.screenshot({animations:'disabled',path:path.join(out,`header-${beta?'beta':'stable'}-${width}.png`)});
  await context.close();
 }
 const context=await browser.newContext({viewport:{width:2200,height:1560}}),page=await context.newPage();
 await context.route('**/*',route=>{assert.equal(new URL(route.request().url()).href,'https://ltm.visual.test/s12-template.png');return route.fulfill({path:path.resolve(root,'../templates/S-12-source.png')});});
 await page.setContent('<meta name="app-token" content="FICTIONAL_OFFLINE_TOKEN">');await page.addScriptTag({content:read('i18n.js')});await page.addScriptTag({content:read('map-export.js')});
 const app=read('app.js');await page.addScriptTag({content:app.slice(0,app.indexOf("document.addEventListener('input'"))});
 await page.evaluate(()=>{state={today:'2026-10-19',cards:[],areas:[],ib:[]};window.GeoUI={data:{roads:[],buildings:[]}};});
 const template='data:image/png;base64,'+fs.readFileSync(path.resolve(root,'../templates/S-12-source.png')).toString('base64');
 for(const dense of [false,true])for(const raster of [false,true]){
  const result=await page.evaluate(async({dense,raster,template})=>{
   const points=[[10,55],[10.02,55],[10.02,55.02],[10,55.02]],members=Array.from({length:dense?36:3},(_,i)=>({id:'fiction-'+i,road:'Fiktiv vej '+(i%3+1),number:String(i+1),lng:10.002+(i%6)*.003,lat:55.002+Math.floor(i/6)*.003,count:1+i%3}));
   GeoUI.data={roads:Array.from({length:6},(_,i)=>({points:[[10,55+i*.004],[10.02,55+i*.004]]})),dividers:[{divider_type:'river',points:[[10.003,55],[10.007,55.01],[10.003,55.02]]},{divider_type:'rail',points:[[10.015,55],[10.015,55.02]]}],buildings:members.map(a=>({points:[[a.lng-.0004,a.lat-.0004],[a.lng+.0004,a.lat-.0004],[a.lng+.0004,a.lat+.0004],[a.lng-.0004,a.lat+.0004]]}))};
   const canvas=document.createElement('canvas');canvas.width=600;canvas.height=600;const ctx=canvas.getContext('2d');ctx.fillStyle='#b9d9a8';ctx.fillRect(0,0,600,600);ctx.lineWidth=3;ctx.strokeStyle='#222';ctx.font='22px Arial';
   for(let i=0;i<6;i++){ctx.strokeRect(20+i*95,20,65,560);ctx.fillStyle=i%2?'#1743ab':'#666';ctx.fillRect(30+i*95,70,36,36);ctx.fillText('F'+i,30+i*95,140);}
   const recipe={publicCard:{id:'fake',number:dense?'F36':'F3',name:dense?'Fiktivt tæt bykort':'Fiktivt spredt kort',map_color:'#477596',geo_polygon:points},publicMembers:members,publicTemplate:template,...(raster?{backgroundImage:canvas.toDataURL(),viewBounds:[10,55,10.02,55.02]}:{})};
   const svg=MapExport.svg('fake',recipe),doc=new DOMParser().parseFromString(svg,'image/svg+xml');
   if(doc.querySelector('parsererror'))throw Error('Invalid SVG');
   const layer=doc.querySelector('[data-map-background]');if(layer.getAttribute('opacity')!=='.5')throw Error('Missing background-only attenuation');
   const dots=[...doc.querySelectorAll('circle')];if(dots.length!==members.reduce((n,a)=>n+a.count,0)||dots.some(n=>n.closest('[data-map-background]')))throw Error('Visit dots must remain full-strength');
   const labels=[...doc.querySelectorAll('text[font-size="20"][paint-order="stroke"]')];if(labels.length!==members.length||labels.some(n=>n.closest('[data-map-background]')))throw Error('House numbers must remain full-strength');
   if(doc.querySelector('[stroke-dasharray="12 7"]').closest('[data-map-background]'))throw Error('Boundary must remain full-strength');
   // Actual SVG-to-PNG decoding, including the blank S-12 miniature.
   const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);});const output=document.createElement('canvas');output.width=2200;output.height=1560;output.getContext('2d').drawImage(image,0,0);
   return {svg,png:output.toDataURL().split(',')[1]};
  },{dense,raster,template});
  const name=`map-${dense?'dense':'sparse'}-${raster?'raster':'local'}`;
  if(out){fs.writeFileSync(path.join(out,name+'.svg'),result.svg);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(result.png,'base64'));}
 }
 await context.close();console.log('Fictional production header: stable/beta, empty/short/long names, four widths; digital cards: dense/sparse, local/raster, full-strength foreground and real PNG decoding passed.');
 await require('./check_partition_browser.cjs')(browser,out);
 await require('./check_share_image_browser.cjs')(browser,out);
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
