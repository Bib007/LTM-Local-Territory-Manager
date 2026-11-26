'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const file=require('node:path').join(__dirname,'..','app','history-grid.js');
const listeners={};
const source=fs.readFileSync(file,'utf8');
const state={
 today:'2026-11-11',profile:null,undo_available:false,
 cards:[{id:'c1',number:'01',name:'Fiktivt kort',area_id:'a1',in_folder:false,last_completed:'2026-10-01'}],
 archived_cards:[],publishers:[{id:'p1',name:'Fiktiv A'}],
 completions:[{id:'e1',card_id:'c1',loan_id:'l1',date:'2026-09-01'}],
 loans:[{id:'l1',card_id:'c1',publisher_id:'p1',assigned:'2026-08-01',returned:'2026-09-01'},
        {id:'l2',card_id:'c1',publisher_id:'p1',assigned:'2026-10-10',returned:null}]
};
const ctx={state,document:{addEventListener:(key,fn)=>{(listeners[key]??=[]).push(fn);}},
 ProfilesUI:{has:()=>true},Workspace:{loanLine:l=>'<div>'+l.id+'</div>'},
 I18n:{language:()=> 'da'},ui:(key,params={})=>key.replace(/\{(\w+)\}/g,(_,name)=>String(params[name]??'')),areaName:()=> 'Fiktivt område',
 publisherName:id=>state.publishers.find(p=>p.id===id)?.name||'Ukendt',
 cmp:(a,b)=>String(a).localeCompare(String(b),'da'),
 esc:value=>String(value??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])),
 Date,console};
vm.createContext(ctx);
vm.runInContext(source+';this.__grid=HistoryGrid;',ctx);
const grid=ctx.__grid;
assert.equal(grid.dateText('2026-11-01'),'01.11.2026');
assert.equal(grid.parseDate('1.11.2026',true),'2026-11-01');
assert.equal(grid.parseDate('2026-11-01',true),'2026-11-01');
assert.equal(grid.parseDate('',false),null);
for(const raw of ['31.02.2026','12.11.2026','01.01.1899','1/2/26','not-a-date']){
 assert.throws(()=>grid.parseDate(raw,true));
}
const html=grid.render();
assert.match(html,/Gennemgange & historik/);
assert.match(html,/Forrige udlevering/);
assert.match(html,/Seneste udlevering/);
assert.match(html,/class="hg-list"/);
assert.match(html,/class="hg-card/);
assert.match(html,/class="hg-periods"/);
assert.match(html,/class="hg-fields"/);
assert.match(html,/class="hg-card-actions"/);
assert.doesNotMatch(html,/<table|class="hg-scroll"/,'History is a card list, not a horizontally scrolling table');
assert.match(html,/<details class="hg-details">/,'All history is collapsed until opened');
assert.doesNotMatch(html,/<details open/);
assert.match(html,/data-hg-id="l1" data-hg-field="assigned"/);
assert.match(html,/data-hg-id="l2" data-hg-field="returned"/);
assert.match(html,/data-hg-add="c1"/);
assert.match(html,/data-history-import="open"/);
assert.match(html,/data-action="backup"/);
assert.ok(html.indexOf('01.08.2026')<html.indexOf('10.10.2026'));
assert.match(html,/Hele historikken \(2 udleveringer · 1 gennemgange\)/);
assert.match(html,/Fiktiv A/);
assert.match(html,/Udleveret · Fiktiv A/);
assert.ok(html.indexOf('01.08.2026')<html.indexOf('10.10.2026'));
assert.ok(html.indexOf('Forrige udlevering')<html.indexOf('Seneste udlevering'));
state.cards.push({id:'c2',number:'02',name:'Kort uden udlevering',area_id:'a1',in_folder:true});
assert.match(grid.row(state.cards[1]),/Ingen udleveringer registreret endnu/);
assert.match(grid.row(state.cards[1]),/data-hg-add="c2"/);
state.cards.pop();
state.archived_cards.push({id:'old',number:'99',name:'Arkiveret',archived:true,area_id:'a1'});
const archived=grid.row(state.archived_cards[0]);
assert.match(archived,/Arkiveret/);assert.doesNotMatch(archived,/data-hg-add/);
state.archived_cards.pop();
state.loans.push({id:'l0',card_id:'c1',publisher_id:'p1',assigned:'2026-01-01',returned:'2026-02-01'});
const multiple=grid.row(state.cards[0]);
assert.equal((multiple.match(/class="hg-period"/g)||[]).length,2,'Only two most recent assignment periods visible');
assert.match(multiple,/3 udleveringer/);
assert.match(multiple,/l0/,'Older assignment remains in the full history');
state.loans.pop();
state.cards[0].name='Fiktivt <script>';
assert.match(grid.row(state.cards[0]),/Fiktivt &lt;script&gt;/);
state.cards[0].name='Fiktivt kort';
grid.filter='active';
assert.equal(grid.visible().length,1);
grid.filter='empty';
assert.equal(grid.visible().length,0);
grid.filter='all';
grid.query='ikke et kort';
assert.equal(grid.visible().length,0);
grid.query='fiktivt';
assert.equal(grid.visible().length,1);
assert.ok(listeners.input?.length&&listeners.change?.length&&listeners.keydown?.length);
const css=fs.readFileSync(require('node:path').join(__dirname,'../app/history-grid.css'),'utf8');
assert.match(css,/grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
assert.match(css,/@media\(max-width:640px\)/);
assert.match(css,/\.hg-fields\{grid-template-columns:1fr/,'Date fields stack on phones');
assert.doesNotMatch(css,/min-width:970px|overflow-x:scroll/,'No forced horizontal scrolling');
let formMarkup;
ctx.openDialog=markup=>{formMarkup=markup;};
grid.openAdd('c1');
assert.match(formMarkup,/<input type="checkbox" name="completed" checked>/,'New history defaults to a completion');

ctx.FormData=function(form){return Object.entries(form.values);};
const writes=[];
ctx.mutate=async(action,data)=>{writes.push({action,data});};
(async()=>{
 for(const [returned,checked,expected] of [['01.07.2026',true,true],['01.07.2026',false,false],['',true,false]]){
  const form={dataset:{hgCard:'c1'},values:{publisher_id:'p1',assigned:'01.06.2026',returned},
   querySelector:()=>({checked})};
  await grid.submit(form);
  const write=writes.at(-1);
  assert.equal(write.action,'history.grid.add');
  assert.equal(write.data.completed,expected);
  assert.equal(write.data.returned,returned?'2026-07-01':null);
 }
 console.log('History UI: rendering, editing and completion defaults passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
