'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),{spawn}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const source=`import sys,tempfile,threading
sys.path.insert(0,'distrikt/app')
from profile_accounts import ProfileAccounts
from profile_http import ProfilePreviewServer
from store import Store
with tempfile.TemporaryDirectory() as root:
 a=ProfileAccounts(root);a.bootstrap('Fiktiv admin','Fiktiv-password-123');store=Store(root);server=ProfilePreviewServer(a,store)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 print(server.origin,flush=True)
 try:sys.stdin.readline()
 finally:server.shutdown();server.server_close();thread.join();store.close()
`;
(async()=>{const child=spawn(process.env.PYTHON||'python',['-u','-c',source],{cwd:path.resolve(__dirname,'..'),stdio:['pipe','pipe','inherit']});let browser;
try{const url=await new Promise((resolve,reject)=>{let text='';child.stdout.on('data',x=>{text+=x;if(text.includes('\n'))resolve(text.trim().split('\n')[0]);});child.on('error',reject);child.on('exit',code=>reject(Error('Fixture exited '+code)));});
 browser=await chromium.launch({args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{assert.equal(new URL(route.request().url()).origin,url);return route.continue();});
 await page.goto(url);await page.locator('#login input[name=name]').fill('Fiktiv admin');await page.locator('#login input[name=password]').fill('Fiktiv-password-123');await page.locator('#login button').click();await page.locator('#admin').waitFor({state:'visible'});
 await page.locator('#role input[name=name]').fill('Kortlæser');await page.locator('#permissions input[value="cards.view"]').check();await page.locator('#role button').click();await page.waitForFunction(()=>[...document.querySelector('#role select').options].some(o=>o.text==='Kortlæser'));
 await page.locator('#user input[name=name]').fill('Fiktiv læser');await page.locator('#roles label').filter({hasText:'Kortlæser'}).locator('input').check();await page.locator('#user input[name=password]').fill('Fiktiv-password-456');await page.locator('#user button').click();await page.waitForFunction(()=>[...document.querySelector('#user select').options].some(o=>o.text==='Fiktiv læser'));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await page.screenshot({path:'/tmp/ltm-profile-mobile.png',fullPage:true});
 await page.locator('#logout').click();await page.locator('#login').waitFor({state:'visible'});await page.locator('#login input[name=name]').fill('Fiktiv læser');await page.locator('#login input[name=password]').fill('Fiktiv-password-456');await page.locator('#login button').click();await page.locator('#workspace').waitFor({state:'visible'});
 assert.equal(await page.locator('#admin').isVisible(),false);assert.equal(await page.locator('#online').innerText(),'');assert.deepEqual(errors,[]);console.log('Real HTTP/browser: login, admin role/user creation, logout, restricted login and mobile layout passed.');
}finally{if(browser)await browser.close();child.stdin.end('\n');}})().catch(e=>{console.error(e);process.exitCode=1;});
