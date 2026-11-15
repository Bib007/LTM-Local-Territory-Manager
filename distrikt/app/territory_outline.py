"""Suggest one connected territory outline from local addresses and obstacles."""
import math
from collections import deque
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


def carve_original_envelope(grid, filled, forbidden, target_cells):
    """Keep the old convex outline and open small *local* cuts for excluded dots.

    The previous fallbacks discarded a broad envelope as soon as it contained
    any non-selected address. They then grew a strip along the shortest route
    between houses, causing narrow, unnatural territories. Here we keep the
    original filled outline and connect every forbidden interior island to the
    outside with a small notch. We never remove a selected address or allow a
    forbidden cell back in. If a valid single polygon is impossible, the caller
    can use its explicitly constrained fallback instead.
    """
    region = filled - forbidden
    targets = set(target_cells)
    if not targets <= region:
        return []

    # Discover the outside of the old polygon; only enclosed forbidden islands
    # need a cut. A hole cannot be stored in the current single-ring format.
    outside = set()
    queue = deque()
    for x in range(grid.width):
        for node in ((x, 0), (x, grid.height-1)):
            if node not in region and node not in outside:
                outside.add(node)
                queue.append(node)
    for y in range(grid.height):
        for node in ((0, y), (grid.width-1, y)):
            if node not in region and node not in outside:
                outside.add(node)
                queue.append(node)
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRECTIONS:
            node = (x+dx, y+dy)
            if grid.inside(node) and node not in region and node not in outside:
                outside.add(node)
                queue.append(node)

    holes = {(x,y) for y in range(grid.height) for x in range(grid.width)
             if (x,y) not in region and (x,y) not in outside}
    if not holes:
        return grid.outline(region, forbidden)

    # A few metres of clearance around chosen entrances stop a notch splitting
    # a selected household from the polygon.
    protected = grid.dilate(targets, 3)
    components = 0
    while holes:
        components += 1
        if components > 300:
            return []
        seed = holes.pop()
        island = {seed}
        pending = [seed]
        while pending:
            x, y = pending.pop()
            for dx,dy in DIRECTIONS:
                node = (x+dx,y+dy)
                if node in holes:
                    holes.remove(node)
                    island.add(node)
                    pending.append(node)

        # Test straight outward cuts on all four sides of the island. This
        # produces a handful of meaningful corners rather than an A* corridor.
        extremes = (
            (sorted(island,key=lambda p:(p[0],p[1]))[:8],(-1,0)),
            (sorted(island,key=lambda p:(-p[0],p[1]))[:8],(1,0)),
            (sorted(island,key=lambda p:(p[1],p[0]))[:8],(0,-1)),
            (sorted(island,key=lambda p:(-p[1],p[0]))[:8],(0,1)),
        )
        choices = []
        for starts,direction in extremes:
            dx,dy = direction
            for start in starts:
                x,y = start
                path = []
                # At most one continuous straight opening to the exterior.
                while grid.inside((x,y)) and (x,y) not in outside:
                    node = (x,y)
                    if node in region:
                        path.append(node)
                    x,y = x+dx,y+dy
                if not grid.inside((x,y)) or len(path)>160 or not path:
                    continue
                if any(cell in protected for cell in path):
                    continue
                choices.append((len(path),len(path),start,direction,path))

        if not choices:
            return []
        choices.sort(key=lambda entry:entry[:4])
        chosen = choices[0][4]
        # A one-cell notch can touch itself diagonally; use a second cell
        # where safe so the resulting perimeter is an ordinary simple ring.
        dx,dy = choices[0][3]
        cut = set(chosen)
        for x,y in chosen:
            for neighbor in ((x+dy,y+dx),):
                if neighbor in region and neighbor not in protected:
                    cut.add(neighbor)
        region.difference_update(cut)
        outside.update(island)
        outside.update(cut)

    # Delete disconnected slack areas, but never a selected home. Otherwise
    # the contour could silently omit a part of the actual territory.
    if not region or targets - region:
        return []
    seen = {next(iter(targets))}
    queue = deque(seen)
    while queue:
        x,y = queue.popleft()
        for dx,dy in DIRECTIONS:
            node = (x+dx,y+dy)
            if node in region and node not in seen:
                seen.add(node)
                queue.append(node)
    if not targets <= seen:
        return []
    return grid.outline(seen, forbidden)


