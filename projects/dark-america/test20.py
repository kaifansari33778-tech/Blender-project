"""Dark America - 20 s world-building test: one continuous 3D scene that rebuilds itself on every phrase.
Usage: python3 test20.py stills <dir> t1,t2 | render <outdir> | mux <outdir> <out.mp4>"""
import sys, os, math, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Cam3, Card, World, dust
from voxkit.show3d import Show3, run, WHITE

_sp = importlib.util.spec_from_file_location('zoo', os.path.join(HERE, 'sample3d.py')); Z = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(Z)
T = Z.T; VOICE = Z.VOICE; DUR = 20.9; pi = math.pi

# ------------------------------------------------------------------ skies that change with the story
SK = {'day': art3d.sky((.36, .56, .78), (.97, .88, .70), 1), 'africa': art3d.sky((.86, .46, .22), (.99, .86, .52), 2), 'city': art3d.sky((.30, .46, .70), (.95, .82, .72), 3),
      'dusk': art3d.sky((.20, .22, .42), (.98, .62, .40), 4), 'night': art3d.sky((.03, .04, .09), (.24, .18, .26), 5)}
SKEYS = [(0, 'day'), (4.3, 'day'), (4.8, 'africa'), (6.7, 'africa'), (7.2, 'day'), (8.4, 'day'), (8.9, 'city'), (10.3, 'city'), (10.8, 'day'), (12.3, 'day'), (12.9, 'dusk'), (15.0, 'dusk'), (15.6, 'night'), (99, 'night')]
def sky_at(t):
    for (ta, a), (tb, b) in zip(SKEYS, SKEYS[1:]):
        if t <= tb:
            k = smooth(seg(t, ta, tb)); return SK[a] if a == b or k <= 0 else SK[a] * (1 - k) + SK[b] * k
    return SK['night']
WORLD = World(art3d.ground_tex(), sky_at, fog=(.86, .78, .64), fog_d=85, focus=8.0, dof=12)

# ------------------------------------------------------------------ pieces
OTA = Z.OTA; PEOPLE = Z.PEOPLE; TREES = Z.TREES; CLOUDS = Z.CLOUDS
GATE = art3d.gate('BRONX ZOO'); CAL = art.calendar('YEAR', '1906', seed=2); AFRICA = K.africa(); LOCK = K.padlock(); PINR = K.mappin()
LIB = K.liberty(); BRIDGE = K.bbridge(); ELE = K.elephant(); GIR = K.giraffe(); BOOTH = K.booth()
_cols = [(.62, .60, .58), (.70, .70, .74), (.78, .70, .58), (.55, .66, .76), (.60, .40, .32), (.50, .52, .58), (.74, .62, .50), (.44, .50, .60)]
TOW = {'empire': K.tower('empire'), 'chrysler': K.tower('chrysler', col=_cols[1]), 'flatiron': K.tower('flatiron', col=_cols[2]), 'wtc': K.tower('wtc', col=_cols[3])}
BLK = [K.tower('block', w=300 + 40 * (i % 3), h=700 + 130 * (i % 5), col=_cols[i % 8], seed=i) for i in range(10)]
_r = np.random.default_rng(12)
CITY = [('empire', 0.0, 17.2, 4.8), ('chrysler', 5.6, 17.0, 4.2), ('wtc', -5.8, 17.4, 5.0), ('flatiron', 2.9, 15.6, 3.2)] + \
       [(int(_r.integers(10)), float(x + _r.uniform(-1, 1)), float(z), float(_r.uniform(3.2, 5.0))) for z in (17, 20, 23.5, 27.5, 32, 37) for x in np.arange(-22, 22.1, 4.4)]
DIAL = art.dial(900); _DC = {}
TEASE = [(cv2.resize(Z.BARS, (500, 350)), 1.6), (K.stamp(), 1.0), (K.bottle(skull=True), .7), (art.gavel(), 1.6), (K.syringe(), 2.2), (K.bomb(), .8), (K.cia_seal(400), 1.5), (K.grave(), 1.0)]
_LB = {}
def LBL(txt, col=ORANGE):
    if txt not in _LB: _LB[txt] = art.label(txt, 150, col=np.asarray(col, np.float32), seed=len(txt))
    return _LB[txt]
_qr = np.random.default_rng(5)
QUEUE = [(1.0 + 0.5 * math.sin(i * .8), 5.4 - i * .62) for i in range(18)]                                       # a line snaking back from the cage
BLOCK = [(x + .3 * (j % 2), z) for j, z in enumerate((6.1, 5.2, 4.3, 3.4, 2.5, 1.6, .7)) for x in (-4.6, -3.6, -2.6, 2.9, 3.9, 4.9)]
PIDX = [int(_qr.integers(12)) for _ in range(80)]


