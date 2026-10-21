"""Conservative local road chains and polygon cuts along their actual vertices.

Only an unbranched path crossing the boundary twice is accepted. No snapping,
straightening, gap filling or road extrapolation; ambiguous geometry is skipped.
"""
import math
from collections import Counter, defaultdict
from geography import valid_coordinate, valid_polygon
from territory_partition import area, allocate_groups, contained, overlaps, strict_inside

MAX_POINTS = 512
MAX_PATHS = 256
MAX_ATTEMPTS = 32
MAX_EDGE_PAIRS = 200000
MAX_OWNERSHIP_WORK = 2000000
MAX_NETWORK_EDGES = 4096
MAX_NETWORK_WORK = 16384
MAX_NETWORK_PATHS = 128
MAX_NETWORK_POINT_WORK = 200000


def _box(points):
    return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)


def _boxes_overlap(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _canonical(points):
    points = tuple(map(tuple, points))
    return min(points, tuple(reversed(points)))


def _intersection(a, b, c, d):
    """Segment intersection; touching/overlapping collinear edges are ambiguous."""
    if not _boxes_overlap(_box((a, b)), _box((c, d))):
        return None
    dx, dy = b[0] - a[0], b[1] - a[1]
    ex, ey = d[0] - c[0], d[1] - c[1]
    denominator = dx * ey - dy * ex
    cx, cy = c[0] - a[0], c[1] - a[1]
    if abs(denominator) < 1e-16:
        if abs(cx * dy - cy * dx) < 1e-14:
            raise ValueError('Vejforløbet berører eller følger en anden kant.')
        return None
    t = (cx * ey - cy * ex) / denominator
    u = (cx * dy - cy * dx) / denominator
    if not (-1e-10 <= t <= 1 + 1e-10 and -1e-10 <= u <= 1 + 1e-10):
        return None
    t, u = max(0, min(1, t)), max(0, min(1, u))
    return t, u, (round(a[0] + t * dx, 7), round(a[1] + t * dy, 7))


def split_polygon_path(poly, points):
    """Split along one simple inside interval of the supplied finite polyline."""
    if not 2 <= len(points) <= MAX_POINTS or len(poly) * (len(points) - 1) > MAX_EDGE_PAIRS:
        raise ValueError('Vejforløbet er for stort til automatisk skæring.')
    points = _canonical([valid_coordinate(p) for p in points])
    if len(set(points)) != len(points):
        raise ValueError('Vejforløbet gentager et punkt eller danner en løkke.')
    # valid_polygon checks proper crossings; here non-adjacent touching and
    # overlapping segments must also be rejected before constructing any rings.
    for i, (a, b) in enumerate(zip(points, points[1:])):
        for c, d in zip(points[i + 2:], points[i + 3:]):
            if _intersection(a, b, c, d) is not None:
                raise ValueError('Vejforløbet krydser eller berører sig selv.')
    for a, b, c in zip(points, points[1:], points[2:]):
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        backtrack = (a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1])
        if abs(cross) < 1e-14 and backtrack > 0:
            raise ValueError('Vejforløbet vender tilbage langs samme strækning.')
    hits = []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        for j, c in enumerate(poly):
            d = poly[(j + 1) % len(poly)]
            hit = _intersection(a, b, c, d)
            if hit is None:
                continue
            t, u, point = hit
            if min(math.dist(point, c), math.dist(point, d)) < 1e-7:
                raise ValueError('Vejforløbet rammer et grænsehjørne.')
            # Endpoints may lie exactly on the boundary. An interior road vertex
            # on it can be a touch rather than a crossing, so do not guess.
            if (t < 1e-10 and i > 0) or (t > 1 - 1e-10 and i < len(points) - 2):
                raise ValueError('Et vejknæk ligger på grænsen.')
            hits.append((i + t, j, u, point))
    hits.sort()
    if len(hits) != 2 or hits[0][3] == hits[1][3]:
        raise ValueError('Vejforløbet skal krydse grænsen præcis to steder.')
    first, last = hits
    inside = [first[3]] + [p for i, p in enumerate(points) if first[0] < i < last[0]] + [last[3]]
    if any(not strict_inside(p, poly) for p in inside[1:-1]):
        raise ValueError('Vejforløbet forlader området.')
    for a, b in zip(inside, inside[1:]):
        if not strict_inside([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], poly):
            raise ValueError('Vejforløbet går ikke gennem områdets indre.')
    boundary = []
    for j, p in enumerate(poly):
        boundary.append(tuple(p))
        boundary.extend(h[3] for h in sorted(hits, key=lambda h: h[2]) if h[1] == j)
    start, end = boundary.index(first[3]), boundary.index(last[3])
    def arc(a, b):
        return boundary[a:b + 1] if a < b else boundary[a:] + boundary[:b + 1]
    rings = [arc(start, end) + list(reversed(inside))[1:-1], arc(end, start) + inside[1:-1]]
    parts = []
    for ring in rings:
        if len(set(ring)) != len(ring):
            raise ValueError('Et grænsehjørne gentages efter skæringen.')
        parts.append(valid_polygon([list(p) for p in ring], limit=5000))
    original = abs(area(poly))
    if abs(sum(abs(area(p)) for p in parts) - original) > max(2e-10, original * 1e-6):
        raise ValueError('Vejskæringen ændrede områdets areal.')
    if not all(contained(p, poly) for p in parts) or overlaps(*parts):
        raise ValueError('Vejskæringen efterlod en ugyldig grænse.')
    return parts


