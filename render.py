"""Usage: python3 render.py <stage> <outdir> [--res WxH] [--samples N] [--every N] [--frames a-b] [--shots i,j]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wj import film
a = sys.argv[1:]
name, out = a[0], a[1]
kw = {}
i = 2
while i < len(a):
    k, v = a[i], a[i + 1]; i += 2
    if k == '--res':
        kw['res'] = tuple(int(x) for x in v.split('x'))
    elif k == '--samples':
        kw['samples'] = int(v)
    elif k == '--every':
        kw['every'] = int(v)
    elif k == '--frames':
        lo, hi = v.split('-'); kw['frames'] = set(range(int(lo), int(hi) + 1))
    elif k == '--shots':
        kw['only'] = set(int(x) for x in v.split(','))
film.render_stage(name, out, **kw)