def suggest_outline(selected, addresses, buildings, neighbors, roads=()):
    """Draw a generous territory around the selected homes, not a thin route.

    1. Prefer a broad, clean silhouette with few corners, like a hand-drawn map.
    2. If that would include an unselected home or another territory, grow a
       connected outline around safe paths and simplify its perimeter.
    3. Buildings with no known unselected address and ordinary map background
       are *not* barriers. An unavoidable neighboring-territory crossing is
       explicitly flagged, never silently treated as clear.

    A proposal is display-only until the caller rechecks it at save time.
    """
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
    chosen_houses = {house_key(a) for a in selected}
    other = [project((a['lng'],a['lat'])) for a in addresses
             if not a.get('retired') and house_key(a) not in chosen_houses
             and near_bounds(world_area,(a['lng'],a['lat'],a['lng'],a['lat']))]
    neighbor_shapes = [list(map(project,p)) for p in neighbors
                       if near_bounds(world_area,bounds(p))]
    # A building footprint is not an address assignment. The user selected
    # individual DAR entrances; only other loaded address *points* and already
    # assigned territory polygons are protected. Sheds and unselected buildings
    # are neutral cartography and may lie inside a proposed outline.
    obstacles = [square(p,ADDRESS_GAP_M) for p in other]
    obstacle_boxes = [(p,bounds(p)) for p in obstacles]
    neighbor_boxes = [(p,bounds(p)) for p in neighbor_shapes]

    def checked(ring, gap):
        if not ring or len(ring)<3:
            return []
        try:
            polygon = valid_polygon([unproject(p) for p in ring],limit=5000)
        except ValueError:
            return []
        projected = list(map(project,polygon))
        box = bounds(projected)
        if any(not point_in_polygon(p,projected) for p in targets):
            return []
        if any(near_bounds(box,b) and meets(projected,p,0)
               for p,b in obstacle_boxes):
            return []
        if gap is not None and any(near_bounds(box,b,gap) and meets(projected,p,gap)
                                   for p,b in neighbor_boxes):
            return []
        return polygon

    def safe_shortcut(patch):
        """Only replace a contour bend if its triangular sweep is empty."""
        box = bounds(patch)
        return (not any(near_bounds(box,(*p,*p)) and point_in_polygon(p,patch)
                        for p in targets)
                and not any(near_bounds(box,b) and meets(patch,p,0)
                            for p,b in obstacle_boxes)
                and not any(near_bounds(box,b,NEIGHBOR_GAP_M) and
                            meets(patch,p,NEIGHBOR_GAP_M)
                            for p,b in neighbor_boxes))

    def smooth(ring, gap):
        if not ring:
            return []
        for tolerance in (16,8,3):
            simplified = simplify_ring(ring,safe_shortcut,tolerance)
            if len(simplified)<len(ring):
                result = checked(simplified,gap)
                if result:
                    return result
        return checked(ring,gap)

    # Return to the original broad convex envelope. A collision must be
    # trimmed *locally* instead of rejecting the entire envelope and falling
    # back to the thinnest possible connection between houses.
    old_envelopes = []
    for padding in (12,24):
        try:
            envelope = enclosing_outline([list(p) for p in chosen],padding_m=padding)
        except ValueError:
            continue
        projected_envelope = [project(p) for p in envelope]
        old_envelopes.append(projected_envelope)
        result = checked(projected_envelope,NEIGHBOR_GAP_M)
        if result:
            return result,'clear'

    # Only if there is no valid carved envelope should an address-safe route
    # be considered. That case is a genuine geometric constraint, not a reason
    # to squeeze every ordinary block into a ribbon.
    grid = OutlineGrid(area,step)
    if grid.width*grid.height > MAX_GRID_CELLS:
        return [],'unavailable'
    names = {a['road'].strip().casefold() for a in selected}
    segments = [(project(a),project(b)) for road in roads
                if road.get('name','').strip().casefold() in names
                for a,b in zip(road['points'],road['points'][1:])
                if near_bounds(world_area,bounds((a,b)))]
    road_cells = grid.road_cells(segments)
    targets_cells = list(dict.fromkeys(map(grid.cell,targets)))
    hard = grid.raster(obstacles)
    borders = grid.raster(neighbor_shapes)
    neighbor_buffer = grid.dilate(borders,NEIGHBOR_GAP_M)
    forbidden = hard | neighbor_buffer
    if any(cell in forbidden for cell in targets_cells):
        return [],'unavailable'

    for envelope in old_envelopes:
        broad = grid.raster([envelope])
        shaped = carve_original_envelope(grid,broad,forbidden,targets_cells)
        result = smooth(shaped,NEIGHBOR_GAP_M) if shaped else []
        if result:
            return result,'clear'

    try:
        route = grid.connect(targets_cells,forbidden,roads=road_cells)
        if route is not None:
            for padding in (36,26,18,12,8,4,0):
                grown = grid.expand(route,forbidden,padding)
                result = smooth(grid.outline(grown,forbidden),NEIGHBOR_GAP_M)
                if result:
                    return result,'clear'
            return [],'unavailable'

        # The user still gets a visible warning when an existing neighboring
        # polygon truly cuts their selected addresses into separate pieces.
        # Never hide a crossing behind a "clear" label.
        if step>2.5 or not borders or grid.connect(targets_cells,hard|borders) is not None:
            return [],'unavailable'
        route = grid.connect(targets_cells,hard,neighbor_buffer,roads=road_cells)
        if route is not None:
            for padding in (18,10,5,0):
                grown = grid.expand(route,forbidden,padding)
                result = smooth(grid.outline(grown,hard|(neighbor_buffer-route)),None)
                if result:
                    ring = list(map(project,result))
                    if any(meets(ring,p,0) for p in neighbor_shapes):
                        return result,'crossing'
    except OverflowError:
        pass
    return [],'unavailable'
