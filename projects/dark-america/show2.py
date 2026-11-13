"""Dark America - full video, world-building edition: every story is one continuous 3D scene that rebuilds on each phrase.
Usage: python3 show2.py stills <dir> t1,t2 | render <outdir> [a-b] | mux <outdir> <out.mp4>"""
import sys, os, math, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Card
from voxkit.show3d import I, Lb, Show3, run, fall, WHITE


def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + '.py')); m = importlib.util.module_from_spec(sp); sys.modules[name] = m; sp.loader.exec_module(m); return m
S = _load('show'); Q = _load('test20')
T = S.T; Z = S.Z; pi = math.pi; DUR = 122.0; pw = S.pw


def skyfn(keys, pal):
    sk = {k: art3d.sky(a, b, i + 20) for i, (k, (a, b)) in enumerate(pal.items())}
    def fn(t):
        if t <= keys[0][0]: return sk[keys[0][1]]
        for (ta, a), (tb, b) in zip(keys, keys[1:]):
            if t <= tb:
                k = smooth(seg(t, tb - .5, tb)); return sk[a] if a == b or k <= 0 else sk[a] * (1 - k) + sk[b] * k
        return sk[keys[-1][1]]
    return fn


def pinned(spr, t0, t1, sx, sy, wf, big=None):
    """A card pinned to the screen: pops at t0, leaves at t1. big=(sx, sy, wf, hold) makes it land large first, then tuck away."""
    def fn(t, cam):
        if t < t0 - .13 or t > t1 + .25: return []
        k = seg(t, t0 - .13, t0); s = lerp(2.2, 1, k * k) * (1 - smooth(seg(t, t1, t1 + .25))); x, y, w = sx, sy, wf
        if big: m = smooth(seg(t, t0 + big[3], t0 + big[3] + .5)); x, y, w = lerp(big[0], sx, m), lerp(big[1], sy, m), lerp(big[2], wf, m)
        return [Q.pin(spr, cam, x, y, w * s, alpha=min(1, k * 2.5))] if s > .02 else []
    return fn


def cal(top, big, seed=0): return art.calendar(top, big, seed=seed)
PINR = Q.PINR; SPIRO = K.spiro(); GERMS = [K.germ(i) for i in range(3)]; MAG = K.magnifier(); COINS = [K.coin(), K.coin(txt='5¢')]
NIGHTTOW = [K.tower(k, col=c, lit=.45) for k, c in (('empire', (.30, .30, .36)), ('chrysler', (.34, .34, .40)), ('wtc', (.26, .32, .40)))] + [K.tower('block', w=320 + 40 * (i % 3), h=800 + 140 * (i % 4), col=(.26 + .03 * (i % 3), .26, .32), seed=i, lit=.4) for i in range(6)]
DAYTOW = [Q.TOW['empire'], Q.TOW['chrysler'], Q.TOW['wtc']] + Q.BLK[:6]
def skyline(tows, t0, out=None, z0=40, quiet=True):
    pos = [(0, z0, 11), (10, z0 + 1, 10), (-10.5, z0 + 2, 11.5)] + [(x, z0 + 5 + (i % 2) * 5, 10) for i, x in enumerate((-26, -17, -5.5, 5.5, 17, 26))]
    return [I(tows[i], x, z, w, t=t0 + i * .05, out=out, quiet=quiet, sh=.3) for i, (x, z, w) in enumerate(pos)]


# ------------------------------------------------------------------ Idaho 1914
M = S.S_MAIL; GRANDMA = K.fig((.50, .40, .50), (.44, .36, .46), 0, 'wig', skirt=True, seed=80); GRANDPA = K.fig((.36, .34, .30), (.24, .22, .22), 0, 'wig', seed=81)
M['world'].sky = skyfn([(20.9, 'dawn'), (23.0, 'day'), (25.4, 'noon'), (28.7, 'gold')], {'dawn': ((.50, .52, .70), (.98, .78, .62)), 'day': ((.40, .60, .80), (.96, .88, .68)), 'noon': ((.30, .56, .84), (.92, .90, .76)), 'gold': ((.46, .50, .66), (.99, .80, .50))})
M['items'] += [I(K.idaho(), 5.2, 16, 7.5, y=.5, t=T('idaho') - .1, out=25.2), I(PINR, 5.0, 15.8, 1.3, y=5.4, t=T('idaho') + .15, out=25.2, sh=0, bob=.25),
               I(art.house(col=(.72, .60, .50)), 6.8, 9.8, 3.6, t=T('grandparents') - .25), I(GRANDMA, 5.9, 8.2, pw(GRANDMA, 1.6), t=T('grandparents'), bob=.02), I(GRANDPA, 6.8, 8.2, pw(GRANDPA, 1.72), t=T('grandparents') + .1, bob=.02),
               I(Z.TRIPOD, -4.2, 7.0, .9, t=T('idaho') + .2)]
