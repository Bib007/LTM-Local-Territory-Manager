'use strict';
// Isolated VM regression for the daily-use folder picker; all cards are fictional.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const app=fs.readFileSync(path.join(__dirname,'../app/app.js'),'utf8');
const admin=fs.readFileSync(path.join(__dirname,'../app/admin.js'),'utf8');
const section=(start,end)=>{
 const first=app.indexOf(start),last=app.indexOf(end,first+start.length);
 assert(first>=0&&last>first,'Missing real picker/event source: '+start);
 return app.slice(first,last);
};
const picker=section(' // Select existing cards only.','\nfunction deskReturns(){');
const events=section("document.addEventListener('input',",'\nasync function loadMap()');
const clickHandler=section("document.addEventListener('click',async event=>", "\ndocument.addEventListener('submit',");
const adminUI=admin.slice(0,admin.indexOf("document.addEventListener('change'"));
assert(adminUI.endsWith('};\n'),'Missing standalone AdminUI');
const nodes={
 dialog:{innerHTML:''},folderCardMatches:{innerHTML:''},
 folderCardFooter:{innerHTML:''},folderCardSearch:{value:''},
};
const listeners={};
const state={
 revision:1,areas:[{id:'n',name:'Fiktivt nord'}],
 cards:[
  {id:'a',number:'F101',name:'Fiktiv alfa',area_id:'n',in_folder:false},
  {id:'b',number:'F102',name:'Fiktiv beta',area_id:'n',in_folder:false},
  {id:'c',number:'F103',name:'Fiktiv udlånt',area_id:'n',in_folder:false},
  {id:'d',number:'F104',name:'Fiktiv i mappen',area_id:'n',in_folder:true},
 ],
 loans:[{id:'loan',card_id:'c',returned:null}],
};
const fixture={
 state,
 I18n:{language:()=> 'da',text:value=>value,attribute:(name,key)=>'aria-label="'+key+'"'},
 ui:(value,params)=>String(value).replace(/\{(\w+)\}/g,(_,key)=>params?.[key]??''),
 esc:value=>String(value??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
 cmp:(a,b)=>String(a).localeCompare(String(b)),
 areaName:id=>state.areas.find(a=>a.id===id)?.name||'Intet område',
 loanFor:id=>state.loans.find(loan=>loan.card_id===id&&!loan.returned),
 card:id=>state.cards.find(c=>c.id===id),
 el:id=>nodes[id],
 openDialog(html){nodes.dialog.innerHTML=html;},
 render(){fixture.renderCount=(fixture.renderCount||0)+1;},
 toast(message){fixture.toastMessage=message;},
 RequestError:class RequestError extends Error{},
 document:{addEventListener(name,handler){listeners[name]=handler;}},
 mutate:async()=>{throw Error('Unexpected write');},
};
const factory=new Function('f',
 'const {state,I18n,ui,esc,cmp,areaName,loanFor,card,el,openDialog,render,toast,RequestError,document}=f;\n'+
 "let page='Udlevering',folderCardPickerSelected=new Set(),editMap=false,mapDraft=[],selected='';\n"+
 'const mutate=(...args)=>f.mutate(...args);\n'+adminUI+'\n'+picker+'\n'+events+'\n'+clickHandler+
 '\nreturn {AdminUI,chooseFolderCard,folderCardPickerRows,folderCardPickerFooter,selectedIds:()=>[...folderCardPickerSelected]};'
);
const pickerUI=factory(fixture);
const select=async(id,checked=true)=>{
 const target={dataset:{folderCardId:id},checked,name:''};
 await listeners.change({target});
 return target;
};
const search=value=>{
 nodes.folderCardSearch.value=value;
 listeners.input({target:{id:'folderCardSearch',value}});
 return nodes.folderCardMatches.innerHTML;
};
const click=async action=>{
 const target={dataset:{action},closest:selector=>selector==='[data-action]'?target:null};
 await listeners.click({target,preventDefault(){}});
};
(async()=>{
 pickerUI.chooseFolderCard();
 assert.match(nodes.dialog.innerHTML,/id="folderCardFooter"/);
 assert.match(nodes.dialog.innerHTML,/data-action="folder-card-preview" disabled/);
 assert.match(pickerUI.folderCardPickerRows(''),/data-folder-card-id="c"[^>]*disabled/);
 assert.match(pickerUI.folderCardPickerRows(''),/data-folder-card-id="d"[^>]*disabled/);
 assert.equal((await select('c')).checked,false,'Issued card cannot be selected');
 assert.deepEqual(pickerUI.selectedIds(),[]);

 await select('a');
 assert.match(search('beta'),/data-folder-card-id="b"/);
 await select('b');
 assert.match(search('alfa'),/data-folder-card-id="a"[^>]*checked/);
 assert.deepEqual(pickerUI.selectedIds(),['a','b'],'Search must preserve hidden selections');
 assert.match(nodes.folderCardFooter.innerHTML,/Læg 2 i mappen/);
 assert.match(search('ingen-kort'),/Ingen eksisterende kort matcher/);
 assert.deepEqual(pickerUI.selectedIds(),['a','b']);

 pickerUI.AdminUI.selected=new Set(['a']); // inventory selection must remain independent
 await click('folder-card-preview');
 assert.deepEqual([...pickerUI.AdminUI.folderPending.ids],['a','b']);
 assert.match(nodes.dialog.innerHTML,/Bekræft og læg 2 i mappen/);

 let resolve,mutations=0,request;
 fixture.mutate=(action,data,options)=>{
  mutations++;request={action,data,options};
  return new Promise(r=>{resolve=r;});
 };
 const first=pickerUI.AdminUI.folderConfirm();
 const second=pickerUI.AdminUI.folderConfirm(); // double click while pending
 assert.equal(mutations,1);
 state.cards[0].in_folder=true;
 state.loans.push({id:'another-user',card_id:'b',returned:null}); // concurrent issuance
 resolve({count:1,updated:['a'],skipped:[{id:'b',reason:'Kortet blev udleveret samtidigt.'}]});
 await Promise.all([first,second]);
 assert.equal(request.action,'folder.set_many');
 assert.deepEqual([...request.data.ids],['a','b']);
 assert.equal(request.data.in_folder,true);
 assert.equal(request.data.expected_in_folder,false);
 assert.equal(request.options.close,false);
 assert.match(nodes.dialog.innerHTML,/1 kort lagt i mappen/);
 assert.match(nodes.dialog.innerHTML,/1 kort ikke ændret/);
 assert.match(nodes.dialog.innerHTML,/Kortet blev udleveret samtidigt/);
 assert(pickerUI.AdminUI.selected.has('a'),'Picker must not change inventory selection');
 assert.equal(state.loans[0].id,'loan','Existing loan history must remain');
 assert.equal(fixture.renderCount,1);

 pickerUI.chooseFolderCard();
 assert.deepEqual(pickerUI.selectedIds(),[],'New picker starts with an empty selection');
 state.cards[0].in_folder=false;
 await select('a');
 assert.match(nodes.folderCardFooter.innerHTML,/Læg 1 i mappen/);
 await click('folder-card-clear');
 assert.deepEqual(pickerUI.selectedIds(),[]);
 assert.match(nodes.folderCardFooter.innerHTML,/data-action="folder-card-preview" disabled/);
 console.log('Daily folder picker: cross-search selection, blocked cards, bulk preview, double click, concurrent partial rejection, inventory isolation and reset passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
