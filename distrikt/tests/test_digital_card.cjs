// Only fictional cards and the public blank form; never a user's data folder.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const template='data:image/png;base64,'+fs.readFileSync(path.join(__dirname,'../templates/S-12-source.png')).toString('base64');
const fetched=[],images=[];
class ImageStub{set src(value){if(value.startsWith('data:image/png')){this.naturalWidth=2000;this.naturalHeight=1288;if(ImageStub.failTemplate){this.onerror();return;}}else images.push(decodeURIComponent(value.split(',').slice(1).join(',')));this.onload();}}
class ReaderStub{readAsDataURL(){this.result=template;this.onload();}}
const canvas={getContext:()=>({drawImage(){}}),toBlob(fn){fn({type:'image/png'});}};
const context={console,Date,Intl,Number,String,Math,JSON,Map,Set,WeakMap,Array,Object,Promise,setTimeout,clearTimeout,
 Image:ImageStub,FileReader:ReaderStub,location:{origin:'http://127.0.0.1:9999'},window:{addEventListener(){}},
 document:{getElementById:()=>({open:false}),querySelector:()=>({content:'FICTIONAL_TOKEN'}),addEventListener(){},createElement(kind){assert.equal(kind,'canvas');return canvas;}},
 fetch:async url=>{fetched.push(url);assert.equal(url,'/s12-template.png','Only the local blank template may be fetched');return {ok:true,blob:async()=>({type:'image/png'})};},
 GeoUI:{data:{roads:[],buildings:[]}},RoadSearch:{normalize:s=>s.toLowerCase()}};
