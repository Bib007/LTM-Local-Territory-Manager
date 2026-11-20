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
const optionalRange={front_addresses:[
 {road:'Eksempelvej',postcode:'9999',numbers:'3 & 7 & 9 & 15 & 25 & 67 (ulige)',short_numbers:'3–67',number_style:'range',count:6},
 {road:'Eksempelvej',postcode:'9999',numbers:'2 & 4 (lige)',number_style:'exact',count:2}
]};
const ranged=JSON.parse(JSON.stringify(ctx.render(optionalRange)));
assert.deepEqual(ranged,[
 {label:'Eksempelvej 3–67 & 2 & 4',count:8}
],'The range and the opposite side share a line, with all original visits counted');
assert.equal(ctx.render(optionalRange,true)[0].label,'Eksempelvej 3–67 & 2 & 4','Mixed streets omit parity markers in English too');
assert.equal(ctx.render({front_addresses:optionalRange.front_addresses.slice(0,1)})[0].label,'Eksempelvej 3–67 (ulige)');
const bothRanged={front_addresses:[
 {road:'Testvej',postcode:'9999',numbers:'1 & 9 (ulige)',short_numbers:'1–9',number_style:'range',count:2},
 {road:'Testvej',postcode:'9999',numbers:'2 & 20 (lige)',short_numbers:'2–20',number_style:'range',count:2}
]};
assert.equal(ctx.render(bothRanged)[0].label,'Testvej 1–9 & 2–20');
assert.equal(ctx.render(bothRanged,true)[0].label,'Testvej 1–9 & 2–20');
const evenOnly={front_addresses:[{road:'Fiktiv lige vej',numbers:'2 & 8 & 14 (lige)',short_numbers:'2–14',number_style:'range',count:3}]};
assert.equal(ctx.render(evenOnly)[0].label,'Fiktiv lige vej 2–14 (lige)');
assert.equal(ctx.render(evenOnly,true)[0].label,'Fiktiv lige vej 2–14 (even)');
optionalRange.front_addresses[0].number_style='exact';
assert.match(ctx.render(optionalRange)[0].label,/3 & 7 & 9 & 15 & 25 & 67/,'Turning off shortening restores exact selected numbers');
const old={geo_addresses:[{road:'Eksempelvej',number:'1',count:2},{road:'Eksempelvej',number:'2',count:1}]};
assert.equal(ctx.render(old)[0].label,'Eksempelvej 1 & 2');
const manual={addresses:[{road:'Eksempelvej',numbers:'1–23 (ulige)',count:0,count_unknown:true},{road:'Eksempelvej',numbers:'2–24 (lige)',count:12}]};
assert.equal(ctx.render(manual)[0].count_unknown,true);
assert.equal(ctx.render(manual)[0].label,'Eksempelvej 1–23 & 2–24');
// Exercise the actual number formatter and the same markup used by print/PDF.
vm.runInContext(src.match(/function compactAddressNumbers\(value\)\{[\s\S]*?\n\}/)[0],ctx);
ctx.esc=value=>String(value);ctx.visitsKnown=()=>true;ctx.visitsCount=c=>c.front_addresses.reduce((n,r)=>n+r.count,0);
vm.runInContext(src.match(/function frontStreetMarkup\(c,english\)\{[^\n]+/)[0],ctx);
for(const [odd,even,expected] of [
 ['1–9','2–10','1-9 & 2-10'],
 ['1A–9B','2A–10B','1A-9B & 2A-10B'],
 ['1','2','1 & 2']
]){
 const fixture={front_addresses:[
  {road:'Fiktivvej',numbers:odd+' (ulige)',short_numbers:odd,number_style:'range',count:3},
  {road:'Fiktivvej',numbers:even+' (lige)',short_numbers:even,number_style:'range',count:4}
 ]};
 const before=JSON.stringify(fixture);
 for(const english of [false,true]){
  assert.equal(ctx.render(fixture,english)[0].label,'Fiktivvej '+expected);
  const markup=ctx.frontStreetMarkup(fixture,english);
  assert.ok(markup.includes('Fiktivvej '+expected));
  assert.ok(markup.includes(english?'7 visits':'7 besøg'));
 }
 assert.equal(JSON.stringify(fixture),before,'Rendering never changes selections or styles');
}
for(const [numbers,short,expected] of [
 ['1 & 9 (ulige)','1–9','1-9 (ulige)'],
 ['2 & 10 (lige)','2–10','2-10 (lige)'],
 ['1A & 9B (ulige)','1A–9B','1A-9B (ulige)'],
 ['2B (lige)','','2B (lige)']
])assert.equal(ctx.render({front_addresses:[{road:'Fiktivvej',numbers,short_numbers:short,number_style:short?'range':'exact',count:2}]})[0].label,'Fiktivvej '+expected);
assert.ok(read('printing.js').includes('frontHTML({...c,form_language:formLanguage})'),'Print/PDF uses the canonical front renderer');
assert.ok(src.includes('frontStreetMarkup(c,english)'),'App front uses canonical street markup');
const ui=read('front-label-ui.js');
for(const label of ['Egen tekst til vejnavn','Egen tekst til husnumre','Visning af husnumre på forsiden','Vis fra første til sidste','data-front-number-style','Intervallet forkorter kun teksten','card.front_labels.save']){
 assert.ok(ui.includes(label),label);
}
assert.ok(read('index.html').includes('/front-label-ui.js'));
assert.ok(read('server.py').includes('/front-label-ui.js'));
assert.ok(read('map-export.js').includes('c.front_addresses?frontRows(c)'), 'public PNG previews use displayed front rows');
console.log('Front labels: canonical DAR/custom rows, preserved counts and editor controls passed.');
