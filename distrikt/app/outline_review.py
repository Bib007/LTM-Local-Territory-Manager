"""Read-only proposals for boundaries that require explicit neighbour approval."""
from territory_outline import suggest_outline, meets
from admin_store import signature


def propose(selected, addresses, cards, target_id, outline, status):
    neighbors=sorted((c for c in cards if c['id']!=target_id and not c.get('archived')
                      and len(c.get('geo_polygon') or [])>=3),key=lambda c:c['id'])
    changes=[];reason=''
    if status in ('unavailable','crossing') and selected:
        candidate,candidate_status=suggest_outline(selected,addresses,[])
        if not candidate:
            # A boundary cannot separate two distinct entrances at one point.
            chosen={(a['id']) for a in selected}
            points={(a['lng'],a['lat']) for a in selected}
            shared=any(a['id'] not in chosen and not a.get('retired') and
                       (a['lng'],a['lat']) in points for a in addresses)
            reason=('Valgte og fravalgte adresser deler samme koordinat. Kontrollér adressevalget ved denne indgang.' if shared else
                    'Der kunne ikke beregnes en sammenhængende grænse uden fravalgte adresser. Kontrollér adressevalget eller tegn grænsen manuelt.')
        else:
            blocking=[c for c in neighbors if meets(candidate,c['geo_polygon'],0)]
            fixed=[c['geo_polygon'] for c in neighbors if c not in blocking]
            lookup={a['id']:a for a in addresses}
            for c in blocking:
                # Retain recorded entrances as well as newer DAR coordinates.
                # Pending address changes must not silently put an old marker outside.
                known=[*c.get('geo_addresses',[]),*(lookup[ident] for ident in c.get('address_ids',[]) if ident in lookup)]
                members=list({(a['id'],a['lng'],a['lat']):a for a in known}.values())
                missing=set(c.get('address_ids',[]))-{a['id'] for a in members}
                if not members or missing:
                    reason='Nabokort {number} mangler kendte adressekoordinater. Grænsen kan ikke ændres automatisk uden at kende kortets adresser.'
                    break
                # Keep every owned entrance, including legacy/retired ones. No assignments move.
                revised,revised_status=suggest_outline(members,[*addresses,*members],[candidate,*fixed])
                if not revised or revised_status!='clear' or meets(revised,candidate,0):
                    reason='Nabokort {number} kan ikke få en sikker sammenhængende grænse med alle sine adresser. Kontrollér de to kort manuelt.'
                    break
                changes.append({'id':c['id'],'number':c['number'],'before':c['geo_polygon'],'polygon':revised})
                fixed.append(revised)
            if reason:
                changes=[];outline=[];status='unavailable'
                return {'outline':outline,'outline_status':status,'outline_changes':changes,
                        'outline_reason':reason,'outline_reason_number':c['number']}
            outline=candidate;status='neighbors' if changes else candidate_status
    return {'outline':outline,'outline_status':status,'outline_changes':changes,'outline_reason':reason}


def expected(selected, addresses, cards, result):
    # Include membership and geometry, not a global revision that unrelated notes change.
    context=[{'id':c['id'],'archived':c.get('archived',False),'address_ids':c.get('address_ids',[]),
              'geo_addresses':c.get('geo_addresses',[]),'geo_polygon':c.get('geo_polygon',[])}
             for c in sorted(cards,key=lambda c:c['id'])]
    return signature([sorted(a['id'] for a in selected),sorted(addresses,key=lambda a:a['id']),context,result])
