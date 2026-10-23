"""Deterministic local spatial partitioning of simple WGS84 polygons, no dependencies."""
import math
from collections import defaultdict
from geography import valid_polygon, point_in_polygon


def area(poly):return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))/2

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def strict_inside(p,poly):
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if abs(cross(a,b,p))<1e-12 and min(a[0],b[0])-1e-10<=p[0]<=max(a[0],b[0])+1e-10 and min(a[1],b[1])-1e-10<=p[1]<=max(a[1],b[1])+1e-10:return False
    return point_in_polygon(p,poly)


def edge_crosses(first,second,tolerance=0):
    edges=sorted((min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]),which,a,b) for which,poly in enumerate((first,second)) for a,b in zip(poly,poly[1:]+poly[:1]))
    active=[]
    for left,right,bottom,top,which,a,b in edges:
        active=[e for e in active if e[1]>=left]
        for _,_,low,high,other,c,d in active:
            if other==which or high<bottom or top<low:continue
            if cross(a,b,c)*cross(a,b,d)<-1e-24 and cross(c,d,a)*cross(c,d,b)<-1e-24:
                if tolerance:
                    inner_a,inner_b=(a,b) if which==0 else (c,d)
                    outer_a,outer_b=(c,d) if which==0 else (a,b)
                    if min(segment_distance(inner_a,outer_a,outer_b),segment_distance(inner_b,outer_a,outer_b))<=tolerance:continue
                return True
        active.append((left,right,bottom,top,which,a,b))
    return False


def segment_distance(p,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy or 1)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def contained(inner,outer):
    if inner==outer:return True
    # Store coordinates are rounded to seven decimals (about one centimetre).
    tolerance=1e-7
    def inside(p):return point_in_polygon(p,outer) or any(segment_distance(p,a,b)<=tolerance for a,b in zip(outer,outer[1:]+outer[:1]))
    return all(inside(p) for p in inner) and not edge_crosses(inner,outer,tolerance) and all(inside([(a[0]+b[0])/2,(a[1]+b[1])/2]) for a,b in zip(inner,inner[1:]+inner[:1]))


def overlaps(a,b):
    if max(p[0] for p in a)<=min(p[0] for p in b) or max(p[0] for p in b)<=min(p[0] for p in a) or max(p[1] for p in a)<=min(p[1] for p in b) or max(p[1] for p in b)<=min(p[1] for p in a):return False
    if edge_crosses(a,b) or any(strict_inside(p,b) for p in a) or any(strict_inside(p,a) for p in b):return True
    # A short inward sample handles coincident polygons and collinear overlap.
    for poly,other in ((a,b),(b,a)):
        direction=1 if area(poly)>0 else -1
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
            if length:
                m=[(p[0]+q[0])/2-dy/length*1e-8*direction,(p[1]+q[1])/2+dx/length*1e-8*direction]
                if strict_inside(m,poly) and strict_inside(m,other):return True
    return False


def split_polygon(poly,axis,cut):
    """Compatibility entry point for existing horizontal/vertical proposals."""
    if axis not in (0,1):raise ValueError('Ugyldig skæreakse.')
    return split_polygon_line(poly,(1,0) if axis==0 else (0,1),cut)


