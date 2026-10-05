"""
Organic Luxury Dining Room — Blender scene builder
Mirrors src/components/dining/DiningScene.tsx (photoreal, warm evening identity).
Blender 3.6+ / 4.x | Cycles | output: //dining_render.png

Shares the apartment's material identity (travertine / walnut / boucle / greige)
and evening light balance: warm golden key from the window + cool room-side fill.
Signature pieces: oval travertine table on a fluted pedestal, boucle dining chairs,
a double-ring suspended chandelier, a fluted-walnut feature wall, and a floating buffet.
"""
import bpy
import bmesh
import math
import random
import sys
from mathutils import Euler

W, D, H = 6.0, 5.0, 3.0
SAMPLES, RESOLUTION = 512, (1920, 1080)
random.seed(11)

def hx(v):
    v = v.lstrip('#'); return tuple(int(v[i:i+2], 16) / 255 for i in (0, 2, 4))

def T(p): return (p[0], p[2], p[1])
def TS(s): return (s[0], s[2], s[1])

def setup_scene(name='Dining_Scene'):
    """Isolates this room: only objects/materials belonging to its scene are removed."""
    scene = bpy.data.scenes.get(name)
    if not scene:
        scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    for obj in list(scene.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for mat in list(bpy.data.materials):
        if mat.name.startswith('DR_') and mat.users == 0: bpy.data.materials.remove(mat)
    return scene

def mat(name, color, rough=0.5, metal=0, emission=None, strength=0, clearcoat=0, transmission=0, alpha=1):
    m = bpy.data.materials.new('DR_' + name); m.use_nodes = True
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

def tbox(name, p, s, material, bevel=0, rot=None):
    o = box(name, T(p), TS(s), material, bevel)
    if rot: o.rotation_euler = Euler([math.radians(a) for a in (rot[0], rot[2], rot[1])])
    return o

def cyl(name, loc, radius, depth, material, scale=(1,1,1), rot=None, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); return o

def torus(name, loc, major, minor, material, rot=None):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=major, minor_radius=minor, major_segments=60, minor_segments=20)
    o = bpy.context.object; o.name = name
    if rot: o.rotation_euler = Euler([math.radians(x) for x in rot])
    o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o

