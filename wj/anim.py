"""Procedural animation layer: every pose is a smooth function of time (no stepped keys),
so motion stays fluid at any frame rate.  Actors get IK hands/feet, finger curls, gaze,
blinks, breathing and expression mixing."""
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion, Euler


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ramp(t, a, b):
    return smooth((t - a) / (b - a)) if b != a else float(t >= a)


def pulse(t, a, b, c, d):
    return ramp(t, a, b) * (1 - ramp(t, c, d))


def lerp(a, b, u):
    return a + (b - a) * u


def vlerp(a, b, u):
    return Vector(a).lerp(Vector(b), u)


def path(t, keys):
    """keys: [(time, value)] with value float or Vector/tuple; smooth ease between keys."""
    if t <= keys[0][0]:
        v = keys[0][1]
        return Vector(v) if not isinstance(v, (int, float)) else v
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ramp(t, t0, t1)
            if isinstance(v0, (int, float)):
                return lerp(v0, v1, u)
            return Vector(v0).lerp(Vector(v1), u)
    v = keys[-1][1]
    return Vector(v) if not isinstance(v, (int, float)) else v


def noise(t, seed=0.0, speed=1.0):
    """smooth pseudo-noise in -1..1"""
    x = t * speed + seed * 17.3
    return (math.sin(x * 1.0) + math.sin(x * 2.3 + 1.7) * 0.5 + math.sin(x * 4.1 + 0.3) * 0.25) / 1.75


def _empty(name, col):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    col.objects.link(e)
    return e


