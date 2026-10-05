"""Material library shared by every room (one definition per finish).

All procedural textures use *object-space* coordinates on real-size meshes,
so pattern scale is identical in both formats and across rooms (no UV
stretching on the procedural fallbacks).
"""

import os

import bpy

from .common import HERE, OWNED, hex_to_linear, kelvin_to_linear

_LIB = {}


def _new(name):
    mat = bpy.data.materials.get(name)
    if mat is not None and mat.get(OWNED):
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat[OWNED] = True
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return mat, nt, bsdf


def _set(bsdf, **kw):
    names = {
        "base": "Base Color", "rough": "Roughness", "metal": "Metallic",
        "sheen": "Sheen Weight", "sheen_rough": "Sheen Roughness",
        "aniso": "Anisotropic", "coat": "Coat Weight", "spec": "Specular IOR Level",
        "transmission": "Transmission Weight", "ior": "IOR",
    }
    for k, v in kw.items():
        bsdf.inputs[names[k]].default_value = v


def _coords(nt, scale=(1.0, 1.0, 1.0)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _bump(nt, bsdf, height_socket, strength):
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    nt.links.new(height_socket, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _ramp(nt, fac_socket, c0, c1, p0=0.0, p1=1.0):
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = p0
    ramp.color_ramp.elements[0].color = hex_to_linear(c0)
    ramp.color_ramp.elements[1].position = p1
    ramp.color_ramp.elements[1].color = hex_to_linear(c1)
    nt.links.new(fac_socket, ramp.inputs["Fac"])
    return ramp.outputs["Color"]


def plaster():
    mat, nt, b = _new("M_plaster_greige")
    _set(b, base=hex_to_linear("#CDC4B7"), rough=0.88, spec=0.3)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 6.0
    nt.links.new(_coords(nt), n.inputs["Vector"])
    _bump(nt, b, n.outputs["Fac"], 0.03)
    return mat


def walnut(name="M_walnut", light="#7A5136", dark="#3E271A", grain_axis_scale=(1.0, 14.0, 14.0)):
    mat, nt, b = _new(name)
    co = _coords(nt, grain_axis_scale)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.5
    noise.inputs["Detail"].default_value = 4.0
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 1.6
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    nt.links.new(co, noise.inputs["Vector"])
    nt.links.new(co, wave.inputs["Vector"])
    col = _ramp(nt, wave.outputs["Fac"], dark, light, 0.2, 0.85)
    nt.links.new(col, b.inputs["Base Color"])
    _set(b, rough=0.42, coat=0.15)
    _bump(nt, b, wave.outputs["Fac"], 0.04)
    return mat


def floor_oak():
    mat, nt, b = _new("M_floor_oak")
    co = _coords(nt)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.37
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 1.4
    brick.inputs["Row Height"].default_value = 0.19
    brick.inputs["Mortar Size"].default_value = 0.002
    brick.inputs["Color1"].default_value = hex_to_linear("#9C7650")
    brick.inputs["Color2"].default_value = hex_to_linear("#80603F")
    brick.inputs["Mortar"].default_value = hex_to_linear("#3B2A1C")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 8.0
    nt.links.new(co, brick.inputs["Vector"])
    nt.links.new(co, wave.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.25
    nt.links.new(brick.outputs["Color"], mix.inputs["A"])
    nt.links.new(wave.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    _set(b, rough=0.38, coat=0.2)
    _bump(nt, b, brick.outputs["Fac"], 0.08)
    return mat


def travertine():
    mat, nt, b = _new("M_travertine")
    co = _coords(nt, (1.0, 1.0, 4.0))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 10.0
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 90.0
    nt.links.new(co, noise.inputs["Vector"])
    nt.links.new(co, vor.inputs["Vector"])
    col = _ramp(nt, noise.outputs["Fac"], "#BCA98D", "#E1D5C0", 0.35, 0.7)
    nt.links.new(col, b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.45
    rough.inputs["To Max"].default_value = 0.7
    nt.links.new(noise.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    _bump(nt, b, vor.outputs["Distance"], 0.05)
    return mat


def _vary(nt, b, hex_color, rough, color_amt=0.08, rough_amt=0.12, scale=3.0, micro=0.0):
    """Break up the 'one colour, one roughness' CG look: large soft blotches (dye, fading,
    handling) modulate colour and roughness; optional micro bump = fine surface texture."""
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 6.0
    nt.links.new(_coords(nt), n.inputs["Vector"])
    c = tuple(hex_to_linear(hex_color)[:3])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e0, e1 = ramp.color_ramp.elements
    e0.position, e0.color = 0.3, tuple(v * (1 - color_amt) for v in c) + (1.0,)
    e1.position, e1.color = 0.7, c + (1.0,)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.0, rough - rough_amt)
    mr.inputs["To Max"].default_value = min(1.0, rough + rough_amt)
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    if micro:
        f = nt.nodes.new("ShaderNodeTexNoise")
        f.inputs["Scale"].default_value = 900.0
        nt.links.new(_coords(nt), f.inputs["Vector"])
        _bump(nt, b, f.outputs["Fac"], micro)


def fabric(name, hex_color, sheen=0.7, rough=0.85, bump=0.2, scale=380.0):
    mat, nt, b = _new(name)
    _set(b, base=hex_to_linear(hex_color), rough=rough, sheen=sheen, sheen_rough=0.45, spec=0.25)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = scale
    nt.links.new(_coords(nt), vor.inputs["Vector"])
    _bump(nt, b, vor.outputs["Distance"], bump)
    _vary(nt, b, hex_color, rough, color_amt=0.1, rough_amt=0.08, scale=2.5)
    return mat


def solid(name, hex_color, rough=0.5, metal=0.0, aniso=0.0, coat=0.0):
    mat, nt, b = _new(name)
    _set(b, base=hex_to_linear(hex_color), rough=rough, metal=metal, aniso=aniso, coat=coat)
    if rough > 0.02:  # mirrors/chrome stay clean; everything else has handling marks
        _vary(nt, b, hex_color, rough, color_amt=0.06 if metal else 0.04,
              rough_amt=min(0.15, rough * 0.45), scale=6.0, micro=0.02 if metal else 0.01)
    return mat


def tile():
    mat, nt, b = _new("M_tile_bath")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.6
    brick.inputs["Row Height"].default_value = 0.3
    brick.inputs["Mortar Size"].default_value = 0.003
    brick.inputs["Color1"].default_value = hex_to_linear("#E6E0D6")
    brick.inputs["Color2"].default_value = hex_to_linear("#DDD6CA")
    brick.inputs["Mortar"].default_value = hex_to_linear("#A79D90")
    nt.links.new(_coords(nt), brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
    _set(b, rough=0.22)
    _bump(nt, b, brick.outputs["Fac"], 0.1)
    return mat


def glass():
    """Architectural glass: refractive for camera rays, transparent for shadow
    rays, so sunlight passes the glazing with caustics disabled (no fireflies)."""
    mat, nt, b = _new("M_glass")
    _set(b, base=(0.95, 0.97, 0.97, 1.0), rough=0.0, transmission=1.0, ior=1.45)
    out = nt.nodes["Material Output"]
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(b.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def emission(name, kelvin, strength):
    mat, nt, b = _new(name)
    nt.nodes.remove(b)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*kelvin_to_linear(kelvin), 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
    return mat


def painting(M):
    """Rembrandt canvas. Uses the licensed hi-res scan from blender/assets/ when
    present; otherwise a clearly-labelled chiaroscuro placeholder."""
    spec = M["assets"]["rembrandt"]
    path = os.path.join(HERE, "..", spec["image"])
    mat, nt, b = _new("M_rembrandt")
    _set(b, rough=0.55, coat=0.35)
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = "sRGB"
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.extension = "CLIP"
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        mat["placeholder"] = False
        mat["source_px"] = list(img.size)
    else:
        grad = nt.nodes.new("ShaderNodeTexGradient")
        grad.gradient_type = "SPHERICAL"
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Location"].default_value = (0.5, 0.55, 0.0)
        mp.inputs["Scale"].default_value = (1.8, 1.5, 1.0)
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
        col = _ramp(nt, grad.outputs["Fac"], "#120C08", "#B27A3E", 0.0, 0.9)
        nt.links.new(col, b.inputs["Base Color"])
        mat["placeholder"] = True
    return mat


def build_library(M):
    _LIB.clear()
    L = M["lighting"]
    _LIB.update({
        "plaster": plaster(),
        "walnut": walnut(),
        "walnut_dark": walnut("M_walnut_dark", "#5A3A26", "#2A1A10"),
        "floor_oak": floor_oak(),
        "travertine": travertine(),
        "boucle": fabric("M_boucle", "#E7E1D6", sheen=0.8, rough=0.82, bump=0.35, scale=420.0),
        "linen": fabric("M_linen", "#E2DACD", sheen=0.5, rough=0.9, bump=0.12, scale=900.0),
        "fabric_dark": fabric("M_fabric_taupe", "#5B5046", sheen=0.5, rough=0.8),
        "rug": fabric("M_rug_wool", "#C9BDAB", sheen=0.6, rough=0.95, bump=0.4, scale=250.0),
        "bronze": solid("M_bronze_brushed", "#8A6A45", rough=0.32, metal=1.0, aniso=0.55),
        "black_metal": solid("M_black_metal", "#161514", rough=0.4, metal=1.0),
        "chrome": solid("M_chrome", "#D9D9D9", rough=0.08, metal=1.0),
        "mirror": solid("M_mirror", "#F2F2F2", rough=0.0, metal=1.0),
        "dark_stone": solid("M_dark_stone", "#23211F", rough=0.3, coat=0.3),
        "ceramic": solid("M_ceramic_white", "#EDEAE4", rough=0.18, coat=0.3),
        "terrace_stone": solid("M_terrace_stone", "#A49C90", rough=0.75),
        "plant": solid("M_plant", "#3E5134", rough=0.6),
        "tile": tile(),
        "glass": glass(),
        "lamp_warm": emission("M_emit_lamp", L["practical_kelvin"], 14.0),
        "led_strip": emission("M_emit_led", L["practical_kelvin"], 28.0),
        "painting": painting(M),
    })
    apply_scanned(M)
    return _LIB


def _image(nt, path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.projection = "BOX"  # tri-planar: no UV seams on the real-size primitives
    tex.projection_blend = 0.25
    return tex


def apply_scanned(M):
    """Swap a finish's procedural colour/roughness/normal for the CC0 scanned set in
    assets/textures/<finish>/ when fetch_assets.py has downloaded it. Tile size is
    real-world metres (object space on real-size meshes = one texel density)."""
    import json
    with open(os.path.join(HERE, "sourcing.json"), encoding="utf-8") as fh:
        S = json.load(fh)
    root = os.path.join(HERE, "..", "assets", "textures")
    done = []
    for key, spec in S["textures"].items():
        mat = _LIB.get(key)
        folder = os.path.join(root, key)
        diff = os.path.join(folder, f"{key}_diff.jpg")
        if mat is None or not os.path.exists(diff):
            continue
        nt = mat.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        normal_only = spec.get("normal_only", False)  # keep the palette colour, borrow the real weave/relief
        for sock in ("Normal",) if normal_only else ("Base Color", "Roughness", "Normal"):
            for link in list(b.inputs[sock].links):
                nt.links.remove(link)
        co = _coords(nt, (1.0 / spec["tile_m"],) * 3)
        nor = os.path.join(folder, f"{key}_nor_gl.jpg")
        if normal_only:
            if os.path.exists(nor):
                t = _image(nt, nor, True)
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = 0.8
                nt.links.new(co, t.inputs["Vector"])
                nt.links.new(t.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
            mat["scanned"] = spec["id"] + " (normal)"
            done.append(key)
            continue
        tex = _image(nt, diff, False)
        nt.links.new(co, tex.inputs["Vector"])
        color = tex.outputs["Color"]
        if "tint" in spec:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs["B"].default_value = hex_to_linear(spec["tint"])
            nt.links.new(color, mix.inputs["A"])
            color = mix.outputs["Result"]
        nt.links.new(color, b.inputs["Base Color"])
        rough = os.path.join(folder, f"{key}_rough.jpg")
        if os.path.exists(rough):
            t = _image(nt, rough, True)
            nt.links.new(co, t.inputs["Vector"])
            nt.links.new(t.outputs["Color"], b.inputs["Roughness"])
        nor = os.path.join(folder, f"{key}_nor_gl.jpg")
        if os.path.exists(nor):
            t = _image(nt, nor, True)
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = 0.8
            nt.links.new(co, t.inputs["Vector"])
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
        mat["scanned"] = spec["id"]
        done.append(key)
    return done


def get(name):
    return _LIB[name]
