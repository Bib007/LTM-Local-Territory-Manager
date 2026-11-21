'use strict';
/* Read-only, on-demand statistics; the server returns aggregates, not raw events. */
const UsageStatsUI={
 data:null,busy:false,selected:'all',
 hours(minutes){return (Number(minutes||0)/60).toLocaleString(I18n.language()==='en'?'en-GB':'da-DK',{minimumFractionDigits:1,maximumFractionDigits:1})+' '+I18n.text('timer');},
 count(n){return Number(n||0).toLocaleString(I18n.language()==='en'?'en-GB':'da-DK');},
 date(value){return value?new Date(value).toLocaleDateString(I18n.language()==='en'?'en-GB':'da-DK'):I18n.text('Ingen registrering');},
 key(user){return user.actor_id===null?'_shared_':user.actor_id;},
 name(user){return user.actor_id===null?I18n.text('Fælles login / ukendt bruger'):user.actor_name||I18n.text('Tidligere bruger');},
 html(){
  return '<section class="panel" id="settings-usage"><h2>'+ui('Brugsstatistik')+' <small>Beta</small></h2>'
   +'<p>'+ui('Se estimeret redigeringstid for hele systemet og for hver bruger, også ud fra tidligere gemte ændringer.')+'</p>'
   +'<p class="hint">'+ui('To gemte redigeringer med højst 15 minutters mellemrum tæller som en aktiv periode. Enkeltstående handlinger og længere pauser giver ingen minutter. Læsetid, ikke-gemte ændringer og tiden før første eller efter sidste handling kan ikke genskabes.')+'</p>'
   +'<div class="actions"><button type="button" data-usage="load" '+(this.busy?'disabled':'')+'>'+ui(this.data?'Opdater statistik':'Beregn statistik')+'</button></div>'
   +'<div id="usageStatsResult" aria-live="polite">'+(this.data?this.results():'<p class="hint">'+ui('Tryk Beregn statistik for at analysere den gemte aktivitetslog. Ingen data ændres.')+'</p>')+'</div></section>';
 },
 results(){
  const d=this.data;
  if(!d||!d.actions)return '<p class="hint">'+ui('Ingen registrerede redigeringer endnu. Historisk aktivitet før loggen blev indført kan ikke beregnes.')+'</p>';
  const all=d.users||[],mine=state?.profile?.user?.id&&all.find(u=>u.actor_id===state.profile.user.id);
  const picked=all.find(u=>this.key(u)===this.selected),months=picked?picked.months:d.months;
  const max=Math.max(1,...months.map(m=>Number(m.minutes)||0));
  const metric=(label,value)=>'<div><small>'+ui(label)+'</small><strong>'+value+'</strong></div>';
  const userRows=all.map(u=>'<tr><td>'+esc(this.name(u))+(u.actor_id&&u.actor_id===state?.profile?.user?.id?' <small>('+ui('dig')+')</small>':'')+'</td><td>'+this.hours(u.minutes)+'</td><td>'+this.count(u.actions)+'</td><td>'+this.count(u.active_days)+'</td><td>'+this.date(u.last_at)+'</td></tr>').join('');
  const options=all.map(u=>'<option value="'+esc(this.key(u))+'" '+(this.selected===this.key(u)?'selected':'')+'>'+esc(this.name(u))+'</option>').join('');
  const monthly=months.map(m=>'<tr><td>'+esc(m.month)+'</td><td>'+this.hours(m.minutes)+'</td><td>'+this.count(m.actions)+'</td><td style="min-width:110px"><div style="height:8px;background:var(--line);border-radius:5px;overflow:hidden" aria-hidden="true"><span style="display:block;height:100%;width:'+Math.max(0,Math.min(100,Number(m.minutes||0)/max*100))+'%;background:var(--accent,#3984b3)"></span></div></td></tr>').join('');
  return '<div class="metrics">'
   +metric('Estimeret samlet arbejdstid',this.hours(d.person_minutes))
   +metric('Systemet med registreret aktivitet',this.hours(d.system_minutes))
   +metric('Gemte redigeringer',this.count(d.actions))
   +metric('Dage med redigeringer',this.count(d.active_days))
   +(mine?metric('Din estimerede tid',this.hours(mine.minutes)):'')+'</div>'
   +'<p class="hint">'+ui('Registreret fra')+' '+this.date(d.first_at)+' '+ui('til')+' '+this.date(d.last_at)+'. '+ui('Arbejdstid summerer brugernes estimerede tid. Systemtid tæller samtidige perioder kun én gang. Tallene er ikke serverens oppetid eller dokumentation for faktisk arbejdstid.')+'</p>'
   +'<h3>'+ui('Fordelt på brugere')+'</h3>'
   +'<div class="tablewrap"><table><thead><tr><th>'+ui('Bruger')+'</th><th>'+ui('Estimerede timer')+'</th><th>'+ui('Redigeringer')+'</th><th>'+ui('Aktive dage')+'</th><th>'+ui('Seneste redigering')+'</th></tr></thead><tbody>'+userRows+'</tbody></table></div>'
   +'<p class="hint">'+ui('Fælles login og handlinger uden sikker brugeridentifikation vises samlet som ukendt. Historiske brugeridentiteter bliver aldrig gættet.')+'</p>'
   +'<h3>'+ui('Udvikling pr. måned')+'</h3><label for="usageStatsFilter">'+ui('Vis udvikling for')+'</label>'
   +'<select id="usageStatsFilter"><option value="all" '+(this.selected==='all'?'selected':'')+'>'+ui('Alle brugere')+'</option>'+options+'</select>'
   +'<div class="tablewrap"><table><thead><tr><th>'+ui('Måned')+'</th><th>'+ui('Estimerede timer')+'</th><th>'+ui('Redigeringer')+'</th><th>'+ui('Aktivitet')+'</th></tr></thead><tbody>'
   +(monthly||'<tr><td colspan="4">'+ui('Ingen aktivitet i perioden.')+'</td></tr>')+'</tbody></table></div>'
   +'<p class="hint">'+ui('Månedstal for arbejdstid summerer brugernes intervaller. Et interval over månedsskiftet tilskrives måneden for den sidste redigering.')+'</p>';
 },
 async load(button){
  if(this.busy)return;
  this.busy=true;button.disabled=true;
  const root=document.getElementById('settings-usage');
  const result=document.getElementById('usageStatsResult');
  if(result)result.textContent=I18n.text('Beregner statistik…');
  try{
   const response=await(await api('/api/usage-statistics')).json();
   if(!response||!Array.isArray(response.users)||!Array.isArray(response.months))throw new Error(I18n.text('Statistikken kunne ikke læses.'));
   this.data=response;
   if(root?.isConnected){const node=root.querySelector('#usageStatsResult');if(node)node.innerHTML=this.results();}
  }catch(error){
   if(root?.isConnected){const node=root.querySelector('#usageStatsResult');if(node)node.textContent=error.message||I18n.text('Statistikken kunne ikke læses.');}
  }finally{
   this.busy=false;
   if(button.isConnected){button.disabled=false;button.textContent=I18n.text('Opdater statistik');}
  }
 }
};
document.addEventListener('click',e=>{const b=e.target.closest('[data-usage="load"]');if(!b||b.disabled)return;e.preventDefault();UsageStatsUI.load(b);});
document.addEventListener('change',e=>{if(e.target.id!=='usageStatsFilter')return;UsageStatsUI.selected=e.target.value;const node=document.getElementById('usageStatsResult');if(node&&UsageStatsUI.data)node.innerHTML=UsageStatsUI.results();});
