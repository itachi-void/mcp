"""
Organic Luxury Living Room — Blender scene builder
Mirrors src/components/livingroom/LivingRoomScene.tsx (photoreal, reference-matched).
Blender 3.6+ / 4.x | Cycles | output: //livingroom_render.png

Reference-driven realism upgrades (kept in sync with the R3F scene):
  · Golden-hour window backdrop + continuous folded sheer curtains (bmesh, not slats)
  · Layered cone flames on a linear fireplace with a warm fire light
  · Floating LED media shelf with framed art + trailing plant
  · Varied throw pillows (olive/sage/cream) + draped chunky knit throw
  · Round travertine coffee table on a fluted drum base
  · Barrel boucle swivel chair, potted olive trees, floor + table lamps, wall AC unit
  · Enhanced slatted divider with lit open shelves + base cabinet
  · Warm key from the window side + cool room-side fill (evening balance)
"""
import bpy
import bmesh
import math
import random
import sys
from mathutils import Euler

W, D, H = 7.2, 6.0, 3.0
SAMPLES, RESOLUTION = 512, (1920, 1080)
random.seed(7)

def hx(v):
    v = v.lstrip('#'); return tuple(int(v[i:i+2], 16) / 255 for i in (0, 2, 4))

def T(p): return (p[0], p[2], p[1])
def TS(s): return (s[0], s[2], s[1])

def setup_scene(name='LivingRoom_Scene'):
    """Isolates this room: only objects/materials belonging to its scene are removed."""
    scene = bpy.data.scenes.get(name)
    if not scene:
        scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    for obj in list(scene.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for mat in list(bpy.data.materials):
        if mat.name.startswith('LR_') and mat.users == 0: bpy.data.materials.remove(mat)
    return scene

def mat(name, color, rough=0.5, metal=0, emission=None, strength=0, clearcoat=0, transmission=0, alpha=1):
    m = bpy.data.materials.new('LR_' + name); m.use_nodes = True
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    if hasattr(m, 'blend_method'): m.blend_method = 'BLEND' if alpha < 1 else 'OPAQUE'
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*hx(color), alpha)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Alpha'].default_value = alpha
    for key in ('Coat Weight', 'Clearcoat'):
        if key in b.inputs: b.inputs[key].default_value = clearcoat; break
    for key in ('Transmission Weight', 'Transmission'):
        if key in b.inputs: b.inputs[key].default_value = transmission; break
    if emission:
        b.inputs['Emission Color'].default_value = (*hx(emission), 1)
        b.inputs['Emission Strength'].default_value = strength
    return m

def micro_bump(m, scale=35, strength=0.05):
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    n = m.node_tree.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale
    bump = m.node_tree.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = strength
    m.node_tree.links.new(n.outputs['Fac'], bump.inputs['Height']); m.node_tree.links.new(bump.outputs['Normal'], b.inputs['Normal'])

def box(name, loc, size, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new('Soft_Edges', 'BEVEL'); mod.width = bevel; mod.segments = 3
    return o

def tbox(name, p, s, material, bevel=0): return box(name, T(p), TS(s), material, bevel)

def cyl(name, loc, radius, depth, material, scale=(1,1,1), rot=None, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); return o

def cone(name, loc, r1, depth, material, rot=None):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r1, radius2=0, depth=depth, location=loc)
    o = bpy.context.object; o.name = name
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); return o

def torus(name, loc, major, minor, material, rot=None):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=major, minor_radius=minor, major_segments=40, minor_segments=16)
    o = bpy.context.object; o.name = name
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o

def sphere(name, loc, radius, material, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, radius=radius, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(material)
    bpy.ops.object.shade_smooth(); return o

def light(name, typ, loc, energy, color, size=0.1, distance=None):
    bpy.ops.object.light_add(type=typ, location=loc); o = bpy.context.object; o.name = name
    o.data.energy = energy; o.data.color = hx(color); o.data.shadow_soft_size = size
    if distance and hasattr(o.data, 'use_custom_distance'):
        o.data.use_custom_distance = True; o.data.cutoff_distance = distance
    return o

def plane(name, loc, sx, sz, material, rot=None):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc); o = bpy.context.object; o.name = name
    o.scale = (sx, sz, 1)
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); return o

