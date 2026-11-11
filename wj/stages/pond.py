"""Sunlit pond: the leech collector (No. 6)."""
import math
from mathutils import Vector
from .. import sets, props, cast, stage
from ..world import sphere, mat
from ..anim import ramp, pulse, lerp, vlerp, path, noise, orient, smooth, attach
from ..film import shoot

WATER = -0.28


def build(scene, cam):
    info = sets.pond(); hf = info['hf']
    stage.sky(scene, elevation=44, rotation=165, strength=0.16, dust=1.2)
    scene.view_settings.exposure = -0.3
    wom = cast.leech_woman(); doc = cast.doctor()
    jar = props.jar(3); coin = props.coin(gold=False)
    rock = sphere(0.3, (0.75, -8.75, hf(0.75, -8.75) + 0.08), mat('stone', c=(0.35, 0.34, 0.32)), scale=(1.1, 1, 0.75), seg=14, noise=0.05, seed=2)
    # leeches fastened to her right calf (rest-space coords) + one free leech that gets pulled off
    h0, h1 = wom.h.rest['lowerleg01.R'][0], wom.h.rest['lowerleg02.R'][1]
    onleg = []
    for u, ang, rot in ((0.3, -0.3, 0.2), (0.5, 0.6, -0.4), (0.68, -1.0, 0.5), (0.42, 2.2, 0.1)):
        l = props.leech(1.15)
        p = h0.lerp(h1, u) + Vector((-math.cos(ang) * 0.052 * (1.1 - u * .5), -math.sin(abs(ang) + 0.6) * 0.05 * (1.1 - u * .5), 0))
        attach(l, wom.h, 'lowerleg01.R', p, (math.pi / 2 + 0.1, rot, ang))
        onleg.append((l, l.matrix_basis.copy()))
    free = props.leech(1.15)
    X0 = 0.25

    def ground(a, x, y):
        a.place((x, y, hf(x, y)), a.heading)

    def skirt_hands(t, lift=1.0):
        for s, sg in (('L', -1), ('R', 1)):
            wom.hand(s, (sg * 0.2, 0.1, 0.78 + 0.07 * lift + wom._pel[0].z), fwd=(0, 0.3, -1), palm=(-sg, 0.2, 0))
            wom.elbow(s, (sg * 0.8, -0.5, 1.1)); wom.fingers(s, 0.85)

    def show_leeches(n):
        for i, (l, M) in enumerate(onleg):
            l.matrix_basis = M if i < n else M @ __import__('mathutils').Matrix.Scale(0.0001, 4)

    def hide_props():
        jar.location = (0, 0, -50); coin.location = (0, 0, -50); free.location = (0, 0, -50)
        doc.place((40, -30, 0), 0)

    def wade(t, t0, t1, y0, y1, step=0.4):
        a = Vector((X0, y0, hf(X0, y0))); b = Vector((X0, y1, hf(X0, y1)))
        wom.walk(t, t0, t1, a, b, step=step, lift=0.14, swing=0.0, lean=0.06, arms='', hip=1.6)
        wom.heading = math.pi; wom.arm.rotation_euler = (0, 0, math.pi)
        skirt_hands(t)

    def s_3a(t):      # wide, rising from the grass: a quiet green place before the unpleasant part
        hide_props(); show_leeches(0)
        wade(t, 22.6, 26.2, -11.2, -7.9, 0.55)
        wom.head(rx=0.15); wom.face(t, brow_inner=0.5, press=0.3, eye_squint=0.2)
        u = ramp(t, 23.2, 25.7)
        shoot(cam, t, vlerp((2.6, -13.6, 0.35), (2.0, -12.6, 1.9), u), vlerp((0.2, -8.5, 0.9), (0.2, -6.5, 0.6), u), lerp(28, 32, u), fstop=5.6, focus=4.5, shake=0.8)

    def s_3b(t):      # water-level front view: bare feet break the surface and we feel the cold with her
        hide_props(); show_leeches(0)
        wade(t, 25.5, 28.6, -7.85, -5.9, 0.36)
        wom.head(rx=0.3); wom.gaze(pitch=0.2)
        cold = pulse(t, 26.0, 26.6, 27.5, 28.2)
        wom.face(t, brow_inner=0.8, brow_up=0.3 * cold, grimace=0.5 * cold, lips_part=0.4 * cold, eye_squint=0.3)
        u = ramp(t, 25.7, 28.2)
        shoot(cam, t, vlerp((-1.3, -3.3, WATER + 0.5), (-1.1, -3.1, WATER + 0.6), u), vlerp((X0, -7.0, 0.35), (X0, -6.0, 0.4), u), 35, fstop=4, focus=3.2, shake=1.4, seed=3)

    def stand_in_water(t, raise_leg):
        y = -5.9
        wom.place((X0, y, hf(X0, y)), math.pi)
        wom.stand(t, 0.6)
        wom.pelvis(right=-0.07 * raise_leg, up=-0.02)
        wom.foot('R', (wom.hip_w + 0.05, 0.16 * raise_leg, 0.52 * raise_leg), pitch=0.5 * raise_leg, yaw=-0.5 * raise_leg)
        wom.knee('R', (0.9, 1.2, 0.9))
        skirt_hands(t, 1.0)

    def s_3c(t):      # close on the calf as she lifts it clear: leeches fastened on; tilt up to the price on her face
        hide_props()
        lift = ramp(t, 28.0, 28.9)
        stand_in_water(t, lift)
        show_leeches(4)
        wom.spine(rx=0.25 * lift, ry=0.12 * lift); wom.head(rx=0.5 * lift, ry=0.2 * lift)
        hurt = ramp(t, 28.7, 29.4)
        wom.face(t, brow_inner=1.0, brow_down=0.4 * hurt, eye_squint=0.6 * hurt, grimace=0.6 * hurt, upper_lip=0.4 * hurt, press=0.3, snarl=0.4 * hurt)
        calf = wom.bone_world('lowerleg01.R', 0.9)
        face = wom.W((0, 0, wom.h.height - 0.1))
        u = ramp(t, 29.2, 30.3)
        tgt = calf.lerp(face, u)
        shoot(cam, t, calf + Vector((-0.75 + 0.15 * u, 0.85, 0.12 + 0.75 * u)), tgt, lerp(55, 50, u), fstop=2.8, shake=1.4, seed=5)

    def s_3d(t):      # on the bank: over the doctor's jar as she peels one off, drops it in, and is paid by the head
        show_leeches(3)
        a = 30.5
        wy = -8.6
        wom.place((0.55, wy, hf(0.55, wy)), math.radians(100)); wom.stand(t, 0.4)
        rk = Vector(rock.location) + Vector((0, 0, 0.2))
        wom.foot('R', rk - Vector((0, 0, 0)) - Vector((0, 0, 0)), pitch=0.1, world=True)
        wom.t['footR'].location = rk + Vector((-0.05, 0, wom.ankle_h - 0.02))
        wom.knee('R', rk + Vector((0.8, 0.1, 0.8)), world=True)
        bend = 0.85
        wom.pelvis(right=0.03, up=-0.06, rx=0.2); wom.spine(rx=bend, rz=-0.15); wom.head(rx=-0.25)
        dp = Vector((1.75, wy - 0.25, hf(1.75, wy)))
        doc.place(dp, math.radians(-75)); doc.stand(t, 0.5); doc.spine(rx=0.22); doc.head(rx=0.3)
        calf = wom.bone_world('lowerleg01.R', 0.3) + Vector((0.03, -0.02, 0.03))
        jp = doc.W((-0.12, 0.5, 0.82))
        orient(jar, jp, z=(0, 0, 1))
        doc.hand('L', jp + doc.D((-0.075, -0.02, 0.07)), fwd=doc.D((0.25, 1, 0)), palm=doc.D((1, 0, 0)), world=True); doc.fingers('L', 0.6, thumb=0.4); doc.elbow('L', (-0.8, -0.6, 1.0))
        reach = ramp(t, a - 0.2, a + 0.5); pinch = ramp(t, a + 0.45, a + 0.75); pull = ramp(t, a + 0.8, a + 1.5); drop = ramp(t, a + 1.5, a + 1.7)
        over = jp + Vector((0, 0, 0.26))
        hp = vlerp(wom.W((0.3, 0.2, 0.7)), calf + Vector((0.02, -0.03, 0.08)), reach).lerp(over + Vector((0, 0, 0.05 * math.sin(pull * math.pi))), pull)
        wom.hand('R', hp, fwd=(0.2, 0.3, -1), palm=(-1, 0.4, 0), world=True); wom.elbow('R', (0.9, -0.6, 0.9))
        wom.fingers('R', each=[lerp(0.2, 0.75, pinch) - 0.3 * drop, 0.5, 0.7, 0.8], thumb=lerp(0.1, 0.9, pinch) - 0.5 * drop)
        wom.hand('L', wom.W((-0.25, 0.25, 0.75)), fwd=wom.D((0, 0.5, -1)), palm=wom.D((1, 0, 0)), world=True); wom.fingers('L', 0.4); wom.elbow('L', (-0.8, -0.5, 1.0))
        wince = pulse(t, a + 0.7, a + 1.0, a + 1.3, a + 1.8)
        wom.face(t, brow_inner=0.8, eye_squint=0.3 + 0.6 * wince, grimace=0.7 * wince, snarl=0.5 * wince, press=0.3, smile=0.3 * ramp(t, a + 2.4, a + 3.0))
        # pulled leech stretches then lets go
        tip = wom.palm('R', 0.13, 0.03)
        if pinch < 0.95:
            free.location = (0, 0, -50); n = 3
        else:
            n = 2
            fall = ramp(t, a + 1.62, a + 1.85)
            free.location = tip.lerp(jp + Vector((0, 0, 0.06)), fall * fall)
            free.rotation_euler = (1.4, 0.3 * math.sin(t * 25), 0.5)
            st = 1 + 0.9 * pulse(t, a + 0.8, a + 0.95, a + 1.0, a + 1.15)
            free.scale = (1.15 / st ** 0.5, 1.15 * st, 1.15 / st ** 0.5)
        show_leeches(n)
        # payment
        pay = ramp(t, a + 2.0, a + 2.7)
        cp0 = doc.W((0.32, 0.15, 1.0)); cp1 = wom.W((-0.05, 0.42, 0.95))
        doc.hand('R', vlerp(cp0, cp1 + Vector((0, 0, 0.1)), pay), fwd=doc.D((-0.3, 1, -0.3)), palm=doc.D((0, 0, -1)), world=True); doc.fingers('R', 0.7 - 0.3 * ramp(t, a + 2.75, a + 2.9), thumb=0.8); doc.elbow('R', (0.9, -0.5, 1.2))
        doc.face(t, brow_up=0.4, smile=0.25, eye_squint=0.2)
        up = ramp(t, a + 1.9, a + 2.6)
        wom.spine(rx=bend - 0.5 * up, rz=-0.15); wom.head(rx=-0.25 + 0.2 * up)
        wom.hand('L', vlerp(wom.W((-0.25, 0.25, 0.75)), cp1, up), fwd=wom.D((0, 1, 0.1)), palm=vlerp(wom.D((1, 0, 0)), (0, 0, 1), up), world=True); wom.fingers('L', 0.4 - 0.25 * up, thumb=0.2)
        cdrop = ramp(t, a + 2.75, a + 2.95)
        coin.location = doc.palm('R', 0.09, 0.035).lerp(wom.palm('L', 0.07, 0.012), cdrop * cdrop)
        u = ramp(t, a, 33.7)
        mid = (wom.pos + doc.pos) / 2
        shoot(cam, t, mid + vlerp((0.7, -3.4, 1.05), (-0.4, -3.3, 1.25), u), mid + vlerp((0.1, 0, 0.85), (0.1, 0, 1.0), u), 32, fstop=3.2, shake=1.2, seed=8)

    return [(23.2, 25.7, s_3a), (25.7, 28.2, s_3b), (28.2, 30.5, s_3c), (30.5, 33.7, s_3d)]
