"""Victorian street + tannery yard: the pure finder (No. 7), the money shots and the sign-off."""
import math
from mathutils import Vector
from .. import sets, props, cast, stage
from ..anim import ramp, pulse, lerp, vlerp, path, noise, orient, smooth
from ..film import shoot

OX = 300.0   # tannery yard lives 300 m east of the street


def build(scene, cam):
    sets.street('victorian', seed=1)
    sets.tannery((OX, 0, 0))
    stage.sky(scene, elevation=50, rotation=187, strength=0.16, dust=2.0)
    scene.view_settings.exposure = -0.3
    fin = cast.purefinder(); tan = cast.tanner()
    bucket = props.bucket(); dung = props.dung()
    piles = []
    for p in ((-1.9, 6.35), (0.9, 3.2), (-2.4, 10.5)):
        d = props.dung(); d.location = (p[0], p[1], 0.0); piles.append(d)
    coins = [props.coin() for _ in range(3)]
    FX = -1.6                      # finder's lane on the road
    W0, W1 = 12.4, 18.2            # walk timing
    YA, YB = 12.2, 6.9

    def hide(objs, v=True):
        for o in objs:
            o.location = (0, 0, -50) if v else o.location

    def carry_bucket(t, sway=1.0):
        p = fin.palm('L', 0.08, 0.02)
        sw = math.sin(t * 5.2) * 0.05 * sway
        orient(bucket, p - Vector((0.0, 0, 0.36)), z=(sw * 0.4, sw, 1), y=(0, 1, 0))

    def finder_walk(t):
        fin.walk(t, W0, W1, (FX, YA, 0), (FX, YB, 0), step=0.5, lift=0.06, swing=0.3, lean=0.16, arms='R')
        # left hand carries the bucket low at his side
        fin.hand('L', (-0.27, 0.06, 0.74 + fin._pel[0].z), fwd=(0, 0.1, -1), palm=(1, 0, 0))
        fin.elbow('L', (-0.7, -0.8, 1.2)); fin.fingers('L', 0.8)
        look = pulse(t, 15.4, 16.2, 17.6, 18.2)
        fin.head(rx=0.25 + 0.2 * look, rz=0.25 * math.sin(t * 1.3) * (1 - look) - 0.2 * look)
        fin.gaze(yaw=0.2 * math.sin(t * 1.3 + 0.4), pitch=0.15)
        fin.face(t, brow_down=0.4, eye_squint=0.35, frown=0.3, press=0.2)
        carry_bucket(t)
        for c in coins:
            c.location = (0, 0, -50)
        dung.location = (0, 0, -50)

    # -- shots on the street ------------------------------------------------
    def s_1a(t):      # montage: long-lens front view, he trudges toward us
        tt = 13.6 + (t - 5.2)
        finder_walk(tt)
        p = fin.pos
        shoot(cam, t, (FX + 0.5, p.y - 7.5 - (t - 5.2) * 0.4, 0.95), (FX, p.y, 1.0), 85, fstop=2.8, shake=1.5)

    def s_2a(t):      # crane down from the rooftops to the lone figure: establishes time and place
        finder_walk(t)
        u = ramp(t, 13.1, 15.6)
        pos = vlerp((1.6, -3.5, 8.5), (0.6, 4.2, 1.5), u)
        tgt = vlerp((0, 14, 4.5), (FX, fin.pos.y, 1.05), u)
        shoot(cam, t, pos, tgt, lerp(24, 32, u), shake=0.6)

    def s_2b(t):      # side tracking shot at his pace: we walk the street with him
        finder_walk(t)
        p = fin.pos
        shoot(cam, t, (FX + 3.4, p.y - 0.9, 1.25), (FX, p.y - 0.15, 1.02), 50, fstop=4, shake=1.6, seed=2)

    def crouch(t, a, b):
        """a: start of crouch, b: start rising (never within this film)"""
        c = ramp(t, a, a + 0.9)
        fin.place((FX, YB, 0), 0.0)
        fin.pelvis(fwd=-0.12 * c, up=-0.035 - 0.5 * c, rx=0.35 * c, right=-0.03 * c)
        fin.spine(rx=0.16 + 0.75 * c, rz=0.25 * c)
        fin.foot('L', (-(fin.hip_w + 0.07), 0.12 * c, 0), yaw=0.25)
        fin.foot('R', ((fin.hip_w + 0.07), -0.16 * c, 0.0), pitch=0.5 * c, yaw=-0.2)
        return c

    def s_2c(t):      # ground-level close-up: the job itself, in his hands
        a = 17.9
        c = crouch(t, a, 99)
        target = Vector((-1.9, 6.35, 0.03))
        bpos = Vector((FX + 0.32, YB - 0.45, 0.0))      # bucket set down by his left foot
        reach = ramp(t, a + 0.35, a + 1.05); grab = ramp(t, a + 1.0, a + 1.3)
        lift = ramp(t, a + 1.35, a + 2.0); drop = ramp(t, a + 2.0, a + 2.2)
        rest = fin.W((0.3, 0.2, 0.75))
        over = bpos + Vector((0, 0, 0.42))
        hp = vlerp(rest, target + Vector((0.02, 0.07, 0.06)), reach)
        hp = hp.lerp(over + Vector((0, 0.06, 0.03 + 0.08 * math.sin(lift * math.pi))), lift)
        fin.hand('R', hp, fwd=vlerp((0, -0.6, -1), (-0.3, -1, -0.5), lift), palm=vlerp((0, -0.3, -1), (0.2, 0, -1), lift), world=True)
        fin.elbow('R', (1.0, -0.3, 0.9))
        fin.fingers('R', lerp(0.15, 0.75, grab) - 0.5 * drop, thumb=lerp(0.1, 0.9, grab) - 0.7 * drop, spread=1 - grab)
        fin.hand('L', bpos + Vector((0.13, 0.02, 0.33)), fwd=(0.2, -0.6, -1), palm=(-1, 0, -0.2), world=True)
        fin.elbow('L', (-0.9, 0.2, 0.7)); fin.fingers('L', 0.7)
        orient(bucket, bpos, z=(0, 0, 1))
        fin.head(rx=0.3 - 0.25 * lift, rz=-0.3 + 0.5 * lift)
        fin.gaze(pitch=0.2)
        disgust = pulse(t, a + 0.9, a + 1.5, 30, 31)
        fin.face(t, brow_down=0.5 + 0.3 * disgust, eye_squint=0.3 + 0.4 * disgust, snarl=0.8 * disgust, upper_lip=0.5 * disgust, frown=0.5, press=0.3)
        if grab < 0.5:
            dung.location = target - Vector((0, 0, 0.03))
        else:
            pp = fin.palm('R', 0.09, 0.035)
            fall = ramp(t, a + 2.05, a + 2.3)
            dung.location = pp.lerp(bpos + Vector((0, 0, 0.05)), fall)
        piles[0].location = (0, 0, -50)
        u = ramp(t, 18.0, 20.3)
        shoot(cam, t, vlerp((-2.75, 5.45, 0.16), (-2.6, 5.25, 0.42), u), vlerp((-1.85, 6.4, 0.12), (-1.5, 6.6, 0.62), smooth(u) ** 1.5), 35, fstop=2.8,
              focus=None, shake=1.2, seed=4)

    def s_9c(t):      # sign-off: he straightens, touches his cap to us
        tt = t - 88.3
        fin.place((FX, YB, 0), 0.0); fin.stand(t)
        tip = pulse(t, 88.3, 88.7, 89.5, 90)
        fin.hand('R', vlerp((0.3, 0.1, 0.85), (0.16, 0.2, fin.h.height - 0.07), tip), fwd=vlerp((0, 0.3, -1), (-0.7, 0.2, 0.6), tip), palm=vlerp((-1, 0, 0), (0, -1, -0.3), tip))
        fin.elbow('R', (1.0, 0.2, 1.2)); fin.fingers('R', 0.3 + 0.4 * tip, thumb=0.7 * tip)
        fin.hand('L', (-0.27, 0.06, 0.74), fwd=(0, 0.1, -1), palm=(1, 0, 0)); fin.fingers('L', 0.8); fin.elbow('L', (-0.7, -0.8, 1.2))
        carry_bucket(t, 0.3)
        fin.head(rx=0.12 * tip, rz=0.0)
        fin.face(t, smile=0.75, brow_up=0.4 * tip, eye_squint=0.35, lips_part=0.2)
        dung.location = (0, 0, -50)
        shoot(cam, t, (FX + 0.35, YB - 1.9 + tt * 0.12, 1.45), (FX, YB, 1.47), 50, fstop=2.8, shake=1.2, seed=9)

    # -- tannery ------------------------------------------------------------
    FP = Vector((OX - 0.55, -0.75, 0)); TP = Vector((OX + 0.55, 0.45, 0))
    hf = math.atan2(TP.x - FP.x, -(TP.y - FP.y)); ht = hf + math.pi
    mid = (FP + TP) / 2

    def tannery_base(t):
        fin.place(FP, hf); fin.stand(t, 0.6)
        tan.place(TP, ht); tan.stand(t, 0.8)
        dung.location = (0, 0, -50)

    def s_2d(t):      # the sale: over-the-shoulder that arcs into a two-shot as bucket and coin change hands
        tannery_base(t)
        a = 20.3
        offer = ramp(t, a - 0.5, a + 0.5); take = ramp(t, a + 0.7, a + 1.35); pay = ramp(t, a + 1.5, a + 2.2); done = ramp(t, a + 2.2, a + 2.6)
        # finder offers bucket with both hands, then releases
        bp_f = fin.W((0.0, 0.42, 0.95)); bp_t = tan.W((-0.22, 0.34, 0.92))
        bpos = bp_f.lerp(bp_t, take)
        orient(bucket, bpos - Vector((0, 0, 0.3)), z=(0.25 * math.sin(take * math.pi), 0, 1))
        fin.hand('L', vlerp(fin.W((-0.25, 0.1, 0.8)), bp_f + Vector((0, 0, 0.02)), offer).lerp(fin.W((-0.3, 0.15, 0.85)), ramp(t, a + 1.2, a + 1.7)), fwd=(0.2, 1, -0.2), palm=(1, 0, -0.3) if False else (0.3, 0, -1), world=True)
        fin.fingers('L', lerp(0.8, 0.2, ramp(t, a + 1.1, a + 1.5))); fin.elbow('L', (-0.8, -0.5, 1.0))
        palm_up = fin.W((0.14, 0.4, 1.02))
        fin.hand('R', vlerp(fin.W((0.28, 0.05, 0.85)), palm_up, ramp(t, a + 1.2, a + 1.8)), fwd=fin.D((0, 1, 0.1)), palm=vlerp(fin.D((-1, 0, 0)), fin.D((0, 0, 1)), ramp(t, a + 1.3, a + 1.8)), world=True)
        fin.fingers('R', lerp(0.3, 0.12, pay) + 0.5 * done, thumb=0.2 + 0.5 * done); fin.elbow('R', (0.9, -0.4, 0.9))
        fin.spine(rx=0.2 + 0.08 * offer); fin.head(rx=-0.12 + 0.3 * pay, rz=0.0)
        fin.face(t, brow_inner=0.6, brow_up=0.3, smile=0.15 + 0.5 * done, eye_squint=0.2)
        # tanner takes the bucket in his left, peers in, pays with his right
        tan.hand('L', vlerp(tan.W((-0.3, 0.05, 0.95)), bp_t + Vector((0, 0, 0.02)), ramp(t, a + 0.3, a + 1.0)), fwd=tan.D((0.2, 1, -0.3)), palm=tan.D((0.3, 0, -1)), world=True)
        tan.fingers('L', lerp(0.3, 0.85, take)); tan.elbow('L', (-0.9, -0.5, 1.1))
        coin_from = tan.W((0.3, 0.1, 1.0)); give = fin.palm('R', 0.07, 0.0) + Vector((0, 0, 0.09))
        tan.hand('R', vlerp(coin_from, give - tan.D((0, 1, 0)) * 0.1, pay).lerp(coin_from, ramp(t, a + 2.4, a + 2.9)), fwd=tan.D((0, 1, -0.3)), palm=tan.D((0, 0, -1)), world=True)
        tan.fingers('R', lerp(0.7, 0.25, ramp(t, a + 2.1, a + 2.3)), thumb=0.8); tan.elbow('R', (0.9, -0.5, 1.2))
        peer = pulse(t, a + 0.9, a + 1.4, a + 1.6, a + 2.0)
        tan.spine(rx=0.05 + 0.18 * peer); tan.head(rx=0.1 + 0.45 * peer, rz=0.25 * peer)
        tan.face(t, brow_down=0.5, snarl=0.6 * peer, eye_squint=0.3 + 0.3 * peer, frown=0.3, smile=0.3 * done)
        cp = tan.palm('R', 0.08, 0.03)
        drop = ramp(t, a + 2.15, a + 2.32)
        land = fin.palm('R', 0.07, 0.012)
        for i, c in enumerate(coins):
            c.location = cp.lerp(land + Vector((0.012 * (i - 1), 0.008 * i, 0.003 * i)), drop) if i == 0 else (0, 0, -50)
        u = ramp(t, 20.3, 23.2)
        ang = lerp(-1.95, -1.25, u)
        pos = mid + Vector((math.cos(ang) * 3.1, math.sin(ang) * 3.1, lerp(1.6, 1.35, u)))
        shoot(cam, t, pos, mid + Vector((0, 0, lerp(1.2, 1.1, u))), lerp(35, 40, u), fstop=3.5, shake=1.2, seed=5)

    def palms(t, close):
        tannery_base(t)
        orient(bucket, tan.W((-0.6, 0.1, 0.0)), z=(0, 0, 1))
        fin.hand('R', fin.W((0.12, 0.42, 1.05)), fwd=fin.D((0, 1, 0.1)), palm=fin.D((0, 0, 1)), world=True)
        fin.elbow('R', (0.9, -0.4, 0.9))
        fin.fingers('R', 0.12 + 0.75 * close, thumb=0.2 + 0.6 * close)
        fin.hand('L', (-0.27, 0.06, 0.8), fwd=(0, 0.1, -1), palm=(1, 0, 0)); fin.fingers('L', 0.4); fin.elbow('L', (-0.7, -0.8, 1.2))
        tan.arms_relaxed(t)
        return fin.palm('R', 0.07, 0.012)

    def s_1e(t):      # "for money": macro on coins dropping into a worn palm
        land = palms(t, 0.0)
        a = 11.0
        hand_in = pulse(t, a - 0.3, a + 0.3, a + 1.3, a + 1.8)
        hp = vlerp(tan.W((0.3, 0.1, 1.05)), land + Vector((0, 0, 0.16)) - tan.D((0, 1, 0)) * 0.1, hand_in)
        tan.hand('R', hp, fwd=tan.D((0, 1, -0.4)), palm=tan.D((0, 0, -1)), world=True); tan.elbow('R', (0.9, -0.5, 1.2))
        tan.fingers('R', 0.75 - 0.4 * ramp(t, a + 0.45, a + 1.2), thumb=0.8)
        src = tan.palm('R', 0.09, 0.035)
        for i, c in enumerate(coins):
            t0 = a + 0.5 + i * 0.3
            fall = (t - t0) / 0.22
            end = land + Vector((0.014 * (i - 1), 0.012 * (i - 1), 0.0025 * i + 0.001))
            if fall < 0:
                c.location = src; c.rotation_euler = (0.3, 0.2, i)
            elif fall < 1:
                c.location = src.lerp(end, fall * fall); c.rotation_euler = (3.0 * (1 - fall) + 0.05, 2.0 * (1 - fall), i)
            else:
                b = max(0, 1 - (fall - 1) * 1.6)
                c.location = end + Vector((0, 0, abs(math.sin((fall - 1) * 9)) * 0.012 * b)); c.rotation_euler = (0.25 * b * math.sin(fall * 14), 0.05 * i, i)
        fin.fingers('R', 0.12 + 0.1 * ramp(t, a + 1.3, a + 2.1), thumb=0.2)
        u = ramp(t, 11.0, 13.1)
        d = fin.D((0.55, 0.35, 0))
        shoot(cam, t, land + d * lerp(0.42, 0.34, u) + Vector((0, 0, 0.2)), land + Vector((0, 0, 0.025)), 60, fstop=2.8, shake=0.8, seed=6)

    def s_9a(t):      # "paid in money": he weighs the coins, closes his fist; tilt from hand to tired half-smile
        a = 84.4
        close = ramp(t, a + 0.7, a + 1.4)
        land = palms(t, close)
        for i, c in enumerate(coins):
            c.location = land + Vector((0.014 * (i - 1), 0.012 * (i - 1), 0.0025 * i + 0.001)) if close < 0.6 else (0, 0, -50)
            c.rotation_euler = (0.05, 0.05 * i, i)
        fin.head(rx=0.35 - 0.3 * ramp(t, a + 1.0, a + 1.7), rz=-0.15)
        fin.face(t, smile=0.2 + 0.4 * close, brow_inner=0.7, eye_squint=0.3)
        u = ramp(t, a, a + 1.8)
        d = fin.D((0.3, 1, 0))
        hd = fin.W((0, 0, fin.h.height - 0.1))
        shoot(cam, t, land + d * 0.75 + Vector((0, 0, 0.25)), land.lerp(hd, smooth(u) * 0.75) + Vector((0, 0, 0.03)), 55, fstop=2.8, shake=1.0, seed=7)

    return [(5.2, 6.7, s_1a), (11.0, 13.1, s_1e), (13.1, 15.6, s_2a), (15.6, 18.0, s_2b), (18.0, 20.3, s_2c), (20.3, 23.2, s_2d), (84.4, 86.2, s_9a), (88.3, 89.25, s_9c)]