def sphere(name, loc, radius, material, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=radius, location=loc)
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
    bm = bmesh.new(); segX, segY = folds * 6, 8; h = z_top - z_bottom
    grid = []
    for ix in range(segX + 1):
        t = ix / segX; px = center_x - width / 2 + width * t
        py = wall_y + math.sin(t * math.pi * 2 * folds) * depth
        grid.append([bm.verts.new((px, py, z_bottom + h * iy / segY)) for iy in range(segY + 1)])
    for ix in range(segX):
        for iy in range(segY):
            bm.faces.new((grid[ix][iy], grid[ix + 1][iy], grid[ix + 1][iy + 1], grid[ix][iy + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(material); o.modifiers.new('Thick', 'SOLIDIFY').thickness = 0.004
    return o

def create_materials():
    M = {
        'wall': mat('Microcement', 'd5cec2', .94), 'ceil': mat('Ceiling', 'e6e0d6', 1),
        'floor': mat('Travertine', 'd4cab9', .34, clearcoat=.4), 'walnut': mat('Walnut', '5e4028', .46),
        'darkwood': mat('Dark_Walnut', '2e211a', .7), 'cream': mat('Boucle_Cream', 'e7dfd1', .92),
        'stone': mat('Table_Travertine', 'cabca6', .34, clearcoat=.28), 'stonebase': mat('Stone_Base', 'c2b49c', .5),
        'rug': mat('Wool_Rug', 'b9aa94', .96), 'brass': mat('Brass', 'b99d78', .34, .55),
        'glass': mat('Window_Glass', 'dbe7ea', .08, transmission=.35, alpha=.28),
        'black': mat('Dark_Ceramic', '171513', .3), 'led': mat('Warm_LED', 'ffd49a', 1, emission='ffd49a', strength=6),
        'ledwarm': mat('LED_Amber', 'ffbf78', 1, emission='ffbf78', strength=8), 'plant': mat('Olive_Leaf', '59674c', .86),
        'winouter': mat('Sky_Outer', 'ffe6bd', 1, emission='ffdca6', strength=1.5),
        'wininner': mat('Sky_Inner', 'fff2d8', 1, emission='fff0cf', strength=2.3, alpha=.85),
        'sheer': mat('Sheer', 'f2ece1', .95, emission='ffdca8', strength=.55, alpha=.62),
        'ring': mat('Chandelier_Ring', 'f6e9cf', .5, emission='ffcf8f', strength=2.6),
        'plate': mat('Plate', 'efe9dd', .35, clearcoat=.3), 'plate2': mat('Plate_Inner', 'd8cdb8', .4),
        'candle': mat('Candle', 'efe7d7', .5), 'flame': mat('Flame', 'ffcf7a', .5, emission='ff9a3c', strength=8),
        'runner': mat('Runner', 'cfc4b2', .85), 'mirror': mat('Mirror', 'b7c3c7', .08, .9),
        'pampas': mat('Pampas', 'cdbd9c', .95), 'ceramic': mat('Ceramic', 'd8ccb8', .5),
        'pot': mat('Planter', 'cabfae', .55), 'trunk': mat('Tree_Trunk', '5b4a37', .85), 'soil': mat('Soil', '2c2620', .9),
        'art': mat('Artwork', '8a7f6d', .7, emission='6a6152', strength=.25),
    }
    for key, sc, st in [('wall', 14, .04), ('floor', 4, .035), ('walnut', 9, .09), ('cream', 80, .06), ('rug', 115, .06)]:
        micro_bump(M[key], sc, st)
    return M

def build_room(M):
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,0)); f=bpy.context.object; f.name='DR_Floor'; f.scale=(W/2,D/2,1); f.data.materials.append(M['floor'])
    tbox('DR_Wall_Back',(0,H/2,-D/2),(W,H,.05),M['wall']); tbox('DR_Wall_Left',(-W/2,H/2,0),(.05,H,D),M['wall']); tbox('DR_Wall_Right',(W/2,H/2,0),(.05,H,D),M['wall'])
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0,0,H)); c=bpy.context.object; c.name='DR_Ceiling'; c.scale=(W/2,D/2,1); c.data.materials.append(M['ceil'])
    for i,(x,y,z,sx,sy,sz) in enumerate([(0,2.91,-2.18,W,.18,.6),(0,2.91,2.18,W,.18,.6),(-2.7,2.91,0,.6,.18,3.8),(2.7,2.91,0,.6,.18,3.8)]): tbox(f'DR_Tray_{i}',(x,y,z),(sx,sy,sz),M['ceil'])
    for i,(x,y,z,sx,sy,sz) in enumerate([(0,2.8,-1.88,5.2,.025,.02),(0,2.8,1.88,5.2,.025,.02),(-2.4,2.8,0,.02,.025,3.76),(2.4,2.8,0,.02,.025,3.76)]): tbox(f'DR_Cove_{i}',(x,y,z),(sx,sy,sz),M['led'])
    for i,(x,z) in enumerate([(1.9,1.5),(-1.9,1.5),(1.9,-1.5),(-1.9,-1.5)]):
        cyl(f'DR_Spot_Ring_{i}',T((x,H-.02,z)),.075,.012,M['darkwood']); cyl(f'DR_Spot_Disc_{i}',T((x,H-.03,z)),.052,.007,M['led'])
        s=light(f'DR_Ceiling_Spot_{i}','SPOT',T((x,H-.055,z)),230,'ffe1bc',.05,4); s.data.spot_size=math.radians(56); s.data.spot_blend=.78

