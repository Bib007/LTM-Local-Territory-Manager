// Response parsing after a confirmed HTTP save; no real data or network.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const validState={
  revision:'before',today:'2026-11-17',settings:{},cards:[],areas:[],publishers:[],
  loans:[],completions:[],ib:[],ignored:[],notes:[],visits:[],recovery:[],maps:[]
};
function setup(){
  const nodes=new Map(),requests=[];
  const el=id=>{
    if(!nodes.has(id))nodes.set(id,{innerHTML:'',textContent:'',dataset:{},style:{},open:false,
      querySelector(){return null;},querySelectorAll(){return [];},showModal(){this.open=true;},
      close(){this.open=false;},addEventListener(){}});
    return nodes.get(id);
  };
  let answer=()=>{throw Error('Unexpected network call');};
  const c={console,Date,Intl,Map,Set,Math,Number,String,JSON,Array,Object,Promise,WeakMap,
    frontResizeObserver:null,DistrictMap:{dispose(){}},
    ProfilesUI:{dialogBase:'',authVersion:0,canAction:()=>true,dialog(){},afterRender(){}},
    setTimeout:()=>0,clearTimeout(){},window:{addEventListener(){},confirm:()=>true},
    document:{getElementById:el,querySelector:()=>({content:'FICTIONAL'}),
      querySelectorAll:()=>[],addEventListener(){}},
    fetch:async(url,options={})=>{
      requests.push({url,body:options.body?JSON.parse(options.body):null});
      return answer(url,options);
    }
  };
  vm.createContext(c);
  for(const name of ['i18n.js','geo.js','workspace.js'])vm.runInContext(read(name),c);
  const src=read('app.js');
  vm.runInContext(src.slice(0,src.indexOf('(async()=>{try{await refresh();')),c);
  const run=code=>vm.runInContext(code,c);
  c.fixture=JSON.parse(JSON.stringify(validState));
  run('state=JSON.parse(JSON.stringify(fixture));render=()=>{};');
  return {c,run,requests,setAnswer:fn=>answer=fn};
}
function fakeResponse(data,{status=200,authorization='2',invalid=false}={}){
  const calls={clone:0,cloneJson:0,bodyJson:0,bodyText:0};
  const raw=JSON.stringify(data);
  const response={
    ok:status>=200&&status<300,status,
    headers:{get(name){return name==='content-type'?'application/json':
      name==='X-LTM-Authorization'?authorization:null;}},
    clone(){calls.clone++;return {json:async()=>{calls.cloneJson++;
      if(invalid)throw SyntaxError('Broken synthetic JSON');
      return JSON.parse(raw);}};},
    async json(){calls.bodyJson++;if(invalid)throw SyntaxError('Broken synthetic JSON');return JSON.parse(raw);},
    async text(){calls.bodyText++;return raw;}
  };
  return {response,calls};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  // The real mutate() reads response.json() after api() validates a clone.
  {
    const f=setup(),data={revision:'saved',result:{id:'fictional-card'},
      state:{...validState,revision:'saved',cards:[{id:'fictional-card',number:'17'}]}};
    const mock=fakeResponse(data);f.setAnswer(()=>mock.response);
    f.run('state.profile=null');
    const result=await f.run("mutate('card.save',{id:'fictional-card',name:'Imaginary'},{close:false})");
    assert.equal(result.id,'fictional-card');
    assert.equal(f.run('state.revision'),'saved');
    assert.equal(f.run('state.cards.length'),1);
    assert.equal(f.requests.length,1);
    assert.equal(mock.calls.cloneJson,1,'The response is parsed once for validation');
    assert.equal(mock.calls.bodyJson,0,'The consumer must reuse that validated parse');
    assert.equal(f.run('WriteGuard.uncertain'),false);
  }
  // Repeated JSON reads use the same receipt without consuming the original body.
  {
    const f=setup(),mock=fakeResponse({revision:'r2',ok:true});
    f.setAnswer(()=>mock.response);
    const r=await f.run("api('/api/mutate',{action:'card.save',data:{name:'Fictional'}})");
    const first=await r.json(),second=await r.json();
    assert.strictEqual(first,second);
    assert.equal(mock.calls.cloneJson,1);
    assert.equal(mock.calls.bodyJson,0);
    assert.equal(await r.text(),JSON.stringify(first),'Preserves original body for non-JSON consumers');
    assert.equal(f.run('ProfilesUI.authVersion'),2);
  }
  // Non-2xx errors remain rejected; their error body is read only once.
  {
    const f=setup(),mock=fakeResponse({error:'Fiktiv afvisning'},{status:400});
    f.setAnswer(()=>mock.response);
    await assert.rejects(f.run("api('/api/mutate',{action:'card.save',data:{name:'Not saved'}})"));
    assert.equal(mock.calls.cloneJson,0);
    assert.equal(mock.calls.bodyJson,1);
    assert.equal(f.run('WriteGuard.uncertain'),false);
  }
  // A corrupt success receipt is uncertain, not proof the write was rejected.
  {
    const f=setup(),mock=fakeResponse(null,{invalid:true});
    f.setAnswer(()=>mock.response);
    await assert.rejects(f.run("api('/api/mutate',{action:'card.save',data:{name:'Fictional'}})"));
    assert.equal(f.run('WriteGuard.uncertain'),true);
    await assert.rejects(f.run("api('/api/mutate',{action:'card.save',data:{name:'Again'}})"));
    assert.equal(f.requests.length,1,'Uncertain write cannot be silently retried');
  }
  // A stale authorization header is checked before JSON is exposed.
  {
    const f=setup(),mock=fakeResponse({revision:'r3'},{authorization:'2'});
    f.run('ProfilesUI.authVersion=3');
    f.setAnswer(()=>mock.response);
    await assert.rejects(f.run("api('/api/mutate',{action:'card.save',data:{name:'Fictional'}})"));
    assert.equal(mock.calls.cloneJson,0);
    assert.equal(f.run('WriteGuard.needsReview'),true);
  }
  // Distinct overlapping requests must never share a parsed response.
  {
    const f=setup();
    const a=fakeResponse({revision:'a',result:{id:'a'}}),b=fakeResponse({revision:'b',result:{id:'b'}});
    let resolveA;
    f.setAnswer((url,options)=>JSON.parse(options.body).data.id==='a'?
      new Promise(resolve=>resolveA=()=>resolve(a.response)):b.response);
    const first=f.run("api('/api/mutate',{action:'card.save',data:{id:'a'}})");
    await tick();
    const second=await f.run("api('/api/mutate',{action:'card.save',data:{id:'b'}})");
    resolveA();
    const firstResponse=await first;
    assert.equal((await second.json()).result.id,'b');
    assert.equal((await firstResponse.json()).result.id,'a');
    assert.equal(a.calls.cloneJson,1);assert.equal(b.calls.cloneJson,1);
    assert.equal(a.calls.bodyJson,0);assert.equal(b.calls.bodyJson,0);
  }
  console.log('PASS response parsed once, original body retained, rejection, uncertainty, stale authority, concurrent receipts and real mutate path');
})().catch(error=>{console.error(error);process.exitCode=1;});