def road_paths(roads, poly, *, unnamed='Unavngiven vej'):
    """Join same-name records only at exact, unbranched shared endpoints."""
    bounds = _box(poly)
    by_name = defaultdict(dict)
    for road in roads:
        raw = road.get('points', [])
        if not 2 <= len(raw) <= MAX_POINTS or not _boxes_overlap(_box(raw), bounds):
            continue
        points = _canonical(raw)
        if len(set(points)) != len(points):
            continue
        name = str(road.get('name') or '').strip()
        # Unnamed lines remain individual candidates, never a guessed network.
        key = name.casefold() if name else ('unnamed', points)
        old = by_name[key].get(points)
        by_name[key][points] = min(old, name) if old is not None else name
    result = []
    for source in by_name.values():
        records = sorted(source)
        endpoints = defaultdict(list)
        degree = Counter()
        for i, points in enumerate(records):
            endpoints[points[0]].append(i)
            endpoints[points[-1]].append(i)
            for a, b in zip(points, points[1:]):
                degree[a] += 1
                degree[b] += 1
        seen = set()
        for i, original in enumerate(records):
            if i in seen:
                continue
            seen.add(i)
            points = list(original)
            names = [source[original]]
            for reverse in (False, True):
                if reverse:
                    points.reverse()
                while degree[points[-1]] == 2 and len(endpoints[points[-1]]) == 2:
                    following = [j for j in endpoints[points[-1]] if j not in seen]
                    if len(following) != 1:
                        break
                    j = following[0]
                    tail = records[j]
                    if tail[-1] == points[-1]:
                        tail = tuple(reversed(tail))
                    if len(points) + len(tail) - 1 > MAX_POINTS:
                        break
                    points.extend(tail[1:])
                    seen.add(j)
                    names.append(source[records[j]])
            if len(set(points)) == len(points):
                result.append((_canonical(points), min(names) or unnamed))
    return sorted(result, key=lambda row: (-sum(math.dist(a, b) for a, b in zip(row[0], row[0][1:])), row))[:MAX_PATHS]


