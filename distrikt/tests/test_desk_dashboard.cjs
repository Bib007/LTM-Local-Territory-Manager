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
 openDialog(html,language){elements.statsDialog={html,language};},
 el:name=>elements[name]||null,
 ui:(value,params={})=>String(value).replace(/\{(\w+)\}/g,(_,k)=>String(params[k]??'{'+k+'}')),
 esc:value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;'),
 cmp:(a,b)=>String(a).localeCompare(String(b)),
 fmt:value=>String(value),
 serviceYear:()=>2027,yearLabel:()=> '2026/2027',dayDiff:(a,b)=>(Date.parse(a)-Date.parse(b))/86400000,
};
vm.createContext(ctx);
for(const name of ['i18n.js','workspace.js','profiles-ui.js','navigation.js'])
 vm.runInContext(source(name),ctx,{filename:name});

vm.runInContext(`var page='Forside',state={
 today:'2026-11-17',
 settings:{},loans:[],completions:[],cards:[],
 profile:{
  desk_only:true,language:'da',
  user:{id:'fictional-user',name:'Fiktiv bruger',onboarded:true},
  permissions:['cards.view','loans.view','loans.manage','publishers.view','dashboard.view']
 },
 dashboard_summary:{as_of:'2026-11-17',revision:'fictional-revision',
  periods:{service:{territories:5,assigned:2,home:3,completed_territories:3,completions:8,missing:2,missing_assigned:1,missing_home:1}},
  territory_totals:{visit_points:62,unknown_visit_cards:1,complete_visit_points:60,temporary_cards:1,ib_total:4,ib_on_current_cards:3,cards_with_ib:2}}
};`,ctx);

const evalJS=s=>vm.runInContext(s,ctx);
assert.equal(evalJS("ProfilesUI.has('dashboard.view')"),true);
assert.equal(evalJS("ProfilesUI.pageAllowed('Forside')"),true);
for(const page of ['Opgaver','Opfølgninger','Rapporter','Adresser','Kortoversigt'])
 assert.equal(evalJS(`ProfilesUI.pageAllowed('${page}')`),false,page);
const html=evalJS('Workspace.dashboard()');
assert.match(html,/data-dashboard-layout="compact-summary"/);
assert.match(html,/data-work="dashboard-stats" aria-haspopup="dialog"/);
evalJS('Workspace.moreStats()');
assert.match(elements.statsDialog.html,/<h2>Flere statistikker<\/h2>/);
assert.match(elements.statsDialog.html,/Gennemsnitligt antal besøg pr\. kort<\/dt><dd>15<\/dd>/);
assert.match(elements.statsDialog.html,/Antal kendte besøg<\/dt><dd>62<\/dd>/);
assert.doesNotMatch(elements.statsDialog.html,/Antal IB|Kort med mindst én IB/);
evalJS("state.profile.permissions.push('ib.view')");
evalJS('Workspace.moreStats()');
assert.match(elements.statsDialog.html,/Antal IB<\/dt><dd>4<\/dd>/);
assert.match(elements.statsDialog.html,/Gennemsnitlige IB pr\. aktuelt kort<\/dt><dd>0,6<\/dd>/);
evalJS("state.profile.permissions.pop()");
assert.doesNotMatch(html,/data-work="dashboard-popularity"/);
evalJS('Workspace.openPopularity()');
assert.match(elements.statsDialog.html,/<h2>Flere statistikker<\/h2>/);
evalJS(`state.profile.permissions.push('history.view');
 state.cards=[{id:'a',number:'101',name:'Fiktiv <vej>'},{id:'b',number:'102'},{id:'zero',number:'103'}];
 state.loans=[
  {id:'l1',card_id:'a',assigned:'2026-09-01',returned:'2026-09-04'},
  {id:'l2',card_id:'b',assigned:'2026-09-05',returned:'2026-09-12'},
  {id:'l3',card_id:'b',assigned:'2026-09-15'},
  {id:'old',card_id:'zero',assigned:'2025-10-01',returned:'2025-10-02'},
  {id:'archived',card_id:'removed',assigned:'2026-11-01'},
  {id:'future',card_id:'zero',assigned:'2026-12-01'}
 ];
 state.completions=[
  {card_id:'a',loan_id:'l1',date:'2026-09-04'},
  {card_id:'a',date:'2026-10-10'},
  {card_id:'b',date:'2026-09-10'},
  {card_id:'removed',date:'2026-11-01'},
  {card_id:'zero',date:'2026-12-01'}
 ];
 state.dashboard_summary.periods.rolling={...state.dashboard_summary.periods.service,start:'2025-11-17',end:state.today};
 state.dashboard_summary.periods.service.start='2026-09-01';
 state.dashboard_summary.periods.service.end=state.today;`);
