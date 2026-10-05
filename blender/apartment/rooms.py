"""Room modules. Contract (unified-apartment-scene.md):

    build_<room>_module(M, offset, collection)

* `offset` is the room's south-west corner in apartment coordinates; all
  furniture below is authored relative to it.
* A module only *adds* objects to its own collection: no clear_scene(), no
  bpy.ops, no engine/world/resolution changes (those live in render_setup).
* Walls belong to the shell, never to a module, so neighbours never double up.
"""

import math

import bmesh
import bpy

from . import materials as mats
from .common import box, cylinder, empty, group, kelvin_to_linear, link, ring, sphere, upholster

# --- shared furniture -------------------------------------------------------


def _floor(M, name, coll, offset, size, mat_name):
    sx, sy = size
    box(f"{name}_floor", coll, (offset[0] + sx / 2, offset[1] + sy / 2, -0.005), (sx, sy, 0.01),
        mats.get(mat_name), bevel=0.0)


def _ceiling_lights(M, name, coll, offset, size, inset=0.5):
    """Same W/m2 and Kelvin in every room -> one exposure for the whole film."""
    L = M["lighting"]
    sx, sy = size
    lw, lh = max(0.4, sx - 2 * inset), max(0.4, sy - 2 * inset)
    light = bpy.data.lights.new(f"{name}_ceiling", "AREA")
    light.shape = "RECTANGLE"
    light.size, light.size_y = lw, lh
    light.energy = L["ceiling_w_per_m2"] * sx * sy
    light.color = kelvin_to_linear(L["kelvin"])
    light.spread = math.radians(120)
    obj = link(bpy.data.objects.new(f"{name}_ceiling", light), coll)
    obj.location = (offset[0] + sx / 2, offset[1] + sy / 2, M["shell"]["wall_height"] - 0.02)
    return obj


def _point(name, coll, loc, watts, radius=0.05, kelvin=2700):
    light = bpy.data.lights.new(name, "POINT")
    light.energy = watts
    light.shadow_soft_size = radius
    light.color = kelvin_to_linear(kelvin)
    obj = link(bpy.data.objects.new(name, light), coll)
    obj.location = loc
    return obj


def sofa(name, coll, loc, rot, length=2.8, depth=0.95, height=0.76, mat="boucle"):
    g = group(name, coll, loc, rot)
    m, metal = mats.get(mat), mats.get("bronze")
    # slim legs lift the body 12 cm: the contact shadow underneath sells the weight
    for sx in (-1, 1):
        for sy in (-1, 1):
            cylinder(f"{name}_leg{sx}{sy}", coll, (sx * (length / 2 - 0.16), sy * (depth / 2 - 0.14), 0.06),
                     0.016, 0.12, metal, segments=16, parent=g, bevel=0.002)
    upholster(box(f"{name}_seat", coll, (0, 0.05, 0.25), (length, depth - 0.1, 0.26), m, bevel=0.06, parent=g),
              puff=0.05, wrinkle=0.003)
    bh = height - 0.34  # back rises from the seat top to the full height
    upholster(box(f"{name}_back", coll, (0, -depth / 2 + 0.12, 0.34 + bh / 2), (length, 0.24, bh), m, bevel=0.09,
                  parent=g), puff=0.06, wrinkle=0.004)
    for s in (-1, 1):
        upholster(box(f"{name}_arm{s}", coll, (s * (length / 2 - 0.12), 0, 0.42), (0.24, depth, 0.32), m,
                      bevel=0.09, parent=g), puff=0.08, wrinkle=0.004, seed=s + 1)
    n = 3 if length > 2.2 else 2
    w = (length - 0.5) / n
    for i in range(n):
        x = -length / 2 + 0.25 + w * (i + 0.5)
        jitter = (0.012, -0.008, 0.006)[i % 3]  # hand-placed, never perfectly aligned
        c = box(f"{name}_cushion{i}", coll, (x + jitter, 0.08 + jitter, 0.45), (w - 0.02, depth - 0.35, 0.15), m,
                bevel=0.06, parent=g)
        c.rotation_euler = (math.radians(1.2 * (i - 1)), 0.0, math.radians(1.5 * (i - 1)))
        upholster(c, puff=0.22, wrinkle=0.007, seed=i)
        # back cushion leaning against the frame
        b = box(f"{name}_backcushion{i}", coll, (x - jitter, -depth / 2 + 0.33, 0.66), (w - 0.04, 0.18, 0.42), m,
                bevel=0.07, parent=g)
        b.rotation_euler = (math.radians(-12), 0.0, math.radians(-1.0 * (i - 1)))
        upholster(b, puff=0.25, wrinkle=0.008, seed=i + 3)
    return g