def folded_curtain(name, center_x, width, wall_y, z_bottom, z_top, material, folds=7, depth=0.05):
    """Continuous sinusoidal sheer built in bmesh so it reads as fabric, not cardboard slats."""
    bm = bmesh.new(); segX, segY = folds * 6, 8; h = z_top - z_bottom
    grid = []
    for ix in range(segX + 1):
        t = ix / segX; px = center_x - width / 2 + width * t
        py = wall_y + math.sin(t * math.pi * 2 * folds) * depth
        col = [bm.verts.new((px, py, z_bottom + h * iy / segY)) for iy in range(segY + 1)]
        grid.append(col)
    for ix in range(segX):
        for iy in range(segY):
            bm.faces.new((grid[ix][iy], grid[ix + 1][iy], grid[ix + 1][iy + 1], grid[ix][iy + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    o.modifiers.new('Thick', 'SOLIDIFY').thickness = 0.004
    return o

def create_materials():
    M = {
        'wall': mat('Microcement', 'd5cec2', .94), 'ceil': mat('Ceiling', 'e6e0d6', 1),
        'floor': mat('Travertine', 'd4cab9', .34, clearcoat=.4), 'walnut': mat('Walnut', '5e4028', .46),
        'darkwood': mat('Dark_Walnut', '2e211a', .7), 'cream': mat('Boucle_Cream', 'e7dfd1', .92),
        'stone': mat('Coffee_Stone', 'd3c6b2', .34, clearcoat=.3), 'stonebase': mat('Stone_Base', 'c9bca6', .5),
        'rug': mat('Wool_Rug', 'b9aa94', .96),
        'glass': mat('Window_Glass', 'dbe7ea', .08, transmission=.35, alpha=.28),
        'black': mat('Screen_Black', '0b0b0b', .18, clearcoat=.7), 'brass': mat('Brass', 'b99d78', .34, .45),
        'led': mat('Warm_LED', 'ffd49a', 1, emission='ffd49a', strength=6),
        'ledwarm': mat('LED_Amber', 'ffbf78', 1, emission='ffbf78', strength=8),
        'plant': mat('Olive_Leaf', '59674c', .86),
        'vase': mat('Vase', '514339', .36, clearcoat=.25),
        'olivepillow': mat('Pillow_Olive', '7c7f54', .9), 'sagepillow': mat('Pillow_Sage', '9a9c72', .9),
        'creampillow': mat('Pillow_Cream', 'e2dacd', .92),
        'knit': mat('Knit_Throw', 'd9cdb6', .98),
        'screenglow': mat('TV_Landscape', '6a5233', .6, emission='8a6a3f', strength=.5),
        'winouter': mat('Sky_Outer', 'ffe6bd', 1, emission='ffdca6', strength=1.5),
        'wininner': mat('Sky_Inner', 'fff2d8', 1, emission='fff0cf', strength=2.4, alpha=.85),
        'flame_o': mat('Flame_Outer', 'ff8a3c', .5, emission='ff6a1f', strength=14, alpha=.85),
        'flame_i': mat('Flame_Inner', 'ffd98a', .5, emission='ffcf6a', strength=22, alpha=.95),
        'shade': mat('Lamp_Shade', 'f3e7cf', .9, emission='ffcf8f', strength=3, alpha=.92),
        'ceramic': mat('Lamp_Ceramic', 'b8a488', .5, clearcoat=.2), 'swivel': mat('Swivel_Base', '2a241f', .4, .4),
        'pot': mat('Planter', 'cabfae', .55), 'trunk': mat('Tree_Trunk', '5b4a37', .85),
        'soil': mat('Soil', '2c2620', .9), 'cabinet': mat('Cabinet', 'e5ddce', .6),
        'ac': mat('AC_Unit', 'f4f1ea', .5),
    }
    for key, sc, st in [('wall', 14, .04), ('floor', 4, .035), ('walnut', 9, .09), ('cream', 80, .06), ('rug', 115, .06),
                        ('knit', 60, .12), ('olivepillow', 80, .05), ('sagepillow', 80, .05)]:
        micro_bump(M[key], sc, st)
    return M

def build_room(M):
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,0)); floor = bpy.context.object; floor.name='LR_Floor'; floor.scale=(W/2,D/2,1); floor.data.materials.append(M['floor'])
    tbox('LR_Wall_Back', (0,H/2,-D/2), (W,H,.05), M['wall'])
    tbox('LR_Wall_Left', (-W/2,H/2,0), (.05,H,D), M['wall'])
    tbox('LR_Wall_Right', (W/2,H/2,0), (.05,H,D), M['wall'])
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,H)); ceil=bpy.context.object; ceil.name='LR_Ceiling'; ceil.scale=(W/2,D/2,1); ceil.data.materials.append(M['ceil'])
    for i,(x,y,z,sx,sy,sz) in enumerate([(0,2.91,-2.68,W,.18,.64),(0,2.91,2.68,W,.18,.64),(-3.28,2.91,0,.64,.18,4.72),(3.28,2.91,0,.64,.18,4.72)]): tbox(f'LR_Tray_{i}',(x,y,z),(sx,sy,sz),M['ceil'])
    for i,(x,y,z,sx,sy,sz) in enumerate([(0,2.8,-2.37,6.3,.025,.02),(0,2.8,2.37,6.3,.025,.02),(-3.07,2.8,0,.02,.025,4.7),(3.07,2.8,0,.02,.025,4.7)]): tbox(f'LR_Cove_{i}',(x,y,z),(sx,sy,sz),M['led'])
    for i,(x,z) in enumerate([(1.65,1.6),(-1.6,1.6),(1.65,-1.6),(-1.6,-1.6),(0,.2)]):
        cyl(f'LR_Spot_Ring_{i}', T((x,H-.02,z)), .075,.012, M['darkwood']); cyl(f'LR_Spot_Disc_{i}',T((x,H-.03,z)),.052,.007,M['led'])
        s=light(f'LR_Ceiling_Spot_{i}','SPOT',T((x,H-.055,z)),260,'ffe1bc',.05,4); s.data.spot_size=math.radians(55); s.data.spot_blend=.75
    # wall-mounted AC unit (reference realism cue)
    tbox('LR_AC_Body',(-2.15,2.62,-2.9),(.92,.28,.18),M['ac'],.04)
    tbox('LR_AC_Vent',(-2.15,2.51,-2.86),(.86,.03,.16),M['stonebase'])

