"""Dark America - full 3D pop-up diorama video, timed to voice/full.mp3.
Usage: python3 show.py stills <dir> t1,t2 | render <outdir> [a-b] | mux <outdir> <out.mp4>"""
import sys, os, math, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Cam3, Card, World, dust
from voxkit.show3d import I, Lb, Show3, run, fall, WHITE, DARK

_sp = importlib.util.spec_from_file_location('zoo', os.path.join(HERE, 'sample3d.py')); Z = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(Z)
T = Z.T; PH = os.path.join(HERE, 'photos', 'wm'); VOICE = Z.VOICE; DUR = 122.0
pi = math.pi


def world(ground, top, bot, fog, focus=8.0, fog_d=75, tile=10.0, gtex=None):
    return World(gtex if gtex is not None else art3d.ground_tex(col=ground, seed=int(sum(ground) * 100)), art3d.sky(top=top, bot=bot, seed=int(sum(top) * 50)), fog=fog, fog_d=fog_d, focus=focus, dof=13, tile=tile)


def fitw(spr, w): return cv2.resize(spr, None, fx=w / spr.shape[1], fy=w / spr.shape[1], interpolation=cv2.INTER_AREA)
def pw(spr, hgt): return hgt * spr.shape[1] / spr.shape[0]                     # card width for a wanted height in metres
def PR(name, w=560, crop=None, cap=60): return art.photo_print(os.path.join(PH, name), crop, w=w, caption_h=cap)
def flagback(spr, a=.93, y=4): return I(spr, 0, 60, 120, y=y, wv=22, sh=0, blur=1.0, fog=False, alpha=a)
def clouds(n=5, a=.92): return [I(Z.CLOUDS[i % 4], x, z, w, y=y, sh=0, blur=1.5, alpha=a, drift=(1.0, 0, 0)) for i, (x, y, z, w) in enumerate(((-34, 40, 90, 34), (30, 48, 84, 30), (-6, 58, 100, 38), (48, 34, 95, 26), (-55, 52, 88, 30))[:n])]
def people(figs, pts, t0, step=0.04, hgt=1.75, **kw): return [I(figs[i % len(figs)], x, z, pw(figs[i % len(figs)], hgt * (0.94 + 0.12 * ((i * 7) % 5) / 4)), t=t0 + i * step, bob=0.02, quiet=i % 3 > 0, **kw) for i, (x, z) in enumerate(pts)]


# ------------------------------------------------------------------ shared pieces
FLAG = Z.BIGFLAG; TREES = Z.TREES; LAMP = Z.LAMP; PINES = [K.pine(i) for i in range(3)]
DOC = K.fig((.95, .95, .92), (.2, .2, .22), 0, 'hair', board=True, seed=1); DOC2 = K.fig((.95, .95, .92), (.25, .22, .2), 1, None, board=True, seed=2); NURSE = K.fig((.95, .95, .93), (.95, .95, .93), 0, 'nurse', skirt=True, seed=3)
JUDGE = [K.fig((.09, .09, .10), skin=i % 2, hat='hair' if i % 3 else None, long=True, seed=10 + i) for i in range(3)]
MAN10 = K.fig((.30, .26, .22), (.2, .18, .17), 0, 'fedora', seed=20); WOMAN10 = K.fig((.45, .32, .36), (.40, .28, .32), 0, 'hair', skirt=True, seed=21)
GIRL = K.fig((.74, .18, .16), (.74, .18, .16), 0, 'hair', skirt=True, seed=22); POSTMAN = K.fig((.20, .28, .46), (.18, .24, .40), 1, 'cap', bag=True, seed=23)
DRINKERS = [K.fig(c, (.16, .15, .15), i % 2, ('fedora', 'cap', None)[i % 3], seed=30 + i) for i, c in enumerate(((.25, .22, .2), (.3, .2, .16), (.18, .2, .26), (.34, .3, .24), (.2, .24, .2)))]
ANON = [K.fig(np.float32([.55, .55, .56]) * k, np.float32([.42, .42, .44]) * k, 0, None, skirt=i % 2 == 1, seed=40 + i) for i, k in enumerate((1, .9, 1.08, .82))]
for a in ANON: a[..., :3] = a[..., :3].mean(2, keepdims=True) * np.float32([1, .98, .95])        # anonymous grey paper people
MEN = [K.fig(c, l, 3 + i % 2, ('cap', None, 'fedora', None)[i % 4], seed=50 + i) for i, (c, l) in enumerate((((.62, .56, .44), (.25, .30, .42)), ((.40, .46, .56), (.3, .26, .22)), ((.72, .68, .60), (.28, .32, .40)), ((.50, .38, .30), (.2, .2, .22)), ((.58, .62, .58), (.25, .28, .38)), ((.66, .5, .36), (.3, .3, .3))))]
PRISONER = K.fig((.86, .84, .80), (.86, .84, .80), 2, None, stripes=True, seed=60); GTWOMAN = [K.fig(c, c, 2, 'hair', skirt=True, seed=61 + i) for i, c in enumerate(((.70, .30, .30), (.30, .45, .60), (.75, .6, .3)))]
PATIENT = K.fig((.80, .86, .84), (.80, .86, .84), 2, None, long=True, seed=64)
AGENT = K.fig((.12, .12, .14), (.10, .10, .12), 0, 'fedora', seed=70); SAILOR = K.fig((.95, .95, .95), (.95, .95, .95), 0, 'sailor', seed=71)
OTA2 = Z.OTA