def chair(name, coll, loc, rot):
    g = group(name, coll, loc, rot)
    wood, fab = mats.get("walnut"), mats.get("fabric_dark")
    for sx in (-0.2, 0.2):
        for sy in (-0.2, 0.2):
            box(f"{name}_leg{sx}{sy}", coll, (sx, sy, 0.22), (0.035, 0.035, 0.44), wood, parent=g)
    upholster(box(f"{name}_seat", coll, (0, 0, 0.47), (0.46, 0.46, 0.07), fab, bevel=0.025, parent=g), puff=0.15, wrinkle=0.003)
    box(f"{name}_back", coll, (0, -0.21, 0.75), (0.44, 0.04, 0.5), wood, bevel=0.01, parent=g)
    return g


def stool(name, coll, loc):
    g = group(name, coll, loc)
    cylinder(f"{name}_post", coll, (0, 0, 0.36), 0.02, 0.72, mats.get("bronze"), parent=g)
    cylinder(f"{name}_base", coll, (0, 0, 0.01), 0.2, 0.02, mats.get("bronze"), parent=g)
    cylinder(f"{name}_seat", coll, (0, 0, 0.74), 0.19, 0.05, mats.get("fabric_dark"), parent=g, bevel=0.015)
    return g


def pendant(name, coll, loc, drop=0.9, kelvin=2700):
    g = group(name, coll, loc)
    cylinder(f"{name}_rod", coll, (0, 0, -drop / 2), 0.004, drop, mats.get("black_metal"), segments=8, parent=g)
    shade = cylinder(f"{name}_shade", coll, (0, 0, -drop - 0.08), 0.16, 0.16, mats.get("bronze"), parent=g)
    sphere(f"{name}_bulb", coll, (0, 0, -drop - 0.14), 0.035, mats.get("lamp_warm"), parent=g)
    p = _point(f"{name}_light", coll, (0, 0, -drop - 0.16), 25, 0.03, kelvin)
    p.parent = g
    return g


def table_lamp(name, coll, loc):
    g = group(name, coll, loc)
    cylinder(f"{name}_base", coll, (0, 0, 0.18), 0.05, 0.36, mats.get("ceramic"), parent=g)
    cylinder(f"{name}_shade", coll, (0, 0, 0.44), 0.16, 0.22, mats.get("linen"), parent=g, bevel=0.0)
    p = _point(f"{name}_light", coll, (0, 0, 0.42), 18, 0.06)
    p.parent = g
    return g


def plant(name, coll, loc, h=1.4):
    """Clipped cypress in a stone planter."""
    g = group(name, coll, loc)
    cylinder(f"{name}_pot", coll, (0, 0, 0.22), 0.22, 0.44, mats.get("terrace_stone"), parent=g)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.24, radius2=0.03, depth=h)
    me = bpy.data.meshes.new(f"{name}_foliage")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mats.get("plant"))
    for p in me.polygons:
        p.use_smooth = True
    leaf = link(bpy.data.objects.new(f"{name}_foliage", me), coll)
    leaf.location = (0, 0, 0.44 + h / 2)
    leaf.parent = g
    return g


# --- modules ----------------------------------------------------------------


def build_entry_module(M, offset, coll):
    ox, oy = offset
    _floor(M, "entry", coll, offset, M["rooms"]["entry"]["size"], M["rooms"]["entry"]["floor"])
    _ceiling_lights(M, "entry", coll, offset, M["rooms"]["entry"]["size"])
    # Walnut slat wall with a bronze-framed LED reveal: the opening close-up.
    for i in range(14):
        x = ox + 0.12 + i * 0.1
        box(f"entry_slat{i}", coll, (x, oy + 2.87, 1.45), (0.07, 0.04, 2.9), mats.get("walnut"), bevel=0.003)
    box("entry_led", coll, (ox + 0.8, oy + 2.85, 1.12), (1.38, 0.012, 0.012), mats.get("led_strip"), bevel=0.0)
    box("entry_led_trim", coll, (ox + 0.8, oy + 2.845, 1.10), (1.42, 0.02, 0.02), mats.get("bronze"))
    box("entry_console", coll, (ox + 0.8, oy + 2.7, 0.82), (1.2, 0.3, 0.05), mats.get("travertine"))
    for s in (-1, 1):
        box(f"entry_console_leg{s}", coll, (ox + 0.8 + s * 0.55, oy + 2.7, 0.4), (0.04, 0.26, 0.8), mats.get("bronze"))