def split_polygon_line(poly,normal,cut):
    """Cut along dot(point, normal) == cut; preserve separate components.
    Build original clipped edges plus oriented intervals on the cutting line.
    Cut positions must avoid vertices. Ambiguous/degenerate cuts are rejected.
    """
    length=math.hypot(*normal)
    if not math.isfinite(length) or not length or not math.isfinite(cut):raise ValueError('Ugyldig skærelinje.')
    nx,ny=(v/length for v in normal);cut/=length
    project=lambda p:p[0]*nx+p[1]*ny
    tangent=lambda p:-p[0]*ny+p[1]*nx
    if any(abs(project(p)-cut)<.000000049 for p in poly):raise ValueError('Skærelinjen rammer et hjørne.')
    if area(poly)<0:poly=list(reversed(poly))
    edges=[[],[]];hits=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        side_p=int(project(p)>cut);side_q=int(project(q)>cut)
        if side_p==side_q:edges[side_p].append((tuple(p),tuple(q)));continue
        fraction=(cut-project(p))/(project(q)-project(p));hit=tuple(round(p[i]+fraction*(q[i]-p[i]),7) for i in (0,1))
        if hit==tuple(p) or hit==tuple(q):raise ValueError('Skæringen ligger for tæt på et hjørne.')
        edges[side_p].append((tuple(p),hit));edges[side_q].append((hit,tuple(q)));hits.append(hit)
    hits=sorted(set(hits),key=tangent)
    for p,q in zip(hits,hits[1:]):
        mid=[(p[i]+q[i])/2 for i in (0,1)]
        # Rounded intersections may be a fraction outside the original edge;
        # use the exact cut coordinate for the interior interval test.
        offset=cut-project(mid);mid=[mid[0]+offset*nx,mid[1]+offset*ny]
        if not strict_inside(mid,poly):continue
        forward=(p,q)
        edges[0].append(forward);edges[1].append(tuple(reversed(forward)))
    output=[]
    for side in edges:
        following={}
        for p,q in side:
            if p==q:continue
            if p in following:raise ValueError('Tvetydig skæring.')
            following[p]=q
        while following:
            start=min(following);point=start;ring=[]
            while True:
                ring.append(list(point))
                if point not in following:raise ValueError('Grænsen kunne ikke lukkes.')
                point=following.pop(point)
                if point==start:break
                if len(ring)>5000:raise ValueError('For mange hjørner i det nye kort.')
            if len(ring)>=3 and abs(area(ring))>1e-12:output.append(valid_polygon(ring,limit=5000))
    if len(output)<2:raise ValueError('Grænsen kunne ikke deles.')
    if abs(sum(abs(area(p)) for p in output)-abs(area(poly)))>max(1e-9,abs(area(poly))*1e-5):raise ValueError('Skæringen ændrede grænsens areal.')
    return output


def allocate_groups(parts,groups):
    allocated=[[] for _ in parts]
    for g in groups:
        owners=[i for i,p in enumerate(parts) if point_in_polygon(g['point'],p)]
        if len(owners)!=1:return None
        allocated[owners[0]].append(g)
    if any(not rows for rows in allocated):return None
    # Check every unit, not only the shared house centre.
    if any(not point_in_polygon([a['lng'],a['lat']],p) for p,gs in zip(parts,allocated) for g in gs for a in g['members']):return None
    return allocated


def road_segments(roads,poly):
    """Bounded candidates from actual local segments; never extrapolate a road."""
    w,e=min(p[0] for p in poly),max(p[0] for p in poly)
    s,n=min(p[1] for p in poly),max(p[1] for p in poly)
    candidates=[]
    for road in roads:
        points=road.get('points',[])
        for a,b in zip(points,points[1:]):
            if max(a[0],b[0])<w or min(a[0],b[0])>e or max(a[1],b[1])<s or min(a[1],b[1])>n:continue
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<.00001:continue
            # Stable sign/deduplication also covers reversed source geometry.
            a,b=sorted((tuple(a),tuple(b)))
            candidates.append((a,b,road.get('name') or 'Unavngiven vej'))
    return sorted(set(candidates),key=lambda row:(-math.dist(row[0],row[1]),row))[:256]


def road_partition(ring,groups,target,segments):
    weight=sum(g['weight'] for g in groups);wanted=max(2,int(weight/target+.5));aim=weight*(wanted//2)/wanted
    candidates=[]
    for a,b,name in segments:
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);normal=(-dy/length,dx/length)
        cut=a[0]*normal[0]+a[1]*normal[1]
        side=sum(g['weight'] for g in groups if g['point'][0]*normal[0]+g['point'][1]*normal[1]<cut)
        if min(side,weight-side)<min(target*.5,weight*.2):continue
        candidates.append((min(abs(side-aim),abs(weight-side-aim)),a,b,name,normal,cut))
    for _,a,b,name,normal,cut in sorted(candidates)[:32]:
        try:parts=split_polygon_line(ring,normal,cut)
        except ValueError:continue
        # Every generated interior cutting interval must be covered by this
        # actual straight segment. A short/bending road cannot become a long line.
        tangent=lambda p:-normal[1]*p[0]+normal[0]*p[1]
        low,high=sorted((tangent(a),tangent(b)))
        hits=[p for part in parts for p in part if abs(p[0]*normal[0]+p[1]*normal[1]-cut)<1e-7]
        if not hits or any(not low-1e-7<=tangent(p)<=high+1e-7 for p in hits):continue
        allocated=allocate_groups(parts,groups)
        if allocated is not None:return parts,allocated,name
    return None


