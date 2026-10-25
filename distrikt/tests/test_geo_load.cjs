// Startup loading may finish after a newer editor/import read. Only the newer data should win.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const pending=[];let paints=0;
const context={document:{addEventListener(){}},window:{addEventListener(){}},api:()=>new Promise(resolve=>pending.push(resolve)),Navigation:{paintFollowupCount(){paints++;}}};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/geo.js'),'utf8'),context);
const geo=vm.runInContext('GeoUI',context);
(async()=>{
 const startup=geo.load(),newer=geo.load();
 pending[1]({json:async()=>({addresses:[{id:'new-fictional'}]})});await newer;
 pending[0]({json:async()=>({addresses:[{id:'old-fictional'}]})});await startup;
 assert.equal(geo.addresses()[0].id,'new-fictional');assert.equal(geo.loaded,true);assert.equal(paints,1);
 const failed=geo.load();pending[2]({json:async()=>{throw Error('Fictional read failure');}});await assert.rejects(failed);
 assert.equal(geo.addresses()[0].id,'new-fictional');assert.equal(paints,1,'A failed read never paints a false zero');
 console.log('Geodata load: late startup response cannot replace newer data; failed reads retain the known total.');
})().catch(error=>{console.error(error);process.exitCode=1;});
