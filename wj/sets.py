"""Sets: Victorian street, tannery yard, pond, sewer, graveyard, plague lane + pit, palace hall."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise as mn
from .world import mat, obj, box, cyl, sphere, grid, join, light
from . import props, stage

BRICKS = [dict(c1=(0.33, 0.13, 0.08), c2=(0.22, 0.09, 0.06)), dict(c1=(0.4, 0.28, 0.16), c2=(0.3, 0.2, 0.12)),
          dict(c1=(0.25, 0.11, 0.09), c2=(0.16, 0.08, 0.07))]


def _roof(w, d, h, loc, material, rot=0.0):
    bm = bmesh.new()
    x, y = w / 2, d / 2
    v = [bm.verts.new(c) for c in ((-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (-x, 0, h), (x, 0, h))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)):
        bm.faces.new([v[i] for i in f])
    o = obj('roof', bm, material)
    o.location = loc; o.rotation_euler = (0, 0, rot)
    return o


def house(yc, w, floors, side, xface, style, r, depth=7.0):
    """Facade plane at x = xface, facing the road (toward x=0). side = -1 (west) or +1 (east)."""
    parts = []
    fh = 3.0 if style == 'victorian' else 2.6
    h = floors * fh
    inward = -side
    xc = xface + side * depth / 2
    if style == 'victorian':
        wall = mat('brick', **r.choice(BRICKS)); trim = mat('stone', c=(0.62, 0.58, 0.5)); frame = mat('plain', c=r.choice([(0.75, 0.73, 0.68), (0.12, 0.2, 0.14), (0.1, 0.1, 0.12)]), rough=0.5)
        roofm = mat('stone', c=(0.13, 0.14, 0.16), bscale=12)
    else:
        wall = mat('plaster', c=r.choice([(0.74, 0.68, 0.55), (0.68, 0.6, 0.46), (0.78, 0.74, 0.64)])); trim = mat('wood', c=(0.1, 0.065, 0.04)); frame = trim
        roofm = mat('cloth', c=(0.33, 0.27, 0.14), scale=3) if r.random() < 0.5 else mat('stone', c=(0.3, 0.16, 0.1), bscale=10)
    parts.append(box((depth, w, h), (xc, yc, h / 2), wall))
    parts.append(_roof(w + 0.3, depth + 0.6, 2.2 if style == 'victorian' else 3.0, (xc, yc, h), roofm, rot=math.pi / 2))
    parts.append(box((0.6, 0.6, 1.6), (xc + side * 1.0, yc + r.uniform(-w / 3, w / 3), h + 1.6), wall))
    glass = mat('glass')
    nwin = max(2, int(w // 1.7))
    door_i = r.randrange(nwin)
    for fl in range(floors):
        jet = 0.0
        if style != 'victorian' and fl >= 1:
            jet = 0.35
            parts.append(box((jet, w, fh), (xface + inward * jet / 2, yc, fl * fh + fh / 2), wall))
            parts.append(box((jet + 0.1, w + 0.1, 0.18), (xface + inward * jet / 2, yc, fl * fh), trim))
        xf = xface + inward * jet
        for i in range(nwin):
            y = yc - w / 2 + w * (i + 0.5) / nwin
            if fl == 0 and i == door_i:
                parts.append(box((0.12, 1.0, 2.1), (xf, y, 1.05), mat('wood', c=r.choice([(0.1, 0.16, 0.12), (0.2, 0.1, 0.06), (0.08, 0.08, 0.1)]), rough=0.5)))
                parts.append(box((0.5, 1.3, 0.16), (xf + inward * 0.2, y, 0.08), mat('stone')))
                parts.append(box((0.2, 1.3, 0.16), (xf + inward * 0.02, y, 2.2), trim))
                parts.append(sphere(0.03, (xf + inward * 0.09, y + 0.35, 1.05), mat('metal', c=(0.7, 0.5, 0.2), rough=0.3), seg=8))
                continue
            wz = fl * fh + (1.75 if style == 'victorian' else 1.5); wh = 1.5 if style == 'victorian' else 1.0; ww = 0.95
            parts.append(box((0.06, ww, wh), (xf + inward * 0.005, y, wz), glass))
            for dy in (-ww / 2, 0, ww / 2):
                parts.append(box((0.1, 0.06, wh + 0.06), (xf + inward * 0.02, y + dy, wz), frame))
            for dz in (-wh / 2, 0, wh / 2):
                parts.append(box((0.1, ww + 0.06, 0.06), (xf + inward * 0.02, y, wz + dz), frame))
            parts.append(box((0.22, ww + 0.25, 0.08), (xf + inward * 0.05, y, wz - wh / 2 - 0.06), trim))
            if style == 'victorian':
                parts.append(box((0.14, ww + 0.25, 0.2), (xf + inward * 0.02, y, wz + wh / 2 + 0.12), trim))
        if style != 'victorian':
            for i in range(nwin + 1):
                y = yc - w / 2 + w * i / nwin
                parts.append(box((0.06, 0.16, fh), (xf + inward * 0.02, y, fl * fh + fh / 2), trim))
            parts.append(box((0.06, w, 0.16), (xf + inward * 0.02, yc, fl * fh + fh - 0.08), trim))
            if fl >= 1:
                for i in range(nwin):
                    y = yc - w / 2 + w * (i + 0.5) / nwin
                    parts.append(box((0.05, 0.12, 1.0), (xf + inward * 0.02, y + 0.33 * (1 if i % 2 else -1), fl * fh + 0.5), trim, rot=(0.6 if i % 2 else -0.6, 0, 0)))
    if style == 'victorian':
        parts.append(box((0.16, w, 0.25), (xface + inward * 0.04, yc, h - 0.15), trim))
        parts.append(box((0.1, w, 0.12), (xface + inward * 0.03, yc, fh), trim))
    return parts


def lamp_post(loc):
    me = mat('metal', c=(0.05, 0.06, 0.05), rough=0.5)
    parts = [cyl(0.07, 0.5, (0, 0, 0.25), me, r2=0.045), cyl(0.035, 2.6, (0, 0, 1.8), me), box((0.5, 0.03, 0.03), (0, 0, 2.85), me),
             cyl(0.14, 0.34, (0, 0, 3.3), mat('clear'), r2=0.2, seg=6), cyl(0.22, 0.12, (0, 0, 3.53), me, r2=0.03, seg=6)]
    o = join(parts, 'lamp'); o.location = loc
    return o


def street(style='victorian', length=80.0, width=7.0, seed=1, market=False):
    """Road runs along Y, centred on x=0. Returns dict with useful dims."""
    r = random.Random(seed)
    pav = 2.2 if style == 'victorian' else 0.0
    if style == 'victorian':
        box((width, length, 0.2), (0, 0, -0.1), mat('cobble'), name='road')
        for s in (-1, 1):
            box((pav, length, 0.3), (s * (width / 2 + pav / 2), 0, -0.01), mat('blocks', c=(0.4, 0.38, 0.35)), name='pavement')
    else:
        grid(width + 1, length, 30, 160, lambda x, y: 0.05 * mn.noise(Vector((x * 0.8, y * 0.8, 0))) - 0.04 * math.exp(-(x * 0.9) ** 2),
             mat('dirt', c=(0.24, 0.18, 0.12), bscale=18, bump=1.0), name='road')
        box((0.5, length, 0.02), (0.1, 0, -0.035), mat('water', c=(0.08, 0.07, 0.05), trans=0.2, bump=0.03), name='gutter')
    parts = []
    xface = width / 2 + pav
    for side in (-1, 1):
        y = -length / 2
        while y < length / 2:
            w = r.uniform(4.6, 7.0)
            floors = r.choice([2, 3, 3] if style == 'victorian' else [2, 2, 3])
            parts += house(y + w / 2, w, floors, side, side * (xface + (r.uniform(-.15, .15) if style != 'victorian' else 0)), style, r)
            y += w + (0 if r.random() < 0.85 else 1.6)
    # closing buildings at both ends so the street reads as a real place, not a strip
    for e in (-1, 1):
        for k, xx in enumerate((-6, 0, 6)):
            hp = house(xx, 6.0, 3, 1, 0, style, r)
            hh = join(hp, 'endhouse'); hh.rotation_euler = (0, 0, math.pi / 2 * e)
            hh.location = (0, e * (length / 2 + 0.2), 0)
    join(parts, 'houses')
    # the rest of the city: ground to the horizon and a skyline of roofs behind the street
    box((1200, 1200, 0.1), (0, 0, -0.3), mat('stone', c=(0.22, 0.2, 0.18)), name='city_ground')
    sky_parts = []
    for i in range(90):
        a = r.uniform(0, 6.283); d = r.uniform(26, 160)
        x, y = math.cos(a) * d, math.sin(a) * d * 1.6
        if abs(x) < xface + 9:
            continue
        w = r.uniform(6, 14); h = r.uniform(7, 15)
        wm = mat('brick', **r.choice(BRICKS)) if style == 'victorian' else mat('plaster', c=(0.7, 0.63, 0.5))
        sky_parts.append(box((w, r.uniform(8, 20), h), (x, y, h / 2), wm))
        sky_parts.append(_roof(w + 0.4, 9, 2.5, (x, y, h), mat('stone', c=(0.14, 0.14, 0.16)), rot=r.choice([0, math.pi / 2])))
        if r.random() < 0.3:
            sky_parts.append(cyl(0.6, h + 9, (x + 2, y + 2, (h + 9) / 2), mat('brick', **BRICKS[2]), r2=0.4, seg=10))
    join(sky_parts, 'skyline')
    if style == 'victorian':
        for i, y in enumerate(range(int(-length / 2) + 6, int(length / 2), 14)):
            lamp_post(((xface - 0.4) * (1 if i % 2 else -1), y, 0.14))
    # dressing
    for i in range(10):
        s = r.choice((-1, 1)); y = r.uniform(-length / 2 + 3, length / 2 - 3)
        if r.random() < 0.5:
            b = props.barrel(); b.location = (s * (xface - 0.5), y, 0.14 if pav else 0)
        else:
            sz = r.uniform(0.45, 0.7)
            box((sz, sz, sz), (s * (xface - 0.5), y, sz / 2 + (0.14 if pav else 0)), mat('wood', c=(0.3, 0.22, 0.13)), rot=(0, 0, r.uniform(0, 1)))
    if market:
        for i, (s, y) in enumerate(((-1, 4.5), (1, 7.5), (-1, 11), (1, 2.5))):
            stall((s * (width / 2 - 1.2), y, 0), s, [(0.55, 0.12, 0.1), (0.15, 0.25, 0.4), (0.6, 0.5, 0.2), (0.2, 0.35, 0.2)][i], r)
    return dict(xface=xface, width=width, pav=pav)


def stall(loc, side, color, r):
    w = mat('wood', c=(0.25, 0.17, 0.1))
    parts = [box((1.0, 2.2, 0.06), (0, 0, 0.9), w)]
    for sx in (-0.45, 0.45):
        for sy in (-1.05, 1.05):
            parts.append(box((0.06, 0.06, 2.3 if sx * side > 0 else 2.0), (sx, sy, 1.15 if sx * side > 0 else 1.0), w))
    aw = box((1.5, 2.5, 0.03), (-side * 0.1, 0, 2.2), mat('cloth', c=color, scale=4), rot=(0, side * 0.22, 0))
    parts.append(aw)
    for i in range(7):
        c = r.choice([(0.6, 0.1, 0.05), (0.7, 0.5, 0.1), (0.3, 0.45, 0.1), (0.5, 0.3, 0.15)])
        parts.append(sphere(r.uniform(0.05, 0.09), (r.uniform(-.35, .35), r.uniform(-.9, .9), 0.99), mat('plain', c=c, rough=0.4), seg=10))
    parts.append(sphere(0.3, (0.1, -1.5, 0.25), mat('cloth', c=(0.45, 0.38, 0.25), scale=12), scale=(1, 1, 0.85), seg=12, noise=0.04))
    o = join(parts, 'stall'); o.location = loc
    return o


def tannery(origin=(0, 0, 0)):
    """Open yard: brick wall, vats, hides drying on racks, lean-to shed."""
    ox, oy, oz = origin
    box((24, 24, 0.2), (ox, oy, -0.1), mat('dirt', c=(0.27, 0.21, 0.15), bscale=14, bump=0.9))
    box((24, 0.4, 3.2), (ox, oy + 7, 1.6), mat('brick', **BRICKS[0]))
    box((0.4, 24, 3.2), (ox - 8, oy, 1.6), mat('brick', **BRICKS[2]))
    box((0.4, 24, 3.2), (ox + 8, oy, 1.6), mat('brick', **BRICKS[1]))
    for x in (-3.4, 0.2, 3.8):
        h = props.hide_rack(); h.location = (ox + x, oy + 4.6, 0); h.rotation_euler = (0, 0, 0.05 * x)
    for i, (x, y) in enumerate(((-3.2, 1.6), (-4.8, -0.6), (4.4, 1.0))):
        cyl(0.8, 0.75, (ox + x, oy + y, 0.375), mat('wood', c=(0.2, 0.14, 0.09)), seg=20)
        cyl(0.74, 0.02, (ox + x, oy + y, 0.7), mat('water', c=[(0.2, 0.12, 0.05), (0.3, 0.3, 0.25), (0.14, 0.09, 0.04)][i], trans=0.1, rough=0.12), seg=20)
    # shed
    w = mat('wood', c=(0.2, 0.14, 0.09))
    for x in (4.2, 7.4):
        for y in (4.0, 6.6):
            box((0.12, 0.12, 2.6), (ox + x, oy + y, 1.3), w)
    box((3.8, 3.2, 0.08), (ox + 5.8, oy + 5.3, 2.65), w, rot=(0.12, 0, 0))
    box((1.6, 0.8, 0.85), (ox + 5.6, oy + 5.6, 0.425), w)
    for i in range(3):
        b = props.barrel(); b.location = (ox - 6.6 + i * 0.75, oy + 6.0, 0)
    # town roofs beyond the wall for depth
    r = random.Random(9)
    parts = []
    for i in range(7):
        parts += house(-18 + i * 6.2, 6.0, r.choice([2, 3]), 1, 0, 'victorian', r)
    hh = join(parts, 'bg_houses'); hh.rotation_euler = (0, 0, -math.pi / 2); hh.location = (ox, oy + 10.5, 0)


def tree(loc, h=6.0, seed=0, leaf=(0.07, 0.16, 0.03), bare=False):
    r = random.Random(seed)
    bark = mat('wood', c=(0.12, 0.09, 0.06), grain=(6, 6, 1))
    parts = [cyl(h * 0.045, h * 0.6, (0, 0, h * 0.3), bark, r2=h * 0.025, seg=10)]
    for i in range(7 if bare else 4):
        a = r.uniform(0, 6.28); tilt = r.uniform(0.5, 1.0); L = h * r.uniform(0.3, 0.45)
        b = cyl(h * 0.018, L, (0, 0, 0), bark, r2=h * 0.006, seg=6)
        b.rotation_euler = (0, tilt, a)
        d = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)))
        b.location = Vector((0, 0, h * r.uniform(0.45, 0.6))) + d * L / 2
        parts.append(b)
        if bare:
            for k in range(2):
                a2 = a + r.uniform(-1, 1); t2 = tilt + r.uniform(-.5, .3); L2 = L * 0.6
                d2 = Vector((math.sin(t2) * math.cos(a2), math.sin(t2) * math.sin(a2), math.cos(t2)))
                b2 = cyl(h * 0.007, L2, b.location + d * L / 2 * r.uniform(0.3, 1) + d2 * L2 / 2, bark, r2=h * 0.002, seg=5); b2.rotation_euler = (0, t2, a2)
                parts.append(b2)
    if not bare:
        lm = mat('leaf', c=leaf)
        for i in range(6):
            a = r.uniform(0, 6.28); rr = r.uniform(0, h * 0.22)
            parts.append(sphere(h * r.uniform(0.18, 0.27), (math.cos(a) * rr, math.sin(a) * rr, h * r.uniform(0.62, 0.9)), lm, scale=(1, 1, 0.8), seg=14, noise=h * 0.07, seed=seed * 10 + i))
    o = join(parts, 'tree'); o.location = loc; o.rotation_euler = (0, 0, r.uniform(0, 6))
    return o


def grass_patch(ground, count=40000, length=0.14, seed=1, color=(0.1, 0.2, 0.04)):
    ps = ground.modifiers.new('grass', 'PARTICLE_SYSTEM').particle_system
    st = ps.settings
    st.type = 'HAIR'; st.count = count; st.hair_length = length; st.hair_step = 2
    st.length_random = 0.6; st.factor_random = 0.008; st.brownian_factor = 0.004
    st.root_radius = 1.0; st.tip_radius = 0.1; st.radius_scale = 0.006
    ground.data.materials.append(mat('plain', c=color, rough=0.5))
    st.material = len(ground.data.materials)
    ps.seed = seed
    return ps


def pond():
    """Sunlit countryside pond; shallow shore at y≈-5.5 where the action happens."""
    def hf(x, y):
        rr = math.hypot(x, y * 0.85)
        bowl = -1.1 * max(0.0, 1 - (rr / 7.5) ** 2)
        hills = 0.5 * mn.noise(Vector((x * 0.05, y * 0.05, 0))) * min(1, max(0, (rr - 8) / 10)) + 0.03 * mn.noise(Vector((x * .6, y * .6, 3)))
        return bowl + hills + min(0.25, max(0, rr - 7.5) * 0.06)
    g = grid(160, 160, 160, 160, hf, mat('grass'), name='land')
    # mud bed
    grid(18, 22, 60, 60, lambda x, y: hf(x, y) + 0.01 if math.hypot(x, y * .85) < 7.6 else -5, mat('mud'), name='bed')
    water = cyl(8.2, 0.02, (0, 0, -0.28), mat('water', c=(0.06, 0.1, 0.07), trans=0.65, bump=0.1, scale=4), seg=48, name='water')
    near = grid(14, 9, 50, 40, lambda x, y: hf(x, y) + 0.005, mat('grass'), loc=(0, -10.5, 0), name='near_grass')
    grass_patch(near, 60000, 0.16)
    r = random.Random(5)
    reeds = []
    rm = mat('plain', c=(0.2, 0.3, 0.08), rough=0.5)
    for i in range(150):
        a = r.uniform(0, 6.28)
        if -2.2 < a - 4.71 < -0.9 or 0.9 < a - 4.71 < 2.2 or r.random() < 0.25:
            rr = r.uniform(6.3, 7.6)
            x, y = math.cos(a) * rr, math.sin(a) * rr / 0.85
            if abs(x) < 2.2 and y < 0:
                continue
            hgt = r.uniform(0.7, 1.6)
            c = cyl(0.012, hgt, (x, y, hf(x, y) + hgt / 2 - 0.05), rm, r2=0.002, seg=4, smooth=False)
            c.rotation_euler = (r.uniform(-.15, .15), r.uniform(-.15, .15), 0)
            reeds.append(c)
            if r.random() < 0.3:
                reeds.append(cyl(0.022, 0.16, (x, y, hf(x, y) + hgt - 0.1), mat('plain', c=(0.16, 0.09, 0.04), rough=0.8), seg=6))
    join(reeds, 'reeds')
    for i in range(46):
        a = r.uniform(0, 6.28); rr = r.uniform(17, 70)
        x, y = math.cos(a) * rr, math.sin(a) * rr
        if y < -8 and abs(x) < 9:
            continue
        tree((x, y, hf(x, y) - 0.1), r.uniform(6, 11), seed=i, leaf=r.choice([(0.07, 0.16, 0.03), (0.1, 0.18, 0.04), (0.05, 0.12, 0.03)]))
    # lily pads
    pads = [cyl(r.uniform(0.1, 0.18), 0.004, (r.uniform(-5, 5), r.uniform(-1, 5), -0.265), mat('plain', c=(0.08, 0.2, 0.05), rough=0.3), seg=12) for _ in range(40)]
    join(pads, 'lilies')
    # cottage
    rr = random.Random(2)
    hh = join(house(0, 8, 2, 1, 0, 'medieval', rr), 'cottage'); hh.location = (-22, 26, hf(-22, 26)); hh.rotation_euler = (0, 0, 0.9)
    return dict(hf=hf, water=water)


def sewer(length=44.0):
    """Brick barrel-vault sewer along Y. Channel water surface z=0.32; ledges at |x|>1.25."""
    br = mat('brick', c1=(0.3, 0.17, 0.11), c2=(0.2, 0.12, 0.09))
    bm = bmesh.new()
    R = 2.05; seg = 28; ny = 2
    rings = []
    for j in (0, 1):
        y = -length / 2 + j * length
        rings.append([bm.verts.new((math.cos(math.pi * i / seg) * R, y, 0.9 + math.sin(math.pi * i / seg) * R * 1.02)) for i in range(seg + 1)])
    for i in range(seg):
        bm.faces.new((rings[0][i], rings[1][i], rings[1][i + 1], rings[0][i + 1]))
    obj('vault', bm, br, smooth=True)
    for s in (-1, 1):
        box((0.2, length, 1.0), (s * (R + 0.08), 0, 0.45), br)
        box((0.8, length, 0.5), (s * 1.65, 0, 0.25), mat('blocks', c=(0.3, 0.29, 0.26)), name='ledge')
    box((2.6, length, 0.2), (0, 0, -0.2), mat('mud'), name='bed')
    water = box((2.5, length, 0.02), (0, 0, 0.3), mat('water', c=(0.07, 0.075, 0.04), trans=0.25, rough=0.08, bump=0.2, scale=3), name='water')
    box((6, 0.5, 6), (0, length / 2, 2), mat('plain', c=(0.0, 0.0, 0.0), rough=1))
    box((6, 0.5, 6), (0, -length / 2, 2), mat('plain', c=(0.0, 0.0, 0.0), rough=1))
    # daylight shafts through street grates
    for y in (7.0, -9.0, 20.0):
        light('SPOT', (0.3, y, 3.6), 9000, (1.0, 0.95, 0.85), size=0.05, rot=(0, 0, 0), spot=math.radians(26))
        for k in range(-3, 4):
            box((0.03, 0.7, 0.03), (0.3 + k * 0.1, y, 3.25), mat('metal', c=(0.03, 0.03, 0.03)))
    # soft cool fill so the brickwork stays readable
    for y in range(-18, 20, 6):
        light('POINT', (0, y, 2.4), 170, (0.62, 0.74, 1.0), size=1.0)
    r = random.Random(4)
    junk = []
    for i in range(30):
        junk.append(sphere(r.uniform(0.04, 0.12), (r.uniform(-1.1, 1.1), r.uniform(-12, 12), 0.27), mat('mud'), scale=(1.5, 1.2, 0.5), seg=8, noise=0.02, seed=i))
    join(junk, 'sludge')
    return dict(water=water)


def headstone(loc, r, cross=False, lean=None):
    st = mat('stone', c=r.choice([(0.38, 0.38, 0.36), (0.3, 0.31, 0.29), (0.45, 0.43, 0.39)]), bscale=14)
    if cross:
        parts = [box((0.14, 0.1, 1.2), (0, 0, 0.6), st), box((0.6, 0.1, 0.14), (0, 0, 0.9), st), box((0.4, 0.3, 0.14), (0, 0, 0.07), st)]
    else:
        h = r.uniform(0.6, 1.0); w = r.uniform(0.45, 0.6)
        parts = [box((w, 0.1, h), (0, 0, h / 2), st), cyl(w / 2, 0.1, (0, 0, h), st, rot=(math.pi / 2, 0, 0), seg=16)]
    o = join(parts, 'stone'); o.location = loc
    o.rotation_euler = (r.uniform(-.08, .08), r.uniform(-.1, .1), r.uniform(-.15, .15)) if lean is None else lean
    return o


def church(loc, rot=0.0):
    st = mat('blocks', c=(0.36, 0.35, 0.33)); roofm = mat('stone', c=(0.1, 0.11, 0.13))
    glow = mat('emit', c=(1.0, 0.7, 0.35), e=2.5)
    parts = [box((9, 18, 7), (0, 0, 3.5), st), _roof(9.4, 18.4, 4, (0, 0, 7), roofm, rot=math.pi / 2), box((5, 5, 15), (0, -11, 7.5), st),
             cyl(3.6, 9, (0, -11, 19.5), roofm, r2=0.05, seg=4)]
    parts[-1].rotation_euler = (0, 0, math.pi / 4)
    for y in (-5, -1, 3, 7):
        for s in (-1, 1):
            parts.append(box((0.1, 1.1, 3.2), (s * 4.52, y, 3.6), glow))
    parts.append(box((1.2, 0.1, 3.0), (0, -13.52, 9), glow))
    o = join(parts, 'church'); o.location = loc; o.rotation_euler = (0, 0, rot)
    return o


def mortsafe(loc):
    """Iron cage bolted over a fresh grave."""
    me = mat('metal', c=(0.05, 0.05, 0.055), rough=0.55)
    parts = [box((1.0, 2.1, 0.12), (0, 0, 0.06), mat('stone', c=(0.3, 0.3, 0.28)))]
    for x in (-0.48, -0.24, 0, 0.24, 0.48):
        parts.append(cyl(0.014, 2.1, (x, 0, 0.72), me, rot=(math.pi / 2, 0, 0), seg=8))
        for y in (-1.03, 1.03):
            parts.append(cyl(0.014, 0.66, (x, y, 0.4), me, seg=8))
    for y in [-1.03 + i * 2.06 / 8 for i in range(9)]:
        parts.append(cyl(0.014, 0.98, (0, y, 0.72), me, rot=(0, math.pi / 2, 0), seg=8))
        for x in (-0.48, 0.48):
            parts.append(cyl(0.014, 0.66, (x, y, 0.4), me, seg=8))
    for z in (0.14, 0.42):
        for x in (-0.48, 0.48):
            parts.append(box((0.03, 2.1, 0.03), (x, 0, z), me))
        for y in (-1.03, 1.03):
            parts.append(box((0.98, 0.03, 0.03), (0, y, z), me))
    o = join(parts, 'mortsafe'); o.location = loc
    return o


def fence(x0, x1, y, h=1.5):
    me = mat('metal', c=(0.04, 0.04, 0.045), rough=0.6)
    parts = [box((x1 - x0, 0.03, 0.04), ((x0 + x1) / 2, y, h * 0.9), me), box((x1 - x0, 0.03, 0.04), ((x0 + x1) / 2, y, 0.25), me)]
    x = x0
    while x <= x1:
        parts.append(cyl(0.012, h, (x, y, h / 2), me, seg=6, r2=0.012))
        parts.append(cyl(0.022, 0.1, (x, y, h + 0.05), me, seg=6, r2=0.001))
        x += 0.18
    return join(parts, 'fence')


def graveyard(grave=True):
    """Open grave at the origin (long axis Y, 0.95 x 2.1 m, 1.3 m deep)."""
    def hf(x, y):
        return 0.12 * mn.noise(Vector((x * 0.12, y * 0.12, 1))) + 0.02 * mn.noise(Vector((x * 0.9, y * 0.9, 4)))
    hole = (-0.5, 0.5, -1.1, 1.1) if grave else None
    g = grid(90, 90, 300, 300, (lambda x, y: hf(x, y) if not (grave and abs(x) < 0.9 and abs(y) < 1.5) else 0.0), mat('grass'), name='land', hole=hole)
    near = grid(12, 12, 40, 40, lambda x, y: hf(x, y) + 0.004 if not (abs(x) < 2.3 and abs(y) < 2.6) else -0.02, mat('grass'), name='near', hole=hole)
    grass_patch(near, 50000, 0.12, color=(0.07, 0.15, 0.04))
    if grave:
        d = mat('dirt', c=(0.16, 0.11, 0.07), bscale=25, bump=1.0)
        for (sz, lc) in (((0.06, 2.5, 1.3), (-0.63, 0, -0.65)), ((0.06, 2.5, 1.3), (0.63, 0, -0.65)), ((1.3, 0.06, 1.3), (0, -1.23, -0.65)), ((1.3, 0.06, 1.3), (0, 1.23, -0.65)),
                         ((1.3, 2.5, 0.06), (0, 0, -1.3))):
            box(sz, lc, d)
        sphere(0.75, (1.45, 0.2, -0.1), d, scale=(1.0, 1.5, 0.7), seg=20, noise=0.12, seed=3, name='mound')
        sphere(0.5, (-1.25, -0.9, -0.12), d, scale=(1.0, 1.2, 0.55), seg=16, noise=0.1, seed=5, name='mound2')
        # coffin lid edge visible in the pit
        box((0.62, 1.9, 0.1), (0, 0, -1.22), mat('wood', c=(0.16, 0.1, 0.06)))
    r = random.Random(11)
    for row in range(-3, 7):
        for k in range(-7, 8):
            x = k * 2.6 + r.uniform(-.4, .4); y = row * 4.2 + 2.3 + r.uniform(-.3, .3)
            if abs(x) < 2.6 and abs(y) < 3.2:
                continue
            if r.random() < 0.82:
                headstone((x, y, hf(x, y) - 0.03), r, cross=r.random() < 0.25)
    headstone((0, 1.75, 0), r, lean=(0.03, 0, 0.02))
    church((-13, 44, 0), rot=0.25)
    fence(-40, 40, 30)
    for i, (x, y) in enumerate(((-7.5, 9), (9, 15), (-18, 24), (16, 27), (5, -9), (-11, -6))):
        tree((x, y, 0), r.uniform(6, 9), seed=20 + i, bare=True)
    return dict(hf=hf)


def night_sky(scene, strength=0.05, exposure=0.6):
    w = bpy.data.worlds.new('night'); scene.world = w; w.use_nodes = True
    nt = w.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sp.inputs[0])
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (0.16, 0.24, 0.42, 1)
    rp.color_ramp.elements[1].position = 0.6; rp.color_ramp.elements[1].color = (0.015, 0.03, 0.09, 1)
    nt.links.new(sp.outputs['Z'], rp.inputs['Fac'])
    st = nt.nodes.new('ShaderNodeTexVoronoi'); st.inputs['Scale'].default_value = 260
    nt.links.new(tc.outputs['Generated'], st.inputs['Vector'])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.035
    nt.links.new(st.outputs['Distance'], lt.inputs[0])
    ad = nt.nodes.new('ShaderNodeMix'); ad.data_type = 'RGBA'; ad.blend_type = 'ADD'; ad.inputs['B'].default_value = (4, 4, 5, 1)
    nt.links.new(lt.outputs[0], ad.inputs['Factor']); nt.links.new(rp.outputs['Color'], ad.inputs['A'])
    bg = nt.nodes['Background']; nt.links.new(ad.outputs['Result'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength
    scene.view_settings.exposure = exposure
    moon = light('SUN', (0, 0, 30), 1.6, (0.62, 0.75, 1.0), size=math.radians(1.2), rot=(math.radians(52), 0, math.radians(150)))
    # visible moon disc
    sphere(9, (-120, 330, 190), mat('emit', c=(0.9, 0.93, 1.0), e=3.0), seg=24, name='moon')
    return moon


def pit_field():
    """Plague pit outside the town wall: pit 5 x 3.6 m centred at the origin."""
    def hf(x, y):
        return 0.15 * mn.noise(Vector((x * 0.1, y * 0.1, 2))) * min(1, max(0, (math.hypot(x, y) - 5) / 6)) + 0.02 * mn.noise(Vector((x, y, 5)))
    grid(120, 120, 240, 240, hf, mat('dirt', c=(0.25, 0.2, 0.13), bscale=10, bump=1.0), name='land', hole=(-2.5, 2.5, -1.8, 1.8))
    d = mat('dirt', c=(0.17, 0.12, 0.08), bscale=22, bump=1.0)
    for (sz, lc) in (((0.1, 3.8, 1.7), (-2.55, 0, -0.85)), ((0.1, 3.8, 1.7), (2.55, 0, -0.85)), ((5.2, 0.1, 1.7), (0, -1.85, -0.85)), ((5.2, 0.1, 1.7), (0, 1.85, -0.85))):
        box(sz, lc, d)
    grid(5.2, 3.8, 20, 16, lambda x, y: -1.55 + 0.08 * mn.noise(Vector((x * 2, y * 2, 1))), mat('plain', c=(0.75, 0.74, 0.7), rough=0.9), name='lime')
    for i, (x, y, a) in enumerate(((3.6, 2.6, 0.3), (-3.8, 2.4, 2.0), (-3.6, -2.9, 4.0))):
        sphere(1.1, (x, y, -0.2), d, scale=(1.3, 1.0, 0.6), seg=18, noise=0.18, seed=i)
    r = random.Random(8)
    for i in range(7):
        s = props.shroud(r.uniform(1.5, 1.8), seed=i, color=r.choice([(0.62, 0.58, 0.5), (0.5, 0.47, 0.4), (0.68, 0.65, 0.58)]))
        s.location = (r.uniform(-1.9, 1.2), r.uniform(-1.3, 0.3), -1.5 + (0.12 if i > 4 else 0)); s.rotation_euler = (r.uniform(-.1, .1), r.uniform(-.15, .15), r.uniform(0, 6.28))
    # town wall + roofs
    box((120, 1.2, 6), (0, 26, 3), mat('blocks', c=(0.42, 0.4, 0.36)))
    for x in range(-56, 60, 4):
        box((2, 1.3, 0.9), (x, 26, 6.4), mat('blocks', c=(0.42, 0.4, 0.36)))
    rr = random.Random(3)
    parts = []
    for i in range(12):
        parts += house(-36 + i * 6.4, 6.0, rr.choice([2, 3]), 1, 0, 'medieval', rr)
    hh = join(parts, 'town'); hh.rotation_euler = (0, 0, -math.pi / 2); hh.location = (0, 31, 0)
    church((24, 48, 0), rot=1.2)
    for i, (x, y) in enumerate(((-9, 9), (11, 13), (-15, -4), (14, -8), (-22, 16))):
        tree((x, y, 0), rr.uniform(6, 9), seed=40 + i, bare=i % 2 == 0, leaf=(0.12, 0.14, 0.04))
    return dict(hf=hf)


def palace():
    """Great hall: 14 (x) by 26 (y) by 9 m. Tall windows on the west wall (x=-7) throw sun across the floor."""
    W, L, H = 14.0, 26.0, 9.0
    m, nt, b = bpy.data.materials.new('marble'), None, None
    m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); ch = nt.nodes.new('ShaderNodeTexChecker'); ch.inputs['Scale'].default_value = 1.0
    ch.inputs['Color1'].default_value = (0.62, 0.58, 0.5, 1); ch.inputs['Color2'].default_value = (0.1, 0.09, 0.085, 1)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.9, 0.9, 0.9); mp.inputs['Rotation'].default_value = (0, 0, math.pi / 4)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], ch.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 10; nz.inputs['Distortion'].default_value = 2.5
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.5
    nt.links.new(ch.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.16
    box((W, L, 0.3), (0, 0, -0.15), m, name='floor')
    st = mat('blocks', c=(0.6, 0.55, 0.47))
    box((0.6, L, H), (W / 2 + 0.3, 0, H / 2), st); box((W + 1.2, 0.6, H), (0, L / 2 + 0.3, H / 2), st); box((W + 1.2, 0.6, H), (0, -L / 2 - 0.3, H / 2), st)
    # west wall with 5 tall window openings
    ys = [-9.6, -4.8, 0, 4.8, 9.6]; ww = 2.0; z0, z1 = 1.4, 7.4
    box((0.6, L, z0), (-W / 2 - 0.3, 0, z0 / 2), st); box((0.6, L, H - z1), (-W / 2 - 0.3, 0, (H + z1) / 2), st)
    edges = [-L / 2] + [e for y in ys for e in (y - ww / 2, y + ww / 2)] + [L / 2]
    for a, c in zip(edges[0::2], edges[1::2]):
        box((0.6, c - a, z1 - z0), (-W / 2 - 0.3, (a + c) / 2, (z0 + z1) / 2), st)
    lead = mat('metal', c=(0.05, 0.05, 0.05))
    for y in ys:
        for k in range(1, 4):
            box((0.05, 0.04, z1 - z0), (-W / 2 - 0.3, y - ww / 2 + ww * k / 4, (z0 + z1) / 2), lead)
        for k in range(1, 8):
            box((0.05, ww, 0.04), (-W / 2 - 0.3, y, z0 + (z1 - z0) * k / 8), lead)
        box((0.9, ww + 0.3, 0.14), (-W / 2 - 0.2, y, z0 - 0.07), mat('stone', c=(0.66, 0.62, 0.55)))
        # sun shaft
        c = box((0.02, ww * 0.95, 9.5), (-W / 2 + 3.2, y + 1.2, 3.6), mat('ray', e=0.02, c=(1, 0.9, 0.7)), rot=(0, math.radians(-52), math.radians(20)))
        c.visible_shadow = False; c.visible_diffuse = False; c.visible_glossy = False
    # ceiling + beams
    box((W + 1.2, L + 1.2, 0.3), (0, 0, H + 0.15), mat('wood', c=(0.16, 0.1, 0.06)))
    for y in range(-12, 13, 3):
        box((W, 0.4, 0.5), (0, y, H - 0.25), mat('wood', c=(0.12, 0.075, 0.045)))
    # columns on the east side, carpet, dais, throne
    for y in range(-10, 11, 5):
        cyl(0.42, H, (W / 2 - 1.4, y, H / 2), mat('stone', c=(0.7, 0.66, 0.58), bscale=8), seg=20)
        box((1.1, 1.1, 0.4), (W / 2 - 1.4, y, 0.2), mat('stone', c=(0.7, 0.66, 0.58)))
    box((2.6, L - 4, 0.02), (0, -1, 0.012), mat('cloth', c=(0.4, 0.035, 0.04), scale=3), name='carpet')
    box((7, 3.5, 0.3), (0, L / 2 - 1.75, 0.15), mat('stone', c=(0.5, 0.47, 0.42))); box((5, 2.5, 0.3), (0, L / 2 - 1.5, 0.45), mat('stone', c=(0.5, 0.47, 0.42)))
    gold = mat('metal', c=(0.9, 0.62, 0.2), rough=0.3); vel = mat('cloth', c=(0.35, 0.03, 0.05), scale=10)
    box((1.1, 0.9, 0.5), (0, L / 2 - 1.3, 0.85), gold, bevel=0.03); box((0.9, 0.7, 0.12), (0, L / 2 - 1.35, 1.16), vel, bevel=0.03)
    box((1.1, 0.16, 2.2), (0, L / 2 - 0.85, 1.7), gold, bevel=0.03); box((0.85, 0.06, 1.5), (0, L / 2 - 0.95, 1.95), vel)
    for sx in (-1, 1):
        box((0.14, 0.8, 0.3), (sx * 0.5, L / 2 - 1.3, 1.25), gold, bevel=0.02)
    # tapestries + banners on the east wall
    for i, y in enumerate((-7.5, -2.5, 2.5, 7.5)):
        box((0.04, 2.6, 4.2), (W / 2 - 0.03, y, 4.6), mat('cloth', c=[(0.4, 0.05, 0.05), (0.07, 0.12, 0.35), (0.35, 0.25, 0.06), (0.08, 0.25, 0.14)][i], scale=2.5))
        box((0.08, 2.9, 0.1), (W / 2 - 0.05, y, 6.75), gold)
    # schoolroom corner: desk, books, stool, globe
    w = mat('wood', c=(0.2, 0.11, 0.06), rough=0.4)
    box((1.6, 0.8, 0.06), (2.6, -3.0, 0.78), w)
    for sx in (-0.7, 0.7):
        for sy in (-0.32, 0.32):
            box((0.07, 0.07, 0.76), (2.6 + sx, -3.0 + sy, 0.38), w)
    r = random.Random(6)
    for i in range(5):
        box((0.2, 0.28, 0.045), (2.2 + r.uniform(-.05, .05), -3.05, 0.83 + i * 0.047), mat('plain', c=r.choice([(0.3, 0.05, 0.05), (0.06, 0.12, 0.25), (0.1, 0.2, 0.1), (0.25, 0.17, 0.08)]), rough=0.5), rot=(0, 0, r.uniform(-.3, .3)))
    box((0.32, 0.42, 0.012), (2.9, -3.0, 0.817), mat('plain', c=(0.85, 0.8, 0.68), rough=0.8), rot=(0, 0, 0.2))
    # warm bounce so faces never go muddy
    light('AREA', (1, -2, 8.2), 2500, (1.0, 0.9, 0.78), size=10, rot=(0, 0, 0))
    return dict(W=W, L=L, H=H)