vm.createContext(context);vm.runInContext(read('i18n.js'),context);vm.runInContext(read('map-export.js'),context);vm.runInContext(read('share-ui.js'),context);
const app=read('app.js');vm.runInContext(app.slice(0,app.indexOf("document.addEventListener('input'")),context);
const run=s=>vm.runInContext(s,context);
run(`state={today:'2026-10-17',cards:[{id:'fake',number:'PRIVATE_NUMBER',name:'PRIVATE_NAME',addresses:[{road:'PRIVATE_IB_ROAD',numbers:'99',count:1}]}],ib:[{card_id:'fake',road:'PRIVATE_IB_ROAD',number:'99'}],publishers:[{name:'PRIVATE_PERSON'}],loans:[],notes:[{text:'PRIVATE_NOTE'}],public_maps:[],areas:[]};`);
context.recipe={publicCard:{id:'fake',number:'F120',name:'Fiktivt byområde & <prøve>',map_color:'#477596',geo_polygon:[[10,55],[10.02,55],[10.02,55.02],[10,55.02]],addresses:[{road:'PRIVATE_INJECTED',numbers:'99',count:5}],ib:'PRIVATE_IB'},publicMembers:[{id:'public-a',road:'Fiktiv Vej',number:'1',lng:10.005,lat:55.005,count:1,notes:'PRIVATE_MEMBER_NOTE'},{id:'public-b',road:'Fiktiv Vej',number:'3',lng:10.01,lat:55.01,count:2}],publicTemplate:template};
const before=run('JSON.stringify(state)'),svg=run("MapExport.svg('fake',recipe)");
assert(svg.includes('DIGITALT DISTRIKTSKORT'));assert(svg.includes('Kortets printforside'));assert(svg.includes('viewBox="0 0 146 94"'));assert(svg.includes(template));assert(svg.includes('Fiktivt byområde &amp; &lt;prøve&gt;'));assert(svg.includes('Fiktiv Vej 1-3'));assert(svg.includes('>3 besøg</text>'));assert(!svg.includes('PRIVATE_'));assert(!svg.includes('<foreignObject'));assert(!svg.includes('<script'));assert.equal((svg.match(/<circle /g)||[]).length,3);
assert.equal(run('JSON.stringify(state)'),before);assert.equal(fetched.length,0,'Pure rendering does not fetch anything');
const muted=svg.match(/<g data-map-background="muted" opacity=".3">([\s\S]*?)<\/g>/);assert(muted,'Public digital background is muted');assert(!muted[1].includes('<circle'));assert(!muted[1].includes('paint-order'));assert(!muted[1].includes('stroke-dasharray'));
context.raster={...context.recipe,backgroundImage:'data:image/png;base64,AAAA',viewBounds:[10,55,10.02,55.02]};const rasterSVG=run("MapExport.svg('fake',raster)");assert.match(rasterSVG,/<g data-map-background="muted" opacity=".3"><image /);assert.equal((rasterSVG.match(/<circle /g)||[]).length,3);assert(!rasterSVG.includes('PRIVATE_'));
context.GeoUI.data.dividers=[{divider_type:'river',points:[[10,55.005],[10.02,55.015]],notes:'PRIVATE_DIVIDER_NOTE'},{divider_type:'rail',points:[[10,55.015],[10.02,55.005]],name:'PRIVATE_UNUSED_LABEL'}];
const naturalSVG=run("MapExport.svg('fake',recipe)"),naturalLayer=naturalSVG.match(/<g data-map-background="muted" opacity=".3">([\s\S]*?)<\/g>/)[1];assert.match(naturalLayer,/stroke="#5598bf"/);assert.match(naturalLayer,/stroke="#69737c"/);assert(!naturalLayer.includes('<circle'));assert(!naturalLayer.includes('stroke-dasharray="12 7"'));assert(!naturalSVG.includes('PRIVATE_'));assert.equal((naturalSVG.match(/<circle /g)||[]).length,3);context.GeoUI.data.dividers=[];
assert.throws(()=>run("MapExport.svg('fake',{...recipe,publicTemplate:'https://example.invalid/private.png'})"),/printforside/);
assert.throws(()=>run("MapExport.svg('fake',{...recipe,publicTemplate:''})"),/printforside/);
assert.equal(run("JSON.stringify(frontRows({addresses:[{road:'Fiktiv Vej',numbers:'1, 3',count:3}]}))"),JSON.stringify([{label:'Fiktiv Vej 1-3',count:3}]),'Physical front and miniature share the row formatter');
const crowded=JSON.parse(JSON.stringify(context.recipe));crowded.publicCard.number='FIKTIVT-LANGT-KORTNUMMER-123456';crowded.publicCard.name='Fiktivt meget langt distriktsnavn med æøå og mange brede bogstaver WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW';crowded.publicMembers=Array.from({length:22},(_,i)=>({id:'fiction'+i,road:'Fiktiv lang vej '+String(i+1).padStart(2,'0'),number:String(i+1),lng:10.002+i*.0005,lat:55.002+i*.0005,count:1}));context.crowded=crowded;
const large=run("MapExport.svg('fake',crowded)");for(let i=1;i<=22;i++)assert(large.includes('Fiktiv lang vej '+String(i).padStart(2,'0')));assert(!large.includes('PRIVATE_'));
const empty=run("MapExport.svg('fake',{...recipe,publicMembers:[],publicCard:{...recipe.publicCard,name:''}})");assert(empty.includes('>0 besøg</text>'));assert(!/=["'](?:NaN|Infinity)/.test(empty));
if(process.argv[2]==='--preview-dir'){
 const folder=process.argv[3];assert(folder);fs.mkdirSync(folder,{recursive:true});for(const [name,data]of [['normal',svg],['crowded',large],['empty',empty]])fs.writeFileSync(path.join(folder,name+'.svg'),data);
}
(async()=>{
 const png=await run("MapExport.blob('fake','local',recipe)");assert.equal(png.type,'image/png');assert.deepEqual(fetched,['/s12-template.png']);assert(images.at(-1).includes('Kortets printforside'));assert(!images.at(-1).includes('PRIVATE_'));assert.equal(canvas.width,2200);assert.equal(canvas.height,1560);
 await run("MapExport.blob('fake','local',recipe)");assert.equal(fetched.length,1,'Cache only the blank public template');
 const savedFetch=context.fetch;context.fetch=async()=>({ok:false});run('MapExport.templatePromise=null');await assert.rejects(run("MapExport.blob('fake','local',recipe)"),/printforside/);assert.equal(run('MapExport.exporting'),false);assert.equal(run('MapExport.templatePromise'),null);context.fetch=savedFetch;
 await run("MapExport.blob('fake','local',recipe)");assert.equal(fetched.length,2,'A failed template load can be retried');
 run('MapExport.templatePromise=null');ImageStub.failTemplate=true;await assert.rejects(run("MapExport.blob('fake','local',recipe)"),/beskadiget/);assert.equal(run('MapExport.exporting'),false);assert.equal(run('MapExport.templatePromise'),null);ImageStub.failTemplate=false;
 run(`api=async(url,data)=>{if(url!='/api/share/prepare'||data.card_id!=='fake')throw Error('Unexpected API call');return {json:async()=>({card:recipe.publicCard,members:recipe.publicMembers,fingerprint:'fictional-hash',render_revision:2})};};DistrictMap={map:{},id:'fake'};MapBackground={change:async()=>{}};MapExport.blob=async()=>({type:'image/png'});openDialog=html=>{previewHTML=html;};`);
 await run("ShareUI.prepare('fake')");assert.equal(run('ShareUI.pending.render_revision'),2);assert.equal(run('ShareUI.pending.fingerprint'),'fictional-hash');assert.equal(run('ShareUI.pending.card_id'),'fake');assert(!run('previewHTML').includes('PRIVATE_'));assert(run('previewHTML').includes('shareApproved'));
 assert.equal(run('JSON.stringify(state)'),before);
 console.log('Digital QR image: public-only miniature, shared front rows, escaping, dense/empty cards, local asset/retry, unchanged PNG size and explicit approval payload passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
