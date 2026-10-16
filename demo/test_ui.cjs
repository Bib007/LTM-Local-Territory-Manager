const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const nodes=new Map(),handlers={},stored=new Map(),pendingTimers=[];
const node=id=>{if(!nodes.has(id))nodes.set(id,{id,innerHTML:'',textContent:'',hidden:false,value:'',open:false,classList:{add(){},remove(){},toggle(){}},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;},attrs:{},setAttribute(k,v){this.attrs[k]=v;},focus(){},setSelectionRange(){}});return nodes.get(id);};
const context={console,Date,Math,Map,Set,JSON,Number,String,Array,Object,Infinity,clearTimeout(){},setTimeout(fn){pendingTimers.push(fn);return pendingTimers.length;},confirm(){return true;},localStorage:{getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v)},document:{getElementById:node,documentElement:{},body:{classList:{add(){},remove(){},toggle(){}}},addEventListener:(k,f)=>handlers[k]=f},window:{addEventListener(){},print(){}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'model.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(__dirname,'demo.js'),'utf8'),context);const run=s=>vm.runInContext(s,context);
assert.match(node('content').innerHTML,/Forside/);assert.match(node('notice').textContent,/opdigtede/);
for(const page of ['home','desk','territories','map','publishers','tasks','reports','settings']){run(`screen='${page}';render()`);assert(node('content').innerHTML.length>100,page);}
run("lang='en';screen='desk';render()");assert.match(node('content').innerHTML,/Territory desk/);assert.equal(context.document.documentElement.lang,'en');
run("data.cards[0].name='<img src=x onerror=alert(1)>';screen='territories';render()");assert.match(node('content').innerHTML,/&lt;img/);assert(!node('content').innerHTML.includes('<img src=x'));
run("openCard(data.cards[0].id)");assert(node('dialog').open);assert.match(node('dialog').innerHTML,/fictional examples/);assert.match(node('dialog').innerHTML,/&lt;img/);
run('close(true)');run('assignForm(data.cards[8].id)');assert.match(node('dialog').innerHTML,/Confirm assignment/);run('close(true)');run('returnForm(data.cards[0].id)');assert.match(node('dialog').innerHTML,/Save return/);run('close(true)');run('noteForm()');assert.match(node('dialog').innerHTML,/fictional information only/);
run("lang='da';color='age';screen='map';render()");assert.match(node('content').innerHTML,/Under 90 dage/);assert.match(node('content').innerHTML,/90–179 dage/);assert.match(node('content').innerHTML,/180\+ dage eller ukendt/);assert(!node('content').innerHTML.includes('Carry folder / recent completion'));
run("color='status';render()");assert.match(run('mapLegend()'),/I mappen/);assert(!run('mapLegend()').includes('90'));
assert.equal(run("errorMessage(new Error('The card number already exists.'))"),'Kortnummeret findes allerede.');
assert.equal(run("errorMessage(new Error('Choose a valid assignment date.'))"),'Vælg en gyldig udleveringsdato, senest i dag.');
run("lang='en';color='age';render()");assert.match(run('mapLegend()'),/Under 90 days/);assert.equal(run("errorMessage(new Error('The card number already exists.'))"),'The card number already exists.');
assert.equal(run('save()'),true);assert(stored.get('ltm-fictional-demo-v1'));context.localStorage.setItem=()=>{throw Error('storage blocked');};assert.equal(run('save()'),false);run("screen='home';render()");assert.match(node('footer').textContent,/Memory in this tab only/);
assert.equal(/fetch\(|XMLHttpRequest|api\/|googleapis/.test(fs.readFileSync(path.join(__dirname,'demo.js'),'utf8')),false);
run('setMenu(true)');assert.equal(node('menu').attrs['aria-expanded'],'true');node('dialog').open=false;let menuEscape=false;handlers.keydown({key:'Escape',target:{closest(){return null;}},preventDefault(){menuEscape=true;}});assert(menuEscape);assert.equal(node('menu').attrs['aria-expanded'],'false');

let resized=0,removed=0;
context.L={map(node,options){assert.equal(options.zoomAnimation,false,'Rapid navigation must not leave a pending Leaflet zoom transition.');return {setView(){return this;},attributionControl:{setPrefix(){}},invalidateSize(){resized++;},remove(){removed++;}};},tileLayer(){return {addTo(){return this;},on(){}};}};
run("mountMap('overviewMap',[]);dispose()");pendingTimers.at(-1)();assert.equal(resized,0,'A deferred resize must not touch a map removed by navigation.');assert.equal(removed,1);
run("mountMap('overviewMap',[])");pendingTimers.at(-1)();assert.equal(resized,1,'The current map still receives its deferred resize.');run('dispose()');
console.log('Demo UI checks: both languages, every screen, escaped edits, storage failure, menu Escape and map disposal passed (browser layout checked separately).');
