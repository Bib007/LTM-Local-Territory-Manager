"""Reviewed DAR suggestions from existing street lines; no network or writes."""
import re
from admin_store import signature
from geography import in_number_range, number_key


def ranges(value):
    value=str(value or '').strip()
    # Separate street sides commonly use '&': 23-29 & 24-26.
    # Keep ordinary unqualified ranges unchanged; only infer sides in this notation.
    sides=bool(re.search(r'&|\bog\b|\band\b',value,re.I))
    result=[]
    for part in re.split(r'[,;&]|\bog\b|\band\b',value,flags=re.I):
        part=part.strip();parity=None
        note=re.search(r'\s*\(\s*(?:kun\s+|only\s+)?(lige|ulige|even|odd)(?:\s+(?:husnumre|numre|numbers?))?\s*\)\s*$',part,re.I)
        if note:parity=note[1].lower();part=part[:note.start()].strip()
        only=re.fullmatch(r'(?:kun\s+|only\s+)?(lige|ulige|even|odd)(?:\s+(?:husnumre|numre|numbers?))?',part,re.I)
        if only:parity=only[1].lower();part='hele vejen'
        parity={'lige':'even','ulige':'odd'}.get(parity,parity)
        if re.fullmatch(r'hele\s+vejen|alle(?:\s+(?:husnumre|numre))?|(?:the\s+)?(?:whole|entire)\s+(?:street|road)|all(?:\s+(?:house\s+)?numbers)?',part,re.I):
            result.append((None,None,parity or 'all'));continue
        match=re.fullmatch(r'\s*(?:nr\.?\s*)?(\d+\s*[A-Za-zÆØÅæøå]?)\s*(?:[-–—]\s*(\d+\s*[A-Za-zÆØÅæøå]?))?\s*',part,re.I)
        if not match:raise ValueError('Vejlinjens nummerinterval er uklart. Ret det før adresseforslaget.')
        start,end=match.groups();start=re.sub(r'\s+','',start);end=re.sub(r'\s+','',end) if end else start
        if parity is None and sides and number_key(start)[0]%2==number_key(end)[0]%2:
            parity='odd' if number_key(start)[0]%2 else 'even'
        parity=parity or 'all'
        in_number_range(start,start,end,parity)
        result.append((start,end,parity))
    return result


def includes(number,part):
    start,end,parity=part
    if start is None:return parity=='all' or number_key(number)[0]%2==(parity=='odd')
    return in_number_range(number,start,end,parity)


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
    records=store.all('geo')
    downloads=[r.get('complete_road') for r in records if r.get('entity')=='download' and isinstance(r.get('complete_road'),dict)]
    if data.get('planning_only'):
        # A complete-road marker is written only for a successful full DAR road import.
        # An individual address/area import is not evidence of a complete street.
        # Check for actual local address records too, so a stale empty marker cannot
        # silently produce a supposedly usable offline suggestion.
        complete={(d.get('road','').casefold(),d.get('postcode')) for d in downloads if isinstance(d.get('road'),str)}
        available={(a.get('road','').casefold(),a.get('postcode')) for a in records
                   if a.get('entity')=='address' and isinstance(a.get('road'),str)}
        local_roads=[r for r in roads if (r['road'].casefold(),r['postcode']) in complete & available]
        refresh=data.get('refresh_downloaded',False)
        if type(refresh) is not bool:raise ValueError('Ugyldigt valg af DAR-opdatering.')
        download_roads=roads if refresh else [r for r in roads if r not in local_roads]
        return {'roads':roads,'local_roads':local_roads,'download_roads':download_roads,
                'source_expected':source,'address_ids':[]}
    selected={};evidence=[]
    for plan in plans:
        road,post=plan['road'],plan['postcode']
        if not any(d.get('road','').casefold()==road.casefold() and d.get('postcode')==post for d in downloads):
            raise ValueError('Hent hver bekræftet vej fra DAR før adresseforslaget.')
        units=[a for a in records if a.get('entity')=='address' and a.get('road','').casefold()==road.casefold() and a.get('postcode')==post]
        evidence.extend(units)
        matches=[a for a in units if not a.get('retired') and any(includes(a['number'],part) for part in plan['ranges'])]
        if not matches:raise ValueError('En vejlinje har ingen aktive DAR-adresser i intervallet. Kontrollér vejnavn, postnummer og numre.')
        for a in matches:selected[a['id']]=a
    if len(selected)>10000:raise ValueError('For mange adresser.')
    return {'roads':roads,'source_expected':source,'street_expected':signature([source,posts,evidence]),'address_ids':list(selected)}
