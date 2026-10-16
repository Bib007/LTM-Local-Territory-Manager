'use strict';
// All records are invented. No congregation data, address downloads or app API.
const DemoModel=(()=>{
 const day=d=>{const x=new Date(d);return `${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-${String(x.getDate()).padStart(2,'0')}`;};
 const offset=(date,n)=>{const d=new Date(date+'T12:00:00');d.setDate(d.getDate()+n);return day(d);};
 const year=date=>Number(date.slice(0,4))+(date.slice(5)>='09-01'?1:0);
 const id=()=>globalThis.crypto?.randomUUID?.()||'demo-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
 function seed(today=day(new Date())){
  const areas=[['Rønne · demo',14.7095,55.1002],['Nexø · demo',15.126,55.057],['Aakirkeby · demo',14.91,55.067],['Allinge · demo',14.79,55.273]].map(([name,lng,lat],i)=>({id:'area-'+i,name,lng,lat}));
  const s={schema:1,fictional:true,today,areas,cards:[],publishers:['Anna','Emil','Sofie','Mikkel','Ida','Oscar'].map((name,i)=>({id:'person-'+i,name:'Demo · '+name})),loans:[],completions:[],notes:[],visits:[{id:'co-demo',date:offset(today,-43)}]};
  for(let i=0;i<24;i++){
   const area=areas[Math.floor(i/6)],x=area.lng+(i%2)*.006,y=area.lat+Math.floor((i%6)/2)*.0035,poly=[[x,y],[x+.005,y],[x+.005,y+.0028],[x,y+.0028]];
   const card={id:'card-'+i,number:String((Math.floor(i/6)+1)*100+i%6),name:['Demokvarteret','Eksempelbakken','Fiktivbyen'][i%3]+' '+(i%6+1),area_id:area.id,kind:i%5===0?'Land':'By',in_folder:i>=8&&i<14,temporary:false,polygon:poly,addresses:[],last_completed:null};
   for(let n=0;n<12;n++)card.addresses.push({id:'address-'+i+'-'+n,road:['Demo Bakkevej','Fiktiv Kløversti','Eksempelvænget'][i%3],number:String(n+1),lng:x+.0006+(n%4)*.00115,lat:y+.00045+Math.floor(n/4)*.0009,dnc:i%4===0&&n===0,dnc_date:offset(today,-20)});
   for(let j=0;j<3;j++){
    const date=offset(today,-((i===0?210:i*9+4)+j*117)),assigned=offset(date,-12-(i%18));
    s.completions.push({id:'completion-'+i+'-'+j,card_id:card.id,date,visits:12,assigned,publisher_id:s.publishers[(i+j)%6].id});
    s.loans.push({id:'old-loan-'+i+'-'+j,card_id:card.id,publisher_id:s.publishers[(i+j)%6].id,assigned,returned:date,completed:true,note:''});
    if(!card.last_completed||date>card.last_completed)card.last_completed=date;
   }
   if(i<8)s.loans.push({id:'loan-'+i,card_id:card.id,publisher_id:s.publishers[i%6].id,assigned:offset(today,-(i===0?139:7+i*5)),returned:null,completed:false,note:''});
   s.cards.push(card);
  }
  s.notes=[{id:'note-1',card_id:'card-2',text:'Demo: Kontroller husnumrene ved næste genprint.',task:true,resolved:false,date:offset(today,-2)},{id:'note-2',card_id:'card-8',text:'Demo: Tilføj en opdigtet IB-adresse efter aflevering.',task:true,resolved:false,date:offset(today,-6)}];return s;
 }
 const active=(s,cardId)=>s.loans.find(l=>l.card_id===cardId&&!l.returned);
 const position=(s,c)=>active(s,c.id)?'assigned':c.in_folder?'folder':'box';
 const count=c=>c.addresses.length;
 const members=c=>c.addresses.filter(a=>!a.dnc&&!a.ignored);
 function assign(s,cardId,publisherId,date){
  const c=s.cards.find(c=>c.id===cardId),p=s.publishers.find(p=>p.id===publisherId);
  if(!c||!p)throw Error('Choose a card and publisher.');if(active(s,c.id))throw Error('This card is already assigned.');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(Date.parse(date+'T12:00:00'))||day(new Date(date+'T12:00:00'))!==date||date>s.today)throw Error('Choose a valid assignment date.');
  const item={id:id(),card_id:c.id,publisher_id:p.id,assigned:date,returned:null,completed:false,note:''};s.loans.push(item);c.in_folder=false;return item;
 }
 function finish(s,cardId,date,completed,note='',task=false){
  const c=s.cards.find(c=>c.id===cardId),l=active(s,cardId);if(!c||!l)throw Error('This card is not assigned.');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(Date.parse(date+'T12:00:00'))||day(new Date(date+'T12:00:00'))!==date||date<l.assigned||date>s.today)throw Error('Choose a return date after assignment and no later than today.');
  note=String(note).trim();if(note.length>1000)throw Error('The note is too long.');l.returned=date;l.completed=!!completed;l.note=note;c.in_folder=false;
  if(completed){s.completions.push({id:id(),card_id:c.id,date,visits:count(c),assigned:l.assigned,publisher_id:l.publisher_id});c.last_completed=[c.last_completed,date].filter(Boolean).sort().at(-1);}
  if(note)s.notes.push({id:id(),card_id:c.id,text:note,task:!!task,resolved:false,date});return l;
 }
 function move(s,cardId,inFolder){const c=s.cards.find(c=>c.id===cardId);if(!c||active(s,cardId))throw Error('Only available cards can be moved.');c.in_folder=!!inFolder;}
 function create(s,number,name,areaId,kind){number=String(number).trim();name=String(name).trim();if(!number||number.length>20||name.length>100)throw Error('Check the number and name.');if(s.cards.some(c=>c.number.toLowerCase()===number.toLowerCase()))throw Error('The card number already exists.');if(!s.areas.some(a=>a.id===areaId)||!['By','Land','Ukendt'].includes(kind))throw Error('Choose an area and type.');const c={id:id(),number,name,area_id:areaId,kind,in_folder:false,temporary:true,polygon:[],addresses:[],last_completed:null};s.cards.push(c);return c;}
 function period(today,mode='service',selectedYear=year(today)){
  if(mode==='service')return {start:(selectedYear-1)+'-09-01',end:selectedYear+'-09-01'};
  const d=new Date(today+'T12:00:00'),n=d.getDate();d.setDate(1);d.setFullYear(d.getFullYear()-1);const max=new Date(d.getFullYear(),d.getMonth()+1,0).getDate();d.setDate(Math.min(n,max));return {start:day(d),end:offset(today,1)};
 }
 function stats(s,p=period(s.today)){
  const events=s.completions.filter(e=>e.date>=p.start&&e.date<p.end),group=new Map();for(const e of s.completions){const a=group.get(e.card_id)||[];a.push(e.date);group.set(e.card_id,a);}const intervals=[];
  for(const dates of group.values()){dates.sort();for(let i=1;i<dates.length;i++)intervals.push((Date.parse(dates[i]+'T12:00:00Z')-Date.parse(dates[i-1]+'T12:00:00Z'))/86400000);}
  return {events:events.length,visits:events.reduce((n,e)=>n+e.visits,0),unique:new Set(events.map(e=>e.card_id)).size,assigned:s.cards.filter(c=>position(s,c)==='assigned').length,folder:s.cards.filter(c=>position(s,c)==='folder').length,box:s.cards.filter(c=>position(s,c)==='box').length,average:intervals.length?Math.round(intervals.reduce((a,b)=>a+b,0)/intervals.length):null};
 }
 return {seed,day,offset,year,id,active,position,count,members,assign,finish,move,create,period,stats};
})();
if(typeof module!=='undefined')module.exports=DemoModel;
