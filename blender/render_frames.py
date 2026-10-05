"""Render previews, stills, CAM_06 bath verify renders, or the full masters.

    blender -b blender/apartment_master.blend -P blender/render_frames.py -- preview
    blender -b blender/apartment_master.blend -P blender/render_frames.py -- verify
    blender -b blender/apartment_master.blend -P blender/render_frames.py -- stills
    blender -b blender/apartment_master.blend -P blender/render_frames.py -- master 16x9         # 1080p (hd)
    blender -b blender/apartment_master.blend -P blender/render_frames.py -- master 16x9 --4k    # 2160p, strong GPU only

'master' renders the animation with resume (existing frames are skipped,
in-progress frames are claimed by placeholders), so a crash only costs the
frame that was rendering.
"""

import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apartment import common, render_setup  # noqa: E402

PREVIEW_FRAMES = [20, 120, 270, 300, 372, 440, 520, 600, 690, 860]


def enable_gpu():
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs is None:
        return False
    cp = prefs.preferences
    for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            cp.compute_device_type = backend
            cp.refresh_devices()
        except TypeError:
            continue
        devices = [d for d in cp.devices if d.type != "CPU"]
        if devices:
            for d in cp.devices:
                d.use = True
            return True
    return False


def still(scene, camera, frame, path, fmt, profile, M):
    render_setup.apply_render(M, scene, fmt, profile)
    scene.camera = camera
    scene.frame_set(frame)
    r = scene.render
    r.use_overwrite = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_depth = "8"
    r.image_settings.color_mode = "RGB"
    r.filepath = path
    if bpy.app.version >= (5, 0, 0):  # previews skip the data-pass compositor
        scene.compositing_node_group = None
    else:
        scene.use_nodes = False
    bpy.context.window_manager  # noqa: B018 (keeps context alive in background)
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=scene.name)
    print(f"  {os.path.basename(path)}  {time.time() - t:.1f}s")


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["preview"]
    mode = args[0]
    M = common.load_config()
    common.assert_version(M)
    gpu = enable_gpu()
    out = os.path.join(HERE, "..", "render", mode)
    os.makedirs(out, exist_ok=True)
    print(f"mode={mode} gpu={gpu}")

    if mode == "preview":
        fmts = [a for a in args[1:] if not a.startswith("--")] or ["16x9", "9x16"]
        frames = PREVIEW_FRAMES
        for a in args[1:]:
            if a.startswith("--frames="):
                frames = [int(x.strip()) for x in a.split("=", 1)[1].split(",") if x.strip()]
        for fmt in fmts:
            sc = bpy.data.scenes[f"FLY_{fmt}"]
            for f in frames:
                sc.frame_set(f)
                for c in (sc.camera,):
                    if gpu:
                        sc.cycles.device = "GPU"
                    still(sc, c, f, os.path.join(out, f"{fmt}_F{f:03d}.png"), fmt, "preview", M)
    elif mode in ("stills", "verify"):
        sc = bpy.data.scenes["STILLS"]
        for cam in [o for o in sc.objects if o.type == "CAMERA"]:
            if mode == "verify" and not cam.get("verify"):
                continue
            if gpu:
                sc.cycles.device = "GPU"
            profile = ("final" if "--4k" in args else "hd") if mode == "stills" else "preview"
            still(sc, cam, 1, os.path.join(out, f"{cam.name}.png"), "stills", profile, M)
    elif mode == "master":
        fmt = args[1]
        # 4K is opt-in only: the default master is 1080p so a weak machine never gets a 4K job.
        profile = "final" if "--4k" in args else "hd"
        print(f"master {fmt} profile={profile}")
        sc = bpy.data.scenes[f"FLY_{fmt}"]
        render_setup.apply_render(M, sc, fmt, profile)
        if gpu:
            sc.cycles.device = "GPU"
        bpy.ops.render.render(animation=True, scene=sc.name)
    else:
        raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    main()
