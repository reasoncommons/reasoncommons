"""Deterministic diagrams of published reasoning: layout, SVG, thumbnails and outlines.

Every arrow comes from a published link. The sources of one link meet at an "and"
junction before a single arrow into the target, so joint conditions never look like
separate causes. Statements without a published connection are grouped by role and
are never joined to anything. A feedback loop returns round the right-hand side, and a
remedy's line ends in a bar at the risk it is meant to prevent. A strict hierarchy of
"is needed for" links reads top to bottom instead, as an indented tree that can be stepped through.
"""
from collections import defaultdict
import html
import math

# Advance widths of the self-hosted Alegreya Sans Latin subset, in thousandths of an em,
# measured in a browser, so wrapped SVG text cannot overflow its box. Kerning only narrows text.
_CHARS = (''.join(chr(c) for c in range(48, 58)) + ''.join(chr(c) for c in range(32, 127) if not chr(c).isdigit())
          + '’‘“”—–…·éèàüöäçñ×→←↑↓✓•£€°½≠↗')
_ADVANCES = {
    400: "528,344,455,412,481,418,470,417,474,470,165,256,280,516,428,824,694,166,288,306,374,480,229,307,229,287,229,229,480,480,480,331,825,578,537,520,646,482,434,600,684,268,310,547,416,789,683,635,520,639,555,472,490,626,564,893,594,528,528,288,287,288,424,450,389,462,514,385,518,461,303,487,520,242,265,456,247,800,516,491,509,510,323,370,319,510,423,674,435,427,412,288,314,288,480,167,167,298,296,929,476,581,229,461,461,462,510,491,462,385,516,480,1000,1000,516,516,764,241,416,484,293,683,549,1000",
    500: "525,351,462,420,490,423,475,424,482,475,160,260,310,529,437,836,701,182,291,303,378,480,229,306,229,286,229,229,480,480,480,335,833,587,554,519,650,493,443,599,689,279,321,563,423,792,688,639,534,643,570,483,495,631,573,897,606,541,536,291,286,291,431,447,389,470,518,385,521,465,314,492,525,250,275,472,254,803,521,492,513,514,334,376,327,515,433,685,446,435,417,291,311,291,480,183,183,329,325,912,469,601,229,465,465,470,515,492,470,385,521,480,1000,1000,523,523,764,251,428,478,293,707,549,1000",
    700: "521,360,471,431,503,432,483,432,493,483,151,264,354,549,450,854,711,205,295,300,383,480,229,304,229,284,229,229,480,480,480,340,844,600,579,517,655,509,456,598,696,295,335,584,433,797,695,643,553,649,590,498,503,638,587,903,623,558,547,295,284,295,441,444,389,481,523,385,526,472,329,500,533,261,285,495,263,807,529,494,518,519,348,384,338,522,445,698,461,447,424,295,307,295,480,207,207,372,366,889,461,630,229,472,472,481,522,494,481,385,529,480,1000,1000,532,532,764,268,446,467,293,741,549,1000",
}
WIDTHS = {weight: dict(zip(_CHARS, map(int, row.split(',')))) for weight, row in _ADVANCES.items()}
assert all(len(row) == len(_CHARS) for row in WIDTHS.values())

DOWNWARD = {"overcomes"}            # an intermediate step sits above the obstacle it overcomes
LATERAL = {"precedes", "conflicts_with"}
FEEDBACK = {"feeds_back_to"}        # a loop stays out of the ranking and returns round the right-hand side
BARRED = {"prevents"}               # a remedy sits below the risk, and its line ends in a bar, not an arrow
RELATIONS = {"necessary_for": "is needed for", "contributes_to": "contributes to", "causes": "causes",
             "produces": "produces", "overcomes": "overcomes", "precedes": "comes before",
             "conflicts_with": "conflicts with", "feeds_back_to": "feeds back to", "prevents": "is meant to prevent"}
STANDINGS = {"accepted": "Accepted for now", "proposed": "Proposed", "disputed": "Disputed"}

NODE_W, GOAL_W, PAD_X, PAD = 214, 260, 14, 18
TEXT_SIZE, TEXT_WEIGHT, LINE = 15, 500, 19.5
KIND_SIZE, KIND_TRACK = 10, 1.1
CREDIT_SIZE, CREDIT_WEIGHT, CREDIT_LINE = 12, 400, 15.5  # Who an idea comes from, beneath a reconstruction's statement.
H_GAP = 26
LANE_GAP, LOOP_TAG_W = 24, 74       # loop lanes beyond the right-hand edge, and the width of their "feeds back" tag
HIER_W, INDENT, ROW_GAP = 600, 34, 14  # an indented tree: the root's width, each level's indent and the gap between rows
RAIL_INSET, STEM_Y = 17, 24            # a parent's rail sits this far into its box; a child's stem leaves at its kind line
CHIP_SIZE, CHIP_H = 11, 18


def esc(value):
    return html.escape(str(value), quote=True)


def text_width(text, size, weight=400, tracking=0.0):
    table = WIDTHS[weight]
    return sum(table.get(char, 620) for char in text) * size / 1000 + tracking * len(text)


def wrap(text, width, size=TEXT_SIZE, weight=TEXT_WEIGHT):
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if text_width(candidate, size, weight) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        while text_width(word, size, weight) > width:  # Never let one long token overflow.
            cut = max(1, max(i for i in range(1, len(word) + 1) if text_width(word[:i], size, weight) <= width))
            lines.append(word[:cut])
            word = word[cut:]
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def shown(node):
    return node.get("label") or node["text"]


def box(node, kind_label, width=None):
    width = width or (GOAL_W if node["kind"] == "goal" else NODE_W)
    lines = wrap(shown(node), width - 2 * PAD_X)
    owner = wrap(node["owner"], width - 2 * PAD_X, CREDIT_SIZE, 700) if node.get("owner") else []
    credit = wrap(node["credit"], width - 2 * PAD_X, CREDIT_SIZE, CREDIT_WEIGHT) if node.get("credit") else []
    extra = 8 + (len(owner) + len(credit)) * CREDIT_LINE if owner or credit else 0
    return {"w": width, "h": round(40 + (len(lines) - 1) * LINE + 15 + extra), "lines": lines, "owner": owner, "credit": credit, "kind_label": kind_label}


