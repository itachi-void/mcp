"""Cinematic flythrough setup for Blender.

Run in Blender's Scripting workspace. It creates non-destructive, prefixed
collections, cameras, editable route curves and timeline markers. Adjust the
route control points in the 3D viewport to match the apartment geometry before
rendering. Existing scene objects are never deleted.
"""

import bpy
from mathutils import Vector


FPS = 24
DURATION_SECONDS = 36
END_FRAME = FPS * DURATION_SECONDS
PREFIX = "CINE_"


def collection(name):
    existing = bpy.data.collections.get(name)
    if existing:
        return existing
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_only(obj, col):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)


def clear_prefixed_objects(col):
    for obj in list(col.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)


def curve_path(name, points, col):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 24
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO_CLAMPED"
        point.handle_right_type = "AUTO_CLAMPED"
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    return obj


def make_camera(name, route, col, sensor_fit):
    camera_data = bpy.data.cameras.new(name)
    camera_data.lens = 24
    camera_data.sensor_fit = sensor_fit
    camera = bpy.data.objects.new(name, camera_data)
    col.objects.link(camera)

    follow = camera.constraints.new("FOLLOW_PATH")
    follow.name = "Cinematic Route"
    follow.target = route
    follow.use_curve_follow = True
    follow.forward_axis = "FORWARD_X"
    follow.up_axis = "UP_Z"
    # Each route point maps to a planned beat. This avoids a mechanically
    # uniform pass and leaves time for the reveals and final hold.
    beat_frames = [1, 49, 97, 193, 289, 385, 481, 577, 673, 769, 840, END_FRAME]
    for frame, factor in zip(beat_frames, [0.0, 0.055, 0.14, 0.28, 0.42, 0.56, 0.68, 0.80, 0.90, 0.975, 1.0, 1.0]):
        follow.offset_factor = factor
        follow.keyframe_insert("offset_factor", frame=frame)

    for curve in camera.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"
    # 32mm removes perspective stretch in the private corridor and bedroom.
    camera_data.lens = 24
    camera_data.keyframe_insert("lens", frame=1)
    camera_data.lens = 32
    camera_data.keyframe_insert("lens", frame=481)
    camera_data.keyframe_insert("lens", frame=672)
    camera_data.lens = 24
    camera_data.keyframe_insert("lens", frame=673)
    return camera


def marker(frame, label):
    bpy.context.scene.timeline_markers.new(label, frame=frame)


def add_markers():
    for item in list(bpy.context.scene.timeline_markers):
        if item.name.startswith(PREFIX):
            bpy.context.scene.timeline_markers.remove(item)
    labels = [
        (1, "CINE_01 Dark close-up"),
        (32, "CINE_Rack focus start"),
        (72, "CINE_Occlusion start"),
        (97, "CINE_02 Hero reveal / living"),
        (193, "CINE_03 Sofa to travertine"),
        (270, "CINE_Match cut travertine"),
        (289, "CINE_04 Kitchen island"),
        (360, "CINE_Shadow wipe"),
        (385, "CINE_05 Dining / terrace"),
        (416, "CINE_Rack focus start"),
        (481, "CINE_06 Private corridor"),
        (552, "CINE_Doorframe occlusion"),
        (577, "CINE_07 Bedroom"),
        (648, "CINE_Match cut light line"),
        (673, "CINE_08 Return transition"),
        (720, "CINE_Shadow wipe complete"),
        (769, "CINE_09 Final hero rise"),
        (840, "CINE_Hero hold"),
        (864, "CINE_END"),
    ]
    for frame, label in labels:
        marker(frame, label)


def configure_scene():
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = END_FRAME
    scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth = "16"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    if hasattr(scene, "view_settings"):
        scene.view_settings.look = "Medium High Contrast"


def main():
    configure_scene()
    routes = collection("CINE_Routes")
    cameras = collection("CINE_Cameras")
    clear_prefixed_objects(routes)
    clear_prefixed_objects(cameras)

    # Placeholder coordinates in metres. Edit these in the 3D viewport.
    # X = progress through the apartment, Y = lateral offset, Z = camera height.
    route_16_9 = curve_path(
        "CINE_Route_16x9",
        [(-5.5, 0.0, 1.45), (-4.5, 0.0, 1.45), (-3.0, 0.6, 1.50),
         (-1.0, 1.0, 1.52), (1.0, 0.8, 1.50), (2.5, 0.0, 1.48),
         (3.8, -0.3, 1.48), (2.6, 0.2, 1.55), (0.0, 0.4, 1.82)],
        routes,
    )
    route_9_16 = curve_path(
        "CINE_Route_9x16",
        [(-5.5, -0.1, 1.35), (-4.6, 0.0, 1.48), (-3.1, 0.4, 1.65),
         (-1.2, 0.8, 1.48), (0.8, 0.6, 1.62), (2.4, 0.0, 1.48),
         (3.6, -0.2, 1.55), (2.4, 0.2, 1.68), (0.0, 0.35, 2.05)],
        routes,
    )
    cam_16_9 = make_camera("CINE_Camera_16x9", route_16_9, cameras, "HORIZONTAL")
    cam_9_16 = make_camera("CINE_Camera_9x16", route_9_16, cameras, "VERTICAL")
    bpy.context.scene.camera = cam_16_9
    add_markers()
    print("Cinematic setup created. Select CINE_Route_16x9 or CINE_Route_9x16 and edit its Bezier points.")
    print("For 9:16 set resolution to 2160x3840 and make CINE_Camera_9x16 active.")


if __name__ == "__main__":
    main()