# ------------------------------------------------------------------ 0. the zoo (0 - 15.1)
def zoo_cards(t, cam): return Z.cards_at(t)
_r = np.random.default_rng(9)
STARE = people(Z.PEOPLE, [(x, z) for z in (-5.2, -4.2, -3.2, -2.2, -1.2, -0.2) for x in (-3.4, -2.3, -1.2, -0.1, 1.0, 2.1, 3.2)], T('while'), 0.02, 1.75)
S_ZOO = dict(t=0.0, world=Z.WORLD, fns=[zoo_cards], extra=Z.extra, items=STARE + [
    Lb('OTA BENGA', 0, 3.0, 7.3, 3.6, T('ota'), WHITE, out=9.9), Lb('LOCKED IN THE MONKEY HOUSE', 0, 0.1, 7.2, 4.8, T('locked'), out=9.9),
    Lb('THE BRONX ZOO · NEW YORK', 0, 6.6, 7.2, 7.0, T('bronx'), out=11.0), Lb('CAGED WITH AN ORANGUTAN', -0.9, 0.1, 7.2, 4.4, T('orangutan'), out=12.5),
    Lb('CROWDS LINED UP TO STARE', 0, 5.5, 7.2, 6.4, T('crowds'))],
    cam=[(0, .9, 2.2, -10.5, -.12, .02), (4.4, 0, 1.75, 1.3, 0, .115), (6.6, .25, 1.9, 3.2, 0, .10), (8.4, .25, 1.9, 3.3, 0, .10), (9.9, 0, 5.2, -4.5, 0, -.13), (10.5, 0, 5.2, -4.5, 0, -.13),
         (11.4, -1.3, 1.6, 3.6, .04, .07), (12.4, -1.3, 1.6, 3.7, .04, .07), (13.6, 0, 3.6, -8.0, 0, -.08), (15.1, 0, 3.3, -6.6, 0, -.07)])

# ------------------------------------------------------------------ 1. sixty seconds (15.1 - 20.9)
_DIAL = art.dial(900); _DC = {}
def dial_card(t, cam):
    k = int(np.floor(seg(t, T('give') + .1, T('give') + 4.6) * 40)); kk = back(seg(t, T('give') - .1, T('give') + .25), 2.0)
    if k not in _DC:
        d = _DIAL.copy(); c = 450; a = k / 40 * 2 * pi * 0.95
        cv2.line(d, (c, c), (int(c + math.sin(a) * 330), int(c - math.cos(a) * 330)), (.80, .32, .05, 1), 26, cv2.LINE_AA); cv2.circle(d, (c, c), 30, (.12, .1, .09, 1), -1, cv2.LINE_AA); _DC[k] = d
    return [Card(_DC[k], 0, 8.0, 4.4 * kk, y=1.3, shadow=.5, fog=False)] if kk > 0 else []
TEASE = [(fitw(Z.BARS, 500), 1.6), (K.stamp(), 1.0), (K.bottle(skull=True), .7), (art.gavel(), 1.6), (K.syringe(), 2.2), (K.bomb(), .8), (K.cia_seal(400), 1.5), (K.grave(), 1.0)]
S_SIXTY = dict(t=15.1, world=world((.22, .20, .24), (.04, .05, .10), (.30, .22, .28), (.20, .18, .24)), fns=[dial_card], items=[flagback(FLAG, .55)] +
    [I(sp, 5.2 * math.cos(pi + (i + .5) / 8 * pi) * (1.0 if i % 2 else .82), 7.4 - 2.6 * math.sin((i + .5) / 8 * pi) + (0 if i % 2 else 1.2), w, t=T('show') + i * .33) for i, (sp, w) in enumerate(TEASE)] +
    [Lb('60 SECONDS', 0, 6.2, 7.6, 3.8, T('sixty')), Lb("AMERICA'S DARKEST CHAPTERS", 0, 0.1, 5.4, 5.0, T('darkest'))],
    cam=[(15.1, 0, 2.3, -5.0, 0, .08), (20.9, 0, 2.1, 1.2, 0, .12)])

# ------------------------------------------------------------------ 2. Idaho, 1914 (20.9 - 30.2)
PO = K.post_office(); LOCO = K.loco(); CAR = K.train_car(); STAMPS = [K.stamp(c) for c in ((.72, .15, .13), (.16, .36, .26), (.18, .26, .5))]; ENV = K.envelope()
MTN = art.mountains(2600, 700, 5, np.array([.36, .42, .52], np.float32), .6, 0)
def train(t, cam):
    x = lerp(-26, 2.6, eout(seg(t, T('to', 2) - .3, T('to', 2) + 1.6), 3))
    return [Card(LOCO, x, 10.6, 5.2), Card(CAR, x - 6.3, 10.6, 7.0), Card(CAR, x - 13.6, 10.6, 7.0)] if t > T('to', 2) - .3 else []
