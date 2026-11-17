'use strict';
// Visual-only update hint. GitHub is queried by the local server without account
// or territory fields. The browser stores only a version-specific display choice.
const UpdateNotice = {
 storagePrefix:'ltm-update-notice:',
 valid(info){
  if(!info||typeof info!=='object'||!/^\d+\.\d+\.\d+(?:-beta\.\d+)?$/.test(info.version||''))return false;
  if(info.channel!==(info.version.includes('-beta.')?'beta':'stable'))return false;
  if(!['home-assistant','macos-app','macos-server','windows-app','windows-server','other'].includes(info.platform))return false;
  const base='https://github.com/Bib007/LTM-Local-Territory-Manager/releases';
  if(info.file_available===false)return info.url===base;
  if(info.file_available!==true||typeof info.url!=='string')return false;
  const prefix=base+'/download/v'+info.version+'/';
  if(!info.url.startsWith(prefix))return false;
  const filename=info.url.slice(prefix.length);
  return /^LTM-[A-Za-z0-9.-]+\.(?:zip|dmg|exe)$/.test(filename)&&!filename.includes('..');
 },
 label(da,en){return typeof I18n!=='undefined'&&I18n.language()==='en'?en:da;},
 key(info){return this.storagePrefix+info.channel+':'+info.platform;},
 preference(info){
  try{const value=JSON.parse(localStorage.getItem(this.key(info))||'null');
   return value?.version===info.version&&
    (value?.hide===true||(Number.isFinite(value?.until)&&value.until>Date.now()));
  }catch{return false;}
 },
 dismiss(info,hide=false){
  const node=document.getElementById('updateNotice');if(node)node.hidden=true;
  try{localStorage.setItem(this.key(info),JSON.stringify({
   version:info.version,hide,until:hide?0:Date.now()+24*60*60*1000,
  }));}catch{} // Restricted storage does not stop dismissing for this page.
 },
 paint(info){
  const node=document.getElementById('updateNotice');
  if(!node||!this.valid(info)||this.preference(info))return;
  const text=document.createElement('span');
  text.className='updateNoticeLabel';
  text.textContent=this.label('Ny version: ','New version: ')+info.version;
  const link=document.createElement('a');
  link.href=info.url;link.target='_blank';link.rel='noopener noreferrer';
  link.textContent=info.file_available
   ?this.label('Se fil på GitHub','View file on GitHub')
   :this.label('Se udgivelser på GitHub','View GitHub releases');
  const later=document.createElement('button');
  later.type='button';later.textContent=this.label('Senere','Later');
  later.addEventListener('click',()=>this.dismiss(info));
  const hide=document.createElement('button');
  hide.type='button';hide.textContent=this.label('Skjul version','Hide version');
  hide.addEventListener('click',()=>this.dismiss(info,true));
  node.replaceChildren(text,link,later,hide);
  node.setAttribute('role','group');
  node.setAttribute('aria-label',this.label('Ny LTM-version tilgængelig','New LTM version available'));
  node.hidden=false;
 },
 async check(){
  const node=document.getElementById('updateNotice');
  const token=document.querySelector('meta[name="app-token"]')?.content;
  if(!node||!token)return;
  try{
   const response=await fetch('/api/update-check',{headers:{'X-Distrikt-Token':token},credentials:'same-origin',cache:'no-store'});
   if(!response.ok)return;
   this.paint(await response.json());
  }catch{} // Offline, timeout or invalid feed: do not interrupt normal work.
 },
};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>UpdateNotice.check());
else UpdateNotice.check();
