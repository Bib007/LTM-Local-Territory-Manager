// Production task UI with fictional state only. No real server, accounts or external data.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright'),root=path.resolve(__dirname,'../distrikt/app'),out=process.env.LTM_BROWSER_OUTPUT;
(async()=>{const browser=await chromium.launch({args:['--no-sandbox']});try{for(const width of [320,390,768,1440]){
 const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[],writes=[];
 const state={revision:'fictional-1',today:'2026-10-21',version:'fictional',cards:[],areas:[],publishers:[],loans:[],completions:[],ib:[],ignored:[],notes:[],tasks:[],visits:[],recovery:[],maps:[],settings:{onboarding:{completed:true},folder_minimum:0,rural_minimum:0},public_maps:[],address_task:{available:true,enabled:false,days:7,time:'02:00',status:'complete',completed_at:'2026-10-21T02:00:00Z',last_result:{new:2,changed:1,retired:1},pending:4}};
 page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/*',async route=>{const u=new URL(route.request().url());assert.equal(u.hostname,'ltm.address-task.test','All test traffic stays fictional');const json=data=>route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
 if(u.pathname==='/api/state')return json(state);
 if(u.pathname==='/api/geo')return json({addresses:[],buildings:[],roads:[],info:{},status:{},changes:[{id:'fictional-change',kind:'new',at:'2026-10-21',after:{label:'Fiktiv vej 1',count:1}}]});
 if(u.pathname==='/api/geo/job')return json({status:'idle'});
 if(u.pathname==='/api/ping')return json({ok:true});
 if(u.pathname==='/api/share/status')return json({connected:false,cards:[]});
 if(u.pathname==='/api/mutate'){
  const data=route.request().postDataJSON();assert.equal(data.action,'address.task.configure');assert.equal(data.data._revision,state.revision);writes.push(data.data);
  Object.assign(state.address_task,data.data,{status:data.data.enabled?'scheduled':'idle',next_due:'2026-10-22T02:15:00Z'});state.revision='fictional-'+(writes.length+1);return json({ok:true,result:{ok:true},revision:state.revision});
 }
 const file=path.join(root,u.pathname==='/'?'index.html':u.pathname.slice(1));assert.ok(file.startsWith(root+path.sep));
 return u.pathname==='/'?route.fulfill({contentType:'text/html',body:fs.readFileSync(file,'utf8').replace('__TOKEN__','FICTIONAL_TOKEN')}):route.fulfill({path:file});
 });
 await page.goto('http://ltm.address-task.test/');await page.waitForFunction(()=>state!==null);
 await page.evaluate(()=>{page='Forside';render();});
 assert.match(await page.locator('#addressTask').innerText(),/2 nye · 1 ændrede · 1 foreslået fjernet/);
 await page.locator('#addressTask [data-work=tasks]').click();await page.locator('#addressTask [data-work=address-task]').click();
 const form=page.locator('[data-work-form=address-task]');await form.locator('[name=enabled]').check();await form.locator('[name=days]').fill('3');await form.locator('[name=time]').fill('02:15');await form.locator('button.primary').click();
 await page.waitForFunction(()=>!el('dialog').open);assert.deepEqual({enabled:writes[0].enabled,days:writes[0].days,time:writes[0].time},{enabled:true,days:3,time:'02:15'});
 assert.ok(await page.locator('#addressTask').evaluate(n=>n.scrollWidth<=n.clientWidth+1),'Task panel fits narrow displays');
 await page.locator('#addressTask [data-work=address-changes]').click();assert.match(await page.locator('#dialog').innerText(),/Fiktiv vej 1/);await page.evaluate(()=>closeDialog());
 await page.evaluate(()=>{state.address_task={...state.address_task,status:'waiting',run:{id:'fictional'},retry_at:'2026-10-22T03:00:00Z',message:'Venter efter fiktiv netfejl'};render();});
 assert.match(await page.locator('#addressTask').innerText(),/Venter og prøver igen/);
 if(out){fs.mkdirSync(out,{recursive:true});await page.screenshot({path:path.join(out,`address-task-${width}.png`),fullPage:true});}
 await page.evaluate(()=>{state.address_task.available=false;render();});assert.equal(await page.locator('#addressTask').count(),0);assert.deepEqual(errors,[]);await context.close();
}console.log('HA address task: dashboard counts, task configuration, revision-guarded writes, review navigation, retry status, desktop exclusion and four screen widths passed.');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
