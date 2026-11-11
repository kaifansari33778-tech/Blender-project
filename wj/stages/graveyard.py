"""Churchyard by moonlight, then at dawn: the body snatchers (No. 3)."""
import math, bpy
from mathutils import Vector, Matrix
from .. import sets, props, cast, stage
from ..anim import ramp, pulse, lerp, vlerp, noise, orient, smooth
from ..film import shoot


def build(scene, cam):
    sets.graveyard()
    day_sk = stage.sky(scene, elevation=9, rotation=115, strength=0.3, dust=3.0)
    day = scene.world
    moon = sets.night_sky(scene, strength=0.09, exposure=1.3)
    night = scene.world
    moon.data.energy = 9.0
    dig = cast.snatcher(); look = cast.tosher('lookout', 31)
    wid = cast.towns_woman('widow', 32, skirt=(0.06, 0.06, 0.07), top=(0.08, 0.08, 0.09), hair='long01', old=0.3)
    man = cast.gentleman('mourner', 33, black=True)
    shovel = props.shovel(); lan = props.lantern(energy=260); lamp = bpy.data.objects[lan['light']]
    body = props.shroud(1.7, seed=3)
    clods = props.clods(9)
    cage = sets.mortsafe((7.5, -5.0, 0.0))
    stone = sets.headstone((7.5, -3.75, 0), __import__('random').Random(2), lean=(0.02, 0, 0))
    MS = Vector((7.5, -5.0, 0))
    from ..world import light as _light
    _light('AREA', (0, 0.5, 4.5), 500, (0.6, 0.72, 1.0), size=6)

    def mode(is_day):
        scene.world = day if is_day else night
        scene.view_settings.exposure = -0.2 if is_day else 1.3
        moon.data.energy = 0.0 if is_day else 9.0
        lamp.data.energy = 0.0 if is_day else 260 * (1 + 0.1 * noise(scene.frame_current / 24, 1, 11))
        bpy.data.objects['moon'].hide_render = is_day

    def away(*actors):
        for a in actors:
            a.place((60, -60, -20), 0)

    def shovel_pose(t, a, period=1.3):
        """one dig cycle: drive down, lever, heave over the shoulder. Returns (phase 0..1, throw strength)."""
        ph = ((t - a) / period) % 1.0
        down = ramp(ph, 0.0, 0.22); lever = ramp(ph, 0.25, 0.42); heave = ramp(ph, 0.45, 0.68); back = ramp(ph, 0.75, 1.0)
        # blade tip target relative to digger (actor space): right, fwd, up
        tip = Vector((0.12, 0.62, 0.55)).lerp(Vector((0.1, 0.55, -0.1)), down).lerp(Vector((0.1, 0.5, 0.25)), lever).lerp(Vector((0.75, -0.25, 1.75)), heave).lerp(Vector((0.12, 0.62, 0.55)), back)
        ax = Vector((-0.1, 0.35, -1)).lerp(Vector((0, 0.9, -0.7)), lever).lerp(Vector((0.7, -0.5, 0.75)), heave).lerp(Vector((-0.1, 0.35, -1)), back).normalized()
        return ph, tip, ax, down, lever, heave, back

    def digger(t, a, base):
        dig.place(base, math.radians(90)); 
        ph, tip, ax, down, lever, heave, back = shovel_pose(t, a)
        bend = 0.55 * down * (1 - heave) + 0.25 * (1 - back) * heave
        dig.pelvis(up=-0.12 - 0.12 * down * (1 - heave), rx=0.15, rz=-0.35 * heave * (1 - back))
        dig.spine(rx=0.3 + bend, rz=-0.6 * heave * (1 - back)); dig.head(rx=-0.2, rz=-0.3 * heave * (1 - back))
        dig.foot('L', (-(dig.hip_w + 0.1), 0.18, 0), yaw=0.2); dig.foot('R', (dig.hip_w + 0.1, -0.15, 0), yaw=-0.3)
        tipw = dig.W(tip); axw = dig.D(ax)          # ax points from handle toward blade
        top = tipw - axw * 1.42
        orient(shovel, top + axw * 0.27, z=-axw, y=dig.D((1, 0, 0)))
        shovel.matrix_world = shovel.matrix_world @ Matrix.Translation((0, 0, -1.15 + 0.27))
        dig.grip('R', top + axw * 0.12, -axw, dig.D((-1, 0, 0))); dig.elbow('R', (1.0, -0.6, 1.2))
        dig.grip('L', top + axw * 0.75, axw, dig.D((1, 0, 0))); dig.elbow('L', (-1.0, -0.2, 0.9))
        strain = down * (1 - back) 
        dig.face(t, brow_down=0.8, eye_squint=0.5, grimace=0.6 * strain, jaw=0.25 * heave * (1 - back), snarl=0.4 * strain, press=0.3)
        # dirt leaves the blade at the top of the heave
        k = int((t - a) / 1.3)
        tl = a + k * 1.3 + 0.62 * 1.3
        for i, c in enumerate(clods):
            dt = t - tl - i * 0.012
            if 0 < dt < 0.9:
                p0 = dig.W(Vector((0.7, -0.2, 1.7)))
                v = dig.D((1.5 + 0.35 * (i % 3), -0.7 - 0.2 * (i % 4), 0)) * 1.6 + Vector((0, 0, 1.9 + 0.3 * (i % 2)))
                c.location = p0 + v * dt + Vector((0, 0, -4.9 * dt * dt))
            else:
                c.location = (0, 0, -50)
        return tipw

    def lookout(t, pos, heading):
        look.place(pos, heading); look.stand(t, 1.5)
        hp = look.W((-0.3, 0.35, 1.3))
        look.hand('L', hp, fwd=look.D((0, 1, 0.3)), palm=look.D((1, 0, 0)), world=True); look.fingers('L', 0.85); look.elbow('L', (-0.9, -0.3, 0.9))
        orient(lan, look.palm('L', 0.07, 0.03) - Vector((0, 0, 0.03)), z=(0.04 * math.sin(t * 3.7), 0.02, 1))
        look.arms_relaxed(t, 'R')
        look.head(rz=0.8 * math.sin(t * 1.1 + 1), rx=-0.05); look.gaze(yaw=0.3 * math.sin(t * 1.1 + 1.4))
        look.face(t, brow_inner=0.7, brow_up=0.4, eye_wide=0.4, press=0.4)

    def s_6a(t):      # crane up over a leaning headstone: moonlit churchyard, two figures where nobody should be
        mode(False); away(wid, man)
        body.location = (0, 0, -50)
        digger(t, 54.2, (0, -0.1, -1.16))
        lookout(t, (1.2, -1.9, 0), math.radians(-150))
        u = ramp(t, 54.6, 57.0)
        shoot(cam, t, vlerp((4.6, -6.2, 0.45), (3.6, -5.6, 2.3), u), vlerp((0.3, 0, 0.6), (0.2, 0.3, 0.5), u), lerp(26, 30, u), shake=0.8)

    def s_6b(t):      # from down in the grave looking up: the spade comes at us, moon behind his shoulder
        mode(False); away(wid, man)
        body.location = (0, 0, -50)
        digger(t, 56.75, (0, -0.25, -1.16))
        lookout(t, (0.95, 1.5, 0), math.radians(160))
        shoot(cam, t, (-0.2, 0.95, -0.9), (0.05, -0.3, 0.3), 20, shake=1.2, seed=3)

    def s_6c(t):      # tracking side shot past the stones: the body leaves on their shoulders
        mode(False); away(wid, man)
        shovel.location = (1.2, 0.6, 0.05); shovel.rotation_euler = (math.pi / 2, 0, 0.3)
        for c in clods:
            c.location = (0, 0, -50)
        a0 = Vector((1.5, -2.2, 0)); a1 = Vector((7.5, -2.9, 0))
        dig.walk(t, 59.0, 63.4, a0, a1, step=0.5, swing=0, arms='', lean=0.12, lift=0.07)
        dv = (a1 - a0).normalized()
        look.walk(t, 59.0, 63.4, a0 - dv * 1.75, a1 - dv * 1.75, step=0.5, swing=0, arms='', lean=0.14, lift=0.07, phase=0.5)
        hgt = 1.02
        head_end = dig.pos - dv * 0.12 + Vector((0, 0, hgt)); foot_end = look.pos + dv * 0.12 + Vector((0, 0, hgt - 0.04))
        sway = Vector((0, 0, 0.012 * math.sin(t * 7)))
        orient(body, foot_end + sway, z=(0, 0, 1), y=dv)
        for a, end, fw in ((dig, head_end, -1), (look, foot_end, 1)):
            for s, sg in (('L', -1), ('R', 1)):
                side = Vector((-dv.y, dv.x, 0)) * sg * 0.17
                a.hand(s, end + side * (1 if a is dig else -1) * -1 + dv * fw * 0.1 + Vector((0, 0, 0.02)), fwd=dv * fw + Vector((0, 0, 0.2)), palm=(0, 0, 1), world=True)
                a.elbow(s, (sg * 0.8, -0.6 * fw * (1 if a is look else -1), 0.9)); a.fingers(s, 0.8)
            a.spine(rx=0.25); a.head(rx=-0.1, rz=0.5 * (1 if a is dig else -0.3))
            a.face(t, brow_down=0.6, grimace=0.5, eye_squint=0.4, press=0.4)
        dig.spine(rx=0.2, rz=1.2); dig.head(rz=1.0, rx=-0.1)          # he walks half-turned, backing up with the load
        orient(lan, Vector((0.9, -1.4, 0.24)), z=(0, 0, 1))
        mid = (dig.pos + look.pos) / 2
        shoot(cam, t, mid + Vector((0.6, -4.4, 1.0)), mid + Vector((0.3, 0, 0.95)), 35, fstop=2.8, shake=1.4, seed=4)

    def s_6d(t):      # dawn: slow arc through the bars of a mortsafe to the family keeping watch
        mode(True); away(dig, look)
        body.location = (0, 0, -50); lan.location = (0, 0, -50); shovel.location = (0, 0, -50)
        for c in clods:
            c.location = (0, 0, -50)
        a = 62.0
        wid.place(MS + Vector((-0.95, 0.15, 0)), math.radians(95)); wid.stand(t, 0.6)
        man.place(MS + Vector((-1.05, -0.85, 0)), math.radians(70)); man.stand(t, 0.6)
        reach = ramp(t, a + 0.2, a + 1.3)
        bar = MS + Vector((-0.48, 0.25, 0.74))
        wid.spine(rx=0.12 + 0.2 * reach); wid.head(rx=0.35)
        wid.hand('L', vlerp(wid.W((-0.25, 0.15, 0.8)), bar + Vector((-0.06, 0, 0.03)), reach), fwd=(1, 0, -0.25), palm=(0, 0, -1), world=True); wid.fingers('L', 0.15 + 0.5 * ramp(t, a + 1.2, a + 1.7)); wid.elbow('L', (-0.8, -0.5, 1.0))
        wid.hand('R', wid.W((0.08, 0.2, 1.12)), fwd=wid.D((-0.8, 0.3, 0.5)), palm=wid.D((0, -1, 0)), world=True); wid.fingers('R', 0.5); wid.elbow('R', (0.8, -0.3, 0.9))
        wid.face(t, brow_inner=1.0, frown=0.8, eye_squint=0.3, press=0.3, eye_close=0.25)
        # he stands guard, arms folded, scanning
        man.hand('R', man.W((-0.12, 0.22, 1.2)), fwd=man.D((-1, 0.1, 0.1)), palm=man.D((0, -1, 0)), world=True); man.hand('L', man.W((0.12, 0.25, 1.15)), fwd=man.D((1, 0.1, 0.1)), palm=man.D((0, -1, 0)), world=True)
        man.elbow('R', (0.9, 0.2, 1.0)); man.elbow('L', (-0.9, 0.2, 1.0)); man.fingers('R', 0.5); man.fingers('L', 0.5)
        man.head(rz=0.5 * math.sin((t - a) * 0.9), rx=-0.02); man.face(t, brow_down=0.7, press=0.6, eye_squint=0.3, frown=0.4)
        u = ramp(t, a, 65.1)
        ang = lerp(-0.25, 0.45, u)
        shoot(cam, t, MS + Vector((math.cos(ang) * 2.5, math.sin(ang) * 2.5 - 0.2, lerp(0.5, 1.0, u))), MS + Vector((-0.7, -0.2, lerp(0.75, 1.15, u))), 32, fstop=2.8,
              focus=lerp(1.9, 3.3, smooth(u)), shake=0.9, seed=5)

    return [(54.6, 57.0, s_6a), (57.0, 59.6, s_6b), (59.6, 62.0, s_6c), (62.0, 65.1, s_6d)]
