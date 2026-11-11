"""Street market: the rat-catcher (No. 4)."""
import math
from mathutils import Vector, Euler
from .. import sets, props, cast, stage
from ..anim import ramp, pulse, lerp, vlerp, noise, orient, smooth
from ..film import shoot


def build(scene, cam):
    sets.street('victorian', seed=4, market=True)
    stage.sky(scene, elevation=52, rotation=185, strength=0.16, dust=2.0)
    scene.view_settings.exposure = -0.3
    rc = cast.ratcatcher()
    crowd = [cast.towns_woman('w1', 21), cast.gentleman('g1', 22), cast.towns_woman('w2', 23, skirt=(0.2, 0.25, 0.33), top=(0.5, 0.4, 0.3), hair='bob02', old=0.7, hat=False)]
    spots = [((-1.7, 4.2), 0.9), ((1.5, 4.6), -0.8), ((0.3, 5.4), 0.1)]      # (pos, heading) around the catcher
    rat = props.Rat('rat'); rat2 = props.Rat('rat2', fur=False)
    cage = props.cage()
    CP = Vector((0, 2.6, 0))       # where the show happens

    def crowd_update(t, react=0.0, watch=None):
        for i, (c, (p, h)) in enumerate(zip(crowd, spots)):
            c.place((p[0], p[1], 0), h); c.stand(t, 1.0); c.arms_relaxed(t)
            r = react * (0.7 + 0.3 * i / 2)
            c.spine(rx=0.03 - 0.12 * r); c.head(rx=-0.05 * r, rz=-h * 0.5)
            if r > 0.01:
                s = 'R' if i != 1 else 'L'; sg = 1 if s == 'R' else -1
                c.hand(s, vlerp(c.W((sg * 0.25, 0.05, 0.85)), c.W((sg * 0.05, 0.16, c.h.height - 0.2)), r), fwd=c.D((-sg * 0.5, 0.2, 1)), palm=c.D((0, -1, 0)), world=True)
                c.elbow(s, (sg * 0.9, 0.2, 1.0)); c.fingers(s, 0.25, spread=0.5)
            c.face(t, brow_up=0.3 + 0.7 * r, eye_wide=0.9 * r, jaw=0.5 * r if i != 1 else 0.1, snarl=0.6 * r if i == 1 else 0, upper_lip=0.5 * r if i == 1 else 0, brow_inner=0.5 * r)

    def cage_at(p):
        orient(cage, p, z=(0, 0, 1)); rat2.set(Vector(p) + Vector((0, 0, 0.045)), (0, 0, 1.3), 0, wag=0.3)

    def hide_rat2():
        rat2.set((0, 0, -50))

    def s_5a(t):      # dolly in from above the stalls: a showman arriving with his cage
        rc.walk(t, 42.5, 46.6, (0.2, 9.0, 0), (0.0, 3.2, 0), step=0.66, swing=0.45, arms='R', lean=0.02)
        gp = rc.W((-0.3, 0.08, 0.8 + rc._pel[0].z))
        rc.hand('L', gp, fwd=rc.D((0, 0.1, -1)), palm=rc.D((1, 0, 0)), world=True); rc.fingers('L', 0.85); rc.elbow('L', (-0.8, -0.6, 1.2))
        cage_at(rc.palm('L', 0.07, 0.02) - Vector((0, 0, 0.3)))
        rc.head(rz=0.3 * math.sin(t * 1.6)); rc.face(t, smile=0.6, brow_up=0.4, eye_squint=0.2)
        crowd_update(t)
        rat.set((0, 0, -50))
        u = ramp(t, 43.9, 46.2)
        shoot(cam, t, vlerp((2.2, -6.0, 4.2), (0.9, -2.2, 1.7), u), vlerp((0, 4.5, 1.6), (0, rc.pos.y, 1.25), u), lerp(26, 35, u), shake=0.8)

    def rat_run(t, a):
        """rat scurries along the kerb then is snatched at a+1.35"""
        u = (t - a) / 1.35
        x = lerp(2.9, 0.75, min(1, u)); y = 1.9 + 0.12 * math.sin(u * 9)
        hop = abs(math.sin(u * 30)) * 0.012
        return Vector((x, y, 0.036 + hop)), (0.06 * math.sin(u * 30), 0, math.pi / 2 + 0.25 * math.cos(u * 9))

    def s_5b(t):      # ground-level track with the rat; a bare hand drops into frame and takes it
        a = 46.2
        hide_rat2(); cage_at((-0.5, 2.4, 0.0))
        crowd_update(t)
        rc.place((0.55, 2.55, 0), math.radians(165))
        c = ramp(t, a + 0.3, a + 1.1)
        rc.pelvis(fwd=-0.1 * c, up=-0.03 - 0.5 * c, rx=0.3 * c); rc.spine(rx=0.1 + 0.8 * c)
        rc.foot('L', (-(rc.hip_w + 0.08), 0.15 * c, 0), yaw=0.25); rc.foot('R', (rc.hip_w + 0.08, -0.15 * c, 0), yaw=-0.25, pitch=0.45 * c)
        rp, rr = rat_run(t, a)
        catch = ramp(t, a + 1.25, a + 1.4); liftu = ramp(t, a + 1.45, a + 2.2)
        end, _ = rat_run(a + 1.35, a)
        grabp = end + Vector((0.0, 0.0, 0.075))
        hp = vlerp(rc.W((0.3, 0.3, 0.9)), end + Vector((0.1, 0.2, 0.45)), ramp(t, a + 0.4, a + 1.05)).lerp(grabp, ramp(t, a + 1.05, a + 1.32))
        hp = hp.lerp(rc.W((0.22, 0.4, 1.0)), liftu)
        rc.hand('R', hp, fwd=vlerp((-0.3, -0.8, -0.6), (-0.2, -1, 0.2), liftu), palm=vlerp((0, 0, -1), (-0.6, 0, -0.6), liftu), world=True); rc.elbow('R', (1.0, -0.3, 1.0))
        rc.fingers('R', lerp(0.1, 0.62, catch), thumb=lerp(0.0, 0.8, catch), spread=1 - catch)
        rc.hand('L', rc.W((-0.3, 0.3, 0.55 + 0.4 * (1 - c))), fwd=rc.D((0, 1, -0.5)), palm=rc.D((0, 0, -1)), world=True); rc.fingers('L', 0.3, spread=0.6); rc.elbow('L', (-0.9, -0.3, 0.9))
        rc.head(rx=-0.3 * c); rc.face(t, brow_down=0.7, eye_squint=0.4, press=0.5, grimace=0.3 * catch)
        if catch < 0.5:
            rat.set(rp, rr, t, wag=1.0)
        else:
            g = rc.palm('R', 0.075, 0.045)
            rat.set(g + Vector((0, 0, -0.01)), (0.5 * liftu + 0.25 * math.sin(t * 22) * (1 - liftu * 0.5), 0.2 * math.sin(t * 17), math.pi / 2 + 0.3 * math.sin(t * 19)), t, wag=2.0, droop=liftu)
        shoot(cam, t, Vector((rp.x * 0.45 + 0.5, 0.95, 0.07 + 0.25 * liftu)), Vector((lerp(rp.x, end.x, catch), 1.9, 0.05)).lerp(hp, liftu * 0.8), 35, fstop=2.8, shake=1.6, seed=3)

    def hold_pose(t, a, mouth):
        """standing showman: rat held up high, then (mouth) brought to the open mouth"""
        rc.place(CP, 0.0); rc.stand(t, 1.2)
        rc.spine(rx=-0.06 - 0.12 * mouth, rz=0.25 * math.sin((t - a) * 1.3) * (1 - mouth)); rc.head(rx=-0.15 - 0.4 * mouth, rz=0.2 * math.sin((t - a) * 1.3) * (1 - mouth))
        high = rc.W((0.3, 0.3, rc.h.height + 0.25)); atm = rc.W((0.03, 0.2, rc.h.height + 0.07))
        hp = high.lerp(atm, mouth)
        rc.hand('R', hp, fwd=vlerp(rc.D((0, 0.3, 1)), rc.D((-0.5, -0.3, 0.2)), mouth), palm=vlerp(rc.D((-1, 0.2, 0)), rc.D((0, -0.6, -1)), mouth), world=True)
        rc.elbow('R', (1.0, 0.2, 1.3)); rc.fingers('R', 0.62, thumb=0.8)
        rc.hand('L', rc.W((-0.45, 0.25, 1.15)), fwd=rc.D((-0.6, 0.5, 0.6)), palm=rc.D((0, 1, 0.3)), world=True); rc.fingers('L', 0.05, spread=1); rc.elbow('L', (-0.9, -0.3, 0.9))
        g = rc.palm('R', 0.075, 0.045)
        # rat hangs head-down from the fist; tail droops and lashes
        rat.set(g + Vector((0, 0, -0.03 - 0.05 * mouth)), (lerp(0.9, 1.45, mouth) + 0.12 * math.sin(t * 13), 0.2 * math.sin(t * 9), 0.3 * math.sin(t * 11) + 3.14), t, wag=1.5, droop=1.0)
        return g

    def s_1c(t):      # montage: low hero angle, rat aloft against the sky
        hide_rat2(); cage_at((-0.55, 2.3, 0.0))
        hold_pose(t, 8.2, 0.0)
        crowd_update(t, 0.4)
        rc.face(t, smile=0.9, brow_up=0.6, jaw=0.25, eye_wide=0.3)
        u = ramp(t, 8.2, 9.6)
        shoot(cam, t, CP + Vector((0.5 - 0.25 * u, -1.5, 0.75)), CP + Vector((0.15, 0, 1.65)), 28, shake=1.3, seed=5)

    def s_5c(t):      # arc from the crowd's side round to his face as the rat goes to his mouth: we get the crowd's view, then theirs of us
        a = 48.5
        hide_rat2(); cage_at((-0.55, 2.3, 0.0))
        mouth = ramp(t, a + 1.7, a + 2.9)
        hold_pose(t, a, mouth)
        crowd_update(t, ramp(t, a + 1.9, a + 2.8))
        rc.face(t, smile=0.8 * (1 - mouth), brow_up=0.6, jaw=0.2 + 0.8 * mouth, eye_wide=0.5 * mouth, lips_part=0.5, upper_lip=0.3 * mouth)
        rc.gaze(pitch=-0.25 * mouth)
        u = ramp(t, a, 52.3)
        ang = lerp(-2.25, -1.25, u)
        shoot(cam, t, CP + Vector((math.cos(ang) * lerp(2.9, 1.5, u), math.sin(ang) * lerp(2.9, 1.5, u), lerp(1.35, 1.6, u))), CP + Vector((0.05, 0.2 * u, lerp(1.45, 1.74, u))), lerp(32, 45, u), fstop=3.2, shake=1.3, seed=6)

    def s_5d(t):      # extreme close: teeth meet skin; rack from the rat to the fear in his eyes
        a = 52.3
        hide_rat2(); cage_at((-0.55, 2.3, 0.0))
        rc.place(CP, 0.0); rc.stand(t, 0.8)
        bite = ramp(t, a + 0.75, a + 0.85); jerk = pulse(t, a + 0.8, a + 0.95, a + 1.2, a + 1.9)
        hp = rc.W((0.16, 0.42, 1.38 + 0.05 * jerk))
        rc.hand('R', hp, fwd=rc.D((-0.5, 0.5, 0.5)), palm=rc.D((-0.6, -0.3, -0.6)), world=True); rc.elbow('R', (1.0, -0.4, 1.0)); rc.fingers('R', 0.62 - 0.2 * jerk, thumb=0.8 - 0.3 * jerk)
        rc.hand('L', vlerp(rc.W((-0.3, 0.2, 1.0)), hp + rc.D((-0.1, 0.02, -0.06)), ramp(t, a + 0.9, a + 1.4)), fwd=rc.D((0.6, 0.6, 0.3)), palm=rc.D((0.5, 0, 1)), world=True); rc.fingers('L', 0.5); rc.elbow('L', (-0.9, -0.4, 1.0))
        g = rc.palm('R', 0.075, 0.045)
        tw = 0.35 * math.sin(t * 16) * (1 - bite) + 0.9 * bite
        rat.set(g + Vector((0, 0, 0.01)), (0.2 + 0.2 * math.sin(t * 12), 0.5 * bite, 3.14 + 1.2 - tw), t, wag=2.5, droop=0.7)
        rc.spine(rx=-0.05 - 0.1 * jerk); rc.head(rx=0.15 - 0.25 * jerk, rz=-0.2)
        rc.gaze(yaw=-0.25, pitch=0.2)
        pain = ramp(t, a + 0.82, a + 1.0)
        rc.face(t, blink=False, smile=0.4 * (1 - pain), brow_up=0.3 + 0.5 * pain, brow_inner=pain, eye_wide=pain, jaw=0.15 + 0.5 * pain, grimace=0.8 * pain, neck=0.8 * pain, snarl=0.4 * pain)
        crowd_update(t, 1.0)
        face = rc.W((0, 0.08, rc.h.height - 0.1))
        u = ramp(t, a + 0.9, a + 1.5)
        cp = g + rc.D((0.28, 0.5, 0)) + Vector((0, 0, 0.02))
        shoot(cam, t, cp, g.lerp(face, 0.25 + 0.3 * u), 60, fstop=2.4, focus=lerp((g - cp).length, (face - cp).length, u), shake=1.6, seed=7)

    return [(8.2, 9.6, s_1c), (43.9, 46.2, s_5a), (46.2, 48.5, s_5b), (48.5, 52.3, s_5c), (52.3, 54.6, s_5d)]