M['fns'] += [fall(COINS, T('fifty'), 29.5, 20, 31, (-3, 3, 4.5, 9), 7.5, .32, 3.0), pinned(cal('YEAR', '1914', 21), T('nineteen', 2), 30.0, .135, .058, .17, big=(.5, .42, .46, .9))]

# ------------------------------------------------------------------ Prohibition
P = S.S_PROH
P['world'].sky = skyfn([(30.2, 'night'), (34.4, 'night'), (35.0, 'eerie'), (36.4, 'eerie'), (37.0, 'night'), (39.4, 'night'), (40.0, 'blood'), (99, 'blood')],
                       {'night': ((.04, .05, .10), (.34, .24, .30)), 'eerie': ((.03, .10, .06), (.30, .44, .22)), 'blood': ((.10, .03, .06), (.62, .20, .16))})
P['items'] += [I(K.factory(), -11, 20, 12, t=T('industrial') - .15, out=37.9, quiet=True), I(K.factory(), 11.5, 21, 12, t=T('industrial'), out=37.9, quiet=True),
               I(K.skull(), 0, 13, 6.5, y=2.2, t=T('scare'), a='grow', sh=0, fog=False, alpha=.92, out=36.4, bob=.15)] + skyline(NIGHTTOW, T('new', 2) - .2, z0=44) + \
              [I(cal('IN', '1 YEAR', 22), 3.4, 7.3, 1.3, y=1.1, t=T('single'), a='slam', sh=0, fog=False, blur=0, face=True, out=43.4)]

# ------------------------------------------------------------------ Supreme Court 1927
C = S.S_COURT; USMAP = K.usmap()
C['world'].sky = skyfn([(46.0, 'day'), (50.3, 'day'), (50.9, 'grey'), (52.0, 'grey'), (52.6, 'cold'), (55.0, 'cold'), (55.6, 'dusk'), (99, 'dusk')],
                       {'day': ((.38, .55, .74), (.97, .90, .76)), 'grey': ((.46, .48, .52), (.82, .80, .76)), 'cold': ((.26, .32, .44), (.74, .76, .80)), 'dusk': ((.22, .22, .40), (.96, .64, .44))})
_pins = [(-5.2, 6.6), (-3.4, 7.6), (-1.6, 6.2), (.2, 7.8), (1.8, 6.4), (3.4, 7.4), (4.8, 6.0), (-2.6, 5.2), (.8, 5.0), (2.8, 5.3), (-4.4, 5.4), (5.6, 7.4)]
C['items'] += [I(USMAP, 0, 14.6, 17, y=2.6, t=T('states') - .15, out=51.9, sh=.3)] + [I(PINR, x, 14.4, .9, y=y, t=T('states') + .1 + i * .05, out=51.9, sh=0, quiet=i % 3 > 0, bob=.12) for i, (x, y) in enumerate(_pins)]
C['fns'] += [fall([cal('YEAR', str(y), 23 + i) for i, y in enumerate((1927, 1950, 1975, 2000, 2026))], T('never') - .2, 58.3, 16, 33, (-3.5, 3.5, 4.5, 8), 8, .7, 3.2), pinned(cal('YEAR', '1927', 24), T('nineteen', 3), 58.3, .135, .058, .17, big=(.5, .42, .46, .8))]

# ------------------------------------------------------------------ Tuskegee
U = S.S_TUSK
U['world'].sky = skyfn([(58.5, 'sunset'), (65.0, 'sunset'), (65.6, 'purple'), (66.6, 'purple'), (67.2, 'hope'), (68.4, 'hope'), (69.0, 'dark'), (99, 'dark')],
                       {'sunset': ((.28, .30, .50), (.98, .66, .40)), 'purple': ((.18, .14, .34), (.70, .40, .44)), 'hope': ((.40, .58, .80), (.98, .92, .74)), 'dark': ((.08, .08, .18), (.52, .30, .30))})
U['items'] += [I(MAG, -3.4, 7.3, 1.3, y=1.9, t=T('watched'), a='grow', sh=0, bob=.08), I(MAG, 3.5, 7.1, 1.3, y=1.9, t=T('watched') + .12, a='grow', sh=0, bob=.08)] + \
              [I(SPIRO, x, 7.9 + (i % 2) * .8, 1.5, y=y, t=T('syphilis') + i * .07, a='grow', sh=0, out=66.4, bob=.1, quiet=i > 0) for i, (x, y) in enumerate(((-2.2, 2.5), (-.6, 3.0), (1.0, 2.6), (2.3, 3.1), (-1.4, 3.6), (.2, 3.7)))] + \
              [I(K.xmark(), 0, 6.6, 1.5, y=1.9, t=T('untreated'), a='slam', sh=0, fog=False, out=66.4)] + \
              [I(S.GRAVES[i % 3], -4.6 + i * 1.85, 13.2, 1.1, t=T('disease') + i * .1, quiet=i > 0) for i in range(6)]
