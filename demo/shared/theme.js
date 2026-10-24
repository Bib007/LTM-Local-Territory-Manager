'use strict';
// Appearance is a per-browser preference. No server write and no user data.
const Theme={key:'ltm-appearance',choice:'dark',media:null,
 valid(value){return ['dark','light','system'].includes(value);},
 effective(){return this.choice==='system'?(this.media?.matches?'light':'dark'):this.choice;},
 apply(){const mode=this.effective();document.documentElement.dataset.theme=mode;document.documentElement.style.colorScheme=mode;document.querySelectorAll?.('img.brandWordmark').forEach(img=>img.setAttribute('src',mode==='light'?'brand-logo-light.svg':'brand-logo.svg'));const field=document.getElementById('appearanceChoice');if(field)field.value=this.choice;},
 set(value){if(!this.valid(value))return;this.choice=value;try{localStorage.setItem(this.key,value);}catch{}this.apply();},
 html(language){const en=language==='en',label=typeof I18n!=='undefined'?I18n.text('Udseende'):en?'Appearance':'Udseende',names=en?['Dark','Light','Follow device']:['Mørkt','Lyst','Følg enheden'];return `<label class="languageChoice appearanceChoice">${label}<select id="appearanceChoice">${['dark','light','system'].map((v,i)=>`<option value="${v}" ${this.choice===v?'selected':''}>${names[i]}</option>`).join('')}</select></label>`;},
 init(){try{const value=localStorage.getItem(this.key);if(this.valid(value))this.choice=value;}catch{}this.media=window.matchMedia?.('(prefers-color-scheme: light)');this.media?.addEventListener?.('change',()=>{if(this.choice==='system')this.apply();});this.apply();document.addEventListener('DOMContentLoaded',()=>this.apply());document.addEventListener('change',event=>{if(event.target.id==='appearanceChoice')this.set(event.target.value);});window.addEventListener('storage',event=>{if(event.key===this.key){this.choice=this.valid(event.newValue)?event.newValue:'dark';this.apply();}});}
};
Theme.init();
