"""
=======================================================================
  Modern Luxury Kitchen — Blender Python Scene Builder  v2
  Integrates KitchenDecorLights: cool under-cabinet LED strips,
  warm toe-kick LED strips, range-hood interior LED, display-niche
  spot, linear LED pendant above peninsula (anodised housing +
  diffuser + suspension cables), peninsula waterfall-side LED strip.

  All materials use Principled BSDF with Sheen and Clearcoat inputs
  where appropriate (mirrors meshPhysicalMaterial in Three.js).

  Reduced global light intensities matching Three.js Lighting values:
    directional 1.4 · ambient 0.18 · hemisphere 0.32
    recessed 5 each · pendant pools 8 each.
=======================================================================
  HOW TO USE:
  1. Open Blender (3.x or 4.x)
  2. Go to Scripting workspace
  3. Click "Open" and select this file  OR  paste contents
  4. Press "Run Script" (or Alt+P)
  5. Press F12 to render

  TEXTURES (optional):
    Place PBR maps in TEXTURE_PATH below:
      tile_albedo.png / tile_roughness.png
      marble_albedo.png
      walnut_albedo.png
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
        if len(obj.data.materials):
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = True
    elif hasattr(obj, 'cycles_visibility'):
        obj.cycles_visibility.shadow = True
    return obj


def add_cylinder(name, loc, radius, height, mat=None, verts=24):
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj  = bpy.data.objects.new(name, mesh)
    link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False,
        segments=verts, radius1=radius, radius2=radius, depth=height
    )
    bm.to_mesh(mesh)
    bm.free()

    obj.location = loc
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
              size=1.0, size_y=None, rot=None):
    """Module-level light factory (replaces the inline helper in setup_lighting)."""
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
    if rot:
        obj.rotation_euler = Euler([math.radians(r) for r in rot])
    obj.data.use_shadow = True
    return obj


def add_point_light(name, loc, energy, color=(1, 1, 1), size=0.05):
    """Convenience wrapper for point lights used in decorative fixtures."""
    return add_light(name, 'POINT', loc, energy, color=color, size=size)


# ═══════════════════════════════════════════════════════════════════════════
#  MATERIALS — Full Principled BSDF PBR
#  Sheen and Clearcoat inputs are set where available to mirror
#  Three.js meshPhysicalMaterial behaviour.
# ═══════════════════════════════════════════════════════════════════════════

def pbr(name, color, roughness=0.5, metallic=0.0, specular=0.5,
        ior=1.45, transmission=0.0, alpha=1.0,
        emission_color=None, emission_strength=0.0,
        subsurface=0.0, subsurface_color=None,
        clearcoat=0.0, clearcoat_roughness=0.10,
        sheen=0.0, sheen_roughness=0.50):
    """Create a Principled BSDF material with optional clearcoat and sheen."""
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

    if subsurface > 0:
        for key in ('Subsurface Weight', 'Subsurface'):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = subsurface
                break
        if subsurface_color:
            sr, sg, sb = subsurface_color
            bsdf.inputs['Subsurface Color'].default_value = (sr, sg, sb, 1.0)

    # Clearcoat — Blender 3.x: 'Clearcoat'/'Clearcoat Roughness';
    # Blender 4.x: 'Coat Weight'/'Coat Roughness'
    if clearcoat > 0:
        for cc_key in ('Coat Weight', 'Clearcoat'):
            if cc_key in bsdf.inputs:
                bsdf.inputs[cc_key].default_value = clearcoat
                break
        for ccr_key in ('Coat Roughness', 'Clearcoat Roughness'):
            if ccr_key in bsdf.inputs:
                bsdf.inputs[ccr_key].default_value = clearcoat_roughness
                break

    # Sheen — Blender 3.x: 'Sheen'/'Sheen Roughness';
    # Blender 4.x: 'Sheen Weight'/'Sheen Roughness'
    if sheen > 0:
        for sh_key in ('Sheen Weight', 'Sheen'):
            if sh_key in bsdf.inputs:
                bsdf.inputs[sh_key].default_value = sheen
                break
        if 'Sheen Roughness' in bsdf.inputs:
            bsdf.inputs['Sheen Roughness'].default_value = sheen_roughness

    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def set_blend(mat, mode='BLEND'):
    if hasattr(mat, 'blend_method'):
        mat.blend_method = mode


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


def load_image_texture(mat, image_path, input_socket, colorspace='sRGB'):
    if not os.path.exists(image_path):
        return False
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf  = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return False
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = bpy.data.images.load(image_path)
    tex_node.image.colorspace_settings.name = colorspace
    links.new(tex_node.outputs['Color'], bsdf.inputs[input_socket])
    return True


def create_materials():
    M = {}

    # ── Structural ──
    M['wall']    = pbr('Wall_Plaster',    (0.72, 0.68, 0.62), roughness=0.94)
    add_micro_bump(M['wall'], scale=12.0, strength=0.04)
    M['ceiling'] = pbr('Ceiling',         (0.80, 0.79, 0.76), roughness=1.00)
    M['floor']   = pbr('Floor_Porcelain', (0.84, 0.81, 0.75), roughness=0.12, ior=1.55,
                        clearcoat=0.6, clearcoat_roughness=0.08)
    procedural_stone(M['floor'], (0.84, 0.81, 0.75), (0.74, 0.71, 0.66), scale=2.2)
    M['grout']   = pbr('Grout',           (0.62, 0.60, 0.57), roughness=0.95)

    floor_tex = os.path.join(TEXTURE_PATH, "tile_albedo.png")
    load_image_texture(M['floor'], floor_tex, 'Base Color')
    load_image_texture(M['floor'], os.path.join(TEXTURE_PATH, "tile_roughness.png"),
                       'Roughness', 'Non-Color')

    # ── Cabinets (warm taupe matte-satin lacquer) ──
    M['cabinet']    = pbr('Cabinet_Taupe',   (0.68, 0.63, 0.56), roughness=0.40,
                           ior=1.50, clearcoat=0.15, clearcoat_roughness=0.35)
    add_micro_bump(M['cabinet'], scale=30.0, strength=0.03)
    M['black_trim'] = pbr('Black_Trim',      (0.05, 0.05, 0.05), roughness=0.28)
    M['dark_int']   = pbr('Cabinet_DarkInt', (0.10, 0.07, 0.05), roughness=0.70)

    # ── Countertop / Backsplash (light quartz with veining) ──
    M['marble'] = pbr('Marble_White', (0.91, 0.89, 0.85), roughness=0.10,
                       ior=1.55, clearcoat=0.70, clearcoat_roughness=0.06)
    procedural_stone(M['marble'], (0.92, 0.90, 0.86), (0.62, 0.60, 0.56), scale=3.5)
    M['backsplash'] = pbr('Backsplash_Stone', (0.86, 0.83, 0.78), roughness=0.22,
                           ior=1.50, clearcoat=0.60, clearcoat_roughness=0.10)
    procedural_stone(M['backsplash'], (0.87, 0.84, 0.79), (0.72, 0.69, 0.64), scale=4.0)

    marble_tex = os.path.join(TEXTURE_PATH, "marble_albedo.png")
    load_image_texture(M['marble'],     marble_tex, 'Base Color')
    load_image_texture(M['backsplash'], marble_tex, 'Base Color')

    # ── Island / Peninsula (dark walnut wood with directional grain) ──
    M['walnut'] = pbr('Walnut_Wood', (0.20, 0.13, 0.07), roughness=0.45,
                       sheen=0.08, sheen_roughness=0.60)
    procedural_wood(M['walnut'], (0.16, 0.10, 0.05), (0.26, 0.17, 0.09),
                    stretch=(1.0, 16.0, 1.0), grain=7.0)
    load_image_texture(M['walnut'], os.path.join(TEXTURE_PATH, "walnut_albedo.png"),
                       'Base Color')

    M['shelf_wood'] = pbr('Shelf_Wood', (0.28, 0.18, 0.10), roughness=0.52,
                           sheen=0.06, sheen_roughness=0.65)
    procedural_wood(M['shelf_wood'], (0.24, 0.15, 0.08), (0.34, 0.23, 0.13),
                    stretch=(1.0, 12.0, 1.0), grain=8.0)

    # ── Appliances ──
    M['black_appliance'] = pbr('BlackAppliance', (0.03, 0.03, 0.03), roughness=0.28,
                                metallic=0.35, clearcoat=0.80, clearcoat_roughness=0.15)
    M['stainless']       = pbr('StainlessSteel', (0.60, 0.61, 0.63), roughness=0.30,
                                metallic=0.98)
    add_micro_bump(M['stainless'], scale=200.0, strength=0.015)
    M['black_sink']      = pbr('BlackSink',      (0.04, 0.04, 0.04), roughness=0.18,
                                metallic=0.5)
    M['cooktop']         = pbr('Cooktop_Glass',  (0.02, 0.02, 0.02), roughness=0.06,
                                ior=1.52, clearcoat=0.60, clearcoat_roughness=0.08)

    # ── Bar stools ──
    M['fabric']      = pbr('Fabric_Gray', (0.52, 0.48, 0.44), roughness=0.95,
                            subsurface=0.02, subsurface_color=(0.52, 0.48, 0.44),
                            sheen=0.30, sheen_roughness=0.70)
    add_micro_bump(M['fabric'], scale=120.0, strength=0.05)
    M['black_metal'] = pbr('Black_Metal', (0.04, 0.04, 0.04), roughness=0.22, metallic=0.9)

    # ── Glass (pendant shade, display niche) ──
    M['glass'] = pbr('Glass_Clear', (0.88, 0.83, 0.72), roughness=0.02,
                     transmission=0.90, ior=1.52, alpha=0.12)
    set_blend(M['glass'])

    # ── Emissives (existing) ──
    M['bulb']       = pbr('Bulb_Filament', (1.0, 0.78, 0.38), roughness=1.0,
                           emission_color=(1.0, 0.78, 0.38), emission_strength=14.0)
    M['led_warm']   = pbr('LED_Cove',      (1.0, 0.86, 0.58), roughness=1.0,
                           emission_color=(1.0, 0.86, 0.58), emission_strength=7.0)
    M['led_under']  = pbr('LED_Under',     (1.0, 0.90, 0.72), roughness=1.0,
                           emission_color=(1.0, 0.90, 0.72), emission_strength=5.0)
    M['led_recess'] = pbr('LED_Recessed',  (1.0, 0.97, 0.92), roughness=0.0,
                           emission_color=(1.0, 0.97, 0.92), emission_strength=10.0)

    # ── NEW Emissives from KitchenDecorLights ──
    # Cool under-cabinet / hood strips  (#deeeff → 0.87, 0.94, 1.0)
    M['led_cool']    = pbr('LED_Cool',     (0.87, 0.94, 1.0), roughness=1.0,
                            emission_color=(0.87, 0.94, 1.0), emission_strength=8.0)
    # Warm toe-kick strips  (#ffd088 → 1.0, 0.82, 0.53)
    M['led_toekick'] = pbr('LED_ToeKick', (1.0, 0.82, 0.53), roughness=1.0,
                            emission_color=(1.0, 0.82, 0.53), emission_strength=6.0)
    # Display niche warm accent LED
    M['led_niche']   = pbr('LED_Niche',   (1.0, 0.90, 0.72), roughness=1.0,
                            emission_color=(1.0, 0.90, 0.72), emission_strength=6.0)
    # Linear pendant — anodised aluminium housing  (#1c1a18 → 0.11, 0.10, 0.09)
    M['lin_housing'] = pbr('LinPend_Housing', (0.11, 0.10, 0.09), roughness=0.35,
                            metallic=0.80)
    # Linear pendant — frosted diffuser / warm white emissive
    M['lin_diffuser'] = pbr('LinPend_Diffuser', (1.0, 0.98, 0.94), roughness=1.0,
                             emission_color=(1.0, 0.91, 0.75), emission_strength=9.0)

    # ── Nature ──
    M['plant'] = pbr('Plant_Leaf',  (0.10, 0.32, 0.10), roughness=0.82,
                     subsurface=0.08, subsurface_color=(0.20, 0.55, 0.20))
    M['pot']   = pbr('Terracotta',  (0.68, 0.38, 0.22), roughness=0.88)

    # ── Window frame ──
    M['win_frame'] = pbr('Window_Frame', (0.82, 0.80, 0.76), roughness=0.35)
    M['win_glass'] = pbr('Window_Glass', (0.76, 0.88, 0.95), roughness=0.02,
                          transmission=0.92, ior=1.52, alpha=0.08)
    set_blend(M['win_glass'])

    return M


# ═══════════════════════════════════════════════════════════════════════════
#  ROOM CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

ROOM_W = 7.20   # X — left to right
ROOM_D = 6.00   # Y — back(-) to front(+)
ROOM_H = 2.85   # Z — floor to ceiling

# Cabinet constants
LOW_D  = 0.60   # lower cabinet depth (Y)
LOW_H  = 0.90   # lower cabinet height (Z)
UPP_D  = 0.35   # upper cabinet depth (Y)
UPP_H  = 0.75   # upper cabinet height (Z)
UPP_Z  = 1.48   # bottom Z of upper cabinets
CT_H   = 0.90   # countertop top surface Z
CT_T   = 0.040  # countertop thickness

# Derived positions (back wall, left wall)
BY     = -ROOM_D / 2 + 0.075 + LOW_D / 2    # back-wall lower cab centre Y  ≈ -2.625
BY_UP  = -ROOM_D / 2 + 0.075 + UPP_D / 2    # back-wall upper cab centre Y  ≈ -2.750
LX     = -ROOM_W / 2 + 0.075 + LOW_D / 2    # left-wall lower cab centre X  ≈ -3.225
LX_UP  = -ROOM_W / 2 + 0.075 + UPP_D / 2   # left-wall upper cab centre X  ≈ -3.350


# ═══════════════════════════════════════════════════════════════════════════
#  ROOM
# ═══════════════════════════════════════════════════════════════════════════

def build_room(M):
    # Floor slab
    add_box('Floor_Slab', (0, 0, -0.06), (ROOM_W, ROOM_D, 0.12), M['floor'])

    # Tile grout lines (horizontal)
    for gy in [-1.2, 0.0, 1.2]:
        add_box(f'Grout_H_{gy}', (0, gy, 0.001), (ROOM_W, 0.005, 0.002), M['grout'])
    # Tile grout lines (vertical)
    for gx in [-1.8, 0.0, 1.8]:
        add_box(f'Grout_V_{gx}', (gx, 0, 0.001), (0.005, ROOM_D, 0.002), M['grout'])

    # Walls
    add_box('Wall_Back',  (0,          -ROOM_D/2, ROOM_H/2), (ROOM_W, 0.14, ROOM_H), M['wall'])
    add_box('Wall_Left',  (-ROOM_W/2,  0,         ROOM_H/2), (0.14, ROOM_D, ROOM_H), M['wall'])
    add_box('Wall_Right', (ROOM_W/2,   0,         ROOM_H/2), (0.14, ROOM_D, ROOM_H), M['wall'])

    # Ceiling
    add_box('Ceiling_Main', (0, 0, ROOM_H + 0.06), (ROOM_W, ROOM_D, 0.12), M['ceiling'])

    # False-ceiling cove frame (tray ceiling)
    DROP = 0.22
    BORD = 0.70
    cz   = ROOM_H - DROP
    add_box('Cove_N', (0,  ROOM_D/2 - BORD/2, cz + DROP/2), (ROOM_W, BORD, DROP), M['ceiling'])
    add_box('Cove_S', (0, -ROOM_D/2 + BORD/2, cz + DROP/2), (ROOM_W, BORD, DROP), M['ceiling'])
    add_box('Cove_E', ( ROOM_W/2 - BORD/2, 0, cz + DROP/2), (BORD, ROOM_D - BORD*2, DROP), M['ceiling'])
    add_box('Cove_W', (-ROOM_W/2 + BORD/2, 0, cz + DROP/2), (BORD, ROOM_D - BORD*2, DROP), M['ceiling'])

    # Inner false-ceiling panel
    iw  = ROOM_W - BORD * 2
    id_ = ROOM_D - BORD * 2
    add_box('Ceiling_Inner', (0, 0, cz + 0.02), (iw, id_, 0.04), M['ceiling'])

    # Warm cove LED strips at inner ledge
    add_box('CoveLED_N', (0,  ROOM_D/2 - BORD + 0.03, cz + 0.018), (ROOM_W-0.4, 0.04, 0.018), M['led_warm'])
    add_box('CoveLED_S', (0, -ROOM_D/2 + BORD - 0.03, cz + 0.018), (ROOM_W-0.4, 0.04, 0.018), M['led_warm'])
    add_box('CoveLED_E', ( ROOM_W/2 - BORD + 0.03, 0, cz + 0.018), (0.04, ROOM_D-BORD*2-0.3, 0.018), M['led_warm'])
    add_box('CoveLED_W', (-ROOM_W/2 + BORD - 0.03, 0, cz + 0.018), (0.04, ROOM_D-BORD*2-0.3, 0.018), M['led_warm'])

    # Baseboard trim
    base_mat = M['ceiling']
    add_box('Base_Back',  (0,          -ROOM_D/2+0.10, 0.06), (ROOM_W-0.14, 0.018, 0.12), base_mat)
    add_box('Base_Left',  (-ROOM_W/2+0.10, 0,          0.06), (0.018, ROOM_D-0.14, 0.12), base_mat)
    add_box('Base_Right', ( ROOM_W/2-0.10, 0,          0.06), (0.018, ROOM_D-0.14, 0.12), base_mat)

    # Window (left wall, above sink)
    build_window(M, pos=(-ROOM_W/2+0.10, -1.10, 1.40), w=1.50, h=1.20)

    # Backsplash zones
    CT_Z  = CT_H
    BS_H  = 0.58
    add_box('BSpBk', (0.20, -ROOM_D/2+0.01, CT_Z+0.04+BS_H/2), (3.80, 0.012, BS_H), M['backsplash'])
    add_box('BSpLf', (-ROOM_W/2+0.01, -0.60, CT_Z+0.04+BS_H/2), (0.012, 2.80, BS_H), M['backsplash'])


def build_window(M, pos, w, h):
    x, y, z = pos
    d = 0.12
    add_box('Win_Frame', (x, y, z),        (d, w + 0.08, h + 0.08), M['win_frame'])
    add_box('Win_Glass', (x+0.01, y, z),   (d*0.4, w-0.06, h-0.06), M['win_glass'])
    add_box('Win_Bar_H', (x+0.01, y, z),   (d*0.42, w+0.02, 0.030), M['win_frame'])
    add_box('Win_Bar_V', (x+0.01, y, z),   (d*0.42, 0.030, h+0.02), M['win_frame'])
    add_box('Win_Sill',  (x+0.05, y, z-h/2-0.04), (0.20, w+0.16, 0.06), M['ceiling'])


# ═══════════════════════════════════════════════════════════════════════════
#  CABINETS
# ═══════════════════════════════════════════════════════════════════════════

def lower_cab(tag, cx, cy, w, M, drawer=False):
    add_box(f'LC_{tag}_Body',    (cx, cy, LOW_H/2),             (w, LOW_D, LOW_H),           M['cabinet'])
    add_box(f'LC_{tag}_TrimTop', (cx, cy, LOW_H-0.004),         (w+0.006, LOW_D+0.006, 0.008), M['black_trim'])
    add_box(f'LC_{tag}_Handle',  (cx, cy-LOW_D/2+0.018, LOW_H*0.55), (w*0.45, 0.014, 0.014),  M['black_trim'])
    if drawer:
        add_box(f'LC_{tag}_DLine', (cx, cy-LOW_D/2+0.003, LOW_H*0.72), (w-0.04, 0.006, 0.006), M['black_trim'])


def upper_cab(tag, cx, cy, cz, w, M, glass=False):
    body_mat = M['dark_int'] if glass else M['cabinet']
    add_box(f'UC_{tag}_Body',  (cx, cy, cz+UPP_H/2),      (w, UPP_D, UPP_H),           body_mat)
    add_box(f'UC_{tag}_TrimB', (cx, cy, cz+0.004),         (w+0.006, UPP_D+0.006, 0.008), M['black_trim'])
    add_box(f'UC_{tag}_TrimT', (cx, cy, cz+UPP_H-0.004),  (w+0.006, UPP_D+0.006, 0.008), M['black_trim'])
    if glass:
        add_box(f'UC_{tag}_GlFrame', (cx, cy-UPP_D/2+0.018, cz+UPP_H/2), (w, 0.022, UPP_H), M['black_trim'])
        gm = pbr(f'UC_{tag}_GlMat', (0.70,0.80,0.92), roughness=0.02,
                 transmission=0.86, ior=1.52, alpha=0.08)
        set_blend(gm)
        add_box(f'UC_{tag}_Glass',  (cx, cy-UPP_D/2+0.014, cz+UPP_H/2), (w*0.88, 0.006, UPP_H*0.86), gm)
        add_box(f'UC_{tag}_IntLED', (cx, cy+UPP_D/2-0.05,  cz+UPP_H-0.06), (w*0.82, 0.05, 0.016), M['led_warm'])
    else:
        add_box(f'UC_{tag}_Handle', (cx, cy-UPP_D/2+0.014, cz+UPP_H*0.45), (w*0.42, 0.014, 0.014), M['black_trim'])


def build_cabinets(M):
    LX_UP_loc = -ROOM_W/2 + 0.075 + UPP_D/2
    BY_UP_loc = -ROOM_D/2 + 0.075 + UPP_D/2

    # ── LEFT WALL LOWER ──
    lower_cab('L1', LX, -1.55, 0.80, M, drawer=True)
    lower_cab('L2', LX, -0.65, 0.80, M)
    lower_cab('L3', LX,  0.20, 0.70, M, drawer=True)
    lower_cab('L4', LX,  0.92, 0.60, M)

    # Left wall countertop + existing warm under-cabinet strip
    add_box('CT_Left',    (LX, -0.50, CT_H + CT_T/2),        (LOW_D + 0.05, 2.85, CT_T),  M['marble'])
    add_box('LED_L_Strip', (LX_UP_loc, -0.50, UPP_Z - 0.022), (UPP_D, 2.75, 0.018),        M['led_under'])

    # ── LEFT WALL UPPER ──
    upper_cab('L1', LX_UP_loc, -1.50, UPP_Z, 0.80, M, glass=True)
    upper_cab('L2', LX_UP_loc, -0.65, UPP_Z, 0.80, M, glass=True)
    upper_cab('L3', LX_UP_loc,  0.22, UPP_Z, 0.75, M)
    upper_cab('L4', LX_UP_loc,  0.98, UPP_Z, 0.65, M)

    # ── BACK WALL LOWER ──
    lower_cab('B1', -1.80, BY, 0.90, M, drawer=True)
    lower_cab('B2', -0.80, BY, 0.90, M)
    lower_cab('B3',  0.20, BY, 0.90, M, drawer=True)
    lower_cab('B4',  1.20, BY, 0.80, M)
    lower_cab('B5',  2.05, BY, 0.65, M)

    # Back wall countertop + existing warm under-cabinet strip
    add_box('CT_Back',    (0.12, BY, CT_H + CT_T/2),          (4.30, LOW_D + 0.05, CT_T),  M['marble'])
    add_box('LED_B_Strip', (0.12, BY_UP_loc, UPP_Z - 0.022),  (3.90, UPP_D, 0.018),         M['led_under'])

    # ── BACK WALL UPPER (gap for range hood) ──
    upper_cab('B1', -1.80, BY_UP_loc, UPP_Z, 0.90, M)
    upper_cab('B2',  0.55, BY_UP_loc, UPP_Z, 1.65, M)

    # ── RIGHT WALL: tall open-shelf tower ──
    RX = ROOM_W/2 - 0.075 - 0.22
    add_box('TowerShelf_Body', (RX, -1.20, ROOM_H/2), (0.44, UPP_D+0.12, ROOM_H-0.06), M['cabinet'])
    for sz in [0.55, 1.10, 1.65, 2.20]:
        add_box(f'TShelf_{sz}', (RX, -1.20, sz), (0.38, UPP_D+0.06, 0.030), M['shelf_wood'])
    add_box('Tower_TrimL', (RX-0.22, -1.20, ROOM_H/2), (0.014, UPP_D+0.13, ROOM_H-0.06), M['black_trim'])
    add_box('Tower_TrimR', (RX+0.22, -1.20, ROOM_H/2), (0.014, UPP_D+0.13, ROOM_H-0.06), M['black_trim'])


def build_cabinet_living_details(M):
    """Practical cabinet inserts mirrored from KitchenScene.tsx.

    Only three units are opened: under-sink care, cookware and a narrow pantry.
    This keeps the hero frame composed while making the kitchen credibly usable.
    """
    pale_int = pbr('Drawer_PaleInterior', (0.78, 0.75, 0.69), roughness=0.68)
    bin_light = pbr('WasteBin_Light', (0.78, 0.76, 0.71), roughness=0.72)
    bin_dark = pbr('WasteBin_Dark', (0.26, 0.26, 0.24), roughness=0.72)
    rail = M['stainless']

    # Integrated dishwasher on the left run: taupe face, discreet dark program rail and amber status LED.
    dish_x, dish_y = LX + LOW_D/2 + 0.015, 0.20
    add_box('Dishwasher_Front', (dish_x, dish_y, 0.45), (0.022, 0.68, 0.82), M['cabinet'])
    add_box('Dishwasher_ControlRail', (dish_x+0.012, dish_y, 0.77), (0.028, 0.61, 0.028), M['black_appliance'])
    add_box('Dishwasher_Status', (dish_x+0.016, dish_y+0.24, 0.77), (0.030, 0.020, 0.012), M['led_warm'])

    # Under-sink double pull-out, visible just enough to read as a genuine utility cabinet.
    sink_x, sink_y = LX + LOW_D/2 + 0.17, -1.55
    add_box('SinkPull_Frame', (sink_x, sink_y, 0.31), (0.32, 0.58, 0.27), pale_int)
    for y in (sink_y - 0.30, sink_y + 0.30):
        add_box(f'SinkPull_Rail_{y:.2f}', (sink_x, y, 0.31), (0.32, 0.040, 0.27), rail)
    add_box('SinkPull_BinWaste', (sink_x, sink_y-0.15, 0.26), (0.25, 0.19, 0.18), bin_light)
    add_box('SinkPull_BinCare',  (sink_x, sink_y+0.15, 0.26), (0.25, 0.19, 0.18), bin_dark)
    bottle_mats = [pbr('CareGreen', (0.30,0.47,0.30), roughness=0.35), pbr('CareOat', (0.82,0.77,0.67), roughness=0.35)]
    for i, (by, bz, mat) in enumerate([(sink_y+0.11,0.50,bottle_mats[0]), (sink_y+0.20,0.49,bottle_mats[1]), (sink_y-0.12,0.48,bin_light)]):
        add_cylinder(f'SinkPull_Bottle_{i}', (sink_x, by, bz), 0.030, 0.13, mat, 14)

    # Open cookware tray on the back run, facing the camera on the same axis as the existing drawers.
    tray_x, tray_y = 0.20, BY - LOW_D/2 - 0.22
    add_box('CookwarePull_Base', (tray_x, tray_y, 0.23), (0.78, 0.36, 0.17), pale_int)
    for x in (tray_x-0.32, tray_x+0.32):
        add_box(f'CookwarePull_Rail_{x:.2f}', (x, tray_y, 0.23), (0.018, 0.36, 0.18), rail)
    pan_mat = pbr('Cookware_Dark', (0.08,0.09,0.10), roughness=0.25, metallic=0.86)
    for i, (px, radius) in enumerate([(tray_x-0.14,0.11), (tray_x+0.15,0.15)]):
        add_cylinder(f'CookwarePull_Pan_{i}', (px, tray_y, 0.31), radius, 0.060, pan_mat, 24)
        add_box(f'CookwarePull_Handle_{i}', (px+radius*1.28, tray_y, 0.31), (radius*0.92, 0.030, 0.035), M['black_trim'])

    # Slim oil-and-spice pull-out beside the cooking zone.
    spice_x, spice_y = 1.20, BY - LOW_D/2 - 0.15
    add_box('SpicePull_Base', (spice_x, spice_y, 0.38), (0.22, 0.24, 0.62), pale_int)
    for z in (0.17, 0.40, 0.62):
        add_box(f'SpicePull_Shelf_{z:.2f}', (spice_x, spice_y, z), (0.22, 0.040, 0.020), rail)
    oil_mats = [pbr('Oil_Olive', (0.23,0.37,0.24), roughness=0.18, transmission=0.15), pbr('Oil_Amber', (0.48,0.29,0.12), roughness=0.18, transmission=0.12)]
    for i, (ox, oz, mat) in enumerate([(spice_x-0.06,0.27,oil_mats[0]), (spice_x+0.02,0.44,oil_mats[1]), (spice_x+0.07,0.27,oil_mats[0])]):
        add_cylinder(f'SpicePull_Bottle_{i}', (ox, spice_y, oz), 0.025, 0.17, mat, 12)

    # Porcelain stacks behind the two glass uppers: a small cue of domestic life, not a visual wall.
    plate_mat = pbr('Porcelain_Warm', (0.92, 0.90, 0.86), roughness=0.24, clearcoat=0.12)
    glass_x = -ROOM_W/2 + 0.075 + UPP_D/2
    for i, z in enumerate((1.67, 1.69, 1.71)):
        add_cylinder(f'GlassCab_Plate_{i}', (glass_x, -1.52, z), 0.075-i*0.004, 0.012, plate_mat, 24)


# ═══════════════════════════════════════════════════════════════════════════
#  ISLAND / PENINSULA
# ═══════════════════════════════════════════════════════════════════════════

IX_REF = 0.20   # island / peninsula X (used by accessories too)

def build_island(M):
    IX, IY      = IX_REF, 1.30
    IW, ID, IH  = 1.90, 0.90, 0.92

    # Main walnut body
    add_box('Isl_Body', (IX, IY, IH/2), (IW, ID, IH), M['walnut'])

    # Vertical fluted slat panel on front face (+Y side)
    SLAT_W   = 0.038
    SLAT_GAP = 0.058
    num_slats = int(IW / (SLAT_W + SLAT_GAP)) - 1
    slat_x0   = IX - (num_slats * (SLAT_W + SLAT_GAP)) / 2 + SLAT_W / 2
    for i in range(num_slats):
        sx = slat_x0 + i * (SLAT_W + SLAT_GAP)
        add_box(f'Slat_{i}', (sx, IY + ID/2 + 0.010, IH*0.48),
                (SLAT_W, 0.018, IH * 0.93), M['black_trim'])

    # Open shelf unit (left side, facing camera)
    SHELF_X = IX - IW/2 + 0.215
    add_box('Isl_ShelfSideL', (SHELF_X-0.195, IY, IH/2), (0.024, ID-0.04, IH), M['shelf_wood'])
    add_box('Isl_ShelfSideR', (SHELF_X+0.195, IY, IH/2), (0.024, ID-0.04, IH), M['shelf_wood'])
    for sz, sh in [(0.32, 0.020), (0.58, 0.020), (0.82, 0.020)]:
        add_box(f'Isl_Shelf_{sz}', (SHELF_X, IY, sz), (0.37, ID-0.06, sh), M['shelf_wood'])
    add_box('Isl_ShelfLED', (SHELF_X, IY, 0.42), (0.32, ID-0.10, 0.014), M['led_warm'])

    # Waterfall marble countertop
    add_box('Isl_Top',     (IX, IY, IH + CT_T/2),  (IW+0.07, ID+0.07, CT_T), M['marble'])
    add_box('Isl_TopEdge', (IX, IY, IH + CT_T),    (IW+0.09, ID+0.09, 0.014), M['black_trim'])

    # Waterfall side panel (right end, stone drops to floor)
    add_box('Isl_WaterfallR',
            (IX + IW/2 + CT_T/2 + 0.005, IY, (IH + CT_T) / 2),
            (CT_T, ID + 0.07, IH + CT_T), M['marble'])

    # Props on island top
    tray_mat = pbr('Tray_Wood', (0.38, 0.24, 0.14), roughness=0.60)
    add_box('Isl_Tray', (IX+0.30, IY-0.12, IH+CT_T+0.012), (0.34, 0.24, 0.024), tray_mat)
    mug_mat  = pbr('Mug_White', (0.92, 0.90, 0.88), roughness=0.30)
    add_cylinder('Isl_Mug', (IX+0.30, IY-0.08, IH+CT_T+0.07), 0.036, 0.09, mug_mat, 16)


# ═══════════════════════════════════════════════════════════════════════════
#  APPLIANCES
# ═══════════════════════════════════════════════════════════════════════════

def build_range_hood(M):
    HX  = -0.45
    HY  = -ROOM_D/2 + 0.075 + 0.24
    CT_Z = CT_H + CT_T

    # Chimney
    add_box('Hood_Chimney', (HX, HY, 2.05),       (0.54, 0.10, 0.80), M['black_appliance'])
    # Body (wider lower)
    add_box('Hood_Body',    (HX, HY-0.06, 1.58),  (0.92, 0.42, 0.47), M['black_appliance'])
    # Front rim
    add_box('Hood_Rim',     (HX, HY-0.04, 1.36),  (0.96, 0.44, 0.044), M['black_trim'])
    # Metal filter grille
    add_box('Hood_Filter',  (HX, HY-0.035, 1.382),(0.80, 0.38, 0.018), M['stainless'])
    # Warm LED under hood (existing, retained)
    add_box('Hood_LED',     (HX, HY-0.030, 1.36), (0.72, 0.34, 0.012), M['led_under'])

    # Gas cooktop
    CTX, CTY = HX, -ROOM_D/2 + 0.075 + LOW_D/2
    add_box('Cooktop_Srf', (CTX, CTY, CT_Z+0.012), (0.80, 0.52, 0.024), M['cooktop'])
    for bx, by in [(-0.18, 0.10), (-0.18,-0.10), (0.10, 0.10), (0.10,-0.10)]:
        r_pos = (CTX+bx, CTY+by, CT_Z+0.038)
        add_cylinder(f'Burner_{bx}_{by}',  r_pos, 0.062, 0.028, M['stainless'], 20)
        add_cylinder(f'BGrate_{bx}_{by}',  r_pos, 0.055, 0.042, M['black_trim'],  8)
        add_cylinder(f'BCenter_{bx}_{by}', r_pos, 0.018, 0.052, M['black_appliance'], 8)

    pot_mat = pbr('Pot_DarkMetal', (0.06,0.06,0.06), roughness=0.30, metallic=0.7)
    add_cylinder('Pot_Body',   (CTX-0.18, CTY-0.10, CT_Z+0.12),  0.095, 0.20, pot_mat, 24)
    add_cylinder('Pot_Lid',    (CTX-0.18, CTY-0.10, CT_Z+0.225), 0.098, 0.025, pot_mat, 24)
    add_cylinder('Pot_Handle', (CTX-0.18, CTY-0.10+0.12, CT_Z+0.15), 0.010, 0.22, pot_mat, 8)


def build_sink(M):
    SX = LX + 0.10
    SY = -1.60
    SZ = CT_H + CT_T

    add_box('Sink_Outer', (SX, SY, SZ-0.08),   (0.62, 0.40, 0.17), M['black_sink'])
    add_box('Sink_Inner', (SX, SY, SZ-0.04),   (0.56, 0.34, 0.16), M['black_trim'])
    add_box('Sink_Base',  (SX, SY, SZ-0.165),  (0.50, 0.28, 0.008), M['black_appliance'])

    add_cylinder('Faucet_Riser', (SX+0.06, SY-0.14, SZ+0.18), 0.020, 0.36, M['black_trim'], 14)
    add_box('Faucet_Neck',       (SX+0.06, SY-0.02, SZ+0.355), (0.018, 0.28, 0.018), M['black_trim'])
    add_cylinder('Faucet_Head',  (SX+0.06, SY+0.10, SZ+0.34),  0.024, 0.04, M['black_trim'], 12)

    build_plant('Plant_Sink', SX-0.48, SY, SZ, scale=0.90, M=M)


def build_refrigerator(M):
    RX = ROOM_W/2 - 0.075 - 0.38
    RY = -ROOM_D/2 + 0.075 + 0.38
    RH, RW, RD = 2.82, 0.76, 0.72

    add_box('Fridge_Body',  (RX, RY, RH/2),            (RW, RD, RH),       M['black_appliance'])
    add_box('Fridge_VLine', (RX, RY-RD/2+0.003, RH*0.60),  (0.012, 0.006, RH*0.95), M['black_trim'])
    add_box('Fridge_HLine', (RX, RY-RD/2+0.003, RH*0.625), (RW*0.96, 0.006, 0.008), M['black_trim'])

    for hx in [-0.18, 0.18]:
        add_box(f'Fridge_Hdl_{hx}', (RX+hx, RY-RD/2-0.028, RH*0.72), (0.028, 0.056, 0.50), M['stainless'])

    add_box('Fridge_Disp', (RX+0.22, RY-RD/2-0.001, RH*0.42), (0.18, 0.042, 0.32), M['black_appliance'])
    disp_btn_mat = pbr('DispBtn', (0.22,0.22,0.22), roughness=0.5)
    add_box('Fridge_DispBtn', (RX+0.22, RY-RD/2-0.006, RH*0.42), (0.10, 0.008, 0.14), disp_btn_mat)
    add_box('Fridge_Strip', (RX, RY-RD/2-0.001, RH-0.09), (RW*0.82, 0.010, 0.06), M['stainless'])


# ═══════════════════════════════════════════════════════════════════════════
#  BAR STOOLS
# ═══════════════════════════════════════════════════════════════════════════

def build_bar_stool(tag, x, y, M):
    SH = 0.74

    add_box(f'Stool_{tag}_Seat',      (x, y,       SH+0.08),  (0.46, 0.42, 0.16), M['fabric'])
    add_box(f'Stool_{tag}_BkFabric',  (x, y+0.16,  SH+0.33),  (0.42, 0.065, 0.48), M['fabric'])
    add_box(f'Stool_{tag}_BkFrame',   (x, y+0.165, SH+0.33),  (0.44, 0.035, 0.50), M['black_metal'])

    add_cylinder(f'Stool_{tag}_Stem', (x, y, SH/2),  0.035, SH,   M['black_metal'], 14)
    add_cylinder(f'Stool_{tag}_Base', (x, y, 0.045), 0.28,  0.065, M['black_metal'], 28)
    add_box(f'Stool_{tag}_Taper',     (x, y, 0.12),  (0.095, 0.095, 0.14), M['black_metal'])
    add_cylinder(f'Stool_{tag}_Foot', (x, y, SH*0.38), 0.12, 0.018, M['black_metal'], 20)


# ═══════════════════════════════════════════════════════════════════════════
#  PENDANT LIGHTS (Edison, existing coned pendants)
# ═══════════════════════════════════════════════════════════════════════════

def build_pendant(tag, x, y, M):
    TOP_Z = ROOM_H - 0.06
    CORD  = 0.65
    PH    = 0.34
    PZ    = TOP_Z - CORD - PH/2

    add_cylinder(f'Pend_{tag}_Can',   (x, y, TOP_Z-0.016), 0.048, 0.032, M['black_metal'], 14)
    add_cylinder(f'Pend_{tag}_Cord',  (x, y, TOP_Z-CORD/2-0.032), 0.006, CORD, M['black_metal'], 6)
    add_cylinder(f'Pend_{tag}_Shade', (x, y, PZ),           0.068, PH,   M['black_metal'], 24)

    gm = pbr(f'Pend_{tag}_GlMat', (0.90, 0.84, 0.70), roughness=0.02,
             transmission=0.88, ior=1.52, alpha=0.10)
    set_blend(gm)
    add_cylinder(f'Pend_{tag}_Glass', (x, y, PZ), 0.060, PH-0.012, gm, 24)
    add_cylinder(f'Pend_{tag}_Bulb',  (x, y, PZ+PH*0.22), 0.022, 0.088, M['bulb'], 14)


# ═══════════════════════════════════════════════════════════════════════════
#  RECESSED CEILING LIGHTS
# ═══════════════════════════════════════════════════════════════════════════

def build_recessed_light(tag, x, y, M):
    DROP = 0.22
    Z    = ROOM_H - DROP - 0.038
    rim_mat = pbr(f'Rim_{tag}', (0.08, 0.08, 0.08), roughness=0.35)
    add_cylinder(f'Rec_{tag}_Rim',  (x, y, Z+0.020), 0.068, 0.038, rim_mat,  22)
    add_cylinder(f'Rec_{tag}_Lens', (x, y, Z+0.008), 0.056, 0.010, M['led_recess'], 22)


# ═══════════════════════════════════════════════════════════════════════════
#  PLANTS & ACCESSORIES
# ═══════════════════════════════════════════════════════════════════════════

def build_plant(tag, x, y, z, scale, M):
    add_cylinder(f'Plt_{tag}_Pot', (x, y, z+0.10*scale), 0.085*scale, 0.20*scale, M['pot'], 16)
    soil_mat = pbr(f'Soil_{tag}', (0.18, 0.12, 0.08), roughness=0.95)
    add_box(f'Plt_{tag}_Soil', (x, y, z+0.20*scale), (0.14*scale, 0.14*scale, 0.022*scale), soil_mat)
    for i, (lx, ly, lz, ls) in enumerate([
        (0.00,  0.00,  0.30*scale, 0.14*scale),
        (0.06*scale,  0.04*scale, 0.40*scale, 0.11*scale),
        (-0.05*scale,-0.03*scale, 0.38*scale, 0.10*scale),
        (0.02*scale, -0.06*scale, 0.46*scale, 0.09*scale),
    ]):
        leaf_m = pbr(f'Leaf_{tag}_{i}', (0.10+i*0.01, 0.30+i*0.02, 0.10), roughness=0.80,
                     subsurface=0.06, subsurface_color=(0.20, 0.55, 0.18))
        add_cylinder(f'Plt_{tag}_L{i}', (x+lx, y+ly, z+lz), ls*0.80, ls*0.70, leaf_m, 10)


def build_accessories(M):
    CT_Z = CT_H + CT_T

    # Cutting boards on back counter
    cb_mat = pbr('CuttingBoard', (0.46, 0.30, 0.16), roughness=0.62)
    add_box('CB1', (-0.20, -ROOM_D/2+0.075+LOW_D*0.45, CT_Z+0.010), (0.32, 0.22, 0.020), cb_mat)
    add_box('CB2', (-0.22, -ROOM_D/2+0.075+LOW_D*0.45, CT_Z+0.022), (0.28, 0.18, 0.016), cb_mat)

    # Spice bottles (back counter)
    spice_mat = pbr('Spice_Glass', (0.55,0.48,0.35), roughness=0.05,
                    transmission=0.6, ior=1.52, alpha=0.5)
    set_blend(spice_mat)
    lid_mat = pbr('Spice_Lid', (0.10,0.10,0.10), roughness=0.4, metallic=0.5)
    for i, sx in enumerate([-0.55, -0.46, -0.37, -0.27, -0.17]):
        h = 0.12 + (i % 2) * 0.03
        add_cylinder(f'Spice_{i}',    (sx, -ROOM_D/2+0.075+LOW_D*0.36, CT_Z+h/2+0.001), 0.030, h, spice_mat, 14)
        add_cylinder(f'SpiceLid_{i}', (sx, -ROOM_D/2+0.075+LOW_D*0.36, CT_Z+h+0.008),  0.032, 0.016, lid_mat, 14)

    # Bowls on island shelves
    bowl_mat   = pbr('Bowl_White',  (0.92, 0.90, 0.88), roughness=0.25)
    basket_mat = pbr('Basket',      (0.55, 0.42, 0.28), roughness=0.90)
    add_cylinder('Bowl1',    (IX_REF-0.22, 1.30, 0.38), 0.075, 0.065, bowl_mat, 18)
    add_cylinder('Basket1',  (IX_REF-0.22, 1.30, 0.62), 0.065, 0.080, basket_mat, 10)
    build_plant('Isl', IX_REF-0.22, 1.30, 0.82, scale=0.65, M=M)

    # Decor on right tower shelf
    vase_mat = pbr('Vase_Dark', (0.12, 0.10, 0.08), roughness=0.35)
    add_cylinder('Vase1',    (ROOM_W/2-0.075-0.22, -1.20, 2.25), 0.055, 0.18, vase_mat, 16)
    build_plant('Tower', ROOM_W/2-0.075-0.22, -1.20, 1.68, scale=0.55, M=M)


# ═══════════════════════════════════════════════════════════════════════════
#  KITCHEN DECOR LIGHTS
#  Integrates KitchenDecorLights from KitchenScene.tsx:
#    • Under-cabinet cool LED strips — back wall + left wall  (#deeeff)
#    • Toe-kick warm LED strips — back wall + left wall  (#ffd088)
#    • Range-hood interior cool LED strip
#    • Display-niche LED shelf strip + accent spot
#    • Linear LED pendant above peninsula
#        – anodised housing + frosted diffuser + ceiling-bounce strip
#        – three suspension cables
#        – downward pool + upward ceiling bounce point lights
#    • Peninsula waterfall-side warm LED strip
#
#  Blender coordinate convention used throughout:
#    X = left(-) / right(+),  Y = back(-3) / front(+3),  Z = up
#  Three.js → Blender:  x→X,  z→Y  (same sign, back=-3 / front=+3),  y→Z
# ═══════════════════════════════════════════════════════════════════════════

def build_decor_lights(M):

    # ── Shared geometry constants ────────────────────────────────────────
    # Front face of back-wall upper cabinets (Y axis)
    uc_front_Y = -ROOM_D/2 + UPP_D + 0.04 + 0.075    # ≈ -2.61
    # Front face of left-wall upper cabinets (X axis)
    uc_front_X = -ROOM_W/2 + UPP_D + 0.04 + 0.075    # ≈ -3.09
    # Z just below the underside of upper cabs
    uc_Z       = UPP_Z - 0.015                         # ≈ 1.465

    # ── UNDER-CABINET COOL LED STRIPS — back wall run ────────────────────
    # Emissive strip at bottom-front edge of back-wall upper cabs, cool white
    # Three.js: Box p=[(ucXStart+ucXEnd)/2, ucY, ucFrontZ-0.01] s=[3.6, 0.012, 0.016]
    add_box('UCab_Cool_Back',
            (0.10, uc_front_Y - 0.01, uc_Z),
            (3.60, 0.020, 0.012),
            M['led_cool'])

    # Point lights washing down onto back countertop
    add_point_light('UCab_Cool_B1',
                    (-1.20, uc_front_Y + 0.12, uc_Z - 0.12),
                    energy=95, color=(0.87, 0.94, 1.0), size=0.06)
    add_point_light('UCab_Cool_B2',
                    ( 0.60, uc_front_Y + 0.12, uc_Z - 0.12),
                    energy=95, color=(0.87, 0.94, 1.0), size=0.06)

    # ── UNDER-CABINET COOL LED STRIPS — left wall run ─────────────────────
    # Three.js: Box p=[-W/2+UPP_D/2+0.04, ucY, -0.6] s=[0.016, 0.012, 2.2]
    add_box('UCab_Cool_Left',
            (uc_front_X - 0.01, -0.50, uc_Z),
            (0.012, 2.60, 0.012),
            M['led_cool'])

    add_point_light('UCab_Cool_L1',
                    (uc_front_X + 0.12, -0.50, uc_Z - 0.12),
                    energy=75, color=(0.87, 0.94, 1.0), size=0.06)

    # ── TOE-KICK WARM LED STRIPS — back wall ─────────────────────────────
    # Three.js: Box p=[0, 0.04, -D/2+0.04] s=[W-1.6, 0.018, 0.01]
    add_box('ToeKick_Back',
            (0.10, -ROOM_D/2 + 0.04, 0.038),
            (4.50, 0.012, 0.020),
            M['led_toekick'])

    add_point_light('ToeKick_B1', (-1.00, -ROOM_D/2 + 0.16, 0.055),
                    energy=40, color=(1.0, 0.82, 0.53), size=0.05)
    add_point_light('ToeKick_B2', ( 1.00, -ROOM_D/2 + 0.16, 0.055),
                    energy=40, color=(1.0, 0.82, 0.53), size=0.05)

    # ── TOE-KICK WARM LED STRIPS — left wall ─────────────────────────────
    # Three.js: Box p=[-W/2+0.04, 0.04, -0.6] s=[0.01, 0.018, 2.2]
    add_box('ToeKick_Left',
            (-ROOM_W/2 + 0.04, -0.50, 0.038),
            (0.012, 2.60, 0.020),
            M['led_toekick'])

    add_point_light('ToeKick_L1', (-ROOM_W/2 + 0.16, -0.50, 0.055),
                    energy=40, color=(1.0, 0.82, 0.53), size=0.05)

    # ── RANGE HOOD INTERIOR COOL LED ─────────────────────────────────────
    # Thin cool strip inside the hood opening, washing down onto range
    # Three.js: Box p=[-0.55, 1.98, -D/2+0.3] (using hood X, not -1.5)
    HX = -0.45
    HY = -ROOM_D/2 + 0.075 + 0.24
    add_box('Hood_IntCoolLED',
            (HX, HY - 0.04, 1.360),
            (0.70, 0.08, 0.010),
            M['led_cool'])

    add_point_light('Hood_IntCool_Pt',
                    (HX, HY + 0.02, 1.355),
                    energy=130, color=(0.91, 0.96, 1.0), size=0.08)

    # ── DISPLAY NICHE ACCENT SPOT ─────────────────────────────────────────
    # Three.js: spotLight at (2.3, H-0.05, -D/2+0.5) →target (2.3, 1.4, -D/2+0.05)
    # Blender: niche right of centre, near back wall
    NX = 2.10
    NY = -ROOM_D/2 + 0.36   # ≈ -2.64

    # LED shelf strip inside niche (warm)
    # Three.js: Box p=[2.3, 1.55, -D/2+0.14]
    add_box('Niche_LED_Strip',
            (NX, NY - 0.10, 1.55),
            (0.72, 0.014, 0.010),
            M['led_niche'])

    # Spot light from near the ceiling angled at niche contents
    bpy.ops.object.light_add(type='SPOT',
                             location=(NX, NY + 0.55, ROOM_H - 0.10))
    niche_spot      = bpy.context.active_object
    niche_spot.name = 'Niche_Spot'
    niche_spot.data.energy           = 300
    niche_spot.data.color            = (1.0, 0.97, 0.91)
    niche_spot.data.spot_size        = math.radians(30)
    niche_spot.data.spot_blend       = 0.80
    niche_spot.data.shadow_soft_size = 0.04
    niche_spot.data.use_shadow       = True
    # Aim toward niche back wall — rotated to point back and slightly down
    niche_spot.rotation_euler = Euler([math.radians(r) for r in (50, 0, 0)])

    # ── LINEAR LED PENDANT above peninsula ───────────────────────────────
    # Three.js: housing at [-0.35, H-0.52, 0.92] s=[1.4, 0.04, 0.08]
    # Blender PIX/PIY match existing build_island IX=0.20, IY=1.30
    PIX, PIY = IX_REF, 1.30
    PHZ      = ROOM_H - 0.52     # housing bottom-centre Z  ≈ 2.33

    # Anodised aluminium housing (#1c1a18 — near black)
    add_box('LinPend_Housing',
            (PIX, PIY, PHZ),
            (1.40, 0.08, 0.040),
            M['lin_housing'])

    # Bottom emissive diffuser (faces down, warm white)
    # Three.js: s=[1.32, 0.008, 0.065] → narrow in Z (up), wide in X
    add_box('LinPend_Diffuser',
            (PIX, PIY, PHZ - 0.026),
            (1.32, 0.065, 0.008),
            M['lin_diffuser'])

    # Top bounce strip — washes ceiling upward
    # Three.js: Box p=[-0.35, H-0.498, 0.92] — slightly above housing centre
    add_box('LinPend_TopBounce',
            (PIX, PIY, PHZ + 0.022),
            (1.32, 0.065, 0.006),
            M['lin_diffuser'])

    # Suspension cables × 3 (vertical cylinders from ceiling to housing top)
    # Three.js: cx ∈ [-0.6, -0.35, -0.1] from pendant centre x=-0.35
    #           → Blender: PIX + offset where offsets are (-0.25, 0, +0.25)
    cable_xs       = [PIX - 0.50, PIX, PIX + 0.50]
    cable_top_Z    = ROOM_H - 0.04
    cable_bot_Z    = PHZ + 0.020
    cable_len      = cable_top_Z - cable_bot_Z        # ≈ 0.47
    cable_centre_Z = (cable_top_Z + cable_bot_Z) / 2

    cable_mat = pbr('LinPend_Cable', (0.16, 0.14, 0.12), roughness=0.50, metallic=0.70)
    for i, cx in enumerate(cable_xs):
        add_cylinder(f'LinPend_Cable_{i}',
                     (cx, PIY, cable_centre_Z),
                     0.003, cable_len, cable_mat, 6)

    # Ceiling canopy discs at cable tops
    canopy_mat = pbr('LinPend_Canopy', (0.12, 0.11, 0.10), roughness=0.40, metallic=0.75)
    for i, cx in enumerate(cable_xs):
        add_cylinder(f'LinPend_Canopy_{i}',
                     (cx, PIY, ROOM_H - 0.018),
                     0.028, 0.022, canopy_mat, 12)

    # Downward pool light (strong warm, illuminates peninsula countertop)
    # Three.js: intensity=10 at [−0.35, H−0.62, 0.92]
    add_point_light('LinPend_Down',
                    (PIX, PIY, PHZ - 0.08),
                    energy=380, color=(1.0, 0.80, 0.50), size=0.10)

    # Upward ceiling bounce (softer, warm)
    # Three.js: intensity=3 at [−0.35, H−0.48, 0.92]
    add_point_light('LinPend_Up',
                    (PIX, PIY, PHZ + 0.025),
                    energy=110, color=(1.0, 0.87, 0.67), size=0.08)

    # ── PENINSULA WATERFALL-SIDE WARM LED STRIP ───────────────────────────
    # Under the stone waterfall edge on the right end of the peninsula.
    # Three.js: Box p=[1.15, 0.9+0.04/2, 0.92] s=[0.01, 0.016, 0.58]
    #           x=1.15 → right edge of peninsula; y≈0.92 (near top); z→Y=IY
    IW_bl = 1.90   # matches build_island
    IH_bl = 0.92
    wf_X  = PIX + IW_bl / 2 + CT_T / 2 + 0.005   # ≈ 1.175  right waterfall X
    add_box('Penin_WF_LED',
            (wf_X, PIY, IH_bl / 2 + CT_T / 2),    # mid-height of waterfall panel
            (0.010, 0.60, 0.016),
            M['led_toekick'])

    # Point light illuminating the floor and right side below the waterfall
    # Three.js: intensity=1.8 at [1.06, 0.5, 0.92]
    add_point_light('Penin_WF_Pt',
                    (wf_X - 0.08, PIY, 0.46),
                    energy=48, color=(1.0, 0.82, 0.53), size=0.05)


# ═══════════════════════════════════════════════════════════════════════════
#  LIGHTING
#  Intensities reduced to match Three.js Lighting proportions:
#    directional 1.4 · ambient 0.18 · hemisphere 0.32
#    recessed 5 each · pendant pools 8 each
# ═══════════════════════════════════════════════════════════════════════════

def setup_lighting():
    # ── World (ambient + hemisphere) ────────────────────────────────────
    world = bpy.data.worlds['World']
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    bg  = wn.new('ShaderNodeBackground')
    out = wn.new('ShaderNodeOutputWorld')
    # ambient 0.18 in Three.js → Blender world strength ≈ 0.18
    bg.inputs['Color'].default_value    = (0.10, 0.09, 0.08, 1.0)
    bg.inputs['Strength'].default_value = 0.18
    wl.new(bg.outputs['Background'], out.inputs['Surface'])

    # ── Daylight through window (directional 1.4 in Three.js) ───────────
    # Area light simulates a directional sun from the left wall window.
    # Original 900 W → scaled by 1.4/2.0 ≈ 0.70 → 630 W
    add_light('Win_Sun',    'AREA',
              (-3.6, -1.1, 1.50), 630,
              color=(0.80, 0.90, 1.0), size=1.20, size_y=1.0, rot=(0, 90, 0))

    # Sky-fill bounce from window
    add_light('Win_Bounce', 'AREA',
              (-2.2, -0.5, 1.80), 126,
              color=(0.78, 0.85, 1.0), size=2.0, size_y=1.5, rot=(0, 90, 0))

    # Hemisphere fill (0.32 in Three.js → cove area reduced 30 %)
    # Cove warm ambient: original 240 W → 168 W
    add_light('Cove_Amb',   'AREA',
              (0, 0, ROOM_H - 0.28), 168,
              color=(1.0, 0.86, 0.62), size=5.2, size_y=4.0, rot=(0, 0, 0))

    # Under-cabinet back (warm strip) — existing, slightly reduced
    add_light('UCab_B',     'AREA',
              (0.12, -2.60, 1.455), 105,
              color=(1.0, 0.88, 0.68), size=3.8, size_y=0.30, rot=(90, 0, 0))

    # Under-cabinet left (warm strip)
    add_light('UCab_L',     'AREA',
              (-3.22, -0.50, 1.455), 90,
              color=(1.0, 0.88, 0.68), size=2.6, size_y=0.30, rot=(90, 0, 90))

    # ── Pendant light pools (Three.js intensity=8 each) ─────────────────
    # Original 65 W → scaled by 8/~10 ≈ 0.80 → 48 W
    # (actual Watts tuned so real Blender result looks like Three.js render)
    add_light('Pend_L', 'POINT',
              (-0.35, 1.05, 2.04), 48, color=(1.0, 0.78, 0.44), size=0.05)
    add_light('Pend_R', 'POINT',
              ( 0.55, 1.05, 2.04), 48, color=(1.0, 0.78, 0.44), size=0.05)

    # Hood LED area
    add_light('Hood_LED_Area', 'AREA',
              (-0.45, -ROOM_D/2+0.28, 1.355), 63,
              color=(1.0, 0.88, 0.70), size=0.72, size_y=0.28, rot=(90, 0, 0))

    # ── Recessed downlights (Three.js intensity=5 each) ─────────────────
    # Original 32 W → 5/8 * 32 ≈ 20 W; tuned to 22 W for Blender
    recessed_positions = [
        (-1.8, -1.8), (-1.8,  0.0), (-1.8,  1.8),
        ( 0.0, -1.8), ( 0.0,  0.0),
        ( 1.8, -1.8), ( 1.8,  0.0), ( 1.8,  1.5),
    ]
    for i, (rx, ry) in enumerate(recessed_positions):
        add_light(f'Rec_{i}', 'POINT',
                  (rx, ry, ROOM_H - 0.26), 22,
                  color=(1.0, 0.93, 0.82), size=0.07)

    # Soft fill from camera direction
    add_light('Fill_Cam', 'AREA',
              (0.5, 4.0, 1.85), 70,
              color=(0.92, 0.92, 1.0), size=3.5, size_y=2.5, rot=(-28, 0, 0))


# ═══════════════════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════════════════

def setup_camera():
    bpy.ops.object.camera_add(location=(2.90, 3.90, 1.68))
    cam = bpy.context.active_object
    cam.name = 'Cam_Main'
    cam.rotation_euler = Euler([math.radians(r) for r in (81.5, 0, 153)])
    cam.data.lens            = 28
    cam.data.clip_start      = 0.1
    cam.data.clip_end        = 50
    cam.data.dof.use_dof     = True
    cam.data.dof.focus_distance  = 4.3
    cam.data.dof.aperture_fstop  = 5.6
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
    scene.render.filepath            = '//kitchen_render.png'

    # Filmic color management
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look           = 'Medium High Contrast'
    scene.view_settings.exposure        = 0.45
    scene.view_settings.gamma           = 1.05


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  Building Modern Luxury Kitchen Scene  v2")
    print("=" * 60)

    clear_scene()
    setup_render()

    print("Creating materials...")
    M = create_materials()

    print("Building room...")
    build_room(M)

    print("Building cabinets...")
    build_cabinets(M)
    print("Adding integrated dishwasher and cabinet storage details...")
    build_cabinet_living_details(M)

    print("Building island / peninsula...")
    build_island(M)

    print("Building appliances...")
    build_range_hood(M)
    build_sink(M)
    build_refrigerator(M)

    print("Building bar stools...")
    build_bar_stool('L', -0.52, 2.08, M)
    build_bar_stool('R',  0.52, 2.08, M)

    print("Building Edison pendant lights...")
    build_pendant('L', -0.35, 1.05, M)
    build_pendant('R',  0.55, 1.05, M)

    print("Building recessed ceiling light geometry...")
    recessed = [(-1.8,-1.8),(0.0,-1.8),(1.8,-1.8),
                (-1.8, 0.0),(0.0, 0.0),
                ( 1.8, 1.5),(1.8, 0.0)]
    for i, (rx, ry) in enumerate(recessed):
        build_recessed_light(f'{i}', rx, ry, M)

    print("Building accessories & plants...")
    build_accessories(M)

    print("Building decorative LED lights (KitchenDecorLights)...")
    build_decor_lights(M)

    print("Setting up global lighting...")
    setup_lighting()

    print("Setting up camera...")
    setup_camera()

    total_obj = len(bpy.data.objects)
    total_mat = len(bpy.data.materials)
    print(f"\n  Scene complete: {total_obj} objects | {total_mat} materials")
    print("  Press F12 to render  |  Output: //kitchen_render.png")
    print("=" * 60 + "\n")


main()