# ---------------------------------------------------------------- geometry helpers

def spread(count, width, center):
    if count == 1:
        return [center]
    span = min(width - 44, (count - 1) * 22)
    return [center - span / 2 + i * span / (count - 1) for i in range(count)]


def pav(desired, widths, gaps):
    """Positions closest to `desired` (least squares) that keep order and minimum spacing."""
    offsets = [0.0]
    for i in range(1, len(desired)):
        offsets.append(offsets[-1] + (widths[i - 1] + widths[i]) / 2 + gaps[i - 1])
    blocks = []
    for value in (d - o for d, o in zip(desired, offsets)):
        blocks.append([value, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            total, count = blocks.pop()
            blocks[-1][0] += total
            blocks[-1][1] += count
    fitted = [total / count for total, count in blocks for _ in range(count)]
    return [f + o for f, o in zip(fitted, offsets)]


def clean(points):
    result = []
    for point in points:
        point = (round(point[0], 1), round(point[1], 1))
        if result and point == result[-1]:
            continue
        if len(result) >= 2:
            (ax, ay), (bx, by) = result[-2], result[-1]
            if (ax == bx == point[0]) or (ay == by == point[1]):
                result[-1] = point
                continue
        result.append(point)
    return result


def rounded(points, radius=7):
    points = clean(points)
    if len(points) < 2:
        return ""
    d = [f"M{points[0][0]:g},{points[0][1]:g}"]
    for i in range(1, len(points) - 1):
        (px, py), (cx, cy), (nx, ny) = points[i - 1], points[i], points[i + 1]
        r = min(radius, abs(cx - px + cy - py) / 2, abs(nx - cx + ny - cy) / 2)
        sx = cx - r * ((cx > px) - (cx < px))
        sy = cy - r * ((cy > py) - (cy < py))
        ex = cx + r * ((nx > cx) - (nx < cx))
        ey = cy + r * ((ny > cy) - (ny < cy))
        d.append(f"L{sx:g},{sy:g}Q{cx:g},{cy:g} {ex:g},{ey:g}")
    d.append(f"L{points[-1][0]:g},{points[-1][1]:g}")
    return "".join(d)


def arrowhead(points):
    points = clean(points)
    (px, py), (x, y) = points[-2], points[-1]
    dx, dy = (x > px) - (x < px), (y > py) - (y < py)
    return (f"M{x:g},{y:g}L{x - dx * 8 - dy * 4.5:g},{y - dy * 8 + dx * 4.5:g}"
            f"L{x - dx * 8 + dy * 4.5:g},{y - dy * 8 - dx * 4.5:g}Z")


def barhead(points):
    """A short bar across the end of a line: the remedy stops at the risk rather than leading into it."""
    points = clean(points)
    (px, py), (x, y) = points[-2], points[-1]
    dx, dy = (x > px) - (x < px), (y > py) - (y < py)
    x, y = x - dx * 2, y - dy * 2
    return f"M{x - dy * 7:g},{y - dx * 7:g}L{x + dy * 7:g},{y + dx * 7:g}"


def longest_segment(points):
    points = clean(points)
    pairs = list(zip(points, points[1:]))
    (ax, ay), (bx, by) = max(pairs, key=lambda p: abs(p[0][0] - p[1][0]) + abs(p[0][1] - p[1][1]))
    return (ax + bx) / 2, (ay + by) / 2


# ---------------------------------------------------------------- layered layout

def layered(nodes, links, boxes, order):
    """Sugiyama-style layout read from the bottom up: sources below, targets above.

    Loops stay out of the ranking, so a published cycle needs no change of topology: each loop
    leaves the top of its source, runs down a lane beyond the right-hand edge and enters the top of its target.
    """
    ids = list(nodes)
    rank = {i: 0 for i in ids}
    ups, downs = defaultdict(set), defaultdict(set)
    flow = [l for l in links if l["relation"] not in LATERAL | FEEDBACK]
    loops = [l for l in links if l["relation"] in FEEDBACK]
    for link in flow:
        for source in link["from"]:
            lower, upper = (link["to"], source) if link["relation"] in DOWNWARD else (source, link["to"])
            ups[lower].add(upper)
            downs[upper].add(lower)
    indegree = {i: len(downs[i]) for i in ids}
    queue = sorted((i for i in ids if not indegree[i]), key=order.get)
    seen = 0
    while queue:
        current = queue.pop(0)
        seen += 1
        for upper in sorted(ups[current], key=order.get):
            rank[upper] = max(rank[upper], rank[current] + 1)
            indegree[upper] -= 1
            if not indegree[upper]:
                queue.append(upper)
    if seen != len(ids):
        raise ValueError("A cycle needs explicit layout support; do not silently alter topology")
    for i in ids:  # Sources sit just below their lowest target rather than at the bottom.
        if not downs[i] and ups[i]:
            rank[i] = min(rank[u] for u in ups[i]) - 1
    for link in loops:  # A statement joined only by a loop sits just above what it feeds back to.
        for source in link["from"]:
            if not ups[source] and not downs[source]:
                rank[source] = max(rank[source], rank[link["to"]] + 1)

    widths = {i: boxes[i]["w"] for i in ids}
    okey = {i: order[i] for i in ids}
    up_n, down_n = defaultdict(list), defaultdict(list)
    chains = {}
    dummy = 0
    for link in flow:
        for source in link["from"]:
            lower, upper = (link["to"], source) if link["relation"] in DOWNWARD else (source, link["to"])
            chain = [lower]
            for r in range(rank[lower] + 1, rank[upper]):
                name = f"~{dummy}"
                dummy += 1
                rank[name], widths[name], okey[name] = r, 14, okey[lower] + 0.5
                chain.append(name)
            chain.append(upper)
            for a, b in zip(chain, chain[1:]):
                up_n[a].append(b)
                down_n[b].append(a)
            chains[(link["id"], source)] = chain
    layers = defaultdict(list)
    for element in rank:
        layers[rank[element]].append(element)
    for layer in layers.values():
        layer.sort(key=okey.get)
    top = max(layers)
    lateral = [(l["from"][0], l["to"]) for l in links if l["relation"] == "precedes"]

    def reorder(layer, neighbours, reference):
        position = {e: i for i, e in enumerate(reference)}
        valued = [(sum(position[n] for n in neighbours[e]) / len(neighbours[e]), i, e)
                  for i, e in enumerate(layer) if neighbours[e]]
        valued.sort()
        result = [None] * len(layer)
        fixed = {i for i, e in enumerate(layer) if not neighbours[e]}
        for i in fixed:
            result[i] = layer[i]
        slots = iter(i for i in range(len(layer)) if i not in fixed)
        for _, _, element in valued:
            result[next(slots)] = element
        for before, after in lateral:
            if before in result and after in result and result.index(before) > result.index(after):
                result.remove(before)
                result.insert(result.index(after), before)
        layer[:] = result

    for sweep in range(8):
        if sweep % 2 == 0:
            for r in range(top - 1, -1, -1):
                reorder(layers[r], up_n, layers[r + 1])
        else:
            for r in range(1, top + 1):
                reorder(layers[r], down_n, layers[r - 1])

    beside = {frozenset(pair) for pair in lateral}

    def gaps(layer):  # Room for a "then" arrow between neighbours in sequence.
        return [10 if a.startswith("~") or b.startswith("~") else 76 if frozenset((a, b)) in beside else H_GAP
                for a, b in zip(layer, layer[1:])]

    x = {}
    for layer in layers.values():
        cursor = 0
        for element, gap in zip(layer, gaps(layer) + [0]):
            x[element] = cursor + widths[element] / 2
            cursor += widths[element] + gap
    for sweep in range(40):
        downward = sweep % 2 == 0
        for r in (range(top - 1, -1, -1) if downward else range(1, top + 1)):
            layer = layers[r]
            neighbours = up_n if downward else down_n
            # math.fsum rounds exactly, so positions do not depend on how a Python version sums floats.
            desired = [math.fsum(x[n] for n in neighbours[e]) / len(neighbours[e]) if neighbours[e] else x[e] for e in layer]
            for element, value in zip(layer, pav(desired, [widths[e] for e in layer], gaps(layer))):
                x[element] = value
    left = min(x[e] - widths[e] / 2 for e in x)
    for element in x:
        x[element] += PAD - left
    right = max(x[e] + widths[e] / 2 for e in x)
    lanes = {link["id"]: right + LANE_GAP + 6 + k * LANE_GAP for k, link in enumerate(loops)}

    # Attachment slots: every connection touches the top of its lower element and the bottom of its upper one.
    junctions = {}
    for link in flow:
        if len(link["from"]) < 2:
            continue
        below = [chains[(link["id"], s)][-2] for s in link["from"]]
        junctions[link["id"]] = {"x": math.fsum(x[e] for e in below) / len(below), "rank": rank[link["to"]], "link": link}
    top_slots, bottom_slots = defaultdict(list), defaultdict(list)
    for link in loops:  # Loops leave and enter at the right-hand end of a box's top edge.
        for source in link["from"]:
            top_slots[source].append((float("inf"), (link["id"], source, "~loop")))
        top_slots[link["to"]].append((float("inf"), (link["id"], "~loop-in", None)))
    for link in flow:
        junction = junctions.get(link["id"])
        for source in link["from"]:
            chain = chains[(link["id"], source)]
            for a, b in zip(chain, chain[1:]):
                upper_x = junction["x"] if junction and b == chain[-1] else x[b]
                top_slots[a].append((upper_x, (link["id"], source, a)))
                if not (junction and b == chain[-1]):
                    bottom_slots[b].append((x[a], (link["id"], source, a)))
        if junction:
            bottom_slots[link["to"]].append((junction["x"], (link["id"], "~join", None)))
    attach_top, attach_bottom = {}, {}
    for slots, attach in ((top_slots, attach_top), (bottom_slots, attach_bottom)):
        for element, entries in slots.items():
            entries.sort(key=lambda entry: entry[0])
            if element.startswith("~"):
                positions = [x[element]] * len(entries)
            else:
                positions = spread(len(entries), widths[element], x[element])
            for (_, key), position in zip(entries, positions):
                attach[(element, key)] = position

    # Horizontal segments per gap, assigned to levels so nested elbows never cross.
    segments = defaultdict(list)  # (rank of upper layer, zone) -> [(lo, hi, key)]

    def run_gap(element):  # A loop's horizontal run sits in the gap above a box, or in a margin above the top layer.
        return (rank[element] + 1, "upper") if rank[element] < top else ("top", "upper")
    for link in loops:
        lane = lanes[link["id"]]
        for element, key in [(s, (link["id"], s, "~loop")) for s in link["from"]] + [(link["to"], (link["id"], "~loop-in", None))]:
            segments[run_gap(element)].append((attach_top[(element, key)], lane, key))
    for link in flow:
        junction = junctions.get(link["id"])
        for source in link["from"]:
            chain = chains[(link["id"], source)]
            for a, b in zip(chain, chain[1:]):
                key = (link["id"], source, a)
                ax = attach_top[(a, key)]
                if junction and b == chain[-1]:
                    bx, zone = junction["x"], "lower"
                else:
                    bx, zone = attach_bottom[(b, key)], "upper"
                segments[(rank[b], zone)].append((min(ax, bx), max(ax, bx), key))
        if junction:
            key = (link["id"], "~join", None)
            bx = attach_bottom[(link["to"], key)]
            segments[(rank[link["to"]], "upper")].append((min(junction["x"], bx), max(junction["x"], bx), key))
    level = {}
    counts = defaultdict(int)
    for gap, items in segments.items():
        placed = defaultdict(list)
        for lo, hi, key in sorted(items, key=lambda s: -(s[1] - s[0])):
            if hi - lo < 1:
                level[(gap, key)] = None
                continue
            index = 0
            while any(lo - 8 < h and l < hi + 8 for l, h in placed[index]):
                index += 1
            placed[index].append((lo, hi))
            level[(gap, key)] = index
            counts[gap] = max(counts[gap], index + 1)

    # Vertical positions: tops aligned per layer, gaps sized for their levels and junctions.
    layer_h = {r: max([boxes[e]["h"] for e in layer if not e.startswith("~")] or [0]) for r, layer in layers.items()}
    has_junction = {j["rank"] for j in junctions.values()}
    margin = counts[("top", "upper")]
    layer_top, gap_top, y = {}, {}, PAD + (14 + (margin - 1) * 9 + 18 if margin else 0)
    for r in range(top, -1, -1):
        layer_top[r] = y
        y += layer_h[r]
        if r == 0:
            break
        gap_top[r] = y
        upper, lower = counts[(r, "upper")], counts[(r, "lower")]
        height = 16 + max(upper - 1, 0) * 9 + 16
        if r in has_junction:
            height += 30 + max(lower - 1, 0) * 8 + 14
        y += max(height, 46)
    canvas_h = y + PAD

    def level_y(r, zone, index):
        if zone == "upper":
            return gap_top[r] + 16 + (index or 0) * 9
        return junction_y(r) + 9 + 12 + (index or 0) * 8

    def junction_y(r):
        return gap_top[r] + 16 + max(counts[(r, "upper")] - 1, 0) * 9 + 16 + 9

    def top_of(element):
        return layer_top[rank[element]]

    def run_y(element, key):
        gap = run_gap(element)
        index = level.get((gap, key)) or 0
        return PAD + 14 + index * 9 if gap[0] == "top" else level_y(gap[0], "upper", index)

    def bottom_of(element):
        return layer_top[rank[element]] + (boxes[element]["h"] if not element.startswith("~") else layer_h[rank[element]])

    placed_nodes = {i: {"x": x[i] - widths[i] / 2, "y": layer_top[rank[i]], **boxes[i]} for i in ids}
    paths, joins = [], []
    for link in flow:
        junction = junctions.get(link["id"])
        for source in link["from"]:
            chain = chains[(link["id"], source)]
            key = (link["id"], source, chain[0])
            points = [(attach_top[(chain[0], key)], top_of(chain[0]))]
            for a, b in zip(chain, chain[1:]):
                key = (link["id"], source, a)
                ax = attach_top[(a, key)]
                into_junction = bool(junction and b == chain[-1])
                r = rank[b]
                zone = "lower" if into_junction else "upper"
                ly = level_y(r, zone, level.get(((r, zone), key)))
                if into_junction:
                    jx, jy = junction["x"], junction_y(r)
                    points += [(ax, ly), (jx, ly), (jx, jy + 9)]
                else:
                    bx = attach_bottom[(b, key)]
                    points += [(ax, ly), (bx, ly), (bx, bottom_of(b))]
                    if b.startswith("~"):
                        points.append((bx, top_of(b)))
            downward = link["relation"] in DOWNWARD
            if downward:
                points.reverse()
            paths.append({"points": points, "link": link, "arrow": not junction})
        if junction:
            r = rank[link["to"]]
            key = (link["id"], "~join", None)
            jx, jy = junction["x"], junction_y(r)
            bx = attach_bottom[(link["to"], key)]
            ly = level_y(r, "upper", level.get(((r, "upper"), key)))
            joins.append({"x": jx, "y": jy, "link": link})
            paths.append({"points": [(jx, jy - 9), (jx, ly), (bx, ly), (bx, bottom_of(link["to"]))], "link": link, "arrow": True})
    for link in links:
        if link["relation"] not in LATERAL:
            continue
        a, b = placed_nodes[link["from"][0]], placed_nodes[link["to"]]
        if a["x"] > b["x"]:
            start, end = (a["x"], a["y"] + a["h"] / 2), (b["x"] + b["w"], b["y"] + b["h"] / 2)
        else:
            start, end = (a["x"] + a["w"], a["y"] + a["h"] / 2), (b["x"], b["y"] + b["h"] / 2)
        mid = (start[0] + end[0]) / 2
        points = [start, (mid, start[1]), (mid, end[1]), end]
        paths.append({"points": points, "link": link, "arrow": True, "lateral": True})
    for link in loops:
        lane, target = lanes[link["id"]], link["to"]
        key = (link["id"], "~loop-in", None)
        tx, ty = attach_top[(target, key)], run_y(target, key)
        arrival = [(lane, ty), (tx, ty), (tx, top_of(target))]
        runs = []
        for source in link["from"]:
            key = (link["id"], source, "~loop")
            sx, sy = attach_top[(source, key)], run_y(source, key)
            runs.append(((sx, top_of(source)), (sx, sy), (lane, sy)))
        if len(runs) == 1:
            paths.append({"points": list(runs[0]) + arrival, "link": link, "arrow": True, "loop": True,
                          "tag": (lane, (runs[0][2][1] + ty) / 2)})
            continue
        for run in runs:  # Joint sources meet at an "and" where the lane turns towards the target, from above or below.
            side = 1 if run[2][1] < ty else -1
            paths.append({"points": list(run) + [(lane, ty - side * 9)], "link": link, "arrow": False, "loop": True})
        joins.append({"x": lane, "y": ty, "link": link})
        far = max((r[2][1] for r in runs), key=lambda value: abs(value - ty))
        paths.append({"points": [(lane - 17, ty)] + arrival[1:], "link": link, "arrow": True, "loop": True, "tag": (lane, (far + ty) / 2)})
    width = max([n["x"] + n["w"] for n in placed_nodes.values()] + [lane + LOOP_TAG_W / 2 for lane in lanes.values()]) + PAD
    return {"w": round(width), "h": round(canvas_h), "nodes": placed_nodes, "paths": paths, "joins": joins, "markers": []}


# ---------------------------------------------------------------- hierarchy: an indented tree, top to bottom

def is_hierarchy(ids, links):
    """One root, one parent each, one source per link and only "is needed for": an indented tree draws it without loss."""
    parents = {}
    for link in links:
        if len(link["from"]) != 1 or link["relation"] != "necessary_for" or link["from"][0] in parents:
            return False
        parents[link["from"][0]] = link["to"]
    return len(ids) > 2 and len(parents) == len(ids) - 1


def plural(count, label):
    word = label.lower()
    return f"{count} {word if count == 1 else word[:-1] + 'ies' if word.endswith('y') else word + 's'}"


def indented(nodes, links, kind_label, order):
    """The root first, each child beneath its parent and indented, joined to it by a rail down the parent's left side.

    Rows are in reading order, so hiding a branch only closes the gap it leaves; app.js relies on that to step through.
    """
    parent = {l["from"][0]: (l["to"], l) for l in links}
    children = defaultdict(list)
    for child in sorted(parent, key=order.get):
        children[parent[child][0]].append(child)
    root = next(i for i in sorted(nodes, key=order.get) if i not in parent)
    rows, stack = [], [(root, 0)]
    while stack:
        ident, depth = stack.pop()
        rows.append((ident, depth))
        stack.extend((child, depth + 1) for child in reversed(children[ident]))
    placed, y = {}, PAD
    for ident, depth in rows:
        placed[ident] = {**box(nodes[ident], kind_label(nodes[ident]["kind"]), HIER_W - depth * INDENT),
                         "x": PAD + depth * INDENT, "y": y, "depth": depth, "parent": parent.get(ident, (None,))[0]}
        kids = children[ident]
        if kids:
            labels = {kind_label(nodes[k]["kind"]) for k in kids}
            chip = plural(len(kids), labels.pop() if len(labels) == 1 else "statement")
            placed[ident].update(kids=len(kids), chip=chip, chip_w=round(text_width(chip, CHIP_SIZE, 700) + 34))
        y += placed[ident]["h"] + ROW_GAP
    paths = []
    for ident, _ in rows[1:]:
        up, link = parent[ident]
        child, top = placed[ident], placed[up]
        rail, stem = top["x"] + RAIL_INSET, child["y"] + STEM_Y
        paths.append({"points": [(child["x"], stem), (rail, stem), (rail, top["y"] + top["h"])], "link": link, "arrow": True})
    return {"w": PAD * 2 + HIER_W, "h": round(y - ROW_GAP + PAD), "nodes": placed, "paths": paths, "joins": [], "markers": [], "hierarchy": True}


# ---------------------------------------------------------------- conflict cloud

def cloud_roles(nodes, links):
    """The classic five-box cloud, when the published kinds have that shape; otherwise None."""
    by_kind = defaultdict(list)
    for node in nodes.values():
        by_kind[node["kind"]].append(node["id"])
    if len(by_kind["objective"]) != 1 or len(by_kind["need"]) != 2 or len(by_kind["prerequisite"]) != 2 or len(nodes) != 5:
        return None
    needs, positions = by_kind["need"], by_kind["prerequisite"]
    for link in links:  # Pair each position with the need its published link serves.
        if link["relation"] == "necessary_for" and link["to"] in needs and link["from"][0] in positions:
            if needs.index(link["to"]) != positions.index(link["from"][0]):
                positions.reverse()
            break
    return {"a": by_kind["objective"][0], "b": needs[0], "c": needs[1], "d": positions[0], "e": positions[1]}


def cloud(nodes, links, boxes, roles):
    col = {"a": 0, "b": 1, "c": 1, "d": 2, "e": 2}
    step = NODE_W + 124
    top_h = max(boxes[roles["b"]]["h"], boxes[roles["d"]]["h"])
    low_h = max(boxes[roles["c"]]["h"], boxes[roles["e"]]["h"])
    row_gap = 96
    placed = {}
    for role, ident in roles.items():
        b = boxes[ident]
        if role == "a":
            y = PAD + (top_h + row_gap + low_h) / 2 - b["h"] / 2
        elif role in "bd":
            y = PAD + (top_h - b["h"]) / 2
        else:
            y = PAD + top_h + row_gap + (low_h - b["h"]) / 2
        placed[ident] = {"x": PAD + col[role] * step, "y": y, **b}
    who = {ident: role for role, ident in roles.items()}
    paths, markers = [], []

    def mid(node):
        return node["y"] + node["h"] / 2

    for link in links:
        source, target = who.get(link["from"][0]), who.get(link["to"])
        s, t = placed[link["from"][0]], placed[link["to"]]
        if link["relation"] == "conflicts_with":
            x0 = s["x"] + s["w"] / 2
            y0, y1 = (s["y"] + s["h"], t["y"]) if s["y"] < t["y"] else (s["y"], t["y"] + t["h"])
            ym = (y0 + y1) / 2
            points = [(x0, y0), (x0, ym - 14), (x0 + 9, ym - 6), (x0 - 9, ym + 6), (x0, ym + 14), (x0, y1)]
            paths.append({"points": points, "link": link, "arrow": False, "conflict": True, "zigzag": True})
            markers.append({"x": x0 + 26, "y": ym, "link": link})
        elif source in ("b", "c") and target == "a":
            offset = -14 if source == "b" else 14
            elbow = t["x"] + t["w"] + 62
            points = [(s["x"], mid(s)), (elbow, mid(s)), (elbow, mid(t) + offset), (t["x"] + t["w"], mid(t) + offset)]
            paths.append({"points": points, "link": link, "arrow": True})
            markers.append({"x": elbow, "y": (mid(s) + mid(t) + offset) / 2, "link": link})
        elif source in ("d", "e") and target in ("b", "c"):
            y_s, y_t = mid(s), mid(t)
            elbow = t["x"] + t["w"] + 62
            points = [(s["x"], y_s), (elbow, y_s), (elbow, y_t), (t["x"] + t["w"], y_t)]
            paths.append({"points": points, "link": link, "arrow": True})
            markers.append({"x": s["x"] - 20, "y": y_s, "link": link})  # Near the position, clear of any standing tag.
        else:
            return None  # An unexpected relation inside the cloud: fall back to the generic layout.
    markers = [m for m in markers if m["link"].get("assumptions")]
    width = PAD + 2 * step + NODE_W + PAD
    height = PAD + top_h + row_gap + low_h + PAD
    return {"w": round(width), "h": round(height), "nodes": placed, "paths": paths, "joins": [], "markers": markers}


# ---------------------------------------------------------------- tree analysis

def view_context(tree, members):
    """A titled part draws every connection into its own statements; sources from elsewhere join as muted context, so no joint condition is split."""
    links = [l for l in tree["links"] if l["to"] in members]
    context = [s for l in links for s in l["from"] if s not in members]
    return links, list(dict.fromkeys(context))


def path_between(tree, start, end):
    """Statements passed through on the shortest chain of published causal links from start to end, or None."""
    forward = defaultdict(set)
    for link in tree["links"]:
        if link["relation"] in ("contributes_to", "necessary_for", "produces"):
            for source in link["from"]:
                forward[source].add(link["to"])
    queue, seen = [(start, [])], {start}
    while queue:
        current, route = queue.pop(0)
        for following in sorted(forward[current]):
            if following == end:
                return route
            if following not in seen:
                seen.add(following)
                queue.append((following, route + [following]))
    return None


def components(tree):
    """Connected pieces (with their links) in source order, and statements with no published link."""
    order = {n["id"]: i for i, n in enumerate(tree["nodes"])}
    parent = {n["id"]: n["id"] for n in tree["nodes"]}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    linked = set()
    for link in tree["links"]:
        ends = link["from"] + [link["to"]]
        linked.update(ends)
        for other in ends[1:]:
            parent[find(other)] = find(ends[0])
    groups = defaultdict(list)
    for node in tree["nodes"]:
        if node["id"] in linked:
            groups[find(node["id"])].append(node["id"])
    pieces = []
    for members in sorted(groups.values(), key=lambda m: min(order[i] for i in m)):
        member_set = set(members)
        pieces.append({"ids": members, "links": [l for l in tree["links"] if l["to"] in member_set]})
    pieces.sort(key=lambda p: -len(p["ids"]))
    loose = [n["id"] for n in tree["nodes"] if n["id"] not in linked]
    return pieces, loose


def geometry(tree, ids, links, kind_label):
    nodes = {n["id"]: n for n in tree["nodes"] if n["id"] in set(ids)}
    order = {n["id"]: i for i, n in enumerate(tree["nodes"])}
    if is_hierarchy(ids, links):
        return annotate(indented(nodes, links, kind_label, order), nodes)
    boxes = {i: box(nodes[i], kind_label(nodes[i]["kind"])) for i in nodes}
    roles = cloud_roles(nodes, links) if tree.get("name") == "conflict" else None
    shape = cloud(nodes, links, boxes, roles) if roles else None
    return annotate(shape or layered(nodes, links, boxes, order), nodes)


# ---------------------------------------------------------------- SVG

def _standing(node, x, y, width, uniform=False):
    if uniform:  # One banner states the standing of everything in this commons.
        return ""
    status = node["status"]
    if status == "accepted":
        cx = x + width - PAD_X - 9
        return f'<path class="n-check" d="M{cx:g},{y - 4:g}l3.2,3.4l6,-7.2"/>'
    word = STANDINGS[status].upper()
    return f'<text class="n-standing" x="{x + width - PAD_X:g}" y="{y:g}" text-anchor="end">{esc(word)}</text>'


def node_svg(node, placed, href, focus=False, context=None, uniform=False):
    """One statement as a link; `context` names the part a muted box belongs to when it is drawn only for context."""
    x, y, w, h = placed["x"], placed["y"], placed["w"], placed["h"]
    classes = f'n role-{node["kind"]}' + ("" if uniform else f' is-{node["status"]}') + (" is-focus" if focus else "") + (" is-context" if context else "")
    standing = STANDINGS[node["status"]]
    label = (f'{placed["kind_label"]}, {standing.lower()}: {node["text"]}' + (f' {node["owner"]}.' if node.get("owner") else "")
             + (f' {node["credit"]}.' if node.get("credit") else "") + (f' Shown for context from {context}.' if context else ""))
    kind = placed["kind_label"].upper()
    kind_room = w - 2 * PAD_X - (0 if uniform else 16 if node["status"] == "accepted" else text_width(STANDINGS[node["status"]].upper(), KIND_SIZE, 700, KIND_TRACK) + 8)
    if text_width(kind, KIND_SIZE, 700, KIND_TRACK) > kind_room:
        while kind and text_width(kind + "…", KIND_SIZE, 700, KIND_TRACK) > kind_room:
            kind = kind[:-1].rstrip()
        kind += "…"
    lines = "".join(f'<tspan x="{x + PAD_X:g}" dy="{0 if i == 0 else LINE:g}">{esc(line)}</tspan>' for i, line in enumerate(placed["lines"]))
    notes, top = "", y + 40 + (len(placed["lines"]) - 1) * LINE + 7 + CREDIT_LINE
    for css, rows in (("n-owner", placed.get("owner", [])), ("n-credit", placed.get("credit", []))):
        if rows:  # Baselines start one note line below the statement's last line, after a small gap.
            spans = "".join(f'<tspan x="{x + PAD_X:g}" dy="{0 if i == 0 else CREDIT_LINE:g}">{esc(line)}</tspan>' for i, line in enumerate(rows))
            notes += f'<text class="{css}" x="{x + PAD_X:g}" y="{top:g}">{spans}</text>'
            top += len(rows) * CREDIT_LINE
    focus_ring = f'<rect class="n-ring" x="{x - 5:g}" y="{y - 5:g}" width="{w + 10:g}" height="{h + 10:g}" rx="13"/>' if focus else ""
    rows, chip = "", ""
    if "depth" in placed:  # A row of an indented tree: where it sits, for stepping through.
        rows = (f' data-depth="{placed["depth"]}" data-x="{x:g}" data-y="{y:g}" data-h="{h:g}"'
                + (f' data-parent="{esc(placed["parent"])}"' if placed["parent"] else "") + (f' data-kids="{placed["kids"]}"' if placed.get("kids") else ""))
    if placed.get("chip"):  # Shown only while stepping through: what opening this box reveals.
        cw, cx, cy = placed["chip_w"], x + w - PAD_X - placed["chip_w"], y + h - CHIP_H / 2
        chip = (f'<g class="n-chip"><rect x="{cx:g}" y="{cy:g}" width="{cw:g}" height="{CHIP_H}" rx="{CHIP_H / 2:g}"/>'
                f'<path class="n-chev" d="M{cx + 10:g},{cy + 7:g}l4,4l4,-4"/>'
                f'<text x="{cx + 24:g}" y="{cy + 12.5:g}">{esc(placed["chip"])}</text></g>')
    return (f'<a class="{classes}" href="{esc(href)}" data-id="{esc(node["id"])}"{rows} aria-label="{esc(label)}">{focus_ring}'
            f'<rect class="n-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="9"/>'
            f'<text class="n-kind" x="{x + PAD_X:g}" y="{y + 20:g}">{esc(kind)}</text>{_standing(node, x, y + 20, w, uniform)}'
            f'<text class="n-text" x="{x + PAD_X:g}" y="{y + 40:g}">{lines}</text>{notes}{chip}</a>')


def svg(shape, nodes, href, title, focus=None, css="", context=None, uniform=False):
    """A diagram whose statements and connections are links into the statement pages.

    `context` maps muted boxes, drawn only so that a joint condition stays whole, to the part each belongs to;
    `uniform` drops the per-box standing where one banner states the standing of everything.
    """
    context = context or {}
    css = (css + " is-uniform" if uniform else css).strip()
    steps = (f' data-hierarchy data-pad="{PAD}" data-row-gap="{ROW_GAP}" data-rail="{RAIL_INSET}" data-stem="{STEM_Y}"'
             if shape.get("hierarchy") else "")
    parts = [f'<svg class="rc-diagram {css}" viewBox="0 0 {shape["w"]} {shape["h"]}" width="{shape["w"]}" height="{shape["h"]}" role="group" aria-label="{esc(title)}"{steps}>']
    for path in shape["paths"]:
        link = path["link"]
        d = rounded(path["points"]) if not path.get("zigzag") else "M" + "L".join(f"{px:g},{py:g}" for px, py in clean(path["points"]))
        cls = ("e" + ("" if uniform else f' is-{link["status"]}') + (" e-conflict" if path.get("conflict") else "") + (" e-down" if link["relation"] in DOWNWARD else "")
               + (" e-loop" if link["relation"] in FEEDBACK else "") + (" e-prevent" if link["relation"] in BARRED else ""))
        cls += " is-focus" if focus == link["id"] else ""
        label = f'Connection, {STANDINGS[link["status"]].lower()}: {RELATIONS.get(link["relation"], link["relation"].replace("_", " "))}'
        if path["arrow"] and link["relation"] in BARRED:
            head = f'<path class="e-bar" d="{barhead(path["points"])}"/>'
        else:
            head = f'<path class="e-head" d="{arrowhead(path["points"])}"/>' if path["arrow"] else ""
        tag = ""
        if path.get("tag"):
            tx, ty = path["tag"]
            tag = (f'<g class="e-tag e-tag-loop"><rect x="{tx - LOOP_TAG_W / 2:g}" y="{ty - 9:g}" width="{LOOP_TAG_W}" height="18" rx="9"/>'
                   f'<text x="{tx:g}" y="{ty + 4:g}" text-anchor="middle">feeds back</text></g>')
        elif link["status"] == "disputed" and path["arrow"]:
            mx, my = longest_segment(path["points"])
            tag = f'<g class="e-tag"><rect x="{mx - 30:g}" y="{my - 9:g}" width="60" height="18" rx="9"/><text x="{mx:g}" y="{my + 4:g}" text-anchor="middle">disputed</text></g>'
        if path.get("lateral") and link["relation"] == "precedes":
            (sx, sy), (ex, ey) = path["points"][0], path["points"][-1]
            tag += f'<text class="e-word" x="{(sx + ex) / 2:g}" y="{min(sy, ey) - 7:g}" text-anchor="middle">then</text>'
        parts.append(f'<a class="{cls}" href="{esc(href(link["id"]))}" data-id="{esc(link["id"])}" data-ends="{esc(" ".join(link["from"] + [link["to"]]))}" aria-label="{esc(label)}">'
                     f'<path class="e-hit" d="{d}"/><path class="e-line" d="{d}"/>{head}{tag}</a>')
    for join in shape["joins"]:
        link = join["link"]
        parts.append(f'<a class="j{"" if uniform else " is-" + link["status"]}" href="{esc(href(link["id"]))}" data-id="{esc(link["id"])}" aria-label="All of these together"><rect x="{join["x"] - 17:g}" y="{join["y"] - 9:g}" width="34" height="18" rx="9"/>'
                     f'<text x="{join["x"]:g}" y="{join["y"] + 4:g}" text-anchor="middle">and</text></a>')
    for ident, placed in shape["nodes"].items():
        parts.append(node_svg(nodes[ident], placed, href(ident), focus == ident, context.get(ident), uniform))
    for marker in shape.get("markers", []):
        number = marker.get("number")
        if number:
            parts.append(f'<g class="m"><circle cx="{marker["x"]:g}" cy="{marker["y"]:g}" r="10"/><text x="{marker["x"]:g}" y="{marker["y"] + 4:g}" text-anchor="middle">{number}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def thumbnail(shapes, loose_nodes, width=176, height=96):
    """The real shape of a tree, small: boxes coloured by role, lines for published links, loose dots."""
    parts = [f'<svg class="rc-thumb" viewBox="0 0 {width} {height}" width="{width}" height="{height}" aria-hidden="true" focusable="false">']
    regions = []
    count = len(shapes) + (1 if loose_nodes else 0)
    if not count:
        parts.append(f'<rect class="t-empty" x="1" y="1" width="{width - 2}" height="{height - 2}" rx="8"/></svg>')
        return "".join(parts)
    weights = [max(s["w"], 1) for s in shapes] + ([max(260, 90 * min(len(loose_nodes), 4))] if loose_nodes else [])
    total = sum(weights)
    cursor = 4
    for weight in weights:
        span = (width - 8 - 6 * (count - 1)) * weight / total
        regions.append((cursor, span))
        cursor += span + 6
    for (left, span), shape in zip(regions, shapes):
        scale = min(span / shape["w"], (height - 8) / shape["h"])
        ox = left + (span - shape["w"] * scale) / 2
        oy = (height - shape["h"] * scale) / 2
        parts.append(f'<g transform="translate({ox:.1f} {oy:.1f}) scale({scale:.4f})">')
        for path in shape["paths"]:
            d = rounded(path["points"], 0)
            parts.append(f'<path class="t-edge is-{path["link"]["status"]}" d="{d}" vector-effect="non-scaling-stroke"/>')
        for placed in shape["nodes"].values():
            parts.append(f'<rect class="t-node role-{placed["kind"]} is-{placed["status"]}" x="{placed["x"]:.0f}" y="{placed["y"]:.0f}" width="{placed["w"]:.0f}" height="{placed["h"]:.0f}" rx="14" vector-effect="non-scaling-stroke"/>')
        parts.append("</g>")
    if loose_nodes:  # Unconnected statements: a loose grid of separate boxes, as large as the space allows.
        left, span = regions[-1]
        count, gap, cap = len(loose_nodes), 5, width * 0.18
        fits = []
        for columns in range(1, count + 1):
            rows = -(-count // columns)
            w = min(span / columns - gap, cap)
            if w > 0 and rows * (w * 0.6 + gap) - gap <= height - 12:
                fits.append((w, columns, rows))
        w, columns, rows = max(fits) if fits else ((span / count) - gap, count, 1)
        h = w * 0.6
        ox = left + (span - (columns * (w + gap) - gap)) / 2
        oy = (height - (rows * (h + gap) - gap)) / 2
        for i, node in enumerate(loose_nodes):
            x, y = ox + (i % columns) * (w + gap), oy + (i // columns) * (h + gap)
            parts.append(f'<rect class="t-node t-loose role-{node["kind"]} is-{node["status"]}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{min(3, w / 6):.1f}"/>')
    parts.append("</svg>")
    return "".join(parts)


def annotate(shape, nodes):
    """Attach kind and standing to placed boxes so thumbnails can be drawn from geometry alone."""
    for ident, placed in shape["nodes"].items():
        placed["kind"], placed["status"] = nodes[ident]["kind"], nodes[ident]["status"]
    return shape


def number_markers(shape):
    """Number the assumptions sitting on cloud arrows, in reading order."""
    order = sorted(shape.get("markers", []), key=lambda m: (round(m["y"] / 40), -m["x"]))
    notes = []
    for marker in order:
        marker["number"] = len(notes) + 1
        notes.append(marker["link"])
    return notes


# ---------------------------------------------------------------- neighbourhood

def neighbourhood(tree, item_id, kind_label, href, uniform=False):
    """A small diagram centred on one statement or connection: only its own published links."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    links = {l["id"]: l for l in tree["links"]}
    if item_id in links:
        selected = [links[item_id]]
    else:
        selected = [l for l in tree["links"] if item_id in l["from"] or l["to"] == item_id]
    if not selected:
        return ""
    ids = []
    for link in selected:
        for ident in link["from"] + [link["to"]]:
            if ident not in ids:
                ids.append(ident)
    order = {n["id"]: i for i, n in enumerate(tree["nodes"])}
    sub = {i: nodes[i] for i in sorted(ids, key=order.get)}
    boxes = {i: box(sub[i], kind_label(sub[i]["kind"]), 196) for i in sub}
    shape = layered(sub, selected, boxes, order)
    return svg(shape, sub, href, "Where this sits", focus=item_id, css="rc-near", uniform=uniform)


# ---------------------------------------------------------------- outline

def outline(tree, ids, links, href, kind_label, uniform=False):
    """The same published topology as nested text, read from the final effect downwards."""
    nodes = {n["id"]: n for n in tree["nodes"]}
    order = {n["id"]: i for i, n in enumerate(tree["nodes"])}
    member = set(ids)
    incoming = defaultdict(list)
    has_parent = set()
    lateral, loops = defaultdict(list), defaultdict(list)
    for link in links:
        if link["relation"] in LATERAL:
            lateral[link["from"][0]].append(link)
            continue
        if link["relation"] in FEEDBACK:  # A loop is noted beside each source; it never makes a parent.
            for source in link["from"]:
                loops[source].append(link)
            continue
        if link["relation"] in DOWNWARD:
            incoming[link["from"][0]].append(("down", link))
            has_parent.add(link["to"])
        else:
            incoming[link["to"]].append(("up", link))
            has_parent.update(link["from"])
    roots = sorted((i for i in member if i not in has_parent), key=order.get)
    shown_once = set()

    def chip(status):
        return "" if status == "accepted" or uniform else f' <span class="chip chip-{status}">{STANDINGS[status]}</span>'

    def standing(item):
        return "" if uniform else f' is-{item["status"]}'

    def names_of(idents):
        return "” and “".join(shown(nodes[i]) for i in idents)

    def line(ident, prefix=""):
        node = nodes[ident]
        owner = f'<span class="o-owner">{esc(node["owner"])}</span>' if node.get("owner") else ""
        credit = f'<span class="o-credit">{esc(node["credit"])}</span>' if node.get("credit") else ""
        return (f'{prefix}<a class="o-item role-{node["kind"]}" href="{esc(href(ident))}"><span class="o-kind">{esc(kind_label(node["kind"]))}</span>'
                f'<span class="o-text">{esc(node["text"])}</span>{owner}{credit}</a>{chip(node["status"])}')

    def branch(ident, depth=0):
        if ident in shown_once:
            return f'<li class="o-again">{line(ident)} <span class="o-note">shown above</span></li>'
        shown_once.add(ident)
        parts = [f"<li>{line(ident)}"]
        for link in lateral.get(ident, []):
            parts.append(f'<p class="o-then">then → <a href="{esc(href(link["to"]))}">{esc(nodes[link["to"]]["text"])}</a></p>')
        for link in loops.get(ident, []):
            together = [s for s in link["from"] if s != ident]
            joint = f'with “{esc(names_of(together))}”, ' if together else ""
            parts.append(f'<p class="o-then o-loop">↺ {joint}<a class="o-rel{standing(link)}" href="{esc(href(link["id"]))}">feeds back to</a>{chip(link["status"])} '
                         f'<a href="{esc(href(link["to"]))}">{esc(nodes[link["to"]]["text"])}</a></p>')
        children = []
        for direction, link in sorted(incoming.get(ident, []), key=lambda e: order.get(e[1]["from"][0] if e[0] == "up" else e[1]["to"], 0)):
            relation = RELATIONS.get(link["relation"], link["relation"].replace("_", " "))
            status = chip(link["status"])
            word = f'<a class="o-rel{standing(link)}" href="{esc(href(link["id"]))}">{"↓ " if direction == "down" else "↑ "}{esc(relation)}</a>{status}'
            if direction == "down":
                children.append(f'<li class="o-link">{word}<ul>{branch(link["to"], depth + 1)}</ul></li>')
            elif len(link["from"]) > 1:
                inner = "".join(branch(s, depth + 1) for s in sorted(link["from"], key=order.get))
                children.append(f'<li class="o-link">{word} <span class="o-and">all of these together</span><ul class="o-joint">{inner}</ul></li>')
            else:
                children.append(f'<li class="o-link">{word}<ul>{branch(link["from"][0], depth + 1)}</ul></li>')
        if children:
            parts.append(f'<ul>{"".join(children)}</ul>')
        parts.append("</li>")
        return "".join(parts)
    return f'<ul class="rc-outline">{"".join(branch(r) for r in roots)}</ul>'
