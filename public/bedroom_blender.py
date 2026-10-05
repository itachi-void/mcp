"""
=======================================================================
  Master Bedroom — Blender Python Scene Builder
  Recreates BedroomScene.tsx in Blender/Cycles
=======================================================================
  HOW TO USE:
  1. Open Blender 3.x or 4.x
  2. Go to Scripting workspace (top menu → Scripting)
  3. Click "Open" and select this file  OR  paste contents into editor
  4. Adjust TEXTURE_PATH, USE_GPU, SAMPLES below as needed
  5. Press "Run Script" (▶ button or Alt+P)
  6. Wait for scene to build (watch the status bar)
  7. Press F12 to render (or Render → Render Image)

  COORDINATE SYSTEM:
    Three.js → Blender mapping used throughout:
      Three.js  x → Blender  X
      Three.js  z → Blender -Y   (back wall Three.js z=-3 → Blender Y=+3)
      Three.js  y → Blender  Z   (up)

  TEXTURES (optional — scene works fully procedurally):
    Place PBR texture sets in TEXTURE_PATH, e.g.
      C:/Users/itachi/Downloads/3d/wood/color.jpg
      C:/Users/itachi/Downloads/3d/marble/color.jpg
    The script references TEXTURE_PATH but uses solid PBR by default.

  GPU RENDER:
    Set USE_GPU = True to render on your GPU.
    Set USE_GPU = False to use CPU.
=======================================================================
"""

import bpy
import bmesh
from mathutils import Vector, Euler, Matrix
import math
import os

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
TEXTURE_PATH = r"C:/Users/itachi/Downloads/3d"
USE_GPU      = True
SAMPLES      = 512
RESOLUTION   = (1920, 1080)


# ─── SCENE CONSTANTS (match Three.js BedroomScene.tsx) ─────────────────────────
W    = 6.6   # room width  (Blender X)
D    = 6.0   # room depth  (Three.js Z; Blender Y)
H    = 2.8   # room height (Blender Z)

# Derived — Blender coordinates
BACK_Y  =  D / 2   # back wall       (Three.js z=-3 → Blender Y=+3)
FRONT_Y = -D / 2   # front/camera    (Three.js z=+3 → Blender Y=-3)
LEFT_X  = -W / 2   # left wall  X = -3.3
RIGHT_X =  W / 2   # right wall X = +3.3
FLOOR_Z =  0.0
CEIL_Z  =  H       # 2.8


# ═══════════════════════════════════════════════════════════════════════════════
#  COORDINATE HELPERS  (Three.js → Blender)
# ═══════════════════════════════════════════════════════════════════════════════

def p(tx, ty, tz):
    """Three.js position (x, y, z) → Blender (X, Y, Z)."""
    return (tx, -tz, ty)

def sz(tw, th, td):
    """Three.js box size (width, height, depth) → Blender (X, Y, Z) scale."""
    return (tw, td, th)

def hex_rgb(h):
    """Hex colour string (#rrggbb) → linear-space (r, g, b) tuple."""
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
    # sRGB → linear  (gamma 2.2 approx)
    return (r ** 2.2, g ** 2.2, b ** 2.2)


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def clear_scene():
    """Remove all objects, meshes, materials, lights and cameras."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials,
                  bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            block.remove(item)


def link(obj):
    """Link object to active collection if not already linked."""
    if obj.name not in bpy.context.collection.objects:
        bpy.context.collection.objects.link(obj)
    return obj


def apply_transforms(obj):
    """Apply scale (and optionally rotation) on an object."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)


def add_box(name, loc, size, mat=None, rot=(0, 0, 0)):
    """Create a UV-mapped box.  size = (X, Y, Z) in Blender space."""
    w, d, h = size
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    # mesh.calc_normals() removed in Blender 4.x — bmesh handles normals.

    obj.location       = loc
    obj.scale          = (w, d, h)
    obj.rotation_euler = Euler(rot)
    apply_transforms(obj)

    if mat:
        if len(obj.data.materials):
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    obj.cycles_visibility.shadow = True if hasattr(obj, 'cycles_visibility') else True
    return obj


