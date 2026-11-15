"""Suggest one connected territory outline from local addresses and obstacles."""
import math
from collections import defaultdict
from heapq import heappop, heappush

from geography import enclosing_outline, point_in_polygon, valid_polygon

NEIGHBOR_GAP_M = 3
ADDRESS_GAP_M = 1
MAX_GRID_CELLS = 250_000
DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))
DIAGONALS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def bounds(points):
    x, y = zip(*points)
    return min(x), min(y), max(x), max(y)


def edges(points):
    return zip(points, (*points[1:], points[0]))


def near_bounds(a, b, gap=0):
    return a[0]-gap <= b[2] and b[0]-gap <= a[2] and a[1]-gap <= b[3] and b[1]-gap <= a[3]


def point_segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = dx*dx+dy*dy
    t = min(1, max(0, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)) if length else 0
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def meets(polygon, obstacle, gap):
    """Includes full containment, crossing edges and clearance at corners."""
    if not near_bounds(bounds(polygon), bounds(obstacle), gap):
        return False
    if point_in_polygon(obstacle[0], polygon) or (len(obstacle)>1 and point_in_polygon(polygon[0], obstacle)):
        return True
    sides = [(a,b,bounds((a,b))) for a,b in edges(polygon)]
    for c,d in edges(obstacle):
        box = bounds((c,d))
        for a,b,side in sides:
            if not near_bounds(side,box,gap):
                continue
            if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:
                return True
            if min(point_segment_distance(a,c,d), point_segment_distance(b,c,d),
                   point_segment_distance(c,a,b), point_segment_distance(d,a,b)) <= gap+1e-6:
                return True
    return False


def square(point, radius):
    x,y = point
    return [(x-radius,y-radius),(x+radius,y-radius),(x+radius,y+radius),(x-radius,y+radius)]


