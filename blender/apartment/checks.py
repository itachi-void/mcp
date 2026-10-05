"""Automated camera QA, run on every build: frame range, waypoint accuracy,
monotonic path timing, wall/furniture clearance, rotation speed, lens per shot."""

import math

import bpy
from mathutils import Vector

from .common import evaluated_matrix, find_fcurve

DIRS = [Vector((math.cos(a), math.sin(a), 0.0)) for a in [i * math.pi / 4 for i in range(8)]]
DIRS += [Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, -0.7)).normalized() for a in [i * math.pi / 2 for i in range(4)]]
DIRS += [Vector((0, 0, -1)), Vector((0, 0, 1))]


def _clearance(scene, depsgraph, origin, limit):
    best = limit
    for d in DIRS:
        o = origin
        remaining = limit
        while remaining > 1e-4:
            hit, loc, _n, _i, obj, _m = scene.ray_cast(depsgraph, o, d, distance=remaining)
            if not hit:
                break
            if obj is not None and (obj.get("transit_occluder") or obj.name.startswith("SHADOW_WIPE")):
                step = (loc - o).length + 1e-3
                o = loc + d * 1e-3
                remaining -= step
                continue
            best = min(best, (loc - origin).length)
            break
    return best


def check_fly_scene(M, scene):
    C = M["checks"]
    T = M["timeline"]
    rep = {"scene": scene.name, "errors": [], "warnings": [], "shots": {}}
    if (scene.frame_start, scene.frame_end, scene.render.fps, scene.render.fps_base) != \
            (T["frame_start"], T["frame_end"], T["fps"], T["fps_base"]):
        rep["errors"].append("frame range / fps mismatch")
    if abs(scene.render.motion_blur_shutter - M["render"]["shutter"]) > 1e-6:
        rep["errors"].append("shutter is not 180 degrees")

    fmt = scene.name.split("_")[-1]
    for shot in M["shots"]:
        cam = bpy.data.objects[f"CAM_{shot['id']}_{fmt}"]
        rig = bpy.data.objects[f"RIG_{shot['id']}_{fmt}"]
        s = {"min_clearance_m": 99.0, "max_yaw_deg_s": 0.0, "max_waypoint_err_m": 0.0,
             "lens": cam.data.lens, "path_length_m": cam.get("path_length_m")}
        fc = find_fcurve(rig, 'constraints["FollowPath"].offset_factor')
        vals = [fc.evaluate(f) for f in range(shot["start"], shot["end"] + 1)]
        if any(b < a - 1e-6 for a, b in zip(vals, vals[1:])):
            rep["errors"].append(f"{shot['id']}: camera reverses along path")
        if abs(vals[0]) > 1e-4 or abs(vals[-1] - 1.0) > 1e-4:
            rep["errors"].append(f"{shot['id']}: offset_factor does not span 0..1")

        offset = Vector(shot["v"]["offset"]) if fmt == "9x16" else Vector()
        targets = {f: Vector(p) + offset for f, p in shot["path"]}
        prev = None
        for f in range(shot["start"], shot["end"] + 1):
            scene.frame_set(f)
            if scene.camera != cam:
                rep["errors"].append(f"F{f}: active camera {scene.camera.name}, expected {cam.name}")
                break
            mw, dg = evaluated_matrix(scene, cam, f)
            pos = mw.translation.copy()
            fwd = (mw.to_quaternion() @ Vector((0, 0, -1))).normalized()
            s["min_clearance_m"] = min(s["min_clearance_m"], _clearance(scene, dg, pos, 1.0))
            if f in targets:
                s["max_waypoint_err_m"] = max(s["max_waypoint_err_m"], (pos - targets[f]).length)
            if prev is not None:
                s["max_yaw_deg_s"] = max(s["max_yaw_deg_s"], math.degrees(prev.angle(fwd, 0.0)) * T["fps"])
            prev = fwd
        for k in ("min_clearance_m", "max_yaw_deg_s", "max_waypoint_err_m"):
            s[k] = round(s[k], 3)
        if s["min_clearance_m"] < C["min_clearance"]:
            rep["warnings"].append(f"{shot['id']}: clearance {s['min_clearance_m']} m < {C['min_clearance']} m")
        if s["max_yaw_deg_s"] > C["max_yaw_deg_per_s"]:
            rep["warnings"].append(f"{shot['id']}: rotation {s['max_yaw_deg_s']} deg/s > {C['max_yaw_deg_per_s']}")
        if s["max_waypoint_err_m"] > C["waypoint_tolerance"]:
            rep["warnings"].append(f"{shot['id']}: waypoint error {s['max_waypoint_err_m']} m")
        rep["shots"][shot["id"]] = s
    scene.frame_set(T["frame_start"])
    return rep
