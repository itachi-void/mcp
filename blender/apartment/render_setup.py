"""The one place that sets engine, sampling, colour, motion blur and output.
Room modules never touch these, so build order cannot change delivery specs.
"""

import os

import bpy

from .common import kelvin_to_linear, hex_to_linear, link


def setup_world(M, apt_coll):
    L = M["lighting"]
    world = bpy.data.worlds.get("W_apartment") or bpy.data.worlds.new("W_apartment")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_to_linear(L["sky_color"])
    bg.inputs["Strength"].default_value = L["sky_strength"]
    _hdri(M, world, bg)

    from mathutils import Vector
    import math
    sun = bpy.data.lights.new("SUN", "SUN")
    sun.energy = L["sun"]["strength"]
    sun.angle = math.radians(L["sun"]["angle_deg"])
    sun.color = kelvin_to_linear(5600)
    obj = link(bpy.data.objects.new("SUN", sun), apt_coll)
    obj.rotation_euler = Vector(L["sun"]["direction"]).normalized().to_track_quat("-Z", "Y").to_euler()
    return world


def _hdri(M, world, bg):
    """Real city view behind the glass (CC0 HDRI) when downloaded; flat sky otherwise."""
    import json
    import math
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "hdri", "day.hdr")
    if not os.path.exists(path):
        return
    with open(os.path.join(os.path.dirname(__file__), "sourcing.json"), encoding="utf-8") as fh:
        rot = json.load(fh).get("hdri_rotation_deg", 0)
    nt = world.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(path, check_existing=True)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    world["hdri"] = os.path.basename(path)


def apply_render(M, scene, fmt, profile="final", world=None):
    R, T = M["render"], M["timeline"]
    P = R["profiles"][profile]
    r = scene.render

    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"

    scene.frame_start, scene.frame_end = T["frame_start"], T["frame_end"]
    r.fps, r.fps_base = T["fps"], T["fps_base"]

    r.engine = "CYCLES"
    if fmt in R["formats"]:
        r.resolution_x, r.resolution_y = R["formats"][fmt]["resolution"]
        r.filepath = R["formats"][fmt]["output"]
    else:  # stills
        r.resolution_x, r.resolution_y = 3840, 2160
        r.filepath = "//../render/stills/"
    r.resolution_percentage = P["percentage"]
    r.pixel_aspect_x = r.pixel_aspect_y = 1.0

    # 180-degree shutter, same for both formats.
    r.use_motion_blur = True
    r.motion_blur_shutter = R["shutter"]
    r.motion_blur_position = "CENTER"

    # Resume after a crash: skip existing frames, claim frames in progress.
    r.use_overwrite = False
    r.use_placeholder = True
    r.use_persistent_data = True
    r.film_transparent = False

    # Beauty plate: scene-linear OpenEXR half (16-bit float), lossless PIZ.
    im = r.image_settings
    im.file_format = "OPEN_EXR"
    im.color_depth = "16"
    im.exr_codec = "PIZ"
    im.color_mode = "RGB"

    c = scene.cycles
    c.device = "CPU"  # render_frames.py switches to GPU when available
    c.samples = P["samples"]
    # weak-machine guard: textures are downscaled at render time (files untouched)
    c.texture_limit_render = P.get("texture_limit", "OFF")
    r.use_simplify = "max_subdiv" in P  # caps the dressing models' subsurf levels
    r.simplify_subdivision_render = P.get("max_subdiv", 6)
    c.use_adaptive_sampling = True
    c.adaptive_threshold = P["threshold"]   # fixed threshold = consistent noise floor per frame
    c.adaptive_min_samples = P["min_samples"]
    c.use_animated_seed = R["animated_seed"]
    c.seed = 0
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "ACCURATE"
    c.sample_clamp_direct = R["clamp_direct"]
    c.sample_clamp_indirect = R["clamp_indirect"]
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = R["filter_glossy"]
    c.use_light_tree = True
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 12, 4, 4
    c.transmission_bounces, c.transparent_max_bounces, c.volume_bounces = 8, 8, 0

    # View transform only affects viewport/PNG previews. EXR is written
    # scene-linear (Linear Rec.709 primaries) and graded in Resolve.
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    if world is not None:
        scene.world = world
    if fmt in R["formats"]:
        _data_passes(M, scene, fmt)


def _data_passes(M, scene, fmt):
    """Depth / AO / Cryptomatte for the grade, written 32-bit float through a
    separate multilayer EXR (half floats break Z and Cryptomatte IDs)."""
    vl = scene.view_layers[0]
    vl.use_pass_z = True
    vl.use_pass_ambient_occlusion = True
    vl.use_pass_cryptomatte_object = True
    vl.use_pass_cryptomatte_material = True
    vl.pass_cryptomatte_depth = 6

    wanted = ["Depth", "AO"] + [f"Crypto{k}{i:02d}" for k in ("Object", "Material") for i in range(3)]
    base = M["render"]["data_passes_output"].format(fmt=fmt)
    if bpy.app.version >= (5, 0, 0):
        _data_passes_v5(scene, base, wanted)
        return

    scene.use_nodes = True
    nt = scene.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], comp.inputs["Image"])

    out = nt.nodes.new("CompositorNodeOutputFile")
    out.name = "DATA_PASSES"
    out.base_path = base
    out.format.file_format = "OPEN_EXR_MULTILAYER"
    out.format.color_depth = "32"
    out.format.exr_codec = "ZIP"
    out.layer_slots.clear()
    for name in wanted:
        if name in rl.outputs:
            out.layer_slots.new(name)
            nt.links.new(rl.outputs[name], out.inputs[name])


def _data_passes_v5(scene, base, wanted):
    """Blender 5.x: compositor is a node group, Composite node became Group Output,
    File Output uses directory/file_name + file_output_items."""
    name = f"APT_COMPOSITE_{scene.name}"
    old = bpy.data.node_groups.get(name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    nt = bpy.data.node_groups.new(name, "CompositorNodeTree")
    nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = nt
    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    gout = nt.nodes.new("NodeGroupOutput")
    nt.links.new(rl.outputs["Image"], gout.inputs["Image"])

    out = nt.nodes.new("CompositorNodeOutputFile")
    out.name = "DATA_PASSES"
    out.directory, out.file_name = os.path.split(base)
    out.format.media_type = "MULTI_LAYER_IMAGE"
    out.format.file_format = "OPEN_EXR_MULTILAYER"
    out.format.color_depth = "32"
    out.format.exr_codec = "ZIP"
    out.file_output_items.clear()
    for pas in wanted:
        if pas in rl.outputs:
            kind = "FLOAT" if pas in ("Depth", "AO") else "RGBA"
            out.file_output_items.new(kind, pas)
            nt.links.new(rl.outputs[pas], out.inputs[pas])
