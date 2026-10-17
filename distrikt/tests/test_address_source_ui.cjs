// Invented keys and local API responses; no browser storage or external service.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const nodes=new Map(),listeners={},calls=[];
const el=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',value:'',disabled:false,dataset:{}});return nodes.get(id);};
const c={console,Date,el,window:{confirm:()=>true},document:{querySelectorAll:()=>[],addEventListener:(type,fn)=>(listeners[type]??=[]).push(fn)},api:async(url,payload)=>{calls.push({url,payload});return {json:async()=>({configured:true,checked_at:'2026-10-16T10:00:00Z',import_ready:true})};}};
vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/i18n.js'),'utf8')+';const ui=(v,p)=>I18n.label(v,p);',c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/address-source-ui.js'),'utf8'),c);const run=code=>vm.runInContext(code,c);
(async()=>{
 assert.match(run('AddressSourceUI.html()'),/portal.datafordeler.dk/);assert.match(run('AddressSourceUI.html()'),/API-Keys/);
 const form={reportValidity:()=>false};await run('AddressSourceUI.act').call(run('AddressSourceUI'),'connect',form);assert.equal(calls.length,0);
 const key='FICTIONAL_ADDRESS_KEY_12345';el('addressSourceKey').value=key;form.reportValidity=()=>true;
 const submit=listeners.submit.find(fn=>String(fn).includes('addressSourceForm'));await submit({target:{id:'addressSourceForm',...form},preventDefault(){}});
 assert.equal(calls[0].url,'/api/address-source/connect');assert.equal(calls[0].payload.api_key,key);assert.equal(el('addressSourceKey').value,'');assert.doesNotMatch(el('addressSourceStatus').textContent,new RegExp(key));
 assert.match(el('addressSourceStatus').textContent,/bruger DAR GraphQL/);
 c.window.confirm=()=>false;await run("AddressSourceUI.act('disconnect')");assert.equal(calls.length,1);
 c.window.confirm=()=>true;await run("AddressSourceUI.act('disconnect')");assert.equal(calls.at(-1).url,'/api/address-source/disconnect');
 let release;c.api=()=>new Promise(r=>release=r);el('addressSourceKey').value=key;
 const pending=run('AddressSourceUI.act("connect")');await run('AddressSourceUI.act("connect")');assert.equal(el('addressSourceKey').value,'');
 nodes.delete('addressSourceStatus');el('addressSourceStatus').textContent='NEWER_DIALOG';release({json:async()=>({configured:true,checked_at:'2026-10-16T10:00:00Z'})});await pending;
 assert.equal(el('addressSourceStatus').textContent,'NEWER_DIALOG');assert.equal(run('AddressSourceUI.busy'),false);
 c.api=async()=>{throw Error('Fiktiv forbindelsesfejl');};el('addressSourceKey').value=key;await run('AddressSourceUI.act("connect")');assert.match(el('addressSourceError').textContent,/Fiktiv/);assert.equal(el('addressSourceKey').value,'');
 console.log('Address source UI: local guide, key clearing, validation, explicit disconnect, busy guard and abandoned-dialog protection passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
