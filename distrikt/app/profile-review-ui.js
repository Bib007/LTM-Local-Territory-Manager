'use strict';
// Format the server-authorized evidence as ordinary fields. Never emit JSON,
// fetch an external image, or interpret a stored value as HTML.
const ProfileReview={
 labels:{road:'Vejnavn',number:'Husnummer',numbers:'Numre / interval',count:'Besøg',type:'Adressetype',name:'Navn',group:'Tjenestegruppe',group_role:'Gruppefunktion',pioneer:'Pioner',date:'Dato',postcode:'Postnummer',floor:'Etage',door:'Dør',frequency:'Gentagelse',weekday:'Ugedag',resolved:'Udført',text:'Tekst',card_id:'Kort',area_id:'Område',address_id:'Adresse-id',id:'Id',lng:'Længdegrad',lat:'Breddegrad'},
 label(field){return this.labels[field]||String(field).replaceAll('_',' ');},
 shown(envelope,field){return !envelope?.present||envelope.value===null?`<p>${ui('Ikke udfyldt')}</p>`:this.value(envelope.value,field);},
 value(value,field='',depth=0){
  if(value===null||value===undefined)return `<span>${ui('Ikke udfyldt')}</span>`;
  if(field==='credential')return `<span>${ui('Adgangskode ændret')}</span>`;
  if(depth>5)return `<span>${ui('Flere oplysninger')}</span>`;
  if(['geo_polygon','polygon'].includes(field)&&Array.isArray(value))return this.boundary(value);
  if(Array.isArray(value)){
   if(!value.length)return `<span>${ui('Ingen oplysninger')}</span>`;
   if(field==='addresses')return value.map((row,i)=>`<section class="profileReviewLine"><h5>${ui('Vejlinje {number}',{number:i+1})}</h5>${this.record(row,depth+1,true)}</section>`).join('');
   return `<ul class="profileReviewList">${value.map(v=>`<li>${this.value(v,field,depth+1)}</li>`).join('')}</ul>`;
  }
  if(typeof value==='object')return this.record(value,depth+1);
  if(typeof value==='boolean')return `<span>${ui(value?'Ja':'Nej')}</span>`;
  if(typeof value==='number')return `<span>${esc(value.toLocaleString(I18n.language()==='en'?'en-GB':'da-DK'))}</span>`;
  if(field==='image')return /^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(value)?`<img class="profileReviewImage" src="${esc(value)}" ${I18n.attribute('alt','Gemt kortbillede')}>`:`<span>${ui('Gemt kortbillede')}</span>`;
  let label=value;
  if(field==='group_role')label=publisherRoleLabels[value]||value;
  if(field==='permissions')label=ProfilesUI.labels[value]||value;
  if(field==='roles')label=ProfilesUI.admin?.roles?.find(r=>r.id===value)?.name||value;
  if(field==='area_id')label=state.areas.find(a=>a.id===value)?.name||value;
  if(field==='card_id')label=card(value)?.number||value;
  if(field==='frequency')label=({daily:'Dagligt',weekly:'Ugentligt',monthly:'Månedligt'})[value]||value;
  if(['date','assigned','returned','last_completed'].includes(field)&&/^\d{4}-\d{2}-\d{2}$/.test(value))label=fmt(value);
  const translated=['group_role','permissions','frequency','type','kind'].includes(field)?I18n.text(String(label)):String(label);
  return `<span class="profileReviewText">${esc(translated)}</span>`;
 },
 record(row,depth,address=false){
  if(!row||typeof row!=='object'||Array.isArray(row))return this.value(row,'',depth);
  if(!Object.keys(row).length)return `<span>${ui('Ingen oplysninger')}</span>`;
  const entries=address?['road','numbers','count','type'].filter(k=>k in row).map(k=>[k,k==='count'&&row.count_unknown?I18n.text('Ukendt'):row[k]]):Object.entries(row);
  return `<dl class="profileReviewFields">${entries.map(([key,value])=>`<div><dt>${ui(this.label(key))}</dt><dd>${this.value(value,key,depth)}</dd></div>`).join('')}</dl>`;
 },
 boundary(points){
  const good=points.slice(0,2000).filter(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite));
  if(!good.length)return `<span>${ui('Ingen grænse')}</span>`;
  const xs=good.map(p=>p[0]),ys=good.map(p=>p[1]),minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(280/(maxX-minX||1),140/(maxY-minY||1));
  const path=good.map(([x,y])=>[(20+(x-minX)*scale).toFixed(2),(160-(y-minY)*scale).toFixed(2)].join(',')).join(' ');
  return `<svg class="profileReviewBoundary" viewBox="0 0 320 180" role="img" ${I18n.attribute('aria','Den gemte grænse')}><polygon points="${path}" fill="#47a3dc33" stroke="#4793c2" stroke-width="2"/></svg><details><summary>${ui('{count} hjørner',{count:good.length})}</summary><ol class="profileReviewList">${good.map(([x,y])=>`<li>${esc(x.toFixed(6))} / ${esc(y.toFixed(6))}</li>`).join('')}</ol></details>`;
 }
};
