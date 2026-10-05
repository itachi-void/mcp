"""Build the unified apartment and both flythrough masters from scratch.

    blender -b --factory-startup -P blender/build_apartment.py

Starts from an empty file (never mutates an existing .blend), builds every
room module into one APARTMENT collection, creates three scenes that share it
(FLY_16x9, FLY_9x16, STILLS), runs camera QA and saves
blender/apartment_master.blend plus blender/build_report.json.
"""

import importlib
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import apartment  # noqa: E402
from apartment import cameras, checks, common, dressing, materials, render_setup, rooms, shell  # noqa: E402

for mod in (common, materials, shell, rooms, cameras, render_setup, checks):
    importlib.reload(mod)

OUT_BLEND = os.path.join(HERE, "apartment_master.blend")
OUT_REPORT = os.path.join(HERE, "build_report.json")


def main():
    M = common.load_config()
    common.assert_version(M)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    fly_h = bpy.context.scene
    fly_h.name = "FLY_16x9"
    apt = common.fresh_collection("APARTMENT", fly_h.collection)

    materials.build_library(M)
    shell.build_shell(M, common.fresh_collection("SHELL", apt))
    for name, room in M["rooms"].items():
        coll = common.fresh_collection(f"ROOM_{name}", apt)
        rooms.MODULES[name](M, tuple(room["origin"]), coll)
    dressing_report = dressing.build(apt)
    print("DRESSING", dressing_report)
    world = render_setup.setup_world(M, apt)

    fly_v = bpy.data.scenes.new("FLY_9x16")
    stills = bpy.data.scenes.new("STILLS")
    for sc in (fly_v, stills):
        sc.collection.children.link(apt)

    report = {"blender": bpy.app.version_string, "scenes": []}
    for sc, fmt in ((fly_h, "16x9"), (fly_v, "9x16")):
        render_setup.apply_render(M, sc, fmt, "final", world)
        cameras.build_fly_scene(M, sc, fmt)
        report["scenes"].append(checks.check_fly_scene(M, sc))
    render_setup.apply_render(M, stills, "stills", "final", world)
    cameras.build_stills_scene(M, stills)

    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    errors = [e for s in report["scenes"] for e in s["errors"]]
    for s in report["scenes"]:
        print(f"[{s['scene']}]", json.dumps(s["shots"]), "warnings:", s["warnings"])
    if errors:
        raise SystemExit("BUILD FAILED: " + "; ".join(errors))
    print("BUILD OK ->", OUT_BLEND)


if __name__ == "__main__":
    main()
