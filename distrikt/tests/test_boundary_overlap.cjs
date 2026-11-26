// Invented polygons only. Positive area is separate from shared edges and address ownership.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const c={document:{addEventListener(){}},window:{addEventListener(){}}};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/workspace.js'),'utf8'),c);
const overlap=vm.runInContext('BoundaryOverlap',c),rect=(x,y,w,h)=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],base=rect(10,55,.01,.01);
const intersects=(a,b)=>overlap.intersects(overlap.ring(a),overlap.ring(b));
const cases=[
 ['disjoint',base,rect(10.02,55,.01,.01),false],
 ['shared edge',base,rect(10.01,55,.01,.01),false],
 ['shared vertex',base,rect(10.01,55.01,.01,.01),false],
 ['overlap',base,rect(10.005,55.005,.01,.01),true],
 ['contained',base,rect(10.002,55.002,.001,.001),true],
 ['identical',base,base,true],
 ['identical reversed closed ring',base,[...base.slice().reverse(),base.at(-1)],true],
 ['aligned strip, no strictly interior vertices',base,rect(10.005,55,.01,.01),true],
 ['crossed strips',rect(10,55.004,.01,.002),rect(10.004,55,.002,.01),true],
 ['concave notch',[[0,0],[4,0],[4,4],[3,4],[3,1],[1,1],[1,4],[0,4]],rect(1.2,2,1.6,1),false],
 ['concave notch shared edges',[[0,0],[4,0],[4,4],[3,4],[3,1],[1,1],[1,4],[0,4]],rect(1,1,2,3),false],
 // Thin crossing between the y sample levels; no vertex is inside the other ring.
 ['crossing triangles',[[0,0],[10,10],[10,9.9]],[[0,9.9],[10,0],[0,10]],true]
];
for(const [name,a,b,expected] of cases){assert.equal(intersects(a,b),expected,name);assert.equal(intersects(b,a),expected,name+' symmetric');}
for(const bad of [null,[[0,0],[1,1],[2,2]],[],[[0,0],[1,1]],[[0,0],[1,1],[NaN,2]],[[0,0],[1,1],['2',2]]])assert.equal(overlap.ring(bad),null);
const cards=[{id:'a',geo_polygon:base},{id:'b',geo_polygon:base},{id:'c',geo_polygon:rect(10.01,55,.01,.01)},{id:'missing'}];
const before=JSON.stringify(cards),pairs=overlap.collect(cards);assert.equal(pairs.length,1);assert.equal(JSON.stringify(pairs[0]),'["a","b"]');assert.strictEqual(overlap.collect(cards),pairs);assert.equal(JSON.stringify(cards),before);
cards[1].geo_polygon=rect(11,56,.01,.01);assert.equal(overlap.collect(cards).length,0,'Boundary changes invalidate the cache');cards.splice(1,1);assert.equal(overlap.collect(cards).length,0,'Deleted cards leave no stale issue');
// Deterministic rectangle property check, including reversed winding and subdivisions.
for(let i=0;i<500;i++){
 const x=(i*17%43)/10,y=(i*29%47)/10,w=(i%7+1)/10,h=(i%11+1)/10,a=rect(1,1,2,2),b=rect(x,y,w,h);
 assert.equal(intersects(a,i%2?b:b.reverse()),Math.min(3,x+w)-Math.max(1,x)>1e-10&&Math.min(3,y+h)-Math.max(1,y)>1e-10,'rectangle '+i);
}
console.log('Boundary overlaps: containment, crossing, identical/concave rings, edge/vertex contact, invalid input, read-only cache and 500 rectangle cases passed.');
