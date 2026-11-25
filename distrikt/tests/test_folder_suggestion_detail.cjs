'use strict';
// Fictional cards and DOM stubs only. No installation data or network writes.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const elements=new Map(),scrolls=[],calls=[];
const c={console,Date,Intl,Number,String,Math,Map,Set,JSON,Array,Object,Promise,setTimeout(){},clearTimeout(){},
 window:{addEventListener(){},scrollX:12,scrollY:480,scrollTo(value){scrolls.push(value);}},
 document:{getElementById:id=>elements.get(id)||{addEventListener(){}},querySelectorAll(){return [];},addEventListener(){},querySelector(){return {content:'FICTIONAL'};}},
 AdminUI:{selected:new Set()},calls};
vm.createContext(c);vm.runInContext(read('i18n.js'),c);
const source=read('app.js');vm.runInContext(source.slice(0,source.indexOf('(async()=>{try{await refresh();')),c);
vm.runInContext(read('profiles-ui.js'),c);
const run=s=>vm.runInContext(s,c);
run(`page='Udlevering';deskTab='Udlever';query='fictional';area='area-1';selected='inside';
 state={today:'2026-11-25',cards:[
 {id:'inside',number:'1',kind:'By',in_folder:true,addresses:[]},
 {id:'box&2',number:'<2>',kind:'By',in_folder:false,addresses:[]},
 {id:'issued',number:'3',kind:'By',in_folder:false,addresses:[]},
 {id:'blocked',number:'4',kind:'By',front_revision:true,in_folder:false,addresses:[]}
 ],loans:[{id:'fictional-loan',card_id:'issued'}],areas:[],settings:{folder_minimum:2,require_revision:true},
 profile:{desk_only:false,permissions:['cards.view','loans.view']}};
 detail=(...args)=>calls.push(args);
`);
for(const lang of ['da','en']){
 run(`I18n.set('${lang}')`);
 const html=run('FolderSuggestions.buttons(folderPlan().picked)');
 assert.match(html,/type="button"/);
 assert.match(html,/data-action="folder-suggestion-detail" data-id="box&amp;2"/);
 assert.match(html,/&lt;2&gt;/);
 assert.doesNotMatch(html,/data-id="issued"|data-id="blocked"|data-id="inside"/);
}
let focused=false;c.opener={focus(options){focused=options.preventScroll;},dataset:{action:'folder-suggestion-detail'}};
run("FolderSuggestions.open('box&2',opener)");
assert.equal(focused,true);assert.equal(calls.length,1);assert.equal(calls[0][0],'box&2');assert.equal(calls[0][1],'Kort');assert.equal(calls[0][2].keepSelection,true);
assert.equal(run('selected'),'inside');assert.equal(run('query'),'fictional');assert.equal(run('area'),'area-1');assert.equal(run('deskTab'),'Udlever');
run("FolderSuggestions.open('issued',opener);FolderSuggestions.open('missing',opener);state.profile.permissions=['loans.view'];FolderSuggestions.open('box&2',opener)");
assert.equal(calls.length,1);
assert.doesNotMatch(run('FolderSuggestions.buttons(folderPlan().picked)'),/data-action=/);
run("state.profile.permissions=['cards.view','loans.view'];state.profile.desk_only=true;FolderSuggestions.open('box&2',opener);state.profile.desk_only=false;state.settings.folder_enabled=false;FolderSuggestions.open('box&2',opener);state.settings.folder_enabled=true");
assert.equal(calls.length,1);
elements.set('dialog',{open:true,addEventListener(){}});
run('DialogFocus.opener={node:opener}');
assert.equal(run('FolderSuggestions.fromDialog()'),true);
elements.get('dialog').open=false;
assert.equal(run('FolderSuggestions.fromDialog()'),false);
let details={open:false},summary={dataset:{deskTab:'Udlever'},querySelector:()=>details};
elements.set('app',{querySelector:()=>summary});
run('var snapshot=FolderSuggestions.capture()');
details={open:true};run('FolderSuggestions.restore(snapshot)');
assert.equal(details.open,false);assert.equal(scrolls.length,1);assert.equal(scrolls[0].top,480);assert.equal(scrolls[0].left,12);
run("deskTab='Aflever';FolderSuggestions.restore(snapshot)");
assert.equal(scrolls.length,1);assert.equal(run('FolderSuggestions.capture()'),null);
run("deskTab='Udlever';state.cards.find(c=>c.id==='box&2').in_folder=true");
assert.equal(run('folderPlan().need'),0);assert.equal(run('FolderSuggestions.buttons(folderPlan().picked)'),'');
console.log('Folder suggestions: fictional eligible cards, escaping, standard detail delegation, permissions, context, scroll and refreshed proposal list.');