def build_feature_wall(M):
    x=-W/2+.03; tbox('DR_Feature_Back',(x,1.5,0),(.04,2.7,3.7),mat('Feature_Base','4a3728',.6))
    for i in range(22): tbox(f'DR_Feature_Slat_{i}',(x+.05,1.5,-1.75+i*.16),(.06,2.6,.09),M['walnut'])
    tbox('DR_Art_Frame',(x+.12,1.65,0),(.05,1.35,.95),M['darkwood']); tbox('DR_Art',(x+.15,1.65,0),(.015,1.2,.82),M['art'])
    p=light('DR_Art_Light','SPOT',T((x+.45,2.45,0)),30,'ffd7a0',.05,2.2); p.rotation_euler=Euler((0,math.radians(-90),0)); p.data.spot_size=math.radians(60)

def build_window(M):
    z=-D/2+.04
    plane('DR_Sky_Outer',(0,z-.32,1.34),2.2,1.7,M['winouter'],rot=(90,0,0)); plane('DR_Sky_Inner',(0,z-.28,1.84),1.4,.85,M['wininner'],rot=(90,0,0))
    tbox('DR_Window',(0,1.54,z),(3.3,2.5,.025),M['glass'])
    for i,x in enumerate([-1.05,0,1.05]): tbox(f'DR_Mullion_{i}',(x,1.54,z+.03),(.035,2.56,.05),M['ceil'])
    tbox('DR_Window_Head',(0,2.83,z+.03),(3.45,.05,.06),M['ceil']); tbox('DR_Window_Sill',(0,.25,z+.03),(3.45,.05,.06),M['ceil'])
    folded_curtain('DR_Sheer_L',-1.55,1.45,z+.18,.1,2.8,M['sheer']); folded_curtain('DR_Sheer_R',1.55,1.45,z+.18,.1,2.8,M['sheer'])
    tbox('DR_Curtain_Rod',(0,2.94,z+.15),(4.6,.045,.045),M['brass'])
    for x in [-2.25,2.25]: sphere(f'DR_Rod_Finial_{x}',T((x,2.94,z+.15)),.05,M['brass'])

def build_table(M):
    cyl('DR_Table_Top',T((0,.75,0)),.85,.08,M['stone'],scale=(1.55,1,1),vertices=64)
    cyl('DR_Table_Ped',T((0,.4,0)),.46,.62,M['stonebase'],scale=(1.15,1,1),vertices=48)
    for i in range(26):
        a=(i/26)*math.pi*2; box(f'DR_Ped_Flute_{i}',T((math.cos(a)*.55*1.15,.4,math.sin(a)*.47)),(.03,.05,.62),M['stonebase'])
    cyl('DR_Table_Foot',T((0,.11,0)),.63,.06,M['stonebase'],scale=(1.2,1,1),vertices=48)
    build_tablescape(M)

def build_tablescape(M):
    y=.79; tbox('DR_Runner',(0,y+.005,0),(2.1,.008,.42),M['runner'])
    cyl('DR_Bowl',T((0,y+.05,0)),.16,.09,M['black'],scale=(1,1,.85),vertices=28)
    for i in range(6):
        b=box(f'DR_Branch_{i}',T((math.sin(i*1.3)*.12,y+.24+(i%2)*.05,math.cos(i*1.3)*.08)),(.012,.03,.36),M['plant']); b.rotation_euler=Euler((0,0,(i-2.5)*.3))
    for x in [-.62,.62]:
        cyl(f'DR_Holder_{x}',T((x,y+.02,0)),.06,.04,M['brass'],vertices=20)
        cyl(f'DR_Taper_{x}',T((x,y+.14,0)),.019,.22,M['candle'],vertices=16)
        sphere(f'DR_Wick_{x}',T((x,y+.27,0)),.02,M['flame']); light(f'DR_Candle_Glow_{x}','POINT',T((x,y+.3,0)),5,'ffb45a',.02,.9)
    for i,(x,zz) in enumerate([(-1.05,.55),(-1.05,-.55),(0,.6),(0,-.6),(1.05,.55),(1.05,-.55)]):
        cyl(f'DR_Plate_{i}',T((x,y+.01,zz)),.15,.012,M['plate'],vertices=32); cyl(f'DR_Plate_In_{i}',T((x,y+.022,zz)),.1,.014,M['plate2'],vertices=32)