def build_media_wall(M):
    x=-W/2+.055; tbox('LR_Media_Back',(x,1.48,-.55),(.08,2.72,3.65),M['darkwood'])
    tbox('LR_TV_Stone',(x+.06,1.55,-.55),(.035,1.44,2.32),M['stone'],.01); tbox('LR_TV',(x+.09,1.55,-.55),(.035,.82,1.48),M['black'],.025)
    tbox('LR_TV_Screen',(x+.11,1.55,-.55),(.01,.74,1.38),M['screenglow'])
    tbox('LR_Media_Console',(x+.11,.25,-.55),(.38,.38,3.48),M['walnut'],.02)
    tbox('LR_Console_LED',(x+.31,.47,-.55),(.02,.022,3.25),M['led'])
    tbox('LR_Console_Underglow',(x+.24,.05,-.55),(.3,.015,3.3),M['ledwarm'])
    tbox('LR_Soundbar',(x+.2,.86,-.55),(.09,.07,1.35),M['black'],.02)
    # console styling
    cyl('LR_Console_Plant_Pot',T((x+.26,.45,.75)),.09,.16,M['darkwood'],vertices=18)
    for i in range(4):
        leaf=box(f'LR_Console_Leaf_{i}',T((x+.26+math.sin(i*1.6)*.09,.53+i*.045,.75+math.cos(i*1.6)*.07)),(.015,.045,.3),M['plant']); leaf.rotation_euler=Euler((0,0,(i-2)*.3))
    build_vase(M,(x+.26,.5,-1.75),'LR_Console',scale=.7)
    # linear fireplace with layered cone flames
    tbox('LR_Fireplace_Cavity',(x+.105,.72,-.55),(.06,.24,2.3),M['black'])
    tbox('LR_Fireplace_Bed',(x+.14,.62,-.55),(.05,.03,2.1),M['darkwood'])
    n=22
    for i in range(n):
        z=-1.55+(i/(n-1))*2.0; h=.13+abs(math.sin(i*1.7))*.14; r=.028+(i%3)*.006; j=(math.sin(i*3.1)*.5+.5)*.02
        cone(f'LR_Flame_O_{i}',T((x+.17+j,.66+h/2,z)),r*1.5,h,M['flame_o'])
        cone(f'LR_Flame_I_{i}',T((x+.17+j,.66+h*.42,z)),r,h*.7,M['flame_i'])
    light('LR_Fire_Glow','POINT',T((x+.32,.81,-.55)),110,'ff9a4a',.15,2.6)
    # upper floating shelf: led backing + framed art + trailing plant + vase
    tbox('LR_Shelf',(x+.12,2.42,.55),(.28,.06,1.9),M['walnut'],.01)
    tbox('LR_Shelf_LED',(x+.1,2.44,.55),(.02,.018,1.78),M['ledwarm'])
    tbox('LR_Shelf_Frame',(x+.14,2.7,.05),(.03,.42,.32),M['darkwood'],.005)
    tbox('LR_Shelf_Art',(x+.17,2.7,.05),(.008,.34,.24),M['screenglow'])
    build_vase(M,(x+.14,2.61,.95),'LR_Shelf',scale=.6)
    cyl('LR_Shelf_Pothos_Pot',T((x+.14,2.54,1.27)),.08,.14,M['darkwood'],vertices=16)
    for i in range(5):
        leaf=box(f'LR_Shelf_Pothos_{i}',T((x+.24,2.4-i*.06,1.27+math.sin(i)*.04)),(.02,.05,.14),M['plant']); leaf.rotation_euler=Euler((0,0,.4))
    # niches with picture lights
    for i,z in enumerate([-1.8,.7]):
        tbox(f'LR_Display_{i}',(x+.1,1.5,z),(.24,2.35,.68),M['darkwood'])
        for j,y in enumerate([.72,0,-.72]): tbox(f'LR_Display_{i}_Shelf_{j}',(x+.125,y+1.5,z),(.25,.025,.62),M['walnut'])
        p=light(f'LR_Display_Light_{i}','SPOT',T((x+.25,2.48,z)),35,'ffd29b',.05,1.3); p.rotation_euler=Euler((0,math.radians(-90),0)); p.data.spot_size=math.radians(65)