tg = T('daughter')
S_MAIL = dict(t=20.9, world=world((.56, .50, .34), (.42, .60, .78), (.96, .86, .66), (.90, .84, .68)), fns=[train, fall(STAMPS + [ENV], T('fifty'), 30.0, 26, 3, (-4, 4, 3, 10), 8, .42, 2.4)], items=
    [I(MTN, 0, 80, 190, sh=0, blur=1.5)] + clouds(4) + [I(PINES[i % 3], x, z, w, t=21.0 + i * .04, sway=.04) for i, (x, z, w) in enumerate(((-9, 15, 5), (9.5, 14, 5.5), (-12, 19, 6), (12, 20, 6), (-7, 22, 5), (6.5, 23, 5), (-10.5, 6, 4.5), (10.8, 5, 4.5)))] +
    [I(PO, -1.5, 13.5, 10, t=21.0), I(K.mailbox(), -2.7, 6.9, .62, t=T('idaho')), I(LAMP, 3.6, 7.4, .6, t=T('idaho') + .1),
     I(MAN10, -1.15, 7.2, pw(MAN10, 1.8), t=T('parents'), bob=.02), I(WOMAN10, 1.15, 7.2, pw(WOMAN10, 1.68), t=T('parents') + .1, bob=.02), I(POSTMAN, 2.5, 6.6, pw(POSTMAN, 1.8), t=T('mailed'), bob=.02),
     I(GIRL, 0, 6.8, pw(GIRL, 1.12), t=tg, bob=.015), I(STAMPS[0], -0.1, 6.76, .2, y=.52, t=T('fifty'), a='grow', sh=0), I(STAMPS[1], 0.11, 6.76, .2, y=.48, t=T('three'), a='grow', sh=0), I(STAMPS[2], 0.0, 6.75, .2, y=.3, t=T('cents'), a='grow', sh=0),
     Lb('IDAHO', 0, 5.7, 7.3, 2.8, T('idaho'), out=26.6), Lb('PARENTS MAILED THEIR DAUGHTER', 0, 4.75, 7.3, 5.4, T('mailed'), WHITE, out=26.6), Lb('AGE 5', 1.05, 1.25, 6.7, 1.25, T('five'), WHITE, a='pop', out=28.5, anchor=True),
     Lb('53¢ IN STAMPS', 0, 0.02, 6.2, 3.6, T('fifty')), Lb('PINNED TO HER COAT', 0, 5.8, 7.3, 4.4, T('pinned'), WHITE)],
    cam=[(20.9, 1.6, 2.5, -8.5, -.1, 0), (24.6, 0, 1.8, 0.4, 0, .1), (26.6, 0, 1.3, 3.0, 0, .08), (30.2, .2, 1.35, 3.4, 0, .08)])

# ------------------------------------------------------------------ 3. Prohibition (30.2 - 46.0)
BLD = [art.building(520, 900, seed=i, dark=.34) for i in range(4)]; BARREL = K.barrel(); BARREL_X = K.barrel(skull=True); BOTTLES = [K.bottle(), K.bottle((.36, .22, .12)), K.bottle(skull=True)]; FLASK = K.flask(); GRAVES = [K.grave(seed=i) for i in range(3)]
COURT = K.courthouse(); COUNTER = K.cut([('p', [(0, 0), (1, 0), (1, 1), (0, 1)])], 1400, 260, (.36, .22, .13), 5)
P_PROH = PR('prohibition_0.jpg', 520, (0, 0, 236, 372))
tp = T('poisoned'); t4 = T('four'); t10 = T('ten')
_g1 = [(x, z) for z in (9.5, 11.5, 13.5) for x in (-3.3, -1.1, 1.1, 3.3)]; _g2 = [(x + .5 * ((int(z) % 2) - .5), z) for z in np.arange(15.5, 62, 2.6) for x in (-4.2, -2.1, 0, 2.1, 4.2)]
S_PROH = dict(t=30.2, world=world((.27, .25, .27), (.04, .05, .10), (.34, .24, .30), (.20, .18, .24), fog_d=60), items=
    [I(art.moon(), 16, 80, 9, y=34, sh=0, fog=False, blur=1)] + [I(BLD[i % 4], sx * 6.2, 1 + i * 6.5, 6.4, yaw=pi / 2, t=30.3 + i * .05, quiet=True) for i in range(5) for sx in (-1, 1)] +
    [I(COURT, 0, 34, 20, t=30.3), I(FLAG, 0, 33.8, 7, y=13, wv=14, sh=0)] + [I(LAMP, sx * 4.6, z, .6, t=30.4) for z in (4, 12, 20) for sx in (-1, 1)] +
    [I(P_PROH, -3.3, 8.2, 2.3, t=T('prohibition') + .3, out=36.3), I(DOC2, -1.3, 8.0, pw(DOC2, 1.8), t=T('government'), bob=.02, out=36.3), I(FLASK, -0.72, 7.9, .5, y=1.0, t=T('alcohol'), a='grow', sh=0, out=36.3)] +
    [I(BARREL, x, 8.3, 1.0, t=T('industrial') + i * .08, out=tp) for i, x in enumerate((.2, 1.3, 2.4))] + [I(BARREL_X, x, 8.3, 1.0, y=0, t=tp + i * .09, a='drop', out=36.3) for i, x in enumerate((.2, 1.3, 2.4))] +
    [I(K.puff(i, (.45, .80, .35)), .2 + i * 1.1, 8.25, 1.3, y=1.35, t=tp + .1 + i * .1, a='grow', sh=0, alpha=.8, drift=(0, .35, 0), out=36.2) for i in range(3)] +
    [I(COUNTER, 0, 8.6, 6.4, t=T('people', 2) - .1, out=38.0)] + [I(DRINKERS[i], -2.4 + i * 1.2, 9.0, pw(DRINKERS[i], 1.8), t=T('people', 2) + i * .06, bob=.03, out=38.0) for i in range(5)] +
    [I(BOTTLES[i % 3], -2.7 + i * .9, 8.55, .3, y=1.19, t=T('drank') + i * .05, a='grow', sh=0, out=38.0) for i in range(7)] +
    [I(GRAVES[i % 3], x, z, 1.0, t=t4 + i * .08) for i, (x, z) in enumerate(_g1)] + [I(GRAVES[i % 3], x, z, 1.0, t=t10 + i * .012, quiet=i % 6 > 0) for i, (x, z) in enumerate(_g2)] +
    [Lb('PROHIBITION', 0, 5.7, 7.3, 4.4, T('prohibition'), out=36.3), Lb('THE GOVERNMENT', 0, 4.8, 7.3, 3.6, T('government'), WHITE, out=36.3), Lb('POISONED THE ALCOHOL', 0, 0.1, 6.6, 5.0, tp, out=36.3),
     Lb('PEOPLE DRANK IT ANYWAY', 0, 5.0, 7.3, 5.2, T('drank'), WHITE, out=38.0), Lb('NEW YORK CITY', 0, 6.0, 7.3, 4.0, T('new', 2), WHITE), Lb('400 DEAD IN ONE YEAR', 0, 0.1, 6.6, 5.0, t4, out=43.5),
     Lb('10,000 DEAD', 0, 0.1, 6.6, 4.4, t10), Lb('BY SOME ESTIMATES', 0, 5.1, 7.3, 3.8, T('by'), WHITE, a='pop')],
    cam=[(30.2, -1, 2.7, -9, -.08, 0), (33.6, 0, 1.8, 1.8, 0, .09), (36.4, .2, 1.75, 3.4, 0, .09), (38.3, 0, 2.4, 1.6, 0, .03), (41.8, 0, 2.8, 2.4, 0, -.02), (46.0, 0, 3.2, 3.4, 0, -.07)])

