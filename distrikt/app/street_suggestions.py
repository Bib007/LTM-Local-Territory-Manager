"""Reviewed DAR suggestions from existing street lines; no network or writes."""
import re
from admin_store import signature
from geography import in_number_range


def ranges(value):
    result=[]
    for part in re.split(r'[,;]',str(value or '')):
        match=re.fullmatch(r'\s*(\d+[A-Za-zÆØÅæøå]?)\s*(?:[-–—]\s*(\d+[A-Za-zÆØÅæøå]?))?\s*(?:\((lige|ulige|even|odd)\))?\s*',part,re.I)
        if not match:raise ValueError('Vejlinjens nummerinterval er uklart. Ret det før adresseforslaget.')
        start,end,parity=match.groups();end=end or start
        parity={'lige':'even','ulige':'odd'}.get((parity or '').lower(),(parity or 'all').lower())
        in_number_range(start,start,end,parity)
        result.append((start,end,parity))
    return result


def suggest(store,data):
    card=store.require('cards',data.get('card_id'))
    lines=card.get('addresses') or [];posts=data.get('postcodes')
    if card.get('archived') or not 1<=len(lines)<=50 or not isinstance(posts,list) or len(posts)!=len(lines):
        raise ValueError('Vælg et aktivt kort med 1–50 vejlinjer og bekræft postnummeret for hver linje.')
    source=signature([card['id'],lines])
    if data.get('source_expected') and data['source_expected']!=source:
        raise ValueError('Kortets vejlinjer er ændret. Åbn adresseforslaget igen.')
    plans=[]
    for row,post in zip(lines,posts):
        if not isinstance(post,str) or not re.fullmatch(r'\d{4}',post):
            raise ValueError('Bekræft et firecifret postnummer for hver vejlinje.')
        road=str(row.get('road') or '').strip()
        if not road or len(road)>120:raise ValueError('Kontrollér vejnavnet på hver linje før adresseforslaget.')
        plans.append({'road':road,'postcode':post,'ranges':ranges(row.get('numbers'))})
    roads=list({(p['road'].casefold(),p['postcode']):{'road':p['road'],'postcode':p['postcode']} for p in plans}.values())
    if data.get('planning_only'):return {'roads':roads,'source_expected':source,'address_ids':[]}
    records=store.all('geo');downloads=[r.get('complete_road') for r in records if r.get('entity')=='download' and r.get('complete_road')]
    selected={};evidence=[]
    for plan in plans:
        road,post=plan['road'],plan['postcode']
        if not any(d.get('road','').casefold()==road.casefold() and d.get('postcode')==post for d in downloads):
            raise ValueError('Hent hver bekræftet vej fra DAR før adresseforslaget.')
        units=[a for a in records if a.get('entity')=='address' and a.get('road','').casefold()==road.casefold() and a.get('postcode')==post]
        evidence.extend(units)
        matches=[a for a in units if not a.get('retired') and any(in_number_range(a['number'],*part) for part in plan['ranges'])]
        if not matches:raise ValueError('En vejlinje har ingen aktive DAR-adresser i intervallet. Kontrollér vejnavn, postnummer og numre.')
        for a in matches:selected[a['id']]=a
    if len(selected)>10000:raise ValueError('For mange adresser.')
    return {'roads':roads,'source_expected':source,'street_expected':signature([source,posts,evidence]),'address_ids':list(selected)}
