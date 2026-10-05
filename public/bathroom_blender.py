"""
=======================================================================
  Luxury Greige Bathroom — Blender Python Scene Builder  v1
  Photorealistic port of src/components/bathroom/BathroomScene.tsx
  (the current, latest revision).

  Reproduces the reference photograph ref_bathroom.jpg:
    · long floating fluted-oak vanity with ONE generous vessel basin
      and a round backlit mirror + slim black pendant on the LEFT wall
    · freestanding oval tub centred on the BACK wall with a
      WALL-MOUNTED filler, in front of a wide, prominent lit niche
    · a narrow fluted decorative stone pillar on the back wall
    · a tall, nearly floor-to-ceiling lit NICHE COLUMN with 5 shelves
      tucked into the LEFT corner of the back wall
    · a black-framed glass rainfall shower in the back-RIGHT corner
    · a wall-hung toilet + framed botanical art on the RIGHT wall
    · large greige stone tile floor with a textured runner rug
    · warm greige microcement walls, matte-black accents, warm cove LED

  All materials use Principled BSDF with Sheen / Clearcoat / Transmission
  inputs where appropriate (mirrors Three.js meshPhysicalMaterial).

  COORDINATES — matches the Three.js scene convention:
    Three.js:  x = left(-)/right(+)   y = up        z = back(-)/front(+)
    Blender :  x = left(-)/right(+)   y = depth     z = up
    → position map  T(x,y,z)  = (x, z, y)
    → size map      TS(w,h,d) = (w, d, h)
=======================================================================
  HOW TO USE:
  1. Open Blender (3.x or 4.x)
  2. Go to the Scripting workspace
  3. Click "Open" and select this file  OR  paste the contents
  4. Press "Run Script" (or Alt+P)
  5. Press F12 to render
=======================================================================
"""

import bpy
import bmesh
from mathutils import Vector, Euler
import math
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────
TEXTURE_PATH = r"C:/Users/itachi/Downloads/3d"
USE_GPU      = True
SAMPLES      = 512
RESOLUTION   = (1920, 1080)

# ─── ROOM SHELL (identical footprint to the other rooms) ─────────────────────
W, D, H  = 6.6, 6.0, 2.8
BACK_Z   = -D / 2
RIGHT_X  =  W / 2
LEFT_X   = -W / 2


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials,
                  bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)


def link(obj):
    if obj.name not in bpy.context.collection.objects:
        bpy.context.collection.objects.link(obj)
    return obj


# ── Three.js → Blender coordinate helpers ────────────────────────────────────
def T(p):
    """Three.js position (x,y,z) → Blender (x,y,z)."""
    return (p[0], p[2], p[1])


def TS(s):
    """Three.js size (w=x, h=y, d=z) → Blender box scale (w, d, h)."""
    return (s[0], s[2], s[1])


def add_box(name, loc, size, mat=None):
    """Create a box primitive with precise world-space dimensions."""
    w, d, h = size
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()

    obj.location = loc
    obj.scale    = (w, d, h)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

    if mat:
        obj.data.materials.append(mat)
    return obj


def tbox(name, p, s, mat=None):
    """Three.js-space box → Blender box."""
    return add_box(name, T(p), TS(s), mat)


def add_cylinder(name, loc, radius, height, mat=None, verts=24,
                 rot=None, radius2=None):
    """Vertical (Z-up) cylinder by default; pass rot to reorient."""
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False,
        segments=verts, radius1=radius,
        radius2=radius if radius2 is None else radius2, depth=height
    )
    bm.to_mesh(mesh)
    bm.free()

    obj.location = loc
    if rot:
        obj.rotation_euler = Euler([math.radians(r) for r in rot])
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_sphere(name, loc, radius, mat=None, scale=(1, 1, 1), segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc,
                                         segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name  = name
    obj.scale = scale
    bpy.ops.object.shade_smooth()
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_torus(name, loc, major, minor, mat=None, scale=(1, 1, 1), rot=None):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=major,
                                     minor_radius=minor,
                                     major_segments=56, minor_segments=18)
    obj = bpy.context.active_object
    obj.name  = name
    obj.scale = scale
    if rot:
        obj.rotation_euler = Euler([math.radians(r) for r in rot])
    bpy.ops.object.shade_smooth()
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_plane(name, loc, size, rot=(0, 0, 0), mat=None):
    w, d = size
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bm.to_mesh(mesh)
    bm.free()

    obj.location       = loc
    obj.rotation_euler = Euler(rot)
    obj.scale          = (w, d, 1)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True, rotation=True)

    if mat:
        obj.data.materials.append(mat)
    return obj