def build_closet_module(M, offset, coll):
    _floor(M, "closet", coll, offset, M["rooms"]["closet"]["size"], M["rooms"]["closet"]["floor"])


def build_walkin_module(M, offset, coll):
    _floor(M, "walkin", coll, offset, M["rooms"]["walkin"]["size"], M["rooms"]["walkin"]["floor"])


def build_living_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["living"]
    _floor(M, "living", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "living", coll, offset, R["size"])
    box("living_rug", coll, (ox + 4.2, oy + 2.9, 0.006), (4.4, 3.2, 0.012), mats.get("rug"), bevel=0.0)

    # Approved decision: Freedom Sofa (proxy at true size, swapped by apply_decisions).
    a = M["assets"]["freedom_sofa"]
    fs = sofa(a["proxy"], coll, (ox + 4.0, oy + 0.85, 0.0), 0.0, *a["expected_dims"])
    fs["asset"] = "freedom_sofa"
    fs["expected_dims"] = a["expected_dims"]
    sofa("living_sofa_east", coll, (ox + 6.6, oy + 3.4, 0.0), 90.0, 2.4, 0.95)

    # Travertine coffee table: SHOT_01 ends on its top (match cut to the island).
    box("living_coffee_top", coll, (ox + 4.0, oy + 3.38, 0.36), (1.3, 0.8, 0.06), mats.get("travertine"), bevel=0.006)
    box("living_coffee_base", coll, (ox + 4.0, oy + 3.38, 0.165), (0.9, 0.45, 0.33), mats.get("travertine"))
    ring("living_bowl", coll, (ox + 3.75, oy + 3.3, 0.41), 0.11, 0.012, mats.get("bronze"))

    # TV / media wall on the corridor side: walnut + dark stone, credenza.
    box("living_tvwall_walnut", coll, (ox + 0.13, oy + 4.55, 1.45), (0.06, 2.5, 2.9), mats.get("walnut_dark"))
    box("living_tvwall_stone", coll, (ox + 0.17, oy + 4.55, 1.35), (0.03, 1.6, 0.9), mats.get("dark_stone"))
    box("living_credenza", coll, (ox + 0.4, oy + 4.55, 0.25), (0.45, 1.9, 0.5), mats.get("walnut"))
    box("living_tv_led", coll, (ox + 0.165, oy + 4.55, 0.55), (0.012, 2.2, 0.012), mats.get("led_strip"), bevel=0.0)

    plant("living_plant", coll, (ox + 7.6, oy + 5.4, 0.0))
    g = group("living_floorlamp", coll, (ox + 1.6, oy + 0.5, 0.0))
    cylinder("living_floorlamp_post", coll, (0, 0, 0.8), 0.012, 1.6, mats.get("bronze"), parent=g)
    cylinder("living_floorlamp_shade", coll, (0, 0, 1.6), 0.2, 0.28, mats.get("linen"), parent=g, bevel=0.0)
    _point("living_floorlamp_light", coll, (0, 0, 1.55), 30, 0.08).parent = g


