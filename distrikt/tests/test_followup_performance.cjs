// Fictional records only; no network, real user files or DOM implementation.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const workspace=read('workspace.js'),i18n=read('i18n.js');
function prepare(source,n,c){
 const addresses=Array.from({length:n},(_,i)=>({id:'a'+i,label:'Fiktivvej '+i,retired:i%23===0}));
 const cards=Array.from({length:c},(_,i)=>({id:'c'+i,number:String(i+1),area_id:'a',address_ids:[],back_revision:i%5===0,geo_polygon:[[10+i*.002,55],[10+i*.002+.001,55],[10+i*.002+.001,55.001],[10+i*.002,55.001]]}));
 addresses.forEach((a,i)=>{cards[i%c].address_ids.push(a.id);if(i%7===0)cards[(i+1)%c].address_ids.push(a.id);});
 cards[1].geo_polygon=cards[0].geo_polygon.map(p=>p.slice());
 const state={cards,loans:[],notes:[],publishers:[],settings:{},ignored:addresses.filter((_,i)=>i%31===0).map(a=>({address_id:a.id})),ib_reviews:[{id:'review',card_id:'c0'}],followup_ignores:[]};
 const geo={loaded:true,addresses:()=>addresses,data:{changes:[{id:'new',kind:'new',after:{label:'Fiktiv ny vej'}}]}};
 const profiles={has:(...rights)=>!state.profile||rights.every(r=>state.profile.permissions.includes(r)),canAction:()=>true};
 const load=new Function('state','GeoUI','ProfilesUI','document','window',i18n+'\n'+
  "const cmp=(a,b)=>String(a).localeCompare(String(b),'da',{numeric:true}),esc=v=>I18n.escape(v),ui=(v,p)=>I18n.label(v,p),loanFor=id=>state.loans.find(l=>l.card_id===id&&!l.returned),publisherName=id=>state.publishers.find(p=>p.id===id)?.name||'Ukendt',empty=v=>'<div>'+v+'</div>';\n"+
  source+'\nreturn {Workspace,I18n};');
 const {Workspace:w,I18n:lang}=load(state,geo,profiles,{addEventListener(){}},{addEventListener(){}});
 return {w,lang,state,geo,addresses};
}
for(const [n,c] of [[500,25],[12000,240]]){
 const {w,lang,state,geo,addresses}=prepare(workspace,n,c);
 const original=w.followupItems.bind(w);
 const compare=(a,b)=>String(a).localeCompare(String(b),'da',{numeric:true});
 const order=(a,b)=>compare(a.card?.number||'',b.card?.number||'')||compare(a.category,b.category)||compare(a.key,b.key);
 const all=original(true);
 assert.deepEqual(all.map(r=>r.key),[...all].sort(order).map(r=>r.key),'Numeric Danish ordering unchanged');
 const overlap=all.find(r=>r.relatedCard);assert.ok(overlap);
 state.followup_ignores=[{key:overlap.key,ignored:true,token:'fictional'}];
 let calls=0;w.followupItems=(...args)=>{calls++;return original(...args);};
 for(const language of ['da','en']){
  lang.set(language);
  for(const filter of ['all','checks','reprint','addresses','ignored','ib-review']){
   w.followupFilter=filter;w.followupQuery='';
   const expected=original(true).filter(r=>filter==='ignored'?r.ignored:!r.ignored&&(filter==='all'||filter===r.category));
   calls=0;
   const html=w.followups();
   assert.equal(calls,1,'One collection per list render');
   assert.equal((html.match(/data-followup=/g)||[]).length,Math.min(expected.length,w.followupLimit));
  }
 }
 // Neither state nor geographic data may be cached across calls.
 w.followupFilter='all';const count=original().length;
 state.cards[0].front_revision=true;assert.equal(original().length,count+1);
 geo.data.changes=[];assert.equal(original().length,count);
 state.followup_ignores[0].ignored=false;assert.equal(original().length,count+1);
 state.profile={permissions:['cards.view','ib.view']};
 assert.deepEqual(original().map(r=>r.category),['ib-review']);
 assert.equal((w.followups().match(/data-followup=/g)||[]).length,1);
 state.profile.desk_only=true;assert.equal(original().length,0);
 state.profile=null;assert.equal(original().length,count+1);
 // A new geographic snapshot is visible immediately, including retired status.
 addresses[1].retired=true;assert.equal(original().length,count+2);
}
console.log('Follow-up performance: single collection, Danish order, bilingual filters, fresh mutations and permission isolation passed.');