class OutlineGrid:
    def __init__(self, area, step):
        self.step = step
        self.x, self.y = area[:2]
        self.width = math.ceil((area[2]-self.x)/step)
        self.height = math.ceil((area[3]-self.y)/step)

    def cell(self, point):
        return (math.floor((point[0]-self.x)/self.step), math.floor((point[1]-self.y)/self.step))

    def point(self, node):
        return (self.x+node[0]*self.step, self.y+node[1]*self.step)

    def inside(self, cell):
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def raster(self, shapes):
        """Mark cells touched by a polygon, including across an edge or in its interior."""
        cells = set()
        for shape in shapes:
            points = [((x-self.x)/self.step, (y-self.y)/self.step) for x,y in shape]
            sides = list(edges(points))
            _,ymin,_,ymax = bounds(points)
            for row in range(max(0,math.floor(ymin-1e-8)),min(self.height,math.floor(ymax+1e-8)+1)):
                hits = []
                for (x0,y0),(x1,y1) in sides:
                    if min(y0,y1)>row+1 or max(y0,y1)<row:
                        continue
                    if (y0>row+.5)!=(y1>row+.5):
                        hits.append(x0+(x1-x0)*(row+.5-y0)/(y1-y0))
                    if y0==y1:
                        low,high = sorted((x0,x1))
                    else:
                        lo,hi = max(row,min(y0,y1)),min(row+1,max(y0,y1))
                        low,high = sorted(x0+(x1-x0)*(sample-y0)/(y1-y0) for sample in (lo,hi))
                    cells.update((col,row) for col in self.columns(low,high))
                hits.sort()
                for low,high in zip(hits[::2],hits[1::2]):
                    cells.update((col,row) for col in self.columns(low,high))
        return cells

    def columns(self, low, high):
        return range(max(0,math.floor(low-1e-8)),min(self.width,math.floor(high+1e-8)+1))

    def dilate(self, cells, distance):
        # Horizontal and vertical passes are enough for a conservative square buffer.
        radius = math.ceil(distance/self.step)
        expanded = {(x+dx,y) for x,y in cells for dx in range(-radius,radius+1) if 0<=x+dx<self.width}
        return {(x,y+dy) for x,y in expanded for dy in range(-radius,radius+1) if 0<=y+dy<self.height}

    def expand(self, cells, forbidden, distance):
        expanded = set(cells)
        frontier = cells
        for _ in range(math.ceil(distance/self.step)):
            frontier = {(x+dx,y+dy) for x,y in frontier for dx,dy in DIRECTIONS
                        if self.inside((x+dx,y+dy))} - forbidden - expanded
            expanded.update(frontier)
        return expanded

    def road_cells(self, segments):
        strips = []
        for a,b in segments:
            dx,dy = b[0]-a[0],b[1]-a[1]
            length = math.hypot(dx,dy)
            if length:
                nx,ny = -.05*dy/length,.05*dx/length
                strips.append([(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),
                               (b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)])
        return self.dilate(self.raster(strips),5)

    def connect(self, targets, blocked, penalized=frozenset(), roads=frozenset()):
        """Find short connections to the existing outline, favoring nearby named roads."""
        cells = {targets[0]}
        left,bottom,right,top = (*targets[0],*targets[0])
        budget = 3*MAX_GRID_CELLS
        cost_crossing = 21*self.width*self.height+1
        # Keep the existing narrow orthogonal crossing when overlap is necessary.
        directions = DIRECTIONS if penalized else DIRECTIONS+DIAGONALS
        for target in targets[1:]:
            if target in cells:
                continue

            def distance(cell):
                dx = max(left-cell[0],0,cell[0]-right)
                dy = max(bottom-cell[1],0,cell[1]-top)
                return 10*max(dx,dy)+4*min(dx,dy)

            h = distance(target)
            queue = [(h,h,target)]
            parents = {target:None}
            costs = {target:0}
            while queue:
                score,h,current = heappop(queue)
                if score-h != costs[current]:
                    continue
                budget -= 1
                if budget < 0:
                    raise OverflowError()
                x,y = current
                if current in cells:
                    while current is not None:
                        x,y = current
                        cells.add(current)
                        left,bottom,right,top = min(left,x),min(bottom,y),max(right,x),max(top,y)
                        current = parents[current]
                    break
                for dx,dy in directions:
                    nxt = (x+dx,y+dy)
                    if not self.inside(nxt) or nxt in blocked:
                        continue
                    diagonal = dx!=0 and dy!=0
                    if diagonal and ((x+dx,y) in blocked or (x,y+dy) in blocked):
                        continue
                    step_cost = 14 if diagonal else 10
                    if roads and nxt not in roads:
                        step_cost += step_cost//2
                    if nxt in penalized:
                        step_cost += cost_crossing
                    cost = costs[current]+step_cost
                    if nxt in costs and cost >= costs[nxt]:
                        continue
                    costs[nxt],parents[nxt] = cost,current
                    h = distance(nxt)
                    heappush(queue,(cost+h,h,nxt))
            else:
                return None
        return cells

    def outline(self, cells, forbidden):
        """Trace the outside of connected cells as a simple ring."""
        pending = list(cells)
        while pending:
            x,y = pending.pop()
            for dx,dy in ((1,1),(1,-1),(-1,1),(-1,-1)):
                if (x+dx,y+dy) not in cells or (x+dx,y) in cells or (x,y+dy) in cells:
                    continue
                bridge = next((p for p in ((x+dx,y),(x,y+dy)) if p not in forbidden),None)
                if bridge is None:
                    return []
                cells.add(bridge)
                pending.append(bridge)
        boundary = {}
        for x,y in cells:
            corners = ((x,y),(x+1,y),(x+1,y+1),(x,y+1))
            for i,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))):
                if (x+dx,y+dy) not in cells:
                    boundary[corners[i]] = corners[(i+1)%4]
        start = min(boundary)
        ring = [start]
        while (nxt := boundary[ring[-1]]) != start:
            ring.append(nxt)
            if len(ring)>len(boundary):
                return []
        if len(ring)!=len(boundary):
            # The storage format has one ring. Filling a hole could cover an obstacle.
            return []
        return [self.point(c) for i,c in enumerate(ring) if cross(ring[i-1],c,ring[(i+1)%len(ring)])]


def simplify_ring(ring, can_shortcut, tolerance):
    """Replace stretches of grid steps with safe straight segments."""
    if len(ring) < 4:
        return ring
    anchor = ring[0]
    opposite = max(range(1,len(ring)),key=lambda i: math.dist(anchor,ring[i]))
    closed = ring+[anchor]
    kept = {0,opposite}
    pending = [(0,opposite),(opposite,len(ring))]
    while pending:
        start,end = pending.pop()
        if end-start < 2:
            continue
        a,b = closed[start],closed[end]
        deviation,split = max((point_segment_distance(closed[i],a,b),i) for i in range(start+1,end))
        if deviation <= tolerance and can_shortcut(closed[start:end+1]):
            continue
        kept.add(split)
        pending.extend(((start,split),(split,end)))
    return [ring[i] for i in sorted(kept)]


