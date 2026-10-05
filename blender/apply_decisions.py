"""Swap the size-exact proxies for the real approved assets (Door02, Freedom
Sofa, Rembrandt scan). Runs on the machine that holds the heavy files.

    # 1) find candidates and report their real sizes (read-only)
    blender -b --factory-startup -P blender/apply_decisions.py -- scan <dir> [<dir> ...]

    # 2) validate + install (writes apartment_final.blend, never touches the master)
    blender -b blender/apartment_master.blend -P blender/apply_decisions.py -- apply assets_map.json

assets_map.json (paths may be absolute, objects are names inside the .blend):
    {"door02":       {"file": "D:/lib/Door02.blend",      "object": "Door02"},
     "freedom_sofa": {"file": "D:/lib/FreedomSofa.blend", "object": "FreedomSofa"},
     "rembrandt":    {"image": "D:/lib/rembrandt.jpg"}}

Every step prints one JSON line and the run ends with apply_report.json.
Exit code: 0 all installed, 2 something failed validation (nothing saved).
"""

import json
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apartment import common  # noqa: E402

MESH_EXT = (".blend", ".glb", ".gltf", ".fbx", ".obj", ".usd", ".usdc", ".usdz")
IMG_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr")


def log(**kw):
    print("APPLY " + json.dumps(kw, ensure_ascii=False), flush=True)


# --- geometry helpers ---------------------------------------------------------

def world_bbox(objs):
    pts = []
    for o in objs:
        if o.type in {"MESH", "CURVE", "SURFACE", "FONT"}:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    if not pts:
        return None, None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def hierarchy(root):
    out = [root]
    for c in root.children_recursive:
        out.append(c)
    return out


def dims_match(got, want, tol):
    """Compare sorted footprint (x/y may be swapped by authoring) + exact height."""
    g_xy, w_xy = sorted(got[:2]), sorted(want[:2])
    errs = [abs(a - b) for a, b in zip(g_xy, w_xy)] + [abs(got[2] - want[2])]
    return max(errs) <= tol, round(max(errs), 3)


# --- loading ------------------------------------------------------------------

def load_blend_object(path, name):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        if name not in src.objects:
            raise LookupError(f"object '{name}' not in {path}; has: {src.objects[:20]}")
        dst.objects = [name]
    root = dst.objects[0]
    # pull in its children too
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n != name]
    kids = [o for o in dst.objects if o is not None]
    keep = {root} | {o for o in kids if _descends(o, root)}
    for o in kids:
        if o not in keep:
            bpy.data.objects.remove(o)
    return root, list(keep)


def _descends(o, root):
    p = o.parent
    while p is not None:
        if p == root:
            return True
        p = p.parent
    return False


