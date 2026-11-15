"""Bhopal 1984 - 20-second sample: crane camera (sky -> street -> sky), 2.5D photo reliefs, Hinglish captions.
Usage: python3 sample.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, json, subprocess, glob, wave as wavmod
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Cam3, Card, World, dust
from voxkit.cine import *

VOICE = os.path.join(HERE, 'voice', 'full.mp3'); T = film.timeline(json.load(open(os.path.join(HERE, 'voice', 'words.json')))); PH = os.path.join(HERE, 'photos', 'wm')
DUR = 21.0; CUTS = [T('aur') - .05, T('mujhe') - .05, 15.42]; X2, X3, X4 = 300.0, 600.0, 900.0     # each set lives at its own x offset


def R(name, w=900, **kw):
    f = [p for p in glob.glob(os.path.join(PH, name + '.*')) if not p.endswith('.svg')]
    return Relief(f[0], w=w, seed=len(name), **kw)
PLANT = [R('bhopal_plant_13'), R('bhopal_plant_3'), R('bhopal_plant_7'), R('union_carbide_pesticide_factory_bhopal_i', sat=1.0, tone=(1, 1, 1))]
MEMORIAL = R('memorial_statue_1985'); PLAQUE = R('bhopal_disaster_plaque_in_greyfriars_kir', pop=False); PROTEST = [R('dow_chemical_banner_bhopal'), R('dow_chemical_banner_bhopal_india')]
SLUM = [R('slum_in_bhopal'), R('slum_in_bhopal_town')]; MOSQUE = [R('taj_ul_masajid_bhopal'), R('taj_ul_masajid_and_its_reflection_bhopal')]; MAPMP = R('india_madhya_pradesh_relief_map_tag', pop=False)
CITY = [R(n) for n in ('bada_talab_in_bhopal', 'city_of_lakes_bhopal', 'bhopal_junction_railway_station', 'bhopal_landscape', '_a_gateway_bhopal_painting_published_in_', '_the_upper_lake_bhopal_painting_publishe', 'bhojtal_with_manuabhan_tekri_in_the_back', 'platform_no_1_bhopal_railway_station_1_')]
MIC = R('methyl_isocyanate_3d_spacefill', pop=False); ALL = PLANT + [MEMORIAL, PLAQUE] + PROTEST + SLUM + MOSQUE + [MAPMP, MIC] + CITY

# ------------------------------------------------------------------ drawn set pieces
def plant(w=2400, h=1100):
    parts = [('p', [(0, .62), (1, .62), (1, 1), (0, 1)]), ('p', [(.05, .40), (.30, .40), (.30, .62), (.05, .62)]), ('p', [(.62, .34), (.90, .34), (.90, .62), (.62, .62)])]
    for x, top in ((.36, .12), (.44, .22), (.52, .05), (.94, .2), (.02, .28)): parts.append(('p', [(x, top), (x + .028, top), (x + .034, .62), (x - .006, .62)]))
    for x in (.12, .2, .72, .8): parts += [('e', x, .40, .05, .09)]
    s = K.cut(parts, w, h, (.20, .22, .26), 601)
    for x in (.12, .2, .72, .8): K.paint(s, [('e', x, .42, .04, .06)], (.30, .32, .36))
    for y in (.5, .56, .7): K.paint(s, [('l', 0, y, 1, y, 5)], (.34, .30, .26))
    for i in range(26):
        r = np.random.default_rng(i); x = r.uniform(.03, .95); y = r.uniform(.66, .92); K.paint(s, [('p', [(x, y), (x + .016, y), (x + .016, y + .035), (x, y + .035)])], (.98, .80, .40) if i % 3 else (.10, .10, .12))
    for x, top in ((.36, .12), (.52, .05)): K.paint(s, [('e', x + .014, top + .012, .012, .018)], (.95, .30, .15))
    t = text_sprite('UNION CARBIDE', 90, np.float32([.92, .88, .78]), pad=4, distress=.2, seed=4); k = w * .26 / t.shape[1]; t = cv2.resize(t, None, fx=k, fy=k); art.paste(s, t, int(w * .06), int(h * .455)); return s


def shanty(seed, lit=True, w=420, h=360):
    r = np.random.default_rng(seed); c = np.float32([(.34, .28, .24), (.26, .30, .34), (.36, .32, .22), (.30, .24, .26)][seed % 4])
    s = K.cut([('p', [(.06, .34), (.94, .34), (.94, 1), (.06, 1)]), ('p', [(0, .38), (.1, .14 + .1 * (seed % 2)), (.9, .08 + .12 * ((seed + 1) % 2)), (1, .38)])], w, h, c, 610 + seed, 3)
    K.paint(s, [('p', [(0, .38), (.1, .14 + .1 * (seed % 2)), (.9, .08 + .12 * ((seed + 1) % 2)), (1, .38)])], c * .6)
    K.paint(s, [('p', [(.14, .52), (.36, .52), (.36, .78), (.14, .78)])], (1.0, .78, .36) if lit else (.07, .07, .09)); K.paint(s, [('p', [(.56, .5), (.78, .5), (.78, 1), (.56, 1)])], (.10, .08, .08)); return s


def mosque(w=1600, h=900):
    parts = [('p', [(.12, .6), (.88, .6), (.88, 1), (.12, 1)])] + [('e', x, .58, r, r * 1.5) for x, r in ((.5, .13), (.28, .09), (.72, .09))]
    for x in (.04, .94): parts += [('p', [(x, .1), (x + .03, .1), (x + .035, 1), (x - .005, 1)]), ('e', x + .015, .09, .028, .04)]
    return K.cut(parts, w, h, (.10, .11, .17), 620, 3)


def india(w=1500, h=1500):
    P = [(74, 37), (78, 36.6), (80, 35.5), (79, 32.5), (78.5, 31), (81, 30), (84, 28.5), (88, 27.8), (89, 26.7), (92, 27.5), (96, 29.3), (97.3, 28), (95, 26), (94.5, 24), (93, 22), (92.3, 23.5), (91.3, 24), (92, 25.2), (89.8, 25.3), (88.3, 24.5),
         (89, 22), (87, 21.5), (85, 19.5), (82.3, 16.7), (80.2, 15.5), (80.3, 13), (79.8, 10.3), (77.5, 8.1), (76.3, 9.5), (74.8, 13), (73, 17), (72.7, 21), (70.5, 20.8), (68.8, 22.5), (68.3, 23.7), (71, 24.5), (70, 27.5), (72.5, 30), (74.5, 31.5), (73.8, 33), (73, 34.5)]
    s = K.cut([('p', [((lo - 67) / 31.5, (37.5 - la) / 30.5) for lo, la in P])], w, h, (.78, .62, .36), 630, 7); return s
BX, BY = (77.4 - 67) / 31.5, (37.5 - 23.3) / 30.5                                             # Bhopal on the map (fractions)


def chair(w=420, h=640):
    s = K.cut([('p', [(.14, .0), (.86, .0), (.86, .58), (.14, .58)]), ('p', [(.08, .52), (.92, .52), (.92, .64), (.08, .64)]), ('p', [(.1, .64), (.2, .64), (.2, 1), (.1, 1)]), ('p', [(.8, .64), (.9, .64), (.9, 1), (.8, 1)])], w, h, (.40, .26, .16), 640, 3)
    K.paint(s, [('p', [(.22, .06), (.78, .06), (.78, .5), (.22, .5)])], (.50, .14, .12)); return s


def boss(w=700, h=1500):
    s = K.cut([('p', [(.16, .3), (.84, .3), (.9, 1), (.1, 1)]), ('e', .5, .17, .15, .11), ('p', [(.4, .25), (.6, .25), (.6, .32), (.4, .32)])], w, h, (.09, .09, .11), 650, 5)
    K.paint(s, [('p', [(.44, .3), (.56, .3), (.5, .62)])], (.85, .83, .78)); K.paint(s, [('p', [(.47, .31), (.53, .31), (.52, .56), (.5, .6), (.48, .56)])], (.55, .10, .10))
    q = text_sprite('?', 300, np.float32([.92, .88, .78]), pad=4, distress=.2, seed=3); k = h * .16 / q.shape[0]; q = cv2.resize(q, None, fx=k, fy=k); art.paste(s, q, int(w / 2 - q.shape[1] / 2), int(h * .09)); return s


def dial(s=600, mode='60'):
    c = np.zeros((int(s * 1.2), s, 4), np.float32); cy = int(s * .68)
    cv2.rectangle(c, (s // 2 - 28, int(s * .04)), (s // 2 + 28, int(s * .22)), (.75, .60, .25, 1), -1); cv2.circle(c, (s // 2, cy), int(s * .47), (.75, .60, .25, 1), -1, cv2.LINE_AA); cv2.circle(c, (s // 2, cy), int(s * .40), (.93, .89, .78, 1), -1, cv2.LINE_AA)
    for i in range(12): a = i * pi / 6; cv2.line(c, (int(s / 2 + s * .33 * math.sin(a)), int(cy - s * .33 * math.cos(a))), (int(s / 2 + s * .38 * math.sin(a)), int(cy - s * .38 * math.cos(a))), (.1, .08, .07, 1), 7, cv2.LINE_AA)
    if mode == '60':
        ts = text_sprite('60', 190, np.float32([.12, .10, .08]), pad=4, distress=.2, seed=2); k = s * .42 / ts.shape[1]; ts = cv2.resize(ts, None, fx=k, fy=k); art.paste(c, ts, (s - ts.shape[1]) // 2, cy - ts.shape[0] // 2)
    else:                                                                                   # a clock a few minutes before midnight
        for a, L, th in ((2 * pi * 11.9 / 12, .2, 14), (2 * pi * 54 / 60, .31, 9)): cv2.line(c, (s // 2, cy), (int(s / 2 + s * L * math.sin(a)), int(cy - s * L * math.cos(a))), (.1, .08, .07, 1), th, cv2.LINE_AA)
        cv2.circle(c, (s // 2, cy), 14, (.7, .15, .1, 1), -1, cv2.LINE_AA)
    return c


def night_sky(seed=1):
    s = art3d.sky((.015, .02, .06), (.13, .16, .30), seed); r = np.random.default_rng(seed)
    for i in range(260): x, y = int(r.integers(W)), int(r.integers(int(H * .8))); cv2.circle(s, (x, y), int(r.integers(1, 3)), tuple(float(v) for v in np.float32([1, .95, .85]) * r.uniform(.3, .9)), -1, cv2.LINE_AA)
    return s


PLANTS = plant(); SH_L = [shanty(i, True) for i in range(8)]; SH_D = [shanty(i, False) for i in range(8)]; MOSQ = mosque(); INDIA = india(); CHAIR = chair(); BOSS = boss(); STOPW = dial(); CLOCK = dial(mode='clock'); MOON = art.moon()
SKYL = tint(art3d.skyline_old(seed=3), (.30, .34, .50)); COURT = tint(K.courthouse(), (.62, .62, .72)); GAVEL = art.gavel(); PIN = K.mappin(); PUFFS = [K.puff(i, col=(.74, .80, .30)) for i in range(5)]; CLOUD = [tint(art3d.cloud(i), (.42, .46, .62)) for i in range(4)]
WN = World(art3d.ground_tex(col=(.24, .23, .27), seed=3), night_sky(), fog=(.09, .10, .17), fog_d=110, focus=20, dof=14)
WC = World(art3d.ground_tex(col=(.30, .29, .30), seed=4), night_sky(2), fog=(.10, .10, .16), fog_d=90, focus=12, dof=14)
WM = World(paper(1024, 1024, np.float32([.10, .16, .24]), 5, .05, .15), night_sky(3), fog=(.09, .10, .17), fog_d=140, focus=30, dof=10)
rng = np.random.default_rng(5)
HUTS = [(x + float(rng.uniform(-.8, .8)), z + float(rng.uniform(-.8, .8)), int(rng.integers(8))) for z in (8, 13, 18, 23, 28) for x in np.arange(-24, 24.1, 4.8)]


# ------------------------------------------------------------------ cameras: up in the sky, down to the street, up again
def cam_at(t):
    if t < CUTS[0]:                                                          # the sky above Bhopal -> dive over the roofs to the plant
        return path(t, [(0, (0, 62, -40), (0, 0, 20)), (1.5, (-9, 44, -27), (0, 0, 22)), (2.9, (-12, 24, -14), (0, 2, 24)), (5.2, (4, 8, -2), (0, 5, 36)), (CUTS[0], (9, 2.4, 11), (-2, 8, 42))])
    if t < CUTS[1]:                                                          # straight down on the empty chair -> swing up to the court
        return path(t, [(CUTS[0], (X2 + .5, 15, 8), (X2, 0, 12)), (8.9, (X2 - 3, 9, 2), (X2, 2, 16)), (CUTS[1], (X2 - 5, 2.6, -2), (X2 + 1, 9, 34))])
    if t < CUTS[2]:                                                          # rising through a tower of photographs
        k = seg(t, CUTS[1], CUTS[2]); a = lerp(-.5, 2.9, smooth(k)); y = lerp(2.5, 38, smooth(k))
        return look(X3, y, 12, X3 + math.sin(a) * 10, y + lerp(3.5, -1.5, k), 12 + math.cos(a) * 10)
    return path(t, [(CUTS[2], (X4, 120, 24), (X4, 0, 40)), (17.2, (X4 + 2, 52, 16), (X4, 0, 40)), (19.1, (X4 - 4, 11, 12), (X4, 4, 46)), (DUR, (X4 - 7, 3.0, 22), (X4 + 1, 8, 62))])


def focus_at(t):
    if t < CUTS[0]: return lerp(70, 22, smooth(seg(t, 0, 5)))
    if t < CUTS[1]: return lerp(22, 16, smooth(seg(t, CUTS[0], CUTS[1])))
    if t < CUTS[2]: return 8
    return lerp(100, 26, smooth(seg(t, CUTS[2], 19.5)))


def drop(Rl, C, x, y, z, w, t, t0, yaw=0.0, ph=0.0, tilt=0.0, **kw):
    """A photo relief that falls in from the sky and settles."""
    if t < t0: return
    Rl.add(C, x, y + (1 - eout(seg(t, t0, t0 + .9), 3)) * 45, z, w, yaw=yaw, t=t, ph=ph, tilt=tilt, **kw)


def cards(t, cam):
    C = []; A = C.append; fy = -cam.yaw
    if t < CUTS[0]:
        A(Card(SKYL, 0, 150, 300, blur=1.2)); A(Card(MOSQ, -52, 120, 70, blur=.9)); A(Card(MOON, 34, 160, 16, y=62, shadow=0, fog=False))
        for i in range(7): A(Card(CLOUD[i % 4], -70 + (t * 2.5 + i * 23) % 140, 20 + i * 14, 34, y=40 + 9 * math.sin(i * 2.1), shadow=0, alpha=.55, blur=2.5))
        A(Card(PLANTS, 0, 44, 46, tilt=up(t, .05, .6) or 0, shadow=.4))
        gas = T('zehreeli'); gk = seg(t, gas, CUTS[0] + .5)
        for i, (x, z, k) in enumerate(HUTS):
            tl = up(t, .2 + (30 - z) * .02 + abs(x) * .008, .45)
            if tl is None: continue
            dark = gk * 52 > (44 - z) + abs(x) * .5                                              # the lights go out as the cloud arrives
            A(Card((SH_D if dark else SH_L)[k], x, z, 3.6, tilt=tl, shadow=.5))
        for i in range(46):                                                                    # the gas: heavier than air, it rolls along the ground
            r = np.random.default_rng(300 + i); a = r.uniform(-1.25, 1.25); d = gk * r.uniform(18, 46)
            if gk > 0: A(Card(PUFFS[i % 5], math.sin(a) * d + 1.5 * math.sin(t * .6 + i), 44 - math.cos(a) * d, r.uniform(8, 14) * (.5 + gk), y=r.uniform(-1.5, 1.2) + .4 * math.sin(t + i), shadow=0, alpha=.34 * min(1, gk * 5), blur=1.6, fog=False))
        # photographs hanging in the sky on the way down, then huge ones dropping in behind the plant
        for i, (Rl, x, y, z, w) in enumerate(((PLANT[3], -10, 36, -14, 13), (CITY[1], 9, 30, -8, 12), (MOSQUE[0], -17, 24, 0, 11), (CITY[0], 15, 20, 4, 11), (SLUM[0], -14, 13, 9, 9), (CITY[3], 15, 10, 14, 9), (PROTEST[0], 0, 26, 6, 10))):
            Rl.add(C, x, y, z, w, yaw=-.5 if x < 0 else .5, t=t, ph=i * 1.7, tilt=.55, fog=False)
        drop(PLANT[0], C, -24, 13, 62, 30, t, 3.1, ph=1); drop(PLANT[1], C, 25, 12, 60, 22, t, 3.6, ph=2); drop(MEMORIAL, C, 2, 22, 70, 22, t, T('hazaaron'), ph=3); drop(PLANT[2], C, -6, 2.5, 30, 9, t, 4.4, ph=4, yaw=.3)
        drop(SLUM[1], C, 13, 3, 24, 9, t, 5.4, ph=5, yaw=-.4)
        caps(C, cam, t, [('KYA AAP JAANTE HAIN?', WHITE, .05, T('unnees') - .1, .14), (cal('YEAR', 1984), None, T('unnees'), T('ek') - .1, .27, .28), ('EK RAAT', WHITE, T('ek'), T('zehreeli') - .1, .14, .5),
                         ('ZEHREELI GAS', BURNT, T('zehreeli'), None, .14), ('HAZAARON LOGON KO', WHITE, T('hazaaron'), T('neend') - .08, .215, .64), ('NEEND MEIN HI MAAR DIYA', WHITE, T('neend'), None, .215, .74)])
    elif t < CUTS[1]:
        A(Card(SKYL, X2, 150, 300, blur=1.2)); A(Card(MOON, X2 - 30, 150, 14, y=60, shadow=0, fog=False))
        A(Card(COURT, X2, 36, 34, tilt=up(t, CUTS[0] + .05, .5) or 0, shadow=.4)); giant(C, BOSS, X2 + 2, 60, 22, t, T('maalik') - .2, 1.6, ph=1, blur=.8)
        A(Card(CHAIR, X2, 12, 3.4, shadow=.6, yaw=fy * .5))
        for i in range(10): A(Card(art3d.lamp(), X2 + (-1) ** i * 6, 4 + (i // 2) * 6, .8, shadow=.4)) if False else None
        hang(C, GAVEL, X2 + 3.5, 15, 4.2, 5.0, t, T('court') - .15, ph=1.1, swing=.5, yaw=fy * .7)
        for i, (Rl, x, y, z, w) in enumerate(((PROTEST[0], -10, 4, 22, 9), (PROTEST[1], 10.5, 5, 24, 9), (PLAQUE, -7, 11, 28, 7), (PLANT[3], 8, 12, 30, 8))): drop(Rl, C, X2 + x, y, z, w, t, CUTS[0] + .3 + i * .25, ph=i * 1.9, yaw=-.35 if x > 0 else .35)
        caps(C, cam, t, [('COMPANY KA MAALIK', BURNT, T('company'), None, .14), ('KABHI COURT TAK NAHI PAHUNCHA', WHITE, T('kabhi'), None, .215, .86)])
    elif t < CUTS[2]:
        for i in range(34):                                                                    # the tower of photographs
            a = i * 2.39996; y = 1.0 + i * 1.18; rr = 8.5 + 1.5 * math.sin(i * 1.3); Rl = ALL[i % len(ALL)]
            Rl.add(C, X3 + math.sin(a) * rr, y, 12 + math.cos(a) * rr, 5.6 + 1.2 * (i % 3), yaw=a + .25 * math.sin(t * .4 + i), t=t, ph=i * 1.1, fog=False, drift=.2)
        for i in range(6): A(Card(CLOUD[i % 4], X3 - 40 + (t * 3 + i * 17) % 80, 50 + i * 8, 30, y=10 + i * 6, shadow=0, alpha=.4, blur=2.5))
        caps(C, cam, t, [('MUJHE SIRF 60 SECOND DIJIYE', WHITE, T('mujhe'), T('main') - .1, .14, .86), (STOPW, None, T('saath') - .1, T('yeh') - .1, .3, .3), ('YEH KAISE HUA?', BURNT, T('yeh'), None, .14)])
    else:
        mw = 150.0; mh = mw; z0 = 40 - (1 - BY) * mh; x0 = X4 + (.5 - BX) * mw                    # the map lies on the ground with Bhopal at (X4, 40)
        A(Card(INDIA, x0, z0, mw, y=.02, tilt=pi / 2 * .999, shadow=0, fog=False))
        A(Card(PIN, X4, 40, 5 * (1 + .1 * math.sin(t * 5)), y=0, yaw=fy, tilt=-cam.pitch * .6, shadow=.5, fog=False)) if t < 19.4 else None
        A(Card(MOON, X4 + 28, 190, 18, y=44, shadow=0, fog=False)); t1 = 17.6
        tl = up(t, t1, .6)
        if tl is not None: A(Card(SKYL, X4, 150, 260, tilt=tl, blur=1.0)); A(Card(MOSQ, X4 + 16, 96, 60, tilt=tl, blur=.6)); A(Card(PLANTS, X4 - 20, 80, 44, tilt=tl, shadow=.3))
        for i, (x, z, k) in enumerate(HUTS):
            tl = up(t, t1 + .2 + i * .012, .4)
            if tl is not None: A(Card(SH_L[k], X4 + x * 1.3, 48 + z * 1.1, 3.8, tilt=tl, shadow=.5))
        for i, (Rl, x, y, z, w) in enumerate(((MAPMP, -9, 30, 14, 12), (MOSQUE[1], 12, 22, 20, 9), (CITY[0], -15, 13, 36, 11), (CITY[2], 14, 9, 44, 10), (MOSQUE[0], -10, 7.5, 56, 10), (CITY[4], 9, 15, 64, 9), (SLUM[0], 0, 17, 76, 13), (CITY[7], -18, 4, 46, 7), (CITY[5], 17, 3.5, 52, 7))):
            drop(Rl, C, X4 + x, y, z, w, t, 16.0 + i * .3, ph=i * 1.7, yaw=-.3 if x > 0 else .3, tilt=.5 * (1 - smooth(seg(t, 18.2, 19.6))))
        hang(C, CLOCK, X4 + 2.5, 34, 3.4, 5.5, t, T('aadhi') - .2, ph=.7, swing=.45, yaw=fy * .8)
        caps(C, cam, t, [('BHOPAL', BURNT, T('bhopal'), T('aadhi') - .15, .14, .6), ('2 DECEMBER 1984', WHITE, T('do'), T('aadhi') - .15, .215, .62), ('AADHI RAAT SE THODI DER PEHLE', BURNT, T('aadhi'), None, .14, .88)])
    return C


def render(f):
    t = min(f / FPS, DUR - .001); cam = cam_at(t); pt = t - 1 / FPS; wd = WN if t < CUTS[0] else WC if t < CUTS[1] else WN if t < CUTS[2] else WM; wd.focus = focus_at(t)
    img = wd.render(cam, cards(t, cam), f, t)
    img = atmos(img, cam, t, col=(.8, .85, 1), beam=(.03, .04, .07), fall=-.6, n=50, amt=.3)
    cutk = max(math.exp(-abs(t - c) * 16) for c in CUTS)
    if pt > 0 and not any(pt < c <= t for c in CUTS):
        prev = cam_at(pt); ox = (cam.yaw - prev.yaw) * cam.f; oy = (cam.pitch - prev.pitch) * cam.f
        if abs(ox) + abs(oy) > 4: img = dir_blur(img, ox * .7, -oy * .7)
    if cutk > .08: img = zoom_blur(img, .22 * cutk, 10)
    expo = 1.95 * smooth(seg(t, 0, .5)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2)) * (1 + .25 * cutk) * (1 + .03 * math.sin(t * 11.3) + .02 * math.sin(t * 17.9))
    img = post(img, f, tilt=0.9, expo=expo)
    lum = img.mean(2, keepdims=True); img = np.clip(img * .85 + lum * np.float32([.92, .98, 1.12]) * .15, 0, 1)
    return (img * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); Rn = np.random.default_rng(4)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)
    for c in CUTS: add(film.whoosh(.6, 200, 2400, .55), c - .3, .15)
    add(film.whoosh(2.6, 150, 1400, .5), .2, .07); add(film.whoosh(2.2, 150, 1400, .5), 15.5, .07)                              # the long descents
    hiss = film._filt(Rn.normal(0, 1, int(3.6 * SR)), 2500, 7000); add(hiss * np.minimum(1, np.arange(len(hiss)) / SR) * np.linspace(1, .2, len(hiss)), T('zehreeli'), .03)   # gas
    for tl in (T('unnees'), T('zehreeli'), T('neend'), T('company'), T('kabhi'), T('saath'), T('yeh'), T('bhopal'), T('do'), T('aadhi')): add(film.thump(82, 32, .6, .14), tl, .17); add(film.nburst(.25, 300, 3000, .04), tl, .05)
    m = int(5 * SR); t2 = np.arange(m) / SR
    bell = lambda f0: sum(a * np.sin(2 * np.pi * f0 * k * t2) * np.exp(-t2 / d) for k, a, d in ((1, .5, 2.6), (2, .35, 1.8), (2.38, .2, 1.2), (3, .16, .9), (.5, .3, 3.2)))
    add(bell(147), T('neend'), .08); add(bell(196), T('aadhi'), .08)
    for i in range(3): add(film.thump(180, 90, .5, .08), T('court') + i * .22, .10)
    for i in range(12): add(film.tick() if hasattr(film, 'tick') else film.nburst(.03, 2000, 6000, .01), T('saath') + i * .25, .04)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.3 * SR):] *= np.linspace(1, 0, int(.3 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (360, 640), interpolation=cv2.INTER_AREA)[..., ::-1])
    else:
        out = sys.argv[2]; sfx = out + '.sfx.wav'; soundtrack(sfx)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-t', str(DUR), '-i', VOICE, '-i', sfx,
                               '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={DUR - .25}:d=0.25,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