def up(t, t_in, t_out=None, d=.45):
    """Pop-up hinge angle: None before t_in / after folding at t_out, else tilt (pi/2 flat -> 0 upright)."""
    if t < t_in: return None
    tilt = (1 - back(seg(t, t_in, t_in + d), 1.4)) * pi / 2
    if t_out is not None and t > t_out:
        ko = seg(t, t_out, t_out + .3)
        if ko >= 1: return None
        tilt = max(tilt, ko * pi / 2)
    return tilt


def pin(spr, cam, sx, sy, wf, alpha=1.0, d=4.0):
    """A card pinned to the screen (fraction coords) but living d metres into the scene."""
    ww = wf * W * d / cam.f; hh = ww * spr.shape[0] / spr.shape[1]
    X, Y = (sx - .5) * W * d / cam.f, (.5 - sy) * H * d / cam.f
    cp, sp = math.cos(cam.pitch), math.sin(cam.pitch); Y1 = Y * cp + d * sp; Z1 = -Y * sp + d * cp
    cy, sn = math.cos(cam.yaw), math.sin(cam.yaw)
    return Card(spr, cam.x + X * cy + Z1 * sn, cam.z - X * sn + Z1 * cy, ww, y=cam.y + Y1 - hh / 2, yaw=-cam.yaw, shadow=0, alpha=alpha, fog=False, blur=0)


def chip(C, cam, t, txt, t0, t1, sy, wf, col=ORANGE, sx=.5, slam=True):
    """Caption: slams in at t0, shrinks away at t1."""
    if t < t0 - .13 or (t1 is not None and t > t1 + .2): return
    k = seg(t, t0 - .13, t0); s = (lerp(2.4, 1, k * k) if slam else back(seg(t, t0, t0 + .22), 1.8)) * (1 - smooth(seg(t, t1, t1 + .2)) if t1 is not None else 1)
    if s > 0.02: C.append(pin(LBL(txt, col), cam, sx, sy, wf * s, alpha=min(1, k * 2.5) if slam else 1))


