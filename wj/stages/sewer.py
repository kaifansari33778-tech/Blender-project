"""London sewer: the tosher (No. 5) and the nightmares line."""
import math
from mathutils import Vector
from .. import sets, props, cast, stage
from ..world import mat, sphere
from ..anim import ramp, pulse, lerp, vlerp, noise, orient, smooth
from ..film import shoot
import bpy

BED = -0.1


def build(scene, cam):
    info = sets.sewer()
    stage.sky(scene, strength=0.0)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    scene.view_settings.exposure = 0.9
    tos = cast.tosher()
    lan = props.lantern(energy=160); lamp = bpy.data.objects[lan['light']]
    pole = props.pole(1.8); coin = props.coin(gold=True)
    hat = props.flatcap((0.09, 0.08, 0.07)); hat.location = (0, 0, -50)
    bone = props.lathe([(0, 0.012), (0.01, 0.016), (0.03, 0.008), (0.15, 0.007), (0.17, 0.015), (0.18, 0.011)], 8, mat('plain', c=(0.75, 0.7, 0.58), rough=0.5), 'bone')
    bone.location = (0, 0, -50)
    E0 = 160

    def flicker(t, k=1.0):
        lamp.data.energy = E0 * k * (1 + 0.12 * noise(t, 3, 9) + 0.06 * noise(t, 5, 23))

    def lantern_hand(t, h=1.25, fwd=0.42, side=-0.3):
        hp = tos.W((side, fwd, h + tos._pel[0].z))
        tos.hand('L', hp, fwd=tos.D((0, 1, 0.3)), palm=tos.D((1, 0, 0)), world=True); tos.fingers('L', 0.85); tos.elbow('L', (-0.9, -0.3, 0.9))
        sw = math.sin(t * 4.3) * 0.06
        orient(lan, tos.palm('L', 0.07, 0.03) - Vector((0, 0, 0.03)), z=(sw, sw * 0.5, 1))

    def wade(t, t0, t1, y0, y1, crouch=0.3):
        tos.walk(t, t0, t1, (0.15, y0, BED), (0.15, y1, BED), step=0.42, lift=0.1, swing=0.0, lean=0.3 + crouch * 0.5, arms='', hip=1.5, bob=0.03)
        P = tos._pel[0]
        tos.pelvis(right=P.x, up=P.z - 0.22 * crouch, rx=0.25 * crouch, rz=0)
        lantern_hand(t)
        # probing pole in the right hand
        gp = tos.W((0.32, 0.3, 0.95 + tos._pel[0].z))
        d = tos.D((0.15 * math.sin(t * 2.1), 0.75, -1)).normalized()
        tos.grip('R', gp, d, tos.D((-1, 0, 0))); tos.elbow('R', (0.9, -0.5, 0.9))
        orient(pole, gp + d * 0.55 + tos.D((-0.05, 0, 0)), z=d)
        tos.head(rx=-0.2 - crouch * 0.3, rz=0.3 * math.sin(t * 0.9)); tos.gaze(yaw=0.25 * math.sin(t * 0.9 + 0.5), pitch=0.1)
        tos.face(t, brow_down=0.5, eye_squint=0.35, lips_part=0.3, press=0.1)
        coin.location = (0, 0, -50); flicker(t)

    def s_1b(t):      # montage: a lone lantern coming out of the black
        tt = 35.9 + (t - 6.7)
        wade(tt, 34.0, 40.5, 6.0, -1.0, 0.5)
        shoot(cam, t, (-0.35, tos.pos.y - 6.5, 0.75), (0.1, tos.pos.y, 1.0), 40, fstop=2.8, shake=1.2)

    def s_4a(t):      # follow from behind, low over the water: we go in after him
        wade(t, 32.5, 37.5, -9.0, -3.5, 0.3)
        u = ramp(t, 33.7, 35.8)
        shoot(cam, t, (0.55, tos.pos.y - 3.3 + 0.5 * u, 0.85), (0.1, tos.pos.y + 3.0, 1.1), 24, shake=1.4, seed=2)

    def s_4b(t):      # front, retreating camera: stooped under the vault, light on his face
        wade(t, 34.0, 40.5, 6.0, -1.0, 0.75)
        shoot(cam, t, (-0.45, tos.pos.y - 2.6, 0.95), (0.1, tos.pos.y, 1.05), 35, fstop=2.8, shake=1.5, seed=3)

    def squat(t):
        tos.place((0.3, -1.0, BED), math.radians(-70))
        tos.pelvis(fwd=-0.12, up=-0.58, rx=0.35)
        tos.spine(rx=0.75, rz=-0.1)
        tos.foot('L', (-(tos.hip_w + 0.08), 0.1, 0), yaw=0.3); tos.foot('R', (tos.hip_w + 0.08, -0.08, 0), yaw=-0.3, pitch=0.35)
        pole.location = (1.35, 1.5, 0.52); pole.rotation_euler = (math.pi / 2, 0, 0.1)

    def s_4c(t):      # close on the hands in the muck; a coin comes up into the lantern light, then his grin
        a = 38.6
        squat(t)
        tos.hand('L', tos.W((-0.3, 0.42, 0.72)), fwd=tos.D((0, 1, 0.3)), palm=tos.D((1, 0, 0)), world=True); tos.fingers('L', 0.85); tos.elbow('L', (-0.9, -0.3, 0.6))
        orient(lan, tos.palm('L', 0.07, 0.03) - Vector((0, 0, 0.03)), z=(0.03 * math.sin(t * 3), 0, 1))
        dig = pulse(t, a - 0.5, a + 0.2, a + 0.9, a + 1.5); up = ramp(t, a + 0.9, a + 1.7)
        mud = tos.W((0.22, 0.5, 0.36)); show = tos.W((0.1, 0.42, 0.88))
        hp = vlerp(tos.W((0.25, 0.4, 0.6)), mud + Vector((0.04 * math.sin(t * 7), 0.03 * math.cos(t * 6), 0)), dig).lerp(show, up)
        tos.hand('R', hp, fwd=vlerp(tos.D((0, 0.5, -1)), tos.D((-0.6, 0.6, 0.6)), up), palm=vlerp(tos.D((0, -0.2, -1)), tos.D((-0.5, -1, 0.2)), up), world=True)
        tos.elbow('R', (0.9, -0.3, 0.6))
        tos.fingers('R', each=[lerp(0.3, 0.9, up), 0.9 * up + 0.2, 0.95 * up + 0.2, up + 0.2], thumb=lerp(0.2, 0.95, up))
        tipp = tos.palm('R', 0.105, 0.045)
        coin.location = tipp if up > 0.05 else (0, 0, -50)
        coin.rotation_euler = (1.3, 0.3 + 2.5 * ramp(t, a + 1.8, a + 2.5), 0.2)
        tos.head(rx=0.25 - 0.3 * up, rz=-0.25 * up); tos.gaze(pitch=0.15 * (1 - up), yaw=-0.15 * up)
        grin = ramp(t, a + 1.5, a + 2.3)
        tos.face(t, brow_down=0.5 - 0.3 * grin, brow_up=0.6 * grin, eye_wide=0.5 * grin, eye_squint=0.3 * (1 - grin), smile=0.9 * grin, lips_part=0.5 * grin)
        flicker(t)
        u = ramp(t, a + 0.9, a + 2.0)
        face = tos.W((0, 0.25, 1.02))
        shoot(cam, t, mud + tos.D((-0.75, 0.75, 0)) + Vector((0, 0, lerp(0.22, 0.52, u))), mud.lerp(show.lerp(face, 0.35), u), 50, fstop=2.4, shake=1.3, seed=4)

    def s_4d(t):      # he is gone: hat on the water, lantern guttering on the ledge; slow retreat
        a = 41.3
        tos.place((0, 0, -60), 0)
        lan.matrix_world = __import__('mathutils').Matrix.Translation((1.55, -0.6, 0.74))
        dim = 1 - 0.85 * ramp(t, a + 0.8, a + 2.6)
        flicker(t, dim * (1 + 0.5 * noise(t, 9, 14) * ramp(t, a + 0.6, a + 2.0)))
        hat.location = (0.3 + 0.1 * math.sin(t * 0.6), 0.2 - 0.25 * (t - a), 0.325 + 0.006 * math.sin(t * 2.2)); hat.rotation_euler = (0.08 * math.sin(t * 1.7), 0.1, t * 0.25)
        pole.location = (-0.4, 0.9 - 0.2 * (t - a), 0.325); pole.rotation_euler = (math.pi / 2, 0, 0.5 + 0.05 * (t - a))
        coin.location = (0, 0, -50)
        u = ramp(t, a, 43.9)
        shoot(cam, t, vlerp((-0.3, -1.6, 0.62), (-0.5, -3.6, 0.95), u), (0.4, 0.3, 0.42), lerp(35, 30, u), fstop=2.8, focus=lerp(1.9, 3.9, u), shake=0.6, seed=6)

    def s_9b(t):      # "paid in nightmares": push in on wide eyes as something moves in the dark behind him
        a = 86.2
        tos.place((0.15, 2.0, BED), 0.0); tos.stand(t, 0.4)
        tos.pelvis(up=-0.15, rx=0.1); tos.spine(rx=0.35)
        lantern_hand(t, h=1.2)
        tos.hand('R', tos.W((0.3, 0.2, 0.95)), fwd=tos.D((0, 1, 0)), palm=tos.D((0, 0, -1)), world=True); tos.fingers('R', 0.5, spread=1); tos.elbow('R', (0.9, -0.4, 0.9))
        pole.location = (0, 0, -50); coin.location = (0, 0, -50)
        turn = ramp(t, a + 0.5, a + 0.85)
        tos.head(rx=-0.25, rz=0.75 * turn - 0.1); tos.gaze(yaw=0.3 * turn)
        fear = ramp(t, a + 0.2, a + 0.9)
        tos.face(t, blink=False, brow_up=0.9 * fear, brow_inner=1.0 * fear, eye_wide=1.0 * fear, jaw=0.35 * fear, lips_part=0.5 * fear, dretract=0.5 * fear, neck=0.7 * fear)
        flicker(t, 0.9 + 0.3 * noise(t, 2, 17))
        u = ramp(t, a, 88.3)
        hd = tos.W((0, 0.05, tos.h.height - 0.26))
        shoot(cam, t, hd + vlerp((-0.3, -1.25, -0.05), (-0.12, -0.72, -0.03), u), hd, 50, fstop=2.0, shake=1.8, roll=lerp(0, -0.06, u), seed=7)

    return [(6.7, 8.2, s_1b), (33.7, 35.8, s_4a), (35.8, 38.6, s_4b), (38.6, 41.3, s_4c), (41.3, 43.9, s_4d), (86.2, 88.3, s_9b)]