def build_window(M):
    z=-D/2+.04
    # golden-hour backdrop behind the glazing
    plane('LR_Sky_Outer', (0,z-.35,1.34), 2.3, 1.8, M['winouter'], rot=(90,0,0))
    plane('LR_Sky_Inner', (0,z-.3,1.89), 1.5, .9, M['wininner'], rot=(90,0,0))
    tbox('LR_Window',(0,1.54,z),(3.55,2.55,.025),M['glass'])
    for i,x in enumerate([-1.15,0,1.15]): tbox(f'LR_Window_Mullion_{i}',(x,1.54,z+.03),(.035,2.62,.05),M['ceil'])
    tbox('LR_Window_Head',(0,2.86,z+.03),(3.7,.05,.06),M['ceil']); tbox('LR_Window_Sill',(0,.22,z+.03),(3.7,.05,.06),M['ceil'])
    # continuous folded sheers
    folded_curtain('LR_Sheer_L', -1.75, 1.55, z+.18, .07, 2.85, M['glass'] if False else mat('Sheer','f2ece1',.95,emission='ffdca8',strength=.55,alpha=.62))
    folded_curtain('LR_Sheer_R', 1.75, 1.55, z+.18, .07, 2.85, mat('Sheer2','f2ece1',.95,emission='ffdca8',strength=.55,alpha=.62))
    tbox('LR_Curtain_Rod',(0,2.96,z+.15),(4.95,.045,.045),M['brass'])
    for x in [-2.4,2.4]: sphere(f'LR_Rod_Finial_{x}',T((x,2.96,z+.15)),.05,M['brass'])

