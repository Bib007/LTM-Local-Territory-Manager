'use strict';
// Only personal acknowledgements are written. Domain forms/data are never changed.
const PersonalGuide={data:null,sequence:0,busy:false,origin:null,visible:false,navigate:true,navigated:false,
 async load({replay=false}={}){
  if(!state?.profile)return;if(replay&&page==='Kortopsætning'&&!GeoUI.canLeave())return;this.navigate=!replay;const sequence=++this.sequence,identity=state.profile.user.id;
  try{const data=replay?await confirmedWrite('/api/profiles/guide/replay',{}):await(await api('/api/profiles/guide')).json();
   if(sequence!==this.sequence||state?.profile?.user.id!==identity)return;
   this.data=data;if(!data.steps.length){this.close();return;}if(el('dialog').open&&!this.visible)return;
   if(!this.origin)this.origin={page,section:Navigation.settingsSection};this.visible=true;this.show();
  }catch(error){if(sequence===this.sequence)toast(error);}
 },
 localize(){if(this.visible)this.show(false);},
 show(navigate=true){
  const step=this.data?.steps?.[0];if(!step||!this.visible)return;
  if(!ProfilesUI.pageAllowed(step.page)){this.cancel();this.load();return;}
  if(navigate&&this.navigate){this.navigated=true;page=step.page;if(step.section)Navigation.settingsSection=step.section;render();}
  el('personalGuideTour')?.remove();const node=document.createElement('section'),english=I18n.language()==='en';node.id='personalGuideTour';node.className='ltmTour';node.setAttribute('role','region');node.lang=I18n.language();node.setAttribute('aria-label',I18n.text('Din personlige guide'));
  node.innerHTML=`<small>${ui(this.data.kind==='news'?'Nyheder i denne opdatering':'Din personlige guide')}</small><h2 tabindex="-1">${esc(step.title[english?1:0])}</h2><p>${esc(step.text[english?1:0])}</p><div class="actions"><button class="primary" data-personal-guide="next" ${this.busy?'disabled':''}>${ui(this.data.steps.length===1?'Afslut guide':'Forstået · næste trin')}</button><button data-personal-guide="later" ${this.busy?'disabled':''}>${ui('Fortsæt senere')}</button></div>`;
  document.body.appendChild(node);node.querySelector('h2').focus();
 },
 async next(){if(this.busy||!this.visible)return;this.busy=true;const sequence=this.sequence,request=this.data,identity=state.profile.user.id;this.show(false);
  try{const data=await confirmedWrite('/api/profiles/guide/progress',{run_id:request.run_id,request_id:request.request_id,step_id:request.steps[0].id});
   if(sequence!==this.sequence||state?.profile?.user.id!==identity)return;this.data=data;if(!data.steps.length){this.close();return;}this.busy=false;this.show();
  }catch(error){if(sequence===this.sequence){toast(error);this.cancel();await this.load();}}
  finally{if(sequence===this.sequence){this.busy=false;if(this.visible)this.show(false);}}
 },
 close(){this.sequence++;this.visible=false;this.busy=false;el('personalGuideTour')?.remove();const origin=this.origin;this.origin=null;if(origin&&this.navigated&&ProfilesUI.pageAllowed(origin.page)){page=origin.page;Navigation.settingsSection=origin.section;render();}this.navigated=false;},
 cancel(){this.sequence++;this.visible=false;this.busy=false;this.data=null;this.origin=null;this.navigated=false;el('personalGuideTour')?.remove();}
};
document.addEventListener('click',async event=>{const b=event.target.closest('[data-personal-guide]');if(!b||b.disabled)return;event.preventDefault();if(b.dataset.personalGuide==='replay'){await closeRequested();if(!el('dialog').open)await PersonalGuide.load({replay:true});}else if(b.dataset.personalGuide==='next')await PersonalGuide.next();else PersonalGuide.close();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&PersonalGuide.visible&&!PersonalGuide.busy){event.preventDefault();PersonalGuide.close();}});