# ------------------------------------------------------------------ 4. Supreme Court, 1927 (46.0 - 58.5)
CB = art.photo_cutout(os.path.join(PH, 'carriebuck_0.jpg'), (0, 20, 560, 700), out_h=900, fg_hint=[(280, 150, 110), (280, 500, 180)], bg_hint=[(40, 60, 40), (560, 60, 40), (40, 250, 30), (580, 250, 30)])
RULING = K.cut([('p', [(0, 0), (1, 0), (1, 1), (0, 1)])], 700, 900, (.93, .90, .80), 7)
for i in range(14): K.paint(RULING, [('l', .1, .26 + i * .048, .9 if i % 4 else .6, .26 + i * .048, 6)], (.3, .28, .26))
_t = art.text_sprite('BUCK v. BELL', 120, INK, pad=4, squeeze=.9, distress=.1, seed=4); art.paste(RULING, fitw(_t, 560), 70, 60)
_f60 = [(x + .4 * (j % 2), 9.5 + j * 1.9) for j in range(12) for x in np.arange(-6.5, 6.6, 1.3)]
S_COURT = dict(t=46.0, world=world((.80, .78, .72), (.38, .55, .74), (.97, .90, .76), (.92, .88, .78)), items=
    [flagback(FLAG, .9, 6)] + clouds(4) + [I(COURT, 0, 15.5, 24, t=46.1)] + [I(TREES[i % 4], x, z, 6, t=46.2 + i * .05, sway=.05) for i, (x, z) in enumerate(((-13, 13), (13, 12.5), (-11, 5), (11, 4.5)))] +
    [I(JUDGE[i % 3], -3.6 + i * .9, 9.6, pw(JUDGE[0], 1.85), t=T('supreme') + i * .05, bob=.01, out=51.9, quiet=i % 3 > 0) for i in range(9)] +
    [I(art.gavel(), 2.9, 7.6, 1.7, t=T('ruled'), a='drop', out=51.9), I(CB, 0, 7.9, 2.0, t=T('people', 3), out=51.9), Lb('CARRIE BUCK', 0, 2.75, 7.85, 1.9, T('people', 3) + .3, WHITE, a='pop', out=51.9, anchor=True)] +
    [I(ANON[i % 4], x, z, pw(ANON[0], 1.75), t=T('sixty', 2) + i * .012, bob=.01, quiet=i % 8 > 0, out=55.1) for i, (x, z) in enumerate(_f60)] +
    [I(RULING, 0, 7.6, 2.5, t=T('ruling'), a='drop'),
     Lb('THE SUPREME COURT', 0, 5.8, 7.3, 4.6, T('supreme'), WHITE, out=51.9), Lb('STATES MAY STERILIZE PEOPLE', 0, 0.1, 6.6, 5.2, T('sterilize'), out=51.9),
     Lb('AGAINST THEIR WILL', 0, 4.8, 7.3, 4.0, T('against'), WHITE, out=51.9), Lb('60,000+ AMERICANS', 0, 5.6, 7.3, 5.0, T('sixty', 2), out=55.1), Lb('STERILIZED', 0, 0.1, 6.6, 3.8, T('sterilized'), WHITE, out=55.1),
     Lb('NEVER OVERTURNED', 0, 0.1, 6.6, 4.8, T('never')), Lb('STILL ON THE BOOKS', 0, 5.8, 7.3, 4.2, T('officially'), WHITE, a='pop')],
    cam=[(46.0, 2, 3.0, -10, -.1, -.03), (49.2, 0, 1.8, 2.2, 0, .1), (51.9, 0, 1.7, 3.8, 0, .09), (53.6, 0, 3.0, 2.0, 0, -.02), (55.2, 0, 2.8, 2.4, 0, -.01), (58.5, 0, 1.9, 3.6, 0, .07)])

