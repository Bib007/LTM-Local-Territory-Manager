// Same v1 file must cross between WebCrypto and the local HTTP fallback.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),{webcrypto}=require('node:crypto');
const ctx={crypto:webcrypto,TextEncoder,TextDecoder,Uint8Array,ArrayBuffer,setTimeout,console,btoa,atob,document:{addEventListener(){}},I18n:{text:s=>s}};vm.createContext(ctx);
for(const file of ['vendor/connection-crypto.js','transfer-ui.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',file),'utf8'),ctx);
const run=s=>vm.runInContext(s,ctx),payload={schema:1,connections:{datafordeler:{api_key:'FICTIONAL-only-æøå'}}},password='Fictional password 123!';ctx.payload=payload;ctx.password=password;
(async()=>{
 const native=await run('ConnectionBackupUI.encrypt(payload,password)');assert.ok(!JSON.stringify(native).includes('FICTIONAL-only'));
 ctx.envelope=native;ctx.crypto={getRandomValues:webcrypto.getRandomValues.bind(webcrypto)};
 const dec=()=>run('ConnectionBackupUI.decrypt({size:1024,text:async()=>JSON.stringify(envelope)},password)');
 assert.equal(JSON.stringify(await dec()),JSON.stringify(payload));
 const fallback=await run('ConnectionBackupUI.encrypt(payload,password)');ctx.envelope=fallback;ctx.crypto=webcrypto;
 assert.equal(JSON.stringify(await dec()),JSON.stringify(payload));
 ctx.password='Wrong password 123';await assert.rejects(dec,/beskadiget/);ctx.password=password;
 const tampered=structuredClone(fallback);const b=Buffer.from(tampered.cipher.ciphertext,'base64');b[0]^=1;tampered.cipher.ciphertext=b.toString('base64');ctx.envelope=tampered;ctx.crypto={getRandomValues:webcrypto.getRandomValues.bind(webcrypto)};await assert.rejects(dec,/beskadiget/);
 console.log('Connection backup: HTTP fallback/native v1 interoperability, Unicode, wrong password and authenticated tamper rejection passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
