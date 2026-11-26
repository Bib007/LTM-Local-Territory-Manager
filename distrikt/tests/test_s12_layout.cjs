'use strict';
// Fictitious S-12 layout offsets only; no private card data.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const c={I18n:{english:{}},document:{addEventListener(){}},state:{settings:{print_profiles:{front:{s12_layout:{en:{title:{x:1,y:0,scale:1},number:{x:0,y:0,scale:1},streets:{x:0,y:0,scale:1},qr:{x:0,y:0,scale:1}}}}}}},ui:x=>x,esc:x=>String(x)};
vm.createContext(c);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/s12-layout.js'),'utf8'),c);
const run=s=>vm.runInContext(s,c);
const fields=Object.fromEntries(['title','number','streets','qr'].flatMap(k=>['x','y',...(k==='qr'?[]:['scale'])].map(axis=>['s12_'+k+'_'+axis,axis==='scale'?'1':'0'])));
Object.assign(fields,{form_language:'da',s12_title_x:'2',s12_qr_y:'-2',s12_streets_scale:'1.05'});
c.fields=fields;
const layout=run('S12Layout.fromFields(fields)');
assert.equal(layout.da.title.x,2);assert.equal(layout.da.qr.y,-2);
assert.equal(layout.da.streets.scale,1.05);assert.equal(layout.en.title.x,1);
assert.equal(layout.da.qr.scale,1);
c.layout={s12_layout:layout};
assert.match(run("S12Layout.css(layout,'da')"),/translate\(2mm,0mm\) scale\(1\)/);
assert.match(run("S12Layout.css(layout,'da')"),/cardQR/);
for(const [key,value] of [['s12_title_x','2.1'],['s12_number_y','-2.1'],['s12_streets_scale','1.06'],['s12_qr_x','Infinity']]){
 const initial=fields[key];fields[key]=value;assert.throws(()=>run('S12Layout.fromFields(fields)'));fields[key]=initial;
}
assert.match(run("S12Layout.controls(layout,'da')"),/name="s12_title_x"/);
assert.doesNotMatch(run("S12Layout.controls(layout,'da')"),/name="s12_qr_scale"/);
console.log('S-12 separate language presets, limits, QR size and control rendering passed.');
