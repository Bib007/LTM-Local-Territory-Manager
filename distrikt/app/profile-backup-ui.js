'use strict';
const ProfileBackupUI={busy:false,
 html(){return state?.profile&&ProfilesUI.has('users.manage')?`<section class="panel profileAccountBackup"><h2>Konti og roller</h2><p>Kontobackup gemmes særskilt fra distriktsdata. Den indeholder brugere, roller og adgangskodehashes, men ingen aktive sessioner.</p><p class="hint">Filen er ikke krypteret. Gem den privat, og del den ikke. Den almindelige ZIP-backup indeholder ikke kontiene.</p><button data-profile="account-backup">Hent kontobackup</button><details><summary>Gendan konti og roller fra fil</summary><p>Dette erstatter konti og roller, bevarer distriktsdata og logger alle ud. Der gemmes først en privat sikkerhedskopi af de nuværende konti på serveren. Du får en forhåndsvisning før ændringen.</p><form id="profileAccountPreview"><label>Kontobackup<input name="backup" type="file" accept=".json,application/json" required></label><label>Din nuværende adgangskode<input name="password" type="password" autocomplete="current-password" maxlength="1024" required></label><button>Kontrollér filen</button><p role="alert"></p></form></details><details><summary>Hvis administratorens login er glemt</summary><p>En anden brugeradministrator kan nulstille adgangskoden under Brugere og roller. Hvis ingen kan logge ind, skal ejeren stoppe LTM og bruge det lokale gendannelsesværktøj på serveren. Der er ingen offentlig omgåelse af login.</p><p>Se <a href="https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/docs/BRUGERE.md#lokal-kontobackup-og-administratorgendannelse" target="_blank" rel="noopener">vejledning til lokal administratorgendannelse</a>.</p></details></section>`:'';},
 async preview(form){
  if(this.busy||!form.reportValidity())return;this.busy=true;
  const generation=openDialog.generation,origin=page,node=form.querySelector('[role=alert]'),button=form.querySelector('button');button.disabled=true;node.textContent='';
  try{
   const file=form.elements.backup.files[0];if(file.size>8*1024*1024)throw Error('Vælg en kontobackup på højst 8 MB i appen. Større filer gendannes med det lokale værktøj.');
   const raw=await file.text();if(!form.isConnected||origin!==page||generation!==openDialog.generation)return;
   let backup;try{backup=JSON.parse(raw);}catch{throw Error('Filen er ikke en gyldig kontobackup.');}
   const result=await(await api('/api/profiles/backup/preview',{backup,password:form.elements.password.value})).json();
   if(!form.isConnected||origin!==page||generation!==openDialog.generation)return;
   openDialog(`<h2>Gendan konti og roller?</h2><p>Filen indeholder <strong>${result.users} brugere</strong> og <strong>${result.roles} roller</strong>. Distriktsdata og forbindelser bevares. Alle sessioner afsluttes; brug et login fra sikkerhedskopien bagefter.</p><p>En privat kopi af de nuværende konti gemmes først på serveren.</p><form id="profileAccountApply" data-snapshot="${esc(result.snapshot)}"><label>Skriv GENDAN KONTI<input name="confirmation" pattern="GENDAN KONTI" required autocomplete="off"></label><button class="danger">Erstat konti og roller</button><p role="alert"></p></form>`);
  }catch(error){if(form.isConnected)node.textContent=error.message;else toast(error);}
  finally{form.elements.password.value='';button.disabled=false;this.busy=false;}
 },
 async apply(form){
  if(this.busy||!form.reportValidity())return;this.busy=true;const button=form.querySelector('button');button.disabled=true;
  try{await confirmedWrite('/api/profiles/backup/apply',{snapshot:form.dataset.snapshot,confirmation:form.elements.confirmation.value});location.replace('/');}
  catch(error){form.querySelector('[role=alert]').textContent=error.message;}
  finally{button.disabled=false;this.busy=false;}
 }
};
document.addEventListener('click',async e=>{const button=e.target.closest('[data-profile="account-backup"]');if(!button)return;e.preventDefault();if(button.disabled)return;button.disabled=true;try{await download('/api/profiles/backup','LTM-kontobackup-'+state.today+'.json');}catch(error){toast(error);}finally{button.disabled=false;}});
document.addEventListener('submit',async e=>{const id=e.target.getAttribute('id');if(!['profileAccountPreview','profileAccountApply'].includes(id))return;e.preventDefault();await ProfileBackupUI[id==='profileAccountPreview'?'preview':'apply'](e.target);});