# ------------------------------------------------------------------ 5. Tuskegee (58.5 - 71.3)
SHACK = K.shack(); VIAL = K.vial(); LOCK = K.padlock(); P_TUSK = PR('tuskegee_0.jpg', 620, (900, 60, 1300, 1450))
C32 = art.calendar('FROM', '1932', seed=11); C72 = art.calendar('TO', '1972', seed=12)
_men = [(x + .35 * (j % 2), 8.6 + j * .9) for j in range(4) for x in np.arange(-2.6, 2.7, .88)]
S_TUSK = dict(t=58.5, world=world((.52, .44, .28), (.28, .30, .50), (.98, .66, .40), (.86, .62, .46)), items=
    [I(MTN, 0, 85, 200, sh=0, blur=1.5)] + clouds(3, .8) + [I(SHACK, -3.4, 13, 8, t=58.6)] + [I((TREES + PINES)[i % 7], x, z, w, t=58.6 + i * .05, sway=.05) for i, (x, z, w) in enumerate(((5, 14, 7), (-10, 12, 6), (10.5, 9, 5.5), (-8, 6, 5), (8.5, 4, 5), (-13, 18, 8), (13, 19, 8)))] +
    [I(C32, -1.5, 7.3, 1.5, y=4.5, t=T('thirty'), a='slam', sh=0, fog=False, blur=0, face=True, out=65.3), I(C72, 1.5, 7.3, 1.5, y=4.5, t=T('seventy'), a='slam', sh=0, fog=False, blur=0, face=True, out=65.3), Lb('40 YEARS', 0, 6.3, 7.3, 2.8, T('two', 2), out=65.3),
     I(DOC, -3.4, 7.6, pw(DOC, 1.8), t=T('doctors'), bob=.01), I(DOC2, 3.5, 7.4, pw(DOC2, 1.8), t=T('doctors') + .1, bob=.01), I(NURSE, -4.3, 8.2, pw(NURSE, 1.7), t=T('doctors') + .2, bob=.01),
     I(P_TUSK, 3.3, 9.3, 2.6, t=T('watched'))] +
    people(MEN, _men, T('four', 2), 0.03, 1.76) +
    [I(VIAL, 0, 6.9, .9, y=1.25, t=T('cure'), a='drop', sh=0), I(LOCK, 0, 6.85, .6, y=1.45, t=T('existed'), a='slam', sh=0),
     Lb('ALMOST 400 BLACK MEN', 0, 0.1, 6.6, 5.0, T('four', 2), out=66.4), Lb('LEFT UNTREATED', 0, 5.3, 7.3, 4.2, T('untreated'), WHITE, out=68.4), Lb('A CURE EXISTED', 0, 0.1, 6.3, 4.2, T('cure')),
     Lb('THEY JUST WATCHED', 0, 5.3, 7.3, 4.6, T('see'), WHITE)],
    cam=[(58.5, -2, 2.7, -9, .1, 0), (61.6, 0, 1.9, 1.2, 0, .1), (65.2, 0, 1.75, 3.2, 0, .09), (68.2, .3, 1.65, 3.6, 0, .08), (71.3, -.3, 1.7, 3.0, 0, .09)])

# ------------------------------------------------------------------ 6. Guatemala (71.3 - 79.8)
GT = K.flag_gt(); HOSP = K.hospital(); SYR = K.syringe(); PRISON = art.prison()
S_GUAT = dict(t=71.3, world=world((.62, .55, .40), (.32, .55, .72), (.96, .86, .60), (.90, .82, .62)), items=
    [flagback(GT, .92, 5)] + clouds(3) + [I(PRISON, -5.2, 13, 9.5, t=71.4), I(HOSP, 5.4, 13.5, 9.5, t=71.5)] + [I(art.palm(), x, z, 3.2, t=71.5 + i * .05, sway=.08) for i, (x, z) in enumerate(((-9.5, 9), (9.8, 8.5), (-0.4, 15), (-7.5, 4), (7.8, 3.6)))] +
    [I(DOC, -.75, 7.5, pw(DOC, 1.8), t=T('researchers'), bob=.01), I(DOC2, .8, 7.5, pw(DOC2, 1.8), t=T('researchers') + .1, bob=.01), I(SYR, 0, 7.2, 3.0, y=2.5, t=T('infected'), a='drop', sh=0)] +
    [I(PRISONER, -3.4 + i * .62, 8.4, pw(PRISONER, 1.74), t=T('prisoners') + i * .06, bob=.01) for i in range(3)] + [I(GTWOMAN[i], 2.2 + i * .62, 8.4, pw(GTWOMAN[i], 1.62), t=T('women') + i * .06, bob=.01) for i in range(3)] +
    [I(PATIENT, -1.0 + i * 1.0, 9.4, pw(PATIENT, 1.7), t=T('mental') + i * .06, bob=.01) for i in range(3)] +
    [Lb('GUATEMALA', 0, 5.8, 7.3, 4.2, T('guatemala')), Lb('1946 – 1948', 0, 5.0, 7.3, 2.8, T('forties'), WHITE, a='pop'), Lb('PRISONERS', -2.8, 2.05, 8.3, 1.7, T('prisoners') + .15, WHITE, a='pop', anchor=True), Lb('WOMEN', 2.8, 1.95, 8.3, 1.2, T('women') + .15, WHITE, a='pop', anchor=True),
     Lb('MENTAL PATIENTS', 0, 2.05, 9.3, 2.4, T('mental') + .2, WHITE, a='pop', anchor=True), Lb('INFECTED ON PURPOSE', 0, 0.1, 6.6, 5.0, T('purpose'))],
    cam=[(71.3, 2, 2.8, -9, -.1, -.02), (74.6, 0, 1.9, 1.6, 0, .09), (79.8, 0, 1.8, 3.4, 0, .09)])

