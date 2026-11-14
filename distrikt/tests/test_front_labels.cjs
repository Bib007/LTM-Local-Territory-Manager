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
const both={front_addresses:[
 {road:'Eksempelvej',postcode:'9999',numbers:'2–24 (lige)',count:12,extra_numbers:'Indgang B'},
 {road:'Eksempelvej',postcode:'9999',numbers:'1–23 (ulige)',count:12},
 {road:'Fiktivsti',postcode:'9999',numbers:'1–23 (ulige)',count:12},
 {road:'Testvej',postcode:'9999',numbers:'2–56 (lige)',count:28},
 {road:'Testvej',postcode:'9998',numbers:'1–5 (ulige)',count:3}
]};
assert.deepEqual(JSON.parse(JSON.stringify(ctx.render(both))),[
 {label:'Eksempelvej 1–23 & 2–24 – Indgang B',count:24},
 {label:'Fiktivsti 1–23 (ulige)',count:12},
 {label:'Testvej 2–56 (lige)',count:28},
 {label:'Testvej 1–5 (ulige)',count:3},
]);
assert.equal(ctx.render(both,true)[1].label,'Fiktivsti 1–23 (odd)');
const old={geo_addresses:[{road:'Eksempelvej',number:'1',count:2},{road:'Eksempelvej',number:'2',count:1}]};
assert.equal(ctx.render(old)[0].label,'Eksempelvej 1 & 2');
const manual={addresses:[{road:'Eksempelvej',numbers:'1–23 (ulige)',count:0,count_unknown:true},{road:'Eksempelvej',numbers:'2–24 (lige)',count:12}]};
assert.equal(ctx.render(manual)[0].count_unknown,true);
assert.equal(ctx.render(manual)[0].label,'Eksempelvej 1–23 & 2–24');
const ui=read('front-label-ui.js');
for(const label of ['Egen tekst til vejnavn','Egen tekst til husnumre','Ryd egen tekst på linjen','card.front_labels.save']){
 assert.ok(ui.includes(label),label);
}
assert.ok(read('index.html').includes('/front-label-ui.js'));
assert.ok(read('server.py').includes('/front-label-ui.js'));
assert.ok(read('map-export.js').includes('c.front_addresses?frontRows(c)'), 'public PNG previews use displayed front rows');
console.log('Front labels: canonical DAR/custom rows, preserved counts and editor controls passed.');