def build_kitchen_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["kitchen"]
    _floor(M, "kitchen", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "kitchen", coll, offset, R["size"])
    # Island: travertine top on walnut, the SHOT_02 opening texture.
    box("kitchen_island_top", coll, (ox + 2.0, oy + 2.2, 0.9), (2.6, 1.0, 0.04), mats.get("travertine"), bevel=0.005)
    box("kitchen_island_base", coll, (ox + 2.0, oy + 2.25, 0.44), (2.5, 0.85, 0.88), mats.get("walnut"))
    for i, x in enumerate((1.2, 2.0, 2.8)):
        stool(f"kitchen_stool{i}", coll, (ox + x, oy + 1.35, 0.0))
    for i, x in enumerate((1.3, 2.7)):
        pendant(f"kitchen_pendant{i}", coll, (ox + x, oy + 2.2, M["shell"]["wall_height"]))
    # Back run + tall walnut cabinets on the north wall.
    box("kitchen_back_base", coll, (ox + 2.2, oy + 3.6, 0.44), (3.4, 0.6, 0.88), mats.get("walnut"))
    box("kitchen_back_top", coll, (ox + 2.2, oy + 3.6, 0.9), (3.4, 0.62, 0.04), mats.get("travertine"))
    box("kitchen_splash", coll, (ox + 2.2, oy + 3.88, 1.25), (3.4, 0.02, 0.66), mats.get("travertine"), bevel=0.0)
    box("kitchen_tall", coll, (ox + 0.55, oy + 3.6, 1.3), (0.7, 0.6, 2.6), mats.get("walnut_dark"))
    box("kitchen_shelf_led", coll, (ox + 2.6, oy + 3.85, 1.6), (2.4, 0.012, 0.012), mats.get("led_strip"), bevel=0.0)


def build_dining_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["dining"]
    _floor(M, "dining", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "dining", coll, offset, R["size"])
    box("dining_table_top", coll, (ox + 2.0, oy + 2.3, 0.74), (2.0, 1.0, 0.04), mats.get("walnut"), bevel=0.006)
    for s in (-1, 1):
        box(f"dining_table_leg{s}", coll, (ox + 2.0 + s * 0.7, oy + 2.3, 0.36), (0.08, 0.7, 0.72), mats.get("walnut_dark"))
    # Bronze ring: rack-focus anchor at F416.
    ring("dining_bronze_ring", coll, (ox + 2.0, oy + 2.3, 0.79), 0.13, 0.014, mats.get("bronze"))
    for i, x in enumerate((1.3, 2.0, 2.7)):
        chair(f"dining_chair_s{i}", coll, (ox + x, oy + 1.55, 0.0), 0.0)
        chair(f"dining_chair_n{i}", coll, (ox + x, oy + 3.05, 0.0), 180.0)
    pendant("dining_pendant", coll, (ox + 2.0, oy + 2.3, M["shell"]["wall_height"]), drop=1.1)

    # Approved decision: Rembrandt on the dining north wall.
    a = M["assets"]["rembrandt"]
    w, h = a["canvas"]
    g = group(a["proxy"], coll, (ox + 2.0, oy + 3.87, 1.6))
    g["asset"] = "rembrandt"
    box("REMBRANDT_frame", coll, (0, 0, 0), (w + 0.16, 0.05, h + 0.16), mats.get("bronze"), parent=g)
    canvas = box("REMBRANDT_canvas", coll, (0, -0.027, 0), (w, 0.004, h), mats.get("painting"), bevel=0.0, parent=g)
    canvas.data.uv_layers.new(name="UVMap")
    _point("REMBRANDT_picture_light", coll, (0, -0.35, h / 2 + 0.15), 12, 0.15).parent = g


def build_corridor_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["corridor"]
    _floor(M, "corridor", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "corridor", coll, offset, R["size"], inset=0.35)
    # Low LED washer along the floor line: the 'line of light' language.
    box("corridor_led", coll, (ox + 1.38, oy + 3.5, 0.05), (0.012, 6.0, 0.012), mats.get("led_strip"), bevel=0.0)


