'use strict';
/* KTM reporting: current territory visit points, all authorized IB, period coverage.
   Summary viewers receive aggregates only; raw card identifiers are never projected. */
const KtmReportUI={
 text(label,localized){return localized?ui(label):esc(label);},
 totals(print=false){
  const totals=state?.report_summary?.territory_totals;
  if(!totals)return '';
  const t=label=>print?esc(I18n.text(label)):ui(label);
  const fields=[['Besøgspunkter på aktuelle distriktskort',totals.visit_points]];
  if(Number.isInteger(totals.ib_total))fields.push(['IB-registreringer i alt',totals.ib_total]);
  const unknown=Number(totals.unknown_visit_cards||0);
  const note=unknown?
   t('Besøgstallet er kun summen af kendte antal på kortene. Kort uden et kendt besøgstal er ikke medregnet:')+' '+unknown+'.':
   t('Besøgstallet er summen af registrerede besøgspunkter på de aktuelle distriktskort. Adresser uden et kort tælles ikke.');
  return '<section class="report boundaryReport"><h2>'+t('Distriktstal')+'</h2><div class="metrics">'+
   fields.map(([label,value])=>'<div><small>'+t(label)+'</small><strong>'+Number(value)+'</strong></div>').join('')+
   '</div><p class="hint">'+note+' '+t('IB-tallet omfatter alle aktive registreringer, også uden en DAR-adresse. Tallene beskriver den nuværende kortbestand.')+'</p></section>';
 },
 ring({total,covered,missing},localized=false){
  const t=label=>this.text(label,localized),safeTotal=Math.max(0,Number(total)||0),safeCovered=Math.max(0,Math.min(safeTotal,Number(covered)||0)),pct=safeTotal?Math.round(safeCovered/safeTotal*100):null;
  const share=safeTotal?safeCovered/safeTotal*100:0;
  return '<div class="reportRings"><figure class="reportRing"><svg viewBox="0 0 100 100" role="img" aria-label="'+(localized?esc(I18n.text('Andel af nuværende distriktskort gennemgået i perioden')):esc('Andel af nuværende distriktskort gennemgået i perioden'))+'"><circle cx="50" cy="50" r="40" fill="none" stroke="#c9d1d8" stroke-width="12"/><circle cx="50" cy="50" r="40" fill="none" stroke="#43836d" stroke-width="12" pathLength="100" stroke-dasharray="'+share+' 100" transform="rotate(-90 50 50)"/><text x="50" y="56" text-anchor="middle" font-size="21" fill="currentColor">'+(pct===null?'—':pct+'%')+'</text></svg><figcaption><h4>'+t('Dækning i perioden')+'</h4><p>'+t('Gennemgåede aktuelle distrikter')+' <strong>'+safeCovered+'</strong></p><p>'+t('Ikke gennemgået i perioden')+' <strong>'+Math.max(0,safeTotal-safeCovered)+'</strong></p></figcaption></figure></div>';
 },
 metrics(mode,localized=false){
  const t=label=>this.text(label,localized),[start,end]=Workspace.periodBounds(mode),s=Workspace.reportInventory(start,end);
  const fields=[['Gennemgange',s.events],['Aktuelle distrikter',s.total],['Ikke gennemgået i perioden',s.missing]];
  return this.ring(s,localized)+'<div class="metrics">'+fields.map(([label,value])=>'<div><small>'+t(label)+'</small><strong>'+value+'</strong></div>').join('')+'</div>';
 },
 missing(mode,localized=false){
  const [start,end]=Workspace.periodBounds(mode),s=Workspace.reportInventory(start,end),t=label=>this.text(label,localized);
  const heading=t('Ikke gennemgåede distriktskort i perioden');
  if(!s.missing)return '<section class="ktmMissing"><h3>'+heading+' · 0</h3><p>'+t('Alle aktuelle distriktskort er registreret gennemgået i perioden.')+'</p></section>';
  const rows=s.missingCards.slice().sort((a,b)=>cmp(a.number,b.number)).map(c=>{
   const title=esc(c.number||'—')+(c.name?' · '+esc(c.name):'')+(c.internal_name?' <small>('+t('Internt navn')+': '+esc(c.internal_name)+')</small>':'');
   return '<tr><td>'+title+'</td><td>'+esc(areaName(c.area_id))+'</td><td>'+((c.last_completed&&/^\d{4}-\d{2}-\d{2}$/.test(c.last_completed))?fmt(c.last_completed):t('Ingen dato registreret'))+'</td></tr>';
  }).join('');
  return '<section class="ktmMissing"><h3>'+heading+' · '+s.missing+' / '+s.total+'</h3>'+
   '<p class="hint">'+t('Listen viser aktuelle kort uden registreret gennemgang i den valgte periode. Sidste dato kan ligge uden for perioden; arkiverede kort er ikke med i listen.')+'</p>'+
   '<div class="tablewrap"><table><thead><tr><th>'+t('Distriktskort')+'</th><th>'+t('Område')+'</th><th>'+t('Senest gennemgået')+'</th></tr></thead><tbody>'+rows+'</tbody></table></div></section>';
 },
 aggregate(summary,selected=''){
  if(!summary)return '';
  const t=label=>this.text(label,true),periods=selected?[[selected,summary.periods[selected]]]:Object.entries(summary.periods);
  return '<section class="report reportOverview"><h2>'+t('Samlet rapportoversigt')+'</h2><p>'+t('Status den')+' '+fmt(summary.as_of)+'</p>'+
   periods.filter(([,v])=>v).map(([kind,v])=>{
    const fields=[['Gennemgange',v.completions],['Aktuelle distrikter',v.territories],['Ikke gennemgået i perioden',v.missing]];
    return '<article class="reportPeriod"><h3>'+t({calendar:'Kalenderår',service:'Tjenesteår',rolling:'Seneste 12 måneder'}[kind])+'</h3><p>'+fmt(v.start)+' – '+fmt(v.end)+'</p>'+
     this.ring({total:v.territories,covered:v.completed_territories,missing:v.missing},true)+
     '<div class="metrics">'+fields.map(([label,value])=>'<div><small>'+t(label)+'</small><strong>'+Number(value)+'</strong></div>').join('')+'</div></article>';
   }).join('')+'<p class="hint">'+t('Gennemgange tæller hver afslutning, mens dækningsprocenten tæller hvert aktuelt kort én gang. Kortlisten kræver adgang til de enkelte kort.')+'</p></section>';
 }
};
