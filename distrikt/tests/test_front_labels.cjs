// Fictional UI/display contracts; no real data, network or uploads.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const src=read('app.js'),match=src.match(/function frontRows\(c,english=false\)\{[\s\S]*?\n\}/);
assert.ok(match,'Canonical front row renderer must be available');
const ctx={compactAddressNumbers:value=>value,cmp:(a,b)=>String(a).localeCompare(String(b))};
vm.createContext(ctx);vm.runInContext(match[0]+';this.render=frontRows;',ctx);
const base={front_addresses:[{road:'Fiktivvej',numbers:'2–4 (lige)',count:2}]};
assert.equal(ctx.render(base)[0].label,'Fiktivvej 2–4 (lige)');
const custom={front_addresses:[{...base.front_addresses[0],extra_road:'Via sidevejen',extra_numbers:'2A–8B (lige)'}]};
assert.equal(ctx.render(custom)[0].label,'Fiktivvej 2–4 (lige) – Via sidevejen – 2A–8B (lige)');
assert.equal(ctx.render(custom,true)[0].label,'Fiktivvej 2–4 (even) – Via sidevejen – 2A–8B (lige)');
assert.equal(ctx.render(custom)[0].count,2,'Visit count remains authoritative');
const ui=read('front-label-ui.js');
for(const label of ['Egen tekst til vejnavn','Egen tekst til husnumre','Ryd egen tekst på linjen','card.front_labels.save']){
 assert.ok(ui.includes(label),label);
}
assert.ok(read('index.html').includes('/front-label-ui.js'));
assert.ok(read('server.py').includes('/front-label-ui.js'));
assert.ok(read('map-export.js').includes('c.front_addresses?frontRows(c)'), 'public PNG previews use displayed front rows');
console.log('Front labels: canonical DAR/custom rows, preserved counts and editor controls passed.');
