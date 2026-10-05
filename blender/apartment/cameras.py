"""Flythrough camera rigs, one per shot and per format.

Rig hierarchy per shot (fixes axis / aim / bank problems of the old script):

    RIG  (Follow Path, use_fixed_location=True, offset_factor keyed by arc length)
     └─ PIVOT (Track To AIM, track -Z, up Y  -> camera looks at AIM, horizon level)
         └─ CAM (local Z = bank roll, tiny noise on local X/Y = FPV breath)

Cuts are camera switches through bound timeline markers: lens changes only
happen on cuts, and motion blur never integrates across a cut.
"""

import math

import bpy
from mathutils import Vector
from mathutils.geometry import interpolate_bezier

from . import materials as mats
from .common import box, empty, evaluated_matrix, find_fcurve, fresh_collection, link, ray_visibility

NOISE_RAD = 0.0035   # ~0.2 deg of breathing on pitch/yaw
NOISE_SCALE = 45.0   # frames per noise period
OCCLUDER_CLEARANCE = 0.30


def _shot_for_format(shot, fmt):
    """9:16 is its own blocking: own lens, offset path, higher aim."""
    if fmt == "16x9":
        return shot["lens"], [(f, Vector(p)) for f, p in shot["path"]], [(f, Vector(p)) for f, p in shot["aim"]]
    v = shot["v"]
    off = Vector(v["offset"])
    aim_dz = Vector((0, 0, v["aim_dz"]))
    return (v["lens"],
            [(f, Vector(p) + off) for f, p in shot["path"]],
            [(f, Vector(p) + aim_dz) for f, p in shot["aim"]])


def _bezier_curve(name, coll, points, frame_end):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.use_path = True
    cu.path_duration = frame_end           # irrelevant with fixed location, set for clarity
    cu.eval_time = 0.0
    cu.resolution_u = 64
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = link(bpy.data.objects.new(name, cu), coll)
    obj.hide_render = True
    return obj


def _arc_fractions(curve_obj, samples=256):
    """Cumulative arc-length fraction at each control point, measured on the
    actual Bézier (offset_factor walks by distance, not by control point)."""
    bpy.context.view_layer.update()
    pts = curve_obj.data.splines[0].bezier_points
    lengths = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        seg = interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, samples)
        lengths.append(lengths[-1] + sum((seg[i + 1] - seg[i]).length for i in range(len(seg) - 1)))
    total = lengths[-1]
    return [l / total for l in lengths], total


def _key_locations(obj, keys):
    for f, p in keys:
        obj.location = p
        obj.keyframe_insert("location", frame=f)
    for i in range(3):
        fc = find_fcurve(obj, "location", i)
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def _key_offset(rig, con, frames, fractions, ease_in, ease_out):
    path = f'constraints["{con.name}"].offset_factor'
    for f, v in zip(frames, fractions):
        con.offset_factor = v
        rig.keyframe_insert(path, frame=f)
    fc = find_fcurve(rig, path)
    kps = fc.keyframe_points
    for i, kp in enumerate(kps):
        kp.interpolation = "BEZIER"
        # Interior keys use AUTO (continuous velocity, no stop-start per beat);
        # only the very first/last frame of the film eases.
        clamped = (i == 0 and ease_in) or (i == len(kps) - 1 and ease_out)
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED" if clamped else "AUTO"
    fc.extrapolation = "LINEAR"  # motion-blur sub-frames at shot edges keep moving
    fc.update()
    # AUTO handles can overshoot and make the camera reverse: verify, fall back.
    vals = [fc.evaluate(f) for f in range(frames[0], frames[-1] + 1)]
    if any(b < a - 1e-6 for a, b in zip(vals, vals[1:])):
        for kp in kps:
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()
    return fc


def _bank_and_noise(cam, shot, fmt_scale, seed):
    if shot["bank"]:
        for f, deg in shot["bank"]:
            cam.rotation_euler[2] = math.radians(deg)
            cam.keyframe_insert("rotation_euler", index=2, frame=f)
    for idx in (0, 1):
        cam.rotation_euler[idx] = 0.0
        cam.keyframe_insert("rotation_euler", index=idx, frame=shot["start"])
        fc = find_fcurve(cam, "rotation_euler", idx)
        mod = fc.modifiers.new("NOISE")
        mod.strength = NOISE_RAD * fmt_scale * (0.6 if idx == 1 else 1.0)
        mod.scale = NOISE_SCALE
        mod.phase = seed * 7.31 + idx * 3.7
        mod.depth = 1