U['fns'] += [fall([cal('YEAR', str(y), 40 + i) for i, y in enumerate((1932, 1942, 1952, 1962, 1972))], T('thirty') - .1, 64.5, 16, 34, (-4, 4, 4.5, 8.5), 8, .7, 3.0)]

# ------------------------------------------------------------------ Guatemala
G = S.S_GUAT; VOLC = art.mountains(2600, 700, 21, np.array([.30, .42, .36], np.float32), .75, 0)
G['world'].sky = skyfn([(71.3, 'tropic'), (74.3, 'tropic'), (74.9, 'sick'), (77.9, 'sick'), (78.5, 'red'), (99, 'red')], {'tropic': ((.26, .56, .78), (.98, .88, .58)), 'sick': ((.34, .40, .22), (.84, .80, .40)), 'red': ((.20, .08, .10), (.80, .34, .22))})
G['items'] += [I(VOLC, 0, 85, 200, sh=0, blur=1.5), I(Z.POLE, -2.2, 8.4, .26, t=T('american')), I(Z.FLAG, -1.2, 8.4, 2.0, y=3.5, wv=12, sh=0, t=T('american') + .2, a='fade'),
               I(cal('YEARS', '1940s', 25), 3.9, 7.3, 1.3, y=3.9, t=T('forties'), a='slam', sh=0, fog=False, blur=0, face=True)] + \
              [I(SPIRO, x, 7.6, 1.5, y=y, t=T('syphilis', 2) + i * .07, a='grow', sh=0, bob=.1, quiet=i > 0) for i, (x, y) in enumerate(((-2.4, 3.0), (-.8, 3.5), (.9, 3.1), (2.4, 3.6)))]

# ------------------------------------------------------------------ San Francisco 1950
F = S.S_SF; BIO = K.biohazard()
F['world'].sky = skyfn([(79.8, 'fog'), (85.9, 'fog'), (86.5, 'sick'), (87.8, 'sick'), (88.4, 'grey'), (92.4, 'grey'), (93.0, 'dusk'), (99, 'dusk')],
                       {'fog': ((.48, .58, .68), (.94, .90, .82)), 'sick': ((.30, .42, .26), (.80, .86, .50)), 'grey': ((.44, .48, .54), (.86, .84, .80)), 'dusk': ((.16, .18, .32), (.80, .50, .42))})
F['items'] += [I(BIO, 0, 34, 13, y=7, t=T('biological'), a='grow', sh=0, fog=False, alpha=.9, out=87.8), I(MAG, 3.5, 7.4, 1.6, y=2.2, t=T('rare'), a='grow', sh=0, out=94.0), I(GERMS[0], 3.5, 7.45, .62, y=3.05, t=T('rare') + .1, a='grow', sh=0, out=94.0),
               I(S.GRAVES[0], S._beds[8][0], S._beds[8][1] + .5, .8, t=T('died', 3) + .2)] + [I(S.SAILOR, -6 + i * 1.3, 15.5, pw(S.SAILOR, 1.8), y=2.2, t=T('navy') + i * .08, sh=0, out=87.6, quiet=i > 0) for i in range(4)]
F['fns'] += [fall(GERMS, T('bacteria'), 87.5, 34, 35, (-7, 7, 5, 30), 12, .7, 2.2), fall([cal('WEEK', str(i + 1), 50 + i) for i in range(4)], T('weeks') - .1, 89.6, 10, 36, (-3.5, 3.5, 4.5, 8), 8, .6, 3.4),
             pinned(cal('YEAR', '1950', 26), T('fifty', 2), 94.0, .135, .058, .17, big=(.5, .42, .46, .8))]