assert.match(evalJS('Workspace.dashboardStatsActions()'),/data-work="dashboard-popularity"/);
evalJS('Workspace.openPopularity()');
const most=elements.statsDialog.html;
assert.match(most,/<h2>Popularitet af distriktskort<\/h2>/);
assert.match(most,/Fiktiv &lt;vej>/);
assert.match(most,/<strong>2<\/strong><small>0,17 pr\. måned<\/small>/);
assert.match(most,/<strong>0<\/strong><small>0 pr\. måned<\/small>/);
assert.ok(most.indexOf('scope="row">101')<most.indexOf('scope="row">102'));
const least=evalJS("Workspace.popularityResults('service','issues','least')");
assert.ok(least.indexOf('scope="row">103')<least.indexOf('scope="row">101'));
assert.ok(least.indexOf('scope="row">101')<least.indexOf('scope="row">102'));
assert.match(least,/aria-sort="ascending">Udleveringer/);
elements.popularityPeriod={value:'rolling'};
elements.popularityMetric={value:'issues'};
elements.popularityOrder={value:'most'};
elements.popularityResults={};
evalJS('Workspace.updatePopularity()');
assert.ok(elements.popularityResults.innerHTML.indexOf('scope="row">102')<elements.popularityResults.innerHTML.indexOf('scope="row">101'));
evalJS('Workspace.moreStats()');
assert.match(elements.statsDialog.html,/Tid fra udlevering til aflevering<\/dt><dd>5 dage i gennemsnit/);
assert.match(elements.statsDialog.html,/Tid fra udlevering til aflevering med gennemgang<\/dt><dd>3 dage i gennemsnit/);
evalJS("state.profile.permissions.pop()");
assert.match(html,/role="progressbar"[^>]*aria-valuenow="60"/,'Summary progress comes only from aggregate completed/current totals');
assert.match(html,/3 af 5 forskellige kort gennemgået/);
assert.doesNotMatch(html,/dashboardLead|dashboardVisits|data-ui="Gennemgange i tjenesteåret"/,'Summary hides redundant title and completion boxes');
assert.doesNotMatch(html,/dashboardAverageValue|data-work="tasks"/,'Summary role cannot expose restricted history or task controls');
for(const value of ['Kortenes placering','Dækning i tjenesteåret','Aktuelle distrikter'])
 assert.ok(html.includes(value),value);
for(const value of ['>2</strong>','>3</strong>','>5</strong>','>60%</strong>'])
 assert.ok(html.includes(value),value);
assert.doesNotMatch(html,/opfølgning|data-work="tasks"|data-work="followups"|taskMetric|recurringTasks|note\.save/i);
assert.doesNotMatch(evalJS('Navigation.html()'),/Opgaver|Opfølgninger|Rapporter|Kortoversigt/);
// The real translation module supplies tooltip attributes and accessible
// visible names without revealing any navigation forbidden to desk users.
for(const [language,home,desk,publishers,guide,toggle] of [
 ['da','Forside','Ind/udlevering','Forkyndere','Trinvis LTM-guide','Fold menu sammen'],
 ['en','Home','Check-in and check-out','Publishers','Step-by-step LTM guide','Collapse menu']
]){
 evalJS("state.profile.language="+JSON.stringify(language));
 const nav=evalJS('Navigation.html()');
 assert.equal(evalJS('I18n.language()'),language);
 assert.equal(evalJS('I18n.fixedLanguage()'),language);
 assert.doesNotMatch(nav,/id="navigationLanguage"/,'A profile-fixed language must not show the browser picker');
 const buttons=Array.from(nav.matchAll(/<button data-navigation="([^"]+)"[^>]*>[\s\S]*?<\/button>/g),m=>[m[1],m[0]]);
 assert.deepEqual(buttons.map(([id])=>id),['0:0','0:1','1:2'],'Desk role only exposes the three permitted routes');
 for(const [id,label] of [['0:0',home],['0:1',desk],['1:2',publishers]]){
  const button=buttons.find(([key])=>key===id)[1];
  assert.ok(button.includes(' title="'+label+'"'),language+' translated tooltip: '+id);
  assert.ok(button.includes('<span class="sidebarNavLabel">'+label+'</span>'),language+' accessible text: '+id);
 }
 assert.match(buttons[0][1],/aria-current="page"/);
 assert.ok(nav.includes(' title="'+guide+'"'));
 assert.ok(nav.includes('https://localterritorymanager.com/'+language+'/guide/'));
 assert.ok(nav.includes(' title="'+toggle+'"'));
 assert.doesNotMatch(nav,/data-navigation="(?:1:[0134]|2:[012])"/);
}
evalJS("state.profile.language='da'");
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
console.log('Restricted desk navigation, Danish/English tooltips and accessible names, and recipient-only task reply notifications verified with fictional data.');