# ------------------------------------------------------------------ 7. San Francisco, 1950 (79.8 - 94.1)
BRIDGE = K.bridge(); SHIP = K.ship(); HILLS = K.hills(); BED = K.bed(); BED_E = K.bed(occupied=False, sheet=(.25, .25, .27)); PUFFS = [K.puff(i) for i in range(5)]
DOCK = K.cut([('p', [(0, 0), (1, 0), (1, 1), (0, 1)])], 1200, 700, (.36, .34, .32), 9)
ts = T('sprayed'); tw = T('weeks'); te = T('eleven')
def ship_fn(t, cam):
    if t > tw + .2: return []
    x = lerp(-9, 3, seg(t, 79.8, tw)); out = [Card(SHIP, x, 17, 13, y=-.25 + .12 * math.sin(t * 1.2), tilt=smooth(seg(t, tw - .2, tw + .2)) * pi / 2, shadow=.4)]
    for i in range(46):
        r = np.random.default_rng(700 + i); t0 = ts + i * .11; dt = t - t0
        if dt <= 0: continue
        k = 1 - math.exp(-dt * .5); sx = lerp(-9, 3, seg(t0, 79.8, tw))
        out.append(Card(PUFFS[i % 5], lerp(sx, r.uniform(-18, 18), k), lerp(17, r.uniform(26, 52), k), 2.5 + 6 * k, y=lerp(2.5, r.uniform(3, 11), k), shadow=0, alpha=.75 * (1 - seg(t, tw - .5, tw + .2)), blur=2))
    return out
_beds = [(-2.75 + i * 1.1, 9.4) for i in range(6)] + [(-2.2 + i * 1.1, 8.0) for i in range(5)]
S_SF = dict(t=79.8, world=world(None, (.48, .58, .68), (.94, .90, .82), (.86, .86, .84), fog_d=48, tile=14.0, gtex=K.water_tex()), fns=[ship_fn], items=
    [I(HILLS, 0, 70, 170, sh=0, blur=1.2), I(BRIDGE, -6, 46, 66, sh=0, blur=.8)] + clouds(5, .85) + [I(art3d.bird(), -6 + i * 2.0, 26, 1.2, y=12 + math.sin(i * 2.0), sh=0, fog=False, drift=(1.6, 0, 0)) for i in range(6)] +
    [I(DOCK, 0, 3.6, 18, flat=True, t=tw - .1, a='fade', sh=0), I(HOSP, 0, 14.5, 13, t=tw)] + [I(BED, x, z, 1.04, t=te + i * .11) for i, (x, z) in enumerate(_beds) if i != 8] +
    [I(BED, _beds[8][0], _beds[8][1], 1.04, t=te + 8 * .11, out=T('died', 3) - .15), I(BED_E, _beds[8][0], _beds[8][1], 1.04, t=T('died', 3) + .1), I(NURSE, -3.6, 9.6, pw(NURSE, 1.7), t=T('hospital'), bob=.01), I(DOC, 3.6, 9.6, pw(DOC, 1.8), t=T('hospital') + .1, bob=.01),
     Lb('SAN FRANCISCO', 0, 5.9, 7.3, 4.6, T('san'), out=84.6), Lb('THE NAVY SPRAYED BACTERIA', 0, 0.3, 6.6, 5.4, ts, out=87.9), Lb('A SECRET GERM-WARFARE TEST', 0, 5.9, 7.3, 5.4, T('biological'), WHITE, out=87.9),
     Lb('WEEKS LATER', 0, 5.6, 7.3, 3.2, tw + .3, WHITE, a='pop'), Lb('11 PATIENTS', 0, 4.7, 7.3, 3.6, te, out=92.6), Lb('ONE RARE INFECTION', 0, 0.1, 5.9, 4.4, T('rare'), out=92.6), Lb('ONE OF THEM DIED', 0, 0.1, 5.9, 4.4, T('died', 3))],
    cam=[(79.8, 0, 3.0, -6, 0, -.02), (84.2, 0, 2.5, -.5, 0, .04), (87.7, 0, 3.4, 2.5, 0, .0), (88.6, 0, 3.6, .6, 0, -.10), (94.1, 0, 3.3, 2.6, 0, -.16)])

