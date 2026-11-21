// Focused offline UI regression against the real administrative render functions.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const src = fs.readFileSync(path.join(__dirname,'../app/app.js'),'utf8');
function section(start,end) {
  const i=src.indexOf(start), j=src.indexOf(end,i+start.length);
  assert(i>=0 && j>i,'app.js function boundaries still exist: '+start);
  return src.slice(i,j);
}
const card={id:'fictional-1',number:'25',internal_number:'B07',name:'Fiktiv syd',
  internal_name:'Ved den fiktive skole <script>alert(1)</script> / '+ 'megetlangt'.repeat(25),
  area_id:'',kind:'By',temporary:true,addresses:[],last_completed:null};
let dialogHTML='';
const values={number:'25',name:'Fiktiv syd',internal_number:'B07',
  internal_name:'Lokalt områdenavn',map_color:'#477596',area_id:'',kind:'By'};
const form={dataset:{id:card.id},querySelectorAll(){return [];}};
class FakeFormData{
  constructor(f){assert.equal(f,form);}
  get(key){return values[key]??null;}
  has(key){return key==='temporary';}
}
const esc=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const ctx={
  state:{cards:[card],settings:{require_revision:false},areas:[],today:'2026-11-21'},
  query:'',area:'',selected:'',folderCardPickerSelected:new Set(),
  esc,ui:(s)=>s,areaName:()=>'',cmp:(a,b)=>String(a).localeCompare(String(b)),
  I18n:{attribute:()=>'',language:()=> 'da', text:s=>s},
  AdminUI:{selected:new Set(),folderReason:()=>'',visible:[]},
  loanFor:()=>null,folderEnabled:()=>false,cardLocation:()=> 'box',
  quickLoanAction:()=>'',taskBadge:()=>'',position:()=> 'I kassen',
  visitsText:()=>'',visitsKnown:()=>false,visitsCount:()=>0,fmt:()=>'-',
  publisherName:()=>'',card:id=>id===card.id?card:null,
  openDialog:html=>{dialogHTML=html;},formEnd:()=>'<button type="submit">Gem</button>',
  cardColor:()=> '#477596',areaOptions:()=>'',addressRow:()=>'',ProfilesUI:{has:()=>false},
  el:id=>id==='cardForm'?form:null,FormData:FakeFormData,
};
vm.createContext(ctx);
vm.runInContext(
  section('function searchText(c)','function cardLocation(c)')+
  section('function table(cards','function controls(')+
  section('function details(c)','function folderPlan(')+
  section(' function folderCardPickerRows(',' function folderCardPickerFooter(')+
  section('function editCard(id)','async function saveCard('),
  ctx,{filename:'internal-names-ui.js'});
assert(ctx.searchText(card).includes('ved den fiktive skole'));
ctx.query='fiktive skole';
assert(ctx.matches(card),'search matches private name');
ctx.query='b07';
assert(ctx.matches(card),'search still matches internal number');
ctx.query='fiktiv syd';
assert(ctx.matches(card),'search still matches public name');
ctx.query='';
const table=ctx.table([card]);
assert(table.includes('Internt navn:'),'list includes internal name label');
assert(table.includes('&lt;script&gt;'),'internal name is HTML escaped');
assert(!table.includes('<script>'),'private name cannot inject HTML');
assert(ctx.details(card).includes('Ved den fiktive skole'),'card details show name');
assert(ctx.folderCardPickerRows('fiktive skole').includes('Ved den fiktive skole'),
  'folder picker supports searching and showing internal name');
ctx.editCard(card.id);
assert(dialogHTML.includes('name="internal_name"'));
assert(dialogHTML.includes('maxlength="160"'));
assert(dialogHTML.includes('Fiktiv syd'),'the official name is not replaced');
assert.equal(ctx.cardFormData().internal_name,'Lokalt områdenavn');
assert(!section('function frontHTML(c)','function backHTML(').includes('internal_name'),
  'public card front never interpolates the internal label');
console.log('Internal names: administrative rendering, search, card picker, editor and escaping OK');
