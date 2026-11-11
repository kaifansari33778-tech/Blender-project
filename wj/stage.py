"""Render/camera/sky setup shared by every set."""
import bpy, math
from mathutils import Vector


def new_scene(res=(720, 1280), samples=12, fps=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    c = s.cycles
    c.samples = samples; c.use_adaptive_sampling = False
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.max_bounces = 5; c.diffuse_bounces = 2; c.glossy_bounces = 2; c.transmission_bounces = 4
    c.transparent_max_bounces = 6; c.volume_bounces = 0
    c.caustics_reflective = False; c.caustics_refractive = False
    c.sample_clamp_indirect = 6.0
    c.use_fast_gi = False
    s.render.use_persistent_data = True
    s.render.resolution_x, s.render.resolution_y = res
    s.render.fps = fps
    s.render.image_settings.file_format = 'JPEG'; s.render.image_settings.quality = 95
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam); s.camera = cam
    cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 24
    cam.data.clip_start = 0.05; cam.data.clip_end = 800
    return s, cam


def sky(scene, elevation=38, rotation=140, strength=0.18, sun_intensity=1.0, air=1.0, dust=1.5, exposure=0.0, sun_size=0.8):
    """Physical sky with a real sun disc. rotation: compass angle of the sun in degrees."""
    w = bpy.data.worlds.new('sky'); scene.world = w; w.use_nodes = True
    nt = w.node_tree
    sk = nt.nodes.new('ShaderNodeTexSky')
    sk.sky_type = 'MULTIPLE_SCATTERING'
    sk.sun_elevation = math.radians(elevation); sk.sun_rotation = math.radians(rotation)
    sk.sun_intensity = sun_intensity; sk.sun_size = math.radians(sun_size)
    sk.air_density = air; sk.aerosol_density = dust
    bg = nt.nodes['Background']; bg.inputs['Strength'].default_value = strength
    nt.links.new(sk.outputs[0], bg.inputs['Color'])
    scene.view_settings.exposure = exposure
    return sk


def look(cam, pos, tgt, lens=50, roll=0.0, fstop=None, focus=None):
    cam.location = Vector(pos)
    d = Vector(tgt) - Vector(pos)
    q = d.to_track_quat('-Z', 'Y')
    cam.rotation_euler = q.to_euler()
    if roll:
        cam.rotation_euler.rotate_axis('Z', roll)
    cam.data.lens = lens
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus if focus else d.length
    else:
        cam.data.dof.use_dof = False