def build_shot(M, scene, coll, shot, fmt, first, last):
    fmt_spec = M["render"]["formats"][fmt]
    lens, path, aim = _shot_for_format(shot, fmt)
    sid = f"{shot['id']}_{fmt}"

    curve = _bezier_curve(f"PATH_{sid}", coll, [p for _, p in path], M["timeline"]["frame_end"])

    rig = empty(f"RIG_{sid}", coll, size=0.2, kind="ARROWS")
    con = rig.constraints.new("FOLLOW_PATH")
    con.name = "FollowPath"
    con.target = curve
    con.use_fixed_location = True      # offset_factor is ignored without this
    con.use_curve_follow = False       # orientation comes from the aim rig instead
    fractions, length = _arc_fractions(curve)
    _key_offset(rig, con, [f for f, _ in path], fractions, ease_in=first, ease_out=last)

    aim_obj = empty(f"AIM_{sid}", coll, size=0.15, kind="SPHERE")
    _key_locations(aim_obj, aim)

    pivot = empty(f"PIVOT_{sid}", coll, size=0.1)
    pivot.parent = rig
    trk = pivot.constraints.new("TRACK_TO")
    trk.target = aim_obj
    trk.track_axis = "TRACK_NEGATIVE_Z"   # camera looks down its local -Z
    trk.up_axis = "UP_Y"                  # camera up is local +Y

    cam_data = bpy.data.cameras.new(f"CAM_{sid}")
    cam_data.lens = lens
    cam_data.sensor_fit = fmt_spec["sensor_fit"]
    cam_data.sensor_width = fmt_spec["sensor"]
    cam_data.sensor_height = fmt_spec["sensor"]
    cam_data.clip_start = 0.03
    cam_data.clip_end = 300.0
    cam = link(bpy.data.objects.new(f"CAM_{sid}", cam_data), coll)
    cam.parent = pivot
    cam.rotation_mode = "XYZ"
    _bank_and_noise(cam, shot, 1.0 if fmt == "16x9" else 0.8, seed=int(shot["id"][-2:]))

    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = shot["fstop"]
    cam_data.dof.aperture_blades = 9
    cam_data.dof.aperture_rotation = math.radians(10)
    if shot["focus"]:
        focus = empty(f"FOCUS_{sid}", coll, size=0.08, kind="SINGLE_ARROW")
        _key_locations(focus, [(f, Vector(p)) for f, p in shot["focus"]])
        cam_data.dof.focus_object = focus
    else:
        cam_data.dof.focus_object = aim_obj

    for obj in (curve, rig, aim_obj, pivot):
        obj.hide_render = True
    cam["shot"] = shot["id"]
    cam["path_length_m"] = round(length, 3)
    return cam


def _camera_state(scene, cam, frame):
    mw, _ = evaluated_matrix(scene, cam, frame)
    return mw.translation.copy(), (mw.to_quaternion() @ Vector((0, 0, -1))).normalized()


def _key_visibility_window(obj, start, end):
    """Render-visible only inside [start, end] (bool keys are constant)."""
    for f, hidden in ((start - 1, True), (start, False), (end, False), (end + 1, True)):
        if f >= 0:
            obj.hide_render = hidden
            obj.keyframe_insert("hide_render", frame=f)


def place_occluder(M, scene, coll, cam, shot, spec, fmt):
    """TRANSIT_OCCLUDER: a floor-to-ceiling walnut fin positioned so it crosses
    frame centre at spec['frame'] while staying >= 30 cm from the camera path
    for the whole shot. Searches a small grid and keeps the best candidate."""
    f = spec["frame"]
    p, fwd = _camera_state(scene, cam, f)
    track = [_camera_state(scene, cam, k)[0] for k in range(shot["start"], shot["end"] + 1)]
    flat = Vector((fwd.x, fwd.y, 0)).normalized()
    side = Vector((-flat.y, flat.x, 0))  # left of view
    prefer = 1.0 if spec.get("side", "left") == "left" else -1.0
    best = None
    for d in (0.55, 0.7, 0.85, 1.0, 1.2):
        for k in range(-8, 9):
            lat = k * 0.08
            c = p + flat * d + side * lat
            c.z = 0.0
            clearance = min((Vector((t.x, t.y, 0)) - c).length for t in track)
            if clearance < OCCLUDER_CLEARANCE:
                continue
            off_axis = math.atan2(abs(lat), d)
            score = off_axis + d * 0.05 - (0.01 if lat * prefer > 0 else 0.0)
            if best is None or score < best[0]:
                best = (score, c, clearance, d, lat)
    if best is None:
        raise RuntimeError(f"{shot['id']} {fmt}: no clear position for occluder at F{f}")
    _, c, clearance, d, lat = best
    H = M["shell"]["wall_height"]
    fin = box(f"TRANSIT_OCCLUDER_{shot['id']}_{fmt}_{spec['label']}", coll,
              (c.x, c.y, H / 2), (0.14, 0.14, H), mats.get("walnut_dark"), bevel=0.004)
    # Camera-only: no shadows, no reflections, no bounce light.
    ray_visibility(fin, camera=True, shadow=False, diffuse=False, glossy=False, transmission=False)
    fin["transit_occluder"] = True
    fin["clearance_m"] = round(clearance, 3)
    _key_visibility_window(fin, shot["start"], shot["end"])
    return fin