class Actor:
    def __init__(self, human, seed=0):
        self.h = h = human
        self.arm = arm = h.arm
        self.seed = seed
        self.R = {n: r[2].to_3x3() for n, r in h.rest.items()}
        self.head0 = {n: r[0] for n, r in h.rest.items()}
        self.pos = Vector((0, 0, 0)); self.heading = 0.0
        self.t = {}
        col = h.col
        for s in 'LR':
            for k in ('hand', 'foot', 'elbow', 'knee'):
                self.t[k + s] = _empty(f'{h.name}_{k}.{s}', col)
        # hand frames (armature rest space)
        self.hf = {}
        for s in 'LR':
            w = self.head0['wrist.' + s]
            f0 = (self.head0['finger3-1.' + s] - w).normalized()
            v1 = self.head0['finger2-1.' + s] - w; v2 = self.head0['finger5-1.' + s] - w
            n0 = v1.cross(v2).normalized()
            if n0.z > 0:
                n0 = -n0
            n0 = (n0 - f0 * n0.dot(f0)).normalized()
            t0 = f0.cross(n0)
            self.hf[s] = (f0, n0, t0)
        self.hip_h = self.head0['upperleg01.L'].z
        self.ankle_h = self.head0['foot.L'].z
        self.hip_w = abs(self.head0['upperleg01.L'].x)
        self.sh = {s: self.head0['upperarm01.' + s].copy() for s in 'LR'}
        self.arm_len = (self.head0['wrist.L'] - self.head0['upperarm01.L']).length
        self.leg_len = (self.head0['foot.L'] - self.head0['upperleg01.L']).length
        self._pel = (Vector((0, 0, 0)), Matrix.Identity(3))
        self.hs = {}
        self._constraints()
        self.reset()

    # -- setup ---------------------------------------------------------------
    def _constraints(self):
        pb = self.arm.pose.bones
        for s in 'LR':
            for tw in ('upperarm02.', 'lowerarm02.', 'upperleg02.', 'lowerleg02.'):
                b = pb[tw + s]; b.lock_ik_x = b.lock_ik_y = b.lock_ik_z = True
            for limb, tgt, pole in (('lowerarm02.', 'hand', 'elbow'), ('lowerleg02.', 'foot', 'knee')):
                c = pb[limb + s].constraints.new('IK')
                c.target = self.t[tgt + s]; c.chain_count = 4; c.use_stretch = False
                c.pole_target = self.t[pole + s]; c.iterations = 60
            for bone, tgt in (('wrist.', 'hand'), ('foot.', 'foot')):
                c = pb[bone + s].constraints.new('COPY_ROTATION')
                c.target = self.t[tgt + s]; c.target_space = 'WORLD'; c.owner_space = 'WORLD'
        # calibrate pole angles
        self.reset_targets()
        for s in 'LR':
            for limb, mid, pole in (('lowerarm02.', 'lowerarm01.', 'elbow'), ('lowerleg02.', 'lowerleg01.', 'knee')):
                c = pb[limb + s].constraints['IK']
                best = None
                for ang in (0, 90, 180, -90):
                    c.pole_angle = math.radians(ang)
                    bpy.context.view_layer.update()
                    d = ((self.arm.matrix_world @ pb[mid + s].head) - self.t[pole + s].matrix_world.translation).length
                    if best is None or d < best[0]:
                        best = (d, ang)
                c.pole_angle = math.radians(best[1])

    def reset_targets(self):
        for s, sg in (('L', 1), ('R', -1)):
            self.hand(s, (0.25 * -sg, 0.25, self.hip_h + 0.1), fwd=(0, 1, -0.3), palm=(sg, 0, 0))
            self.foot(s, (self.hip_w * -sg, 0, 0))
            self.elbow(s, (0.5 * -sg, -0.6, 1.0))
            self.knee(s, (self.hip_w * -sg * 1.3, 1.5, 0.5))
        bpy.context.view_layer.update()

    # -- frames ---------------------------------------------------------------
    def place(self, pos, heading=0.0):
        """heading: radians, 0 = facing world -Y; positive turns to the actor's left."""
        self.pos = Vector(pos); self.heading = heading
        self.arm.location = self.pos
        self.arm.rotation_euler = (0, 0, heading)

    def M(self):
        return Matrix.Translation(self.pos) @ Matrix.Rotation(self.heading, 4, 'Z')

    def W(self, v):
        """actor space (right, forward, up) -> world"""
        return self.M() @ Vector((-v[0], -v[1], v[2]))

    def D(self, v):
        """actor-space direction -> world direction"""
        return Matrix.Rotation(self.heading, 3, 'Z') @ Vector((-v[0], -v[1], v[2]))

    def reset(self):
        for b in self.arm.pose.bones:
            b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
        self.reset_targets()

    # -- body ---------------------------------------------------------------
    def rot(self, bone, rx=0.0, ry=0.0, rz=0.0):
        """Rotate bone relative to its parent, angles (radians) about ACTOR axes:
        rx>0 bends forward, ry>0 leans to actor's right, rz>0 turns to actor's left."""
        R = self.R[bone]
        Q = Euler((rx, -ry, rz), 'XYZ').to_matrix()
        self.arm.pose.bones[bone].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()

    def pelvis(self, right=0.0, fwd=0.0, up=0.0, rx=0.0, ry=0.0, rz=0.0):
        """Offset/rotate the hips (root bone) in actor space; `up` is relative to standing."""
        R = self.R['root']
        b = self.arm.pose.bones['root']
        b.location = R.inverted() @ Vector((-right, -fwd, up))
        Q = Euler((rx, -ry, rz), 'XYZ').to_matrix()
        b.rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()
        self._pel = (Vector((right, fwd, up)), Q)

    def spine(self, rx=0.0, ry=0.0, rz=0.0):
        for n, w in (('spine05', .15), ('spine04', .2), ('spine03', .2), ('spine02', .25), ('spine01', .2)):
            self.rot(n, rx * w, ry * w, rz * w)

    def head(self, rx=0.0, ry=0.0, rz=0.0):
        for n, w in (('neck01', .2), ('neck02', .2), ('neck03', .2), ('head', .4)):
            self.rot(n, rx * w, ry * w, rz * w)

    def clav(self, s, up=0.0, fwd=0.0):
        sg = 1 if s == 'L' else -1
        self.rot('clavicle.' + s, 0, -up * sg, -fwd * sg)

    def gaze(self, yaw=0.0, pitch=0.0):
        for s in 'LR':
            self.rot('eye.' + s, pitch, 0, yaw)

    # -- limbs (targets in ACTOR space unless world=True) -----------------------
    def _w(self, p, world):
        return Vector(p) if world else self.W(p)

    def _d(self, d, world):
        return Vector(d).normalized() if world else self.D(d).normalized()

    def hand(self, s, pos, fwd=(0, 1, 0), palm=(0, 0, -1), world=False):
        """pos = wrist position; fwd = direction fingers point; palm = direction the palm faces."""
        e = self.t['hand' + s]
        e.location = self._w(pos, world)
        f = self._d(fwd, world); n = self._d(palm, world)
        n = (n - f * n.dot(f)).normalized()
        t = f.cross(n)
        self.hs[s] = (e.location.copy(), f, n, t)
        f0, n0, t0 = self.hf[s]
        F = Matrix((f, n, t)).transposed(); F0 = Matrix((f0, n0, t0)).transposed()
        e.rotation_euler = (F @ F0.transposed() @ self.R['wrist.' + s]).to_euler()

    def elbow(self, s, pos, world=False):
        self.t['elbow' + s].location = self._w(pos, world)

    def knee(self, s, pos, world=False):
        self.t['knee' + s].location = self._w(pos, world)

    def foot(self, s, pos, pitch=0.0, yaw=0.0, roll=0.0, world=False):
        """pos = point on the ground under the ankle (sole height added); pitch>0 = toes down."""
        e = self.t['foot' + s]
        p = self._w(pos, world)
        e.location = p + Vector((0, 0, self.ankle_h))
        Q = Matrix.Rotation(self.heading + yaw, 3, 'Z') @ Euler((pitch, roll, 0), 'XYZ').to_matrix()
        e.rotation_euler = (Q @ self.R['foot.' + s]).to_euler()
        k = self.t['knee' + s]
        k.location = p + Matrix.Rotation(self.heading + yaw, 3, 'Z') @ Vector((0, -1.5, 0.5))

    def fingers(self, s, curl=0.2, thumb=None, spread=0.0, each=None):
        """curl 0 (flat) .. 1 (fist). each = per-finger curls [index, middle, ring, pinky]."""
        f0, n0, t0 = self.hf[s]
        sg = 1 if s == 'L' else -1
        each = each or [curl] * 4
        for i, c in zip((2, 3, 4, 5), each):
            for j, k in ((1, 1.25), (2, 1.5), (3, 1.0)):
                bn = f'finger{i}-{j}.{s}'
                R = self.R[bn]
                Q = Matrix.Rotation(c * k, 3, t0)
                if j == 1 and spread:
                    Q = Matrix.Rotation(spread * (i - 3.5) * 0.12 * sg, 3, n0) @ Q
                self.arm.pose.bones[bn].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()
        th = curl if thumb is None else thumb
        d0 = (self.h.rest[f'finger1-2.{s}'][1] - self.h.rest[f'finger1-2.{s}'][0]).normalized()
        ax = d0.cross(n0 * 0.6 + f0 * 0.8).normalized()
        for j, k in ((1, 0.5), (2, 0.6), (3, 0.9)):
            bn = f'finger1-{j}.{s}'
            R = self.R[bn]
            Q = Matrix.Rotation(th * k, 3, ax)
            if j == 1:
                Q = Matrix.Rotation(th * 0.5, 3, f0 * -sg * -1) @ Q
            self.arm.pose.bones[bn].rotation_quaternion = (R.inverted() @ Q @ R).to_quaternion()

    # -- face ---------------------------------------------------------------
    def blink(self, t):
        """natural blink track 0..1"""
        r = random.Random(self.seed * 7919 + 13)
        tt, v = -r.uniform(0, 2), 0.0
        while tt < t + 1:
            tt += r.uniform(1.8, 4.2)
            v = max(v, pulse(t, tt, tt + 0.07, tt + 0.1, tt + 0.22))
        return v

    def face(self, t, blink=True, **kw):
        """expression units; l/r pairs may be given without side, e.g. brows_up=.5.
        Shortcuts: brow_up, brow_down, brow_inner, eye_wide, eye_squint, eye_close, smile, frown,
        jaw (mouth-open), snarl, lips_part, pucker, grimace, press."""
        m = {}

        def both(base, v):
            m[base.replace('#', 'left')] = v; m[base.replace('#', 'right')] = v
        pairs = dict(brow_up='eyebrows-#-up', brow_down='eyebrows-#-down', brow_inner='eyebrows-#-inner-up',
                     brow_outer='eyebrows-#-extern-up', eye_wide='eye-#-opened-up', eye_squint='eye-#-slit',
                     eye_close='eye-#-closure', snarl='nose-#-elevation')
        single = dict(smile='mouth-corner-puller', frown='mouth-depression', jaw='mouth-open', lips_part='mouth-parling',
                      pucker='mouth-pursing', grimace='mouth-retraction', press='mouth-compression',
                      upper_lip='mouth-elevation', wide='mouth-part-later', neck='neck-platysma', nose='nose-compression',
                      sneer='mouth-upward-retraction', pout='mouth-protusion', dretract='mouth-depression-retraction')
        for k, v in kw.items():
            if k in pairs:
                both(pairs[k], v)
            elif k in single:
                m[single[k]] = v
            else:
                m[k.replace('_', '-')] = v
        if blink:
            b = self.blink(t)
            for sd in ('left', 'right'):
                key = f'eye-{sd}-closure'
                m[key] = max(m.get(key, 0), b)
        self.h.face(**m)

    def breathe(self, t, amount=1.0):
        a = math.sin(t * 2 * math.pi / 3.6 + self.seed) * 0.012 * amount
        return a

    # -- canned motion ---------------------------------------------------------
    def stand(self, t, sway=1.0, feet=0.0):
        """relaxed idle: weight shift, breathing; feet planted."""
        sx = noise(t, self.seed, 0.5) * 0.012 * sway
        self.pelvis(right=sx, up=-0.01 + self.breathe(t) * 0.2, ry=sx * 1.5)
        self.spine(rx=0.03 + self.breathe(t), ry=-sx * 2)
        self.head(rx=noise(t, self.seed + 3, 0.7) * 0.03, rz=noise(t, self.seed + 5, 0.4) * 0.05)
        for s, sg in (('L', -1), ('R', 1)):
            self.foot(s, (sg * (self.hip_w + 0.02 + feet), 0, 0), yaw=-sg * 0.15)

    def arms_relaxed(self, t, which='LR', swing=0.0):
        for s, sg in (('L', -1), ('R', 1)):
            if s not in which:
                continue
            sw = swing if s == 'L' else -swing
            sh = self.sh[s]
            L = self.arm_len * 0.97
            p = (sg * (abs(sh.x) + 0.07), 0.04 + math.sin(sw) * L * 0.6, sh.z - L * math.cos(sw * 0.6) + self._pel[0].z)
            self.hand(s, p, fwd=(0, 0.25 + sw, -1), palm=(-sg, 0, 0))
            self.elbow(s, (sg * 0.6, -0.8, sh.z - 0.2))
            self.fingers(s, 0.35 + 0.05 * noise(t, self.seed + sg, 0.8))

    def walk(self, t, t0, t1, a, b, step=0.68, lift=0.09, bob=0.022, swing=0.5, arms='LR', lean=0.05, phase=0.0, hip=1.0):
        """Walk along a straight line a->b (world xy) during t0..t1 with eased start/stop.
        Returns travelled distance; sets feet, pelvis, spine, arm swing."""
        a = Vector(a); b = Vector(b)
        total = (b - a).length
        u = clamp((t - t0) / (t1 - t0))
        # ease in/out over ~half a step while keeping constant speed in the middle
        e = 0.12
        if u < e:
            d = total * (u * u / (2 * e)) / (1 - e)
        elif u > 1 - e:
            v = 1 - u
            d = total * (1 - (v * v / (2 * e)) / (1 - e))
        else:
            d = total * (u - e / 2) / (1 - e)
        dirv = (b - a).normalized()
        heading = math.atan2(dirv.x, -dirv.y)
        moving = pulse(t, t0 - 0.01, t0 + 0.35, t1 - 0.35, t1 + 0.01)
        self.place(a + dirv * d, heading)
        ph = d / (2 * step) + phase
        feet = {}
        for s, off, sg in (('L', 0.0, -1), ('R', 0.5, 1)):
            x = ph + off
            c = math.floor(x); f = x - c
            if f < 0.5:      # stance
                sf = (c + 0.25) * 2 * step; h = 0.0; pitch = 0.0
                roll_off = (f - 0.25) / 0.25      # -1 heel strike .. 1 toe off
                pitch = max(0, roll_off) ** 2 * 0.35 * moving - max(0, -roll_off) ** 2 * 0.18 * moving
            else:            # swing
                v = (f - 0.5) / 0.5
                sv = v * v * (3 - 2 * v)
                sf = (c + 0.25 + sv) * 2 * step
                h = math.sin(math.pi * v) ** 1.3 * lift * moving
                pitch = lerp(0.35, -0.18, sv) * moving + math.sin(math.pi * v) * 0.25 * moving
            rel = (sf - phase * 2 * step) - d
            rel = clamp(rel, -step * 0.75, step * 0.75) * (0.25 + 0.75 * moving) if total > 0 else 0
            feet[s] = rel
            self.foot(s, (sg * (self.hip_w + 0.015), rel, h), pitch=pitch, yaw=-sg * 0.08)
        cyc = ph * 2 * math.pi
        sway = math.sin(cyc) * 0.022 * moving * hip      # toward stance foot
        self.pelvis(right=sway, up=-0.035 - bob * (0.5 + 0.5 * math.cos(2 * cyc)) * moving,
                    rz=math.sin(cyc + math.pi / 2) * 0.09 * moving * hip, ry=-math.sin(cyc) * 0.035 * moving * hip, rx=lean * 0.3)
        self.spine(rx=lean + self.breathe(t), rz=-math.sin(cyc + math.pi / 2) * 0.16 * moving, ry=math.sin(cyc) * 0.03 * moving)
        self.head(rx=-lean * 0.5, rz=math.sin(cyc + math.pi / 2) * 0.05 * moving)
        sw = math.sin(cyc + math.pi / 2) * swing * moving
        self.arms_relaxed(t, arms, swing=sw)
        return d

    def palm(self, s, along=0.085, out=0.03):
        """world position of the palm centre (from the last hand() call)"""
        p, f, n, t = self.hs[s]
        return p + f * along + n * out

    def bone_world(self, bone, u=0.5, off=(0, 0, 0)):
        """world position of a point along a posed bone (+ offset in ACTOR-REST axes rotated with the bone)"""
        bpy.context.view_layer.update()
        pb = self.arm.pose.bones[bone]
        M = self.arm.matrix_world @ pb.matrix
        local = Vector((0, pb.bone.length * u, 0)) + self.R[bone].inverted() @ Vector(off)
        return M @ local

    def grip(self, s, pos, d, n, world=True):
        """Hold a handle: wrist at pos, handle pointing along d (out of the thumb side), palm facing n."""
        d = self._d(d, world); n = self._d(n, world)
        f = n.cross(d) if s == 'R' else d.cross(n)
        self.hand(s, pos if world else self.W(pos), fwd=f, palm=n, world=True)
        self.fingers(s, 0.85, thumb=0.6)

    def head_pos(self):
        bpy.context.view_layer.update()
        return self.arm.matrix_world @ self.arm.pose.bones['head'].tail


def orient(o, pos, z=(0, 0, 1), y=(0, 1, 0)):
    """Place prop: local Z -> z, local Y -> y (orthonormalised)."""
    z = Vector(z).normalized(); y = Vector(y)
    y = (y - z * y.dot(z))
    y = y.normalized() if y.length > 1e-6 else z.orthogonal().normalized()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(pos)
    o.matrix_world = M


def attach(o, human, bone, loc, rot=(0, 0, 0), scale=1.0):
    """Rigidly attach prop to a bone; loc/rot given in ACTOR REST space (armature coords)."""
    arm = human.arm
    b = arm.data.bones[bone]
    P = b.matrix_local @ Matrix.Translation((0, b.length, 0))
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bone
    o.matrix_parent_inverse = Matrix.Identity(4)
    M = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Scale(scale, 4)
    o.matrix_basis = P.inverted() @ M