# ------------------------------------------------------------------ 8. MKUltra (94.1 - 104.2)
SEAL = K.cia_seal(); CAB = K.cabinet(); SUBJ = K.chair_subject(); FIRE = K.flames(); TRIP = art.rays(1400, 16, np.array([.85, .25, .75], np.float32), .8); TRIP2 = art.rays(1400, 11, np.array([.95, .85, .2], np.float32), .7)
LABWALL = art3d.wall(1400, 900, (.16, .22, .21), 8); PAPERS = [fitw(art.doc(seed=i), 240) for i in range(3)]; BLOT = [K.cut([('p', [(0, 0), (1, 0), (1, 1), (0, 1)])], 120, 120, c, 3 + i, 3) for i, c in enumerate(((.9, .3, .7), (.3, .8, .9), (.95, .85, .3)))]
td = T('destroyed')
S_MK = dict(t=94.1, world=world((.30, .34, .33), (.04, .07, .08), (.16, .20, .20), (.12, .16, .16), fog_d=50), fns=[fall(BLOT, T('l'), 100.2, 26, 5, (-3.5, 3.5, 5, 9.5), 7, .22, 2.2), fall(PAPERS, T('files') - .2, 104.0, 30, 6, (-3.5, 3.5, 5.5, 9), 8, .55, 3.0)], items=
    [I(LABWALL, 0, 12, 26), I(SEAL, 0, 11.9, 3.6, y=5.6, t=T('c'), a='grow', sh=0)] + [I(CAB, sx * (4.4 + (i % 2) * .0), 6.5 + i * 1.3, 1.1, t=94.2 + i * .05, quiet=True) for i in range(4) for sx in (-1, 1)] +
    [I(AGENT, -2.7, 8.6, pw(AGENT, 1.82), t=T('secretly'), bob=.01, out=100.4), I(AGENT, 2.7, 8.6, pw(AGENT, 1.82), t=T('secretly') + .1, bob=.01, out=100.4), I(DOC2, 1.6, 9.2, pw(DOC2, 1.8), t=T('secretly') + .2, bob=.01, out=100.4),
     I(TRIP, 0, 8.7, 8.0, y=-2.2, t=T('l'), a='grow', sh=0, fog=False, alpha=.85, out=100.4), I(TRIP2, 0, 8.65, 5.4, y=-.9, t=T('s', 1) if False else T('l') + .25, a='grow', sh=0, fog=False, alpha=.8, out=100.4),
     I(SUBJ, 0, 8.0, 1.25, t=T('people', 5), out=100.4), I(K.flask(liquid=(.75, .3, .8)), -1.5, 7.6, .45, y=0, t=T('drugged'), out=100.4),
     I(FIRE, 0, 7.4, 3.2, t=td - .1, a='grow', sh=0, fog=False, bob=.08), I(FIRE, .3, 7.5, 2.2, y=.2, t=td, a='grow', sh=0, fog=False, bob=.12, alpha=.9),
     Lb('THE CIA', 0, 5.8, 7.3, 2.6, T('c'), WHITE, out=98.9), Lb('SECRETLY DRUGGED PEOPLE', 0, 4.6, 7.3, 5.0, T('drugged'), out=98.9), Lb('WITH LSD', 0, 0.1, 6.6, 3.2, T('l'), out=100.4),
     Lb('PROJECT MKULTRA', 0, 5.8, 7.3, 4.8, T('m'), out=100.4), Lb('1973', 0, 5.8, 7.3, 2.2, T('seventy', 2), WHITE), Lb('FILES DESTROYED', 0, 4.6, 7.3, 4.4, td)],
    cam=[(94.1, -1.5, 2.4, -7, .08, .03), (97.2, 0, 1.8, 2.4, 0, .1), (100.4, .2, 1.7, 3.6, 0, .09), (104.2, 0, 1.9, 2.6, 0, .09)])

# ------------------------------------------------------------------ 9. Goldsboro, 1961 (104.2 - 114.4)
B52 = K.b52(); BOMB = K.bomb(); CHUTE = K.chute(); PANEL = K.panel(3); BARN = K.barn(); FARM = art.house(col=(.86, .84, .78))
tdr = T('dropped'); tsw = T('one', 3)
def plane(t, cam):
    out = []; x = lerp(-34, 9, seg(t, 105.4, 108.6)); y = 13 - 2.5 * seg(t, 107.2, 108.6)
    if 105.4 < t < 110.6: out.append(Card(B52, x, 24, 17, y=y, shadow=0, fog=False));
    if 107.0 < t < 110.6: out.append(Card(FIRE, x + 2, 23.9, 3.2, y=y + .6, shadow=0, fog=False))
    if t > tdr and t < tsw + .2:
        k = seg(t, tdr, 110.4); y1 = lerp(11, 1.4, eout(k, 2))
        out += [Card(CHUTE, -1.7 + .15 * math.sin(t * 2), 9.0, 2.2, y=y1 + 1.7, shadow=0), Card(BOMB, -1.7 + .15 * math.sin(t * 2), 9.0, .7, y=y1, shadow=.4)]
        k2 = seg(t, T('two', 3), T('two', 3) + .9); out.append(Card(BOMB, 2.1, 9.6, .7, y=lerp(12, -.7, k2 * k2), shadow=.4))
    return out
def gold_extra(img, cam, t): dust(img, cam, (2.1, .2, 9.5), t, T('two', 3) + .9, col=(.30, .24, .16), n=50, seed=8, speed=4.0)
STARS = np.zeros((500, 1400, 4), np.float32)
for _i in range(160): cv2.circle(STARS, (int(_r.integers(1400)), int(_r.integers(500))), int(_r.integers(1, 4)), (1, 1, .9, float(_r.uniform(.4, 1))), -1, cv2.LINE_AA)
S_GOLD = dict(t=104.2, world=world((.17, .27, .19), (.02, .04, .11), (.20, .25, .38), (.12, .16, .25), fog_d=60), fns=[plane], extra=gold_extra, items=
    [I(STARS, 0, 110, 230, y=14, sh=0, fog=False), I(art.moon(), 18, 90, 10, y=38, sh=0, fog=False, blur=1)] + clouds(4, .35) + [I(FARM, -5.2, 14, 6, t=104.3), I(BARN, 5.6, 15, 7, t=104.4)] +
    [I((TREES + PINES)[i % 7], x, z, w, t=104.3 + i * .05, sway=.05) for i, (x, z, w) in enumerate(((-10, 11, 6), (10.5, 10, 6), (-1, 18, 7), (-8, 5, 5), (8.4, 4.5, 5), (-13, 20, 8), (13, 21, 8)))] +
    [I(PANEL, 0, 7.0, 3.6, y=.75, t=tsw, a='drop', sh=.4, fog=False),
     Lb('NORTH CAROLINA', 0, 6.0, 7.3, 4.6, T('north'), out=110.6), Lb('DROPPED BY ACCIDENT', 0, 5.1, 7.3, 4.2, T('accidentally') + .3, WHITE, a='pop', out=110.6), Lb('2 HYDROGEN BOMBS', 0, 0.1, 6.6, 5.0, T('hydrogen'), out=110.6),
     Lb('ONE SWITCH', 0, 4.5, 7.3, 3.6, T('switch')), Lb('STOPPED A NUCLEAR EXPLOSION', 0, 0.02, 6.2, 5.2, T('stopped'), WHITE)],
    cam=[(104.2, 0, 2.2, -8, 0, .12), (107.6, 0, 2.0, -2.5, 0, .2), (110.4, 0, 1.9, 1.8, 0, .1), (114.4, 0, 1.8, 2.6, 0, .09)])

