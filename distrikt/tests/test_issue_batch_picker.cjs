// Exercise the real batch-picker functions with fictional cards and no server.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../app/app.js'),'utf8');
const start=source.indexOf('function issueCardLabel('),end=source.indexOf("function issue(id='',initial=false)",start);
assert(start>=0&&end>start);
const cards=[
 {id:'a',number:'101',name:'Fiktiv Nord',in_folder:true},
 {id:'b',number:'102',name:'Fiktiv Syd',in_folder:true},
 {id:'c',number:'103',name:'Fiktiv Vest',internal_number:'I003',in_folder:true},
 {id:'d',number:'104',name:'Fiktiv Øst',in_folder:true},
 {id:'e',number:'105',name:'Fiktiv Midt',in_folder:true},
 {id:'f',number:'106',name:'Fiktiv Ekstra',in_folder:true},
 {id:'g',number:'107',name:'Fiktiv Udleveret',in_folder:true},
 {id:'h',number:'108',name:'Fiktiv Kasse',in_folder:false},
 {id:'i',number:'109',name:'Fiktiv Print',in_folder:true,front_revision:true},
 {id:'j',number:'110',name:'Fiktiv Arkiv',in_folder:true,archived:true},
 {id:'k',number:'111',name:'Fiktiv <test>',in_folder:true}
];
const state={cards,settings:{require_revision:true},loans:[{card_id:'g'}]};
function node(value=''){
 const handlers={};
 return {value,innerHTML:'',textContent:'',hidden:false,focused:false,
  addEventListener(type,fn){handlers[type]=fn;},
  fire(type,event={}){handlers[type](event);},
  focus(){this.focused=true;},
  querySelector(){return this.innerHTML.includes('data-issue-add=')?{focus:()=>{this.focused=true;}}:null;}
 };
}
const primary=node('a'),search=node(),picker=node(),selected=node(),count=node(),warning=node();
const nodes={issueExtraCard:picker,issueSelectedCards:selected,issueSelectedCount:count,issueTaskWarning:warning};
const form={elements:{namedItem:()=>primary}};
const fixture={state,areaName:()=> 'Fiktiv område',loanFor:id=>state.loans.find(l=>l.card_id===id),
 folderEnabled:()=>state.settings.folder_enabled!==false,el:id=>nodes[id],
 esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;'),
 ui:s=>s,cmp:(a,b)=>a.localeCompare(b),I18n:{format:(s,o)=>s.replace('{count}',o.count),attribute:()=>''},
 taskWarning:id=>id==='b'?'Fiktiv opgave':''};
const functions=new Function('f','const {state,areaName,loanFor,folderEnabled,el,esc,ui,cmp,I18n,taskWarning}=f;'+source.slice(start,end)+';return {issueBatchPicker,issueCardOptions};')(fixture);
functions.issueBatchPicker(form,search,false);
const includes=id=>picker.innerHTML.includes('data-issue-add="'+id+'"');
const extras=()=>[...selected.innerHTML.matchAll(/name="additional_card_id" value="([^"]+)"/g)].map(m=>m[1]);
const pick=id=>picker.fire('click',{target:{closest:()=>({dataset:{issueAdd:id}})}});
const find=s=>{search.value=s;search.fire('input');};
const remove=id=>selected.fire('click',{target:{closest:()=>({dataset:{issueRemove:id}})}});
assert.equal(count.textContent,'1 af 5 kort valgt');
assert(picker.hidden&&picker.innerHTML==='','No results until a deliberate search');
find('   ');assert(picker.hidden);
find('Fiktiv');assert(!picker.hidden&&includes('b')&&includes('f')&&includes('k'));
assert(!['a','g','h','i','j'].some(includes));
assert(picker.innerHTML.includes('&lt;test&gt;'));
assert(picker.innerHTML.includes('<button type="button"'),'Results are native non-submit buttons');
assert(functions.issueCardOptions([cards[1]]).includes('<option'),'Primary select is unchanged');
find('no-match');assert(!picker.hidden&&picker.innerHTML.includes('Ingen ledige kort matcher.'));
let prevented=false;
search.fire('keydown',{key:'Enter',preventDefault(){prevented=true;}});
assert(prevented,'No implicit form submission even with no matches');
find('sYD');assert(includes('b')&&!includes('c'));
prevented=false;search.fire('keydown',{key:'ArrowDown',preventDefault(){prevented=true;}});
assert(prevented&&picker.focused,'Keyboard can move from search to a result');
pick('b');assert.deepEqual(extras(),['b']);assert(warning.innerHTML.includes('Fiktiv opgave'));
assert(search.value===''&&search.focused&&picker.hidden,'Click/tap resets results for the next search');
find('I003');assert(includes('c')&&!includes('b'));pick('c');
find('104');assert(includes('d'));pick('d');
find('105');pick('e');assert.equal(count.textContent,'5 af 5 kort valgt');
find('106');assert(picker.hidden);pick('f');pick('b');pick('a');assert.deepEqual(extras(),['b','c','d','e']);
remove('c');assert(!picker.hidden&&search.focused&&includes('f'));pick('f');
primary.value='b';primary.fire('change');assert.deepEqual(extras(),['d','e','f']);find('Fiktiv');assert(!includes('b'));
state.loans.push({card_id:'d'});find('Fiktiv');assert(!includes('d'));assert(extras().includes('d'),'Do not silently drop a conflicting selected card');assert(selected.innerHTML.includes('Kan ikke vælges'));
remove('d');assert.deepEqual(extras(),['e','f']);
find('103');assert(includes('c'));state.loans.push({card_id:'c'});pick('c');
assert.deepEqual(extras(),['e','f'],'Recheck eligibility on click');assert(picker.innerHTML.includes('Ingen ledige kort matcher.'));
find('Fiktiv');assert(!includes('e')&&!includes('f')&&!includes('b'));
console.log('Batch picker: deliberate search, result buttons, keyboard, no matches, escaping, removal, cap, duplicates and stale selection passed.');
