"""Suggest one connected territory outline from local addresses and obstacles."""
import math
from collections import deque

from geography import enclosing_outline, point_in_polygon, valid_polygon

NEIGHBOR_GAP_M = 3
ADDRESS_GAP_M = 1
MAX_GRID_CELLS = 250_000
DIRECTIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))


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

    def outline(self, cells, forbidden):
        """Trace the outside of connected cells as a simple ring."""
        cells = set(cells)
        pending = sorted(cells)
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
                    if corners[i] in boundary:
                        return []
                    boundary[corners[i]] = corners[(i+1)%4]
        if not boundary:
            return []
        start = min(boundary)
        ring = [start]
        while (nxt := boundary.get(ring[-1])) != start:
            if nxt is None:
                return []
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


def trim_empty_fringe(ring, targets, chord_clear, validate):
    """Cut across a long jagged edge when the piece behind it has no homes."""
    accepted = validate(ring)
    if not accepted or len(ring) < 8:
        return accepted

    def totals(nodes):
        lengths, areas = [0], [0]
        for a,b in edges(nodes):
            lengths.append(lengths[-1]+math.dist(a,b))
            areas.append(areas[-1]+cross((0,0),a,b))
        return lengths, areas

    _, areas = totals(ring)
    direction = 1 if areas[-1] > 0 else -1
    # Keep most of the broad outline even when a large empty area is available.
    minimum_area = abs(areas[-1])*.55
    for _ in range(6):
        n = len(ring)
        doubled = ring+ring
        lengths, areas = totals(doubled)
        budget = areas[n]*direction-minimum_area
        stride = max(1, math.ceil(n/160))
        candidates = []
        for i in range(0,n,stride):
            for span in range(5,n-2,stride):
                j = i+span
                a,b = doubled[i], doubled[j]
                chord = math.dist(a,b)
                saved = lengths[j]-lengths[i]-chord
                if chord < 4 or saved < max(12,chord*.3):
                    continue
                removed = (areas[j]-areas[i]+cross((0,0),b,a))*direction
                if not 0 < removed <= budget:
                    continue
                candidates.append((saved, -removed, i, j))

        # Prefer the cuts that remove the most zigzag. Check the retained edge
        # for intersections, then verify the new outline with the usual rules.
        for _,_,i,j in sorted(candidates, reverse=True)[:1500]:
            a,b = doubled[i], doubled[j]
            if any(point_segment_distance(p,a,b)<3 for p in targets):
                continue
            if not chord_clear(a,b):
                continue
            box = bounds((a,b))
            retained = doubled[j+1:i+n]
            if any(near_bounds(box,bounds((c,d))) and meets((a,b),(c,d),0)
                   for c,d in zip(retained,retained[1:])):
                continue
            candidate = doubled[j:i+n+1]
            result = validate(candidate)
            if result:
                ring, accepted = candidate, result
                break
        else:
            break
    return accepted


def house_key(address):
    return (address['postcode'],address['road'].casefold(),address['number'].upper())


def adjacent(cell):
    x, y = cell
    return ((x+dx, y+dy) for dx, dy in DIRECTIONS)


def component(seed, cells):
    seen = {seed}
    queue = deque([seed])
    while queue:
        for node in adjacent(queue.popleft()):
            if node in cells and node not in seen:
                seen.add(node)
                queue.append(node)
    return seen


def carve_envelope(grid, filled, forbidden, targets, clearance):
    """Trace the filled area after opening interior exclusions to the outside.

    A single ring cannot represent holes. Find the shortest openings through
    the filled area, sharing cuts wherever their paths join. Protect the
    selected entrances and discard the candidate if a cut separates them.
    """
    available = filled - forbidden
    if not targets <= available:
        return []
    region = component(min(targets), available)
    if not targets <= region:
        return []

    exterior = {(x,y) for x in range(grid.width) for y in range(grid.height)} - region
    outside = component((0,0), exterior)
    holes = exterior - outside
    if not holes:
        return grid.outline(region, forbidden)

    protected = grid.dilate(targets, clearance)
    # Start with the inside edge of the exterior. This stores only potential
    # cuts, and lets each hole find a bent opening when a straight ray is blocked.
    roots = sorted(cell for cell in region - protected
                   if any(node in outside for node in adjacent(cell)))
    parents = dict.fromkeys(roots)
    queue = deque(roots)
    cut = set()
    while queue and holes:
        cell = queue.popleft()
        for node in adjacent(cell):
            if node in holes:
                holes.difference_update(component(node, holes))
                branch = cell
                while branch is not None and branch not in cut:
                    cut.add(branch)
                    branch = parents[branch]
            elif node in region and node not in protected and node not in parents:
                parents[node] = cell
                queue.append(node)
    if holes:
        return []
    remaining = component(min(targets), region - cut)
    if not targets <= remaining:
        return []
    # A bridge at a diagonal touch may use spare envelope cells, but must
    # never close an opening or put back an excluded address.
    return grid.outline(remaining, forbidden | cut | (region - remaining))