def partition(poly,addresses,target,roads=(),dividers=()):
    labels={}
    def warning_fields(messages):
        messages=list(dict.fromkeys(messages))
        return {'warning':' '.join(messages),'warning_ui':[labels.get(m,{'key':m,'params':{}}) for m in messages]}
    houses=defaultdict(list)
    for a in addresses:houses[(a['postcode'],a['road'].casefold(),a['number'].upper())].append(a)
    clusters=defaultdict(list)
    for members in houses.values():
        # Units at a shared physical point stay together even if house labels differ.
        point=(round(sum(a['lng'] for a in members)/len(members),7),round(sum(a['lat'] for a in members)/len(members),7))
        clusters[point].extend(members)
    groups=[{'point':point,'members':sorted(members,key=lambda a:a['id']),'weight':sum(a.get('count',1) for a in members)} for point,members in sorted(clusters.items())]
    from territory_paths import road_paths,network_paths,divider_paths,path_partition
    paths=road_paths(roads,poly)
    networks=network_paths(roads,poly)
    natural=divider_paths(dividers,poly)
    segments=road_segments(roads,poly)
    result=[];pending=[(poly,groups,0,())]
    while pending:
        ring,groups,depth,basis=pending.pop();weight=sum(g['weight'] for g in groups)
        wanted=max(1,int(weight/target+.5))
        if wanted<=1 or len(groups)<=1 or depth>=24:
            result.append({'polygon':ring,'members':[a for g in groups for a in g['members']],'visits':weight,**warning_fields(basis+(('Besøgstallet afviger fra ønsket; kontrollér grænsen manuelt.',) if weight>target*1.5 else ()))});continue
        boundary=path_partition(ring,groups,target,natural)
        road=boundary or path_partition(ring,groups,target,paths) or path_partition(ring,groups,target,networks) or road_partition(ring,groups,target,segments)
        if road:
            parts,allocated,name=road
            note=('Skel følger '+name+'. Kontrollér passage og lokale forhold.') if boundary else ('Skel følger vejforløbet '+name+'. Kontrollér adgang og lokale forhold.')
            if boundary:
                rail=name.startswith('Jernbane')
                key='Skel følger jernbanen{suffix}. Kontrollér passage og lokale forhold.' if rail else 'Skel følger vandløbet{suffix}. Kontrollér passage og lokale forhold.'
                labels[note]={'key':key,'params':{'suffix':name[len('Jernbane' if rail else 'Vandløb'):]}}
            else:labels[note]={'key':'Skel følger vejforløbet {name}. Kontrollér adgang og lokale forhold.','params':{'name':name}}
            pending.extend((p,gs,depth+1,basis+(note,)) for p,gs in reversed(list(zip(parts,allocated))))
            if len(result)+len(pending)>500:raise ValueError('Forslaget giver over 500 kort. Vælg flere besøg pr. kort eller færre områder ad gangen.')
            continue
        spread=[(max(g['point'][i] for g in groups)-min(g['point'][i] for g in groups))*(math.cos(math.radians(groups[0]['point'][1])) if i==0 else 1) for i in (0,1)]
        success=False
        for axis in sorted((0,1),key=lambda i:-spread[i]):
            ordered=sorted(groups,key=lambda g:(g['point'][axis],g['point'][1-axis]));running=0;candidates=[];aim=weight*(wanted//2)/wanted
            for i in range(len(ordered)-1):
                running+=ordered[i]['weight'];left=ordered[i]['point'][axis];right=ordered[i+1]['point'][axis]
                if right-left<.0000003:continue
                candidates.append((abs(running-aim),left,right))
            for _,left,right in sorted(candidates)[:10]:
                for fraction in (.5,.47,.53):
                    cut=round(left+(right-left)*fraction,7)
                    try:parts=split_polygon(ring,axis,cut)
                    except ValueError:continue
                    allocated=allocate_groups(parts,groups)
                    if allocated is None:continue
                    note='Geometrisk deling uden egnet gennemgående vejforløb. Kontrollér og ret skel manuelt.'
                    pending.extend((p,gs,depth+1,basis+(note,)) for p,gs in reversed(list(zip(parts,allocated))))
                    success=True;break
                if success:break
            if success:break
        if not success:result.append({'polygon':ring,'members':[a for g in groups for a in g['members']],'visits':weight,**warning_fields(('Området kunne ikke deles yderligere uden at dele et hus eller skabe en tom/usammenhængende grænse. Ret kortet manuelt.',))})
        if len(result)+len(pending)>500:raise ValueError('Forslaget giver over 500 kort. Vælg flere besøg pr. kort eller færre områder ad gangen.')
    return result