def cards(t, cam):
    C = []; A = C.append
    fold = 15.1                                                                # everything folds away for the stopwatch
    # ---- sky dressing
    for i, (x, y, z, w) in enumerate(((-34, 40, 90, 34), (30, 48, 84, 30), (-6, 58, 100, 38), (48, 34, 95, 26), (-55, 52, 88, 30))):
        A(Card(CLOUDS[i % 4], x + t * 1.2, z, w, y=y, shadow=0, blur=1.5, alpha=.9 * (1 - .7 * seg(t, 15.2, 15.8))))
    for i in range(7): A(Card(Z.BIRD, -14 + i * 2.2 + t * 2.6, 30, 1.4, y=17 + 1.2 * math.sin(i * 1.7) + .4 * math.sin(t * 6 + i), shadow=0, fog=False, blur=.8))
    # ---- "America": the flag rises; it sinks for Africa and New York, returns dark for the ending
    fa = eout(seg(t, T('america') - .2, T('america') + .6), 3) * (1 - smooth(seg(t, 4.4, 4.9))) + smooth(seg(t, 6.9, 7.4)) * (1 - smooth(seg(t, 8.4, 8.9))) + smooth(seg(t, 10.4, 10.9)) * (1 - smooth(seg(t, 15.0, 15.4))) + .6 * smooth(seg(t, 16.6, 17.4))
    if fa > .01: A(Card(Z.BIGFLAG, 0, 60, 120, y=4 - 46 * (1 - min(1, fa)), wv=22, shadow=0, blur=1.0, fog=False, alpha=.93 * min(1, fa * 1.5), ph=2))
    # ---- "African man": the continent rises behind him
    ta = up(t, T('african') - .2, 6.75)
    if ta is not None:
        A(Card(AFRICA, 2.2, 11.5, 11.5, y=.6, tilt=ta, shadow=.4)); A(Card(PINR, 3.0, 11.3, 1.3, y=6.6 + .25 * abs(math.sin(t * 5)), tilt=ta, shadow=0))
        for i, (x, z, w) in enumerate(((-6.5, 12, 6), (-9, 8, 5), (8.6, 8, 5))): A(Card(art_ACACIA, x, z, w, tilt=ta))
    # ---- "New York": the city pops up behind, wave after wave
    for i, (kind, x, z, w) in enumerate(CITY):
        tl = up(t, T('new') - .25 + (z - 17) * .03 + (i % 5) * .02, fold, .5)
        if tl is not None and t < 10.9 + 10: A(Card(TOW[kind] if isinstance(kind, str) else BLK[kind], x * 1.9, z * 1.5 + 2, w * 2.3, tilt=tl, shadow=.3))
    tl = up(t, T('new') - .1, fold)
    if tl is not None:
        A(Card(LIB, -17, 21, 8.5, tilt=tl)); A(Card(BRIDGE, 24, 34, 50, tilt=tl, shadow=0, blur=.6))
    # ---- "in a zoo": gate, trees, animals
    tz = up(t, T('zoo') - .35, fold)
    if tz is not None:
        A(Card(GATE, 0, 0.2, 11.5, tilt=tz))
        for i, (x, z, w) in enumerate(((-9.5, 10, 6), (9.6, 9.5, 6.5), (-8.5, 4, 5), (8.6, 3.6, 5), (-12.5, 14, 8), (12.8, 15, 8))): A(Card(TREES[i % 4], x, z, w, tilt=tz, sway=.06, ph=i))
        for sx_ in (-1, 1): A(Card(Z.LAMP, sx_ * 4.3, 6.4, .62, tilt=tz))
    tb = up(t, T('bronx') - .1, fold)
    if tb is not None:
        A(Card(ELE, -8.2, 8.6, 4.0, y=.03 * abs(math.sin(t * 2)), tilt=tb)); A(Card(GIR, 8.0, 8.8, 2.3, tilt=tb)); A(Card(Z.CAGE2, -8.2, 7.4, 5.0, tilt=tb)); A(Card(Z.CAGE2, 8.0, 7.4, 5.0, tilt=tb))
        A(Card(BOOTH, -4.9, 3.2, 1.5, tilt=tb)); A(Card(PINR, 0, 9.0, 2.2, y=lerp(22, 8.3, eout(seg(t, T('bronx'), T('bronx') + .35), 2)) + .3 * abs(math.sin(t * 5)), shadow=0, fog=False, alpha=1 - smooth(seg(t, 10.3, 10.6))))
    # ---- "the monkey house": building + a lit enclosure
    tm = up(t, T('locked') - .1, fold)
    if tm is not None:
        A(Card(Z.HOUSE, 0, 12.0, 22, tilt=tm)); A(Card(Z.INWALL, 0, 10.0, 5.6, tilt=tm)); A(Card(Z.STRAW, 0, 7.55, 5.5, tilt=pi / 2, shadow=0, alpha=seg(t, T('locked') + .2, T('locked') + .4) * (1 - seg(t, fold, fold + .2))))
        a2 = seg(t, T('locked') + .25, T('locked') + .45) * (1 - seg(t, fold, fold + .2))
        A(Card(Z.SIDEWALL, -2.8, 8.75, 2.5, yaw=pi / 2, alpha=a2, shadow=0)); A(Card(Z.SIDEWALL, 2.8, 8.75, 2.5, yaw=pi / 2, alpha=a2, shadow=0)); A(Card(Z.BRANCH, -.3, 9.7, 5.0, y=2.2, tilt=tm, shadow=0))
        A(Card(Z.ROOF, 0, 7.5, 5.9, y=3.92, shadow=0, alpha=a2)); A(Card(Z.SIGN, 0, 7.45, 3.6, y=4.45, shadow=0, alpha=a2)); A(Card(Z.PARROT, 1.9, 9.6, .45, y=2.75, tilt=tm, shadow=0))
    # ---- "with an orangutan": swings in from the side
    if T('orangutan') - .5 < t < fold + .3:
        k = eout(seg(t, T('orangutan') - .5, T('orangutan') + .1), 3)
        A(Card(Z.ORANG, lerp(-6.5, -1.7, k), 9.1, 1.6, y=1.6 * math.sin(pi * k) + .03 * abs(math.sin(t * 3)), tilt=max(0, (seg(t, fold, fold + .3)) * pi / 2)))
    # ---- him: enters alone, steps aside for Africa, back to centre for the cage
    to = up(t, T('human') - .1, fold)
    if to is not None:
        ox = -1.3 * smooth(seg(t, 4.4, 4.9)) * (1 - smooth(seg(t, 6.6, 7.0))) + .35 * smooth(seg(t, 10.3, 11.0))
        A(Card(OTA, ox, 8.8, 2.6, tilt=to))
    kb = seg(t, T('zoo') - .14, T('zoo'))                                      # bars slam on "zoo"
    if kb > 0 and t < fold + .3: A(Card(Z.BARS, 0, 7.5, 5.6, y=lerp(9, 0, kb * kb), shadow=.5, tilt=seg(t, fold, fold + .3) * pi / 2))
    kl = seg(t, T('locked') - .14, T('locked'))                                # the padlock drops on "locked"
    if kl > 0 and t < fold: A(Card(LOCK, 1.75, 7.42, .8 * (1 + .25 * math.exp(-max(0, t - T('locked')) * 14)), y=lerp(9, 1.1, kl * kl), shadow=0, fog=False))
    # ---- "crowds lined up": a queue snakes back from the cage, then the plaza fills
    for i, (x, z) in enumerate(QUEUE):
        tl = up(t, T('crowds') - .1 + i * .045, fold, .3)
        if tl is not None: p = PEOPLE[PIDX[i]]; A(Card(p, x + .03 * math.sin(t * 1.7 + i), z, 1.75 * p.shape[1] / p.shape[0], y=.02 * abs(math.sin(t * 2.2 + i)), tilt=tl, ph=i))
    for i, (x, z) in enumerate(BLOCK):
        tl = up(t, T('lined') + i * .02, fold, .3)
        if tl is not None:
            p = PEOPLE[PIDX[20 + i]]; A(Card(p, x, z, 1.75 * p.shape[1] / p.shape[0], y=.02 * abs(math.sin(t * 2.2 + i)), tilt=tl, ph=i))
            if i % 6 == 1 and tl < .05: A(Card(Z.BALLOONS[i % 3], x + .28, z + .02, .42, y=1.0 + .05 * math.sin(t * 1.6 + i), shadow=0, sway=.06, ph=i))
            if i % 6 == 4 and tl < .05: A(Card(Z.PARASOL, x + .1, z + .02, 1.15, y=1.28, shadow=0))
    # ---- "sixty seconds": the stopwatch and a ring of what is coming
    if t > T('give') - .1:
        kk = back(seg(t, T('give') - .1, T('give') + .3), 2.0); k = int(np.floor(seg(t, T('give') + .1, DUR) * 46))
        if k not in _DC:
            d = DIAL.copy(); c = 450; a = k / 46 * 2 * pi * .95
            cv2.line(d, (c, c), (int(c + math.sin(a) * 330), int(c - math.cos(a) * 330)), (.80, .32, .05, 1), 26, cv2.LINE_AA); cv2.circle(d, (c, c), 30, (.12, .1, .09, 1), -1, cv2.LINE_AA); _DC[k] = d
        A(Card(_DC[k], 0, 8.0, 4.6 * kk, y=1.2, shadow=.5, fog=False))
        for i, (sp, w) in enumerate(TEASE):
            tl = up(t, T('show') + i * .32)
            if tl is not None: a = pi + (i + .5) / 8 * pi; A(Card(sp, 5.4 * math.cos(a) * (1.0 if i % 2 else .8), 7.6 - 2.8 * math.sin((i + .5) / 8 * pi) + (0 if i % 2 else 1.3), w * 1.15, tilt=tl))
    # ---- captions and pinned chips (rearranged as the story moves on)
    k0 = seg(t, T('nineteen') - .13, T('nineteen'))
    if k0 > 0 and t < 15.3:                                                    # the year: lands big in the middle, then tucks into the corner
        m = smooth(seg(t, 1.35, 1.9)); A(pin(CAL, cam, lerp(.5, .16, m), lerp(.40, .085, m), lerp(.46, .2, m) * lerp(2.2, 1, k0 * k0) * (1 - smooth(seg(t, 15.0, 15.3))), alpha=min(1, k0 * 2.5)))
    if T('new') - .1 < t < 10.75:                                              # he lifts above the city while New York builds
        k = back(seg(t, T('new') - .1, T('new') + .3), 1.6) * (1 - smooth(seg(t, 10.4, 10.75))); A(pin(OTA, cam, .78, .60, .30 * k)) if k > .02 else None
    chip(C, cam, t, 'A HUMAN BEING', T('human'), 4.35, .2, .74, WHITE); chip(C, cam, t, 'IN A ZOO', T('zoo'), 4.35, .81, .62)
    chip(C, cam, t, 'FROM AFRICA', T('african'), 5.75, .81, .62); chip(C, cam, t, 'OTA BENGA', T('ota'), 8.35, .2, .66, WHITE)
    chip(C, cam, t, 'LOCKED IN THE MONKEY HOUSE', T('locked'), 8.35, .81, .9); chip(C, cam, t, 'NEW YORK CITY', T('new'), 10.3, .16, .78)
    chip(C, cam, t, 'THE BRONX ZOO', T('bronx'), 10.3, .86, .72, WHITE); chip(C, cam, t, 'CAGED WITH AN ORANGUTAN', T('orangutan'), 12.3, .81, .9)
    chip(C, cam, t, 'CROWDS LINED UP TO STARE', T('crowds'), 15.0, .16, .9); chip(C, cam, t, '60 SECONDS', T('sixty'), None, .13, .66)
    chip(C, cam, t, "AMERICA'S DARKEST CHAPTERS", T('darkest'), None, .82, .92)
    return C