def build_sectional(M):
    for name,p,s,r in [('Base_Back',(0.95,.42,-1.58),(3.8,.62,.88),.22),('Base_Chaise',(2.38,.42,-.1),(.95,.62,2.25),.22),('Back_Back',(1,.93,-1.93),(3.65,.64,.23),.11),('Back_Chaise',(2.82,.93,-.15),(.23,.64,2.05),.11)]: tbox('LR_Sofa_'+name,p,s,M['cream'],r)
    for i,x in enumerate([-.2,.85,1.85]): tbox(f'LR_Sofa_Seat_{i}',(x,.78,-1.58),(.86+(i%2)*.05,.16,.76),M['cream'],.11)
    tbox('LR_Sofa_Chaise_Back',(2.02,.78,-.1),(.72,.16,1.9),M['cream'],.11)
    # varied throw pillows (colour + tilt)
    pillows=[((-.2,1.12,-1.32),(.66,.5,.16),M['creampillow'],(0,6,3)),((.75,1.1,-1.33),(.62,.46,.16),M['olivepillow'],(0,-5,-3)),
             ((1.72,1.14,-1.31),(.7,.52,.16),M['sagepillow'],(0,3,5)),((2.02,.72,.72),(.62,.46,.16),M['olivepillow'],(7,0,6)),
             ((2.02,.74,-.28),(.6,.44,.16),M['creampillow'],(6,0,-3))]
    for i,(p,s,m,rot) in enumerate(pillows):
        o=tbox(f'LR_Pillow_{i}',p,s,m,.08); o.rotation_euler=Euler([math.radians(a) for a in (rot[0],rot[2],rot[1])])

def build_throw(M):
    # chunky knit throw draped over the right arm, cascading to the seat
    segs=[((1.85,.86,-.35),(.62,.1,.7),0),((1.9,.7,0),(.58,.09,.42),29),((1.93,.5,.15),(.55,.08,.34),52),((1.95,.3,.2),(.5,.07,.26),63)]
    for i,(p,s,tilt) in enumerate(segs):
        o=tbox(f'LR_Throw_{i}',p,s,M['knit'],.05); o.rotation_euler=Euler((math.radians(tilt),0,math.radians(-9)))

def build_rug_table(M):
    tbox('LR_Rug',(.32,.025,.12),(4.65,.04,3.28),M['rug'],.08)
    # round travertine top on a fluted drum base
    cyl('LR_CoffeeTop',T((.15,.4,.18)),.72,.11,M['stone'])
    cyl('LR_CoffeeBase',T((.15,.2,.18)),.53,.32,M['stonebase'])
    for i in range(22):
        a=(i/22)*math.pi*2; box(f'LR_Coffee_Flute_{i}',T((.15+math.cos(a)*.53,.2,.18+math.sin(a)*.53)),(.03,.05,.32),M['stonebase'])
    tbox('LR_Book_1',(.31,.475,.23),(.3,.04,.2),mat('Book_Linen','d8d0c4',.72)); tbox('LR_Book_2',(.33,.515,.25),(.28,.04,.18),mat('Book_Taupe','8d7760',.68))
    cyl('LR_Tray',T((-.07,.475,.28)),.19,.02,mat('Tray','2a2420',.4,.3),vertices=32)
    tbox('LR_Remote',(.57,.48,-.12),(.055,.025,.15),M['black'],.012)
    cyl('LR_Candle',T((-.07,.505,.28)),.05,.07,mat('Candle','e9e1d4',.54,clearcoat=.18),vertices=16)
    light('LR_Candle_Glow','POINT',T((-.07,.6,.28)),4,'ffbd70',.03,.55)
    build_vase(M,(.27,.455,.18),'LR_Table')