def simple_ring(ring):
    """Reject vertex touches and collinear overlaps as well as crossings."""
    if len(set(ring)) != len(ring):
        return False
    sides = sorted((bounds((a,b)), i, a, b) for i,(a,b) in enumerate(edges(ring)))
    active = []
    for box,i,a,b in sides:
        active = [side for side in active if side[0][2] >= box[0]]
        for other,j,c,d in active:
            if abs(i-j) in (1,len(ring)-1) or not near_bounds(box,other):
                continue
            if meets((a,b),(c,d),0):
                return False
        active.append((box,i,a,b))
    # Adjacent edges may share a vertex, but may not fold back over it.
    return all(cross(a,b,c) != 0 or
               (a[0]-b[0])*(c[0]-b[0])+(a[1]-b[1])*(c[1]-b[1]) < 0
               for a,b,c in zip(ring[-1:]+ring[:-1],ring,ring[1:]+ring[:1]))


def suggest_outline(selected, addresses, neighbors):
    """Suggest a single filled, address-safe territory from the classic hull."""
    if not selected:
        return [], 'unavailable'

    chosen = sorted({(a['lng'], a['lat']) for a in selected})
    lng, lat = chosen[0]
    scale = 111320*math.cos(math.radians(lat))

    def project(point):
        return ((point[0]-lng)*scale, (point[1]-lat)*111320)

    def unproject(point):
        return [lng+point[0]/scale, lat+point[1]/111320]

    targets = sorted(set(map(project, chosen)))
    x0, y0, x1, y1 = bounds(targets)
    margin = min(240, max(85, max(x1-x0, y1-y0)*.32))
    area = (x0-margin-.37, y0-margin-.61, x1+margin, y1+margin)
    # Allow a detour around the end of a nearby neighbor instead of crossing it.
    extent = (x0-280, y0-280, x1+280, y1+280)
    for neighbor in neighbors:
        box = bounds(neighbor)
        box = (*project(box[:2]), *project(box[2:]))
        fits = box[0]>extent[0] and box[1]>extent[1] and box[2]<extent[2] and box[3]<extent[3]
        if fits and near_bounds((x0,y0,x1,y1),box,16):
            area = (min(area[0],box[0]-12),min(area[1],box[1]-12),
                    max(area[2],box[2]+12),max(area[3],box[3]+12))

    step = max(.75, math.sqrt((area[2]-area[0])*(area[3]-area[1])/(MAX_GRID_CELLS*.85)))
    extra = step+NEIGHBOR_GAP_M+5
    world_area = bounds([unproject((area[0]-extra,area[1]-extra)),
                         unproject((area[2]+extra,area[3]+extra))])
    chosen_entrances = {(house_key(a), a['lng'], a['lat']) for a in selected}
    other = {project((a['lng'], a['lat'])) for a in addresses
             if not a.get('retired')
             and (house_key(a), a['lng'], a['lat']) not in chosen_entrances
             and near_bounds(world_area,(a['lng'],a['lat'],a['lng'],a['lat']))}
    neighbor_shapes = [list(map(project,p)) for p in neighbors
                       if near_bounds(world_area,bounds(p))]
    obstacles = [square(p, ADDRESS_GAP_M) for p in sorted(other)]
    obstacle_boxes = [(p,bounds(p)) for p in obstacles]
    neighbor_boxes = [(p,bounds(p)) for p in neighbor_shapes]

    def checked(ring, gap, avoided):
        if not ring or len(ring)<3:
            return []
        try:
            polygon = valid_polygon([unproject(p) for p in ring],limit=5000)
        except ValueError:
            return []
        projected = list(map(project,polygon))
        if not simple_ring(projected):
            return []
        box = bounds(projected)
        if any(not point_in_polygon(p,projected) or
               any(point_segment_distance(p,a,b) < .01 for a,b in edges(projected))
               for p in targets):
            return []
        if any(near_bounds(box,b) and meets(projected,p,0)
               for p,b in obstacle_boxes):
            return []
        if any(near_bounds(box,b,gap) and meets(projected,p,gap) for p,b in avoided):
            return []
        return polygon

    def smooth(ring, gap, avoided):
        def safe_shortcut(patch):
            box = bounds(patch)
            return (not any(near_bounds(box,(*p,*p)) and point_in_polygon(p,patch)
                            for p in targets)
                    and not any(near_bounds(box,b) and meets(patch,p,0)
                                for p,b in obstacle_boxes)
                    and not any(near_bounds(box,b,gap) and meets(patch,p,gap) for p,b in avoided))

        def chord_clear(a,b):
            span = (a,b)
            box = bounds(span)
            return (not any(near_bounds(box,bounds_) and meets(span,p,0)
                            for p,bounds_ in obstacle_boxes)
                    and not any(near_bounds(box,bounds_,gap) and meets(span,p,gap)
                                for p,bounds_ in avoided))

        def validate(candidate):
            return checked(candidate, gap, avoided)

        if not ring:
            return []
        for tolerance in (10, 6, 3):
            result = trim_empty_fringe(simplify_ring(ring,safe_shortcut,tolerance), targets,
                                       chord_clear, validate)
            if result:
                return result
        return trim_empty_fringe(ring, targets, chord_clear, validate)

    try:
        original = [project(p) for p in enclosing_outline(chosen, padding_m=12)]
    except ValueError:
        return [], 'unavailable'
    result = checked(original, NEIGHBOR_GAP_M, neighbor_boxes)
    if result:
        return result, 'clear'

    grid = OutlineGrid(area, step)
    if grid.width*grid.height > MAX_GRID_CELLS:
        return [], 'unavailable'
    target_cells = set(map(grid.cell, targets))
    hard = grid.raster(obstacles)
    if target_cells & hard:
        return [], 'unavailable'

    # A selected entrance in a neighboring polygon makes some overlap
    # unavoidable. A failed bounded search alone is no proof of that.
    avoided = [(p,b) for p,b in neighbor_boxes
               if not any(near_bounds(b,(*t,*t)) and point_in_polygon(t,p) for t in targets)]
    status = 'clear' if len(avoided) == len(neighbor_boxes) else 'crossing'
    borders = grid.raster([p for p,_ in avoided])
    grouped = grid.dilate(hard, 8) - grid.dilate(target_cells, 3)
    for gap in (NEIGHBOR_GAP_M, 0) if borders else (NEIGHBOR_GAP_M,):
        forbidden = hard | (grid.dilate(borders, gap) if gap else borders)
        if target_cells & forbidden:
            continue
        # Grow the filled envelope to allow a detour when clipping the first
        # hull separates two groups. Keep an exterior frame for opening holes.
        for padding in (12, 24, 48, 96, 192, None):
            if padding is None:
                filled = {(x,y) for x in range(1,grid.width-1) for y in range(1,grid.height-1)}
            else:
                try:
                    envelope = enclosing_outline(chosen, padding_m=padding)
                except ValueError:
                    continue
                filled = {cell for cell in grid.raster([list(map(project,envelope))])
                          if 0 < cell[0] < grid.width-1 and 0 < cell[1] < grid.height-1}
            # Nearby excluded dots can share a single indentation. Keep the
            # original hard exclusions if there is too little room.
            for blockers, clearance in ((forbidden | grouped,3), (forbidden,3), (forbidden,0)):
                ring = carve_envelope(grid, filled, blockers, target_cells, clearance)
                result = smooth(ring, gap, avoided)
                if result:
                    return result, status
    return [], 'unavailable'
