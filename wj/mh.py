"""Build realistic rigged humans in Blender from MakeHuman / MPFB CC0 *data* files.

Only data is read from the asset repos (base mesh, morph targets, rig + weights, fitted
clothes/hair, textures); every line of code that touches them lives here.
"""
import bpy, os, json, gzip, struct, math
import numpy as np
from mathutils import Vector, kdtree

ROOT = os.environ.get('WJ_ASSETS', os.path.expanduser('~/.cache/wj_assets'))
MP = os.path.join(ROOT, 'mpfb2/src/mpfb/data')
VA = os.path.join(ROOT, 'vrm-avatar-maker/web/assets')
NBODY = 13380

_cache = {}


def _base():
    if 'base' in _cache:
        return _cache['base']
    V, VT, faces, grp = [], [], [], None
    for line in open(os.path.join(MP, '3dobjs/base.obj')):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            V.append((float(p[1]), float(p[2]), float(p[3])))
        elif p[0] == 'vt':
            VT.append((float(p[1]), float(p[2])))
        elif p[0] == 'g':
            grp = p[1]
        elif p[0] == 'f' and grp == 'body':
            c = [q.split('/') for q in p[1:]]
            faces.append(([int(q[0]) - 1 for q in c], [int(q[1]) - 1 for q in c]))
    groups = json.load(open(os.path.join(MP, 'mesh_metadata/basemesh_vertex_groups.json')))
    _cache['base'] = (np.array(V, dtype=np.float64), VT, faces, groups)
    return _cache['base']


def read_target(rel):
    key = 't:' + rel
    if key not in _cache:
        path = os.path.join(MP, 'targets', rel + '.target.gz')
        idx, d = [], []
        with gzip.open(path, 'rt') as f:
            for line in f:
                p = line.split()
                if len(p) == 4 and p[0][0] != '#':
                    idx.append(int(p[0])); d.append((float(p[1]), float(p[2]), float(p[3])))
        _cache[key] = (np.array(idx, dtype=np.int64), np.array(d))
    return _cache[key]


def _apply(C, rel, w):
    if abs(w) < 1e-4:
        return
    i, d = read_target(rel)
    if len(i):
        C[i] += d * w


def _mix(v, lo, mid, hi):
    """slider 0..1 -> weights over (lo, mid, hi) names"""
    if v < 0.5:
        return {lo: 1 - v * 2, mid: v * 2}
    return {mid: 1 - (v - 0.5) * 2, hi: (v - 0.5) * 2}


def shape_coords(gender=1.0, age=None, muscle=0.5, weight=0.5, height=0.5, race='caucasian', details=None):
    """Return MakeHuman-space coords (N,3) for the given macro description."""
    V = _base()[0]
    C = V.copy()
    age = age or {'young': 1.0}
    G = {'male': gender, 'female': 1 - gender}
    M = _mix(muscle, 'minmuscle', 'averagemuscle', 'maxmuscle')
    W = _mix(weight, 'minweight', 'averageweight', 'maxweight')
    H = _mix(height, 'minheight', None, 'maxheight')
    for g, gw in G.items():
        for a, aw in age.items():
            _apply(C, f'macrodetails/{race}-{g}-{a}', gw * aw)
            for m, mw in M.items():
                for w, ww in W.items():
                    _apply(C, f'macrodetails/universal-{g}-{a}-{m}-{w}', gw * aw * mw * ww)
                    for h, hw in H.items():
                        if h:
                            _apply(C, f'macrodetails/height/{g}-{a}-{m}-{w}-{h}', gw * aw * mw * ww * hw)
    for rel, w in (details or {}).items():
        _apply(C, rel, w)
    return C


def ground_of(C):
    g = _base()[3]['joint-ground'][0]
    return C[g[0]:g[1] + 1, 1].mean()


def to_bl(C, ground):
    """MakeHuman (y up, dm, faces +z) -> Blender (z up, m, faces -y), feet on z=0."""
    return np.stack([C[:, 0], -C[:, 2], C[:, 1] - ground], axis=1) * 0.1


def _cube(C, name):
    r = _base()[3][name][0]
    return C[r[0]:r[1] + 1].mean(axis=0)


EXPR = ['eye-left-closure', 'eye-right-closure', 'eye-left-opened-up', 'eye-right-opened-up', 'eye-left-slit',
        'eye-right-slit', 'eyebrows-left-down', 'eyebrows-right-down', 'eyebrows-left-inner-up',
        'eyebrows-right-inner-up', 'eyebrows-left-up', 'eyebrows-right-up', 'eyebrows-left-extern-up',
        'eyebrows-right-extern-up', 'mouth-compression', 'mouth-corner-puller', 'mouth-depression',
        'mouth-depression-retraction', 'mouth-elevation', 'mouth-eversion', 'mouth-open', 'mouth-parling',
        'mouth-part-later', 'mouth-protusion', 'mouth-pursing', 'mouth-retraction', 'mouth-upward-retraction',
        'nose-compression', 'nose-left-elevation', 'nose-right-elevation', 'neck-platysma']


