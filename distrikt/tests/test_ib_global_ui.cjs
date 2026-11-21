// Global IB approvals use read-only local preview and one guarded mutation.
// This UI contract uses fictional values and no server or network.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const handlers={},calls=[],requests=[],dialog={open:false,innerHTML:''};
const result={matches:2,remaining:3,expected:'fictional-immutable-plan',
 cards:[{card_id:'fictional-a',number:'101',matches:1,remaining:2},
        {card_id:'fictional-b',number:'102',matches:1,remaining:1}]};
function openDialog(html){dialog.open=true;dialog.innerHTML=html;openDialog.generation++;}
openDialog.generation=0;
const state={revision:'fictional-revision',profile:null,cards:[],ib:[]};
const context={console,Promise,Map,Set,Date,Array,Object,JSON,Number,String,
 state,page:'Adresser',addressTab:'IB',openDialog,
 globalButton:{disabled:false,isConnected:true},
 globalForm:{isConnected:true,dataset:{expected:result.expected,count:String(result.matches)}},
 ui:(text,values)=>String(text).replace('{count}',values?.count??'{count}'),
 esc:value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;'),
 I18n:{language:()=> 'da',format:(key,values)=>key.replace('{count}',values.count)},
 el:()=>dialog,card:()=>null,detail(){},
 toast(error){throw error;},
 api:async(path,body)=>{requests.push({path,body});return {json:async()=>({result})};},
 mutate:async(action,data,options)=>{calls.push({action,data,options});return {count:2,remaining:3,cards:2};},
 document:{addEventListener:(name,fn)=>{(handlers[name]??=[]).push(fn);}}
};
vm.createContext(context);
vm.runInContext(read('ib-ui.js'),context);
const run=expr=>vm.runInContext(expr,context);
(async()=>{
 assert.match(run('IBUI.globalButton()'),/data-ib-global-suggest/);
 await run('IBUI.globalSuggest(globalButton)');
 assert.deepEqual(JSON.parse(JSON.stringify(requests)),[{path:'/api/mutate',body:{action:'ib.global.preview',data:{}}}]);
 assert.match(dialog.innerHTML,/Sikre match/);
 assert.match(dialog.innerHTML,/Til manuel gennemgang/);
 assert.match(dialog.innerHTML,/id="ibGlobalForm"/);
 assert.match(dialog.innerHTML,/name="confirmed" required/);
 assert.match(dialog.innerHTML,/Godkend 2 sikre match/);
 assert.match(dialog.innerHTML,/data-ib-global-review="fictional-b"/);
 assert.equal(context.globalButton.disabled,false);
 await run('IBUI.globalApply(globalForm)');
 assert.equal(calls.length,1);
 assert.equal(calls[0].action,'ib.global.apply');
 assert.deepEqual(JSON.parse(JSON.stringify(calls[0].data)),{
  expected:result.expected,count:2,confirm:'GODKEND SIKRE IB'});
 assert.equal(calls[0].options.close,false);
 assert.match(dialog.innerHTML,/2 sikre IB-match godkendt/);
 assert.match(dialog.innerHTML,/3 manuelle IB-linjer/);
 run('state.profile={permissions:[]};ProfilesUI={canAction:()=>false}');
 assert.equal(run('IBUI.globalButton()'),'','No bulk button for unauthorized users');
 assert(handlers.click.some(fn=>String(fn).includes('data-ib-global-review')));
 assert(handlers.submit.some(fn=>String(fn).includes('ibGlobalForm')));
 console.log('Global IB UI: safe preview, explicit confirmation, grouped review, write payload and permissions passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
