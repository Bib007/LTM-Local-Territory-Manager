'use strict';
// Local parsing previews use the existing mutation permissions; there is no apply action here.
const ColumnImportUI={instances:{},
 create(kind,source,options){this.instances[kind]?.dispose();const mapper={kind,source,options,sequence:0,disposed:false,sheet:'',sheets:[],header:1,description:null,mapping:[],busy:false,error:null,
  host(){return el(kind==='card'?'cardImportMapping':'setupIBMapping');},
  current(){return !this.disposed&&options.current();},
  dispose(){this.disposed=true;this.sequence++;this.source=null;},
  data(){return {...this.source,sheet:this.sheet||null,header_row:this.header,column_map:this.mapping.slice()};},
  invalidate(){this.sequence++;this.error=null;options.invalidate();},
  valid(){const fields=this.description?.fields||[],selected=this.mapping.filter(Boolean);return !!this.description&&!this.busy&&selected.length===new Set(selected).size&&fields.every(f=>!f.required||selected.includes(f.key));},
  async inspect(){const sequence=++this.sequence;this.description=null;this.mapping=[];this.busy=true;this.error=null;options.invalidate();this.paint();
   try{const r=await(await api('/api/mutate',{action:kind==='card'?'setup.card-import.inspect':'setup.ib.inspect',data:this.data()})).json();if(sequence!==this.sequence||!this.current())return;const d=r.result;if(d.needs_sheet)this.sheets=d.sheets;else{this.description=d;this.mapping=Array(d.width).fill(null);}}
   catch(error){if(sequence===this.sequence&&this.current())this.error=error;}
   finally{if(sequence===this.sequence&&this.current()){this.busy=false;this.paint();}}
  },
  html(){const d=this.description,selected=this.mapping.filter(Boolean),missing=(d?.fields||[]).filter(f=>f.required&&!selected.includes(f.key)),duplicates=selected.length!==new Set(selected).size;
   const option=(value,key,isSelected)=>`<option value="${esc(value)}" data-ui="${esc(key)}" ${isSelected?'selected':''}>${esc(I18n.text(key))}</option>`;
   return `<section class="columnImport" data-column-owner="${kind}"><h3>${ui('Vælg filens kolonner')}</h3><p class="hint">${ui('Alle kolonner starter som Ignorér. Vælg selv felterne; kolonnevalg gemmer ingen data.')}</p><p class="hint">${ui('XLSX: sikre heltal og enkle nulformater bevares. Kontrollér prøverækkerne. Usikre værdier skal gemmes som tekst eller ignoreres.')}</p>${this.sheets.length?`<label>${ui('Vælg fane')}<select data-column-change="sheet"><option value="" data-ui="Vælg fane">${esc(I18n.text('Vælg fane'))}</option>${this.sheets.map(n=>`<option value="${esc(n)}" ${this.sheet===n?'selected':''}>${esc(n)}</option>`).join('')}</select></label>`:''}<label class="check"><input type="checkbox" data-column-change="has-header" ${this.header!==null?'checked':''}>${ui('Filen har en overskriftsrække')}</label>${this.header!==null?`<label>${ui('Overskriftsrækkens nummer')}<input type="number" min="1" max="20001" data-column-change="header" value="${this.header}"></label>`:''}${this.busy?`<p role="status">${ui('Kontrollerer filen…')}</p>`:''}${this.error?`<div class="formError" role="alert">${I18n.errorHTML(this.error)}</div>`:''}${d?`<p>${ui('{count} datarækker. De første {sample} vises.',{count:d.rows,sample:d.sample.length})}</p><div class="tablewrap"><table><thead><tr><th>${ui('Kilderække')}</th>${d.columns.map(c=>`<th>${ui('Kolonne {number}',{number:c.index+1})}${c.label?` · ${esc(c.label)}`:''}</th>`).join('')}</tr></thead><tbody>${d.sample.map(r=>`<tr><th>${r.line}</th>${r.values.map((v,i)=>`<td>${esc(v)}${(d.issues||[]).filter(x=>x.line===r.line&&x.column===i).map(x=>`<small class="notice">${ui(x.message)}</small>`).join('')}</td>`).join('')}</tr>`).join('')}</tbody></table></div><div class="columnImportFields">${d.columns.map(c=>`<label>${ui('Kolonne {number}',{number:c.index+1})}${c.label?` · ${esc(c.label)}`:` · ${ui('Ingen overskrift')}`}<select data-column-change="field" data-column-index="${c.index}">${option('','Ignorér denne kolonne',!this.mapping[c.index])}${d.fields.map(f=>option(f.key,f.label,this.mapping[c.index]===f.key)).join('')}</select></label>`).join('')}</div><p role="status">${missing.length?ui('Obligatoriske felter mangler')+': '+missing.map(f=>ui(f.label)).join(', '):ui('Alle obligatoriske kolonner er valgt.')}${duplicates?' '+ui('Samme importfelt er valgt flere gange. Ret kolonnevalget.'):''}</p><p class="hint">${this.mapping.some(v=>!v)?ui('Ignorerede kildekolonner: {columns}',{columns:this.mapping.map((v,i)=>v?null:i+1).filter(Boolean).join(', ')}):ui('Ingen ignorerede kildekolonner.')}</p><button data-column-preview ${this.valid()?'':'disabled'}>${ui('Vis normal importkontrol')}</button>`:''}</section>`;
  },
  paint(){if(!this.current())return;const node=this.host();if(node){node.innerHTML=this.html();I18n.applyShell();}}
 };this.instances[kind]=mapper;return mapper;}
};
document.addEventListener('change',async e=>{const n=e.target,owner=n.closest('[data-column-owner]');if(!owner||!n.dataset.columnChange)return;const m=ColumnImportUI.instances[owner.dataset.columnOwner];if(!m?.current())return;
 m.invalidate();if(n.dataset.columnChange==='field'){m.mapping[Number(n.dataset.columnIndex)]=n.value||null;m.paint();return;}
 if(n.dataset.columnChange==='sheet')m.sheet=n.value;
 if(n.dataset.columnChange==='has-header')m.header=n.checked?1:null;
 if(n.dataset.columnChange==='header')m.header=Number(n.value);
 await m.inspect();
});
document.addEventListener('click',async e=>{const b=e.target.closest('[data-column-preview]');if(!b||b.disabled)return;const owner=b.closest('[data-column-owner]'),m=ColumnImportUI.instances[owner.dataset.columnOwner];if(!m?.current()||!m.valid())return;e.preventDefault();await m.options.preview();});