# ------------------------------------------------------------------ MKUltra
K_ = S.S_MK
K_['world'].sky = skyfn([(94.1, 'lab'), (96.2, 'lab'), (96.8, 'trip'), (100.2, 'trip'), (100.8, 'lab'), (102.8, 'lab'), (103.4, 'fire'), (99999, 'fire')], {'lab': ((.04, .07, .08), (.16, .20, .20)), 'trip': ((.40, .10, .46), (.96, .70, .26)), 'fire': ((.14, .05, .04), (.70, .30, .12))})
K_['items'] += [I(K.dossier(), -2.9, 7.2, 1.9, t=T('m'), a='drop', out=103.0), I(K.syringe(), 2.2, 7.4, 1.6, y=1.5, t=T('drugged'), a='grow', sh=0, out=100.4, bob=.06)]
K_['fns'] += [fall([cal('YEAR', str(y), 60 + i) for i, y in enumerate((1953, 1958, 1963, 1968, 1973))], T('for') - .1, 100.2, 14, 37, (-4, 4, 4.5, 8.5), 8, .65, 3.2)]
def mk_grade(img, t):
    k = smooth(seg(t, T('l') - .1, T('l') + .4)) * (1 - smooth(seg(t, 100.2, 100.6)))
    if k <= 0: return img
    a = t * 2.2; m = np.float32([[.6 + .4 * math.cos(a), .4 * math.sin(a), .4 * (1 - math.cos(a)) * .5], [.3 * (1 - math.cos(a)), .6 + .4 * math.cos(a + 2), .4 * math.sin(a + 1)], [.4 * math.sin(a + 3), .3 * (1 - math.cos(a)), .6 + .4 * math.cos(a + 4)]])
    return img * (1 - .55 * k) + np.clip(np.abs(img @ m.T), 0, 1.2) * .55 * k
K_['grade'] = mk_grade

# ------------------------------------------------------------------ Goldsboro 1961
O = S.S_GOLD; CLOUD = K.mushroom()
O['world'].sky = skyfn([(104.2, 'night'), (112.4, 'night'), (112.9, 'flash'), (113.5, 'flash'), (114.2, 'night'), (999, 'night')], {'night': ((.02, .04, .11), (.20, .25, .38)), 'flash': ((.50, .22, .10), (.98, .80, .50))})
O['items'] += [I(K.ncmap(), 0, 18, 20, y=1.2, t=T('north') - .15, out=110.6, sh=.3), I(PINR, 1.6, 17.8, 1.6, y=5.6, t=T('carolina'), out=110.6, sh=0, bob=.2),
               I(CLOUD, 0, 30, 26, t=T('nuclear') - .15, a='grow', sh=0, fog=False, alpha=.62, out=113.6), I(K.xmark(), 0, 6.0, 2.6, y=2.4, t=T('explosion') + .25, a='slam', sh=0, fog=False)]
O['fns'] += [pinned(cal('YEAR', '1961', 27), T('sixty', 3), 114.2, .135, .058, .17, big=(.5, .42, .46, .7))]

# ------------------------------------------------------------------ the apology, 2020
E_ = S.S_END
E_['world'].sky = skyfn([(114.4, 'dusk'), (116.9, 'dusk'), (117.5, 'today'), (120.6, 'today'), (121.2, 'night'), (999, 'night')], {'dusk': ((.14, .20, .34), (.96, .66, .44)), 'today': ((.30, .52, .82), (.96, .90, .78)), 'night': ((.04, .05, .11), (.30, .22, .30))})
E_['items'] += skyline(DAYTOW, T('twenty', 2) - .2, z0=30) + [I(K.letter(), -2.9, 7.3, 1.6, t=T('apologized'), a='drop'), I(Q.GATE, 0, 3.4, 11.5, t=114.5)] + \
               [I(Z.PEOPLE[i % 12], x, 5.2 + (i % 2) * .7, 1.75 * Z.PEOPLE[i % 12].shape[1] / Z.PEOPLE[i % 12].shape[0], t=T('zoo', 3) + i * .05, bob=.02, quiet=True) for i, x in enumerate((-4.6, -3.7, 3.6, 4.5, -5.4, 5.4))]
E_['fns'] += [fall([cal('YEAR', str(y), 70 + i) for i, y in enumerate((1906, 1930, 1960, 1990, 2020))], T('one', 4) - .2, 120.8, 16, 38, (-4, 4, 4.5, 8.5), 8, .7, 3.2)]

SCENES = [Q.SCENE, S.S_MAIL, S.S_PROH, S.S_COURT, S.S_TUSK, S.S_GUAT, S.S_SF, S.S_MK, S.S_GOLD, S.S_END]


def sfx(add):
    Q.sfx(add)
    S.sfx(lambda x, t_, g=1.0, pan=0.0: add(x, t_, g, pan) if t_ > 20.9 else None)
    for tb, n in ((T('new', 2), 12), (T('states'), 12), (T('twenty', 2), 12)):
        for i in range(n): add(film.nburst(.09, 900, 5000, .02), tb - .2 + i * .05, .028, (-1) ** i * .5)
    add(film.thump(45, 22, 1.6, .5), T('nuclear'), .22)


SHOW = Show3(SCENES, DUR, S.VOICE, sfx_extra=sfx)
if __name__ == '__main__': run(SHOW, sys.argv)