def add_cylinder(name, loc, radius_top, radius_bot, height, mat=None,
                 verts=24, rot=(0, 0, 0)):
    """Create a cylinder/cone.  Default axis = Blender Z (up)."""
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False,
        segments=verts, radius1=radius_bot, radius2=radius_top, depth=height
    )
    bm.to_mesh(mesh)
    bm.free()

    obj.location       = loc
    obj.rotation_euler = Euler(rot)
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_torus(name, loc, major_r, minor_r, mat=None, rot=(0, 0, 0),
              major_seg=48, minor_seg=12):
    """Create a torus ring."""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_r, minor_radius=minor_r,
        major_segments=major_seg, minor_segments=minor_seg,
        location=loc, rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_plane(name, loc, size, rot=(0, 0, 0), mat=None):
    """Flat plane.  size = (X, Y) dimensions."""
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
    apply_transforms(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


# ─── Light helpers ─────────────────────────────────────────────────────────────

def add_point_light(name, loc, energy, color=(1, 1, 1), radius=0.05):
    """Emit a point light."""
    data = bpy.data.lights.new(name, 'POINT')
    data.energy = energy
    data.color  = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    link(obj)
    return obj


def add_spot_light(name, loc, target_loc, energy, color=(1, 1, 1),
                   spot_size=0.5, spot_blend=0.6):
    """Emit a spot light aimed at target_loc."""
    data = bpy.data.lights.new(name, 'SPOT')
    data.energy     = energy
    data.color      = color
    data.spot_size  = spot_size
    data.spot_blend = spot_blend
    data.shadow_soft_size = 0.05
    obj = bpy.data.objects.new(name, data)
    obj.location = loc

    # Point toward target
    direction = Vector(target_loc) - Vector(loc)
    rot_quat  = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()
    link(obj)
    return obj


def add_area_light(name, loc, energy, color=(1, 1, 1), size=(1.0, 1.0),
                   rot=(0, 0, 0)):
    """Create a rectangular area light (good for LED strips)."""
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.color  = color
    data.shape  = 'RECTANGLE'
    data.size   = size[0]
    data.size_y = size[1]
    obj = bpy.data.objects.new(name, data)
    obj.location       = loc
    obj.rotation_euler = Euler(rot)
    link(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
#  MATERIALS — Principled BSDF PBR
# ═══════════════════════════════════════════════════════════════════════════════

def make_pbr_material(name, color_hex, roughness=0.5, metallic=0.0,
                      transmission=0.0, ior=1.45, alpha=1.0,
                      emit_hex=None, emit_strength=0.0,
                      sheen=0.0, sheen_roughness=0.5, sheen_hex=None,
                      coat=0.0, coat_roughness=0.25):
    """
    Full Principled BSDF material.

    Parameters
    ----------
    color_hex      : '#rrggbb'  base colour
    roughness      : 0=mirror .. 1=fully diffuse
    metallic       : 0=dielectric .. 1=metal
    transmission   : 0=opaque .. 1=fully transparent (glass)
    ior            : Index of refraction (glass=1.5, water=1.33)
    alpha          : Opacity (1=solid; use with transmission for glass)
    emit_hex       : '#rrggbb' emission colour (None = no emission)
    emit_strength  : Emission wattage multiplier
    sheen          : Fabric micro-fibre sheen weight
    sheen_roughness: Sheen roughness
    sheen_hex      : Sheen colour hex
    coat           : Clear-coat weight (0-1)
    coat_roughness : Clear-coat roughness
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    lnks  = mat.node_tree.links
    nodes.clear()

    out  = nodes.new('ShaderNodeOutputMaterial'); out.location  = (700, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (200, 0)

    cr, cg, cb = hex_rgb(color_hex)
    bsdf.inputs['Base Color'].default_value = (cr, cg, cb, 1.0)
    bsdf.inputs['Roughness'].default_value  = roughness
    bsdf.inputs['Metallic'].default_value   = metallic
    bsdf.inputs['IOR'].default_value        = ior
    bsdf.inputs['Alpha'].default_value      = alpha

    # Transmission — key name changed in Blender 4.x
    for tkey in ('Transmission Weight', 'Transmission'):
        if tkey in bsdf.inputs:
            bsdf.inputs[tkey].default_value = transmission
            break

    # Emission
    if emit_hex and emit_strength > 0:
        er, eg, eb = hex_rgb(emit_hex)
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value    = (er, eg, eb, 1.0)
        elif 'Emission' in bsdf.inputs:
            bsdf.inputs['Emission'].default_value          = (er, eg, eb, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emit_strength

    # Sheen (fabric/velvet)
    if sheen > 0:
        for skey in ('Sheen Weight', 'Sheen'):
            if skey in bsdf.inputs:
                bsdf.inputs[skey].default_value = sheen
                break
        if 'Sheen Roughness' in bsdf.inputs:
            bsdf.inputs['Sheen Roughness'].default_value = sheen_roughness
        if sheen_hex and 'Sheen Tint' in bsdf.inputs:
            sr, sg, sb = hex_rgb(sheen_hex)
            bsdf.inputs['Sheen Tint'].default_value = (sr, sg, sb, 1.0)

    # Clear-coat
    if coat > 0:
        for ckey in ('Coat Weight', 'Clearcoat'):
            if ckey in bsdf.inputs:
                bsdf.inputs[ckey].default_value = coat
                break
        for crkey in ('Coat Roughness', 'Clearcoat Roughness'):
            if crkey in bsdf.inputs:
                bsdf.inputs[crkey].default_value = coat_roughness
                break

    # Transparency blend mode (pre-4.2 EEVEE)
    if alpha < 1.0 or transmission > 0:
        if hasattr(mat, 'blend_method'):
            mat.blend_method  = 'BLEND'
        if hasattr(mat, 'shadow_method'):
            mat.shadow_method = 'HASHED'

    lnks.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


# ─── Shared material library ───────────────────────────────────────────────────

def build_materials():
    M = {}
    # Room shell
    M['wall']       = make_pbr_material('wall',       '#c8c1b5', roughness=0.96)
    M['ceiling']    = make_pbr_material('ceiling',    '#d3d0ca', roughness=1.0)
    M['floor']      = make_pbr_material('floor',      '#c79a6a', roughness=0.55,
                                         coat=0.25, coat_roughness=0.35)
    M['baseboard']  = make_pbr_material('baseboard',  '#e0dcd4', roughness=0.5)
    M['window_frm'] = make_pbr_material('window_frm', '#eae7e1', roughness=0.4)
    M['window_gl']  = make_pbr_material('window_gl',  '#d7ecfa', roughness=0.08,
                                         transmission=0.8, ior=1.5, alpha=0.5,
                                         emit_hex='#e6f3ff', emit_strength=0.6)
    M['sheer']      = make_pbr_material('sheer',      '#f3efe8', roughness=0.9,
                                         alpha=0.5, transmission=0.2)

    # Accent wall
    M['walnut']     = make_pbr_material('walnut',     '#3a2513', roughness=0.6)
    M['walnut_sl']  = make_pbr_material('walnut_slat','#5a3d20', roughness=0.55)

    # Bed
    M['headboard']  = make_pbr_material('headboard',  '#8f8578', roughness=0.85,
                                         sheen=0.5, sheen_roughness=0.7, sheen_hex='#a09589')
    M['bed_base']   = make_pbr_material('bed_base',   '#6d6459', roughness=0.9,
                                         sheen=0.35, sheen_roughness=0.8, sheen_hex='#7a6e65')
    M['duvet']      = make_pbr_material('duvet',      '#e7e2d8', roughness=0.95,
                                         sheen=0.45, sheen_roughness=0.65, sheen_hex='#ede8de')
    M['sheet']      = make_pbr_material('sheet',      '#f2eee6', roughness=0.92)
    M['pillow']     = make_pbr_material('pillow',     '#efe9df', roughness=0.92,
                                         sheen=0.4, sheen_roughness=0.72)
    M['euro_pl']    = make_pbr_material('euro_pl',    '#c9b79a', roughness=0.9,
                                         sheen=0.5, sheen_roughness=0.68, sheen_hex='#c8b48e')
    M['throw']      = make_pbr_material('throw',      '#9a7d5a', roughness=0.9,
                                         sheen=0.55, sheen_roughness=0.6, sheen_hex='#b89060')
    M['lumbar']     = make_pbr_material('lumbar',     '#3e4a44', roughness=0.82,
                                         sheen=0.65, sheen_roughness=0.55, sheen_hex='#3e6045')
    M['duvet_cuff'] = make_pbr_material('duvet_cuff', '#f0ebe1', roughness=0.95,
                                         sheen=0.4, sheen_roughness=0.65)

    # Furniture
    M['brass']      = make_pbr_material('brass',      '#b0894f', roughness=0.25, metallic=0.92)
    M['brass_drk']  = make_pbr_material('brass_dark', '#7a6030', roughness=0.3,  metallic=0.88)
    M['marble']     = make_pbr_material('marble',     '#e8e5df', roughness=0.5,
                                         coat=0.6, coat_roughness=0.1)
    M['wood_warm']  = make_pbr_material('wood_warm',  '#7a5230', roughness=0.45)
    M['bench_uph']  = make_pbr_material('bench_uph',  '#c9b79a', roughness=0.85,
                                         sheen=0.4, sheen_roughness=0.7)

    # Wardrobe
    M['wardrobe_body']  = make_pbr_material('wardrobe_body',   '#c8c0b0', roughness=0.52)
    M['wardrobe_inner'] = make_pbr_material('wardrobe_inner',  '#a8a09a', roughness=0.7)
    M['wardrobe_shelf'] = make_pbr_material('wardrobe_shelf',  '#c8c0b4', roughness=0.45,
                                             coat=0.3, coat_roughness=0.2)
    M['cornice']        = make_pbr_material('cornice',         '#d2cab8', roughness=0.48,
                                             coat=0.35, coat_roughness=0.25)
    M['bz_glass']       = make_pbr_material('bronze_glass',    '#d4b870', roughness=0.03,
                                             transmission=0.86, ior=1.5, alpha=0.2)
    M['garment_cream']  = make_pbr_material('garment_cream',   '#c4b5a0', roughness=0.88,
                                             sheen=0.35, sheen_roughness=0.72)
    M['garment_black']  = make_pbr_material('garment_black',   '#2e2820', roughness=0.88,
                                             sheen=0.35, sheen_roughness=0.72)
    M['garment_white']  = make_pbr_material('garment_white',   '#e8e0d4', roughness=0.88,
                                             sheen=0.35, sheen_roughness=0.72)
    M['garment_brown']  = make_pbr_material('garment_brown',   '#6a5540', roughness=0.88,
                                             sheen=0.35, sheen_roughness=0.72)
    M['garment_beige']  = make_pbr_material('garment_beige',   '#b0a090', roughness=0.88,
                                             sheen=0.35, sheen_roughness=0.72)

    # Dressing station
    M['desk_top']   = make_pbr_material('desk_top',   '#d6cfca', roughness=0.35,
                                         coat=0.55, coat_roughness=0.12)
    M['mirror_gl']  = make_pbr_material('mirror_gl',  '#9ab5c8', roughness=0.012,
                                         metallic=0.97)
    M['mirror_halo']= make_pbr_material('mirror_halo','#fffbf0', roughness=1.0,
                                         emit_hex='#ffe090', emit_strength=4.5)
    M['vase']       = make_pbr_material('vase',        '#141210', roughness=0.12,
                                         metallic=0.08)
    M['plant_green']= make_pbr_material('plant_green', '#2e5226', roughness=0.9)
    M['perf_pink']  = make_pbr_material('perf_pink',   '#e4c8d2', roughness=0.04,
                                         transmission=0.74, ior=1.5, alpha=0.88)
    M['perf_teal']  = make_pbr_material('perf_teal',   '#ccddd8', roughness=0.04,
                                         transmission=0.74, ior=1.5, alpha=0.88)
    M['perf_gold']  = make_pbr_material('perf_gold',   '#f0deb8', roughness=0.04,
                                         transmission=0.74, ior=1.5, alpha=0.88)

    # Velvet stool
    M['stool_velvet']= make_pbr_material('stool_velvet','#d8d0c2', roughness=0.86,
                                          sheen=0.65, sheen_roughness=0.58, sheen_hex='#c5baa8')

    # Reading nook
    M['sage']       = make_pbr_material('sage',        '#6f7a6b', roughness=0.85,
                                         sheen=0.45, sheen_roughness=0.7)
    M['sage_throw'] = make_pbr_material('sage_throw',  '#9a7d5a', roughness=0.9,
                                         sheen=0.5, sheen_roughness=0.65)

    # Rug
    M['rug']        = make_pbr_material('rug',         '#b8ab96', roughness=0.98,
                                         sheen=0.7, sheen_roughness=0.5, sheen_hex='#c8bca6')
    M['rug_border'] = make_pbr_material('rug_border',  '#c8bda8', roughness=0.98)

    # LEDs
    M['led_warm']   = make_pbr_material('led_warm',    '#ffd090', roughness=1.0,
                                         emit_hex='#ffd090', emit_strength=4.0)
    M['led_hot']    = make_pbr_material('led_hot',     '#ffe4b0', roughness=1.0,
                                         emit_hex='#ffe4b0', emit_strength=3.5)
    M['led_under']  = make_pbr_material('led_under',   '#ffe0a6', roughness=1.0,
                                         emit_hex='#ffe0a6', emit_strength=2.5)
    M['led_cove']   = make_pbr_material('led_cove',    '#ffcf82', roughness=1.0,
                                         emit_hex='#ffcf82', emit_strength=5.5)
    M['led_sconce'] = make_pbr_material('led_sconce',  '#fff6e0', roughness=1.0,
                                         emit_hex='#ffd070', emit_strength=3.5)
    M['bulb_glow']  = make_pbr_material('bulb_glow',   '#fff0d0', roughness=1.0,
                                         emit_hex='#ffcf82', emit_strength=5.0)
    M['lamp_shade'] = make_pbr_material('lamp_shade',  '#f2e6cf', roughness=0.9,
                                         alpha=0.96,
                                         emit_hex='#ffcd7a', emit_strength=0.9)
    M['downlight']  = make_pbr_material('downlight',   '#ffffff', roughness=1.0,
                                         emit_hex='#fff2da', emit_strength=3.6)
    M['crystal']    = make_pbr_material('crystal',     '#ffffff', roughness=0.02,
                                         transmission=1.0, ior=1.5,
                                         emit_hex='#fff2d6', emit_strength=0.35)
    M['dl_ring']    = make_pbr_material('dl_ring',     '#3a352f', roughness=0.4,
                                         metallic=0.5)

    # Art / misc
    M['art_frame']  = make_pbr_material('art_frame',   '#2a2622', roughness=0.5,
                                         metallic=0.7)
    M['art_canvas'] = make_pbr_material('art_canvas',  '#d8c7a8', roughness=0.85)
    M['art_oc1']    = make_pbr_material('art_oc1',     '#a9743f', roughness=0.8)
    M['art_oc2']    = make_pbr_material('art_oc2',     '#5c6b57', roughness=0.8)
    M['art_oc3']    = make_pbr_material('art_oc3',     '#3a3733', roughness=0.8)

    # Shelf decor
    M['handbag']    = make_pbr_material('handbag',     '#c8b48a', roughness=0.55,
                                         coat=0.25)
    M['gold_torus'] = M['brass']
    M['book']       = make_pbr_material('book',        '#33413c', roughness=0.6)
    M['mug']        = make_pbr_material('mug',         '#efe9df', roughness=0.4)
    M['marble_top'] = M['marble']

    return M


# ═══════════════════════════════════════════════════════════════════════════════
#  SCENE PIECES
# ═══════════════════════════════════════════════════════════════════════════════

def build_room(M):
    """Floor, ceiling, walls, tray ceiling, cove LED, downlights, window, baseboards."""
    drop = 0.2;  bord = 0.7
    cz   = H - drop   # tray lower face Z = 2.6

    # ── Floor ──────────────────────────────────────────────────────────────────
    add_plane('floor', (0, 0, 0), (W, D), rot=(0, 0, 0), mat=M['floor'])

    # ── Ceiling ────────────────────────────────────────────────────────────────
    add_plane('ceiling', (0, 0, CEIL_Z), (W, D), mat=M['ceiling'])

    # ── Walls (back, left, right) ──────────────────────────────────────────────
    # back wall  (Three.js z=-3 → Blender Y=+3)
    add_box('wall_back',  (0,  BACK_Y,  H/2),    sz(W, H, 0.05), mat=M['wall'])
    # left wall
    add_box('wall_left',  (LEFT_X,  0, H/2),     sz(0.05, H, D), mat=M['wall'])
    # right wall
    add_box('wall_right', (RIGHT_X, 0, H/2),     sz(0.05, H, D), mat=M['wall'])

    # ── Tray ceiling border ────────────────────────────────────────────────────
    # back strip
    add_box('tray_back',  (0, BACK_Y - bord/2,   cz + drop/2), sz(W, drop, bord),       mat=M['ceiling'])
    # front strip
    add_box('tray_front', (0, FRONT_Y + bord/2,  cz + drop/2), sz(W, drop, bord),       mat=M['ceiling'])
    # left strip
    add_box('tray_left',  (LEFT_X  + bord/2, 0,  cz + drop/2), sz(bord, drop, D-bord*2), mat=M['ceiling'])
    # right strip
    add_box('tray_right', (RIGHT_X - bord/2, 0,  cz + drop/2), sz(bord, drop, D-bord*2), mat=M['ceiling'])
    # inner tray face
    add_box('tray_inner', (0, 0, cz), sz(W - bord*2, D - bord*2, 0.04), mat=M['ceiling'])

    # ── Cove LED strips (Three.js → Blender) ──────────────────────────────────
    # back cove strip: Three.js position [0, cz-0.02, -D/2+bord-0.03]
    #   → Blender (0, -(−D/2+bord−0.03), cz−0.02) = (0, D/2−bord+0.03, cz−0.02)
    add_box('cove_back',  (0,  BACK_Y - bord + 0.03,  cz - 0.02), sz(W - bord, 0.04, 0.02),  mat=M['led_cove'])
    add_box('cove_left',  (LEFT_X  + bord - 0.03,  0, cz - 0.02), sz(0.02, 0.04, D - bord*2), mat=M['led_cove'])
    add_box('cove_right', (RIGHT_X - bord + 0.03,  0, cz - 0.02), sz(0.02, 0.04, D - bord*2), mat=M['led_cove'])

    # Cove area light
    add_area_light('cove_led_light', (0, 0, cz + 0.05), energy=8,
                   color=hex_rgb('#ffcf82'), size=(W - bord*2, D - bord*2),
                   rot=(math.pi, 0, 0))   # face downward

    # ── 5 Recessed downlights ─────────────────────────────────────────────────
    # Three.js positions: [x, z] → Blender [x, -z, H-0.005]
    dl_positions = [(-1.7, -1.4), (1.7, -1.4), (-1.7, 1.2), (1.7, 1.2), (0, 1.6)]
    for i, (tx, tz) in enumerate(dl_positions):
        bx, by, bz = tx, -tz, CEIL_Z - 0.005
        # ring
        add_cylinder(f'dl_ring_{i}', (bx, by, bz - 0.01),
                     0.082, 0.082, 0.005, mat=M['dl_ring'], verts=28)
        # disc
        add_cylinder(f'dl_disc_{i}', (bx, by, bz - 0.015),
                     0.06, 0.06, 0.003, mat=M['downlight'], verts=24)

    # ── Window on right wall ───────────────────────────────────────────────────
    # Three.js: position [W/2-0.05, 1.5, 0.4] → Blender (W/2-0.05, -0.4, 1.5)
    build_window(M, bx=RIGHT_X - 0.05, by=-0.4, bz=1.5)

    # ── Baseboards ────────────────────────────────────────────────────────────
    # back wall: Three.js [0, 0.05, -D/2+0.06] → Blender (0, D/2-0.06, 0.05)
    add_box('base_back',  (0,      BACK_Y  - 0.06, 0.05), sz(W-0.1, 0.1, 0.02), mat=M['baseboard'])
    add_box('base_left',  (LEFT_X + 0.06, 0,       0.05), sz(0.02, 0.1, D-0.1), mat=M['baseboard'])


def build_window(M, bx, by, bz):
    """Right-wall window with frame, sky glass, muntin, sheer curtains, rod."""
    ww = 0.06;  wwid = 1.8;  wh = 1.35
    # outer frame
    add_box('win_frame',  (bx, by, bz), sz(ww+0.06, wh+0.14, wwid+0.14), mat=M['window_frm'])
    # sky glass
    add_box('win_glass',  (bx+0.02, by, bz), sz(0.02, wh, wwid),          mat=M['window_gl'])
    # muntin bar (vertical)
    add_box('win_muntin', (bx-0.01, by, bz), sz(0.05, wh, 0.03),           mat=M['window_frm'])
    # sheer curtain left
    add_box('curtain_l',  (bx-0.14, by - (wwid/2 + 0.18), bz+0.05),
            sz(0.03, wh+0.5, 0.5), mat=M['sheer'])
    # sheer curtain right
    add_box('curtain_r',  (bx-0.14, by + (wwid/2 + 0.18), bz+0.05),
            sz(0.03, wh+0.5, 0.5), mat=M['sheer'])
    # curtain rod — horizontal, along Y in Blender
    # Three.js [-0.16, wh/2+0.32, 0] → Blender (bx-0.16, by, bz + wh/2+0.32)
    rod_z = bz + wh/2 + 0.32
    rod = add_cylinder('curtain_rod', (bx-0.16, by, rod_z),
                        0.015, 0.015, wwid+0.7, mat=M['brass'], verts=12)
    # lay rod along Y axis: rotate 90° around X
    rod.rotation_euler = Euler((math.pi/2, 0, 0))


def build_accent_wall(M):
    """Walnut fluted back wall (headboard feature wall)."""
    # Three.js: z = -D/2+0.03 → Blender Y = D/2-0.03 = 2.97
    by   = BACK_Y - 0.03
    ww   = 3.0;   wh = H - 0.3;   wy = H/2 - 0.15
    slatW = 0.06; gap = 0.03
    n    = int(ww / (slatW + gap))
    x0   = -(n-1) * (slatW + gap) / 2

    # Backing panel
    add_box('accent_back', (0, by, wy), sz(ww, wh, 0.03), mat=M['walnut'])

    # Vertical fluted slats
    for i in range(n):
        sx = x0 + i * (slatW + gap)
        add_box(f'slat_{i}', (sx, by - 0.04, wy), sz(slatW, wh, 0.05), mat=M['walnut_sl'])


def build_bed(M):
    """King bed: headboard, platform, mattress, duvet, pillows, throw."""
    bw = 2.0;  bl = 2.15
    # Three.js: cz = -D/2+0.12 = -2.88  →  Blender by_head = D/2-0.12 = 2.88
    by_head = BACK_Y - 0.12
    cx = 0

    # Headboard: Three.js [cx, 1.15, cz] → Blender (cx, by_head, 1.15)
    add_box('headboard', (cx, by_head, 1.15), sz(bw+0.3, 1.3, 0.14), mat=M['headboard'])

    # Channel-tuft seams
    for sx in (-0.75, -0.25, 0.25, 0.75):
        add_box(f'seam_{sx}', (cx+sx, by_head - 0.075, 1.15),
                sz(0.012, 1.24, 0.02), mat=make_pbr_material(f'seam_m_{sx}', '#6f665b', roughness=0.9))

    # Platform base: Three.js center z = cz+0.18+bl/2 = -2.88+0.18+1.075 = -1.625
    #   → Blender Y = 1.625
    plat_y = 1.625
    add_box('bed_platform', (cx, plat_y, 0.22), sz(bw+0.24, 0.44, bl+0.2), mat=M['bed_base'])

    # Mattress
    add_box('mattress', (cx, plat_y, 0.45), sz(bw, 0.22, bl), mat=M['sheet'])

    # Fitted sheet top
    add_box('sheet', (cx, plat_y + 0.06, 0.555), sz(bw-0.02, 0.03, bl-0.1), mat=M['sheet'])

    # Duvet — lower 72% of bed
    add_box('duvet', (cx, plat_y + 0.62*bl*0.5 - 0.055, 0.56+0.06),
            sz(bw+0.06, 0.14, bl*0.72), mat=M['duvet'])

    # Folded duvet cuff (near head)
    # Three.js: [cx, mattY+0.12, cz+0.18+bl*0.30] → Blender: cz+0.18+bl*0.30 = -2.88+0.18+0.645 = -2.055 → Y=2.055
    add_box('duvet_cuff', (cx, 2.055, 0.56+0.12), sz(bw+0.06, 0.1, 0.34), mat=M['duvet_cuff'])

    # Caramel throw at foot
    # Three.js: bedFrontZ = cz+0.18+bl = -2.88+0.18+2.15 = -0.55 → Blender Y=0.55
    # throw at bedFrontZ - 0.28 → Blender Y = 0.83
    add_box('throw', (cx, 0.83, 0.56+0.02), sz(bw+0.04, 0.09, 0.6), mat=M['throw'])

    # Euro pillows (standing): Three.js z = cz+0.28 → Blender Y = 2.60
    for sx in (-0.55, 0.55):
        add_box(f'euro_{sx}', (cx+sx, 2.60, 0.55+0.24), sz(0.62, 0.5, 0.16), mat=M['euro_pl'])

    # Sleeping pillows: Three.js z = cz+0.5 → Blender Y = 2.38
    for sx in (-0.52, 0.52):
        add_box(f'slpil_{sx}', (cx+sx, 2.38, 0.55+0.14), sz(0.72, 0.22, 0.4), mat=M['pillow'])

    # Lumbar: Three.js z = cz+0.72 → Blender Y = 2.16
    add_box('lumbar', (cx, 2.16, 0.55+0.16), sz(1.0, 0.2, 0.28), mat=M['lumbar'])


def build_nightstand(M, tx):
    """Floating walnut nightstand with marble top, LED underglow, table lamp."""
    # Three.js: z = -D/2+0.42 = -2.58 → Blender Y = 2.58
    by  = 2.58
    bx  = tx
    topZ = 0.5
    w = 0.56;  d = 0.42;  bh = 0.24

    # Cabinet body
    add_box(f'ns_body_{tx}', (bx, by, topZ - bh/2), sz(w, bh, d), mat=M['wood_warm'])

    # Drawer reveal
    add_box(f'ns_drawer_{tx}', (bx, by - d/2 - 0.004, topZ - bh/2 + 0.02),
            sz(w*0.9, 0.006, 0.01),
            mat=make_pbr_material(f'ns_drawer_m_{tx}', '#4a3320', roughness=0.6))

    # Marble top
    add_box(f'ns_top_{tx}', (bx, by, topZ + 0.012), sz(w+0.02, 0.02, d+0.02), mat=M['marble'])

    # LED underglow strip
    add_box(f'ns_led_{tx}', (bx, by + 0.02, topZ - bh - 0.01), sz(w*0.85, 0.015, d*0.7),
            mat=M['led_under'])
    add_point_light(f'ns_pl_{tx}', (bx, by + 0.05, topZ - bh - 0.05),
                    energy=80, color=hex_rgb('#ffcc88'))

    # Table lamp
    build_table_lamp(M, bx=bx - 0.12, by=by - 0.02, bz=topZ + 0.022, label=str(tx).replace('-','n').replace('.','_'))

    # Book
    add_box(f'ns_book_{tx}', (bx + 0.17, by - 0.02, topZ + 0.05), sz(0.16, 0.045, 0.12), mat=M['book'])


def build_table_lamp(M, bx, by, bz, label=''):
    """Ceramic base + brass stem + linen shade table lamp."""
    # Brass base disc
    add_cylinder(f'lamp_base_{label}', (bx, by, bz + 0.015),
                 0.07, 0.08, 0.03, mat=M['brass'], verts=24)
    # Stem
    add_cylinder(f'lamp_stem_{label}', (bx, by, bz + 0.19),
                 0.012, 0.014, 0.32, mat=M['brass'], verts=16)
    # Linen shade (open cone)
    add_cylinder(f'lamp_shade_{label}', (bx, by, bz + 0.4),
                 0.11, 0.14, 0.2, mat=M['lamp_shade'], verts=32)
    # Glowing bulb
    add_cylinder(f'lamp_bulb_{label}', (bx, by, bz + 0.4),
                 0.04, 0.04, 0.05, mat=M['bulb_glow'], verts=16)
    # Point light
    add_point_light(f'lamp_light_{label}', (bx, by, bz + 0.4),
                    energy=200, color=hex_rgb('#ffbe66'))


def build_bench(M):
    """Upholstered bench at foot of bed with hairpin-style legs."""
    # Three.js: z = -D/2+0.12+0.18+2.15+0.28 = -2.27 → Blender Y = 2.27
    by = 2.27
    add_box('bench_seat', (0, by, 0.34), sz(1.5, 0.2, 0.5), mat=M['bench_uph'])

    leg_mat = make_pbr_material('bench_leg', '#b0894f', roughness=0.3, metallic=0.9)
    for lx, ly in [(-0.68, by-0.2), (0.68, by-0.2), (-0.68, by+0.2), (0.68, by+0.2)]:
        add_cylinder(f'bench_leg_{lx}_{ly}', (lx, ly, 0.12),
                     0.022, 0.03, 0.24, mat=leg_mat, verts=12)


def build_wardrobe(M):
    """
    Full wardrobe system on left wall — champagne body, glass doors,
    dressing station, open shelving, velvet stool.
    """
    px   = LEFT_X + 0.31    # Three.js px = -W/2+0.31 = -2.99
    d    = 0.62             # depth
    uh   = 2.55             # unit height
    # Three.js Z ranges → Blender Y ranges (negate)
    # z0=-0.55 → by_end=0.55;  z5=2.87 → by_start=-2.87
    z0=0.55; z1=z0-0.72; z2=z1-0.72; z3=z2-0.74; z4=z3-0.72; z5=z4-0.52
    # (z0..z5 are Blender Y values, so z5 < z4 < ... < z0)
    zC = (z0 + z5) / 2    # = (0.55 + (-2.87))/2 = -1.16

    def sc(a, b): return (a + b) / 2
    def sw(a, b): return abs(a - b)

    front_x = px + d/2   # front face X of wardrobe

    # ── Carcass ────────────────────────────────────────────────────────────────
    # Back panel (thin slab at back of wardrobe interior)
    add_box('wd_back', (px - d/2 + 0.02, zC, uh/2),
            (0.04, sw(z0, z5), uh), mat=M['wardrobe_body'])

    # Top cornice
    add_box('wd_cornice', (px + 0.01, zC, uh + 0.034),
            (d + 0.05, sw(z0, z5) + 0.06, 0.072), mat=M['cornice'])

    # Base plinth
    add_box('wd_plinth', (px, zC, 0.042),
            (d + 0.02, sw(z0, z5) + 0.02, 0.084), mat=M['wardrobe_body'])

    # LED cove on top cornice (faces toward room, +X direction)
    add_box('wd_cove_led', (front_x + 0.018, zC, uh + 0.005),
            (0.012, sw(z0, z5) * 0.92, 0.014), mat=M['led_warm'])
    add_point_light('wd_cove_pl', (front_x + 0.14, zC, uh + 0.01),
                    energy=60, color=hex_rgb('#ffcf70'))

    # Vertical dividers at section boundaries
    for zy in [z1, z2, z3, z4]:
        add_box(f'wd_div_{zy:.2f}', (px, zy, uh/2),
                (d - 0.02, 0.022, uh - 0.02), mat=M['wardrobe_body'])
    # End panels
    add_box('wd_end_top', (px, z0 - 0.012, uh/2), (d, 0.024, uh), mat=M['wardrobe_body'])
    add_box('wd_end_bot', (px - 0.04, z5 + 0.012, uh/2), (d - 0.1, 0.026, uh), mat=M['wardrobe_body'])

    # ── Glass wardrobe helper ──────────────────────────────────────────────────
    def glass_door(label, by_sec, wy_sec):
        # Brass outer frame
        add_box(f'gd_frame_{label}', (front_x - 0.004, by_sec, uh/2),
                (0.024, wy_sec - 0.01, uh - 0.02), mat=M['brass_drk'])
        # Bronze glass panel
        add_box(f'gd_glass_{label}', (front_x + 0.007, by_sec, uh/2),
                (0.007, wy_sec - 0.08, uh - 0.1), mat=M['bz_glass'])
        # Brass bar pull
        add_box(f'gd_pull_{label}',
                (front_x + 0.013, by_sec + wy_sec/2 - 0.09, uh*0.5),
                (0.009, 0.014, 0.18), mat=M['brass'])

    # ── Wardrobe interior helper ───────────────────────────────────────────────
    garment_colors = {
        'cream': '#c4b5a0', 'black': '#2e2820', 'white': '#e8e0d4',
        'brown': '#6a5540', 'beige': '#b0a090', 'dkbeige': '#d8cfc0',
        'charcoal': '#1a1612', 'taupe': '#c8b8a0', 'warmbrn': '#8a7860',
        'grey': '#b0a898', 'ltbrown': '#d4c8b8', 'dk': '#786858',
    }

    def wardrobe_interior(label, y_from, y_to, garment_list):
        """
        garment_list: list of (hex_color, length) tuples
        y_from, y_to: Blender Y extents (y_to < y_from, e.g. -2.87 to -2.15)
        """
        by_sec  = sc(y_from, y_to)
        wy_sec  = sw(y_from, y_to)
        rod_z   = uh - 0.62

        # Interior back panel
        add_box(f'wi_back_{label}', (px - d/2 + 0.04, by_sec, uh/2),
                (0.018, wy_sec - 0.04, uh - 0.04), mat=M['wardrobe_inner'])

        # Upper shelf
        add_box(f'wi_ushelf_{label}', (px - 0.02, by_sec, uh - 0.26),
                (d - 0.06, wy_sec - 0.05, 0.022), mat=M['wardrobe_shelf'])

        # Folded items on upper shelf
        for fi in range(2):
            fc = '#e8e2d8' if fi == 0 else '#c0b8a8'
            add_box(f'wi_fold_{label}_{fi}',
                    (px - 0.06, y_from - 0.12 - fi*0.26 if y_from > y_to else y_from + 0.12 + fi*0.26, uh - 0.15),
                    (d*0.55, 0.22, 0.12),
                    mat=make_pbr_material(f'wi_fold_m_{label}_{fi}', fc, roughness=0.88))

        # Hanging rod (horizontal, along Y)
        rod = add_cylinder(f'wi_rod_{label}', (px - 0.05, by_sec, rod_z),
                            0.008, 0.008, wy_sec - 0.1, mat=M['brass'], verts=10)
        rod.rotation_euler = Euler((math.pi/2, 0, 0))

        # Hanging garments
        n_garments = len(garment_list)
        step = (wy_sec - 0.18) / max(n_garments - 1, 1)
        for hi, (gcol, glen) in enumerate(garment_list):
            gz = y_from - 0.09 - hi*step if y_from > y_to else y_from + 0.09 + hi*step
            gmat = make_pbr_material(f'garm_{label}_{hi}', gcol, roughness=0.88,
                                     sheen=0.35, sheen_roughness=0.72)
            # Hanger arc (torus)
            hanger = add_torus(f'wi_hanger_{label}_{hi}',
                               (px - 0.05, gz, rod_z),
                               major_r=0.09, minor_r=0.005,
                               rot=(0, 0, math.pi/2), mat=M['brass'])
            # Garment body
            gobj = add_box(f'wi_garm_{label}_{hi}',
                           (px - 0.05, gz, rod_z - glen/2 - 0.01),
                           (0.016, 0.36, glen), mat=gmat)

        # 3 lower drawers
        for di, dy in enumerate([0.12, 0.31, 0.50]):
            add_box(f'wi_drw_{label}_{di}', (px - 0.01, by_sec, dy),
                    (d - 0.06, wy_sec - 0.05, 0.17), mat=M['wardrobe_shelf'])
            add_box(f'wi_pull_{label}_{di}', (front_x - 0.03, by_sec, dy),
                    (0.01, 0.2, 0.007), mat=M['brass'])

        # Top LED strip
        add_box(f'wi_led_top_{label}', (px - 0.05, by_sec, uh - 0.13),
                (0.013, wy_sec - 0.09, 0.017), mat=M['led_cove'])
        add_point_light(f'wi_pl_top_{label}', (px - 0.05, by_sec, uh - 0.3),
                        energy=300, color=hex_rgb('#ffcf78'))

        # Floor LED wash
        add_box(f'wi_led_fl_{label}', (px - d/2 + 0.07, by_sec, 0.07),
                (0.01, wy_sec - 0.12, 0.012), mat=M['led_warm'])
        add_point_light(f'wi_pl_fl_{label}', (px - 0.1, by_sec, 0.2),
                        energy=130, color=hex_rgb('#ffcf78'))

    # ── GLASS WARDROBE 1 ──────────────────────────────────────────────────────
    glass_door('gw1', sc(z0, z1), sw(z0, z1))
    wardrobe_interior('gw1', z0, z1, [
        ('#c4b5a0', 0.44), ('#2e2820', 0.44), ('#e8e0d4', 0.58),
        ('#6a5540', 0.44), ('#b0a090', 0.58),
    ])

    # ── GLASS WARDROBE 2 ──────────────────────────────────────────────────────
    glass_door('gw2', sc(z1, z2), sw(z1, z2))
    wardrobe_interior('gw2', z1, z2, [
        ('#d8cfc0', 0.58), ('#1a1612', 0.44), ('#c8b8a0', 0.52), ('#8a7860', 0.48),
    ])

    # ── DRESSING STATION ──────────────────────────────────────────────────────
    ds_cen = sc(z2, z3)   # Blender Y center of dressing station
    ds_w   = sw(z2, z3)

    # 9 walnut fluted slats on back of dressing station
    for fi in range(9):
        fz = z2 - 0.04 - fi * (ds_w - 0.08) / 8  # step through Y range
        add_box(f'ds_slat_{fi}', (px - d/2 + 0.06, fz, uh*0.55),
                (0.030, 0.036, uh*0.88), mat=M['walnut_sl'])

    # Dressing chest base (2 drawers)
    add_box('ds_chest', (px - 0.01, ds_cen, 0.40), sz(d-0.05, 0.76, ds_w-0.04), mat=M['cornice'])
    for di, dy in [(-0.17, 0.23), (0.17, 0.57)]:
        add_box(f'ds_pull_{di}', (front_x + 0.01, ds_cen, 0.40 + di),
                (0.012, 0.24, 0.009), mat=M['brass'])

    # Polished desk top
    add_box('ds_top', (px + 0.01, ds_cen, 0.80), sz(d, 0.04, ds_w), mat=M['desk_top'])

    # Brass cosmetics tray
    add_box('ds_tray', (px + 0.06, ds_cen - 0.2, 0.824), sz(0.24, 0.018, 0.22), mat=M['brass'])

    # 3 perfume bottles (glass)
    perf_mats = [M['perf_pink'], M['perf_teal'], M['perf_gold']]
    perf_heights = [0.12, 0.14, 0.10]
    for pi_, (pm, ph) in enumerate(zip(perf_mats, perf_heights)):
        add_box(f'ds_perf_{pi_}',
                (px + 0.06 - 0.07 + pi_*0.07, ds_cen - 0.2, 0.824 + ph/2),
                (0.038, 0.038, ph), mat=pm)

    # Dark vase + plant
    add_cylinder('ds_vase', (px + 0.04, ds_cen + 0.22, 0.98),
                 0.038, 0.048, 0.22, mat=M['vase'], verts=14)
    for pi_ in range(3):
        px2 = px + 0.04 + math.sin(pi_*2.1)*0.04
        py2 = ds_cen + 0.22 + math.cos(pi_*2.1)*0.04
        add_cylinder(f'ds_plant_{pi_}', (px2, py2, 1.08),
                     0.028, 0.028, 0.05, mat=M['plant_green'], verts=6)

    # LED top strip
    add_box('ds_led_top', (px - d/2 + 0.07, ds_cen, uh*0.97),
            (0.012, ds_w - 0.08, 0.016), mat=M['led_warm'])
    add_point_light('ds_pl_top', (px - 0.01, ds_cen, uh*0.88),
                    energy=230, color=hex_rgb('#ffdd90'))

    # Floor uplighter
    add_box('ds_led_fl', (px - d/2 + 0.07, ds_cen, 0.07),
            (0.01, ds_w - 0.1, 0.012), mat=M['led_warm'])
    add_point_light('ds_pl_fl', (px - 0.04, ds_cen, 0.22),
                    energy=160, color=hex_rgb('#ffcf70'))

    # Oval LED mirror — faces +X toward room
    # Three.js: position [front-0.016, 1.48, sc(z2,z3)], rotation [0, π/2, 0]
    # Blender: (front_x - 0.016, ds_cen, 1.48)
    # The torus is scaled to oval: scale [1, 1.42, 1] in Three.js (X-Z plane oval)
    # In Blender: oval in Y-Z plane → we apply scale Y=1.42
    mir_x = front_x - 0.016;  mir_y = ds_cen;  mir_z = 1.48
    # Outer brass frame torus
    mir_frame = add_torus('mir_frame', (mir_x, mir_y, mir_z),
                          major_r=0.30, minor_r=0.025, mat=M['brass'],
                          rot=(math.pi/2, 0, 0))
    mir_frame.scale = (1.0, 1.0, 1.42)   # oval stretch in Z
    apply_transforms(mir_frame)

    # Halo glow ring (inner)
    mir_halo = add_torus('mir_halo', (mir_x, mir_y, mir_z),
                         major_r=0.276, minor_r=0.015, mat=M['mirror_halo'],
                         rot=(math.pi/2, 0, 0))
    mir_halo.scale = (1.0, 1.0, 1.42)
    apply_transforms(mir_halo)

    # Mirror glass disc
    add_plane('mir_glass', (mir_x, mir_y, mir_z), (0.516, 0.516*1.42),
              rot=(0, math.pi/2, 0), mat=M['mirror_gl'])

    # Mirror point light (warm halo)
    add_point_light('mir_light', (mir_x + 0.18, mir_y, mir_z),
                    energy=145, color=hex_rgb('#ffd060'))

    # ── GLASS WARDROBE 3 ──────────────────────────────────────────────────────
    glass_door('gw3', sc(z3, z4), sw(z3, z4))
    wardrobe_interior('gw3', z3, z4, [
        ('#e8ddd0', 0.54), ('#b0a898', 0.44), ('#d4c8b8', 0.58), ('#786858', 0.44),
    ])

    # ── OPEN SHELVING ─────────────────────────────────────────────────────────
    os_cen = sc(z4, z5)
    os_w   = sw(z4, z5)

    # Back panel
    add_box('os_back', (px - d/2 + 0.04, os_cen, uh/2),
            (0.02, os_w - 0.04, uh - 0.04), mat=M['wardrobe_inner'])

    # 4 floating shelves at Z = 0.52, 1.06, 1.60, 2.10
    for i, sy in enumerate([0.52, 1.06, 1.60, 2.10]):
        add_box(f'os_shelf_{i}', (px - 0.02, os_cen, sy),
                (d - 0.06, os_w - 0.04, 0.022), mat=M['wardrobe_shelf'])
        # Under-shelf LED
        add_box(f'os_led_{i}', (front_x - 0.06, os_cen, sy - 0.018),
                (0.012, os_w - 0.1, 0.014), mat=M['led_warm'])

    # Hanging plant on top shelf
    add_cylinder('os_plant_pot', (px - 0.01, os_cen - 0.06, 2.16),
                 0.05, 0.055, 0.1, mat=M['plant_green'], verts=12)
    for j in range(5):
        add_cylinder(f'os_leaf_{j}',
                     (px - 0.01 + math.sin(j*1.26)*0.08,
                      os_cen - 0.06 + math.cos(j*1.26)*0.08,
                      2.23),
                     0.032, 0.032, 0.05,
                     mat=M['plant_green'], verts=6)

    # Handbag on mid shelf
    add_box('os_handbag', (px - 0.01, os_cen + 0.02, 1.22),
            (0.08, 0.17, 0.2), mat=M['handbag'])

    # Framed art on lower shelf
    add_box('os_art', (px + 0.01, os_cen, 0.70),
            (0.04, 0.14, 0.19), mat=M['art_frame'])

    # Gold torus decor
    add_torus('os_torus', (px + 0.02, os_cen + 0.1, 0.57),
              major_r=0.045, minor_r=0.012, mat=M['brass'],
              rot=(math.pi/2, 0, 0))

    # ── VELVET STOOL (in front of dressing station) ───────────────────────────
    stool_x = front_x + 0.52;  stool_y = ds_cen

    # Velvet cushion top
    add_cylinder('stool_top', (stool_x, stool_y, 0.46),
                 0.24, 0.22, 0.14, mat=M['stool_velvet'], verts=32)

    # Gold ring torus
    add_torus('stool_ring', (stool_x, stool_y, 0.21),
              major_r=0.2, minor_r=0.02, mat=M['brass'],
              rot=(math.pi/2, 0, 0))

    # Brass stem
    add_cylinder('stool_stem', (stool_x, stool_y, 0.12),
                 0.018, 0.018, 0.22, mat=M['brass'], verts=10)

    # Brass disc base
    add_cylinder('stool_disc', (stool_x, stool_y, 0.014),
                 0.2, 0.2, 0.028, mat=M['brass'], verts=32)


def build_rug(M):
    """Large greige area rug with a border stripe."""
    # Three.js: z = -D/2+0.12+0.18+1.2 = -1.5 → Blender Y = 1.5
    by = 1.5
    add_box('rug',        (0, by, 0.006), sz(3.4, 0.012, 2.8), mat=M['rug'])
    add_box('rug_border', (0, by, 0.008), sz(3.1, 0.012, 2.5), mat=M['rug_border'])


def build_reading_nook(M):
    """Sage armchair, arc floor lamp, marble side table — rotated -45° at (2.15, -1.85)."""
    # Three.js: position [2.15, 0, 1.85] rotation [0, -π/4, 0]
    # Blender: position (2.15, -1.85, 0), rotation around Z = +π/4
    bx = 2.15;  by = -1.85;  seatZ = 0.42
    rot = (0, 0, math.pi/4)   # -45° in Three.js = +45° Blender Z (coords flipped)

    # ── Armchair ──────────────────────────────────────────────────────────────
    # Seat cushion
    seat = add_box('chair_seat', (bx, by, seatZ), sz(0.66, 0.16, 0.62), mat=M['sage'])
    seat.rotation_euler = Euler(rot)
    # Back
    back = add_box('chair_back', (bx, by + 0.28, seatZ + 0.32),
                   sz(0.66, 0.6, 0.14), mat=M['sage'])
    back.rotation_euler = Euler(rot)
    # Armrests
    for ax in (-0.33, 0.33):
        arm = add_box(f'chair_arm_{ax}', (bx + ax, by, seatZ + 0.14),
                      sz(0.12, 0.32, 0.6), mat=M['sage'])
        arm.rotation_euler = Euler(rot)
    # Wood legs
    leg_mat = make_pbr_material('chair_leg', '#7a5230', roughness=0.4)
    for lx, ly in [(-0.26, -0.24), (0.26, -0.24), (-0.26, 0.24), (0.26, 0.24)]:
        leg = add_cylinder(f'chair_leg_{lx}_{ly}',
                           (bx + lx, by - ly, 0.17), 0.02, 0.026, 0.34,
                           mat=leg_mat, verts=10)
        leg.rotation_euler = Euler(rot)

    # Throw cushion
    throw_c = add_box('chair_throw', (bx + 0.05, by + 0.02, seatZ + 0.14),
                      sz(0.34, 0.14, 0.3), mat=M['sage_throw'])
    throw_c.rotation_euler = Euler(rot)

    # ── Arc floor lamp ────────────────────────────────────────────────────────
    # lamp base offset [0.55, 0, -0.1] relative to chair position
    lx = bx + 0.55;  ly = by + 0.1
    # Base disc
    add_cylinder('arc_base', (lx, ly, 0.015), 0.13, 0.15, 0.03, mat=M['brass'], verts=24)
    # Pole
    add_cylinder('arc_pole', (lx, ly, 0.9), 0.014, 0.014, 1.8, mat=M['brass'], verts=12)
    # Quarter-torus arm  (approximate with a cylinder bent — use box as stand-in)
    add_box('arc_arm', (lx - 0.16, ly, 1.78 + 0.16), sz(0.35, 0.028, 0.028),
            mat=M['brass'])
    # Dome shade
    add_cylinder('arc_shade', (lx - 0.32, ly, 1.66), 0.13, 0.13, 0.14,
                 mat=M['brass'], verts=24)
    # Glow bulb
    add_cylinder('arc_bulb', (lx - 0.32, ly, 1.60), 0.06, 0.06, 0.05,
                 mat=M['bulb_glow'], verts=16)
    add_point_light('arc_light', (lx - 0.32, ly, 1.55), energy=260, color=hex_rgb('#ffbe66'))

    # ── Marble side table ─────────────────────────────────────────────────────
    # offset [-0.6, 0, 0.15] relative to chair → Blender (bx-0.6, by-0.15, 0)
    tx = bx - 0.6;  ty = by - 0.15
    add_cylinder('side_top',    (tx, ty, 0.48), 0.22, 0.22, 0.04, mat=M['marble'], verts=32)
    add_cylinder('side_stem',   (tx, ty, 0.24), 0.02, 0.02, 0.48, mat=M['brass'],  verts=12)
    add_cylinder('side_base',   (tx, ty, 0.01), 0.16, 0.16, 0.02, mat=M['brass'],  verts=20)
    # Coffee mug on table
    add_cylinder('mug', (tx + 0.05, ty + 0.03, 0.52), 0.035, 0.03, 0.06, mat=M['mug'], verts=18)


def build_headboard_art(M):
    """Wide framed canvas with abstract earth-tone composition on accent wall."""
    # Three.js: [0, 2.2, -D/2+0.11] = [0, 2.2, -2.89] → Blender (0, 2.89, 2.2)
    by = BACK_Y - 0.11
    add_box('art_frame',  (0, by,       2.2 ), sz(1.5, 0.5, 0.03),   mat=M['art_frame'])
    add_box('art_canvas', (0, by - 0.02, 2.2 ), sz(1.4, 0.42, 0.01),  mat=M['art_canvas'])
    add_box('art_oc1',    (0, by - 0.03, 2.2 - 0.05), sz(0.55, 0.28, 0.008), mat=M['art_oc1'])
    add_box('art_oc2',    (0, by - 0.03, 2.2 + 0.06), sz(0.6,  0.18, 0.008), mat=M['art_oc2'])
    add_box('art_oc3',    (0, by - 0.035,2.2 - 0.1 ), sz(0.3,  0.12, 0.008), mat=M['art_oc3'])


def build_chandelier(M, tx=0, tz=0.55):
    """Brass tiered chandelier with crystal pendants + candle bulbs."""
    # Three.js [0, ?, 0.55] → Blender (0, -0.55, ?)
    bx = tx;  by = -tz
    top_z   = CEIL_Z - 0.03
    body_z  = top_z - 0.62
    r_top   = 0.42;   r_bot = 0.28

    # Canopy
    add_cylinder('ch_canopy', (bx, by, top_z - 0.015), 0.07, 0.09, 0.03, mat=M['brass'], verts=24)
    # Drop rod
    rod_z = (top_z + body_z + 0.18) / 2
    rod_h  = top_z - body_z - 0.18
    add_cylinder('ch_rod', (bx, by, rod_z), 0.012, 0.012, rod_h, mat=M['brass'], verts=12)

    # Upper ring
    add_torus('ch_ring_top', (bx, by, body_z + 0.16),
              major_r=r_top, minor_r=0.014, mat=M['brass'],
              rot=(math.pi/2, 0, 0))
    # Lower ring
    add_torus('ch_ring_bot', (bx, by, body_z - 0.04),
              major_r=r_bot, minor_r=0.012, mat=M['brass'],
              rot=(math.pi/2, 0, 0))

    # 8 candle arms + bulbs on upper ring
    n_candles = 8
    for i in range(n_candles):
        a   = (i / n_candles) * math.pi * 2
        cax = bx + math.cos(a) * r_top
        cay = by + math.sin(a) * r_top
        # Candle body
        add_cylinder(f'ch_candle_{i}', (cax, cay, body_z + 0.16 + 0.045),
                     0.016, 0.022, 0.09, mat=M['brass'], verts=14)
        # Flame bulb
        add_cylinder(f'ch_bulb_{i}', (cax, cay, body_z + 0.16 + 0.14),
                     0.032, 0.032, 0.04, mat=M['bulb_glow'], verts=16)

    # 12 crystal strands (3 beads each) on upper ring
    n_strands = 12
    for i in range(n_strands):
        a    = (i / n_strands) * math.pi * 2
        scx  = bx + math.cos(a) * r_top
        scy  = by + math.sin(a) * r_top
        for k, dy in enumerate([0.05, 0.13, 0.21]):
            r_bead = max(0.028 - k*0.004, 0.01)
            add_cylinder(f'ch_crystal_{i}_{k}', (scx, scy, body_z + 0.16 - dy),
                         r_bead, r_bead, r_bead*2, mat=M['crystal'], verts=8)

    # Inner 8 crystals on lower ring
    for i in range(8):
        a    = (i / 8) * math.pi * 2
        icx  = bx + math.cos(a) * r_bot
        icy  = by + math.sin(a) * r_bot
        add_cylinder(f'ch_inner_{i}', (icx, icy, body_z - 0.1),
                     0.03, 0.03, 0.06, mat=M['crystal'], verts=8)

    # Central finial crystal drop
    add_cylinder('ch_finial', (bx, by, body_z - 0.14),
                 0.055, 0.055, 0.09, mat=M['crystal'], verts=8)

    # Glow core + main chandelier light
    add_cylinder('ch_glow', (bx, by, body_z + 0.05),
                 0.06, 0.06, 0.1, mat=M['bulb_glow'], verts=16)
    add_point_light('ch_main_light', (bx, by, body_z + 0.05),
                    energy=730, color=hex_rgb('#ffc978'), radius=0.1)


def build_decor_lighting(M):
    """LED panel above bed, floor-wash strips, sconces, accent spots, under-bed/wardrobe LEDs."""
    # Three.js bedCZ = -D/2+0.12+0.18+1.075 = -1.625 → Blender Y = 1.625
    bed_cy = 1.625
    wd_x   = LEFT_X + 0.6/2 + 0.03   # ≈ -2.97

    # ── Floating LED panel above bed ──────────────────────────────────────────
    # Three.js: [0, H-0.07, bedCZ+0.25] → Blender (0, -(bedCZ+0.25), H-0.07)
    panel_y = -(bed_cy + 0.25)
    add_box('led_panel_body', (0, panel_y, CEIL_Z - 0.07), sz(1.55, 0.045, 0.16),
            mat=make_pbr_material('panel_body', '#e8e4dc', roughness=0.6, metallic=0.4))
    add_box('led_panel_bot', (0, panel_y, CEIL_Z - 0.096), sz(1.46, 0.006, 0.09),
            mat=M['led_hot'])
    add_box('led_panel_top', (0, panel_y, CEIL_Z - 0.048), sz(1.46, 0.006, 0.09),
            mat=make_pbr_material('panel_top_led', '#ffe4b0', roughness=1.0,
                                  emit_hex='#ffe4b0', emit_strength=1.6))
    add_point_light('panel_pl_main', (0, panel_y, CEIL_Z - 0.18), energy=260, color=hex_rgb('#ffc878'))
    add_point_light('panel_pl_ceil', (0, panel_y, CEIL_Z - 0.02), energy=78,  color=hex_rgb('#ffe0a8'))

    # ── Floor-wash LED strips ─────────────────────────────────────────────────
    led_warm_col = hex_rgb('#ffd088')
    # Back wall floor-wash
    add_box('flw_back', (0, BACK_Y - 0.048, 0.018), sz(W-0.18, 0.022, 0.01), mat=M['led_warm'])
    add_point_light('flw_back_pl', (0, BACK_Y - 0.14, 0.06), energy=90, color=led_warm_col)
    # Left wall
    add_box('flw_left', (LEFT_X + 0.048, 0, 0.018), sz(0.01, 0.022, D-0.18), mat=M['led_warm'])
    add_point_light('flw_left_pl', (LEFT_X + 0.14, -0.1, 0.06), energy=90, color=led_warm_col)
    # Right wall
    add_box('flw_right', (RIGHT_X - 0.048, 0, 0.018), sz(0.01, 0.022, D-0.18), mat=M['led_warm'])
    add_point_light('flw_right_pl', (RIGHT_X - 0.14, -0.1, 0.06), energy=90, color=led_warm_col)

    # ── Wall box sconces on headboard wall ────────────────────────────────────
    # Three.js: x=±1.22, y=1.86, z=-D/2+0.085 → Blender x=±1.22, y=D/2-0.085=2.915, z=1.86
    sconce_by = BACK_Y - 0.085
    for sx in (-1.22, 1.22):
        add_box(f'sconce_body_{sx}', (sx, sconce_by, 1.86),
                sz(0.055, 0.21, 0.072), mat=M['brass'])
        # Up slit
        add_box(f'sconce_up_{sx}',   (sx, sconce_by - 0.012, 1.86 + 0.115),
                sz(0.038, 0.016, 0.055), mat=M['led_sconce'])
        # Down slit
        add_box(f'sconce_dn_{sx}',   (sx, sconce_by - 0.012, 1.86 - 0.115),
                sz(0.038, 0.016, 0.055), mat=M['led_sconce'])
        add_point_light(f'sconce_up_pl_{sx}',  (sx, sconce_by - 0.08, 2.02),  energy=100, color=hex_rgb('#ffbe60'))
        add_point_light(f'sconce_dn_pl_{sx}',  (sx, sconce_by - 0.08, 1.70),  energy=100, color=hex_rgb('#ffbe60'))

    # ── Accent spotlights on fluted wall ──────────────────────────────────────
    # Three.js: position [-0.85, H-0.08, -D/2+0.75] → Blender (-0.85, -(−D/2+0.75), H-0.08)
    #         = (-0.85, D/2-0.75, H-0.08) = (-0.85, 2.25, 2.72)
    # target:  [-0.85, 1.1, -D/2+0.05] → Blender (-0.85, D/2-0.05, 1.1) = (-0.85, 2.95, 1.1)
    add_spot_light('spot_accent_l',
                   (-0.85, 2.25, CEIL_Z - 0.08),
                   target_loc=(-0.85, 2.95, 1.1),
                   energy=455, color=hex_rgb('#fff8ee'),
                   spot_size=0.42, spot_blend=0.8)
    add_spot_light('spot_accent_r',
                   (0.85, 2.25, CEIL_Z - 0.08),
                   target_loc=(0.85, 2.95, 1.1),
                   energy=455, color=hex_rgb('#fff8ee'),
                   spot_size=0.42, spot_blend=0.8)

    # ── Under-bed LED ─────────────────────────────────────────────────────────
    add_box('under_bed_led', (0, -bed_cy + 0.05, 0.018), sz(2.05, 0.016, 1.95), mat=M['led_warm'])
    add_point_light('under_bed_pl', (0, -bed_cy, 0.05), energy=90, color=led_warm_col)

    # ── Under-wardrobe LED ───────────────────────────────────────────────────
    # Three.js: [wdX, 0.016, 1.0] wdX≈-2.97, z=1.0 → Blender (-2.97, -1.0, 0.016)
    add_box('under_wd_led', (wd_x, -1.0, 0.016), sz(0.48, 0.014, 2.28), mat=M['led_warm'])
    add_point_light('under_wd_pl', (wd_x + 0.28, -1.0, 0.05), energy=90, color=led_warm_col)

    # ── Wardrobe top LED ─────────────────────────────────────────────────────
    add_box('wd_top_led', (wd_x, -1.0, 2.505), sz(0.54, 0.014, 2.28), mat=M['led_warm'])
    add_point_light('wd_top_pl', (wd_x + 0.3, -1.0, 2.55), energy=65, color=led_warm_col)


def build_lighting():
    """Primary daylight, window spot, ambient, hemisphere, downlights, fill lights."""
    # ── Directional (sun/daylight from window side) ───────────────────────────
    data = bpy.data.lights.new('dir_light', 'SUN')
    data.energy = 1.6
    data.color  = hex_rgb('#fff4e8')
    data.angle  = 0.05
    sun = bpy.data.objects.new('dir_light', data)
    sun.location       = (9, -0.5, 5.5)
    sun.rotation_euler = Euler((-0.55, 0.0, 1.45))
    link(sun)

    # ── Window spot (sunspot on floor) ────────────────────────────────────────
    # Three.js: position [W/2+0.4, 2.0, 0.4] → Blender (W/2+0.4, -0.4, 2.0)
    # target: [-1.5, 0, 0.5] → Blender (-1.5, -0.5, 0)
    add_spot_light('win_spot',
                   (RIGHT_X + 0.4, -0.4, 2.0),
                   target_loc=(-1.5, -0.5, 0),
                   energy=580, color=hex_rgb('#fff8ec'),
                   spot_size=0.38, spot_blend=0.72)

    # ── Ambient (world) ───────────────────────────────────────────────────────
    world = bpy.context.scene.world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wn.clear()
    bg   = wn.new('ShaderNodeBackground')
    wout = wn.new('ShaderNodeOutputWorld')
    bg.inputs['Color'].default_value    = (*hex_rgb('#fff0d5'), 1.0)
    bg.inputs['Strength'].default_value = 0.18
    world.node_tree.links.new(bg.outputs['Background'], wout.inputs['Surface'])

    # ── Hemisphere-style fill (sky/ground) ────────────────────────────────────
    # Approximated with two area lights pointing down (sky) and up (ground)
    add_area_light('hemi_sky',   (0, 0, CEIL_Z - 0.01), energy=22,
                   color=hex_rgb('#e4eeff'), size=(W, D), rot=(math.pi, 0, 0))
    add_area_light('hemi_ground',(0, 0, 0.01),           energy=7,
                   color=hex_rgb('#b8aa95'), size=(W, D), rot=(0, 0, 0))

    # ── 5 Recessed downlights (actual point lights) ───────────────────────────
    dl_positions = [(-1.7, -1.4), (1.7, -1.4), (-1.7, 1.2), (1.7, 1.2), (0, 1.6)]
    for i, (tx, tz) in enumerate(dl_positions):
        add_point_light(f'dl_pl_{i}', (tx, -tz, CEIL_Z - 0.15),
                        energy=290, color=hex_rgb('#ffefd2'), radius=0.06)

    # ── Camera-side soft fill ─────────────────────────────────────────────────
    # Three.js: [2.5, 2.4, 4.5] → Blender (2.5, -4.5, 2.4)
    add_point_light('cam_fill',  (2.5, -4.5, 2.4),  energy=260, color=hex_rgb('#eef1ff'))

    # ── Back fill ─────────────────────────────────────────────────────────────
    # Three.js: [0, 2.2, -1.5] → Blender (0, 1.5, 2.2)
    add_point_light('back_fill', (0, 1.5, 2.2), energy=97, color=hex_rgb('#ffd9a8'))


# ═══════════════════════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════════════════════

def build_camera():
    """
    Camera position matches Three.js [3.6, 2.55, 6.6].
    Three.js → Blender: (3.6, -6.6, 2.55).
    Points toward target (0, -0.9, 0.6) [from Three.js (0, 0.6, 0.9)].
    """
    cam_loc    = (3.6, -6.6, 2.55)
    target_loc = (0.0, -0.9, 0.6)

    cam_data = bpy.data.cameras.new('BedroomCam')
    cam_data.lens       = 35        # 35 mm — moderate wide
    cam_data.clip_start = 0.05
    cam_data.clip_end   = 30.0

    cam_obj = bpy.data.objects.new('BedroomCam', cam_data)
    cam_obj.location = cam_loc

    # Point camera toward target
    direction = Vector(target_loc) - Vector(cam_loc)
    rot_quat  = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj


# ═══════════════════════════════════════════════════════════════════════════════
#  RENDER SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

def configure_render():
    """Cycles + GPU + ACES + denoising + resolution."""
    scene = bpy.context.scene
    scene.render.engine        = 'CYCLES'
    scene.render.resolution_x  = RESOLUTION[0]
    scene.render.resolution_y  = RESOLUTION[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath      = '//bedroom_render.png'

    # Samples
    cycles = scene.cycles
    cycles.samples             = SAMPLES
    cycles.use_denoising       = True
    try:
        cycles.denoiser        = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cycles.use_preview_denoising = True

    # GPU
    if USE_GPU:
        prefs = bpy.context.preferences.addons.get('cycles')
        if prefs:
            cprefs = prefs.preferences
            try:
                cprefs.compute_device_type = 'CUDA'
            except Exception:
                try:
                    cprefs.compute_device_type = 'OPTIX'
                except Exception:
                    pass
        scene.cycles.device = 'GPU'

    # Tone mapping: ACES-like via Filmic + high contrast
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look           = 'High Contrast'
    scene.view_settings.exposure       = 0.15
    scene.view_settings.gamma          = 1.05

    # Light paths (for glass and crystals)
    cycles.max_bounces             = 12
    cycles.diffuse_bounces         = 4
    cycles.glossy_bounces          = 6
    cycles.transmission_bounces    = 8
    cycles.transparent_max_bounces = 8

    # Shadow catcher support
    scene.render.use_freestyle     = False


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Building Master Bedroom Scene …")
    print("=" * 60)

    clear_scene()
    configure_render()

    print("  Building materials …")
    M = build_materials()

    print("  Building room shell …")
    build_room(M)

    print("  Building accent wall …")
    build_accent_wall(M)

    print("  Building bed …")
    build_bed(M)

    print("  Building nightstands …")
    build_nightstand(M, tx=-1.72)
    build_nightstand(M, tx= 1.72)

    print("  Building bench …")
    build_bench(M)

    print("  Building wardrobe system …")
    build_wardrobe(M)

    print("  Building rug …")
    build_rug(M)

    print("  Building reading nook …")
    build_reading_nook(M)

    print("  Building headboard art …")
    build_headboard_art(M)

    print("  Building chandelier …")
    build_chandelier(M, tx=0, tz=0.55)

    print("  Building decorative lighting …")
    build_decor_lighting(M)

    print("  Building primary lighting rig …")
    build_lighting()

    print("  Setting up camera …")
    build_camera()

    print("=" * 60)
    print("  Scene complete!")
    print(f"  Objects : {len(bpy.data.objects)}")
    print(f"  Materials: {len(bpy.data.materials)}")
    print("  Press F12 to render.")
    print("=" * 60)


main()
