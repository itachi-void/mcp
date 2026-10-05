"""Shared helpers: version pin, config, colour conversion, safe collections,
geometry primitives and Blender 4.4+/5.x-safe F-curve access.

Nothing in this module deletes data it did not create.
"""

import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OWNED = "apt_owned"  # custom prop that marks data created by this pipeline


def load_config():
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as fh:
        return json.load(fh)


def assert_version(M):
    allowed = [tuple(v) for v in M["blender_versions"]]
    if bpy.app.version[:2] not in allowed:
        pins = ", ".join(f"{a}.{b}.x" for a, b in allowed)
        raise RuntimeError(f"apartment pipeline is pinned to Blender {pins}, running {bpy.app.version_string}")


# --- colour -----------------------------------------------------------------

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    """Proper sRGB EOTF for every material colour (one rule for all rooms)."""
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


def kelvin_to_linear(k):
    """Tanner Helland blackbody approximation, returned as linear RGB."""
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = (99.4708025861 * math.log(t) - 161.1195681661) if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    return tuple(srgb_to_linear(max(0.0, min(255.0, c)) / 255.0) for c in (r, g, b))


# --- collections ------------------------------------------------------------

def _remove_owned_tree(coll):
    for child in list(coll.children):
        _remove_owned_tree(child)
    for obj in list(coll.objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is not None and data.users == 0:
            for kind, store in ((bpy.types.Mesh, bpy.data.meshes), (bpy.types.Curve, bpy.data.curves),
                                (bpy.types.Light, bpy.data.lights), (bpy.types.Camera, bpy.data.cameras)):
                if isinstance(data, kind):
                    store.remove(data)
                    break
    bpy.data.collections.remove(coll)


def fresh_collection(name, parent):
    """Create (or rebuild) a pipeline-owned collection. Only a collection that
    this pipeline created earlier is ever removed, never user collections."""
    old = bpy.data.collections.get(name)
    if old is not None:
        if not old.get(OWNED):
            raise RuntimeError(f"collection '{name}' exists and is not pipeline-owned; refusing to touch it")
        _remove_owned_tree(old)
    coll = bpy.data.collections.new(name)
    coll[OWNED] = True
    parent.children.link(coll)
    return coll


def link(obj, coll):
    coll.objects.link(obj)
    obj[OWNED] = True
    return obj


# --- geometry ---------------------------------------------------------------

def _mesh_object(name, coll, bm, mat, location=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat is not None:
        me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    return link(obj, coll)


def box(name, coll, center, size, mat, bevel=0.004, parent=None):
    """Axis-aligned box with real-size vertices (no object scale), so
    object-space procedural textures keep one texel density everywhere."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    obj = _mesh_object(name, coll, bm, mat, center)
    if bevel:
        add_bevel(obj, bevel)
    if parent is not None:
        set_parent(obj, parent)
    return obj


def cylinder(name, coll, center, radius, depth, mat, segments=40, parent=None, bevel=0.003):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth)
    obj = _mesh_object(name, coll, bm, mat, center)
    for p in obj.data.polygons:
        p.use_smooth = True
    if bevel:
        add_bevel(obj, bevel)
    if parent is not None:
        set_parent(obj, parent)
    return obj


def sphere(name, coll, center, radius, mat, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=radius)
    obj = _mesh_object(name, coll, bm, mat, center)
    for p in obj.data.polygons:
        p.use_smooth = True
    if parent is not None:
        set_parent(obj, parent)
    return obj


def ring(name, coll, center, radius, thickness, mat, parent=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = thickness
    cu.bevel_resolution = 6
    sp = cu.splines.new("NURBS")
    pts = 8
    sp.points.add(pts - 1)
    for i in range(pts):
        a = 2 * math.pi * i / pts
        sp.points[i].co = (radius * math.cos(a), radius * math.sin(a), 0.0, 1.0)
    sp.use_cyclic_u = True
    sp.order_u = 4
    if mat is not None:
        cu.materials.append(mat)
    obj = link(bpy.data.objects.new(name, cu), coll)
    obj.location = center
    if parent is not None:
        set_parent(obj, parent)
    return obj


def add_bevel(obj, width):
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = 2
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    return mod


def empty(name, coll, location=(0, 0, 0), rot_z_deg=0.0, size=0.25, kind="PLAIN_AXES"):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = kind
    obj.empty_display_size = size
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
    return link(obj, coll)


def set_parent(child, parent):
    """Parent while keeping the child's coordinates *local* to the parent."""
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)


def group(name, coll, location, rot_z_deg=0.0):
    """Furniture group: children are authored in local metres, front = +Y."""
    return empty(name, coll, location, rot_z_deg, size=0.3, kind="CUBE")


def ray_visibility(obj, camera=True, shadow=True, diffuse=True, glossy=True, transmission=True):
    obj.visible_camera = camera
    obj.visible_shadow = shadow
    obj.visible_diffuse = diffuse
    obj.visible_glossy = glossy
    obj.visible_transmission = transmission


# --- animation (Blender 4.4+ layered actions, works on 5.x) -----------------

def fcurves(id_data):
    ad = id_data.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    if bpy.app.version >= (4, 4, 0):
        from bpy_extras import anim_utils
        bag = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(bag.fcurves) if bag else []
    return list(act.fcurves)


def find_fcurve(id_data, data_path, index=0):
    for fc in fcurves(id_data):
        if fc.data_path == data_path and fc.array_index == index:
            return fc
    return None


def look_quat(src, dst):
    return (Vector(dst) - Vector(src)).to_track_quat("-Z", "Y")


def evaluated_matrix(scene, obj, frame):
    """World matrix of obj at frame, evaluated in *scene's* own depsgraph
    (works for non-active scenes and in background mode)."""
    scene.frame_set(frame)
    dg = scene.view_layers[0].depsgraph
    dg.update()
    return obj.evaluated_get(dg).matrix_world.copy(), dg