def build_chairs(M):
    for i,(x,z,ry) in enumerate([(-1.05,1.05,0),(0,1.05,0),(1.05,1.05,0),(-1.05,-1.05,180),(0,-1.05,180),(1.05,-1.05,180)]):
        build_chair(M,(x,0,z),ry,f'DR_Chair_{i}')

def build_chair(M,p,ry,tag):
    r=math.radians(ry); cx,cz=p[0],p[2]
    def rp(dx,dz):
        return (cx+dx*math.cos(r)-dz*math.sin(r), 0, cz+dx*math.sin(r)+dz*math.cos(r))
    s=rp(0,0); tbox(tag+'_Seat',(s[0],.47,s[2]),(.5,.12,.48),M['cream'],.06)
    b=rp(0,-.24); back=tbox(tag+'_Back',(b[0],.75,b[2]),(.46,.5,.12),M['cream'],.09); back.rotation_euler=Euler((0,r,0))
    c=rp(0,-.22); curve=cyl(tag+'_Back_Curve',T((c[0],.75,c[2])),.26,.56,M['cream'],rot=(90,ry,0),vertices=32)
    for dx,dz in [(-.2,-.2),(.2,-.2),(-.2,.2),(.2,.2)]:
        lp=rp(dx,dz); cyl(f'{tag}_Leg_{dx}_{dz}',T((lp[0],.2,lp[2])),.025,.42,M['walnut'],vertices=12)

def build_chandelier(M):
    for i in range(2):
        torus(f'DR_Ring_{i}',T((i*.32,2.28-i*.06,0)),.62-i*.22,.035,M['ring'])
    for x in [-.5,.5]: cyl(f'DR_Rod_{x}',T((x,2.64,0)),.004,.72,M['brass'],vertices=8)
    cyl('DR_Canopy',T((0,3.0,0)),.06,.03,M['brass'],vertices=20)
    light('DR_Chandelier_Key','POINT',T((0,2.15,0)),140,'ffcd85',.16,5); light('DR_Chandelier_Fill','POINT',T((0,1.55,0)),55,'ffdca0',.12,3)

def build_sideboard(M):
    x=W/2-.04
    tbox('DR_Buffet',(x-.28,.68,.4),(.5,.62,2.4),M['walnut'],.02)
    tbox('DR_Buffet_Underglow',(x-.28,.375,.4),(.42,.012,2.3),M['ledwarm'])
    for z in [-.4,.4,1.2]: tbox(f'DR_Buffet_Seam_{z}',(x-.03,.68,z),(.01,.6,.012),M['darkwood'])
    cyl('DR_Mirror',T((x-.02,1.85,.4)),.55,.04,M['mirror'],rot=(0,-90,0),vertices=48); torus('DR_Mirror_Frame',T((x-.04,1.85,.4)),.55,.03,M['brass'],rot=(0,0,90))
    cyl('DR_Pampas_Vase',T((x-.28,1.0,-.5)),.12,.34,M['ceramic'],vertices=24)
    for i in range(7):
        b=box(f'DR_Pampas_{i}',T((x-.28+math.sin(i*.9)*.1,1.35+i*.05,-.5+math.cos(i*.9)*.08)),(.016,.03,.42),M['pampas']); b.rotation_euler=Euler((0,0,(i-3)*.22))
    sphere('DR_Sculpture',T((x-.28,1.06,.5)),.1,M['black']); cyl('DR_Bowls',T((x-.28,1.05,1.05)),.12,.06,M['ceramic'],vertices=28)
    light('DR_Buffet_Glow','POINT',T((x-.5,1.5,.4)),50,'ffd6a0',.2,2.6)