def network_paths(roads, poly):
    """Bounded extra candidates through simple, same-name branching networks.

    Connect only identical recorded vertices. Never snap, infer an intersection,
    cross a name change, extend a dead end or choose a route around a cycle.
    Existing unbranched candidates are kept separately and tried first.
    """
    bounds = _box(poly)
    records = set()
    for road in roads:
        name = str(road.get('name') or '').strip()
        raw = road.get('points', [])
        if not name or not 2 <= len(raw) <= MAX_POINTS or not _boxes_overlap(_box(raw), bounds):
            continue
        points = _canonical(raw)
        if len(set(points)) == len(points):
            records.add((name.casefold(), points, name))
    graphs = defaultdict(lambda: defaultdict(set))
    names = {}
    edges = 0
    for key, points, name in sorted(records):
        names[key] = min(names.get(key, name), name)
        for a, b in zip(points, points[1:]):
            if a == b or b in graphs[key][a]:
                continue
            if edges >= MAX_NETWORK_EDGES:
                # Never mistake a truncated cycle or junction for a complete
                # tree. Keep the existing conservative fallback for this input.
                return []
            graphs[key][a].add(b)
            graphs[key][b].add(a)
            edges += 1
    result = set()
    work = 0
    point_work = 0
    for key, graph in sorted(graphs.items()):
        seen = set()
        for root in sorted(graph):
            if root in seen:
                continue
            component = set()
            pending = [root]
            while pending:
                node = pending.pop()
                if node in component:
                    continue
                component.add(node)
                pending.extend(graph[node] - component)
            seen.update(component)
            # A tree has one actual route between vertices. Cyclic or highly
            # branched networks need manual review rather than guessed routing.
            if (not any(len(graph[n]) > 2 for n in component)
                    or any(len(graph[n]) > 8 for n in component)
                    or sum(len(graph[n]) for n in component) != 2 * (len(component) - 1)):
                continue
            needed = len(component) * len(poly)
            if point_work + needed > MAX_NETWORK_POINT_WORK:
                continue
            point_work += needed
            inside = {n: strict_inside(n, poly) for n in component}
            starts = sorted((a, b) for a in component if not inside[a] for b in graph[a] if inside[b])
            for a, b in starts:
                pending = [(a, b)]
                while pending:
                    points = pending.pop()
                    work += 1
                    if work > MAX_NETWORK_WORK:
                        return sorted(result, key=lambda row: (-len(row[0]), row))[:MAX_NETWORK_PATHS]
                    last = points[-1]
                    if not inside[last]:
                        result.add((_canonical(points), names[key]))
                        if len(result) >= MAX_NETWORK_PATHS:
                            return sorted(result, key=lambda row: (-len(row[0]), row))
                        continue
                    if len(points) >= MAX_POINTS:
                        continue
                    for following in sorted(graph[last], reverse=True):
                        if following not in points:
                            pending.append(points + (following,))
    return sorted(result, key=lambda row: (-len(row[0]), row))


def divider_paths(dividers, poly):
    """Actual unbranched surface waterways/railways; never join different kinds.

    Tunnel, bridge and ambiguous layer sections remain visible context but are
    not used to infer a continuous ground-level boundary across a missing part.
    """
    sources = defaultdict(list)
    for item in dividers:
        kind = item.get('divider_type')
        if (kind not in ('river','stream','canal','rail') or item.get('retired')
                or str(item.get('layer') or '0') != '0'
                or item.get('tunnel') not in (None,'','no')
                or item.get('bridge') not in (None,'','no')):
            continue
        sources[kind].append(item)
    paths = []
    for kind, rows in sorted(sources.items()):
        label = 'Jernbane' if kind=='rail' else 'Vandløb'
        for points, name in road_paths(rows, poly, unnamed=''):
            # road_paths keeps unnamed records separate. Use an honest label
            # here, after candidate creation, without inventing a shared name.
            paths.append((points, label + (' · '+name if name else '')))
    return sorted(set(paths), key=lambda row: (-sum(math.dist(a,b) for a,b in zip(row[0],row[0][1:])),row))[:MAX_PATHS]


def path_partition(ring, groups, target, paths):
    weight = sum(g['weight'] for g in groups)
    wanted = max(2, int(weight / target + .5))
    aim = weight * (wanted // 2) / wanted
    bounds = _box(ring)
    candidates = []
    attempts = 0
    for points, name in paths:
        if not _boxes_overlap(_box(points), bounds):
            continue
        if attempts >= MAX_ATTEMPTS:
            break
        attempts += 1
        try:
            parts = split_polygon_path(ring, points)
        except ValueError:
            continue
        if len(groups) * sum(map(len, parts)) > MAX_OWNERSHIP_WORK:
            continue
        allocated = allocate_groups(parts, groups)
        if allocated is None:
            continue
        weights = [sum(g['weight'] for g in rows) for rows in allocated]
        if min(weights) < min(target * .5, weight * .2):
            continue
        score = min(abs(w - aim) for w in weights)
        candidates.append((score, points, name, parts, allocated))
    if not candidates:
        return None
    _, _, name, parts, allocated = min(candidates, key=lambda c: c[:3])
    return parts, allocated, name
