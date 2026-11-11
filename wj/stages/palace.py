"""Palace hall: the whipping boy (No. 1) and the cold open."""
import math, bpy
from mathutils import Vector, Matrix
from .. import sets, props, cast, stage
from ..world import box, mat
from ..anim import ramp, pulse, lerp, vlerp, noise, orient, smooth
from ..film import shoot


def build(scene, cam):
    sets.palace()
    stage.sky(scene, elevation=34, rotation=262, strength=0.2, dust=1.5)
    scene.view_settings.exposure = -0.1
    boy = cast.whipping_boy(); pr = cast.prince(); tu = cast.tutor()
    whip = props.Whip()
    books = [props.book(c) for c in ((0.3, 0.05, 0.05), (0.06, 0.12, 0.25), (0.1, 0.2, 0.1))]
    bench = box((1.1, 0.4, 0.06), (-0.9, -2.2, 0.72), mat('wood', c=(0.2, 0.11, 0.06), rough=0.4))
    for sx in (-0.48, 0.48):
        box((0.06, 0.34, 0.7), (-0.9 + sx, -2.2, 0.35), mat('wood', c=(0.2, 0.11, 0.06), rough=0.4))
    BP = Vector((-0.9, -2.75, 0))      # boy stands at the bench, facing +Y (heading pi)
    TP = Vector((-1.75, -3.85, 0))     # tutor behind him to his left
    PP = Vector((1.3, -2.2, 0))        # prince by the desk

    def aim(frm, to):
        d = Vector(to) - Vector(frm)
        return math.atan2(d.x, -d.y)

    # ---- the whip stroke: pure function of time so the lash can look back in time ----
    def stroke(t, hits, origin, heading, hit_h=1.0, reach=1.05):
        """returns wrist position + handle direction (world) for strikes at the given impact times."""
        R = Matrix.Rotation(heading, 3, 'Z')

        def W(v):
            return origin + R @ Vector((-v[0], -v[1], v[2]))

        def D(v):
            return (R @ Vector((-v[0], -v[1], v[2]))).normalized()
        rest_p, rest_d = Vector((0.35, 0.2, 1.0)), Vector((0.2, 0.6, -0.75))
        up_p, up_d = Vector((0.42, -0.12, 1.95)), Vector((0.15, -0.75, 0.65))
        hit_p, hit_d = Vector((0.2, 0.52, hit_h + 0.22)), Vector((-0.25, 0.93, -0.28))
        fol_p, fol_d = Vector((-0.05, 0.42, hit_h - 0.12)), Vector((-0.55, 0.6, -0.6))
        p, d = rest_p, rest_d
        for h in hits:
            wind = ramp(t, h - 0.95, h - 0.3)
            p = p.lerp(up_p, wind); d = d.lerp(up_d, wind)
            x = (t - (h - 0.24)) / 0.24
            if x > 0:
                sw = min(1, x) ** 2.2          # accelerating downswing
                p = p.lerp(hit_p, sw); d = d.lerp(hit_d, sw)
            fo = ramp(t, h, h + 0.22)
            p = p.lerp(fol_p, fo); d = d.lerp(fol_d, fo)
            rec = ramp(t, h + 0.3, h + 0.95)
            p = p.lerp(rest_p, rec); d = d.lerp(rest_d, rec)
        return W(p), D(d)

    def tutor_whips(t, hits, target):
        hd = aim(TP, target)
        tu.place(TP, hd); tu.stand(t, 0.5)
        fn = lambda tt: stroke(tt, hits, TP, hd)
        p, d = fn(t)
        eff = max([pulse(t, h - 0.9, h - 0.3, h + 0.05, h + 0.6) for h in hits] + [0])
        swing = max([pulse(t, h - 0.25, h, h + 0.1, h + 0.6) for h in hits] + [0])
        tu.pelvis(up=-0.03, rz=-0.25 * eff + 0.45 * swing, fwd=0.06 * swing)
        tu.spine(rx=-0.12 * eff + 0.32 * swing, rz=-0.4 * eff + 0.6 * swing); tu.head(rx=0.1 + 0.1 * swing, rz=0.1)
        tu.clav('R', up=0.5 * eff)
        tu.grip('R', p, d, tu.D((-1, 0, 0)) if True else None); tu.elbow('R', (1.1, -0.5, 1.3))
        tu.hand('L', tu.W((-0.3, 0.12, 1.0)), fwd=tu.D((0, 0.6, -0.8)), palm=tu.D((1, 0, 0)), world=True); tu.fingers('L', 0.6); tu.elbow('L', (-0.8, -0.6, 1.1))
        tu.face(t, brow_down=0.9, eye_squint=0.4, press=0.6 * (1 - swing), snarl=0.5 * swing, grimace=0.5 * swing, frown=0.4)
        whip.update(t, lambda tt: (lambda q: (q[0] + q[1] * 0.02, q[1]))(fn(tt)), lag=0.17)

    def boy_takes(t, hits):
        boy.place(BP, math.pi)
        fl = max([pulse(t, h - 0.01, h + 0.07, h + 0.25, h + 0.9) for h in hits] + [0])
        dread = max([pulse(t, h - 0.9, h - 0.2, h, h + 0.1) for h in hits] + [0])
        after = max([ramp(t, h, h + 0.3) for h in hits] + [0])
        boy.pelvis(up=-0.1 - 0.05 * fl, fwd=0.05 * fl, rx=0.2)
        boy.spine(rx=0.55 - 0.3 * fl, rz=0.05 * noise(t, 2, 3)); boy.head(rx=-0.35 - 0.3 * fl + 0.25 * dread, rz=0.12)
        boy.foot('L', (-(boy.hip_w + 0.05), -0.12, 0), yaw=0.15); boy.foot('R', (boy.hip_w + 0.05, -0.2, 0), yaw=-0.15, pitch=0.2 * fl)
        for s, sg in (('L', -1), ('R', 1)):
            boy.hand(s, Vector((-0.9 + sg * 0.22, -2.3, 0.77)), fwd=(0, 1, -0.15), palm=(0, 0, -1), world=True)
            boy.fingers(s, 0.25 + 0.6 * max(fl, dread), thumb=0.4); boy.elbow(s, (sg * 0.9, -0.6, 0.9)); boy.clav(s, up=0.5 * max(fl, dread))
        hurt = max(fl, 0.55 * after)
        boy.face(t, blink=False, eye_close=min(1, 0.6 * dread + fl), brow_inner=0.6 + 0.4 * hurt, brow_down=0.7 * fl, eye_squint=0.5 * hurt, grimace=0.9 * fl + 0.25 * after,
                 jaw=0.5 * fl, upper_lip=0.5 * fl, snarl=0.6 * fl, neck=0.8 * fl, frown=0.6 * after * (1 - fl), press=0.4 * dread)

    def prince_watch(t, smirk=0.6, guilt=0.0):
        pr.place(PP, aim(PP, BP)); pr.stand(t, 1.0)
        pr.hand('R', pr.W((-0.1, 0.2, 0.98)), fwd=pr.D((-1, 0.1, 0.15)), palm=pr.D((0, -1, 0)), world=True); pr.hand('L', pr.W((0.1, 0.22, 0.94)), fwd=pr.D((1, 0.1, 0.15)), palm=pr.D((0, -1, 0)), world=True)
        pr.elbow('R', (0.9, 0.2, 0.8)); pr.elbow('L', (-0.9, 0.2, 0.8)); pr.fingers('R', 0.5); pr.fingers('L', 0.5)
        pr.spine(rx=-0.04); pr.head(rx=0.05 + 0.25 * guilt, rz=-0.1 - 0.5 * guilt); pr.gaze(yaw=0.15 * guilt, pitch=0.2 * guilt)
        pr.face(t, smile=0.5 * smirk * (1 - guilt), sneer=0.3 * smirk, brow_up=0.3 * smirk, eye_squint=0.3, brow_inner=0.8 * guilt, frown=0.5 * guilt, press=0.4 * guilt)

    def books_rest():
        for i, b in enumerate(books):
            b.location = (2.2, -3.05, 0.83 + i * 0.047); b.rotation_euler = (0, 0, 0.2 * (i - 1))

    def s_0a(t):      # cold open: tight on the boy as the lash lands; slow push so we can't look away
        books_rest()
        hits = [2.12]
        tutor_whips(t, hits, BP); boy_takes(t, hits); prince_watch(t)
        u = ramp(t, 0, 2.7)
        hd = boy.W((0, 0.15, 1.0))
        shoot(cam, t, hd + vlerp((0.75, 1.75, 0.02), (0.55, 1.3, 0.0), u), hd + Vector((-0.1, 0, 0.0)), 40, fstop=2.8, focus=lerp(1.95, 1.45, u), shake=1.2 + 4 * pulse(t, 2.1, 2.16, 2.2, 2.5))

    def s_0b(t):      # reveal who earned it: slide past the boy's shoulder to the prince, untouched, amused
        books_rest()
        hits = [2.12, 4.6]
        tutor_whips(t, hits, BP); boy_takes(t, hits); prince_watch(t, smirk=1.0)
        u = ramp(t, 2.7, 5.2)
        hd = pr.W((0, 0, pr.h.height - 0.1))
        shoot(cam, t, hd + vlerp((-1.5, -0.15, -0.12), (-1.05, -0.6, -0.1), u), hd, 55, fstop=2.4, shake=1.0, seed=2)

    def s_8a(t):      # the hall itself: descend through the sun shafts to three small figures
        books_rest()
        tutor_whips(t, [], PP); boy_takes(t, []); prince_watch(t, 0.3)
        boy.spine(rx=0.15); boy.head(rx=0.3)
        for s, sg in (('L', -1), ('R', 1)):
            boy.hand(s, boy.W((sg * 0.12, 0.12, 0.62)), fwd=boy.D((-sg * 0.6, 0.2, -0.8)), palm=boy.D((0, -1, 0)), world=True); boy.fingers(s, 0.5)
        boy.face(t, brow_inner=0.9, frown=0.5, eye_squint=0.2)
        u = ramp(t, 75.5, 77.9)
        shoot(cam, t, vlerp((3.6, -11.2, 5.6), (2.2, -8.4, 1.7), u), vlerp((-0.4, 0, 2.8), (0, -2.6, 1.1), u), lerp(22, 30, u), shake=0.6, seed=3)

    def s_8b(t):      # low angle on the prince as he sweeps the lesson off the desk; the tutor's raised hand stops dead
        a = 77.9
        hd = aim(PP, (2.4, -3.0, 0))
        pr.place(PP + Vector((0.45, -0.25, 0)), hd); pr.stand(t, 1.0)
        sw = ramp(t, a + 0.25, a + 0.75)
        pr.spine(rz=0.5 - 1.0 * sw, rx=0.1); pr.head(rz=-0.5 * ramp(t, a + 1.0, a + 1.6), rx=-0.05)
        pr.hand('R', vlerp((2.0, -3.25, 0.98), (2.75, -2.85, 0.95), sw), fwd=vlerp((0.3, 0.2, -0.2), (1, 0.6, 0), sw), palm=(0, 0, -1), world=True); pr.elbow('R', (0.9, -0.5, 0.9)); pr.fingers('R', 0.15, spread=1)
        pr.hand('L', pr.W((-0.25, 0.1, 0.72)), fwd=pr.D((0, 0.3, -1)), palm=pr.D((1, 0, 0)), world=True); pr.fingers('L', 0.7); pr.elbow('L', (-0.8, -0.5, 0.9))
        pr.face(t, brow_down=0.6 * (1 - ramp(t, a + 1.0, a + 1.5)), sneer=0.6, smile=0.8 * ramp(t, a + 1.2, a + 1.9), eye_squint=0.4, jaw=0.2 * pulse(t, a + 0.3, a + 0.5, a + 0.7, a + 1.0))
        for i, b in enumerate(books):
            t0 = a + 0.42 + 0.05 * i; dt = t - t0
            p0 = Vector((2.2, -3.05, 0.83 + i * 0.047))
            if dt < 0:
                b.location = p0; b.rotation_euler = (0, 0, 0.2 * (i - 1))
            else:
                v = Vector((2.2 + 0.4 * i, 0.9 - 0.3 * i, 0.6))
                z = p0.z + v.z * dt - 4.9 * dt * dt
                tl = (v.z + math.sqrt(v.z ** 2 + 2 * 9.8 * (p0.z - 0.03))) / 9.8
                dd = min(dt, tl)
                b.location = (p0.x + v.x * dd + 0.25 * v.x * (1 - math.exp(-3 * max(0, dt - tl))), p0.y + v.y * dd, max(0.03, p0.z + v.z * dd - 4.9 * dd * dd))
                b.rotation_euler = (4.0 * dd * (i - 1), 3.0 * dd, 0.2 * (i - 1) + 5 * dd)
        # tutor steps in, whip up... and freezes
        tp = PP + Vector((-1.5, -1.3, 0))
        th = aim(tp, pr.pos)
        tu.place(tp, th); tu.stand(t, 0.6)
        up = ramp(t, a + 0.9, a + 1.45); drop = ramp(t, a + 2.1, a + 2.9)
        k = up * (1 - drop)
        trem = 0.012 * math.sin(t * 38) * k
        wp = tu.W(Vector((0.35, 0.2, 1.0)).lerp(Vector((0.42, -0.05, 1.9 + trem)), k)); wd = tu.D(Vector((0.2, 0.6, -0.75)).lerp(Vector((0.15, -0.7, 0.7)), k))
        tu.grip('R', wp, wd, tu.D((-1, 0, 0))); tu.elbow('R', (1.1, -0.5, 1.3)); tu.clav('R', up=0.5 * k)
        tu.hand('L', tu.W((-0.3, 0.12, 1.0)), fwd=tu.D((0, 0.6, -0.8)), palm=tu.D((1, 0, 0)), world=True); tu.fingers('L', 0.8); tu.elbow('L', (-0.8, -0.6, 1.1))
        tu.spine(rx=-0.1 * k, rz=-0.3 * k); tu.head(rx=0.15)
        tu.face(t, brow_down=1.0, snarl=0.6 * k, press=0.7, eye_squint=0.4, frown=0.5 * drop)

        def g(tt):
            kk = ramp(tt, a + 0.9, a + 1.45) * (1 - ramp(tt, a + 2.1, a + 2.9))
            return (tu.W(Vector((0.35, 0.2, 1.0)).lerp(Vector((0.42, -0.05, 1.9)), kk)), tu.D(Vector((0.2, 0.6, -0.75)).lerp(Vector((0.15, -0.7, 0.7)), kk)))
        whip.update(t, g, lag=0.25)
        boy_takes(t, [])
        boy.face(t, brow_inner=1.0, brow_up=0.5, eye_wide=0.6, press=0.4); boy.head(rz=-0.9, rx=-0.2)
        u = ramp(t, a, 80.9)
        hdp = pr.W((0, 0, pr.h.height - 0.2))
        shoot(cam, t, vlerp((0.2, -7.6, 1.0), (0.5, -7.0, 1.05), u), (0.75, -3.0, 1.25), 26, fstop=4, focus=4.3, shake=1.2, seed=4)

    def s_8c(t):      # wide profile, prince in the foreground: the punishment crosses the frame to the wrong child
        books_rest()
        hits = [81.85, 83.15]
        tutor_whips(t, hits, BP); boy_takes(t, hits)
        prince_watch(t, smirk=0.8 * (1 - ramp(t, 81.9, 82.4)), guilt=0.5 * ramp(t, 81.9, 82.6))
        u = ramp(t, 80.9, 82.6)
        shoot(cam, t, vlerp((2.6, -3.3, 1.25), (2.35, -3.05, 1.2), u), (-0.9, -2.9, 0.98), 32, fstop=4, focus=3.4, shake=1.2 + 4 * pulse(t, 81.84, 81.9, 81.95, 82.25), seed=5)

    def s_8d(t):      # end on the boy's face for the second stroke; the prince, soft behind, finally looks away
        books_rest()
        hits = [81.85, 83.15]
        tutor_whips(t, hits, BP); boy_takes(t, hits)
        prince_watch(t, smirk=0.0, guilt=ramp(t, 82.8, 83.6))
        u = ramp(t, 82.6, 84.4)
        hd = boy.W((0, 0.15, 1.0))
        shoot(cam, t, hd + vlerp((-0.75, 1.25, -0.02), (-0.55, 0.95, -0.02), u), hd + Vector((0.0, 0, 0.03)), 50, fstop=2.4, shake=1.2 + 4 * pulse(t, 83.14, 83.2, 83.25, 83.55), seed=6)

    return [(0.0, 2.7, s_0a), (2.7, 5.2, s_0b), (75.5, 77.9, s_8a), (77.9, 80.9, s_8b), (80.9, 82.6, s_8c), (82.6, 84.4, s_8d)]