def house_key(address):
    return (address['postcode'],address['road'].casefold(),address['number'].upper())


def unselected_buildings(shapes, selected, excluded):
    """Associate each known entrance with its closest saved footprint."""
    tile_size = 25
    points = set(selected)|set(excluded)
    excluded = set(excluded)
    tiles = defaultdict(list)
    for p in points:
        tiles[(math.floor(p[0]/tile_size),math.floor(p[1]/tile_size))].append(p)
    tx0,ty0,tx1,ty1 = bounds(tiles)
    nearest = {}
    blocked = set()
    reach = 5
    for i,shape in enumerate(shapes):
        x0,y0,x1,y1 = bounds(shape)
        x_tiles = range(max(tx0,math.floor((x0-reach)/tile_size)),min(tx1,math.floor((x1+reach)/tile_size))+1)
        y_tiles = range(max(ty0,math.floor((y0-reach)/tile_size)),min(ty1,math.floor((y1+reach)/tile_size))+1)
        if len(x_tiles)*len(y_tiles) <= len(tiles):
            nearby = (tiles.get((x,y),()) for x in x_tiles for y in y_tiles)
        else:
            nearby = (bucket for (x,y),bucket in tiles.items() if x in x_tiles and y in y_tiles)
        for bucket in nearby:
            for p in bucket:
                if not (x0-reach<=p[0]<=x1+reach and y0-reach<=p[1]<=y1+reach):
                    continue
                inside = point_in_polygon(p,shape)
                if inside and p in excluded:
                    blocked.add(i)
                distance = 0 if inside else min(point_segment_distance(p,a,b) for a,b in edges(shape))
                if distance>reach:
                    continue
                old = nearest.get(p)
                if old is None or distance<old[0]-1e-6:
                    nearest[p] = (distance,{i})
                elif abs(distance-old[0])<=1e-6:
                    old[1].add(i)
    for p in excluded:
        if p in nearest:
            blocked.update(nearest[p][1])
    # A tied entrance is ambiguous. Only allow a footprint associated unambiguously.
    allowed = {next(iter(nearest[p][1])) for p in selected if p in nearest and len(nearest[p][1])==1}-blocked
    return [shape for i,shape in enumerate(shapes) if i not in allowed]