def read_item(name):
    key = 'i:' + name
    if key in _cache:
        return _cache[key]
    meta = json.load(open(os.path.join(VA, 'items', name + '.json')))
    blob = gzip.open(os.path.join(VA, 'items', name + '.bin.gz')).read()

    def chunk(k):
        off, n, kind = meta['layout'][k][:3]
        return np.frombuffer(blob, dtype='<u4' if kind == 'I' else '<f4', count=n, offset=off)
    it = dict(meta=meta, source=chunk('source').astype(np.int64), uv=chunk('uv').reshape(-1, 2),
              tris=chunk('indices').reshape(-1, 3).astype(np.int64), refs=chunk('refs').reshape(-1, 3).astype(np.int64),
              w=chunk('weights').reshape(-1, 3).astype(np.float64), off=chunk('offsets').reshape(-1, 3).astype(np.float64),
              delete=chunk('delete').astype(np.int64))
    _cache[key] = it
    return it


def fit_item(it, C):
    """Fitted positions (MakeHuman space) of an item's render vertices on body coords C."""
    sc = []
    for ax, k in enumerate('xyz'):
        a, b, d = it['meta']['scale'][k]
        sc.append(abs(C[int(a), ax] - C[int(b), ax]) / d if d else 1.0)
    P = (C[it['refs']] * it['w'][:, :, None]).sum(axis=1) + it['off'] * np.array(sc)
    return P[it['source']]


