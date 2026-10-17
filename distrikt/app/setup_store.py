"""One-time local setup and IB imports; previews in RAM, writes in existing files."""
import csv
import io
import re
import time
import uuid
from collections import Counter,defaultdict
from datetime import date
from admin_store import signature
from geography import valid_polygon,point_in_polygon
from territory_partition import partition,contained,overlaps

IB_HEADERS=['kortnummer','vejnavn','husnummer','postnummer','etage','dør','dato']

def ib_template():return ('\ufeff'+';'.join(IB_HEADERS)+'\r\n').encode('utf-8')
def clean(value):return re.sub(r'\s+',' ',str(value or '').strip()).casefold()
def ib_number(a):return a['number']+(', '+' '.join(str(a[k]) for k in ('floor','door') if a.get(k)) if a.get('floor') or a.get('door') else '')
def bounded_int(value,low,high,label):
    try:n=int(str(value))
    except (ValueError,TypeError):raise ValueError(label+' skal være et helt tal.') from None
    if not low<=n<=high:raise ValueError(f'{label} skal være mellem {low} og {high}.')
    return n

def defaults(data):
    numbering=data.get('numbering','hundreds')
    if numbering not in ('continuous','hundreds','prefix'):raise ValueError('Vælg en nummereringsmetode.')
    start=bounded_int(data.get('start',100),1,999999,'Startnummer')
    block=bounded_int(data.get('block',100),10,10000,'Områdeblok')
    if numbering=='hundreds' and (block%100 or start%100):raise ValueError('Områdeblok og startnummer skal være hele 100-tal.')
    return {'numbering':numbering,'start':start,'block':block,'target':bounded_int(data.get('target',50),1,1000,'Besøg pr. kort')}


