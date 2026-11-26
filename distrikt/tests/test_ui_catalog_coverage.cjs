// Shipped interface labels must have an English entry; user data is never scanned.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'../app'),c={document:{addEventListener(){}},window:{addEventListener(){}}};vm.createContext(c);
for(const name of ['i18n.js','split-suggestions.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),c);
const keys=new Set(vm.runInContext('Object.keys(I18n.english)',c)),missing=[];
const quoted="(['\"])((?:\\\\.|(?!\\1)[^\\r\\n])*)\\1";
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#(?:x27|39);/gi,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
function requireKey(value,file){if(/\p{L}/u.test(value)&&!keys.has(value))missing.push(file+': '+value);}
for(const file of fs.readdirSync(root).filter(n=>n.endsWith('.js')&&n!=='i18n.js')){
 const source=fs.readFileSync(path.join(root,file),'utf8');
 for(const prefix of ['\\b(?:ui|I18n\\.(?:text|label|format))\\(\\s*','I18n\\.attribute\\(\\s*[\'\"][^\'\"]*[\'\"]\\s*,\\s*']){
  for(const m of source.matchAll(new RegExp(prefix+quoted,'g')))requireKey(vm.runInContext(m[1]+m[2]+m[1],c),file);
 }
 for(const m of source.matchAll(/data-ui(?:-placeholder|-aria|-title)?=(['"])(.*?)\1/g))if(!m[2].includes('${')&&!/^['"]\+.*\+['"]$/.test(m[2]))requireKey(decode(m[2]),file);
}
assert.deepEqual(missing,[],'Every declared interface label needs an English translation');
console.log('English UI catalog covers literal labels, placeholders, accessibility labels and titles across shipped client modules. Original forms and user content are unchanged.');
