// Save only explicitly selected synthetic bytes; no real files or provider calls.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const read=p=>fs.readFileSync(path.join(__dirname,'../app',p),'utf8');
const app=read('app.js'),start=app.indexOf('function canChooseBackupLocation()'),end=app.indexOf("document.addEventListener('input'",start);
const events=[],blob={fictional:true},c={console,isSecureContext:true,api:async()=>{events.push('fetch');return {blob:async()=>blob};},URL:{createObjectURL(){events.push('url');return 'blob:invented';},revokeObjectURL(){events.push('revoke');}},document:{createElement(){return {click(){events.push('click');}};},addEventListener(){}},setTimeout:fn=>fn(),ui:s=>s};
vm.createContext(c);vm.runInContext(read('i18n.js')+'\n'+app.slice(start,end)+'\n'+read('transfer-ui.js'),c);
const run=s=>vm.runInContext(s,c),save=()=>run("download('/api/export/backup','invented.zip',{chooseLocation:true})");
run('ui=(key,params)=>I18n.label(key,params)');
(async()=>{
 assert.equal(run('canChooseBackupLocation()'),false);assert.doesNotMatch(run('TransferUI.saveHTML()'),/data-action="backup-save"/);
 await assert.rejects(save,/Filvælgeren/);assert.deepEqual(events,[]);
 c.showSaveFilePicker=async options=>{events.push('picker');assert.equal(options.suggestedName,'invented.zip');return {createWritable:async()=>({write:async value=>{assert.equal(value,blob);events.push('write');},close:async()=>events.push('close'),abort:async()=>events.push('abort')})};};
 assert.match(run('TransferUI.saveHTML()'),/data-action="backup-save"/);
 assert.equal(await save(),true);assert.deepEqual(events,['picker','fetch','write','close']);
 events.length=0;c.showSaveFilePicker=async()=>{throw {name:'AbortError'};};assert.equal(await save(),false);assert.deepEqual(events,[]);
 c.showSaveFilePicker=async()=>{throw {name:'SecurityError',message:'Private path must not be shown'};};await assert.rejects(save,/Filvælgeren/);assert.deepEqual(events,[]);
 c.showSaveFilePicker=async()=>({createWritable:async()=>({write:async()=>{throw Error('Private path');},abort:async()=>events.push('abort')})});
 await assert.rejects(save,/Sikkerhedskopien kunne ikke gemmes/);assert.deepEqual(events,['fetch','abort']);
 events.length=0;c.showSaveFilePicker=async()=>({createWritable:async()=>{throw Error('Private path');}});await assert.rejects(save,/Sikkerhedskopien kunne ikke gemmes/);assert.deepEqual(events,['fetch']);
 events.length=0;c.isSecureContext=false;assert.equal(run('canChooseBackupLocation()'),false);await assert.rejects(save,/Filvælgeren/);assert.deepEqual(events,[]);
 assert.equal(await run("download('/api/export/backup','invented.zip')"),true);assert.deepEqual(events,['fetch','url','click','revoke']);
 assert.match(app,/if\(await download\([^\n]+chooseLocation:d.action==='backup-save'[^\n]+mutate\('backup.record'/,'Cancelled/failed saves must not record a successful backup');
 run("I18n.set('en')");assert.match(run('TransferUI.saveHTML()'),/browser download settings/);
 console.log('Backup save: chooser before fetch, capability fallback, cancel without export, safe failure/abort and unchanged normal download passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