def build_vase(M,p,tag,scale=1.0):
    cyl(tag+'_Vase',T(p),.12*scale,.28*scale,M['vase'],vertices=20)
    for i in range(5):
        leaf=box(tag+'_Leaf_'+str(i),T((p[0]+math.sin(i*1.4)*.13*scale,p[1]+(.3+i*.06)*scale,p[2]+math.cos(i*1.4)*.1*scale)),(.018*scale,.055*scale,.42*scale),M['plant']); leaf.rotation_euler=Euler((0,0,(i-2)*.28))

def build_chair(M):
    # barrel boucle swivel chair
    cx,cz=-1.55,1.15
    cyl('LR_Chair_Drum',T((cx,.42,cz)),.5,.42,M['cream'],vertices=40)
    torus('LR_Chair_Back',T((cx,.5,cz)),.46,.16,M['cream'],rot=(90,0,0))
    tbox('LR_Chair_Seat',(cx,.5,cz+.02),(.72,.16,.7),M['cream'],.08)
    cyl('LR_Chair_Swivel',T((cx,.05,cz)),.3,.06,M['swivel'],vertices=32)

def build_divider(M):
    tbox('LR_Divider_Frame',(-1.75,1.5,2.18),(2.5,.08,.28),M['walnut'])
    for i in range(12): tbox(f'LR_Divider_Slat_{i}',(-2.86+i*.135,1.55,2.18),(.06,2.4,.10),M['walnut'])
    for i,y in enumerate([2.32,1.62,.92]):
        tbox(f'LR_Divider_Shelf_{i}',(-2.35,y,2.18),(1.0,.05,.34),M['walnut'])
        tbox(f'LR_Divider_Shelf_LED_{i}',(-2.35,y+.03,2.05),(.9,.015,.02),M['ledwarm'])
    build_vase(M,(-2.35,1.72,2.2),'LR_Divider_A',scale=.7); build_vase(M,(-2.55,1.02,2.2),'LR_Divider_B',scale=.55)
    tbox('LR_Divider_Cabinet',(-2.12,.28,2.18),(1.64,.52,.5),M['cabinet'],.03)
    build_vase(M,(-2.55,.58,2.18),'LR_Divider_C')

def build_tree(M,p,h,tag):
    cyl(tag+'_Pot',T((p[0],.24,p[2])),.19,.48,M['pot'],vertices=24)
    cyl(tag+'_Soil',T((p[0],.46,p[2])),.17,.04,M['soil'],vertices=24)
    cyl(tag+'_Trunk',T((p[0]+.01,.42+(h-.42)/2,p[2])),.03,h-.42,M['trunk'],vertices=10)
    for i in range(42):
        a=i*2.4; ry=.45+random.random()*(h-.9); rad=.28*(1-(ry/h)*.3)*(.4+random.random()*.9); s=.5+random.random()*.5
        leaf=box(f'{tag}_Leaf_{i}',T((p[0]+math.cos(a)*rad,.42+ry,p[2]+math.sin(a)*rad)),(.11*s,.05*s,.03),M['plant'])
        leaf.rotation_euler=Euler((random.random(),random.random()*6,random.random()))

def build_lamps(M):
    # side table + table lamp
    stx,stz=3.0,1.7
    cyl('LR_Side_Table_Top',T((stx,.28,stz)),.3,.05,M['walnut'],vertices=32)
    for i in range(16):
        a=(i/16)*math.pi*2; box(f'LR_Side_Flute_{i}',T((stx+math.cos(a)*.24,.14,stz+math.sin(a)*.24)),(.03,.04,.28),M['walnut'])
    cyl('LR_Lamp_Base',T((stx,.42,stz)),.075,.22,M['ceramic'],vertices=24)
    cyl('LR_Lamp_Shade',T((stx,.62,stz)),.19,.2,M['shade'],vertices=32)
    light('LR_Table_Lamp','POINT',T((stx,.62,stz)),95,'ffcd85',.14,3.2)
    cyl('LR_Side_Candle',T((stx+.16,.33,stz+.08)),.03,.06,mat('SideCandle','e7ddcb',.6,emission='ffb45a',strength=1),vertices=16)
    # floor lamp
    flx,flz=3.15,-1.6
    cyl('LR_Floor_Lamp_Base',T((flx,.02,flz)),.17,.04,M['swivel'],vertices=24)
    cyl('LR_Floor_Lamp_Stem',T((flx,.85,flz)),.018,1.7,M['brass'],vertices=12)
    cyl('LR_Floor_Lamp_Shade',T((flx,1.68,flz)),.2,.24,M['shade'],vertices=32)
    light('LR_Floor_Lamp_Glow','POINT',T((flx,1.62,flz)),120,'ffcd85',.16,4)

