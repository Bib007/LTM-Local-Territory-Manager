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
 I18n:{language:()=> 'da'},areaName:()=> 'Fiktivt område',
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
assert.match(html,/1 · Udleveret/);
assert.match(html,/2 · Indleveret/);
assert.ok(html.indexOf('01.08.2026')<html.indexOf('10.10.2026'));
assert.match(html,/Hele historikken \(2 udleveringer · 1 gennemgange\)/);
assert.match(html,/Fiktiv A/);
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
console.log('history-grid fictional UI contracts passed');