def build_bathroom_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["bathroom"]
    _floor(M, "bathroom", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "bathroom", coll, offset, R["size"])
    for name, c, s in (("bath_wall_w", (ox + 0.11, oy + 2.0, 1.2), (0.02, 3.8, 2.4)),
                       ("bath_wall_n", (ox + 1.5, oy + 3.89, 1.2), (2.8, 0.02, 2.4))):
        box(name, coll, c, s, mats.get("tile"), bevel=0.0)
    box("bath_vanity", coll, (ox + 0.4, oy + 2.0, 0.55), (0.5, 1.6, 0.35), mats.get("walnut"))
    box("bath_vanity_top", coll, (ox + 0.42, oy + 2.0, 0.74), (0.55, 1.62, 0.04), mats.get("travertine"))
    box("bath_basin", coll, (ox + 0.45, oy + 2.0, 0.8), (0.38, 0.5, 0.1), mats.get("ceramic"), bevel=0.03)
    box("bath_mirror", coll, (ox + 0.135, oy + 2.0, 1.55), (0.01, 1.2, 0.9), mats.get("mirror"), bevel=0.0)
    for s in (-1, 1):
        cylinder(f"bath_sconce{s}", coll, (ox + 0.18, oy + 2.0 + s * 0.75, 1.6), 0.03, 0.4, mats.get("lamp_warm"))
    tub = group("bath_tub", coll, (ox + 1.9, oy + 3.25, 0.0), 0.0)
    box("bath_tub_shell", coll, (0, 0, 0.29), (1.7, 0.78, 0.58), mats.get("ceramic"), bevel=0.15, parent=tub)
    box("bath_tub_water", coll, (0, 0, 0.5), (1.5, 0.6, 0.02), mats.get("glass"), bevel=0.0, parent=tub)
    cylinder("bath_tub_tap", coll, (ox + 2.85, oy + 3.25, 0.5), 0.015, 1.0, mats.get("bronze"))


def build_bedroom_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["bedroom"]
    _floor(M, "bedroom", coll, offset, R["size"], R["floor"])
    _ceiling_lights(M, "bedroom", coll, offset, R["size"])
    bx, by = ox + 4.25, oy + 3.85  # bed centre (headboard on the north wall)
    upholster(box("bed_headboard", coll, (bx, oy + 4.86, 1.0), (3.2, 0.08, 2.0), mats.get("fabric_dark"), bevel=0.03), puff=0.02, wrinkle=0.002)
    box("bed_frame", coll, (bx, by, 0.18), (1.9, 2.1, 0.3), mats.get("walnut_dark"))
    upholster(box("bed_mattress", coll, (bx, by, 0.43), (1.8, 2.0, 0.22), mats.get("linen"), bevel=0.05), puff=0.04, wrinkle=0.006)
    box("bed_throw", coll, (bx, by - 0.65, 0.55), (1.86, 0.6, 0.03), mats.get("fabric_dark"), bevel=0.012)
    for s in (-1, 1):
        upholster(box(f"bed_pillow{s}", coll, (bx + s * 0.42, oy + 4.6, 0.63), (0.7, 0.25, 0.18), mats.get("linen"), bevel=0.07), puff=0.3, wrinkle=0.008, seed=s + 1)
        box(f"bed_side{s}", coll, (bx + s * 1.5, oy + 4.6, 0.25), (0.5, 0.4, 0.5), mats.get("walnut"))
        table_lamp(f"bed_lamp{s}", coll, (bx + s * 1.5, oy + 4.6, 0.5))
    # Bedside light line at headboard height: match cut into the living LED line.
    box("bed_led_line", coll, (bx, oy + 4.81, 2.02), (3.2, 0.012, 0.012), mats.get("led_strip"), bevel=0.0)
    box("bed_wardrobe", coll, (ox + 0.4, oy + 2.4, 1.3), (0.6, 3.0, 2.6), mats.get("walnut"))
    box("bed_curtain", coll, (ox + 8.35, oy + 2.5, 1.45), (0.04, 3.4, 2.8), mats.get("linen"), bevel=0.0)


def build_terrace_module(M, offset, coll):
    ox, oy = offset
    R = M["rooms"]["terrace"]
    _floor(M, "terrace", coll, offset, R["size"], R["floor"])
    box("terrace_rail_glass", coll, (ox + R["size"][0] - 0.05, oy + R["size"][1] / 2, 0.55), (0.012, R["size"][1], 1.1), mats.get("glass"), bevel=0.0)
    box("terrace_rail_cap", coll, (ox + R["size"][0] - 0.05, oy + R["size"][1] / 2, 1.11), (0.05, R["size"][1], 0.03), mats.get("black_metal"))
    for i, y in enumerate((1.5, 5.0, 8.5)):
        plant(f"terrace_plant{i}", coll, (ox + 1.9, oy + y, 0.0), h=1.8)


MODULES = {
    "entry": build_entry_module,
    "closet": build_closet_module,
    "living": build_living_module,
    "kitchen": build_kitchen_module,
    "dining": build_dining_module,
    "corridor": build_corridor_module,
    "bathroom": build_bathroom_module,
    "walkin": build_walkin_module,
    "bedroom": build_bedroom_module,
    "terrace": build_terrace_module,
}
