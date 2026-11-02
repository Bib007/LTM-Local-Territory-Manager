"""Local geographic selection, conservative house-number formatting, and DAR decoding.
No network requests in this module. Coordinates use WGS84 [longitude, latitude].
"""
import math
import re
from collections import defaultdict


def number_key(value):
    match = re.fullmatch(r'\s*(\d+)\s*([A-Za-zÆØÅæøå]*)\s*', str(value))
    if not match:
        raise ValueError('Brug et husnummer som 42 eller 42B.')
    return int(match[1]), match[2].upper()


def in_number_range(value, start, end, parity='all'):
    n, suffix = number_key(value)
    a, sa = number_key(start); b, sb = number_key(end)
    if (a, sa) > (b, sb):
        raise ValueError('Fra-nummer skal være før til-nummer.')
    if parity not in ('all', 'even', 'odd'):
        raise ValueError('Vælg alle, lige eller ulige numre.')
    # A numeric end includes its A/B variants; an explicit letter limits that end.
    return (n, suffix) >= (a, sa) and (n < b or n == b and (not sb or suffix <= sb)) and (parity == 'all' or n % 2 == (parity == 'odd'))


def valid_coordinate(point):
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        raise ValueError('Ugyldigt koordinat.')
    lng, lat = float(point[0]), float(point[1])
    if not math.isfinite(lng) or not math.isfinite(lat) or not (7 <= lng <= 16 and 54 <= lat <= 58.5):
        raise ValueError('Kortkoordinatet skal ligge i Danmark.')
    return [round(lng, 7), round(lat, 7)]


def valid_polygon(points,limit=250):
    if not isinstance(points, list) or not 3 <= len(points) <= limit:
        raise ValueError(f'Grænsen skal have 3–{limit} hjørner.')
    points = [valid_coordinate(p) for p in points]
    if len({tuple(p) for p in points}) < 3:
        raise ValueError('Grænsen skal have mindst tre forskellige hjørner.')
    area = sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))
    if abs(area) < 1e-12:
        raise ValueError('Grænsen skal omslutte et areal.')
    def orientation(a, b, c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    segments=sorted([(min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]),i,a,b) for i,a in enumerate(points) for b in [points[(i+1)%len(points)]]])
    active=[]
    for xmin,xmax,ymin,ymax,i,a,b in segments:
        active=[seg for seg in active if seg[1]>=xmin]
        for _,_,cymin,cymax,j,c,d in active:
            if abs(i-j)==1 or {i,j}=={0,len(points)-1} or cymax<ymin or ymax<cymin:continue
            if orientation(a,b,c)*orientation(a,b,d)<0 and orientation(c,d,a)*orientation(c,d,b)<0:
                raise ValueError('Grænsen krydser sig selv. Flyt eller tegn hjørnerne igen.')
        active.append((xmin,xmax,ymin,ymax,i,a,b))
    return points


def point_in_polygon(point, polygon):
    x, y = point; inside = False
    for i, a in enumerate(polygon):
        b = polygon[(i+1) % len(polygon)]
        cross = (x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if abs(cross) < 1e-12 and min(a[0],b[0])-1e-10 <= x <= max(a[0],b[0])+1e-10 and min(a[1],b[1])-1e-10 <= y <= max(a[1],b[1])+1e-10:
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def enclosing_outline(points, padding_m=12):
    """Convex hull with modest padding. A suggested envelope, never a road boundary."""
    points = sorted(set(tuple(valid_coordinate(p)) for p in points))
    if not points:raise ValueError('Vælg mindst én adresse.')
    latitude = sum(p[1] for p in points)/len(points)
    dx = padding_m/(111320*math.cos(math.radians(latitude))); dy = padding_m/111320
    padded = [(x+sx*dx,y+sy*dy) for x,y in points for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1))]
    padded = sorted(set(padded))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in padded:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(padded):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return valid_polygon([list(p) for p in lower[:-1]+upper[:-1]])


def format_numbers(values):
    """Lossless labels: keep gaps and lettered houses explicit, separate sides."""
    values=sorted({str(v).strip().upper() for v in values},key=number_key)
    parts=[]
    for parity in (0,1):
        side=[v for v in values if number_key(v)[0]%2==parity]
        if not side:continue
        labels=[];i=0
        while i<len(side):
            j=i
            # Compress adjacent houses only; a gap starts another interval.
            def adjacent(a,b):
                n,sa=number_key(a);m,sb=number_key(b)
                return (not sa and not sb and m==n+2) or (n==m and len(sb)==1 and ((not sa and sb=='A') or (len(sa)==1 and ord(sb)==ord(sa)+1)))
            while j+1<len(side) and adjacent(side[j],side[j+1]):j+=1
            if j>i:labels.append(side[i]+'–'+side[j])
            else:labels.extend(side[i:j+1])
            i=j+1
        label=' & '.join(labels)
        parts.append(label+(f" ({'lige' if parity==0 else 'ulige'})" if len(values)>1 else ''))
    return ' & '.join(parts)


