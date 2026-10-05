"""Set dressing with CC0 Poly Haven models (fetch_assets.py). Each model is
appended once into a hidden source collection and placed as collection
instances on top of / next to a named anchor object, so the layout survives
furniture moves. Missing downloads are skipped, never fatal."""

import json
import math
import os

import bpy
from mathutils import Vector

from .common import HERE, OWNED, link

ROOT = os.path.join(HERE, "..", "assets", "models")


def _source(pid, lib):
    coll = bpy.data.collections.get(f"SRC_{pid}")
    if coll is not None:
        return coll
    path = os.path.join(ROOT, pid, f"{pid}.blend")
    if not os.path.exists(path):
        return None
    with bpy.data.libraries.load(path, link=False, relative=False) as (src, dst):
        dst.objects = list(src.objects)
    coll = bpy.data.collections.new(f"SRC_{pid}")
    coll[OWNED] = True
    lib.children.link(coll)
    for o in dst.objects:
        # Poly Haven files carry hidden helper meshes (e.g. "Sphere_stash"): skip them
        if o is not None and o.type in {"MESH", "EMPTY", "CURVE"} and not o.hide_render and "stash" not in o.name.lower():
            coll.objects.link(o)
    # put the model's bottom-centre on the origin so placement is exact
    pts = [o.matrix_world @ Vector(c) for o in coll.objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    coll.instance_offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    return coll


def _top(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return max(p.z for p in pts)


def build(apt_coll):
    with open(os.path.join(HERE, "sourcing.json"), encoding="utf-8") as fh:
        S = json.load(fh)
    lib = bpy.data.collections.new("DRESSING_SRC")  # not in any scene: only instanced
    lib[OWNED] = True
    lib.use_fake_user = True
    out = bpy.data.collections.new("DRESSING")
    out[OWNED] = True
    apt_coll.children.link(out)
    bpy.context.view_layer.update()
    placed, skipped = [], []
    for i, d in enumerate(S["dressing"]):
        anchor = bpy.data.objects.get(d["anchor"])
        src = _source(d["model"], lib)
        if anchor is None or src is None:
            skipped.append(d["model"])
            continue
        base = anchor.matrix_world.translation
        z = _top(anchor) if d["on"] == "top" else 0.0
        inst = bpy.data.objects.new(f"DRESS_{i:02d}_{d['model']}", None)
        inst.instance_type = "COLLECTION"
        inst.instance_collection = src
        inst.location = (base.x + d["dx"], base.y + d["dy"], z)
        inst.rotation_euler.z = math.radians(d["rot"])
        inst.scale = (d.get("scale", 1.0),) * 3
        link(inst, out)
        if d.get("replace"):
            for o in [anchor] + list(anchor.children_recursive):
                o.hide_render = o.hide_viewport = True
        placed.append(d["model"])
    return {"placed": placed, "skipped": skipped}