# ------------------------------------------------------------------ 10. the apology (114.4 - 122)
PLAQUE = K.plaque(OTA2); FLOWERS = [K.flower(c) for c in ((.95, .93, .88), (.90, .30, .30), (.95, .80, .30))]; C2020 = art.calendar('YEAR', '2020', seed=15)
S_END = dict(t=114.4, world=world((.60, .52, .40), (.14, .20, .34), (.96, .66, .44), (.80, .62, .50)), items=
    [flagback(FLAG, .8, 4)] + clouds(4, .7) + [I(Z.HOUSE, 0, 12.5, 22, t=114.5)] + [I(TREES[i % 4], x, z, 6, t=114.5 + i * .05, sway=.05) for i, (x, z) in enumerate(((-9, 10), (9.3, 9.5), (-7.5, 4), (7.8, 3.6)))] +
    [I(LAMP, sx * 3.6, 7.2, .62, t=114.6) for sx in (-1, 1)] + [I(PLAQUE, 0, 7.8, 2.7, t=T('ota', 2))] + [I(FLOWERS[i % 3], -1.5 + i * .5, 7.3 - .1 * (i % 2), .34, t=T('benga', 2) + i * .07, sway=.03) for i in range(7)] +
    [I(C2020, 2.75, 7.2, 1.35, y=1.2, t=T('twenty', 2), a='slam', sh=0, fog=False, blur=0, face=True, out=120.9),
     Lb('THE ZOO APOLOGIZED', 0, 5.3, 7.3, 4.8, T('apologized'), WHITE, out=120.9), Lb('114 YEARS LATER', 0, 0.1, 6.4, 5.0, T('hundred', 3), out=120.9), Lb('FOLLOW FOR MORE', 0, 0.3, 6.2, 5.2, T('follow'))],
    cam=[(114.4, 0, 3.4, -8, 0, -.05), (118.2, 0, 1.9, 2.2, 0, .1), (122.0, 0, 1.8, 3.4, 0, .09)])

SCENES = [S_ZOO, S_SIXTY, S_MAIL, S_PROH, S_COURT, S_TUSK, S_GUAT, S_SF, S_MK, S_GOLD, S_END]


def sfx(add):
    SR = film.SR; n = int(.5 * SR); tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / .12) * .5 + np.sin(2 * np.pi * 1210 * tt) * np.exp(-tt / .07) * .3, T('zoo'), 0.10); add(film.thump(60, 30, 1.0, .3), T('zoo'), 0.28); add(film.riser(.9), T('zoo') - .9, .1)
    for i in range(40): add(film.tick(), T('give') + .1 + i * 4.5 / 40, 0.05)
    m = int(2.6 * SR); t2 = np.arange(m) / SR; add(film._filt(np.random.default_rng(1).normal(0, 1, m), 60, 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t2)) * np.exp(-t2 / 1.6), T('to', 2) - .3, 0.07)   # train
    for i in range(12): add(film.thump(120, 60, .2, .05), T('ten') + i * .1, 0.03)
    for th in (T('ruling'), T('ruled')): add(film.thump(140, 70, .3, .06), th, 0.12)
    f = film._filt(np.random.default_rng(2).normal(0, 1, int(3 * SR)), 300, 4000); add(f * (0.5 + 0.5 * np.random.default_rng(3).random(len(f))) * np.minimum(1, np.arange(len(f)) / SR), T('destroyed') - .1, 0.035)           # fire
    p = int(4.5 * SR); t3 = np.arange(p) / SR; add(film._filt(np.random.default_rng(4).normal(0, 1, p), 50, 400) * np.sin(np.pi * t3 / 4.5), 105.4, 0.09)                                                              # bomber
    w = int(.9 * SR); t4 = np.arange(w) / SR; add(np.sin(2 * np.pi * np.cumsum(1400 - 900 * t4 / .9) / SR) * np.sin(np.pi * t4 / .9) * .5, T('two', 3), 0.05); add(film.thump(55, 28, 1.0, .3), T('two', 3) + .9, 0.26)
    s = int(3 * SR); t5 = np.arange(s) / SR; add(film._filt(np.random.default_rng(5).normal(0, 1, s), 800, 5000) * np.sin(np.pi * t5 / 3) ** 2, T('sprayed'), 0.03)                                                     # spray hiss


SHOW = Show3(SCENES, DUR, VOICE, sfx_extra=sfx)
if __name__ == '__main__': run(SHOW, sys.argv)