art_ACACIA = K.cut([('p', [(.46, .5), (.54, .5), (.56, 1), (.44, 1)]), ('e', .5, .34, .48, .16), ('e', .3, .28, .22, .1), ('e', .72, .26, .2, .1)], 700, 700, (.30, .36, .16), 140)
K.paint(art_ACACIA, [('p', [(.47, .5), (.53, .5), (.55, .99), (.45, .99)])], (.36, .24, .14))


def extra(img, cam, t):
    dust(img, cam, (0, .2, 7.4), t, T('zoo'), n=46, seed=3, speed=3.2)


def grade(img, t):
    k = smooth(seg(t, 16.9, 17.8))                                             # "the darkest things": the world goes cold and dark
    if k <= 0: return img
    lum = img.mean(2, keepdims=True); return (img * (1 - .45 * k) + lum * .45 * k) * (1 - .22 * k) * (1 + k * (np.float32([.86, .95, 1.18]) - 1))


SCENE = dict(t=0.0, world=WORLD, items=[], fns=[cards], extra=extra, grade=grade,
             cam=[(0, 0, 2.0, -4.5, 0, .06), (2.0, 0, 1.9, .2, 0, .09), (3.5, 0, 1.8, 1.4, 0, .1), (4.5, .2, 1.85, 1.4, 0, .1), (5.6, .9, 2.2, -.6, -.08, .12), (6.7, .5, 2.0, .4, -.04, .11),
                  (8.3, 0, 1.85, 2.6, 0, .1), (9.4, 0, 17.0, -17.0, 0, -.14), (10.3, 0, 18.5, -18.5, 0, -.15), (11.4, -1.2, 1.6, 3.6, .04, .07), (12.4, -1.2, 1.6, 3.7, .04, .07),
                  (13.8, 0, 3.8, -8.5, 0, -.08), (15.0, 0, 3.4, -7.2, 0, -.06), (16.2, 0, 2.3, -3.4, 0, .08), (20.9, 0, 2.1, .8, 0, .11)])
