// Update hint only; invented GitHub releases and browser state. No external calls.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../app/updates.js'),'utf8');
const BASE='https://github.com/Bib007/LTM-Local-Territory-Manager/releases';

function environment(blocked=false){
 const storage=new Map(),timers=[],requests=[];
 let now=1800000000000,language='da',reply=async()=>({ok:true,json:async()=>null});
 const notice={hidden:true,children:[],attrs:{},replaceChildren(...items){this.children=items;},
   setAttribute(key,value){this.attrs[key]=value;}};
 const make=tag=>({tag,textContent:'',attrs:{},listeners:{},
   setAttribute(key,value){this.attrs[key]=value;},
   addEventListener(key,fn){this.listeners[key]=fn;}});
 const doc={readyState:'loading',listeners:{},getElementById:id=>id==='updateNotice'?notice:null,
   querySelector:sel=>sel==='meta[name="app-token"]'?{content:'FICTIONAL-CSRF'}:null,
   createElement:make,addEventListener(key,fn){this.listeners[key]=fn;}};
 const c={console,document:doc,Date:{now:()=>now},JSON,Number,String,Promise,
   I18n:{language:()=>language},setTimeout(fn,delay){timers.push({fn,delay});},
   localStorage:{getItem(key){if(blocked)throw Error('storage disabled');return storage.get(key);},
    setItem(key,val){if(blocked)throw Error('storage disabled');storage.set(key,val);}},
   fetch:async(url,options)=>{requests.push({url,options});return reply();}};
 vm.createContext(c);vm.runInContext(source,c);
 const run=code=>vm.runInContext(code,c);
 return {c,run,notice,storage,timers,requests,reply:fn=>reply=fn,
  setNow:v=>now=v,setLanguage:v=>language=v};
}
const info=(version='1.12.20',platform='windows-app',file=true)=>({
 version,channel:version.includes('beta')?'beta':'stable',platform,file_available:file,
 url:file?BASE+'/download/v'+version+'/LTM-Windows-v'+version+'-Setup.exe':BASE,
});
(async()=>{
 const env=environment();
 env.reply(async()=>({ok:true,json:async()=>info()}));
 await env.run('UpdateNotice.check()');
 assert.equal(env.notice.hidden,false);
 assert.equal(env.notice.children[0].textContent,'Ny version: 1.12.20');
 assert.equal(env.notice.children[1].href,info().url);
 assert.equal(env.notice.children[1].target,'_blank');
 assert.equal(env.notice.children[1].rel,'noopener noreferrer');
 assert.equal(env.requests.length,1);
 assert.equal(env.requests[0].url,'/api/update-check');
 assert.equal(env.requests[0].options.headers['X-Distrikt-Token'],'FICTIONAL-CSRF');
 assert.equal(env.requests[0].options.credentials,'same-origin');
 assert.equal(env.requests[0].options.body,undefined);
 env.notice.children[2].listeners.click(); // Postpone the current version.
 assert.equal(env.notice.hidden,true);
 env.run('UpdateNotice.paint('+JSON.stringify(info())+')');
 assert.equal(env.notice.hidden,true);
 env.setNow(1800000000000+24*60*60*1000+1);
 env.run('UpdateNotice.paint('+JSON.stringify(info())+')');
 assert.equal(env.notice.hidden,false);
 env.notice.children[3].listeners.click(); // Hide exactly that version.
 env.run('UpdateNotice.paint('+JSON.stringify(info())+')');
 assert.equal(env.notice.hidden,true);
 env.run('UpdateNotice.paint('+JSON.stringify(info('1.12.21'))+')');
 assert.equal(env.notice.hidden,false,'A newer release is not hidden');
 assert.ok([...env.storage.keys()].every(k=>k.startsWith('ltm-update-notice:')));
 assert.doesNotMatch(JSON.stringify([...env.storage]),/FICTIONAL-CSRF/);

 const beta=info('1.12.20-beta.3','windows-app',false);
 env.run('UpdateNotice.paint('+JSON.stringify(beta)+')');
 assert.equal(env.notice.children[1].href,BASE,'Missing platform asset must use the release overview');
 const stableHidden=env.storage.size;
 env.notice.children[3].listeners.click();
 assert.equal(env.storage.size,stableHidden+1,'Beta uses a distinct preference key');
 env.setLanguage('en');
 env.run('UpdateNotice.paint('+JSON.stringify(info('1.12.22'))+')');
 assert.equal(env.notice.children[0].textContent,'New version: 1.12.22');

 for(const bad of [
  {...info(),url:'https://attacker.example/malware.exe'},
  {...info(),url:BASE+'/download/v1.12.19/LTM-Windows-v1.12.20-Setup.exe'},
  {...info(),url:BASE+'/download/v1.12.20/../../evil.exe'},
  {...info(),version:'1.12.20-evil'},
  {...info(),channel:'beta'},
  {...info(),file_available:false,url:BASE+'/tag/v1.12.20'},
 ]){
  const fresh=environment();fresh.run('UpdateNotice.paint('+JSON.stringify(bad)+')');
  assert.equal(fresh.notice.hidden,true,'Untrusted or wrong-channel URL cannot display');
 }

 const offline=environment(true);
 offline.reply(async()=>{throw Error('Fictional offline');});
 await offline.run('UpdateNotice.check()');
 assert.equal(offline.notice.hidden,true);
 offline.run('UpdateNotice.paint('+JSON.stringify(info())+')');
 assert.equal(offline.notice.hidden,false,'Blocked storage cannot break display');
 offline.notice.children[2].listeners.click();
 assert.equal(offline.notice.hidden,true,'Dismissing still works without storage');
 const pending=environment();
 let phase=0;
 pending.reply(async()=>({ok:true,json:async()=>++phase===1?{checking:true}:info()}));
 await pending.run('UpdateNotice.check()');
 assert.equal(pending.notice.hidden,true);
 assert.equal(pending.timers[0].delay,1250);
 await pending.timers[0].fn();
 assert.equal(pending.notice.hidden,false);
 assert.equal(pending.requests.length,2);
 console.log('Release hint: verified link, platform fallback, Beta separation, later/hide, offline and invalid URL passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
