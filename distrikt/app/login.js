'use strict';
const LoginText={current:'da',english:{"Brugernavn":"Username","Forkert brugernavn eller adgangskode. Vent fem minutter efter gentagne forsøg.":"Incorrect username or password. Wait five minutes after repeated attempts.","Privat adgang · hjemmenetværk og VPN":"Private access · home network and VPN","Adgangskode":"Password","Log ind":"Sign in","Logger ind…":"Signing in…","Sprog":"Language","Svaret kunne ikke læses. Prøv at logge ind igen.":"The response could not be read. Try signing in again.","Login mislykkedes.":"Sign-in failed.","Login blev ikke bekræftet. Genindlæs siden og kontrollér adgangen.":"Sign-in was not confirmed. Reload the page and check access.","Ingen forbindelse til login. Kontrollér Wi-Fi / VPN, og prøv igen.":"Cannot reach sign-in. Check Wi-Fi / VPN and try again.","Forkert adgangskode eller for mange forsøg. Vent fem minutter efter gentagne forsøg.":"Incorrect password or too many attempts. Wait five minutes after repeated attempts."},
 language(){return this.current;},text(key){return this.current==='en'&&Object.prototype.hasOwnProperty.call(this.english,key)?this.english[key]:key;},
 set(language){if(!['da','en'].includes(language))return;this.current=language;try{localStorage.setItem('ltm-language',language);}catch{}},
 content(node,key){if(!node)return;node.dataset.ui=key;node.textContent=this.text(key);node.lang=this.current==='en'&&Object.prototype.hasOwnProperty.call(this.english,key)?'en':'da';},
 errorContent(node,error){this.content(node,error?.uiKey||error?.message||String(error??''));},
 applyShell(){document.querySelectorAll('[data-ui]').forEach(node=>this.content(node,node.dataset.ui));}
};
try{LoginText.current=localStorage.getItem('ltm-language')==='en'?'en':'da';}catch{}
const LoginUI={busy:false,
 localize(){document.documentElement.lang=LoginText.language();const language=document.getElementById('loginLanguage');if(language)language.value=LoginText.language();document.title=(document.title.includes('Beta')?'LTM Beta':'LTM')+' · '+LoginText.text('Log ind');LoginText.applyShell();},
 async submit(form){
  if(this.busy||!form.reportValidity())return;
  const password=document.getElementById('loginPassword'),button=form.querySelector('button[type=submit]'),body=JSON.stringify({password:password.value,...(document.getElementById('loginName')?{name:document.getElementById('loginName').value}:{})}),controller=typeof AbortController==='function'?new AbortController():null;
  this.busy=true;button.disabled=true;password.disabled=true;password.removeAttribute('aria-invalid');form.setAttribute('aria-busy','true');document.getElementById('loginError').textContent='';LoginText.content(button,'Logger ind…');let success=false;
  const timer=controller?setTimeout(()=>controller.abort(),30000):null;
  try{
   const response=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body,...(controller?{signal:controller.signal}:{})});
   let data;try{data=await response.json();}catch{throw {uiKey:'Svaret kunne ikke læses. Prøv at logge ind igen.'};}
   if(!response.ok)throw {uiKey:typeof data?.error==='string'?data.error:'Login mislykkedes.',credentialError:response.status===401};
   if(data?.ok!==true)throw {uiKey:'Login blev ikke bekræftet. Genindlæs siden og kontrollér adgangen.'};
   success=true;password.value='';location.replace('/');
  }catch(error){LoginText.errorContent(document.getElementById('loginError'),error?.uiKey?error:{uiKey:'Ingen forbindelse til login. Kontrollér Wi-Fi / VPN, og prøv igen.'});if(error?.credentialError)password.setAttribute('aria-invalid','true');}
  finally{if(timer!==null)clearTimeout(timer);this.busy=false;button.disabled=false;password.disabled=false;form.removeAttribute('aria-busy');LoginText.content(button,'Log ind');if(!success&&[button,password,document.body].includes(document.activeElement))password.focus({preventScroll:true});}
 }
};
LoginUI.localize();
document.getElementById('loginLanguage')?.addEventListener('change',event=>{LoginText.set(event.target.value);LoginUI.localize();});
document.getElementById('loginForm').addEventListener('submit',event=>{event.preventDefault();LoginUI.submit(event.target);});
