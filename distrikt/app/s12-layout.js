'use strict';
// Millimetre adjustments are intentionally small: printed S-12 artwork remains authoritative.
// Language-specific presets live in the congregation's existing private print profile.
const S12Layout = {
 fields:['title','number','streets','qr'],
 labels:{title:'Distriktets navn',number:'Kortnummer',streets:'Vej- og adresselinjer',qr:'QR-kode'},
 blank(){return Object.fromEntries(this.fields.map(key=>[key,{x:0,y:0,scale:1}]));},
 forLanguage(profile,language){
  return {...this.blank(),...(profile?.s12_layout?.[language]||{})};
 },
 controls(profile,language){
  const selected=this.forLanguage(profile,language);
  const fields=this.fields.map(key=>{
   const v=selected[key],title=this.labels[key];
   const input=(axis,min,max,step,value)=>`<label>${ui(axis==='x'?'Vandret, mm':axis==='y'?'Lodret, mm':'Tekststørrelse')}<input type="number" name="s12_${key}_${axis}" min="${min}" max="${max}" step="${step}" value="${esc(value)}" required></label>`;
   return `<fieldset class="s12Field"><legend>${ui(title)}</legend><div class="twocol">${input('x',-2,2,.1,v.x)}${input('y',-2,2,.1,v.y)}${key==='qr'?'':input('scale',.95,1.05,.01,v.scale)}</div></fieldset>`;
  }).join('');
  return `<details class="s12Adjust"><summary>${ui('S-12 · justér tekst og QR')}</summary><p class="hint">${ui('Placering måles i mm fra skabelonens oprindelige position (højre/ned = positiv). Tekst kan skaleres 95–105 %. QR-størrelsen fastholdes af hensyn til læsbarheden. Indstillinger gemmes kun for dette formularsprog i denne menighed.')}</p>${fields}<button type="button" data-s12-reset>${ui('Nulstil S-12-felter')}</button><p class="hint">${ui('Se A4-prøven i 100 %, kontrollér skabelonens faste felter og scan QR-koden før endeligt print.')}</p></details>`;
 },
 fromFields(fields){
  const language=fields.form_language;
  if(!['da','en'].includes(language))throw Error('Vælg dansk eller engelsk formular.');
  const saved=state?.settings?.print_profiles?.front?.s12_layout||{};
  const selected={};
  for(const key of this.fields){
   selected[key]={};
   for(const axis of ['x','y','scale']){
    const v=axis==='scale'&&key==='qr'?1:Number(fields[`s12_${key}_${axis}`]);
    const min=axis==='scale'?(key==='qr'?1:.95):-2,max=axis==='scale'?(key==='qr'?1:1.05):2;
    if(!Number.isFinite(v)||v<min||v>max)throw Error('S-12: højst ±2 mm, tekst 95–105 %.');
    selected[key][axis]=v;
   }
  }
  return {...saved,[language]:selected};
 },
 css(profile,language){
  const values=this.forLanguage(profile,language);
  return this.fields.map(key=>{
   const v=values[key],x=Number(v.x),y=Number(v.y),scale=key==='qr'?1:Number(v.scale);
   if(!Number.isFinite(x)||!Number.isFinite(y)||!Number.isFinite(scale)||Math.abs(x)>2||Math.abs(y)>2||(key!=='qr'&&(scale<.95||scale>1.05)))return '';
   const selector=key==='qr'?'.cardQR':'.'+key;
   return `.cardPreview[data-form-language="${language}"] ${selector}{transform:translate(${x}mm,${y}mm) scale(${scale});transform-origin:top left}`;
  }).join('');
 },
 // Disable printing if an offset would clip a field or overlap other variable content.
 fits(front){
  if(!front)return true;
  const mm=front.clientWidth/Number(front.closest('.sheet')?.dataset.widthMm||146),rect=front.getBoundingClientRect();
  const parts=this.fields.map(key=>front.querySelector(key==='qr'?'.cardQR':'.'+key)).filter(Boolean);
  const bounds=parts.map(node=>node.getBoundingClientRect());
  if(bounds.some(b=>b.left<rect.left+mm*1.5-1||b.right>rect.right-mm*1.5+1||b.top<rect.top+mm*1.5-1||b.bottom>rect.bottom-mm*1.5+1))return false;
  for(let i=0;i<bounds.length;i++)for(let j=i+1;j<bounds.length;j++){
   const a=bounds[i],b=bounds[j];if(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top)return false;
  }
  return true;
 }
};
Object.assign(I18n.english,{
 'S-12 · justér tekst og QR':'S-12 · adjust text and QR',
 'Distriktets navn':'Territory name','Kortnummer':'Card number','Vej- og adresselinjer':'Street and address lines','QR-kode':'QR code',
 'Vandret, mm':'Horizontal, mm','Lodret, mm':'Vertical, mm','Tekststørrelse':'Text size',
 'Nulstil S-12-felter':'Reset S-12 fields',
 'Placering måles i mm fra skabelonens oprindelige position (højre/ned = positiv). Tekst kan skaleres 95–105 %. QR-størrelsen fastholdes af hensyn til læsbarheden. Indstillinger gemmes kun for dette formularsprog i denne menighed.':'Positions use mm relative to the original template (right/down = positive). Text can scale to 95–105%. QR size stays fixed for readability. Settings apply only to this form language and congregation.',
 'Se A4-prøven i 100 %, kontrollér skabelonens faste felter og scan QR-koden før endeligt print.':'Preview A4 at 100%, check the original form fields and scan the QR code before final printing.'
});
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-s12-reset]');
 if(!button)return;
 const form=button.closest('#printForm');if(!form)return;
 event.preventDefault();
 for(const key of S12Layout.fields)for(const axis of ['x','y','scale']){
  const input=form.elements[`s12_${key}_${axis}`];
  if(input)input.value=axis==='scale'?'1':'0';
 }
});
document.addEventListener('change',event=>{
 if(event.target.name!=='form_language')return;
 const form=event.target.closest('#printForm');if(!form)return;
 const profile=state.settings.print_profiles?.front||{},values=S12Layout.forLanguage(profile,event.target.value);
 for(const key of S12Layout.fields)for(const axis of ['x','y','scale']){
  const input=form.elements[`s12_${key}_${axis}`];
  if(input)input.value=values[key][axis];
 }
});