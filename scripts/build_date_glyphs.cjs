// Developer-only build of the fixed date alphabet. Runtime needs no font engine.
'use strict';
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const [fontPath,sourcePath]=process.argv.slice(2);
 if(!fontPath||!sourcePath)throw Error('Usage: node scripts/build_date_glyphs.cjs FONT.ttf SOURCE.json');
 const font=fs.readFileSync(fontPath).toString('base64'),source=JSON.parse(fs.readFileSync(sourcePath,'utf8'));
 const browser=await chromium.launch({...(process.env.LTM_CHROME?{executablePath:process.env.LTM_CHROME}:{}),args:['--no-sandbox']});
 try{
  const context=await browser.newContext();await context.route('**/*',()=>{throw Error('No network during font compilation');});
  const page=await context.newPage();
  const glyphs=await page.evaluate(async data=>{
   const face=new FontFace('LTMDate','url(data:font/ttf;base64,'+data+')',{weight:'500'});await face.load();document.fonts.add(face);
   await document.fonts.load('500 48px LTMDate','0123456789.-');
   const result={};
   for(const char of '0123456789.-'){
    const canvas=document.createElement('canvas'),measure=canvas.getContext('2d');measure.font='500 48px LTMDate';
    const advance=measure.measureText(char).width;canvas.width=Math.ceil(advance)+4;canvas.height=58;
    const context=canvas.getContext('2d');context.font='500 48px LTMDate';context.fillStyle='black';context.fillText(char,2,46);
    const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;
    result[char]={width:canvas.width,height:canvas.height,advance,alpha:Array.from({length:canvas.width*canvas.height},(_,i)=>pixels[i*4+3])};
   }
   return result;
  },font);
  for(const glyph of Object.values(glyphs)){glyph.alpha=zlib.deflateSync(Buffer.from(glyph.alpha)).toString('base64');}
  const output=path.resolve(__dirname,'../distrikt/app/vendor_fonts/date-glyphs.json');fs.mkdirSync(path.dirname(output),{recursive:true});
  fs.writeFileSync(output,JSON.stringify({format:1,font:'LTM Date Digits',derivedFrom:'Noto Sans',weight:500,pixels:48,source,glyphs},null,2)+'\n');
  console.log('Built fixed date alphabet: '+Object.keys(glyphs).length+' glyphs.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