SCENE['hits'] = []


def sfx(add):
    SR = film.SR; n = int(.5 * SR); tt = np.arange(n) / SR; clang = np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / .12) * .5 + np.sin(2 * np.pi * 1210 * tt) * np.exp(-tt / .07) * .3
    add(clang, T('zoo'), .10); add(film.thump(60, 30, 1.0, .3), T('zoo'), .28); add(film.riser(.9), T('zoo') - .9, .1); add(clang, T('locked'), .06); add(film.thump(90, 40, .5, .12), T('locked'), .2)
    for tc in (T('nineteen'), T('human'), T('african'), T('ota'), T('new'), T('bronx'), T('orangutan'), T('crowds'), T('sixty'), T('darkest')): add(film.thump(82, 32, .6, .14), tc, .2); add(film.nburst(.25, 300, 3000, .04), tc, .06)
    for i in range(30): add(film.nburst(.09, 900, 5000, .02), T('new') - .2 + i * .04, .03, (-1) ** i * .5)          # the city popping up
    for i in range(24): add(film.nburst(.09, 900, 5000, .02), T('crowds') + i * .05, .025, (-1) ** i * .5)
    add(film.whoosh(1.0, 200, 2000, .5), T('america') - .3, .08); add(film.whoosh(.9, 200, 2000, .5), 8.5, .1); add(film.whoosh(.8, 200, 2000, .5), 15.0, .12)
    for i in range(46): add(film.tick(), T('give') + .1 + i * (DUR - T('give') - .1) / 46, .05)
    c = film._filt(np.random.default_rng(2).normal(0, 1, int(2.6 * SR)), 250, 1200); add(c * np.sin(np.pi * np.arange(len(c)) / len(c)), T('crowds'), .02)


SHOW = Show3([SCENE], DUR, VOICE, sfx_extra=sfx)
if __name__ == '__main__': run(SHOW, sys.argv)