class SetupStore:
    def setup_signature(self,ib=False):
        return signature([self.main_boundary(),self.all('cards')+self.all('cards',deleted=True),self.all('ignored'),[a for a in self.all('geo') if a.get('entity') in ('address','road')],[a for a in self.all('settings') if a.get('id')!='config'],self.all('ib') if ib else []])
    def setup_remember(self,kind,payload):
        now=time.monotonic();self._setup_previews={k:v for k,v in self._setup_previews.items() if v['until']>now}
        if len(self._setup_previews)>=6:self._setup_previews.pop(next(iter(self._setup_previews)))
        token=uuid.uuid4().hex;self._setup_previews[token]={'kind':kind,'until':now+1800,'expected':self.setup_signature(ib=kind=='ib'),'payload':payload}
        return token
    def setup_require_preview(self,data,kind):
        p=self._setup_previews.get(data.get('token'))
        if not p or p['kind']!=kind or p['until']<=time.monotonic():raise ValueError('Forhåndsvisningen er udløbet. Lav et nyt forslag.')
        if self.setup_signature(ib=kind=='ib')!=p['expected']:raise ValueError('Kort, adresser, veje, områder eller IB er ændret. Lav en ny forhåndsvisning.')
        return p['payload']
    def setup_plan(self,data):
        options=defaults(data);main=self.main_boundary()
        if not main:raise ValueError('Gem den samlede ydergrænse først.')
        raw_areas=data.get('areas')
        if not isinstance(raw_areas,list) or not 1<=len(raw_areas)<=50:raise ValueError('Tilføj 1–50 områder.')
        from store import clean_text
        areas=[];seen=set();corners=0
        for i,raw in enumerate(raw_areas):
            if not isinstance(raw,dict):raise ValueError('Ugyldigt område.')
            ident=raw.get('id') or ''
            existing=self.require('settings',ident) if ident else None
            if existing and (ident=='config' or existing.get('entity')):raise ValueError('Vælg et gyldigt område.')
            name=clean_text(existing['name'] if existing else raw.get('name'),80,True)
            if clean(name) in seen:raise ValueError('Et område er valgt flere gange.')
            seen.add(clean(name))
            if not ident and any(clean(a.get('name'))==clean(name) for a in self.all('settings')+self.all('settings',deleted=True) if a.get('id')!='config' and not a.get('entity')):raise ValueError('Området '+name+' findes allerede. Vælg det fra listen.')
            points=raw.get('polygon') or (main['points'] if len(raw_areas)==1 else None)
            poly=valid_polygon(points,limit=5000);corners+=len(poly)
            if corners>20000:raise ValueError('Områdegrænserne må samlet have højst 20.000 hjørner. Opret færre områder ad gangen.')
            if not contained(poly,main['points']):raise ValueError('Områdegrænsen for '+name+' går udenfor ydergrænsen.')
            for other in areas:
                if overlaps(poly,other['polygon']):raise ValueError('Områdegrænserne for '+name+' og '+other['name']+' overlapper. Ret dem før oprettelse.')
            prefix=clean_text(raw.get('prefix'),10).upper()
            if options['numbering']=='prefix' and not re.fullmatch(r'[A-ZÆØÅ]{1,6}',prefix):raise ValueError('Angiv 1–6 områdeforbogstaver, fx F eller B.')
            kind=raw.get('kind','Ukendt')
            if kind not in ('By','Land','Ukendt'):raise ValueError('Vælg områdets distriktstype.')
            start=options['start'] if options['numbering']=='continuous' else bounded_int(raw.get('start') or (options['start']+i*options['block'] if options['numbering']=='hundreds' else options['start']),1,999999,'Områdets startnummer')
            if options['numbering']=='hundreds' and start%100:raise ValueError('Områdets startnummer skal være et helt 100-tal.')
            if options['numbering']=='hundreds' and any(max(start,a['start'])<min(start+options['block'],a['start']+options['block']) for a in areas):raise ValueError('Områdernes nummerblokke overlapper. Vælg startnumre med plads til hele blokken.')
            areas.append({'id':ident,'name':name,'polygon':poly,'kind':kind,'prefix':prefix,'start':start,'target':bounded_int(raw.get('target') or options['target'],1,1000,'Besøg pr. kort')})
        cards=self.all('cards')+self.all('cards',deleted=True)
        owned={a for c in cards if not c.get('archived') for a in c.get('address_ids',[])}
        from geo_store import address_key
        owned_keys={address_key(a) for c in cards if not c.get('archived') for a in c.get('geo_addresses',[])}
        ignored={i['address_id'] for i in self.all('ignored')};all_addresses=[a for a in self.all('geo') if a.get('entity')=='address'];ignored_keys={address_key(a) for a in all_addresses if a['id'] in ignored};eligible=[];excluded=Counter();seen_addresses=set()
        for a in sorted(all_addresses,key=lambda a:(not a.get('verified'),a['id'])):
            key=address_key(a)
            if key in seen_addresses:excluded['duplicates']+=1;continue
            seen_addresses.add(key)
            if a.get('retired'):excluded['retired']+=1;continue
            if a['id'] in ignored or key in ignored_keys:excluded['ignored']+=1;continue
            if a['id'] in owned or address_key(a) in owned_keys:excluded['assigned']+=1;continue
            if not point_in_polygon([a['lng'],a['lat']],main['points']):excluded['outside']+=1;continue
            eligible.append(a)
        if len(eligible)>50000:raise ValueError('Opret højst 50.000 adresser ad gangen. Vælg et mindre område.')
        buckets=[[] for _ in areas];uncovered=0
        boxes=[(min(p[0] for p in a['polygon']),min(p[1] for p in a['polygon']),max(p[0] for p in a['polygon']),max(p[1] for p in a['polygon'])) for a in areas]
        for a in eligible:
            point=[a['lng'],a['lat']];owners=[i for i,(region,(w,s,e,n)) in enumerate(zip(areas,boxes)) if w<=a['lng']<=e and s<=a['lat']<=n and point_in_polygon(point,region['polygon'])]
            if len(owners)>1:raise ValueError('Adressen '+a['label']+' ligger på flere områdegrænser. Flyt en grænse en smule.')
            if not owners:uncovered+=1
            else:buckets[owners[0]].append(a)
        local_roads=[r for r in self.all('geo') if r.get('entity')=='road']
        proposed=[];next_number=options['start'];numbers={c['number'].casefold() for c in cards}
        for i,(region,members) in enumerate(zip(areas,buckets)):
            if not members:continue
            parts=partition(region['polygon'],members,region['target'],roads=local_roads)
            if options['numbering']=='hundreds' and len(parts)>options['block']:raise ValueError('Området '+region['name']+' kræver flere numre end den valgte områdeblok. Vælg en større blok.')
            for j,part in enumerate(parts):
                if len(part['members'])>10000:raise ValueError('Et kort har over 10.000 adresser. Inddel det berørte område manuelt.')
                number=str(next_number if options['numbering']=='continuous' else region['start']+j)
                if options['numbering']=='prefix':number=region['prefix']+number
                next_number+=1
                if number.casefold() in numbers:raise ValueError('Kortnummer '+number+' findes allerede eller er reserveret i Gendan ved fejl. Vælg et andet startnummer eller forbogstav.')
                numbers.add(number.casefold());roads=Counter()
                for a in part['members']:roads[a['road']]+=a.get('count',1)
                road=sorted(roads,key=lambda r:(-roads[r],r.casefold()))[0]
                proposed.append({'key':str(len(proposed)),'number':number,'name':(region['name']+' – '+road)[:100],'area_index':i,'area_name':region['name'],'kind':region['kind'],'polygon':part['polygon'],'address_ids':[a['id'] for a in part['members']],'visits':part['visits'],'warning':part['warning']})
        if not proposed:raise ValueError('Ingen ledige adresser indenfor de valgte områder. Hent adresser først, eller kontrollér eksisterende kort og Se bort fra.')
        if len(proposed)>500:raise ValueError('Forslaget giver over 500 kort. Opret færre områder ad gangen.')
        payload={'areas':areas,'cards':proposed,'options':options,'uncovered':uncovered,'excluded':dict(excluded),'visits':sum(c['visits'] for c in proposed)}
        return dict(payload,token=self.setup_remember('cards',payload))
    def setup_mutate(self,action,data):
        if action=='setup.card-import.preview':
            from card_import import preview
            return preview(self,data)
        if action=='setup.card-import.apply':
            from card_import import apply
            return apply(self,data)
        if action=='setup.onboarding.save':
            answers=data.get('answers')
            choices={'mode':('desk','map'),'boundary':('yes','later'),'cards':('numbers','excel','auto','manual'),'ib':('yes','later')}
            if not isinstance(answers,dict) or set(answers)!=set(choices) or any(answers[k] not in allowed for k,allowed in choices.items()):raise ValueError('Vælg et svar på alle spørgsmål.')
            if answers['mode']=='desk' and (answers['boundary']!='later' or answers['cards']=='auto'):raise ValueError('Automatisk inddeling kræver kortfunktion.')
            config=dict(self.require('settings','config'));config['onboarding']={'version':1,'answers':dict(answers),'completed':True};self.put('settings',config);return {}
        if action=='setup.preview':return self.setup_plan(data)
        if action=='setup.adjust.preview':
            import copy
            from territory_partition import area as polygon_area
            plan=self.setup_require_preview(data,'cards');edits=data.get('cards')
            if not isinstance(edits,list) or len(edits)!=len(plan['cards']):raise ValueError('Kontrollér alle kortgrænser samlet.')
            by_key={e.get('key'):e for e in edits if isinstance(e,dict)}
            if len(by_key)!=len(plan['cards']):raise ValueError('Et kort mangler eller er gentaget.')
            revised=copy.deepcopy(plan);address_lookup={a['id']:a for a in self.all('geo') if a.get('entity')=='address'}
            for c in revised['cards']:
                e=by_key.get(c['key'])
                if not e:raise ValueError('Et kort mangler.')
                c['polygon']=valid_polygon(e.get('polygon'),limit=5000)
                if len({tuple(p) for p in c['polygon']})!=len(c['polygon']):raise ValueError('Et hjørne er gentaget. Flyt hjørnerne fra hinanden.')
                c['number']=str(e.get('number',c['number'])).strip()[:30];c['name']=str(e.get('name',c['name'])).strip()[:100]
                if not contained(c['polygon'],plan['areas'][c['area_index']]['polygon']):raise ValueError('Kort '+c['number']+' går udenfor sit område. Flyt grænsen tilbage.')
            for i,region in enumerate(plan['areas']):
                cards=[c for c in revised['cards'] if c['area_index']==i]
                if not cards:continue
                for j,c in enumerate(cards):
                    if any(overlaps(c['polygon'],other['polygon']) for other in cards[j+1:]):raise ValueError('Kortgrænser overlapper. Flyt de fælles hjørner sammen.')
                baseline=sum(abs(polygon_area(c['polygon'])) for c in plan['cards'] if c['area_index']==i)
                if abs(sum(abs(polygon_area(c['polygon'])) for c in cards)-baseline)>max(2e-10,baseline*1e-8):raise ValueError('Grænserne efterlader et hul i området. Flyt de fælles hjørner sammen.')
                originals=[c for c in plan['cards'] if c['area_index']==i];old_owner={a:c['key'] for c in originals for a in c['address_ids']};assigned={c['key']:[] for c in cards}
                for ident,old in old_owner.items():
                    a=address_lookup[ident];owners=[c for c in cards if point_in_polygon([a['lng'],a['lat']],c['polygon'])]
                    if not owners:raise ValueError('En adresse falder udenfor kortene efter ændringen. Ret grænserne.')
                    owner=next((c for c in owners if c['key']==old),owners[0]);assigned[owner['key']].append(ident)
                houses={}
                for c in cards:
                    ids=assigned[c['key']]
                    if not ids:raise ValueError('Et kort har ingen adresser. Flyt grænsen tilbage eller lav et nyt forslag.')
                    for ident in ids:
                        a=address_lookup[ident];house=(a['postcode'],clean(a['road']),clean(a['number']))
                        if house in houses and houses[house]!=c['key']:raise ValueError('Et hus med lejligheder bliver delt mellem flere kort. Ret grænsen.')
                        houses[house]=c['key']
                    c['address_ids']=ids;c['visits']=sum(address_lookup[a].get('count',1) for a in ids)
                    c['warning']='Kontrollér besøgstallet efter grænseændringen.' if not region['target']*.5<=c['visits']<=region['target']*1.5 else ''
            return dict(revised,token=self.setup_remember('cards',revised))
        if action=='setup.defaults':
            config=dict(self.require('settings','config'));config['setup_defaults']=defaults(data);self.put('settings',config);return {}
        if action=='setup.apply':
            if data.get('confirm')!='OPRET KORT':raise ValueError('Skriv OPRET KORT for at bekræfte oprettelsen.')
            plan=self.setup_require_preview(data,'cards');edits=data.get('cards')
            if not isinstance(edits,list) or len(edits)!=len(plan['cards']):raise ValueError('Alle kort skal kontrolleres før oprettelse.')
            from store import clean_text
            by_key={e.get('key'):e for e in edits if isinstance(e,dict)}
            if len(by_key)!=len(plan['cards']):raise ValueError('Listen indeholder gentagne eller manglende kort.')
            existing={c['number'].casefold() for c in self.all('cards')+self.all('cards',deleted=True)};prepared=[]
            for c in plan['cards']:
                edit=by_key.get(c['key'])
                if not edit:raise ValueError('Et kort mangler i listen.')
                number=clean_text(edit.get('number'),30,True);name=clean_text(edit.get('name'),100,True)
                if number.casefold() in existing:raise ValueError('Kortnummer '+number+' findes allerede eller er gentaget.')
                existing.add(number.casefold());prepared.append(dict(c,number=number,name=name))
            area_ids={};ids=[]
            for i,a in enumerate(plan['areas']):
                if not any(c['area_index']==i for c in prepared):continue
                area_ids[i]=a['id'] or self._mutate('area.save',{'name':a['name']})['id']
                record=dict(self.require('settings',area_ids[i]));record['setup_polygon']=a['polygon'];record['setup_prefix']=a['prefix'];self.put('settings',record)
            # The immutable, signed source preview has already checked ownership,
            # ignored records and polygons. Read geography once for the whole batch.
            from geography import street_rows
            from geo_store import stamp
            addresses={a['id']:a for a in self.all('geo') if a.get('entity')=='address'}
            for c in prepared:
                members=[addresses[i] for i in c['address_ids']]
                ident=self._mutate('card.save',{'number':c['number'],'name':c['name'],'area_id':area_ids[c['area_index']],'kind':c['kind'],'temporary':False,'addresses':street_rows(members)})['id']
                saved=dict(self.require('cards',ident),address_ids=c['address_ids'],geo_addresses=members,geo_polygon=c['polygon'],geo_outline_source='manual',geo_updated=stamp(),front_revision=True)
                self.put('cards',saved);ids.append(ident)
            config=dict(self.require('settings','config'));config['setup_defaults']=plan['options'];self.put('settings',config)
            return {'ids':ids,'count':len(ids),'visits':plan['visits']}
        if action=='setup.ib.preview':return self.setup_ib_preview(data)
        if action=='setup.ib.apply':
            if data.get('confirm')!='IMPORTÉR IB':raise ValueError('Skriv IMPORTÉR IB for at bekræfte importen.')
            payload=self.setup_require_preview(data,'ib')
            if payload['errors']:raise ValueError('Ret fejlene i importfilen, og lav en ny forhåndsvisning.')
            affected=set()
            for row in payload['rows']:
                if row['status']!='new':continue
                self.put('ib',dict(row['record'],id=uuid.uuid4().hex));affected.add(row['record']['card_id'])
            for ident in affected:
                c=dict(self.require('cards',ident));c['back_revision']=True;self.put('cards',c)
            return {'count':payload['new'],'skipped':payload['existing'],'cards':len(affected)}
        raise ValueError('Ukendt opsætningshandling.')
    def setup_ib_preview(self,data):
        raw=data.get('content','')
        if not isinstance(raw,str) or len(raw.encode('utf-8'))>2000000:raise ValueError('IB-filen må højst fylde 2 MB.')
        sample=raw.lstrip('\ufeff');delimiter=';' if sample.split('\n',1)[0].count(';')>=sample.split('\n',1)[0].count(',') else ','
        aliases={'kortnummer':'card','card':'card','vejnavn':'road','road':'road','husnummer':'number','husnr':'number','number':'number','postnummer':'postcode','postnr':'postcode','postcode':'postcode','etage':'floor','floor':'floor','dør':'door','doer':'door','door':'door','dato':'date','date':'date'}
        reader=csv.DictReader(io.StringIO(sample),delimiter=delimiter)
        if not reader.fieldnames:raise ValueError('Importfilen mangler kolonneoverskrifter.')
        fields=[aliases.get(clean(n)) for n in reader.fieldnames]
        if any(not x for x in fields) or len(set(fields))!=len(fields) or not {'road','number','postcode'}.issubset(fields):raise ValueError('Brug skabelonens kolonner: kortnummer, vejnavn, husnummer, postnummer, etage, dør, dato.')
        from store import valid_day
        default_day=valid_day(data.get('date') or date.today().isoformat())
        cards=[c for c in self.all('cards') if not c.get('archived')];by_number={clean(c['number']):c for c in cards};lookup=defaultdict(list)
        for c in cards:
            for a in c.get('geo_addresses') or c.get('imported_addresses') or [self.get('geo',i) for i in c.get('address_ids',[])]:
                if a:lookup[(clean(a['road']),clean(a['number']),str(a['postcode']))].append((c,a))
        ibs=self.all('ib');seen=set();rows=[]
        for line,values in enumerate(reader,2):
            if line>5001:raise ValueError('Importfilen må højst indeholde 5.000 linjer.')
            if not any(str(v or '').strip() for v in values.values()):continue
            row={'line':line,'status':'error'}
            try:
                if None in values or any(v is None for v in values.values()):raise ValueError('Linjen har et forkert antal kolonner.')
                v={aliases[clean(k)]:str(value).strip() for k,value in values.items()}
                if any(len(value)>250 for value in v.values()):raise ValueError('Et felt er for langt.')
                if not v.get('road') or not v.get('number') or not re.fullmatch(r'\d{4}',v.get('postcode','')):raise ValueError('Udfyld vejnavn, husnummer og firecifret postnummer.')
                card_number=clean(v.get('card'))
                if card_number and card_number not in by_number:raise ValueError('Kortnummeret findes ikke.')
                candidates=lookup.get((clean(v['road']),clean(v['number']),v['postcode']),[])
                if card_number:candidates=[(c,a) for c,a in candidates if c['id']==by_number[card_number]['id']]
                candidates=[(c,a) for c,a in candidates if clean(a.get('floor'))==clean(v.get('floor')) and clean(a.get('door'))==clean(v.get('door'))]
                if not candidates:raise ValueError('Adressen findes ikke entydigt på kortene. Kontrollér husnummer, etage/dør og kortets adressevalg.')
                if len(candidates)!=1:raise ValueError('Flere adresser matcher. Angiv korrekt kortnummer, etage og dør.')
                c,a=candidates[0];key=(c['id'],a['id']);day=valid_day(v.get('date') or default_day)
                duplicate=key in seen or any(i['card_id']==c['id'] and (i.get('address_id')==a['id'] or clean(i.get('road'))==clean(a['road']) and clean(i.get('number')) in (clean(ib_number(a)),clean(a['number']))) for i in ibs)
                row.update(status='existing' if duplicate else 'new',card_number=c['number'],label=a.get('label') or a['road']+' '+ib_number(a),date=day,record={'card_id':c['id'],'address_id':a['id'],'road':a['road'],'number':ib_number(a),'date':day});seen.add(key)
            except (ValueError,TypeError) as error:row['error']=str(error)
            rows.append(row)
        if not rows:raise ValueError('Importfilen indeholder ingen IB-linjer. Udfyld skabelonen først.')
        payload={'rows':rows,'new':sum(r['status']=='new' for r in rows),'existing':sum(r['status']=='existing' for r in rows),'errors':sum(r['status']=='error' for r in rows)}
        return dict(payload,token=self.setup_remember('ib',payload))
