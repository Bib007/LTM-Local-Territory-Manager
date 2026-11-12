"""Local S-12 text supplements for authoritative DAR/geographic rows."""
import hashlib
import json
import unicodedata


def token(card):
    """Optimistic concurrency token for one card's source and manual front labels."""
    raw={'geo_addresses':card.get('geo_addresses') or [],
         'front_line_overrides':card.get('front_line_overrides') or []}
    return hashlib.sha256(json.dumps(raw,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()


def _match(rows, overrides):
    """Only attach a saved override when its address membership has one unique match.

    DAR can rename a road or extend an interval without changing the selected
    addresses. Ambiguous splits/merges retain the saved override for manual
    review instead of applying it to the wrong street.
    """
    candidates={}
    for idx,item in enumerate(overrides):
        if not isinstance(item,dict):continue
        ids=set(item.get('source_ids') or [])
        targets=[j for j,row in enumerate(rows) if ids.intersection(row.get('source_ids') or [])]
        if len(targets)==1:candidates.setdefault(targets[0],[]).append(idx)
    matched={j:entries[0] for j,entries in candidates.items() if len(entries)==1}
    pending=[item for idx,item in enumerate(overrides) if idx not in matched.values()]
    return matched,pending


def apply_overrides(card, rows):
    """Attach free text to transient front rows alongside their original DAR values."""
    saved=card.get('front_line_overrides') or []
    if not isinstance(saved,list):saved=[]
    matched,pending=_match(rows,saved)
    for j,row in enumerate(rows):
        item=saved[matched[j]] if j in matched else {}
        row['extra_road']=item.get('road') or ''
        row['extra_numbers']=item.get('numbers') or ''
    card['front_label_unmatched']=len(pending)


def _custom(value, limit):
    if value is None:return None
    if not isinstance(value,str) or not value.strip() or len(value.strip())>limit:
        raise ValueError('Kontrollér den manuelle tekst og dens længde.')
    value=value.strip()
    # Control/bidi formatting, newlines and hidden characters are unsafe in
    # printed labels and make SVG/PDF line breaks inconsistent.
    if any(unicodedata.category(c) in ('Cc','Cf','Cs') for c in value):
        raise ValueError('Manuel tekst må ikke indeholde linjeskift eller skjulte styretegn.')
    return value


def save(store,data):
    card=store.require('cards',data['card_id'])
    if not card.get('geo_addresses'):
        raise ValueError('DAR-overstyring kræver et kort med valgte geografiske adresser.')
    if not isinstance(data.get('expected_token'),str) or data['expected_token']!=token(card):
        raise ValueError('DAR-grundlaget eller en anden redigering er ændret. Genåbn vejlinjerne før du gemmer.')
    from geography import front_summaries
    working={'geo_addresses':card['geo_addresses']}
    front_summaries([working])
    source_rows=[row for row in working.get('front_addresses',[]) if row['source_ids']]
    submitted=data.get('rows')
    if not isinstance(submitted,list) or len(submitted)!=len(source_rows) or len(submitted)>300:
        raise ValueError('Vejlinjerne er ændret. Genåbn redigeringen.')
    previous=card.get('front_line_overrides') or []
    if not isinstance(previous,list):raise ValueError('Gemte forsidetekster har et ugyldigt format.')
    matched,pending=_match(source_rows,previous)
    clear_unmatched=data.get('clear_unmatched',False)
    if not isinstance(clear_unmatched,bool):raise ValueError('Ugyldigt valg for nulstilling til DAR.')
    if clear_unmatched:pending=[]
    updated=[]
    for source,entry in zip(source_rows,submitted):
        if not isinstance(entry,dict) or entry.get('source_ids')!=source.get('source_ids'):
            raise ValueError('DAR-adresserne er ændret. Genåbn redigeringen.')
        road=_custom(entry.get('road'),120)
        numbers=_custom(entry.get('numbers'),100)
        if road and numbers and len(road)+len(numbers)>180:
            raise ValueError('Den samlede vejlinje er for lang.')
        if road or numbers:
            updated.append({'source_ids':source['source_ids'],'dar_road':source['road'],
                'dar_numbers':source['numbers'],'road':road,'numbers':numbers})
    # Preserve unresolved deliberate edits across DAR sync/split/merge.
    updated.extend(pending)
    if updated!=previous:
        card['front_line_overrides']=updated
        card['front_revision']=True
        store.put('cards',card)
    return {'id':card['id'],'unmatched':len(pending)}