def load_generic(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        bpy.ops.wm.usd_import(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None or o.parent not in new]
    if len(roots) == 1:
        return roots[0], new
    root = bpy.data.objects.new(os.path.basename(path), None)
    bpy.context.scene.collection.objects.link(root)
    for r in roots:
        r.parent = root
    return root, new + [root]


# --- scan ---------------------------------------------------------------------

def scan(dirs):
    M = common.load_config()
    keys = {"door02": ("door",), "freedom_sofa": ("freedom", "sofa"), "rembrandt": ("rembrandt",)}
    found = []
    for d in dirs:
        for dp, _dn, files in os.walk(d):
            for f in files:
                low = f.lower()
                for k, words in keys.items():
                    if any(w in low for w in words) and low.endswith(MESH_EXT + IMG_EXT):
                        p = os.path.join(dp, f)
                        found.append({"asset": k, "path": p, "mb": round(os.path.getsize(p) / 1e6, 1)})
    for c in found:
        p = c["path"]
        try:
            if p.lower().endswith(IMG_EXT):
                img = bpy.data.images.load(p)
                c["px"] = list(img.size)
                c["ok"] = max(img.size) >= M["assets"]["rembrandt"]["min_long_edge_px"]
            elif p.lower().endswith(".blend"):
                with bpy.data.libraries.load(p) as (src, _dst):
                    c["objects"] = list(src.objects)[:30]
        except Exception as e:  # noqa: BLE001
            c["error"] = str(e)
        log(step="scan", **c)
    with open(os.path.join(HERE, "scan_report.json"), "w", encoding="utf-8") as fh:
        json.dump(found, fh, indent=1, ensure_ascii=False)


# --- apply --------------------------------------------------------------------

def install_mesh(M, key, spec, coll):
    a = M["assets"][key]
    proxy = bpy.data.objects.get(a["proxy"])
    if proxy is None:
        raise LookupError(f"proxy {a['proxy']} missing — open apartment_master.blend")
    path = spec["file"]
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if path.lower().endswith(".blend"):
        root, objs = load_blend_object(path, spec.get("object", a["object"]))
    else:
        root, objs = load_generic(path)
    for o in objs:
        if not o.users_collection:
            coll.objects.link(o)
    root.parent = None
    root.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()

    lo, hi = world_bbox(objs)
    if lo is None:
        raise ValueError("asset has no geometry")
    dims = list(hi - lo)
    # unit fix: centimetre / millimetre exports
    for factor in (1.0, 0.01, 0.001):
        ok, err = dims_match([d * factor for d in dims], a["expected_dims"], a["tolerance"])
        if ok:
            break
    if not ok:
        for o in objs:
            bpy.data.objects.remove(o)
        return {"asset": key, "ok": False, "dims": [round(d, 3) for d in dims],
                "expected": a["expected_dims"], "err": err}
    root.scale = (factor,) * 3
    # footprint swapped? rotate 90 so long side follows the proxy's X
    if (dims[0] < dims[1]) != (a["expected_dims"][0] < a["expected_dims"][1]):
        root.rotation_euler.z += 1.5707963
    bpy.context.view_layer.update()
    lo, hi = world_bbox(objs)
    bottom_center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    # put asset's bottom-centre on the proxy's bottom-centre, same yaw
    plo, phi = world_bbox(hierarchy(proxy))
    target = Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, plo.z))
    yaw = proxy.matrix_world.to_euler().z
    root.location -= bottom_center
    holder = bpy.data.objects.new(f"{a['proxy']}_REAL", None)
    coll.objects.link(holder)
    root.parent = holder
    holder.location = target
    holder.rotation_euler.z = yaw
    holder["asset"] = key
    holder["source"] = path
    for o in hierarchy(proxy):
        o.hide_render = o.hide_viewport = True
    return {"asset": key, "ok": True, "scale": factor, "err": err,
            "dims": [round(d * factor, 3) for d in dims]}


def install_image(M, spec):
    a = M["assets"]["rembrandt"]
    path = spec["image"]
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    img = bpy.data.images.load(path, check_existing=True)
    if max(img.size) < a["min_long_edge_px"]:
        return {"asset": "rembrandt", "ok": False, "px": list(img.size), "min": a["min_long_edge_px"]}
    w, h = a["canvas"]
    ar_img, ar_canvas = img.size[0] / img.size[1], w / h
    img.colorspace_settings.name = "sRGB"
    img.pack()  # the final .blend is self-contained
    mat = bpy.data.materials["M_rembrandt"]
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None) or nt.nodes.new("ShaderNodeTexImage")
    tex.image, tex.extension = img, "CLIP"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    mat["placeholder"] = False
    mat["source_px"] = list(img.size)
    return {"asset": "rembrandt", "ok": True, "px": list(img.size),
            "aspect_err": round(abs(ar_img - ar_canvas) / ar_canvas, 3)}


def apply(map_path):
    M = common.load_config()
    common.assert_version(M)
    with open(map_path, encoding="utf-8") as fh:
        amap = json.load(fh)
    coll = bpy.data.collections.get("ASSETS_REAL") or bpy.data.collections.new("ASSETS_REAL")
    if coll.name not in bpy.data.collections["APARTMENT"].children:
        bpy.data.collections["APARTMENT"].children.link(coll)
    results = []
    for key, spec in amap.items():
        try:
            r = install_image(M, spec) if key == "rembrandt" else install_mesh(M, key, spec, coll)
        except Exception as e:  # noqa: BLE001
            r = {"asset": key, "ok": False, "error": str(e)}
        log(step="apply", **r)
        results.append(r)
    with open(os.path.join(HERE, "apply_report.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)
    if not all(r["ok"] for r in results):
        log(step="done", saved=False)
        sys.exit(2)
    out = os.path.join(HERE, "apartment_final.blend")
    if os.path.exists(out):
        try:
            os.remove(out)
        except OSError:
            pass
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    log(step="done", saved=out)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args or args[0] not in ("scan", "apply"):
        raise SystemExit(__doc__)
    scan(args[1:]) if args[0] == "scan" else apply(args[1])
