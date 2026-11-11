"""Plague lane and the pit outside the walls: the body collector (No. 2)."""
import math, bpy
from mathutils import Vector, Matrix
from .. import sets, props, cast, stage
from ..anim import ramp, pulse, lerp, vlerp, noise, orient, smooth
from ..film import shoot

OX = 900.0


def build(scene, cam):
    sets.street('medieval', seed=7, width=5.5)
    stage.sky(scene, elevation=40, rotation=186, strength=0.17, dust=6.0, air=1.5)
    scene.view_settings.exposure = -0.25
    # pit field is built 300 m east
    import bpy as _b
    before = set(_b.data.objects)
    sets.pit_field()
    for o in set(_b.data.objects) - before:
        if o.parent is None:
            o.location.x += OX
    col = cast.plague_collector(); mate = cast.plague_collector('mate', 41)
    cart, wheels = props.cart()
    load = [props.shroud(1.72, seed=11), props.shroud(1.6, seed=12, color=(0.52, 0.5, 0.44))]
    for i, b in enumerate(load):
        b.parent = cart; b.location = (-0.2 + 0.4 * i, -0.82 + 0.05 * i, 0.66 + 0.02 * i); b.rotation_euler = (0, 0.05 * (i * 2 - 1), 0.06 * (1 - 2 * i))
    toss = props.shroud(1.7, seed=13)
    bell = props.bell()
    X = 0.4
    T0, T1, Y0, Y1 = 64.0, 73.5, 13.0, 2.6

    def push(t, tt=None):
        tt = t if tt is None else tt
        d = col.walk(tt, T0, T1, (X, Y0, 0), (X, Y1, 0), step=0.56, lift=0.07, swing=0.0, lean=0.22, arms='', bob=0.02)
        P = col._pel[0]
        cy = col.pos.y - 2.15
        jolt = 0.012 * noise(tt, 4, 9)
        cart.location = (X, cy, jolt); cart.rotation_euler = (0.02 * noise(tt, 5, 7), 0.015 * noise(tt, 6, 8), 0)
        for w in wheels:
            w.rotation_euler = (d / 0.53, 0, 0)
        for s, sg in (('L', -1), ('R', 1)):
            hp = Vector((X + sg * -0.4 * -1 * -1, cy + 1.95, 0.71 + jolt))
            hp = Vector((X - sg * 0.4, cy + 2.05, 0.74 + jolt))
            col.hand(s, hp, fwd=(0, -1, -0.05), palm=(0, 0, -1), world=True); col.fingers(s, 0.9, thumb=0.6); col.elbow(s, (sg * 0.9, -0.6, 0.9))
        col.head(rx=-0.25, rz=0.12 * math.sin(tt * 0.8))
        toss.location = (0, 0, -50); bell.location = (0, 0, -50)
        mate.place((60, 60, -20), 0)
        return d

    def s_1d(t):      # montage: looking down from an upper window as the cart passes beneath
        tt = 66.5 + (t - 9.6)
        push(t, tt)
        col.face(t, brow_down=0.5, frown=0.5, eye_squint=0.3)
        shoot(cam, t, (-2.4, col.pos.y - 5.5, 6.2), (X, col.pos.y - 1.2, 0.6), 35, shake=1.0)

    def s_7a(t):      # low and wide, cart coming straight at us down the empty lane
        push(t)
        col.face(t, brow_down=0.6, frown=0.6, eye_squint=0.35, press=0.4)
        u = ramp(t, 65.1, 67.8)
        shoot(cam, t, (X - 1.9, col.pos.y - 6.0 - 0.3 * u, 1.05), (X + 0.1, col.pos.y - 0.6, 1.15), 28, shake=1.0, seed=2)

    def s_7b(t):      # side track at wheel height: the turning wheel and the load, his strain beyond
        push(t)
        eff = 0.5 + 0.5 * math.sin(t * 3.1)
        col.face(t, brow_down=0.8, grimace=0.35 * eff, eye_squint=0.5, snarl=0.3 * eff, press=0.3)
        shoot(cam, t, (X - 2.75, col.pos.y - 2.3, 0.7), (X, col.pos.y - 0.9, 1.0), 30, fstop=3.5, shake=1.5, seed=3)

    def s_7c(t):      # low-angle close-up: bell up, the cry rolls down the street
        a = 70.3
        col.place((X, 5.4, 0), 0.0); col.stand(t, 1.0)
        cy = 5.4 - 2.15
        cart.location = (X, cy, 0); cart.rotation_euler = (0, 0, 0)
        col.hand('L', (X + 0.4, cy + 2.05, 0.74), fwd=(0, -1, -0.05), palm=(0, 0, -1), world=True); col.fingers('L', 0.9); col.elbow('L', (-0.9, -0.6, 0.9))
        up = ramp(t, a - 0.3, a + 0.5)
        ring = math.sin((t - a) * 2 * math.pi * 2.6) * up
        hp = col.W((0.32, 0.25, lerp(0.95, 1.62, up) + 0.03 * ring))
        d = Vector((0.5 * ring, 0.25 * ring, -1)).normalized()
        col.grip('R', hp, col.D((0.5 * ring, 0.3 * ring, -1)), col.D((-1, 0, 0))); col.elbow('R', (1.0, -0.2, 1.2))
        orient(bell, col.palm('R', 0.02, 0.03) + col.D((0.5 * ring, 0.3 * ring, -1)).normalized() * 0.19, z=-col.D((0.5 * ring, 0.3 * ring, -1)))
        # "Bring out your dead": one jaw pulse per word
        words = [(71.4, 71.68, 0.55), (71.72, 71.93, 0.75), (71.96, 72.1, 0.5), (72.14, 72.62, 1.0)]
        jaw = max(pulse(t, w0 - 0.05, w0 + 0.07, w1 - 0.06, w1 + 0.08) * k for w0, w1, k in words)
        shout = pulse(t, 71.1, 71.4, 72.6, 72.9)
        col.spine(rx=-0.08 * shout); col.head(rx=-0.3 * shout - 0.05, rz=0.25 * math.sin((t - a) * 1.4))
        col.face(t, brow_down=0.5, brow_inner=0.5, eye_squint=0.3 + 0.2 * shout, jaw=0.15 + 0.85 * jaw, wide=0.3 * jaw, upper_lip=0.3 * jaw, neck=0.8 * jaw, snarl=0.3 * jaw, lips_part=0.4 * shout)
        toss.location = (0, 0, -50); mate.place((60, 60, -20), 0)
        u = ramp(t, a, 72.9)
        hd = col.W((0, 0, col.h.height - 0.12))
        shoot(cam, t, hd + vlerp((-0.55, -1.45, -0.42), (-0.35, -1.05, -0.36), u), hd + Vector((0.08, 0, 0.02)), 40, fstop=2.8, shake=1.4, seed=4)

    def s_7d(t):      # from inside the pit looking up: two silhouettes swing the body out over us and let go
        a = 72.9
        cart.location = (OX + 3.2, -5.5, 0); cart.rotation_euler = (0, 0, 0.6); bell.location = (0, 0, -50)
        col.place((OX - 0.85, -2.45, 0), math.pi); mate.place((OX + 0.85, -2.45, 0), math.pi)
        rel = a + 1.45
        sw = math.sin((min(t, rel) - a) * 2 * math.pi / 1.1 - 0.6)             # swing back and forth, release on a forward swing
        fwd = 0.25 + 0.42 * sw
        hgt = 0.62 + 0.22 * abs(sw)
        after = ramp(t, rel, rel + 0.5)
        for ac, sg in ((col, 1), (mate, -1)):
            ac.stand(t, 0.5, feet=0.06)
            ac.pelvis(up=-0.12, fwd=0.05 * sw, rx=0.1); ac.spine(rx=0.35 + 0.25 * sw - 0.2 * after, rz=sg * 0.25); ac.head(rx=0.15)
            for s, k in (('L', -1), ('R', 1)):
                hp = ac.W((-sg * 0.42 + k * 0.1, fwd, hgt)).lerp(ac.W((k * 0.3, 0.25, 0.85)), after)
                ac.hand(s, hp, fwd=ac.D((-sg * 0.8, 0.3, -0.4)), palm=ac.D((0, 0.3, 1)), world=True); ac.elbow(s, (k * 0.9, -0.6, 0.9)); ac.fingers(s, 0.85 - 0.6 * after)
            ac.face(t, brow_down=0.7, grimace=0.5 * (1 - after), eye_squint=0.5, press=0.3, jaw=0.2 * abs(sw) * (1 - after))
        cpos = Vector((OX - 0.85, -2.45 + fwd, hgt - 0.1))
        if t < rel:
            toss.location = cpos; toss.rotation_euler = (0, 0.06 * sw, -math.pi / 2)
        else:
            dt = t - rel
            v0 = 2.6
            toss.location = Vector((OX - 0.85, -2.45 + 0.25 + 0.42 * math.sin((rel - a) * 2 * math.pi / 1.1 - 0.6) + v0 * dt, max(-1.42, hgt - 0.1 + 1.2 * dt - 4.9 * dt * dt)))
            toss.rotation_euler = (min(0.9, 1.6 * dt) * (1 if toss.location.z > -1.4 else 0.1), 0.2 * dt, -math.pi / 2 + 0.5 * dt)
        shoot(cam, t, (OX + 0.55, 0.95, -1.18), (OX - 0.1, -2.2, 0.75), 20, shake=1.0, seed=6)

    return [(9.6, 11.0, s_1d), (65.1, 67.8, s_7a), (67.8, 70.3, s_7b), (70.3, 72.9, s_7c), (72.9, 75.5, s_7d)]