def suggest_outline(selected, addresses, buildings, neighbors, roads=()):
    """Use stricter obstacles first, then try a narrow crossing if they divide the search area."""
    if not selected:
        return [],'unavailable'
    chosen = sorted({(a['lng'],a['lat']) for a in selected})
    lng,lat = chosen[0]
    scale = 111320*math.cos(math.radians(lat))

    def project(point):
        return ((point[0]-lng)*scale,(point[1]-lat)*111320)

    def unproject(point):
        return [lng+point[0]/scale,lat+point[1]/111320]

    targets = sorted(set(map(project,chosen)))
    x0,y0,x1,y1 = bounds(targets)
    margin = min(180,max(60,max(x1-x0,y1-y0)*.30))
    area = (x0-margin-.37,y0-margin-.61,x1+margin,y1+margin)
    # Include the ends of nearby borders when they fit in the local search,
    # so a detour around an ordinary adjacent area wins over a crossing.
    extent = (x0-240,y0-240,x1+240,y1+240)
    for neighbor in neighbors:
        box = bounds(neighbor)
        corner0,corner1 = box[:2],box[2:]
        box = (*project(corner0),*project(corner1))
        fits = box[0]>extent[0] and box[1]>extent[1] and box[2]<extent[2] and box[3]<extent[3]
        if fits and near_bounds((x0,y0,x1,y1),box,12):
            area = (min(area[0],box[0]-10),min(area[1],box[1]-10),max(area[2],box[2]+10),max(area[3],box[3]+10))
    step = max(.75,math.sqrt((area[2]-area[0])*(area[3]-area[1])/(MAX_GRID_CELLS*.85)))
    # The last grid cells can extend past the requested area. Include the data
    # beside them too, so rounding the grid cannot hide nearby obstacles.
    extra = step+NEIGHBOR_GAP_M+5
    world_area = bounds([unproject((area[0]-extra,area[1]-extra)),
                         unproject((area[2]+extra,area[3]+extra))])
    houses = {house_key(a) for a in selected}
    other = [project((a['lng'],a['lat'])) for a in addresses
             if not a.get('retired') and house_key(a) not in houses
             and near_bounds(world_area,(a['lng'],a['lat'],a['lng'],a['lat']))]
    neighbor_shapes = [list(map(project,p)) for p in neighbors if near_bounds(world_area,bounds(p))]
    obstacles = [square(p,ADDRESS_GAP_M) for p in other]
    footprints = [list(map(project,building)) for building in buildings if near_bounds(world_area,bounds(building))]
    obstacles.extend(unselected_buildings(footprints,targets,other))
    obstacle_boxes = [(p,bounds(p)) for p in obstacles]

    def checked(ring, gap):
        try:
            polygon = valid_polygon([unproject(p) for p in ring],limit=5000)
        except ValueError:
            return []
        ring = list(map(project,polygon))
        box = bounds(ring)
        if any(not point_in_polygon(p,ring) for p in targets) or any(near_bounds(box,b) and meets(ring,p,0) for p,b in obstacle_boxes):
            return []
        if gap is not None and any(meets(ring,p,gap) for p in neighbor_shapes):
            return []
        return polygon

    neighbor_boxes = [(p,bounds(p)) for p in neighbor_shapes]

    def can_shortcut(patch):
        # The chord changes only this patch. Keep the original bends wherever
        # the change would affect a selected house or enter reserved space.
        box = bounds(patch)
        return (not any(near_bounds(box,(*p,*p)) and point_in_polygon(p,patch) for p in targets)
                and not any(near_bounds(box,b) and meets(patch,p,0) for p,b in obstacle_boxes)
                and not any(near_bounds(box,b,NEIGHBOR_GAP_M) and meets(patch,p,NEIGHBOR_GAP_M)
                            for p,b in neighbor_boxes))

    def smooth(ring, gap):
        for tolerance in (8,3):
            reduced = simplify_ring(ring,can_shortcut,tolerance)
            if len(reduced) < len(ring):
                polygon = checked(reduced,gap)
                if polygon:
                    return polygon
        return checked(ring,gap)

    try:
        hull = enclosing_outline([list(p) for p in chosen])
    except ValueError:
        hull = []
    if hull:
        clear = checked([project(p) for p in hull],NEIGHBOR_GAP_M)
        if clear:
            return clear,'clear'

    grid = OutlineGrid(area,step)
    if grid.width*grid.height > MAX_GRID_CELLS:
        return [],'unavailable'
    road_names = {a['road'].strip().casefold() for a in selected}
    segments = [(project(a),project(b)) for road in roads
                if road.get('name','').strip().casefold() in road_names
                for a,b in zip(road['points'],road['points'][1:])
                if near_bounds(world_area,bounds((a,b)))]
    road_cells = grid.road_cells(segments)
    cells = list(dict.fromkeys(map(grid.cell,targets)))
    hard = grid.raster(obstacles)
    raw_borders = grid.raster(neighbor_shapes)
    buffered = grid.dilate(raw_borders,NEIGHBOR_GAP_M)
    strict = hard|buffered
    if any(cell in strict for cell in cells):
        # A selected house next to a border must not trigger an overlap exception.
        return [],'unavailable'
    try:
        route = grid.connect(cells,strict,roads=road_cells)
        if route is not None:
            # A wider ring may enclose an obstacle even though the route
            # itself passes it safely. Retry with less space beside the route.
            for padding in (5,2,0):
                area_cells = grid.expand(route,strict,padding)
                polygon = smooth(grid.outline(area_cells,strict),NEIGHBOR_GAP_M)
                if polygon:
                    return polygon,'clear'
            return [],'unavailable'
        if step > 2.5 or not raw_borders or grid.connect(cells,hard|raw_borders) is not None:
            return [],'unavailable'
        route = grid.connect(cells,hard,buffered,roads=road_cells)
        if route is not None:
            # Keep the crossing one cell wide and expand only into clear space.
            for padding in (5,2,0):
                area_cells = grid.expand(route,strict,padding)
                polygon = smooth(grid.outline(area_cells,hard|(buffered-route)),None)
                if polygon:
                    ring = list(map(project,polygon))
                    if any(meets(ring,p,0) for p in neighbor_shapes):
                        return polygon,'crossing'
    except OverflowError:
        pass
    return [],'unavailable'
