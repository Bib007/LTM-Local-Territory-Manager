// Language changes must leave private data and unfinished form contents alone.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
function environment(storedLanguage,blocked=false){
 const stored=new Map(storedLanguage?[['ltm-language',storedLanguage]]:[]),listeners={},writes=[],opened=[];
 const nodes={nav:{innerHTML:''},dialog:{open:true},title:{textContent:''},subtitle:{textContent:''},
  navigationLanguage:{focused:false,focus(){this.focused=true;}},form:{value:'UNSAVED_FICTIONAL_VALUE'},custom:{textContent:'Forside'},brand:{dataset:{ui:'Privat lokal installation'},textContent:''}};
 const context={console,Number,Math,Map,Set,JSON,Object,localStorage:{getItem(k){if(blocked)throw Error('blocked');return stored.get(k);},setItem(k,v){if(blocked)throw Error('blocked');stored.set(k,v);writes.push(k);}},
  state:{cards:[{id:'fictional-card',name:'Forside'}],publishers:[],loans:[]},page:'Distrikter',
  esc:s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;'),el:id=>nodes[id],
  render(){throw Error('Language change must not render app forms');},
  document:{activeElement:{id:'navigationLanguage'},addEventListener(k,f){(listeners[k]??=[]).push(f);},querySelectorAll(q){return q==='[data-ui]'?[nodes.brand]:[];},querySelector(q){return q==='[data-ui-title]'?nodes.title:q==='[data-ui-subtitle]'?nodes.subtitle:null;}},
  openDialog(html){opened.push(html);},closeDialog(){}};
 vm.createContext(context);
 for(const file of ['i18n.js','navigation.js','workspace.js','onboarding.js','welcome.js'])vm.runInContext(source(file),context);
 return {context,nodes,listeners,stored,writes,opened,run:s=>vm.runInContext(s,context)};
}
const e=environment();assert.equal(e.run('I18n.language()'),'da');
assert.match(e.run('Navigation.html()'),/Distriktskort/);
assert.match(e.run('Navigation.html()'),/value="da" selected/);
const before=JSON.stringify(e.context.state),draft=e.nodes.form;
e.listeners.change.forEach(fn=>fn({target:{id:'navigationLanguage',value:'en'}}));
assert.equal(e.run('I18n.language()'),'en');assert.equal(e.run('Welcome.language()'),'en');
assert.match(e.nodes.nav.innerHTML,/Territory cards/);assert.match(e.nodes.nav.innerHTML,/value="en" selected/);
assert.equal(e.nodes.title.textContent,'Territory cards');assert.equal(e.nodes.brand.textContent,'Private local installation');
assert.equal(e.nodes.form,draft);assert.equal(draft.value,'UNSAVED_FICTIONAL_VALUE');assert.equal(e.nodes.dialog.open,true);
assert.equal(e.nodes.navigationLanguage.focused,true);
assert.equal(JSON.stringify(e.context.state),before);assert.equal(e.nodes.custom.textContent,'Forside');
assert.deepEqual(e.writes,['ltm-language']);assert.equal(e.stored.get('ltm-language'),'en');
assert.equal(e.run("I18n.text('Unknown fictional road')"),'Unknown fictional road');
assert.match(e.run("I18n.errorText(new Error('Datafordeleren afviste nøglen. Kontrollér API-key på dit IT-system. En ny nøgle kan være op til 15 minutter om at blive aktiv. Ventetid er kun én mulig årsag. Prøv forbindelsen igen, når der er gået 15 minutter.'))"),/rejected the key.*15 minutes.*only one possible cause/);
assert.equal(e.run("I18n.set('<script>')"),false);assert.equal(e.run('I18n.language()'),'en');
const englishTargets=e.run('Navigation.html().match(/data-navigation="[^"]+"/g).join()');
e.run("I18n.set('da');Navigation.localize()");assert.equal(e.run('Navigation.html().match(/data-navigation="[^"]+"/g).join()'),englishTargets);
assert.equal(e.nodes.title.textContent,'Distriktskort');
e.run('Onboarding.open(2)');e.listeners.change.forEach(fn=>fn({target:{id:'onboardingLanguage',value:'en',dataset:{}}}));
assert.equal(e.run('Onboarding.step'),2);assert.match(e.opened.at(-1),/How would you like to create cards/);assert.match(e.opened.at(-1),/lang="en"/);
assert.match(e.nodes.nav.innerHTML,/Territory cards/);assert.equal(JSON.stringify(e.context.state),before);
assert.equal(environment('en').run('Welcome.language()'),'en');
assert.equal(environment('unsupported').run('I18n.language()'),'da');
const denied=environment('en',true);assert.equal(denied.run('I18n.language()'),'da');
denied.run("I18n.set('en');Navigation.localize()");assert.equal(denied.run('Welcome.language()'),'en');
const html=source('index.html');assert(html.indexOf('/i18n.js')<html.indexOf('/navigation.js'));
assert(html.includes('lang="da"'));assert(!html.includes('Lokalt på din Mac'));
assert(source('server.py').includes("'/i18n.js'"));
console.log('Navigation language, unchanged data/routes/drafts, shared guide preference and blocked-storage fallback passed.');