def place_shadow_wipe(M, scene, coll, cam, shot, spec, fmt, half=12):
    """Shadow wipe: a hard spot aimed where the camera looks at spec['frame'];
    a camera-invisible flag slides through the beam over +-half frames so a
    hard shadow edge sweeps across the frame."""
    f = spec["frame"]
    p, fwd = _camera_state(scene, cam, f)
    H = M["shell"]["wall_height"]
    target = p + fwd * 2.2
    target.z = max(0.0, target.z)
    src = Vector((p.x - fwd.x * 0.4, p.y - fwd.y * 0.4, H - 0.12))
    light = bpy.data.lights.new(f"SHADOW_WIPE_KEY_{shot['id']}_{fmt}", "SPOT")
    light.energy = 450.0
    light.spot_size = math.radians(70)
    light.spot_blend = 0.15
    light.shadow_soft_size = 0.01
    light.color = (1.0, 0.86, 0.7)
    key = link(bpy.data.objects.new(light.name, light), coll)
    key.location = src
    key.rotation_euler = (target - src).to_track_quat("-Z", "Y").to_euler()

    beam = (target - src).normalized()
    across = beam.cross(Vector((0, 0, 1))).normalized()
    mid = src + (target - src) * 0.35
    flag = box(f"SHADOW_WIPE_FLAG_{shot['id']}_{fmt}", coll, mid, (0.9, 0.9, 0.01),
               mats.get("black_metal"), bevel=0.0)
    flag.rotation_euler = beam.to_track_quat("Z", "Y").to_euler()
    ray_visibility(flag, camera=False, shadow=True, diffuse=False, glossy=False, transmission=False)
    for frame, s in ((f - half, -1.3), (f + half, 1.3)):
        flag.location = mid + across * s
        flag.keyframe_insert("location", frame=frame)
    for obj in (key, flag):
        _key_visibility_window(obj, shot["start"], shot["end"])
    return key, flag


def build_fly_scene(M, scene, fmt):
    coll = fresh_collection(f"RIG_{fmt}", scene.collection)
    transit = fresh_collection(f"TRANSIT_{fmt}", scene.collection)
    scene.timeline_markers.clear()
    shots = M["shots"]
    cams = []
    for i, shot in enumerate(shots):
        cam = build_shot(M, scene, coll, shot, fmt, first=(i == 0), last=(i == len(shots) - 1))
        m = scene.timeline_markers.new(shot["id"], frame=shot["start"])
        m.camera = cam
        for f, label in shot["transitions"]:
            scene.timeline_markers.new(f"{f:03d}_{label}", frame=f)
        cams.append(cam)
    scene.camera = cams[0]

    for cam, shot in zip(cams, shots):
        for spec in shot["occluders"]:
            place_occluder(M, scene, transit, cam, shot, spec, fmt)
        for spec in shot["shadow_wipes"]:
            place_shadow_wipe(M, scene, transit, cam, shot, spec, fmt)
    scene.frame_set(M["timeline"]["frame_start"])
    return cams


def build_stills_scene(M, scene):
    coll = fresh_collection("STILL_CAMERAS", scene.collection)
    cams = []
    for s in M["stills"]:
        data = bpy.data.cameras.new(s["id"])
        data.lens = s["lens"]
        data.sensor_fit = "HORIZONTAL"
        data.sensor_width = 36.0
        data.clip_start = 0.03
        cam = link(bpy.data.objects.new(s["id"], data), coll)
        cam.location = s["loc"]
        cam.rotation_euler = (Vector(s["aim"]) - Vector(s["loc"])).to_track_quat("-Z", "Y").to_euler()
        cam["verify"] = bool(s.get("verify"))
        cams.append(cam)
    scene.camera = cams[0]
    return cams
