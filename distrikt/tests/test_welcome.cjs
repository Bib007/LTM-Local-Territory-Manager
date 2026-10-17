// Guide navigation is read-only and must not appear over an existing database.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const stored=new Map();let opened=[];
const context={console,localStorage:{getItem:k=>stored.get(k),setItem:(k,v)=>stored.set(k,v)},state:{cards:[],publishers:[],loans:[]},document:{addEventListener(){}},openDialog:s=>opened.push(s),closeDialog(){},Number,Math};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/i18n.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/onboarding.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/welcome.js'),'utf8'),context);
const run=s=>vm.runInContext(s,context);
run('Welcome.auto()');assert.equal(opened.length,1);assert.match(opened[0],/Velkommen til LTM/);
opened=[];context.state.cards=[{id:'fictional-existing'}];run('Welcome.auto()');assert.equal(opened.length,0);
context.state.cards=[];context.state.loans=[{id:'fictional-existing'}];run('Welcome.auto()');assert.equal(opened.length,0);
context.state.loans=[];stored.set('ltm-welcome-seen','1');run('Welcome.auto()');assert.equal(opened.length,0);
run("I18n.set('en');Welcome.open(0)");assert.match(opened.at(-1),/Welcome to LTM/);
for(let i=0;i<5;i++){run('Welcome.open('+i+')');assert.match(opened.at(-1),/welcomeGuide/);}
assert.match(opened.at(-1),/Save and start tour/);assert.doesNotMatch(opened.at(-1),/data-onboarding="reference"|data-onboarding="save"/);assert.equal(context.state.cards.length,0);
console.log('Read-only welcome guide, existing-data guard, dismissal and bilingual steps passed.');
