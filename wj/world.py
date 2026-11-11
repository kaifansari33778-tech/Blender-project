"""Procedural materials, props and sets (all geometry is generated; no external models)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

_m = {}


def _new(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']


def _coord(nt, scale=1.0, wall=False):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    out = tc.outputs['Object']
    if wall:   # map (x+y, z) so brick courses run horizontally on any vertical wall
        sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(out, sp.inputs[0])
        ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'
        nt.links.new(sp.outputs['X'], ad.inputs[0]); nt.links.new(sp.outputs['Y'], ad.inputs[1])
        cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(ad.outputs[0], cb.inputs['X']); nt.links.new(sp.outputs['Z'], cb.inputs['Y'])
        out = cb.outputs[0]
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(out, mp.inputs['Vector'])
    return mp.outputs['Vector']


def _bump(nt, b, height, strength=0.5, dist=0.02):
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
    nt.links.new(height, bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])


def _ramp(nt, fac, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
    el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p, c in stops[1:-1]:
        e = el.new(p); e.color = (*c, 1)
    nt.links.new(fac, r.inputs['Fac'])
    return r.outputs['Color']


def _noise(nt, vec, scale, detail=6, rough=0.55):
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def mat(kind, **kw):
    key = kind + repr(sorted(kw.items()))
    if key in _m:
        return _m[key]
    m, nt, b = _new(kind)
    if kind == 'brick':
        v = _coord(nt, 1.0, wall=True)
        br = nt.nodes.new('ShaderNodeTexBrick')
        c1 = kw.get('c1', (0.33, 0.13, 0.08)); c2 = kw.get('c2', (0.22, 0.09, 0.06))
        br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1)
        br.inputs['Mortar'].default_value = (0.42, 0.39, 0.34, 1)
        br.inputs['Scale'].default_value = 4.4; br.inputs['Mortar Size'].default_value = 0.012
        br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 0.34
        nt.links.new(v, br.inputs['Vector'])
        grime = _noise(nt, _coord(nt, 0.6), 1.5)
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.75
        nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(_ramp(nt, grime, [(0.3, (0.35, 0.33, 0.3)), (0.7, (1, 1, 1))]), mx.inputs['B'])
        nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.9
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
        nt.links.new(br.outputs['Fac'], inv.inputs[1])
        _bump(nt, b, inv.outputs[0], 0.8, 0.02)
    elif kind == 'cobble':
        v = _coord(nt, kw.get('scale', 5.5))
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'F1'; vo.inputs['Randomness'].default_value = 0.75
        nt.links.new(v, vo.inputs['Vector'])
        ed = nt.nodes.new('ShaderNodeTexVoronoi'); ed.feature = 'DISTANCE_TO_EDGE'; ed.inputs['Randomness'].default_value = 0.75
        nt.links.new(v, ed.inputs['Vector'])
        h = _ramp(nt, ed.outputs['Distance'], [(0.0, (0, 0, 0)), (0.12, (0.8, 0.8, 0.8)), (0.5, (1, 1, 1))])
        base = kw.get('c', (0.2, 0.19, 0.18))
        hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.inputs['Color'].default_value = (*base, 1)
        sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(vo.outputs['Color'], sp.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 1.35
        nt.links.new(sp.outputs[0], mr.inputs['Value']); nt.links.new(mr.outputs[0], hsv.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
        nt.links.new(hsv.outputs['Color'], mx.inputs['A']); nt.links.new(_ramp(nt, ed.outputs['Distance'], [(0.0, (0.25, 0.22, 0.18)), (0.1, (1, 1, 1))]), mx.inputs['B'])
        nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
        wet = _noise(nt, _coord(nt, 0.35), 1.0)
        nt.links.new(_ramp(nt, wet, [(0.35, (kw.get('wet', 0.25),) * 3), (0.65, (0.75,) * 3)]), b.inputs['Roughness'])
        _bump(nt, b, h, 1.0, 0.03)
    elif kind in ('plaster', 'stone', 'dirt', 'mud', 'sand'):
        c = kw.get('c', dict(plaster=(0.72, 0.66, 0.54), stone=(0.42, 0.4, 0.37), dirt=(0.2, 0.14, 0.09), mud=(0.1, 0.075, 0.05), sand=(0.5, 0.42, 0.3))[kind])
        n = _noise(nt, _coord(nt, 1), kw.get('scale', 2.5), 8, 0.65)
        d = tuple(x * 0.55 for x in c)
        nt.links.new(_ramp(nt, n, [(0.3, d), (0.7, c)]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = dict(mud=0.35).get(kind, 0.9)
        n2 = _noise(nt, _coord(nt, 1), kw.get('bscale', 30), 6, 0.7)
        _bump(nt, b, n2, kw.get('bump', 0.5), 0.02)
    elif kind == 'blocks':   # dressed stone blocks
        v = _coord(nt, 1.0, wall=True)
        br = nt.nodes.new('ShaderNodeTexBrick')
        c = kw.get('c', (0.5, 0.47, 0.42))
        br.inputs['Color1'].default_value = (*c, 1); br.inputs['Color2'].default_value = (*(x * 0.8 for x in c), 1)
        br.inputs['Mortar'].default_value = (*(x * 0.5 for x in c), 1)
        br.inputs['Scale'].default_value = 1.6; br.inputs['Mortar Size'].default_value = 0.008
        nt.links.new(v, br.inputs['Vector'])
        n = _noise(nt, _coord(nt, 1), 6, 8, 0.7)
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.6
        nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(_ramp(nt, n, [(0.2, (0.5, 0.5, 0.5)), (0.8, (1, 1, 1))]), mx.inputs['B'])
        nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.85
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
        nt.links.new(br.outputs['Fac'], inv.inputs[1])
        _bump(nt, b, inv.outputs[0], 0.6, 0.02)
    elif kind == 'wood':
        c = kw.get('c', (0.23, 0.14, 0.08))
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = kw.get('grain', (14, 14, 1.2)); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        n = _noise(nt, mp.outputs['Vector'], 3, 8, 0.6)
        nt.links.new(_ramp(nt, n, [(0.3, tuple(x * 0.5 for x in c)), (0.7, c)]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = kw.get('rough', 0.7)
        _bump(nt, b, n, 0.4, 0.01)
    elif kind == 'grass':
        n = _noise(nt, _coord(nt, 1), 0.6, 8, 0.6)
        nt.links.new(_ramp(nt, n, [(0.3, (0.06, 0.13, 0.03)), (0.55, (0.13, 0.22, 0.05)), (0.75, (0.22, 0.26, 0.08))]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.8
        _bump(nt, b, _noise(nt, _coord(nt, 1), 60, 4, 0.8), 1.0, 0.04)
    elif kind == 'water':
        c = kw.get('c', (0.05, 0.09, 0.06))
        b.inputs['Base Color'].default_value = (*c, 1)
        b.inputs['Roughness'].default_value = kw.get('rough', 0.04)
        b.inputs['Transmission Weight'].default_value = kw.get('trans', 0.55)
        b.inputs['IOR'].default_value = 1.33
        tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.name = 'flow'
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        n = _noise(nt, mp.outputs['Vector'], kw.get('scale', 5), 3, 0.5)
        _bump(nt, b, n, kw.get('bump', 0.12), 0.05)
    elif kind == 'metal':
        b.inputs['Base Color'].default_value = (*kw.get('c', (0.1, 0.1, 0.1)), 1)
        b.inputs['Metallic'].default_value = 1.0; b.inputs['Roughness'].default_value = kw.get('rough', 0.45)
        _bump(nt, b, _noise(nt, _coord(nt, 1), 80, 4, 0.7), 0.15, 0.005)
    elif kind == 'glass':
        b.inputs['Base Color'].default_value = (*kw.get('c', (0.03, 0.04, 0.05)), 1)
        b.inputs['Roughness'].default_value = 0.05; b.inputs['Metallic'].default_value = 0.6
    elif kind == 'clear':
        b.inputs['Base Color'].default_value = (0.9, 0.95, 0.92, 1); b.inputs['Roughness'].default_value = 0.02
        b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.45
    elif kind == 'emit':
        b.inputs['Emission Color'].default_value = (*kw.get('c', (1, 0.6, 0.25)), 1)
        b.inputs['Emission Strength'].default_value = kw.get('e', 20)
        b.inputs['Base Color'].default_value = (*kw.get('c', (1, 0.6, 0.25)), 1)
    elif kind == 'cloth':
        c = kw.get('c', (0.5, 0.45, 0.35))
        n = _noise(nt, _coord(nt, 1), kw.get('scale', 6), 6, 0.6)
        nt.links.new(_ramp(nt, n, [(0.25, tuple(x * 0.6 for x in c)), (0.75, c)]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.9; b.inputs['Sheen Weight'].default_value = 0.3
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 300
        nt.links.new(_coord(nt, 1), wv.inputs['Vector'])
        ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 5
        nt.links.new(n, ad.inputs[0]); nt.links.new(wv.outputs['Fac'], ad.inputs[2])
        _bump(nt, b, ad.outputs[0], 0.5, 0.004)
    elif kind == 'leaf':
        n = _noise(nt, _coord(nt, 1), 9, 3, 0.6)
        c = kw.get('c', (0.07, 0.16, 0.03))
        nt.links.new(_ramp(nt, n, [(0.3, tuple(x * 0.45 for x in c)), (0.7, tuple(min(1, x * 1.5) for x in c))]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.6
        b.inputs['Subsurface Weight'].default_value = 0.2
        _bump(nt, b, _noise(nt, _coord(nt, 1), 25, 3, 0.8), 1.0, 0.08)
    elif kind == 'plain':
        b.inputs['Base Color'].default_value = (*kw.get('c', (0.5, 0.5, 0.5)), 1)
        b.inputs['Roughness'].default_value = kw.get('rough', 0.6)
        b.inputs['Metallic'].default_value = kw.get('metal', 0.0)
        if kw.get('sss'):
            b.inputs['Subsurface Weight'].default_value = kw['sss']; b.inputs['Subsurface Scale'].default_value = 0.01
    elif kind == 'fur':
        c = kw.get('c', (0.12, 0.09, 0.07))
        n = _noise(nt, _coord(nt, 1), 40, 4, 0.7)
        nt.links.new(_ramp(nt, n, [(0.3, tuple(x * 0.5 for x in c)), (0.7, tuple(x * 1.3 for x in c))]), b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.55
    elif kind == 'ray':   # fake light shaft
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (*kw.get('c', (1, 0.93, 0.8)), 1); em.inputs['Strength'].default_value = kw.get('e', 0.6)
        ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
        nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    _m[key] = m
    return m


# ---------------------------------------------------------------- geometry helpers
def obj(name, bm, material=None, smooth=False, col=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(o)
    if material:
        me.materials.append(material)
    return o


def box(size, loc, material, rot=(0, 0, 0), name='box', bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
    o = obj(name, bm, material, smooth=bool(bevel))
    o.location = loc; o.rotation_euler = rot
    return o


def cyl(r, h, loc, material, rot=(0, 0, 0), seg=20, r2=None, name='cyl', caps=True, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = obj(name, bm, material, smooth=smooth)
    o.location = loc; o.rotation_euler = rot
    if smooth:
        m = o.modifiers.new('e', 'EDGE_SPLIT'); m.split_angle = math.radians(50)
    return o


def sphere(r, loc, material, scale=(1, 1, 1), seg=20, name='sph', noise=0.0, seed=0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 2, radius=r)
    if noise:
        rnd = random.Random(seed)
        from mathutils import noise as mn
        off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
        for v in bm.verts:
            v.co += v.co.normalized() * mn.noise(v.co * (1.6 / r) + off) * noise
    o = obj(name, bm, material, smooth=True)
    o.location = loc; o.scale = scale
    return o


def grid(sx, sy, nx, ny, hfun, material, loc=(0, 0, 0), name='ground', hole=None):
    """height-field ground; hole=(x0,x1,y0,y1) removes faces inside (for pits/graves)."""
    bm = bmesh.new()
    vs = [[None] * (ny + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -sx / 2 + sx * i / nx; y = -sy / 2 + sy * j / ny
            vs[i][j] = bm.verts.new((x, y, hfun(x + loc[0], y + loc[1])))
    for i in range(nx):
        for j in range(ny):
            cx = -sx / 2 + sx * (i + .5) / nx + loc[0]; cy = -sy / 2 + sy * (j + .5) / ny + loc[1]
            if hole and hole[0] < cx < hole[1] and hole[2] < cy < hole[3]:
                continue
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    o = obj(name, bm, material, smooth=True)
    o.location = loc
    return o


def join(objs, name='joined'):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = objs[0]
    o.name = name
    # bake the transform so the joined object's origin is the world origin
    M = Matrix.Translation(o.location) @ Euler(o.rotation_euler).to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale, 1))
    o.data.transform(M)
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    return o


def light(kind, loc, energy, color=(1, 1, 1), size=0.2, rot=(0, 0, 0), spot=None, name='light'):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind in ('POINT', 'SPOT'):
        d.shadow_soft_size = size
    elif kind == 'AREA':
        d.size = size
    elif kind == 'SUN':
        d.angle = size
    if spot:
        d.spot_size = spot; d.spot_blend = 0.4
    o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o


def parent_to_bone(o, arm, bone, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Attach a prop to a bone; loc/rot are in bone space (y along the bone)."""
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bone
    L = arm.data.bones[bone].length
    o.location = Vector(loc) - Vector((0, L, 0)); o.rotation_euler = rot
    return o