def add_light(name, ltype, loc, energy, color=(1, 1, 1),
              size=1.0, size_y=None, rot=None, distance=None):
    bpy.ops.object.light_add(type=ltype, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.energy = energy
    obj.data.color  = color
    if ltype == 'AREA':
        obj.data.size   = size
        obj.data.size_y = size_y or size
    elif ltype in ('POINT', 'SPOT'):
        obj.data.shadow_soft_size = size
        if distance and hasattr(obj.data, 'cutoff_distance'):
            obj.data.use_custom_distance = True
            obj.data.cutoff_distance = distance
    if rot:
        obj.rotation_euler = Euler([math.radians(r) for r in rot])
    obj.data.use_shadow = True
    return obj


# ═══════════════════════════════════════════════════════════════════════════
#  MATERIALS — Full Principled BSDF PBR
# ═══════════════════════════════════════════════════════════════════════════

def pbr(name, color, roughness=0.5, metallic=0.0, ior=1.45,
        transmission=0.0, alpha=1.0,
        emission_color=None, emission_strength=0.0,
        clearcoat=0.0, clearcoat_roughness=0.10,
        sheen=0.0, sheen_roughness=0.50):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'OPAQUE' if alpha >= 1.0 else 'BLEND'
    if hasattr(mat, 'shadow_method'):
        mat.shadow_method = 'OPAQUE' if alpha >= 1.0 else 'HASHED'

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new('ShaderNodeOutputMaterial'); out.location  = (600, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (200, 0)

    r, g, b = color
    bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
    bsdf.inputs['Roughness'].default_value  = roughness
    bsdf.inputs['Metallic'].default_value   = metallic
    bsdf.inputs['IOR'].default_value        = ior
    bsdf.inputs['Alpha'].default_value      = alpha

    for key in ('Transmission Weight', 'Transmission'):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = transmission
            break

    if emission_color and emission_strength > 0:
        er, eg, eb = emission_color
        bsdf.inputs['Emission Color'].default_value    = (er, eg, eb, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength

    if clearcoat > 0:
        for cc_key in ('Coat Weight', 'Clearcoat'):
            if cc_key in bsdf.inputs:
                bsdf.inputs[cc_key].default_value = clearcoat
                break
        for ccr_key in ('Coat Roughness', 'Clearcoat Roughness'):
            if ccr_key in bsdf.inputs:
                bsdf.inputs[ccr_key].default_value = clearcoat_roughness
                break

    if sheen > 0:
        for sh_key in ('Sheen Weight', 'Sheen'):
            if sh_key in bsdf.inputs:
                bsdf.inputs[sh_key].default_value = sheen
                break
        if 'Sheen Roughness' in bsdf.inputs:
            bsdf.inputs['Sheen Roughness'].default_value = sheen_roughness

    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def _bsdf_of(mat):
    return next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def add_micro_bump(mat, scale=45.0, strength=0.06, detail=2.0):
    bsdf = _bsdf_of(mat)
    if not bsdf:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tc    = nodes.new('ShaderNodeTexCoord');  tc.location    = (-900, -260)
    noise = nodes.new('ShaderNodeTexNoise');  noise.location = (-620, -260)
    noise.inputs['Scale'].default_value = scale
    if 'Detail' in noise.inputs:
        noise.inputs['Detail'].default_value = detail
    bump  = nodes.new('ShaderNodeBump');      bump.location  = (-320, -260)
    bump.inputs['Strength'].default_value = strength
    links.new(tc.outputs['Object'],   noise.inputs['Vector'])
    links.new(noise.outputs['Fac'],   bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])


def procedural_wood(mat, c1, c2, stretch=(1.0, 14.0, 1.0), grain=8.0):
    bsdf = _bsdf_of(mat)
    if not bsdf:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tc   = nodes.new('ShaderNodeTexCoord');  tc.location  = (-1100, 200)
    mp   = nodes.new('ShaderNodeMapping');   mp.location  = (-900, 200)
    mp.inputs['Scale'].default_value = stretch
    nz   = nodes.new('ShaderNodeTexNoise');  nz.location  = (-680, 200)
    nz.inputs['Scale'].default_value = grain
    if 'Detail' in nz.inputs:
        nz.inputs['Detail'].default_value = 6.0
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-420, 200)
    ramp.color_ramp.elements[0].color = (c1[0], c1[1], c1[2], 1.0)
    ramp.color_ramp.elements[1].color = (c2[0], c2[1], c2[2], 1.0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.75
    links.new(tc.outputs['Object'],   mp.inputs['Vector'])
    links.new(mp.outputs['Vector'],   nz.inputs['Vector'])
    links.new(nz.outputs['Fac'],      ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'],  bsdf.inputs['Base Color'])
    add_micro_bump(mat, scale=grain * 3, strength=0.10)


def procedural_stone(mat, base, vein, scale=3.5):
    bsdf = _bsdf_of(mat)
    if not bsdf:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tc   = nodes.new('ShaderNodeTexCoord');  tc.location  = (-1100, 400)
    nz   = nodes.new('ShaderNodeTexNoise');  nz.location  = (-820, 400)
    nz.inputs['Scale'].default_value = scale
    if 'Detail' in nz.inputs:
        nz.inputs['Detail'].default_value = 8.0
    if 'Distortion' in nz.inputs:
        nz.inputs['Distortion'].default_value = 1.6
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-560, 400)
    ramp.color_ramp.elements[0].color = (base[0], base[1], base[2], 1.0)
    ramp.color_ramp.elements[1].color = (vein[0], vein[1], vein[2], 1.0)
    ramp.color_ramp.elements[0].position = 0.55
    ramp.color_ramp.elements[1].position = 0.72
    links.new(tc.outputs['Object'],   nz.inputs['Vector'])
    links.new(nz.outputs['Fac'],      ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'],  bsdf.inputs['Base Color'])
    add_micro_bump(mat, scale=60.0, strength=0.02)


# ── palette (mirrors the `C` object in BathroomScene.tsx) ────────────────────
def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def create_materials():
    M = {}

    # ── Structural ──
    M['wall'] = pbr('Wall_Microcement', hx('c4bcae'), roughness=0.88)
    add_micro_bump(M['wall'], scale=14.0, strength=0.03)
    M['ceiling'] = pbr('Ceiling', hx('cdc7bb'), roughness=1.0)

    M['floor'] = pbr('Floor_GreigeStone', hx('c6bfb2'), roughness=0.5,
                     ior=1.5, clearcoat=0.35, clearcoat_roughness=0.4)
    procedural_stone(M['floor'], hx('c6bfb2'), hx('b4ad9f'), scale=2.4)
    M['wet_floor'] = pbr('Floor_WetStone', hx('b4ad9f'), roughness=0.28,
                         ior=1.5, clearcoat=0.6, clearcoat_roughness=0.2)
    procedural_stone(M['wet_floor'], hx('b4ad9f'), hx('a49d8f'), scale=2.4)

    M['stone'] = pbr('Wall_Stone', hx('c9c1b4'), roughness=0.78)
    procedural_stone(M['stone'], hx('c9c1b4'), hx('b9b1a4'), scale=3.0)
    M['stone_dk'] = pbr('Niche_Stone', hx('a89e8d'), roughness=0.84)
    M['stone_back'] = pbr('Niche_Back', hx('9e9585'), roughness=0.87)
    M['stone_jamb'] = pbr('Niche_Jamb', hx('b4aa9a'), roughness=0.72)
    M['shelf'] = pbr('Niche_Shelf', hx('bfb8a8'), roughness=0.55)
    M['skirt'] = pbr('Skirting', hx('b3aa9a'), roughness=0.6)

    # ── Vanity — warm fluted oak + honed quartz ──
    M['vanity'] = pbr('Vanity_Oak', hx('a07d54'), roughness=0.5,
                      sheen=0.05, sheen_roughness=0.6)
    procedural_wood(M['vanity'], hx('8a6a45'), hx('b08a5e'),
                    stretch=(14.0, 1.0, 1.0), grain=7.0)
    M['vanity_dk'] = pbr('Vanity_Body', hx('6f5433'), roughness=0.55)
    M['teak'] = pbr('Teak_Caddy', hx('8a6a45'), roughness=0.55)
    M['counter'] = pbr('Quartz_Honed', hx('ddd6c9'), roughness=0.32,
                       ior=1.5, clearcoat=0.5, clearcoat_roughness=0.12)
    procedural_stone(M['counter'], hx('ddd6c9'), hx('c6bfb2'), scale=3.4)

    # ── Ceramics ──
    M['ceramic'] = pbr('Ceramic', hx('f3efe7'), roughness=0.18,
                       ior=1.5, clearcoat=0.7, clearcoat_roughness=0.1)
    M['ceramic_in'] = pbr('Ceramic_Interior', hx('eae4da'), roughness=0.2)
    M['cistern'] = pbr('Cistern', hx('d8d1c4'), roughness=0.6)

    # ── Matte-black fixtures ──
    M['black'] = pbr('Matte_Black', hx('141312'), roughness=0.5,
                     metallic=0.6)
    M['black_semi'] = pbr('Black_Semi', hx('1c1a18'), roughness=0.4,
                         metallic=0.5)
    M['flush'] = pbr('Flush_Plate', hx('e8e2d6'), roughness=0.4, metallic=0.2)

    # ── Mirror + glass ──
    M['mirror'] = pbr('Mirror', hx('aabccb'), roughness=0.02, metallic=0.98)
    M['glass'] = pbr('Shower_Glass', hx('cfe0ea'), roughness=0.02,
                     transmission=0.9, ior=1.5, alpha=0.16)

    # ── Textiles / decor ──
    M['rug'] = pbr('Rug', hx('b6ab98'), roughness=0.98,
                   sheen=0.6, sheen_roughness=0.6)
    add_micro_bump(M['rug'], scale=120.0, strength=0.05)
    M['rug_in'] = pbr('Rug_Inner', hx('bcb2a0'), roughness=0.99)
    M['towel'] = pbr('Towel', hx('9a9184'), roughness=0.9)
    M['plant'] = pbr('Plant', hx('3a5a34'), roughness=0.85)
    M['plant2'] = pbr('Plant_Sage', hx('5a6e4a'), roughness=0.85)
    M['vase'] = pbr('Vase_Black', hx('20201e'), roughness=0.3, clearcoat=0.4)
    M['art_frame'] = pbr('Art_Frame', hx('efe9dd'), roughness=0.5)
    M['art_face'] = pbr('Art_Face', hx('e7ded0'), roughness=0.7)
    M['paper'] = pbr('Toilet_Paper', hx('f4f1ea'), roughness=0.9)

    # ── Emissives ──
    M['led_warm'] = pbr('LED_Cove', hx('ffcf88'), roughness=1.0,
                        emission_color=hx('ffcf88'), emission_strength=7.5)
    M['led_niche'] = pbr('LED_Niche', hx('ffcf88'), roughness=1.0,
                         emission_color=hx('ffcf88'), emission_strength=8.2)
    M['led_under'] = pbr('LED_Under', hx('ffdca8'), roughness=1.0,
                         emission_color=hx('ffdca8'), emission_strength=3.4)
    M['led_recess'] = pbr('LED_Recessed', hx('ffe6c2'), roughness=0.0,
                          emission_color=hx('ffe6c2'), emission_strength=7.0)
    M['halo'] = pbr('Mirror_Halo', hx('ffdc9c'), roughness=1.0,
                    emission_color=hx('ffdc9c'), emission_strength=5.2)
    M['flame'] = pbr('Flame', hx('ffbe66'), roughness=1.0,
                     emission_color=hx('ffbe66'), emission_strength=10.0)
    M['recess_ring'] = pbr('Recess_Ring', hx('3a352f'), roughness=0.4, metallic=0.5)

    return M


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — ROOM SHELL
# ═══════════════════════════════════════════════════════════════════════════

def build_room(M):
    # greige stone tile floor
    add_plane('Floor', (0, 0, 0), (W, D), rot=(0, 0, 0), mat=M['floor'])
    # microcement walls (back / left / right)
    tbox('Wall_Back',  (0, H / 2, BACK_Z),  (W, H, 0.05), M['wall'])
    tbox('Wall_Left',  (LEFT_X, H / 2, 0),  (0.05, H, D), M['wall'])
    tbox('Wall_Right', (RIGHT_X, H / 2, 0), (0.05, H, D), M['wall'])
    # ceiling
    add_plane('Ceiling', (0, 0, H), (W, D), rot=(0, 0, 0), mat=M['ceiling'])

    # recessed tray + warm cove LED around the perimeter
    drop, bord = 0.16, 0.55
    cz = H - drop
    trays = [
        (0, cz + drop / 2, BACK_Z + bord / 2,        W, drop, bord),
        (0, cz + drop / 2, D / 2 - bord / 2,         W, drop, bord),
        (LEFT_X + bord / 2, cz + drop / 2, 0,        bord, drop, D - bord * 2),
        (RIGHT_X - bord / 2, cz + drop / 2, 0,       bord, drop, D - bord * 2),
    ]
    for i, (x, y, z, sx, sy, sz) in enumerate(trays):
        tbox(f'Tray_{i}', (x, y, z), (sx, sy, sz), M['ceiling'])
    tbox('Tray_Ceil', (0, cz, 0), (W - bord * 2, 0.04, D - bord * 2), M['ceiling'])

    coves = [
        (0, cz - 0.02, BACK_Z + bord - 0.02, W - bord, 0.03, 0.02),
        (0, cz - 0.02, D / 2 - bord + 0.02,  W - bord, 0.03, 0.02),
        (LEFT_X + bord - 0.02, cz - 0.02, 0, 0.02, 0.03, D - bord * 2),
        (RIGHT_X - bord + 0.02, cz - 0.02, 0, 0.02, 0.03, D - bord * 2),
    ]
    for i, (x, y, z, sx, sy, sz) in enumerate(coves):
        tbox(f'Cove_{i}', (x, y, z), (sx, sy, sz), M['led_warm'])

    # recessed downlights — physical warm spotlights, vertically aimed at floor.
    # Blender SPOT lamps point along local -Z by default, so no rotation is needed.
    for i, (x, z) in enumerate([(-1.6, -1.3), (1.5, -1.3), (-1.6, 1.2), (1.5, 1.2), (0, 0.2)]):
        add_cylinder(f'Rec_Ring_{i}', T((x, H - 0.02, z)), 0.07, 0.01,
                     M['recess_ring'], verts=24)
        add_cylinder(f'Rec_Disc_{i}', T((x, H - 0.03, z)), 0.05, 0.005,
                     M['led_recess'], verts=20)
        spot = add_light(f'Ceiling_Spot_{i}', 'SPOT', T((x, H - 0.055, z)),
                         260.0, color=hx('ffe2bc'), size=0.045, distance=4.1)
        spot.data.spot_size = math.radians(55)
        spot.data.spot_blend = 0.72

    # skirting
    tbox('Skirt_Back',  (0, 0.04, BACK_Z + 0.03), (W - 0.1, 0.08, 0.02), M['skirt'])
    tbox('Skirt_Left',  (LEFT_X + 0.03, 0.04, 0), (0.02, 0.08, D - 0.1), M['skirt'])
    tbox('Skirt_Right', (RIGHT_X - 0.03, 0.04, 0), (0.02, 0.08, D - 0.1), M['skirt'])


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — BACK WALL: fluted pillar + wide horizontal lit niche
# ═══════════════════════════════════════════════════════════════════════════

def build_feature_wall(M):
    z = BACK_Z + 0.03
    # narrow fluted decorative pillar (repositioned near -1.46)
    wWidth, cx, wy, wh = 0.28, -1.46, H / 2, H - 0.04
    slatW, gap = 0.032, 0.014
    n = int(wWidth / (slatW + gap))
    x0 = cx - (n - 1) * (slatW + gap) / 2
    tbox('Pillar_Back', (cx, wy, z), (wWidth, wh, 0.02), M['stone_dk'])
    for i in range(n):
        sx = x0 + i * (slatW + gap)
        add_cylinder(f'Pillar_Slat_{i}', T((sx, wy, z + 0.03)),
                     slatW / 2, wh, M['stone'], verts=12)

    # wide horizontal lit niche behind the tub — very prominent
    tbox('HNiche_Back', (0.2, 1.05, z + 0.05), (2.1, 0.40, 0.028), M['stone_dk'])
    tbox('HNiche_LED',  (0.2, 1.26, z + 0.065), (2.04, 0.018, 0.04), M['led_niche'])
    add_light('HNiche_Pt', 'POINT', T((0.2, 1.0, z + 0.55)), 3.2,
              color=hx('ffcf80'), size=0.08, distance=2.8)

    items = [(-0.62, '2b2723', 0.16), (-0.40, '8c7150', 0.20), (-0.18, '2b2723', 0.14),
             (0.10, 'c9bda6', 0.12), (0.55, '2b2723', 0.18)]
    for i, (nx, col, h) in enumerate(items):
        m = pbr(f'HNiche_Item_{i}', hx(col), roughness=0.35, clearcoat=0.4)
        add_cylinder(f'HNiche_Item_{i}', T((0.2 + nx, 0.97, z + 0.13)),
                     0.028, h, m, verts=16)
    build_vase(M, (0.65, 0.93, z + 0.13), 0.17, 0.048, sprigs=True, tag='HNiche')


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — FLOATING FLUTED VANITY + SINGLE VESSEL (left wall)
# ═══════════════════════════════════════════════════════════════════════════

def build_vanity(M):
    px = LEFT_X + 0.02
    d = 0.56
    cx = px + d / 2
    topY = 0.86
    bodyH = 0.5
    zC = 0.28
    length = 3.3
    nSlats = 20

    body_y = topY - 0.03 - bodyH / 2
    tbox('Vanity_Body', (cx, body_y, zC), (d, bodyH, length), M['vanity_dk'])

    for i in range(nSlats):
        fz = zC - length / 2 + 0.08 + (i * (length - 0.16)) / (nSlats - 1)
        # vertical fluted reeds on the room-facing (+X) front, spaced along the length
        add_cylinder(f'Vanity_Slat_{i}', T((cx + d / 2 - 0.006, body_y, fz)),
                     0.026, bodyH - 0.02, M['vanity'], verts=10)

    tbox('Vanity_Top', (cx, topY, zC), (d + 0.02, 0.05, length + 0.02), M['counter'])

    # warm LED underglow
    tbox('Vanity_LED', (cx, topY - 0.03 - bodyH - 0.005, zC),
         (d * 0.8, 0.012, length * 0.92), M['led_under'])
    add_light('Vanity_Under_Pt', 'POINT', T((cx, topY - bodyH - 0.1, zC)), 2.0,
              color=hx('ffcc88'), size=0.08, distance=2.2)

    # one generous vessel + wall-mounted faucet
    sz = 0.98
    build_vessel(M, cx, topY + 0.025, zC + sz)
    build_faucet(M, px + 0.03, topY + 0.30, zC + sz)

    # soap dispensers on a stone tray
    tbox('Soap_Tray', (cx + 0.05, topY + 0.04, zC + 1.24), (0.16, 0.02, 0.24), M['black_semi'])
    for i, o in enumerate([-0.05, 0.05]):
        col = hx('22201d') if i == 0 else hx('e9e3d8')
        m = pbr(f'Soap_{i}', col, roughness=0.4, metallic=0.1)
        add_cylinder(f'Soap_{i}', T((cx + 0.05 + o, topY + 0.10, zC + 1.24)),
                     0.028, 0.13, m, verts=18)

    # lit candle
    add_cylinder('Candle', T((cx - 0.02, topY + 0.06, zC + 0.58)), 0.05, 0.06,
                 pbr('Candle', hx('e7e0d4'), roughness=0.6), verts=20)
    add_sphere('Candle_Flame', T((cx - 0.02, topY + 0.13, zC + 0.58)), 0.014,
               M['flame'], segments=8, rings=8)
    add_light('Candle_Pt', 'POINT', T((cx - 0.02, topY + 0.14, zC + 0.58)), 0.7,
              color=hx('ffb455'), size=0.03, distance=0.8)

    # small vase + folded towel bundle
    build_vase(M, (cx - 0.06, topY + 0.03, zC - 0.02), 0.14, 0.04, sprigs=True, tag='Vanity')
    tbox('Vanity_Towel', (cx, topY - 0.03 - bodyH + 0.09, zC - length / 2 + 0.02),
         (d - 0.06, 0.16, 0.02), M['towel'])


def build_vessel(M, x, y, z):
    add_sphere('Vessel_Bowl', (x, z, y), 0.19, M['ceramic'],
               scale=(1, 0.72, 0.5), segments=32, rings=16)
    add_torus('Vessel_Rim', (x, z, y), 0.185, 0.012, M['ceramic'],
              scale=(1, 0.72, 1))


def build_faucet(M, x, y, z):
    tbox('Faucet_Plate', (x, y, z), (0.02, 0.12, 0.07), M['black'])
    # horizontal spout arm extends into the room (along +X) → rotate Z-up cyl about Y
    add_cylinder('Faucet_Arm', T((x + 0.14, y + 0.02, z)), 0.011, 0.28,
                 M['black'], verts=12, rot=(0, 90, 0))
    add_cylinder('Faucet_Spout', T((x + 0.28, y - 0.05, z)), 0.008, 0.06,
                 M['black'], verts=10)
    add_cylinder('Faucet_Lever', T((x - 0.02, y - 0.09, z)), 0.008, 0.09,
                 M['black'], verts=8, rot=(0, 90, 0))


def build_vase(M, p, h, r, sprigs=False, tag='V'):
    add_cylinder(f'{tag}_Vase', T(p), r, h, M['vase'], verts=20, radius2=r * 0.8)
    if sprigs:
        for j in range(5):
            sx = math.sin(j * 1.3) * 0.04
            sy = h * 0.5 + 0.1 + j * 0.02
            sz = math.cos(j * 1.3) * 0.04
            o = add_box(f'{tag}_Sprig_{j}', T((p[0] + sx, p[1] + sy, p[2] + sz)),
                        (0.005, 0.22, 0.02), M['plant'])
            o.rotation_euler = Euler((0, 0, (j - 2) * 0.25))


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — ROUND BACKLIT MIRROR + SLIM BLACK PENDANT (left wall)
# ═══════════════════════════════════════════════════════════════════════════

def build_mirror(M):
    px = LEFT_X + 0.04
    p = T((px, 1.55, 1.1))
    # halo backlight (faces into room, +X)
    add_cylinder('Mirror_Halo', (p[0] - 0.02, p[1], p[2]), 0.52, 0.005,
                 M['halo'], verts=64, rot=(0, 90, 0))
    add_torus('Mirror_Rim', (p[0], p[1], p[2]), 0.48, 0.012, M['black'],
              rot=(0, 90, 0))
    add_cylinder('Mirror_Glass', (p[0] + 0.005, p[1], p[2]), 0.475, 0.004,
                 M['mirror'], verts=64, rot=(0, 90, 0))
    add_light('Mirror_Pt', 'POINT', (p[0] + 0.4, p[1], p[2]), 2.0,
              color=hx('ffd68a'), size=0.08, distance=2.4)


def build_pendant(M, x=None, z=1.25):
    if x is None:
        x = LEFT_X + 0.55
    cord_h = H - 1.55
    add_cylinder('Pend_Mount', T((x, H - 0.02, z)), 0.02, 0.03, M['black'], verts=16)
    add_cylinder('Pend_Cord', T((x, (H + 1.55) / 2, z)), 0.003, cord_h, M['black'], verts=6)
    add_cylinder('Pend_Shade', T((x, 1.5, z)), 0.045, 0.26, M['black'], verts=24)
    add_sphere('Pend_Bulb', T((x, 1.38, z)), 0.04, M['flame'], segments=16, rings=16)
    add_light('Pend_Pt', 'POINT', T((x, 1.36, z)), 3.2, color=hx('ffbe66'),
              size=0.05, distance=2.6)


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — FREESTANDING OVAL TUB (centre, against feature wall)
# ═══════════════════════════════════════════════════════════════════════════

def build_bathtub(M):
    cx, cz = 0.15, BACK_Z + 0.95
    # outer flared oval shell (cone: bottom smaller)
    add_cylinder('Tub_Shell', (cx, cz, 0.32), 0.62, 0.62, M['ceramic'],
                 verts=48, radius2=0.52)
    # scale for oval (Z depth 0.66) — apply on the object
    for name in ('Tub_Shell',):
        o = bpy.data.objects[name]
        o.scale = (1, 0.66, 1)
    add_torus('Tub_Rim', (cx, cz, 0.63), 0.6, 0.03, M['ceramic'], scale=(1, 0.66, 1))
    # hollow interior
    inner = add_cylinder('Tub_Inner', (cx, cz, 0.4), 0.55, 0.46, M['ceramic_in'],
                         verts=48, radius2=0.44)
    inner.scale = (1, 0.66, 1)
    add_plane('Tub_Bottom', (cx, cz, 0.44), (0.88, 0.58), rot=(0, 0, 0),
              mat=M['ceramic_in'])

    # WALL-MOUNTED filler on the back wall (behind the tub)
    fz = BACK_Z + 0.04
    tbox('Tub_Escutcheon', (cx, 0.70, fz), (0.055, 0.10, 0.03), M['black'])
    add_cylinder('Tub_Spout_Arm', T((cx, 0.70, fz + 0.22)), 0.016, 0.44,
                 M['black'], verts=12, rot=(90, 0, 0))
    add_cylinder('Tub_Spout_Down', T((cx, 0.54, fz + 0.42)), 0.013, 0.30,
                 M['black'], verts=10)
    add_cylinder('Tub_Valve', T((cx + 0.10, 0.70, fz + 0.06)), 0.009, 0.09,
                 M['black'], verts=8, rot=(0, 90, 0))

    # teak bath caddy + soap bottle across the rim
    tbox('Tub_Caddy', (cx, 0.64, cz), (0.5, 0.02, 0.14), M['teak'])
    add_cylinder('Tub_Bottle', T((cx - 0.12, 0.74, cz)), 0.021, 0.09,
                 pbr('Tub_Bottle', hx('e9e3d8'), roughness=0.4), verts=12)


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — TALL LIT NICHE COLUMN (left corner of back wall, 5 shelves)
# ═══════════════════════════════════════════════════════════════════════════

def build_niche_column(M):
    x = LEFT_X + 0.62
    z = BACK_Z + 0.07
    unitW, unitH = 0.74, 2.54
    centerY = unitH / 2 + 0.07
    shelf_offsets = [-0.92, -0.45, 0.0, 0.46, 0.92]
    item_colors = ['2b2723', 'c9bda6', '7d6448', 'e6e0d4', '2b2723']

    def gp(lx, ly, lz):
        return (x + lx, centerY + ly, z + lz)

    tbox('NC_Back', gp(0, 0, -0.025), (unitW, unitH, 0.05), M['stone_back'])
    tbox('NC_JambL', gp(-unitW / 2 + 0.025, 0, 0.01), (0.05, unitH, 0.20), M['stone_jamb'])
    tbox('NC_JambR', gp(unitW / 2 - 0.025, 0, 0.01), (0.05, unitH, 0.20), M['stone_jamb'])
    tbox('NC_Top',  gp(0, unitH / 2 - 0.015, 0.01), (unitW - 0.06, 0.03, 0.20), M['stone_jamb'])
    tbox('NC_Base', gp(0, -unitH / 2 + 0.015, 0.01), (unitW - 0.06, 0.03, 0.20), M['stone_jamb'])

    for i, sy in enumerate(shelf_offsets):
        tbox(f'NC_Shelf_{i}', gp(0, sy, 0.01), (unitW - 0.08, 0.026, 0.19), M['shelf'])
        tbox(f'NC_ShelfLED_{i}', gp(0, sy + 0.115, 0.025),
             (unitW - 0.14, 0.015, 0.018), M['led_warm'])
        for j, ox in enumerate([-0.18, -0.03, 0.14]):
            if j == 2 and i % 2 == 0:
                build_vase(M, gp(ox, sy + 0.08, 0.04), 0.12, 0.028, tag=f'NC_{i}')
            else:
                col = item_colors[(i * 2 + j) % 5]
                m = pbr(f'NC_Item_{i}_{j}', hx(col), roughness=0.35, clearcoat=0.32)
                add_cylinder(f'NC_Item_{i}_{j}', T(gp(ox, sy + 0.09, 0.04)),
                             0.021, 0.10 + j * 0.025, m, verts=14)
    add_light('NC_Pt', 'POINT', T(gp(0, 0, 0.65)), 2.0, color=hx('ffcf80'),
              size=0.08, distance=2.2)


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — GLASS RAINFALL SHOWER (back-right corner)
# ═══════════════════════════════════════════════════════════════════════════

def build_shower(M):
    x0 = RIGHT_X - 0.04
    zBack = BACK_Z + 0.04
    sw, sd = 1.5, 1.35
    zC = zBack + sw / 2
    xC = x0 - sd / 2
    glassH = 2.2

    # wet-zone floor pan + linear drain
    add_plane('Shower_Pan', (xC, zC, 0.006), (sd, sw), rot=(0, 0, 0), mat=M['wet_floor'])
    tbox('Shower_Drain', (xC, 0.012, zBack + 0.2), (sd - 0.3, 0.006, 0.04), M['black_semi'])

    # fixed glass panel facing the room (front, along x) + black frame
    tbox('Glass_Front', (xC, glassH / 2, zC + sw / 2), (sd, glassH, 0.012), M['glass'])
    tbox('Frame_Top',  (xC, glassH, zC + sw / 2), (sd, 0.03, 0.03), M['black'])
    tbox('Frame_L',    (xC - sd / 2, glassH / 2, zC + sw / 2), (0.03, glassH, 0.03), M['black'])
    tbox('Frame_R',    (xC + sd / 2, glassH / 2, zC + sw / 2), (0.03, glassH, 0.03), M['black'])
    tbox('Door_Handle', (xC + sd / 2 - 0.12, glassH / 2, zC + sw / 2 + 0.03),
         (0.02, 0.28, 0.02), M['black'])

    # return glass panel (along z) + frame
    tbox('Glass_Return', (xC - sd / 2, glassH / 2, zC), (0.012, glassH, sw), M['glass'])
    tbox('Frame_Return', (xC - sd / 2, glassH, zC), (0.03, 0.03, sw), M['black'])

    # ceiling-mount rainfall head
    hx_ = xC
    add_cylinder('Rain_Mount', T((hx_, H - 0.02, zBack + 0.55)), 0.02, 0.04, M['black'], verts=12)
    add_cylinder('Rain_Arm', T((hx_, (H + 2.05) / 2, zBack + 0.55)), 0.014, H - 2.05, M['black'], verts=12)
    add_cylinder('Rain_Head', T((hx_, 2.02, zBack + 0.55)), 0.14, 0.03, M['black'], verts=28)

    # wall controls + slide bar + hand shower
    add_box('Shower_Ctrl', T((x0 - 0.02, 1.15, zBack + 0.2)), TS((0.02, 0.2, 0.09)), M['black'])
    add_cylinder('Slide_Bar', T((x0 - 0.02, 1.75, zBack + 0.2)), 0.01, 0.6, M['black'],
                 verts=10, rot=(90, 0, 0))
    add_cylinder('Hand_Arm', T((x0 - 0.06, 1.55, zBack + 0.2)), 0.012, 0.14, M['black'],
                 verts=12, rot=(0, 30, 0))
    add_cylinder('Hand_Head', T((x0 - 0.11, 1.47, zBack + 0.2)), 0.05, 0.02, M['black'],
                 verts=20, rot=(0, 90, 0))

    # small lit niche inside the shower on the back wall
    tbox('SNiche_Back', (xC + 0.1, 1.3, zBack + 0.05), (0.5, 0.34, 0.02), M['stone_dk'])
    tbox('SNiche_LED',  (xC + 0.1, 1.47, zBack + 0.06), (0.48, 0.015, 0.03), M['led_warm'])
    for i, ox in enumerate([-0.12, 0.02]):
        col = hx('2b2723') if i == 0 else hx('8c7150')
        m = pbr(f'SNiche_Item_{i}', col, roughness=0.35, clearcoat=0.35)
        add_cylinder(f'SNiche_Item_{i}', T((xC + 0.1 + ox, 1.22, zBack + 0.12)),
                     0.027, 0.15, m, verts=14)
    add_light('Shower_Pt', 'POINT', T((xC, 1.6, zC)), 2.2, color=hx('ffd08a'),
              size=0.08, distance=2.8)


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — WALL-HUNG TOILET + FRAMED BOTANICAL ART (right wall)
# ═══════════════════════════════════════════════════════════════════════════

def build_toilet(M):
    # Three authors the toilet in a group at (x,0,z) rotated -90° about Y, so
    # local (lx,ly,lz) → world (x - lz, ly, z + lx) and a local size (sx,sy,sz)
    # becomes world (sz, sy, sx). We bake that transform directly here.
    gx, gz = RIGHT_X - 0.04, 1.9

    def wp(lx, ly, lz):
        return (gx - lz, ly, gz + lx)

    def ws(sx, sy, sz):
        return (sz, sy, sx)

    # concealed cistern face flush against the right wall
    tbox('WC_Cistern', wp(0, 1.0, -0.14), ws(0.4, 0.5, 0.06), M['cistern'])
    tbox('WC_Flush',   wp(0, 1.12, -0.1), ws(0.11, 0.16, 0.01), M['flush'])

    # bowl (capsule approximated by a scaled sphere) projecting into the room
    add_sphere('WC_Bowl', wp(0, 0.42, 0.05), 0.19, M['ceramic'],
               scale=(0.7, 0.9, 0.85), segments=24, rings=16)
    tbox('WC_Seat', wp(0, 0.55, 0.06), ws(0.36, 0.04, 0.5), M['ceramic'])

    # wall-mounted toilet-paper holder (bar runs along the wall = world Z)
    tbox('WC_TP_Arm', wp(0, 0.75, 0.5 - 0.06), ws(0.02, 0.03, 0.1), M['black'])
    add_cylinder('WC_TP_Bar', wp(0, 0.75, 0.5), 0.012, 0.12, M['black'],
                 verts=10, rot=(90, 0, 0))
    add_cylinder('WC_TP_Roll', wp(0, 0.75, 0.5), 0.055, 0.1, M['paper'],
                 verts=20, rot=(90, 0, 0))


def build_wall_art(M):
    x, z = RIGHT_X - 0.04, 1.9
    tbox('Art_Frame', (x, 1.85, z), (0.02, 0.66, 0.5), M['art_frame'])
    tbox('Art_Face',  (x - 0.011, 1.85, z), (0.005, 0.58, 0.42), M['art_face'])
    stem = add_box('Art_Stem', T((x - 0.02, 1.69, z)), (0.004, 0.34, 0.006), M['plant2'])
    stem.rotation_euler = Euler((0.15, 0, 0))
    for i, h in enumerate([0.02, 0.08, 0.14, 0.2]):
        add_sphere(f'Art_Leaf_L{i}', T((x - 0.02, 1.69 + h, z - 0.05)), 0.03,
                   M['plant2'], scale=(0.6, 1, 1))
        add_sphere(f'Art_Leaf_R{i}', T((x - 0.02, 1.69 + h, z + 0.05)), 0.03,
                   M['plant2'], scale=(0.6, 1, 1))


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD — RUNNER RUG + FLOOR DECOR
# ═══════════════════════════════════════════════════════════════════════════

def build_rug(M):
    tbox('Rug', (-0.35, 0.012, 1.0), (0.92, 0.024, 2.7), M['rug'])
    tbox('Rug_Inner', (-0.35, 0.016, 1.0), (0.84, 0.024, 2.6), M['rug_in'])


def build_floor_decor(M):
    # tall dark vase + branches front-left of the tub
    add_cylinder('Decor_Vase', T((-0.9, 0.28, -0.9)), 0.12, 0.56, M['vase'],
                 verts=24, radius2=0.09)
    for j in range(4):
        bx = math.sin(j * 1.6) * 0.06
        by = 0.72 + j * 0.06
        bz = math.cos(j * 1.6) * 0.06
        o = add_box(f'Decor_Branch_{j}', T((-0.9 + bx, by, -0.9 + bz)),
                    (0.008, 0.4, 0.02), pbr(f'Branch_{j}', hx('5a4a38'), roughness=0.85))
        o.rotation_euler = Euler((0, 0, (j - 1.5) * 0.3))


# ═══════════════════════════════════════════════════════════════════════════
#  LIGHTING  (mirrors the Lighting() component)
# ═══════════════════════════════════════════════════════════════════════════

def setup_lighting():
    world = bpy.data.worlds['World']
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()
    bg  = wn.new('ShaderNodeBackground')
    out = wn.new('ShaderNodeOutputWorld')
    bg.inputs['Color'].default_value    = (*hx('ffe8d4'), 1.0)
    bg.inputs['Strength'].default_value = 0.22
    wl.new(bg.outputs['Background'], out.inputs['Surface'])

    # warm key from ceiling, shifted left toward the niche column (SUN)
    key = add_light('Key_Sun', 'SUN', T((-1.0, 4.2, 3.0)), 1.6, color=hx('ffe8cc'))
    key.rotation_euler = Euler([math.radians(a) for a in (52, 8, -18)])
    if hasattr(key.data, 'angle'):
        key.data.angle = math.radians(3.5)

    # warm fill from the camera side
    fill = add_light('Fill_Cam', 'SUN', T((-2, 2.5, 5)), 0.55, color=hx('ffd8b0'))
    fill.rotation_euler = Euler([math.radians(a) for a in (30, 0, -12)])

    # general warm bounce
    add_light('Bounce', 'POINT', T((-1.0, 2.2, 0.0)), 3.0, color=hx('ffdcae'),
              size=0.4, distance=8.0)
    # extra warm fill for the left-wall vanity area
    add_light('Vanity_Fill', 'POINT', T((-2.8, 1.8, 1.2)), 2.2, color=hx('ffcc88'),
              size=0.3, distance=4.0)


# ═══════════════════════════════════════════════════════════════════════════
#  CAMERA  (matches App.tsx bathroom framing: pos[-0.5,1.65,7.2] → tgt[-0.15,1.0,-0.6], fov 44)
# ═══════════════════════════════════════════════════════════════════════════

def setup_camera():
    tgt = bpy.data.objects.new('Cam_Target', None)
    link(tgt)
    tgt.location = T((-0.15, 1.0, -0.6))

    bpy.ops.object.camera_add(location=T((-0.5, 1.65, 7.2)))
    cam = bpy.context.active_object
    cam.name = 'Cam_Main'
    con = cam.constraints.new(type='TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis    = 'UP_Y'

    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y    = math.radians(44)
    cam.data.clip_start = 0.1
    cam.data.clip_end   = 60
    cam.data.dof.use_dof        = True
    cam.data.dof.focus_distance = 6.2
    cam.data.dof.aperture_fstop = 6.0
    bpy.context.scene.camera = cam


# ═══════════════════════════════════════════════════════════════════════════
#  RENDER SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

def setup_render():
    scene = bpy.context.scene
    scene.render.engine              = 'CYCLES'
    scene.cycles.device              = 'GPU' if USE_GPU else 'CPU'
    scene.cycles.samples             = SAMPLES
    scene.cycles.use_denoising       = True
    scene.cycles.denoiser            = 'OPENIMAGEDENOISE'
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x        = RESOLUTION[0]
    scene.render.resolution_y        = RESOLUTION[1]
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath            = '//bathroom_render.png'

    # AgX color management (with a matching Filmic look on Blender 3.6).
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except (TypeError, ValueError):
        scene.view_settings.view_transform = 'Filmic'
        scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.30
    scene.view_settings.gamma    = 1.02


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  Building Luxury Greige Bathroom Scene  v1")
    print("=" * 60)

    clear_scene()
    setup_render()

    print("Creating materials...")
    M = create_materials()

    print("Building room shell...")
    build_room(M)
    print("Building feature wall (fluted pillar + horizontal niche)...")
    build_feature_wall(M)
    print("Building floating fluted vanity + vessel...")
    build_vanity(M)
    print("Building round backlit mirror + pendant...")
    build_mirror(M)
    build_pendant(M)
    print("Building freestanding oval tub (wall-mounted filler)...")
    build_bathtub(M)
    print("Building tall lit niche column (5 shelves)...")
    build_niche_column(M)
    print("Building glass rainfall shower...")
    build_shower(M)
    print("Building wall-hung toilet + botanical art...")
    build_toilet(M)
    build_wall_art(M)
    print("Building rug + floor decor...")
    build_rug(M)
    build_floor_decor(M)

    print("Setting up global lighting...")
    setup_lighting()
    print("Setting up camera...")
    setup_camera()

    total_obj = len(bpy.data.objects)
    total_mat = len(bpy.data.materials)
    print(f"\n  Scene complete: {total_obj} objects | {total_mat} materials")
    print("  Press F12 to render  |  Output: //bathroom_render.png")
    print("=" * 60 + "\n")


main()
