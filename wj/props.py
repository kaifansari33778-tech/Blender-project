"""Props: everything hand-held or dressed into the sets, plus the rat and the whip."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from .world import mat, obj, box, cyl, sphere, join, light


def lathe(profile, seg=16, material=None, name='lathe', axis='Z', ell=None, smooth=True):
    """profile: [(pos, radius)] along axis; ell: optional [(sx, sy)] per ring for elliptical sections."""
    bm = bmesh.new()
    rings = []
    for k, (p, r) in enumerate(profile):
        ex, ey = ell[k] if ell else (1, 1)
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            x, y = math.cos(a) * r * ex, math.sin(a) * r * ey
            co = dict(Z=(x, y, p), Y=(x, p, y), X=(p, x, y))[axis]
            ring.append(bm.verts.new(co))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj(name, bm, material, smooth=smooth)


def bucket():
    w = mat('wood', c=(0.25, 0.17, 0.1))
    bm = bmesh.new()
    seg = 20
    for r_out, r_in in ((0.13, 0.12),):
        pass
    o = lathe([(0, 0.105), (0.24, 0.135), (0.24, 0.125), (0.015, 0.097), (0.015, 0.0)][:4] + [(0.016, 0.02)], 20, w, 'bucket')
    parts = [o]
    for z in (0.05, 0.19):
        parts.append(cyl(0.11 + z * 0.125 + 0.004, 0.018, (0, 0, z), mat('metal', c=(0.12, 0.11, 0.1)), caps=False))
    # bail handle
    bm = bmesh.new()
    pts = [Vector((math.cos(a) * 0.135, 0, 0.23 + math.sin(a) * 0.13)) for a in [math.pi * i / 14 for i in range(15)]]
    prev = None
    for p in pts:
        c = bmesh.ops.create_circle(bm, segments=6, radius=0.004, matrix=Matrix.Translation(p) @ Matrix.Rotation(math.pi / 2, 4, 'X'))['verts']
        if prev:
            for i in range(6):
                bm.faces.new((prev[i], prev[(i + 1) % 6], c[(i + 1) % 6], c[i]))
        prev = c
    parts.append(obj('bail', bm, mat('metal', c=(0.1, 0.1, 0.1)), smooth=True))
    return join(parts, 'bucket')


def jar(leeches=5):
    g = lathe([(0, 0.045), (0.11, 0.05), (0.13, 0.035), (0.14, 0.04)], 20, mat('clear'), 'jar')
    parts = [g]
    r = random.Random(3)
    for i in range(leeches):
        l = leech(); l.location = (r.uniform(-.02, .02), r.uniform(-.02, .02), 0.012 + i * 0.012); l.rotation_euler = (0.2, 0.3, r.uniform(0, 6))
        parts.append(l)
    return join(parts, 'jar')


def leech(scale=1.0):
    m = mat('plain', c=(0.035, 0.03, 0.02), rough=0.18)
    o = lathe([(-0.03, 0.001), (-0.026, 0.004), (-0.012, 0.007), (0.005, 0.008), (0.02, 0.006), (0.028, 0.0035), (0.031, 0.001)], 10, m, 'leech', axis='Y',
              ell=[(1, .7)] * 7)
    o.scale = (scale,) * 3
    return o


def lantern(energy=60, color=(1.0, 0.62, 0.3)):
    me = mat('metal', c=(0.08, 0.07, 0.06), rough=0.5)
    parts = [box((0.1, 0.1, 0.012), (0, 0, -0.2), me), box((0.11, 0.11, 0.012), (0, 0, -0.04), me)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box((0.008, 0.008, 0.16), (sx * 0.045, sy * 0.045, -0.12), me))
    parts.append(cyl(0.02, 0.03, (0, 0, -0.02), me, r2=0.006))
    parts.append(box((0.085, 0.085, 0.15), (0, 0, -0.12), mat('clear')))
    parts.append(sphere(0.016, (0, 0, -0.13), mat('emit', c=color, e=60), scale=(1, 1, 1.6), seg=8))
    o = join(parts, 'lantern')
    l = light('POINT', (0, 0, -0.13), energy, color, size=0.03)
    l.parent = o
    o['light'] = l.name
    return o


def shovel():
    parts = [cyl(0.016, 1.15, (0, 0, 0.575), mat('wood', c=(0.3, 0.2, 0.12))),
             box((0.19, 0.012, 0.27), (0, 0, -0.12), mat('metal', c=(0.18, 0.17, 0.16), rough=0.5), bevel=0.004),
             cyl(0.02, 0.12, (0, 0, 1.15), mat('wood', c=(0.3, 0.2, 0.12)), rot=(0, math.pi / 2, 0))]
    return join(parts, 'shovel')


def coin(gold=False):
    c = (0.9, 0.62, 0.2) if gold else (0.55, 0.3, 0.16)
    return cyl(0.013, 0.0022, (0, 0, 0), mat('metal', c=c, rough=0.3), seg=18, name='coin')


def dung():
    m = mat('mud', c=(0.11, 0.07, 0.035))
    parts = [sphere(0.022, (dx, dy, 0.012 + dz), m, scale=(1.3, 1, .8), seg=8, noise=0.006, seed=i)
             for i, (dx, dy, dz) in enumerate([(0, 0, 0), (0.03, 0.01, 0), (-0.02, 0.025, 0), (0.008, 0.012, 0.018)])]
    return join(parts, 'dung')


def shroud(length=1.7, seed=0, color=(0.62, 0.58, 0.5)):
    """A body sewn into a winding sheet, lying along +Y, back on z=0."""
    s = length / 1.7
    prof = [(0, 0.02), (0.03, 0.085), (0.12, 0.105), (0.22, 0.09), (0.27, 0.075), (0.36, 0.2), (0.55, 0.19), (0.75, 0.165), (0.95, 0.175),
            (1.2, 0.13), (1.45, 0.1), (1.6, 0.085), (1.68, 0.1), (1.7, 0.02)]
    ell = [(1, 1), (1, 1), (1, 1.05), (1, 1), (1, .9), (1, .55), (1, .6), (1, .6), (1, .58), (1, .6), (1, .62), (1, .7), (.9, 1.1), (1, 1)]
    o = lathe([(p * s, r * s) for p, r in prof], 18, mat('cloth', c=color, scale=9), 'shroud', axis='Y', ell=ell)
    from mathutils import noise as mn
    off = Vector((seed * 3.1, seed * 1.7, 0))
    for v in o.data.vertices:
        v.co += v.normal * mn.noise(v.co * 9 + off) * 0.018
        v.co.z += 0.105 * s
    parts = [o]
    for y in (0.3, 0.9, 1.5):
        parts.append(cyl(0.2 * s if y < 1.2 else 0.11 * s, 0.012, (0, y * s, 0.105 * s), mat('plain', c=(0.3, 0.24, 0.15), rough=0.9), rot=(math.pi / 2, 0, 0), caps=False))
        parts[-1].scale = (1, 1, 0.62)
    return join(parts, 'shroud')


def cart():
    w = mat('wood', c=(0.21, 0.14, 0.08)); me = mat('metal', c=(0.07, 0.07, 0.07), rough=0.6)
    parts = [box((0.95, 1.9, 0.05), (0, 0, 0.62), w)]
    for sx in (-1, 1):
        parts.append(box((0.04, 1.9, 0.3), (sx * 0.475, 0, 0.78), w))
        parts.append(box((0.05, 1.3, 0.05), (sx * 0.4, -1.55, 0.62), w, rot=(0.06, 0, 0)))     # shafts toward -Y (pusher side)
        parts.append(box((0.05, 0.05, 0.62), (sx * 0.4, 0.8, 0.31), w))
    parts.append(box((0.95, 0.04, 0.3), (0, 0.95, 0.78), w))
    body = join(parts, 'cart')
    wheels = []
    for sx in (-1, 1):
        ps = [cyl(0.52, 0.06, (0, 0, 0), w, rot=(0, math.pi / 2, 0), seg=28, caps=False),
              cyl(0.47, 0.05, (0, 0, 0), w, rot=(0, math.pi / 2, 0), seg=28, caps=False),
              cyl(0.535, 0.045, (0, 0, 0), me, rot=(0, math.pi / 2, 0), seg=28, caps=False),
              cyl(0.07, 0.14, (0, 0, 0), w, rot=(0, math.pi / 2, 0), seg=12)]
        for k in range(8):
            a = math.pi * k / 8
            ps.append(box((0.04, 0.05, 0.96), (0, 0, 0), w, rot=(a, 0, 0)))
        wh = join(ps, 'wheel')
        wh.parent = body; wh.location = (sx * 0.56, -0.1, 0.53)
        wheels.append(wh)
    return body, wheels


def barrel(h=0.9, r=0.3):
    w = mat('wood', c=(0.24, 0.16, 0.09))
    o = lathe([(0, r * .85), (h * .25, r * .98), (h * .5, r), (h * .75, r * .98), (h, r * .85)], 18, w, 'barrel')
    parts = [o] + [cyl(r * (0.9 if z in (0.08, 0.92) else 0.985) + 0.004, 0.035, (0, 0, h * z), mat('metal', c=(0.1, 0.09, 0.08)), caps=False) for z in (0.08, 0.3, 0.7, 0.92)]
    return join(parts, 'barrel')


def crown():
    g = mat('metal', c=(0.95, 0.68, 0.2), rough=0.25)
    parts = [cyl(0.088, 0.035, (0, 0, 0), g, caps=False, seg=24)]
    for i in range(8):
        a = 2 * math.pi * i / 8
        parts.append(cyl(0.013, 0.05, (math.cos(a) * 0.088, math.sin(a) * 0.088, 0.04), g, r2=0.001, seg=6))
        parts.append(sphere(0.008, (math.cos(a + .39) * 0.09, math.sin(a + .39) * 0.09, 0.0), mat('plain', c=(0.5, 0.02, 0.03), rough=0.1), seg=8))
    o = join(parts, 'crown')
    m = o.modifiers.new('s', 'SOLIDIFY'); m.thickness = 0.004
    return o


def bell():
    br = mat('metal', c=(0.75, 0.55, 0.2), rough=0.3)
    o = lathe([(0, 0.055), (0.01, 0.05), (0.06, 0.035), (0.085, 0.02), (0.09, 0.008)], 18, br, 'bell')
    h = cyl(0.012, 0.1, (0, 0, 0.14), mat('wood', c=(0.15, 0.08, 0.05)))
    return join([o, h], 'bell')


def flatcap(color=(0.1, 0.09, 0.08)):
    m = mat('cloth', c=color, scale=20)
    top = sphere(0.104, (0, 0.0, 0.0), m, scale=(1, 1.14, 0.5), seg=16)
    brim = sphere(0.07, (0, -0.105, -0.022), m, scale=(1.1, 0.9, 0.12), seg=12)
    return join([top, brim], 'cap')


def tophat(color=(0.03, 0.03, 0.035)):
    m = mat('plain', c=color, rough=0.45)
    return join([cyl(0.092, 0.17, (0, 0, 0.085), m, r2=0.098, seg=24), cyl(0.15, 0.008, (0, 0, 0.0), m, seg=24),
                 cyl(0.095, 0.025, (0, 0, 0.018), mat('plain', c=(0.1, 0.1, 0.1), rough=0.3), seg=24, caps=False)], 'tophat')


def hide_rack():
    w = mat('wood', c=(0.22, 0.15, 0.09))
    parts = [box((0.07, 0.07, 2.0), (-1.1, 0, 1.0), w), box((0.07, 0.07, 2.0), (1.1, 0, 1.0), w), box((2.4, 0.06, 0.06), (0, 0, 1.95), w)]
    r = random.Random(4)
    for i, x in enumerate((-0.6, 0.05, 0.7)):
        c = [(0.42, 0.26, 0.14), (0.5, 0.36, 0.22), (0.3, 0.17, 0.09)][i]
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=8, y_segments=10, size=0.5)
        from mathutils import noise as mn
        for v in bm.verts:
            x0, y0 = v.co.x, v.co.y
            edge = 1 + 0.12 * mn.noise(Vector((x0 * 3, y0 * 3, i)))
            v.co = Vector((x0 * 0.55 * edge * (1 - 0.25 * abs(y0)), 0.04 * math.sin(x0 * 7 + i) + 0.02 * mn.noise(Vector((x0 * 5, y0 * 5, i * 2))), y0 * 1.45))
        h = obj('hide', bm, mat('plain', c=c, rough=0.55), smooth=True)
        h.location = (x, 0, 1.2); m = h.modifiers.new('s', 'SOLIDIFY'); m.thickness = 0.006
        parts.append(h)
    return join(parts, 'hide_rack')


# ------------------------------------------------------------------ rat
class Rat:
    """Brown rat (~22 cm body) with fur, ears, bead eyes, paws and a procedurally whipping tail.
    Body lies along -Y (nose toward -Y) so it matches the actors' facing convention."""

    def __init__(self, name='rat', scale=1.0, fur=True, color=(0.16, 0.11, 0.075)):
        s = scale
        skin = mat('plain', c=(0.55, 0.36, 0.33), rough=0.5, sss=0.3)
        prof = [(-0.118, 0.002), (-0.112, 0.008), (-0.095, 0.017), (-0.07, 0.026), (-0.045, 0.031), (-0.02, 0.036), (0.02, 0.046), (0.06, 0.05),
                (0.09, 0.046), (0.108, 0.034), (0.118, 0.016), (0.121, 0.004)]
        ell = [(1, 1), (1, .9), (1, .95), (1, 1), (1.05, 1), (1.05, 1), (1.1, 1), (1.12, 1), (1.1, 1), (1, 1), (1, 1), (1, 1)]
        body = lathe(prof, 16, mat('fur', c=color), name, axis='Y', ell=ell)
        for v in body.data.vertices:      # arch the back, drop the head, flatten the belly
            y = v.co.y
            v.co.z += 0.014 * math.exp(-((y - 0.03) / 0.07) ** 2) - 0.012 * max(0, -y - 0.04) / 0.08
            if v.co.z < -0.02:
                v.co.z = -0.02 + (v.co.z + 0.02) * 0.4
        body.data.update()
        self.ob = body
        body.scale = (s, s, s)
        parts = []
        for sx in (-1, 1):
            ear = sphere(0.016, (sx * 0.022, -0.052, 0.034), skin, scale=(0.9, 0.25, 1.0), seg=10); ear.rotation_euler = (-0.3, sx * 0.4, sx * 0.5)
            eye = sphere(0.0055, (sx * 0.018, -0.083, 0.012), mat('plain', c=(0.005, 0.005, 0.005), rough=0.03), seg=10)
            parts += [ear, eye]
            for y, sp in ((-0.04, 0.03), (0.07, 0.04)):
                parts.append(sphere(0.011, (sx * sp, y - 0.012, -0.032), skin, scale=(0.8, 1.9, 0.45), seg=8))
                parts.append(cyl(0.008, 0.03, (sx * sp, y, -0.02), mat('fur', c=color), seg=8))
            for k in range(4):   # whiskers
                wz = cyl(0.00035, 0.05, (sx * 0.03, -0.105, -0.002 + k * 0.003), mat('plain', c=(0.8, 0.8, 0.8), rough=0.4), rot=(0.25 * (k - 1.5), math.pi / 2 + sx * 0.5, 0), seg=4)
                parts.append(wz)
        parts.append(sphere(0.005, (0, -0.118, -0.006), mat('plain', c=(0.6, 0.3, 0.3), rough=0.3), seg=8))
        parts.append(box((0.006, 0.002, 0.007), (0, -0.112, -0.014), mat('plain', c=(0.9, 0.8, 0.5), rough=0.3)))   # incisors
        for p in parts:
            p.parent = body
        self.parts = parts
        if fur:
            ps = body.modifiers.new('fur', 'PARTICLE_SYSTEM').particle_system
            st = ps.settings
            st.type = 'HAIR'; st.count = 3000; st.hair_length = 0.009; st.hair_step = 2
            st.child_type = 'INTERPOLATED'; st.child_percent = 8; st.rendered_child_count = 8; st.clump_factor = 0.25
            st.roughness_1 = 0.02; st.roughness_endpoint = 0.01
            st.root_radius = 1.0; st.tip_radius = 0.1; st.radius_scale = 0.0005
            st.object_align_factor = (0, 0.006, 0)    # combed toward the tail
            st.material = 1
            st.use_hair_bspline = False
        # tail
        cu = bpy.data.curves.new(name + '_tail', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0052 * s; cu.bevel_resolution = 3
        sp = cu.splines.new('POLY'); self.N = 14; sp.points.add(self.N - 1)
        for i, p in enumerate(sp.points):
            p.radius = 1.0 - 0.9 * i / (self.N - 1)
        cu.materials.append(skin)
        self.tail = bpy.data.objects.new(name + '_tail', cu); bpy.context.scene.collection.objects.link(self.tail)
        self.s = s
        self.update(0)

    def set(self, loc, rot=(0, 0, 0), t=0.0, wag=1.0, droop=0.0):
        self.ob.location = loc; self.ob.rotation_euler = rot
        self.update(t, wag, droop)

    def update(self, t, wag=1.0, droop=0.0):
        M = self.ob.matrix_basis if True else None
        from mathutils import Euler
        M = Matrix.Translation(self.ob.location) @ Euler(self.ob.rotation_euler).to_matrix().to_4x4() @ Matrix.Scale(self.s, 4)
        sp = self.tail.data.splines[0]
        L = 0.2
        for i, p in enumerate(sp.points):
            u = i / (self.N - 1)
            x = math.sin(t * 9 - u * 4) * 0.03 * u * wag + math.sin(t * 3.1 + u * 2) * 0.02 * u * wag
            z = -0.01 - 0.02 * u + 0.025 * u * u * (1 - droop)
            loc = M @ Vector((x, 0.118 + u * L, z))
            if droop:   # hang under gravity in world space
                base = M @ Vector((0, 0.118, -0.01))
                hang = base + Vector((math.sin(t * 5 + u * 3) * 0.012 * u * wag, 0, -u * L))
                loc = loc.lerp(hang, droop * min(1, u * 2.5))
            p.co = (*loc, 1)


# ------------------------------------------------------------------ whip
class Whip:
    """A tapered leather lash that trails the handle with per-segment delay, so it arcs,
    snaps and recoils like a real whip instead of swinging as a stick."""

    def __init__(self, length=1.25, n=22, handle=0.32):
        cu = bpy.data.curves.new('whip', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0075; cu.bevel_resolution = 3
        sp = cu.splines.new('POLY'); sp.points.add(n - 1)
        for i, p in enumerate(sp.points):
            u = i / (n - 1)
            p.radius = 1.5 if u < handle / (length + handle) else max(0.12, 1.0 - u * 0.95)
        cu.materials.append(mat('plain', c=(0.07, 0.04, 0.025), rough=0.45))
        self.ob = bpy.data.objects.new('whip', cu); bpy.context.scene.collection.objects.link(self.ob)
        self.n = n; self.length = length; self.handle = handle

    def update(self, t, grip_fn, lag=0.2, gravity=0.35):
        """grip_fn(t) -> (position, direction) of the handle in world space."""
        sp = self.ob.data.splines[0]
        tot = self.length + self.handle
        for i, p in enumerate(sp.points):
            d = i / (self.n - 1) * tot
            if d <= self.handle:
                pos, dr = grip_fn(t)
                co = pos + dr * d
            else:
                u = (d - self.handle) / self.length
                tt = t - lag * u ** 0.8
                pos, dr = grip_fn(tt)
                pos0, dr0 = grip_fn(t)
                # where a rigid extension of the delayed handle would put this point
                co = pos + dr * d
                # keep the lash attached and inextensible-ish
                tip = pos0 + dr0 * self.handle
                v = co - tip
                if v.length > 1e-6:
                    v = v.normalized() * (d - self.handle)
                co = tip + v
                speed = (grip_fn(t + 0.02)[0] + grip_fn(t + 0.02)[1] * 0.6 - pos0 - dr0 * 0.6).length / 0.02
                co.z -= gravity * u * u * self.length * max(0.0, 1 - speed / 2.5)
            p.co = (*co, 1)


def cage():
    w = mat('wood', c=(0.22, 0.15, 0.09)); me = mat('metal', c=(0.12, 0.12, 0.12), rough=0.5)
    parts = [box((0.34, 0.22, 0.015), (0, 0, 0.0), w), box((0.34, 0.22, 0.015), (0, 0, 0.2), w)]
    for i in range(9):
        x = -0.16 + i * 0.04
        for y in (-0.105, 0.105):
            parts.append(cyl(0.0022, 0.2, (x, y, 0.1), me, seg=5))
    for j in range(5):
        y = -0.1 + j * 0.05
        for x in (-0.165, 0.165):
            parts.append(cyl(0.0022, 0.2, (x, y, 0.1), me, seg=5))
    parts.append(cyl(0.004, 0.1, (0, 0, 0.25), me, rot=(0, math.pi / 2, 0), seg=6))
    return join(parts, 'cage')


def pole(length=1.9):
    return cyl(0.014, length, (0, 0, 0), mat('wood', c=(0.25, 0.17, 0.1)), seg=8, name='pole')


def book(color=(0.3, 0.05, 0.05)):
    return join([box((0.2, 0.28, 0.045), (0, 0, 0), mat('plain', c=color, rough=0.5)), box((0.19, 0.27, 0.035), (0.006, 0, 0), mat('plain', c=(0.85, 0.8, 0.68), rough=0.8))], 'book')


def clods(n=7, seed=0):
    r = random.Random(seed)
    return [sphere(r.uniform(0.025, 0.06), (0, 0, -50), mat('dirt', c=(0.16, 0.11, 0.07)), seg=6, noise=0.015, seed=i) for i in range(n)]
