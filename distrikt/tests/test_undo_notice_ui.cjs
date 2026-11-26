'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

const state={revision:'fictional-1',undo_available:true,undo_action:'loan.issue',profile:{desk_only:true}};
const writes=[],listeners={};
let html=[],removed=0,confirmed=0,language='da';
const app={
 insertAdjacentHTML(where,markup){html.unshift(markup);},
 querySelector(selector){return selector==='.undoBar'&&html.some(s=>s.includes('class="undoBar"'))?{remove(){removed++;html=html.filter(s=>!s.includes('class="undoBar"'));}}:null;}
};
const ctx={state,page:'Forside',document:{addEventListener:(name,fn)=>{listeners[name]=fn;}},
 window:{requestAnimationFrame(){},confirm(){confirmed++;return true;}},
 el:id=>id==='app'?app:null,openDialog:{generation:0},
 ui:key=>key,esc:value=>String(value),I18n:{attribute:(kind,key)=>(kind==='aria'?'aria-label':kind)+'="'+(language==='en'&&key==='Luk'?'Close':key)+'"',text:key=>key},
 PendingSaves:{count:0},WriteGuard:{uncertain:false,needsReview:false,loginExpired:false},
 mutate:async(action,data)=>writes.push({action,revision:data.expected_revision}),
 toast(error){throw error;}
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/workspace.js'),'utf8')+';this.workspace=Workspace;',ctx);
const w=ctx.workspace;
const render=page=>{ctx.page=page;html=[];w.afterRender();return html.find(s=>s.includes('class="undoBar"'))||'';};
const click=(work,revision)=>listeners.click({target:{closest:()=>({dataset:{work,revision}})},preventDefault(){}});

(async()=>{
 assert.equal(render('Forside'),'');
 assert.match(render('Udlevering'),/Fortryd udlevering/);
 assert.match(render('Opgaver'),/data-revision="fictional-1"/);
 assert.equal(render('Forside'),'');
 assert.match(render('Udlevering'),/data-work="dismiss-undo"/);
 assert.match(w.undoNotice(),/aria-label="Luk"/);
 language='en';assert.match(w.undoNotice(),/aria-label="Close"/);
 await click('dismiss-undo','fictional-1');
 assert.equal(removed,1);assert.equal(w.undoNotice(),'');
 assert.equal(state.undo_available,true);assert.equal(state.revision,'fictional-1');
 assert.equal(writes.length,0);assert.equal(confirmed,0);
 assert.equal(render('Opgaver'),'');assert.equal(render('Forside'),'');assert.equal(render('Udlevering'),'');
 state.revision='fictional-2';state.undo_action='loan.finish';
 assert.match(render('Udlevering'),/Fortryd aflevering eller gennemgang/);
 await click('dismiss-undo','fictional-1');
 assert.match(w.undoNotice(),/fictional-2/);assert.equal(removed,1);
 await click('undo','fictional-1');assert.equal(writes.length,0);
 ctx.WriteGuard.uncertain=true;
 await click('undo','fictional-2');assert.equal(writes.length,0);
 ctx.WriteGuard.uncertain=false;
 await click('undo','fictional-2');
 assert.deepEqual(writes,[{action:'workflow.undo',revision:'fictional-2'}]);assert.equal(confirmed,1);
 state.undo_available=false;assert.equal(render('Udlevering'),'');
 state.undo_available=true;state.revision='fictional-3';state.undo_action='note.save';
 assert.match(render('Opgaver'),/Fortryd sidste handling/);
 console.log('Undo notice navigation, dismissal, next revision and guarded undo passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