def build_decor_lighting(M):
    for i,(x,z) in enumerate([(-2.85,-1.75),(2.92,-2.1)]):
        build_vase(M,(x,.25,z),f'LR_Floor_{i}'); light(f'LR_PlantGlow_{i}','POINT',T((x,1.0,z+.2)),45 if i else 28,'ffd19b',.25,2.2)
    world=bpy.context.scene.world or bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(*hx('fff0da'),1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.14
    # warm golden key from the window side (evening)
    sun=light('LR_Key_Sun','SUN',T((-1.5,4.2,-3.8)),1.9,'ffd9a0'); sun.rotation_euler=Euler(tuple(math.radians(a) for a in (128,-8,10))); sun.data.angle=math.radians(4)
    # cooler room-side fill for depth
    fill=light('LR_Fill_Sun','SUN',T((3.5,3.5,4.0)),.5,'cfe0f2'); fill.rotation_euler=Euler(tuple(math.radians(a) for a in (55,12,-30)))
    light('LR_Window_Bounce','POINT',T((0,1.7,-2.35)),85,'ffe8ce',.5,5); light('LR_Room_Bounce','POINT',T((0,2.15,-1.5)),45,'ffe0b2',.4,7)

def setup_camera(scene):
    target=bpy.data.objects.new('LR_Camera_Target',None); bpy.context.collection.objects.link(target); target.location=T((0,.9,-.25))
    bpy.ops.object.camera_add(location=T((4.65,2.25,6.85))); cam=bpy.context.object; cam.name='LR_Camera_Main'; cam.data.lens=47; cam.data.sensor_fit='VERTICAL'
    c=cam.constraints.new('TRACK_TO'); c.target=target; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'; cam.data.dof.use_dof=True; cam.data.dof.focus_distance=7.0; cam.data.dof.aperture_fstop=7.2; scene.camera=cam
    # Portrait camera is kept in the file for client-facing 2:3 deliverables.
    bpy.ops.object.camera_add(location=T((4.15,2.12,6.55))); portrait=bpy.context.object; portrait.name='LR_Camera_Portrait'; portrait.data.lens=52; portrait.data.sensor_fit='VERTICAL'
    pcon=portrait.constraints.new('TRACK_TO'); pcon.target=target; pcon.track_axis='TRACK_NEGATIVE_Z'; pcon.up_axis='UP_Y'

def setup_render(scene):
    scene.render.engine='CYCLES'; scene.cycles.samples=SAMPLES; scene.cycles.use_denoising=True; scene.render.resolution_x,scene.render.resolution_y=RESOLUTION; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.filepath='//livingroom_render.png'
    try: scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'
    except (TypeError,ValueError): scene.view_settings.view_transform='Filmic'; scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=.2

def main():
    scene=setup_scene(); setup_render(scene); M=create_materials()
    build_room(M); build_media_wall(M); build_window(M); build_sectional(M); build_throw(M)
    build_rug_table(M); build_chair(M); build_divider(M)
    build_tree(M,(-0.95,0,-2.35),1.75,'LR_Tree_A'); build_tree(M,(1.5,0,-2.4),1.55,'LR_Tree_B')
    build_lamps(M); build_decor_lighting(M); setup_camera(scene)
    if '--portrait' in sys.argv:
        scene.camera=bpy.data.objects['LR_Camera_Portrait']; scene.render.resolution_x,scene.render.resolution_y=(1080,1620); scene.render.filepath='//livingroom_portrait.png'
    print(f'Living room complete: {len(scene.objects)} objects | {len(bpy.data.materials)} materials')
    if '--render' in sys.argv: bpy.ops.render.render(write_still=True)

main()
