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
    """Cut along an axis; keep disconnected components as separate polygons.
    Build original clipped edges plus oriented intervals on the cutting line.
    Cut positions must avoid vertices. Ambiguous/degenerate cuts are rejected.
    """
    if any(abs(p[axis]-cut)<.000000049 for p in poly):raise ValueError('Skærelinjen rammer et hjørne.')
    if area(poly)<0:poly=list(reversed(poly))
    edges=[[],[]];hits=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        side_p=int(p[axis]>cut);side_q=int(q[axis]>cut)
        if side_p==side_q:edges[side_p].append((tuple(p),tuple(q)));continue
        fraction=(cut-p[axis])/(q[axis]-p[axis]);hit=tuple(round(p[i]+fraction*(q[i]-p[i]),7) for i in (0,1))
        if hit==tuple(p) or hit==tuple(q):raise ValueError('Skæringen ligger for tæt på et hjørne.')
        edges[side_p].append((tuple(p),hit));edges[side_q].append((hit,tuple(q)));hits.append(hit)
    hits=sorted(set(hits),key=lambda p:p[1-axis])
    for p,q in zip(hits,hits[1:]):
        mid=[(p[i]+q[i])/2 for i in (0,1)]
        # Rounded intersections may be a fraction outside the original edge;
        # use the exact cut coordinate for the interior interval test.
        mid[axis]=cut
        if not strict_inside(mid,poly):continue
        forward=(p,q) if axis==0 else (q,p)
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


def partition(poly,addresses,target):
    houses=defaultdict(list)
    for a in addresses:houses[(a['postcode'],a['road'].casefold(),a['number'].upper())].append(a)
    clusters=defaultdict(list)
    for members in houses.values():
        # Units at a shared physical point stay together even if house labels differ.
        point=(round(sum(a['lng'] for a in members)/len(members),7),round(sum(a['lat'] for a in members)/len(members),7))
        clusters[point].extend(members)
    groups=[{'point':point,'members':sorted(members,key=lambda a:a['id']),'weight':sum(a.get('count',1) for a in members)} for point,members in sorted(clusters.items())]
    result=[];pending=[(poly,groups,0)]
    while pending:
        ring,groups,depth=pending.pop();weight=sum(g['weight'] for g in groups)
        wanted=max(1,int(weight/target+.5))
        if wanted<=1 or len(groups)<=1 or depth>=24:
            result.append({'polygon':ring,'members':[a for g in groups for a in g['members']],'visits':weight,'warning':'Besøgstallet afviger fra ønsket; kontrollér grænsen manuelt.' if weight>target*1.5 else ''});continue
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
                    allocated=[[] for _ in parts];okay=True
                    for g in groups:
                        owners=[i for i,p in enumerate(parts) if point_in_polygon(g['point'],p)]
                        if len(owners)!=1:okay=False;break
                        allocated[owners[0]].append(g)
                    if not okay or any(not rows for rows in allocated):continue
                    # Address coordinates, not only the house centre, must stay inside.
                    if any(not point_in_polygon([a['lng'],a['lat']],p) for p,gs in zip(parts,allocated) for g in gs for a in g['members']):continue
                    pending.extend((p,gs,depth+1) for p,gs in reversed(list(zip(parts,allocated))))
                    success=True;break
                if success:break
            if success:break
        if not success:result.append({'polygon':ring,'members':[a for g in groups for a in g['members']],'visits':weight,'warning':'Området kunne ikke deles yderligere uden at dele et hus eller skabe en tom/usammenhængende grænse. Ret kortet manuelt.'})
        if len(result)+len(pending)>500:raise ValueError('Forslaget giver over 500 kort. Vælg flere besøg pr. kort eller færre områder ad gangen.')
    return result