def image(path, colorspace='sRGB'):
    img = bpy.data.images.get(os.path.basename(path)) or bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def _nodes(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']


def skin_material(name, tex, age_bump=0.3):
    m, nt, b = _nodes(name)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image(os.path.join(VA, 'textures', tex))
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.9, 0.35, 0.2)
    b.inputs['Subsurface Scale'].default_value = 0.006
    b.inputs['Roughness'].default_value = 0.48
    b.inputs['Specular IOR Level'].default_value = 0.4
    # pores + fine wrinkles
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 900; n1.inputs['Detail'].default_value = 4
    n2 = nt.nodes.new('ShaderNodeTexVoronoi'); n2.inputs['Scale'].default_value = 260
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'ADD'
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    add2 = nt.nodes.new('ShaderNodeMath'); add2.operation = 'ADD'
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = age_bump; bp.inputs['Distance'].default_value = 0.0006
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector']); nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    nt.links.new(n1.outputs['Fac'], mx.inputs[0]); nt.links.new(n2.outputs['Distance'], mx.inputs[1])
    nt.links.new(t.outputs['Color'], bw.inputs[0]); nt.links.new(mx.outputs[0], add2.inputs[0]); nt.links.new(bw.outputs[0], add2.inputs[1])
    nt.links.new(add2.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
    return m


def item_material(name, meta, tint=None, sat=1.0, val=1.0, rough=0.85, kind='cloth', mix=1.0, flat=0.0):
    """tint: rgb multiply applied to a desaturated texture (keeps painted wrinkles/seams)."""
    m, nt, b = _nodes(name)
    b.inputs['Roughness'].default_value = rough
    if meta.get('texture'):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = image(os.path.join(VA, 'textures', meta['texture']))
        col = t.outputs['Color']
        hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat
        hsv.inputs['Value'].default_value = val
        nt.links.new(col, hsv.inputs['Color']); col = hsv.outputs['Color']
        if flat:
            fl = nt.nodes.new('ShaderNodeMix'); fl.data_type = 'RGBA'
            fl.inputs['Factor'].default_value = flat; fl.inputs['B'].default_value = (0.55, 0.55, 0.55, 1)
            nt.links.new(col, fl.inputs['A']); col = fl.outputs['Result']
        if tint:
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = mix
            mx.inputs['B'].default_value = (*tint, 1)
            nt.links.new(col, mx.inputs['A']); col = mx.outputs['Result']
        nt.links.new(col, b.inputs['Base Color'])
        if meta.get('cutout'):
            nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
            m.surface_render_method = 'DITHERED'
    elif tint:
        b.inputs['Base Color'].default_value = (*tint, 1)
    if kind == 'cloth':
        tc = nt.nodes.new('ShaderNodeTexCoord')
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 700; wv.inputs['Distortion'].default_value = 1.5
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14; nz.inputs['Detail'].default_value = 5
        ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 6.0
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.002
        nt.links.new(tc.outputs['UV'], wv.inputs['Vector']); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], ad.inputs[0]); nt.links.new(wv.outputs['Fac'], ad.inputs[2])
        nt.links.new(ad.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
        b.inputs['Sheen Weight'].default_value = 0.3
    elif kind == 'hair':
        b.inputs['Roughness'].default_value = 0.55
        b.inputs['Specular IOR Level'].default_value = 0.25
    elif kind == 'eye':
        b.inputs['Roughness'].default_value = 0.05
        b.inputs['Coat Weight'].default_value = 1.0
        b.inputs['Coat Roughness'].default_value = 0.02
    elif kind == 'wet':
        b.inputs['Roughness'].default_value = 0.25
    return m


FACE_KINDS = ('eyes', 'eyebrows', 'eyelashes', 'teeth', 'tongue', 'beard', 'moustache')


class Human:
    """A rigged character: self.arm (armature), self.body (mesh), self.parts {name: mesh}."""

    def __init__(self, name, skin='skin_young_caucasian_male.jpg', eyes='eye_brown.jpg', items=(), tints=None,
                 skin_bump=0.3, collection=None, **macro):
        self.name = name
        self.col = collection or bpy.context.scene.collection
        self.Cm = shape_coords(**macro)
        self.ground = ground_of(self.Cm)
        self.C = to_bl(self.Cm, self.ground)
        V, VT, faces, groups = _base()
        self.tints = tints or {}
        items = list(items)
        base_items = ['low-poly', 'eyelashes01', 'teeth_front', 'tongue01']
        self.items = {n: read_item(n) for n in base_items + items}
        hidden = set()
        for n in items:
            hidden.update(self.items[n]['delete'].tolist())
        self._expr = {}
        for e in EXPR:
            Ce = self.Cm.copy(); _apply(Ce, 'expression/units/caucasian/' + e, 1.0)
            self._expr[e] = Ce
        self._build_rig()
        self._build_body(faces, VT, hidden, skin, skin_bump)
        for n, it in self.items.items():
            self._build_item(n, it, eyes)
        self.height = float(self.C[:NBODY, 2].max())

    # -- rig ---------------------------------------------------------------
    def _pos(self, spec):
        s = spec['strategy']
        if s == 'CUBE':
            return _cube(self.C, spec['cube_name'])
        if s == 'VERTEX':
            return self.C[spec['vertex_index']]
        if s == 'MEAN':
            return self.C[spec['vertex_indices']].mean(axis=0)
        return np.array(spec['default_position'])

    def _build_rig(self):
        rig = json.load(open(os.path.join(MP, 'rigs/standard/rig.default.json')))
        ad = bpy.data.armatures.new(self.name + '_rig')
        arm = bpy.data.objects.new(self.name, ad)
        self.col.objects.link(arm)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        for bn, b in rig.items():
            eb = ad.edit_bones.new(bn)
            eb.head = Vector(self._pos(b['head'])); eb.tail = Vector(self._pos(b['tail'])); eb.roll = b['roll']
        for bn, b in rig.items():
            if b['parent']:
                ad.edit_bones[bn].parent = ad.edit_bones[b['parent']]
        bpy.ops.object.mode_set(mode='OBJECT')
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
        self.arm = arm
        self.rest = {b.name: (b.head_local.copy(), b.tail_local.copy(), b.matrix_local.copy()) for b in ad.bones}
        w = json.load(open(os.path.join(MP, 'rigs/standard/weights.default.json')))['weights']
        self.W = {k: v for k, v in w.items() if v}
        # dense per-vertex weights for interpolation onto clothes
        self.bone_names = sorted(self.W)
        bi = {n: i for i, n in enumerate(self.bone_names)}
        D = np.zeros((len(self.C), len(self.bone_names)), dtype=np.float32)
        for n, lst in self.W.items():
            a = np.array(lst)
            D[a[:, 0].astype(int), bi[n]] = a[:, 1]
        self.D = D
        self.has_w = D.sum(axis=1) > 1e-4
        kd = kdtree.KDTree(NBODY)
        for i in range(NBODY):
            kd.insert(Vector(self.C[i]), i)
        kd.balance()
        self.kd = kd

    def _mesh(self, name, co, faces, uvs=None, loop_uv=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(c) for c in co], [], faces)
        if uvs is not None or loop_uv is not None:
            uvl = me.uv_layers.new(name='UVMap')
            if loop_uv is None:
                idx = np.zeros(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', idx)
                loop_uv = np.asarray(uvs)[idx]
            uvl.data.foreach_set('uv', np.asarray(loop_uv, dtype=np.float32).ravel())
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.update()
        ob = bpy.data.objects.new(name, me)
        self.col.objects.link(ob)
        ob.parent = self.arm
        return ob

    def _bind(self, ob, dense, names=None):
        names = names or self.bone_names
        for j, n in enumerate(names):
            col = dense[:, j]
            nz = np.nonzero(col > 1e-3)[0]
            if len(nz) == 0:
                continue
            vg = ob.vertex_groups.new(name=n)
            for i in nz:
                vg.add([int(i)], float(col[i]), 'REPLACE')
        md = ob.modifiers.new('rig', 'ARMATURE'); md.object = self.arm

    def _build_body(self, faces, VT, hidden, skin, skin_bump):
        fl, luv = [], []
        for vi, ti in faces:
            if all(v in hidden for v in vi):
                continue
            fl.append(vi); luv.extend(VT[t] for t in ti)
        ob = self._mesh(self.name + '_body', self.C[:NBODY], fl, loop_uv=luv)
        self._bind(ob, self.D[:NBODY])
        ob.shape_key_add(name='Basis')
        for e, Ce in self._expr.items():
            sk = ob.shape_key_add(name=e)
            sk.data.foreach_set('co', to_bl(Ce, self.ground)[:NBODY].astype(np.float32).ravel())
        ob.data.materials.append(skin_material(self.name + '_skin', skin, skin_bump))
        sub = ob.modifiers.new('sub', 'SUBSURF'); sub.levels = 0; sub.render_levels = 1
        self.body = ob
        self.parts = {}
        self.keyed = [ob]

    def _item_weights(self, it):
        """Interpolate body bone weights onto the item's fit vertices."""
        refs, w = it['refs'], np.clip(it['w'], 0, None)
        w = w / np.maximum(w.sum(axis=1, keepdims=True), 1e-9)
        out = np.zeros((len(refs), self.D.shape[1]), dtype=np.float32)
        helper_map = {}
        for k in range(3):
            r = refs[:, k]
            rr = r.copy()
            for i in np.nonzero(~self.has_w[r])[0]:
                v = int(r[i])
                if v not in helper_map:
                    helper_map[v] = self.kd.find(Vector(self.C[v]))[1]
                rr[i] = helper_map[v]
            out += self.D[rr] * w[:, k:k + 1].astype(np.float32)
        s = out.sum(axis=1, keepdims=True)
        return out / np.maximum(s, 1e-9)

    def _build_item(self, n, it, eyes):
        kind = it['meta']['kind']
        P = to_bl(fit_item(it, self.Cm), self.ground)
        ob = self._mesh(f'{self.name}_{n}', P, [tuple(t) for t in it['tris']], uvs=np.stack([it['uv'][:, 0], it['uv'][:, 1]], axis=1))
        nv = len(P)
        is_eye = n == 'low-poly'
        if is_eye:
            for side, sgn in (('eye.L', 1), ('eye.R', -1)):
                vg = ob.vertex_groups.new(name=side)
                vg.add([i for i in range(nv) if P[i, 0] * sgn > 0], 1.0, 'REPLACE')
            md = ob.modifiers.new('rig', 'ARMATURE'); md.object = self.arm
        elif kind in ('hair', 'hat') or n in ('eyelashes01', 'teeth_front', 'tongue01') or kind in FACE_KINDS:
            vg = ob.vertex_groups.new(name='head'); vg.add(list(range(nv)), 1.0, 'REPLACE')
            md = ob.modifiers.new('rig', 'ARMATURE'); md.object = self.arm
        else:
            self._bind(ob, self._item_weights(it)[it['source']])
        if n in ('eyelashes01', 'teeth_front', 'tongue01') or kind in ('eyebrows', 'beard', 'moustache'):
            ob.shape_key_add(name='Basis')
            for e, Ce in self._expr.items():
                Pe = to_bl(fit_item(it, Ce), self.ground)
                if np.abs(Pe - P).max() < 1e-5:
                    continue
                sk = ob.shape_key_add(name=e)
                sk.data.foreach_set('co', Pe.astype(np.float32).ravel())
            self.keyed.append(ob)
        t = self.tints.get(n, {})
        if is_eye:
            meta = dict(it['meta'], texture=eyes)
            mat = item_material(ob.name, meta, kind='eye')
        elif kind in ('hair', 'eyebrows', 'eyelashes', 'beard', 'moustache'):
            mat = item_material(ob.name, it['meta'], kind='hair', **t)
        elif n in ('teeth_front', 'tongue01'):
            mat = item_material(ob.name, it['meta'], kind='wet', **t)
        else:
            kw = dict(t); k = kw.pop('kind', 'cloth')
            mat = item_material(ob.name, it['meta'], kind=k, **kw)
        ob.data.materials.append(mat)
        self.parts[n] = ob

    # -- animation helpers ---------------------------------------------------
    def face(self, **kw):
        """Set expression unit values, e.g. face(**{'mouth-open': .5}). Unspecified keys go to 0."""
        for ob in self.keyed:
            for kb in ob.data.shape_keys.key_blocks[1:]:
                kb.value = kw.get(kb.name, 0.0)

    def bone(self, n):
        return self.arm.pose.bones[n]
