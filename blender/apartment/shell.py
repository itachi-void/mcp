"""Architectural shell: every wall exists exactly once, with real thickness
(no double walls / z-fighting between rooms), one ceiling slab over the
whole interior (no light leaks), glazing and door proxies.
"""

from . import materials as mats
from .common import box, empty, group, link, ray_visibility


def _wall_ends(M):
    """For each h-wall end decide whether to extend by t/2: only at true
    corners (the end touches the *end* of a v-wall). T-junctions stay buried
    inside the crossing wall, so no coplanar faces appear inside rooms."""
    v_ends = set()
    for w in M["walls"]:
        if w["axis"] == "v":
            v_ends.add((round(w["at"], 3), round(w["from"], 3)))
            v_ends.add((round(w["at"], 3), round(w["to"], 3)))
    return v_ends


def _pieces(a0, a1, openings, height):
    """Split a wall run [a0, a1] into solid boxes around its openings.
    Returns (start, end, z0, z1) tuples along the wall axis."""
    out, cursor = [], a0
    for o0, o1, sill, head in sorted(openings):
        if o0 > cursor:
            out.append((cursor, o0, 0.0, height))
        if sill > 0.0:
            out.append((o0, o1, 0.0, sill))
        if head < height:
            out.append((o0, o1, head, height))
        cursor = o1
    if cursor < a1:
        out.append((cursor, a1, 0.0, height))
    return out


def build_shell(M, coll):
    S = M["shell"]
    H, T = S["wall_height"], S["wall_thickness"]
    plaster = mats.get("plaster")
    v_ends = _wall_ends(M)

    for i, w in enumerate(M["walls"]):
        a0, a1 = w["from"], w["to"]
        if w["axis"] == "h":
            if (round(a0, 3), round(w["at"], 3)) in v_ends:
                a0 -= T / 2
            if (round(a1, 3), round(w["at"], 3)) in v_ends:
                a1 += T / 2
        for j, (s, e, z0, z1) in enumerate(_pieces(a0, a1, w["openings"], H)):
            mid, length = (s + e) / 2, e - s
            if w["axis"] == "h":
                center, size = (mid, w["at"], (z0 + z1) / 2), (length, T, z1 - z0)
            else:
                center, size = (w["at"], mid, (z0 + z1) / 2), (T, length, z1 - z0)
            box(f"WALL_{i:02d}_{j}", coll, center, size, plaster, bevel=0.0)

    # One continuous slab over the interior footprint (terrace excluded).
    interior = [r for r in M["rooms"].values() if not r.get("outdoor")]
    x0 = min(r["origin"][0] for r in interior) - T / 2
    y0 = min(r["origin"][1] for r in interior) - T / 2
    x1 = max(r["origin"][0] + r["size"][0] for r in interior) + T / 2
    y1 = max(r["origin"][1] + r["size"][1] for r in interior) + T / 2
    st = S["slab_thickness"]
    box("CEILING_SLAB", coll, ((x0 + x1) / 2, (y0 + y1) / 2, H + st / 2), (x1 - x0, y1 - y0, st), plaster, bevel=0.0)
    box("FLOOR_SLAB", coll, ((x0 + x1) / 2, (y0 + y1) / 2, -st / 2 - 0.002), (x1 - x0, y1 - y0, st), mats.get("dark_stone"), bevel=0.0)

    _glazing(M, coll)
    _doors(M, coll)


def _glazing(M, coll):
    T = M["shell"]["wall_thickness"]
    frame = mats.get("black_metal")
    for g_i, g in enumerate(M["glazing"]):
        length = g["to"] - g["from"]
        h = g["head"] - g["sill"]
        zc = g["sill"] + h / 2
        n = max(1, round(length / g["mullion_every"]))
        step = length / n
        for k in range(n + 1):
            a = g["from"] + k * step
            c = (g["at"], a, zc) if g["axis"] == "v" else (a, g["at"], zc)
            s = (0.06, 0.05, h) if g["axis"] == "v" else (0.05, 0.06, h)
            box(f"MULLION_{g_i}_{k}", coll, c, s, frame, bevel=0.002)
        for z in (g["sill"] + 0.025, g["head"] - 0.025):
            c = (g["at"], (g["from"] + g["to"]) / 2, z)
            s = (0.07, length, 0.05)
            if g["axis"] == "h":
                c, s = (c[1], c[0], z), (length, 0.07, 0.05)
            box(f"TRANSOM_{g_i}_{z:.2f}", coll, c, s, frame, bevel=0.002)
        c = (g["at"], (g["from"] + g["to"]) / 2, zc)
        s = (0.012, length, h)
        if g["axis"] == "h":
            c, s = (c[1], c[0], zc), (length, 0.012, h)
        pane = box(f"GLASS_{g_i}", coll, c, s, mats.get("glass"), bevel=0.0)
        pane["is_glass"] = True


def _doors(M, coll):
    """Door02 (approved) at the front door, plus interior leaves.
    ASSET_DOOR02 is a size-exact proxy; apply_decisions.py swaps the real asset."""
    walnut = mats.get("walnut_dark")
    bronze = mats.get("bronze")

    d = M["assets"]["door02"]
    w, t, h = d["expected_dims"]
    g = group(d["proxy"], coll, (1.5, 0.0, 0.0))
    g["asset"] = "door02"
    g["expected_dims"] = d["expected_dims"]
    box("DOOR02_leaf", coll, (0.0, 0.0, h / 2), (w - 0.01, t, h - 0.01), walnut, parent=g)
    box("DOOR02_pull", coll, (0.38, 0.06, 1.05), (0.025, 0.04, 0.9), bronze, parent=g)

    # Interior doors stand open against the wall so the path stays clear.
    for name, hinge, rot, width in (("DOOR_bath", (1.5, 4.5, 0.0), 180.0, 0.8),
                                    ("DOOR_bedroom", (1.75, 10.0, 0.0), 90.0, 1.0)):
        leaf = group(name, coll, hinge, rot)
        box(f"{name}_leaf", coll, (width / 2, -0.03, 1.1), (width - 0.02, 0.045, 2.18), walnut, parent=leaf)