def street_rows(addresses):
    groups=defaultdict(list)
    for a in addresses:
        groups[(a['road'],a.get('postcode',''),a.get('type','Hus'),number_key(a['number'])[0]%2)].append(a)
    rows=[]
    for (road,post,typ,parity),members in sorted(groups.items(),key=lambda p:(p[0][0].casefold(),p[0][1],p[0][2],p[0][3])):
        houses=defaultdict(list)
        for a in members:houses[a['number']].append(a)
        batch=[]
        def emit():
            rows.append({'road':road,'numbers':format_numbers([a['number'] for a in batch]),'count':sum(a.get('count',1) for a in batch),'type':typ})
        for number in sorted(houses,key=number_key):
            if batch and len(format_numbers([a['number'] for a in batch]+[number]))>100:
                emit();batch=[]
            batch.extend(houses[number])
        if batch:emit()
    return rows


def wgs84_to_utm32(lng,lat):
    """ETRS89 / UTM 32N forward projection (GRS80)."""
    lng,lat=valid_coordinate([lng,lat]);p=math.radians(lat);l=math.radians(lng)
    a=6378137.;e2=.00669438002290;ep=e2/(1-e2);k=.9996
    n=a/math.sqrt(1-e2*math.sin(p)**2);t=math.tan(p)**2;c=ep*math.cos(p)**2;d=math.cos(p)*(l-math.radians(9))
    m=a*((1-e2/4-3*e2**2/64-5*e2**3/256)*p-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*p)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*p)-35*e2**3/3072*math.sin(6*p))
    return [500000+k*n*(d+(1-t+c)*d**3/6+(5-18*t+t*t+72*c-58*ep)*d**5/120),k*(m+n*math.tan(p)*(d*d/2+(5-t+9*c+4*c*c)*d**4/24+(61-58*t+t*t+600*c-330*ep)*d**6/720))]


def utm32_to_wgs84(x,y):
    """Inverse transverse Mercator, ETRS89 / UTM 32N (GRS80). No extra package."""
    a=6378137.0; e2=0.00669438002290; k=.9996; e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    m=float(y)/k; mu=m/(a*(1-e2/4-3*e2**2/64-5*e2**3/256))
    p=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*math.sin(4*mu)+(151*e1**3/96)*math.sin(6*mu)+(1097*e1**4/512)*math.sin(8*mu)
    ep=e2/(1-e2); c=ep*math.cos(p)**2; t=math.tan(p)**2; n=a/math.sqrt(1-e2*math.sin(p)**2); r=a*(1-e2)/(1-e2*math.sin(p)**2)**1.5; d=(float(x)-500000)/(n*k)
    lat=p-(n*math.tan(p)/r)*(d*d/2-(5+3*t+10*c-4*c*c-9*ep)*d**4/24+(61+90*t+298*c+45*t*t-252*ep-3*c*c)*d**6/720)
    lon=math.radians(9)+(d-(1+2*t+c)*d**3/6+(5-2*c+28*t-3*c*c+8*ep+24*t*t)*d**5/120)/math.cos(p)
    return valid_coordinate([math.degrees(lon),math.degrees(lat)])


def decode_dar(items):
    output=[]
    for a in items:
        if str(a.get('status'))!='3' or a.get('virkningtil'):continue
        h=a.get('husnummer') or {};g=(h.get('adgangspunkt') or {}).get('geometri') or {};coords=g.get('coordinates')
        if not coords:raise ValueError('En DAR-adresse mangler koordinater; hentningen blev ikke gemt som komplet.')
        crs=((g.get('crs') or {}).get('properties') or {}).get('name','EPSG:25832')
        point=valid_coordinate(coords) if crs.endswith('4326') else utm32_to_wgs84(*coords) if crs.endswith('25832') else None
        if not point:raise ValueError('Ukendt koordinatsystem fra adressekilden.')
        floor=a.get('etagebetegnelse') or '';door=a.get('doerbetegnelse') or ''
        output.append({'id':'dar:'+a['id_lokalid'],'entity':'address','source':'DAR / Adressevælger','house_id':h['id_lokalid'],'road':h['vejnavn'],'number':h['husnummertekst'],
            'postcode':(h.get('postnummer') or {}).get('postnr',''),'floor':floor,'door':door,'label':a.get('adressebetegnelse',''),
            'lng':point[0],'lat':point[1],'count':1,'type':'Lejlighed' if floor or door else 'Hus','verified':True})
    return output


def front_summaries(cards):
    """Numeric display intervals; missing base numbers split, internal letters do not."""
    for card in cards:
        members=card.get('geo_addresses') or []
        if not members:continue
        # Incomplete legacy snapshots retain their existing street text.
        try:
            groups=defaultdict(list)
            for a in members:groups[(a['road'],a.get('postcode',''),number_key(a['number'])[0]%2)].append(a)
        except (KeyError,ValueError,TypeError):continue
        rows=[]
        for (road,post,parity),units in sorted(groups.items(),key=lambda item:(item[0][0].casefold(),item[0][1],item[0][2])):
            houses=defaultdict(list)
            for a in units:houses[number_key(a['number'])[0]].append(a['number'])
            selected=sorted(houses);intervals=[];start=end=selected[0]
            def label(first,last):
                tail=max(houses[last],key=number_key)
                return str(first) if first==last else str(first)+'–'+tail
            for n in selected[1:]:
                if n!=end+2:
                    intervals.append(label(start,end));start=n
                end=n
            intervals.append(label(start,end))
            rows.append({'road':road,'numbers':' & '.join(intervals)+f" ({'ulige' if parity else 'lige'})",'count':sum(a.get('count',1) for a in units),'type':'Hus'})
        card['front_addresses']=rows