def build_tree(M,p,h,tag):
    cyl(tag+'_Pot',T((p[0],.24,p[2])),.18,.48,M['pot'],vertices=24); cyl(tag+'_Soil',T((p[0],.46,p[2])),.16,.04,M['soil'],vertices=24)
    cyl(tag+'_Trunk',T((p[0]+.01,.42+(h-.42)/2,p[2])),.03,h-.42,M['trunk'],vertices=10)
    for i in range(40):
        a=i*2.4; ry=.45+random.random()*(h-.9); rad=.26*(1-(ry/h)*.3)*(.4+random.random()*.9); s=.5+random.random()*.5
        leaf=box(f'{tag}_Leaf_{i}',T((p[0]+math.cos(a)*rad,.42+ry,p[2]+math.sin(a)*rad)),(.1*s,.05*s,.03),M['plant']); leaf.rotation_euler=Euler((random.random(),random.random()*6,random.random()))

def build_lighting():
    world=bpy.context.scene.world or bpy.data.worlds.new('World'); bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(*hx('fff0da'),1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.14
    sun=light('DR_Key_Sun','SUN',T((-1.2,4.2,-3.6)),1.85,'ffd9a0'); sun.rotation_euler=Euler(tuple(math.radians(a) for a in (126,-6,8))); sun.data.angle=math.radians(4)
    fill=light('DR_Fill_Sun','SUN',T((3.2,3.4,3.8)),.48,'cfe0f2'); fill.rotation_euler=Euler(tuple(math.radians(a) for a in (54,10,-28)))
    light('DR_Room_Bounce','POINT',T((0,2.2,0)),50,'ffe8ce',.4,6)

def setup_camera(scene):
    target=bpy.data.objects.new('DR_Camera_Target',None); bpy.context.collection.objects.link(target); target.location=T((0,.95,-.15))
    bpy.ops.object.camera_add(location=T((4.35,2.3,6.2))); cam=bpy.context.object; cam.name='DR_Camera_Main'; cam.data.lens=47; cam.data.sensor_fit='VERTICAL'
    c=cam.constraints.new('TRACK_TO'); c.target=target; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'; cam.data.dof.use_dof=True; cam.data.dof.focus_distance=6.4; cam.data.dof.aperture_fstop=7.0; scene.camera=cam
    bpy.ops.object.camera_add(location=T((3.95,2.18,5.95))); portrait=bpy.context.object; portrait.name='DR_Camera_Portrait'; portrait.data.lens=52; portrait.data.sensor_fit='VERTICAL'
    pcon=portrait.constraints.new('TRACK_TO'); pcon.target=target; pcon.track_axis='TRACK_NEGATIVE_Z'; pcon.up_axis='UP_Y'

def setup_render(scene):
    scene.render.engine='CYCLES'; scene.cycles.samples=SAMPLES; scene.cycles.use_denoising=True; scene.render.resolution_x,scene.render.resolution_y=RESOLUTION; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.filepath='//dining_render.png'
    try: scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'
    except (TypeError,ValueError): scene.view_settings.view_transform='Filmic'; scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=.2

def main():
    scene=setup_scene(); setup_render(scene); M=create_materials()
    build_room(M); build_feature_wall(M); build_window(M); build_table(M); build_chairs(M); build_chandelier(M); build_sideboard(M)
    build_tree(M,(2.35,0,-1.85),1.6,'DR_Tree'); build_lighting(); setup_camera(scene)
    if '--portrait' in sys.argv:
        scene.camera=bpy.data.objects['DR_Camera_Portrait']; scene.render.resolution_x,scene.render.resolution_y=(1080,1620); scene.render.filepath='//dining_portrait.png'
    print(f'Dining room complete: {len(scene.objects)} objects | {len(bpy.data.materials)} materials')
    if '--render' in sys.argv: bpy.ops.render.render(write_still=True)

main()
