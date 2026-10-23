// Fictional names only. Exercise delegated input, keyboard, mouse/touch and language events.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const listeners={},attrs=new Map(),options=[];
let focused=false;
const input={id:'issuePublisherName',value:'',matches:s=>s==='[data-publisher-search]',closest:()=>parent,
 setAttribute:(k,v)=>attrs.set(k,v),getAttribute:k=>attrs.get(k),removeAttribute:k=>attrs.delete(k),
 focus(){if(!focused){focused=true;fire('focusin');}}};
const hint={textContent:''},list={hidden:true,_html:'',get innerHTML(){return this._html;},set innerHTML(html){this._html=html;options.length=0;for(const match of html.matchAll(/id="([^"]+)" aria-selected="false" data-publisher-option="(\d+)"/g)){const a=new Map();options.push({id:match[1],dataset:{publisherOption:match[2]},setAttribute:(k,v)=>a.set(k,v),getAttribute:k=>a.get(k),scrollIntoView(){this.scrolled=true;},closest:s=>s==='[data-publisher-option]'?options[Number(match[2])]:parent});}},querySelectorAll:()=>options};
const parent={querySelector:s=>s==='[role="listbox"]'?list:s==='.publisherSearchHint'?hint:input,contains:n=>n===input||options.includes(n)};
const context={console,Intl,WeakMap,Map,String,Number,JSON,Object,Array,
 esc:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'),
 document:{addEventListener:(kind,fn)=>(listeners[kind]??=[]).push(fn),querySelectorAll:()=>[input]},
 fetch(){throw Error('No network is allowed');},localStorage:{setItem(){throw Error('No browser storage is allowed');}}};
vm.createContext(context);vm.runInContext(read('i18n.js'),context);vm.runInContext(read('publisher-search.js'),context);
context.input=input;
const run=s=>vm.runInContext(s,context);
function fire(kind,properties={}){const e={target:input,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;},...properties};for(const fn of listeners[kind]||[])fn(e);return e;}
function type(value){input.value=value;fire('input');}
const records=[{name:'Anna Test Jensen'},{name:'Test Jensen'},{name:'Jens Eksempel'},{name:'Jensen Fiktiv'},{name:'André Øster'},{name:'<img src=x onerror="fake()">'}];
context.records=records;const original=JSON.stringify(records);run('PublisherSearch.attach(input,records)');
fire('focusin');assert.equal(attrs.get('aria-expanded'),'true');assert.equal(options.length,6);assert.equal(attrs.has('aria-activedescendant'),false);
assert(list.innerHTML.includes('&lt;img'));assert(!list.innerHTML.includes('<img'));
type('jens');assert.equal(options.length,4);assert(list.innerHTML.indexOf('Jens Eksempel')<list.innerHTML.indexOf('Test Jensen'));
type('anna jens');assert.equal(options.length,1);assert(list.innerHTML.includes('Anna Test Jensen'));
type('andre ost');assert.equal(options.length,1);assert(list.innerHTML.includes('André Øster'));
const down=fire('keydown',{key:'ArrowDown'});assert(down.prevented);assert.equal(options[0].getAttribute('aria-selected'),'true');assert.equal(attrs.get('aria-activedescendant'),options[0].id);
const enter=fire('keydown',{key:'Enter'});assert(enter.prevented);assert.equal(input.value,'André Øster');assert.equal(attrs.get('aria-expanded'),'false','Refocusing after touch selection must leave popup closed');
assert.equal(fire('keydown',{key:'Enter'}).prevented,undefined,'A subsequent Enter may submit the form');
type('jens');const ime=fire('keydown',{key:'Enter',isComposing:true});assert.equal(ime.prevented,undefined);assert.equal(attrs.get('aria-expanded'),'true');
const esc=fire('keydown',{key:'Escape'});assert(esc.prevented&&esc.stopped);assert.equal(attrs.get('aria-expanded'),'false');assert.equal(input.value,'jens');assert.equal(fire('keydown',{key:'Escape'}).prevented,undefined,'Second Escape reaches the native dialog');
fire('keydown',{key:'ArrowUp'});assert.equal(attrs.get('aria-activedescendant'),options.at(-1).id);fire('keydown',{key:'Tab'});assert.equal(attrs.get('aria-expanded'),'false');assert.equal(input.value,'jens');
type('Anna');const unchosen=fire('keydown',{key:'Enter'});assert(unchosen.prevented);assert.equal(input.value,'Anna','Never select an unrequested suggestion or accidentally save');
type('Helt nyt fiktivt navn');assert.equal(options.length,0);assert.equal(list.hidden,true);assert.match(hint.textContent,/nyt navn/);assert.equal(fire('keydown',{key:'Enter'}).prevented,undefined);
run("I18n.set('en');PublisherSearch.localize()");assert.match(hint.textContent,/new name/);assert.equal(input.value,'Helt nyt fiktivt navn');
context.many=Array.from({length:12},(_,i)=>({name:'Eksempel '+(i+1)}));run('PublisherSearch.attach(input,many)');type('eksempel');assert.equal(options.length,8);assert.match(hint.textContent,/8 of 12/);assert(list.innerHTML.indexOf('Eksempel 2<')<list.innerHTML.indexOf('Eksempel 3<'));
fire('keydown',{key:'ArrowDown'});run("I18n.set('da');PublisherSearch.localize()");assert.equal(input.value,'eksempel');assert.equal(attrs.has('aria-activedescendant'),false);assert.match(hint.textContent,/8 af 12/);
fire('focusout',{relatedTarget:{}});assert.equal(list.hidden,true);
fire('focusin');const mouse=fire('pointerdown',{target:options[1],pointerType:'mouse'});assert(mouse.prevented);
const touch=fire('pointerdown',{target:options[1],pointerType:'touch'});assert.equal(touch.prevented,undefined,'Touch scrolling must not be cancelled');focused=false;fire('click',{target:options[1]});assert.equal(input.value,'Eksempel 2');assert.equal(list.hidden,true);assert.match(hint.textContent,/Navnet er valgt/);
assert.equal(JSON.stringify(records),original,'Suggestions never create or change records');
assert.match(run('PublisherSearch.field()'),/name="publisher_name"/);assert.match(run('PublisherSearch.field()'),/maxlength="100" required autocomplete="off"/);
const index=read('index.html'),server=read('server.py');assert(index.indexOf('/publisher-search.js')<index.indexOf('/app.js'));assert(server.includes("'/publisher-search.js'"),'Server must actually serve the module');
console.log('Local publisher ranking, escaping, limits, keyboard/IME, mouse/touch, language and free-name form contracts passed.');
