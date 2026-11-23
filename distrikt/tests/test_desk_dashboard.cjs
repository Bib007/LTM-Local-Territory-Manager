// Fictional projection and DOM stubs only: no private installation is read.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const source=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const elements={
 profileUser:{elements:{entityId:{value:'fictional-user'}}},
 profileRoles:{querySelectorAll:()=>[{value:'fictional-desk'},{value:'fictional-extra'}]},
 profileEffectiveRights:{innerHTML:''},
 profileGuideAssignment:{innerHTML:''},
};
const ctx={
 document:{addEventListener(){}},
 window:{},
 el:name=>elements[name]||null,
 I18n:{language:()=> 'da',fixedLanguage:()=>true,text:text=>text},
 ui:(value,params={})=>String(value).replace(/\{(\w+)\}/g,(_,k)=>String(params[k]??'{'+k+'}')),
 esc:value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;'),
 serviceYear:()=>2027,yearLabel:()=> '2026/2027',
};
vm.createContext(ctx);
for(const name of ['workspace.js','profiles-ui.js','navigation.js'])
 vm.runInContext(source(name),ctx,{filename:name});

vm.runInContext(`var page='Forside',state={
 today:'2026-11-17',
 settings:{},
 profile:{
  desk_only:true,
  user:{id:'fictional-user',name:'Fiktiv bruger',onboarded:true},
  permissions:['cards.view','loans.view','loans.manage','publishers.view','dashboard.view']
 },
 dashboard_summary:{as_of:'2026-11-17',revision:'fictional-revision',
  periods:{service:{territories:5,assigned:2,home:3,completed_territories:3,completions:8}}}
};`,ctx);

const evalJS=s=>vm.runInContext(s,ctx);
assert.equal(evalJS("ProfilesUI.has('dashboard.view')"),true);
assert.equal(evalJS("ProfilesUI.pageAllowed('Forside')"),true);
for(const page of ['Opgaver','Opfølgninger','Rapporter','Adresser','Kortoversigt'])
 assert.equal(evalJS(`ProfilesUI.pageAllowed('${page}')`),false,page);
const html=evalJS('Workspace.dashboard()');
for(const value of ['Tjenesteår','Kortenes placering','Dækning i tjenesteåret','Gennemgange i tjenesteåret','Aktuelle distrikter'])
 assert.ok(html.includes(value),value);
for(const value of ['>2</strong>','>3</strong>','>5</strong>','>8</strong>','>60%</strong>'])
 assert.ok(html.includes(value),value);
assert.doesNotMatch(html,/opfølgning|data-work="tasks"|data-work="followups"|taskMetric|recurringTasks|note\.save/i);
assert.doesNotMatch(evalJS('Navigation.html()'),/Opgaver|Opfølgninger|Rapporter|Kortoversigt/);
assert.equal(evalJS('Workspace.myTasksWelcome(7)'),'');
assert.equal(evalJS('ProfilesUI.welcome()').includes('Se mine opgaver'),false);

vm.runInContext(`ProfilesUI.admin={
 users:[{id:'fictional-user'}],
 roles:[{id:'fictional-desk',desk_only:true,permissions:[]},
        {id:'fictional-extra',permissions:['notes.view','ib.view','reports.view']}]
};`,ctx);
evalJS('ProfilesUI.userExtras()');
assert.match(elements.profileEffectiveRights.innerHTML,/Se forsidestatus/);
assert.doesNotMatch(elements.profileEffectiveRights.innerHTML,/Se opgaver|Se IB|Se rapportoversigt/);
vm.runInContext(`state={
  ...state,
  profile:{...state.profile,desk_only:false,user:{id:'fictional-recipient',name:'Fiktiv modtager'},permissions:['notes.view','dashboard.view']},
  notes:[{id:'fictional-task',text:'Fiktiv <opgave>',task_history:[
   {id:'unread-1',reply:'Svar <ikke HTML>',recipient_self:true,read:false,author:'Fiktiv afsender'},
   {id:'already-read',reply:'Gammelt svar',recipient_self:true,read:true},
   {id:'other-user',reply:'Privat svar',read:false}
  ]}]
};`,ctx);
const replyNotice=evalJS('Workspace.replyNotifications()');
assert.match(replyNotice,/Nye svar på dine opgaver/);
assert.match(replyNotice,/1 ulæste svar/);
assert.match(replyNotice,/data-work="read-task-reply"/);
assert.match(replyNotice,/data-work="task-replies"/);
assert.match(replyNotice,/Fiktiv &lt;opgave>/);
assert.match(replyNotice,/Svar &lt;ikke HTML>/);
assert.doesNotMatch(replyNotice,/Gammelt svar|Privat svar/);
assert.match(evalJS('Workspace.taskHistory(state.notes[0],false)'),/data-work="read-task-reply"/);
vm.runInContext('state.notes[0].task_history[0].read=true',ctx);
assert.equal(evalJS('Workspace.replyNotifications()'),'');
assert.doesNotMatch(evalJS('Workspace.taskHistory(state.notes[0],false)'),/data-work="read-task-reply"/);
vm.runInContext("state.profile.permissions=['dashboard.view']",ctx);
assert.equal(evalJS('Workspace.replyNotifications()'),'');
console.log('Restricted desk and recipient-only task reply notifications verified with fictional data.');
