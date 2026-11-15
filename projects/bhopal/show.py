"""Bhopal 1984 - full video (Documentary Template 2). Usage: python3 show.py stills <dir> t1,t2 | render <outdir> [a-b] | mux <outdir> <out.mp4>"""
import sys, os, math, json, subprocess, glob, wave as wavmod, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K, world7 as V7
from voxkit.pop3d import Card, World
from voxkit.cine import look, pin, tint, hang, pi
from voxkit.collage import *

_sp = importlib.util.spec_from_file_location('s3', os.path.join(HERE, 'sample3.py')); S3 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S3); S = S3.S
T = S.T; RAWW = S.WORDS; load = S.load; WD = S.WD; DUR = 106.27
NUMW = {('unnees', 'sau', 'chauraasi'): '1984', ('do', 'december'): '2 December', ('saath', 'second'): '60 second', ('teen', 'hazaar', 'aath', 'sau'): '3,800', ('aath', 'hazaar'): '8,000', ('paanch', 'lakh'): '5 lakh',
        ('do', 'hazaar', 'chaudah'): '2014', ('unnees', 'sau', 'navaasi'): '1989', ('chaar', 'sau', 'sattar', 'million', 'dollar'): '470 million dollar', ('chaalees', 'ton'): '40 ton'}
WORDS = merge_words(RAWW, NUMW)
S.typed = lambda C, cam, t, a, b, sy=.085: typed(C, cam, t, WORDS, RAWW[a][1], RAWW[b][1] if b < len(RAWW) else 1e9, sy)      # scenes 1-3: same captions, numbers as digits
RED = np.float32([.78, .16, .12]); BLUE = np.float32([.20, .50, .86]); GASC = np.float32(S.GASC)


def photo(name, tone=(1.02, .97, .88), gain=.95, sat=.06, seed=0, con=1.15): return grade(load(name), tone, sat, gain, seed, con)
def opaque(img): return np.dstack([img, np.ones(img.shape[:2], np.float32)])
def push(t, t0, t1, i, f=1150):
    """Slow push-in; the drift direction and the rise/fall alternate from scene to scene."""
    k = seg(t, t0, t1); sx = 1 if i % 2 else -1; sy = 1 if i % 3 else -1; e = eout(seg(t, t0, t0 + .5), 3) * .25 + k * .75
    return look(sx * lerp(-2.0, 1.6, k), 5.0 + sy * lerp(-1.3, 1.0, k), lerp(-4, 5, e), 0, 6, 30, f)
def pop(C, spr, t, t0, w, y, z=46, x=0.0, t1=1e9, blur=.5):
    k = back(seg(t, t0 - .1, t0 + .32), 1.6) * (1 - smooth(seg(t, t1, t1 + .3)))
    if k > .02: C.append(Card(spr, x, z, w * k, y=y, shadow=0, blur=blur, fog=False, alpha=min(1, k * 2)))
def rise(C, spr, t, t0, x, z, w, y, d=.9, **kw):
    k = eout(seg(t, t0, t0 + d), 3)
    if k > 0: C.append(Card(spr, x + .12 * math.sin(t * .6), z, w, y=y - (1 - k) * (w * spr.shape[0] / spr.shape[1] + 6), shadow=0, fog=False, **kw))
def gas(C, t, t0, t1, n=24, x0=-34, zr=(9, 29), yr=(-12, -3), a=.26, seed=400, spread=(28, 62)):
    gk = seg(t, t0, t1)
    for i in range(n):
        r = np.random.default_rng(seed + i); z = r.uniform(*zr); x = x0 + gk * r.uniform(*spread) * (1 if x0 < 0 else -1) + 1.2 * math.sin(t * .7 + i)
        if gk > 0: C.append(Card(S.PUFFS[i % 5], x, z, r.uniform(9, 15), y=r.uniform(*yr) + .5 * math.sin(t + i), shadow=0, alpha=a * min(1, gk * 6), blur=None if z > 16 else 3.0, fog=False))


# ------------------------------------------------------------------ plates
TK = load('bhopal_plant_7'); TKBG = opaque(grade(TK, (1.02, .97, .86), .05, .62, 21)); TKFG = layer(grade(TK, (1.03, .97, .86), .10, 1.0, 22), subject(TK, (.38, .28, .62, .66)), 5)
TKHOT = layer(grade(TK, (1.25, .62, .45), .10, 1.05, 23), TKFG[..., 3], 5); TKBGD = opaque(grade(TK, (.70, .74, 1.0), .0, .34, 24))
ST = load('bhopal_plant_13'); STA = nonsky(ST, .03, .62, .12); STRUCT = layer(grade(ST, (1.02, .97, .88), .05, .92, 25), STA, 4); STB = band(grade(ST, (1.0, .96, .86), .0, .7, 26), .72, seed=27)
VCOLD = layer(grade(S3.V, (.62, .80, 1.05), .05, .9, 28), S3.VFG[..., 3], 5); VBGC = opaque(grade(S3.V, (.60, .76, 1.0), .0, .45, 29))
SL = load('slum_in_bhopal'); SLA = nonsky(SL, .40, .56, .46); SLUM2 = layer(grade(SL, (.62, .74, 1.0), .10, .62, 30, 1.25), SLA, 0); SLB = band(grade(SL, (.55, .66, .95), .10, .5, 31, 1.25), .62, seed=32)
SLDAY = layer(grade(S.S, (1.03, .97, .86), .05, .9, 33), S.SA, 0); SLDAYB = band(grade(S.S, (1.0, .96, .86), .0, .72, 34), .60, seed=35)
PR = load('dow_chemical_banner_bhopal_india'); PROT = opaque(grade(PR, (1.02, .97, .88), .12, .9, 36)); PROTFG = band(grade(load('dow_chemical_banner_bhopal'), (1.02, .97, .88), .12, .95, 37), .28, seed=38)
SC = load('supreme_court_of_india_inside_buildings_'); SCA = nonsky(SC, .02, .62, .10); SCOURT = layer(grade(SC, (1.02, .97, .88), .08, .95, 39), SCA, 4); SCB = band(grade(SC, (1.0, .96, .86), .05, .7, 40), .70, seed=41)
PLQ = opaque(grade(load('bhopal_disaster_plaque_in_greyfriars_kir'), (1.0, .98, .92), .05, .85, 42))
MICI = load('methyl_isocyanate_3d_spacefill'); MIC = np.dstack([MICI, np.clip((1 - MICI.min(2)) * 6, 0, 1)]).astype(np.float32)
STAT = S.STATUE; SKYD = S.SKY1; SKYN = S3.SKY6; SKYR = sky_plate((.20, .08, .07), (.80, .36, .20), 7); SKYB = sky_plate((.30, .46, .62), (.90, .80, .62), 8); SKYF = sky_plate((.95, .55, .25), (.98, .86, .55), 9)
FN = S3.FNIGHT; GN = S3.GNIGHT


def _stream(w=160, h=1200):
    s = np.zeros((h, w, 4), np.float32); cv2.line(s, (w // 2, 0), (w // 2, h - 60), tuple(float(v) for v in BLUE) + (1.0,), 46, cv2.LINE_AA)
    for i in range(9): cv2.circle(s, (w // 2 + (i % 3 - 1) * 34, 80 + i * 120), 20, (.6, .8, 1, 1), -1, cv2.LINE_AA)
    cv2.ellipse(s, (w // 2, h - 50), (70, 44), 0, 0, 360, tuple(float(v) for v in BLUE) + (1.0,), -1, cv2.LINE_AA); return s
def _thermo(level, w=220, h=900):
    s = np.zeros((h, w, 4), np.float32); cv2.rectangle(s, (w // 2 - 34, 40), (w // 2 + 34, h - 150), (.93, .90, .82, 1), -1); cv2.circle(s, (w // 2, 40), 34, (.93, .90, .82, 1), -1, cv2.LINE_AA); cv2.circle(s, (w // 2, h - 110), 92, (.93, .90, .82, 1), -1, cv2.LINE_AA)
    cv2.circle(s, (w // 2, h - 110), 70, (.85, .14, .10, 1), -1, cv2.LINE_AA); top = int((h - 170) - level * (h - 260)); cv2.rectangle(s, (w // 2 - 18, top), (w // 2 + 18, h - 150), (.85, .14, .10, 1), -1)
    for i in range(9): cv2.line(s, (w // 2 + 34, 90 + i * 72), (w // 2 + 70, 90 + i * 72), (.93, .90, .82, 1), 6)
    return s
def _switch(on, w=520, h=640):
    s = K.cut([('p', [(.06, .04), (.94, .04), (.94, .96), (.06, .96)])], w, h, (.26, .28, .30), 700, 5); K.paint(s, [('p', [(.36, .2), (.64, .2), (.64, .8), (.36, .8)])], (.10, .10, .11))
    y = .26 if on else .74; K.paint(s, [('p', [(.44, .5), (.56, .5), (.60, y), (.40, y)])], (.80, .78, .72)); K.paint(s, [('e', .5, y, .12, .07)], (.20, .70, .30) if on else (.80, .16, .12))
    t = text_sprite('ON' if on else 'OFF', 120, np.float32([.93, .90, .82]), pad=4, distress=.1, seed=2); k = w * .3 / t.shape[1]; t = cv2.resize(t, None, fx=k, fy=k); art.paste(s, t, int(w / 2 - t.shape[1] / 2), int(h * .84)); return s
def _plane(w=1400, h=460):
    s = K.cut([('e', .5, .55, .46, .12), ('p', [(.06, .5), (.0, .1), (.1, .1), (.2, .5)]), ('p', [(.42, .56), (.62, .56), (.36, .98), (.28, .98)]), ('p', [(.9, .5), (1, .56), (.9, .64)])], w, h, (.90, .89, .86), 710, 4)
    for i in range(16): K.paint(s, [('e', .22 + i * .04, .52, .009, .018)], (.12, .14, .2))
    K.paint(s, [('p', [(.06, .5), (.0, .1), (.1, .1), (.2, .5)])], (.20, .30, .55)); return s
def _palm(seed=0, w=600, h=1100):
    r = np.random.default_rng(seed); s = np.zeros((h, w, 4), np.float32); c = (.07, .06, .07, 1.0)
    cv2.polylines(s, [np.int32([(w * .5 + 40 * math.sin(y / 300), y) for y in range(int(h * .25), h, 30)])], False, c, 26, cv2.LINE_AA)
    for a in np.linspace(-2.9, -.25, 9): cv2.ellipse(s, (int(w * .5 + math.cos(a) * w * .22), int(h * .25 + math.sin(a) * h * .12 + 40)), (int(w * .26), 34), float(math.degrees(a) + r.uniform(-10, 10)), 0, 360, c, -1, cv2.LINE_AA)
    return s
def _disc(col, s=500): d = np.zeros((s, s, 4), np.float32); cv2.circle(d, (s // 2, s // 2), s // 2 - 4, tuple(col) + (1.0,), -1, cv2.LINE_AA); return d
STREAM = _stream(); THERMO = [_thermo(i / 7) for i in range(8)]; SW_ON, SW_OFF = _switch(True), _switch(False); PLANE = _plane(); PLANEF = PLANE[:, ::-1].copy(); PALMS = [_palm(i) for i in range(3)]; SUN = _disc((1.0, .93, .70))
SKULL = K.skull(); BEDS = K.bed(); RUN = [tint(K.fig((.1, .1, .12), (.08, .08, .1), i, None, seed=720 + i, skirt=i % 2 == 1), (.5, .55, .7)) for i in range(5)]; CUFF = V7.shackle(); BARS = art3d.bars(); GRAVE = K.grave(); BILLS = [art.bill(seed=i) for i in range(4)]
def _anderson(w=700, h=1500):
    """The artist's ink portrait of Warren Anderson (Wikimedia Commons, Khaydock, CC BY-SA 3.0) as a paper cut-out on a plain suit body."""
    c = cv2.imread(os.path.join(HERE, 'photos', 'anderson_cut.png'), cv2.IMREAD_UNCHANGED)[:535]; c = np.dstack([c[..., 2::-1], c[..., 3]]).astype(np.float32) / 255
    k = w / c.shape[1]; c = cv2.resize(c, (w, int(c.shape[0] * k))); bh = c.shape[0]; s = np.zeros((h, w, 4), np.float32); ink = (.08, .08, .08, 1.0)
    body = np.int32([(w * .07, bh - 70), (w * .93, bh - 40), (w * .99, h), (w * .01, h)]); cv2.fillPoly(s, [body], (.95, .94, .90, 1.0), cv2.LINE_AA); cv2.polylines(s, [body], True, ink, 7, cv2.LINE_AA)
    cv2.line(s, (int(w * .345), bh - 20), (int(w * .33), h), ink, 6, cv2.LINE_AA); cv2.fillPoly(s, [np.int32([(w * .31, bh - 30), (w * .38, bh - 30), (w * .37, bh + 260), (w * .345, bh + 310), (w * .32, bh + 260)])], ink, cv2.LINE_AA)
    for i in range(4): cv2.circle(s, (int(w * .40), bh + 120 + i * 150), 9, ink, -1, cv2.LINE_AA)
    a = c[..., 3:4]; s[:bh] = s[:bh] * (1 - a) + c * a; s[..., :3] *= (0.93 + 0.1 * fbm(h, w, 8, 3, 5))[..., None]
    e = cv2.dilate(s[..., 3], np.ones((11, 11))) - s[..., 3]; s[..., :3] = s[..., :3] * (1 - e[..., None]) + CREAM * e[..., None]; s[..., 3] = np.maximum(s[..., 3], np.clip(e * 2, 0, 1)); return s
FLAGUS = art.flag_us(); BOSS = _anderson(); S.BOSS = BOSS; COURT = S.COURT; CANDLE = V7.candle()
_AR = {}
def arrow(k, flip=False, col=(.95, .92, .84)):
    """A hand-drawn curved arrow (pointing down-right, or down-left when flipped) that draws itself as k goes 0..1."""
    q = (int(k * 12), flip, col)
    if q not in _AR:
        s = np.zeros((520, 620, 4), np.float32); r = np.random.default_rng(3); P = [(60 + 470 * u + 6 * r.normal(), 70 + 360 * u ** 2.2 + 30 * math.sin(u * 3.1) + 4 * r.normal()) for u in np.linspace(0, 1, 40)]
        n = max(2, int(len(P) * min(1, k / .8)))
        for off in ((0, 0), (3, 2)): cv2.polylines(s, [np.int32([(x + off[0], y + off[1]) for x, y in P[:n]])], False, tuple(col) + (1.0,), 13, cv2.LINE_AA)
        if k > .8:
            (x1, y1), (x0, y0) = P[-1], P[-4]; a = math.atan2(y1 - y0, x1 - x0); L = 95 * min(1, (k - .8) / .2)
            for da in (2.55, -2.55): cv2.line(s, (int(x1), int(y1)), (int(x1 + L * math.cos(a + da)), int(y1 + L * math.sin(a + da))), tuple(col) + (1.0,), 14, cv2.LINE_AA)
        _AR[q] = s[:, ::-1].copy() if flip else s
    return _AR[q]
def point(C, t, t0, t1, x, y, z, w, flip=False, col=(.95, .92, .84)):
    """Draw an arrow in the scene whose tip lands at world point (x, y, z)."""
    if t < t0 or t > t1: return
    k = seg(t, t0, t0 + .45); a = 1 - seg(t, t1 - .25, t1); tipx = (530 / 620 - .5) * w * (-1 if flip else 1); C.append(Card(arrow(k, flip, col), x - tipx + .05 * math.sin(t * 7), z, w, y=y - w * 520 / 620 * (1 - 430 / 520), shadow=0, fog=False, alpha=a, blur=0))
BT = lambda txt, col=(.90, .88, .80), size=380, seed=5: big_text(txt, col, size, seed)
T_UC = BT('UNION CARBIDE', (.93, .80, .16), 300); T_40 = BT('40 TON', (.93, .80, .16)); T_HAWA = BT('BHAARI', (.90, .88, .80)); T_3800 = BT('3,800', (.86, .30, .12)); T_8000 = BT('8,000', (.86, .30, .12)); T_5L = BT('5 LAKH+', (.86, .30, .12))
T_2014 = BT('2014'); T_470 = BT('$470M', (.93, .80, .16)); T_FOLLOW = BT('FOLLOW', (.93, .80, .16)); T_COOL = BT('COOLING', (.70, .86, 1.0)); T_4DIN = BT('4 DIN BAAD')


# ------------------------------------------------------------------ scenes (start time, function); each is one phrase and one image
def sc6(t, cam, a, b):                                   # "aadhi raat se thodi der pehle, Union Carbide ki pesticide factory mein"
    C = [Card(SKYN, 0, 75, 130, y=-52, shadow=0, blur=1.0, fog=False)]; pop(C, S3.CLOCK, t, a + .25, 22, 10, 44, -.5, T('union') - .2); pop(C, T_UC, t, T('union'), 31, 20, 46)
    C += [Card(FN, 0, 30, 58, y=-14.5, shadow=0, fog=False), Card(GN, -1, 15, 44, y=-9.5, shadow=0, fog=False)]
    point(C, t, T('pesticide'), b, 1.5, 9.0, 27, 10, col=(.93, .80, .16))
    hl(C, cam, t, 'AADHI RAAT SE PEHLE', T('aadhi') + .1, T('union') - .1, .80, .86); hl(C, cam, t, 'PESTICIDE FACTORY', T('pesticide'), b + .3, .80, .80); return C
def sc_tank(t, cam, a, b):                               # "ek tank ke andar paani chala jaata hai"
    C = [Card(TKBG, 0, 34, 66, y=-15, shadow=0, blur=2.0, fog=False), Card(TKFG, 0, 28, 56, y=-12.5, shadow=0, fog=False)]
    k = eout(seg(t, T('paani') - .2, T('paani') + .9), 2)
    if k > 0: C.append(Card(STREAM[:max(8, int(1200 * k))], 5.4, 27.5, 2.2, y=24 - 16.5 * k, shadow=0, fog=False))
    point(C, t, T('tank') - .1, T('paani') + .9, .5, 1.0, 20, 8, col=(.93, .80, .16))
    hl(C, cam, t, 'TANK MEIN PAANI', T('paani') - .1, b + .3, .80, .74, BLUE); return C
def sc_mic(t, cam, a, b):                                # "us tank mein lagbhag 40 ton methyl isocyanate tha, duniya ke sabse khatarnaak chemicals mein se ek"
    C = [Card(TKBGD, 0, 34, 66, y=-15, shadow=0, blur=2.2, fog=False)]; pop(C, T_40, t, T('chaalees'), 21, 19, 31, t1=T('duniya') - .2, blur=None)
    k = back(seg(t, T('methyl') - .15, T('methyl') + .4), 1.5)
    if k > 0: C.append(Card(MIC, .4 * math.sin(t * .7), 22, 17 * k, y=-1 + .5 * math.sin(t * 1.1), yaw=.25 * math.sin(t * .5), shadow=0, fog=False))
    rise(C, SKULL, t, T('khatarnaak') - .3, 2.6, 10, 5.2, -2.0)
    hl(C, cam, t, 'METHYL ISOCYANATE', T('methyl'), T('duniya') - .1, .80, .84, GASC); hl(C, cam, t, 'SABSE KHATARNAAK CHEMICAL', T('sabse'), b + .3, .80, .92, GASC); return C
def sc_hot(t, cam, a, b):                                # "tank garam hone lagta hai aur gas bahar nikal jaati hai"
    hk = seg(t, a, T('aur', 2)); C = [Card(SKYR, 0, 75, 130, y=-55, shadow=0, blur=1.2, fog=False), Card(TKBG, 0, 34, 66, y=-15, shadow=0, blur=2.0, fog=False, alpha=1 - .5 * hk), Card(TKFG, 0, 28, 56, y=-12.5, shadow=0, fog=False),
                                    Card(TKHOT, 0, 27.9, 56, y=-12.5, shadow=0, fog=False, alpha=hk * (.85 + .15 * math.sin(t * 9)))]
    C.append(Card(THERMO[min(7, int(hk * 8))], -3.2, 12, 1.5, y=1.5, shadow=0, fog=False, sway=.03 * hk * math.sin(t * 40)))
    gk = seg(t, T('gas', 2) - .1, b)
    for i in range(22):
        r = np.random.default_rng(500 + i); an = r.uniform(-1.3, 1.3); d = gk * r.uniform(8, 30)
        if gk > 0: C.append(Card(S.PUFFS[i % 5], 6 + math.sin(an) * d, 26 - r.uniform(0, 14) * gk, r.uniform(7, 13) * (.4 + gk), y=6 + math.cos(an) * d * .8, shadow=0, alpha=.34 * min(1, gk * 6), fog=False, blur=2.0))
    hl(C, cam, t, 'TANK GARAM', T('garam'), T('aur', 2), .80, .62, RED); hl(C, cam, t, 'GAS BAHAR NIKLI', T('gas', 2), b + .3, .80, .74, GASC); return C
def sc_safety(t, cam, a, b):                             # "safety system ya toh band the, ya repair mein the, ya itne kamzor the ki kuch rok hi nahi paaye"
    C = [Card(SKYD, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False), Card(STRUCT, 2, 30, 60, y=-19, shadow=0, fog=False), Card(STB, 0, 15, 44, y=-10.5, shadow=0, fog=False)]
    for i, (txt, tw, x, y) in enumerate((('BAND', T('band'), -2.6, 6.2), ('REPAIR MEIN', T('repair'), .4, 3.9), ('KAMZOR', T('kamzor'), 2.6, 1.6))):
        hang(C, box(txt, RED, CREAM), x, 11 + i * .6, 3.0 + .5 * (i == 1), y, t, tw - .15, ph=i * 1.9, swing=.5, L=16)
    hl(C, cam, t, 'SAFETY SYSTEM', T('safety'), T('ki', 3) - .1, .80, .66); hl(C, cam, t, 'KUCH ROK NAHI PAAYE', T('kuch'), b + .3, .80, .86); return C
def sc_cool(t, cam, a, b):                               # "jo cooling system chemical ko thanda rakhta, woh mahino pehle hi band kar diya gaya tha"
    C = [Card(VBGC, 0, 34, 46, y=-25, shadow=0, blur=2.2, fog=False)]; pop(C, T_COOL, t, T('cooling'), 20, 18, 31, blur=None); C.append(Card(VCOLD, 0, 26, 36, y=-19.5, shadow=0, fog=False))
    off = t > T('band', 2) - .1; C.append(Card(SW_OFF if off else SW_ON, 1.4, 10, 3.0 * (1 + .12 * math.exp(-max(0, t - T('band', 2) + .1) * 6) * off), y=1.0, shadow=0, fog=False, yaw=-.15))
    hl(C, cam, t, 'COOLING SYSTEM', T('cooling'), T('woh', 1) - .1, .80, .70, BLUE); hl(C, cam, t, 'MAHINO PEHLE HI BAND', T('mahino'), b + .3, .80, .88, RED); return C
def sc_heavy(t, cam, a, b):                              # "yeh gas hawa se bhaari thi. woh zameen ke paas ... bastiyon mein phail gayi, jab poore parivaar so rahe the"
    C = [Card(SKYN, 0, 75, 130, y=-52, shadow=0, blur=1.0, fog=False)]; pop(C, T_HAWA, t, T('bhaari'), 38, 19, 46, t1=T('bastiyon'))
    C.append(Card(SLUM2, 0, 30, 62, y=-17, shadow=0, fog=False)); gas(C, t, a + .2, b, 28, a=.24, seed=600); C.append(Card(SLB, 1, 15, 46, y=-13.5, shadow=0, fog=False))
    for i, x in enumerate((-2.6, .4, 3.2)): rise(C, BEDS, t, T('poore') - .2 + i * .15, x, 9.5 + i * .4, 3.2, .9 + i * .2, .7)
    hl(C, cam, t, 'HAWA SE BHAARI', T('hawa'), T('woh', 2), .80, .70, GASC); hl(C, cam, t, 'BASTIYON MEIN PHAIL GAYI', T('bastiyon') - .3, T('jab') - .05, .80, .90, GASC); hl(C, cam, t, 'POORE PARIVAAR SO RAHE THE', T('poore'), b + .3, .80, .92); return C
def sc_run(t, cam, a, b):                                # "log khaanste hue, aankhon mein jalan ke saath uthe, aur bhaagte hue usi zehreeli gas mein ghus gaye"
    C = [Card(SKYN, 0, 75, 130, y=-52, shadow=0, blur=1.0, fog=False), Card(S.SLUM, 0, 30, 62, y=-17, shadow=0, fog=False)]; gas(C, t, a - 3, b, 26, x0=34, a=.30, seed=650, zr=(12, 29), yr=(-10, 0)); C.append(Card(S.ROOFS, 1, 15, 46, y=-13.5, shadow=0, fog=False))
    rk = t - T('bhaagte') + .4
    for i in range(9):
        r = np.random.default_rng(660 + i); x = -6 + i * 1.4 + max(0, rk) * r.uniform(1.6, 2.6); z = 7.5 + (i % 3) * 1.2; p = RUN[i % 5]
        C.append(Card(p, x, z, 3.6 * p.shape[1] / p.shape[0], y=.3 + .12 * abs(math.sin(t * (4 if rk < 0 else 9) + i)), shadow=0, fog=False, sway=.25 * (rk > 0), ph=pi / 2 - t * 1.3, alpha=1 - seg(x, 3.5, 8)))
    hl(C, cam, t, 'AANKHON MEIN JALAN', T('aankhon'), T('aur', 3), .80, .80, RED); hl(C, cam, t, 'USI GAS MEIN GHUS GAYE', T('usi'), b + .3, .80, .88, GASC); return C
def sc_toll(t, cam, a, b):                               # "us waqt sarkaari aankda lagbhag 3,800 maut ka tha. doosre andaaze ... lagbhag 8,000 log mare"
    C = [Card(SKYD, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]; t8 = T('aath', 2); pop(C, T_3800, t, T('teen'), 36, 17, 46, t1=t8 - .35); pop(C, T_8000, t, t8, 34, 17, 46)
    C.append(Card(PLQ, -7 + .3 * math.sin(t * .4), 34, 26, y=-16, shadow=0, blur=1.6, fog=False, yaw=.2)); C.append(Card(STAT, cam.x * .7 + .6, 13, 9.5, y=-6.4, shadow=0, fog=False))
    for i in range(14): r = np.random.default_rng(670 + i); C.append(Card(CANDLE, r.uniform(-5, 5), 7 + r.uniform(0, 3), .26 * (1 + .06 * math.sin(t * 11 + i)), y=-1.4 - r.uniform(0, .8), shadow=0, fog=False))
    hl(C, cam, t, 'SARKAARI AANKDA', T('sarkaari'), T('doosre') - .1, .80, .74); hl(C, cam, t, 'KUCH HI DINON MEIN', T('kuch', 2), b + .3, .80, .80, RED); return C
def sc_5lakh(t, cam, a, b):                              # "aur paanch lakh se zyada log is gas ki chapet mein aaye"
    C = [Card(SKYD, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]; pop(C, T_5L, t, T('paanch'), 33, 19, 46); C.append(Card(SLDAY, 0, 30, 62, y=-17, shadow=0, fog=False)); gas(C, t, a - 2, b + 3, 16, a=.16, seed=690)
    C.append(Card(SLDAYB, 1, 15, 46, y=-13.5, shadow=0, fog=False)); hl(C, cam, t, 'GAS KI CHAPET MEIN', T('chapet') - .4, b + .3, .80, .84, GASC); return C
def sc_arrest(t, cam, a, b):                             # "chaar din baad, Union Carbide ka American boss, Warren Anderson, India aata hai aur giraftaar hota hai"
    C = [Card(SKYB, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]; pop(C, T_4DIN, t, T('chaar') , 40, 21, 46, t1=T('american') - .2)
    k = eout(seg(t, T('american') - .2, T('american') + .8), 3)
    if k > 0: C.append(Card(FLAGUS, 0, 44, 46, y=-2 + (1 - k) * 40, shadow=0, wv=10, fog=False, blur=.6))
    pk = seg(t, T('india') - .5, T('aur', 5) + .3); C.append(Card(PLANE, lerp(-40, 6, eout(pk, 2)), 38, 20, y=lerp(24, 8, eout(pk, 2)), shadow=0, fog=False)) if pk > 0 else None
    rise(C, BOSS, t, T('boss') - .25, 0, 22, 12, -9.5); C.append(Card(COURT, 0, 30, 40, y=-22, shadow=0, fog=False, alpha=0))
    hang(C, CUFF, 1.2, 11, 3.2, 1.0, t, T('giraftaar') - .15, ph=.9, swing=.5, L=16)
    point(C, t, T('warren') - .05, T('aur', 5) + .2, 1.3, 8.6, 18, 7, flip=True, col=(.93, .80, .16))
    hl(C, cam, t, 'AMERICAN BOSS', T('american'), T('warren') - .05, .80, .66); hl(C, cam, t, 'WARREN ANDERSON', T('warren'), T('aur', 5), .80, .80); hl(C, cam, t, 'GIRAFTAAR', T('giraftaar'), b + .3, .80, .56, RED); return C
def sc_bail(t, cam, a, b):                               # "kuch hi ghanton mein use bail mil jaati hai, use state se bahar bhej diya jaata hai, aur woh kabhi waapas nahi aata"
    C = [Card(SKYB, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False), Card(COURT, 0, 34, 44, y=-10, shadow=0, fog=False)]
    lk = eio(seg(t, T('bail') - .1, T('bail') + .9), 2); C.append(Card(BOSS, lerp(0, 0, lk), 20, 9, y=-8.5, shadow=0, fog=False, alpha=1 - seg(t, T('state'), T('state') + .6))); C.append(Card(BARS, 0, 16, 16, y=-7 + lk * 22, shadow=0, fog=False))
    fk = seg(t, T('state') - .1, b)
    if fk > 0: C.append(Card(PLANEF, lerp(-8, 30, ein(fk, 1.6)), 26, lerp(16, 9, fk), y=lerp(-2, 26, ein(fk, 1.4)), shadow=0, fog=False))
    hl(C, cam, t, 'KUCH HI GHANTON MEIN BAIL', T('bail') - .2, T('use', 2) - .1, .80, .92); hl(C, cam, t, 'STATE SE BAHAR', T('state'), T('aur', 6), .80, .72); hl(C, cam, t, 'KABHI WAAPAS NAHI AAYA', T('kabhi', 2), b + .3, .80, .88, RED); return C
def sc_florida(t, cam, a, b):                            # "2014 mein Florida mein uski maut ho gayi"
    C = [Card(SKYF, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False), Card(SUN, 4, 60, 22, y=2, shadow=0, fog=False)]; pop(C, T_2014, t, a + .15, 38, 20, 46)
    C.append(Card(opaque(np.zeros((40, 400, 3), np.float32) + np.float32([.10, .16, .24])), 0, 40, 160, y=-22, shadow=0, fog=False))
    for i, (x, z, w) in enumerate(((-9, 24, 10), (9.5, 22, 11), (-4.5, 30, 9), (13, 32, 9))): C.append(Card(PALMS[i % 3], x, z, w, y=-9, shadow=0, fog=False, sway=.35, ph=i * 2))
    rise(C, GRAVE, t, T('uski') - .3, 0, 12, 4.2, -1.4); hl(C, cam, t, 'FLORIDA', T('florida'), T('uski') - .1, .80, .52); hl(C, cam, t, 'USKI MAUT HO GAYI', T('uski'), b + .3, .80, .84, RED); return C
def sc_470(t, cam, a, b):                                # "1989 mein company ne 470 million dollar diye"
    C = [Card(SKYD, 0, 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]; pop(C, T_470, t, T('chaar', 2), 40, 20, 46); C += [Card(SCOURT, -3, 30, 78, y=-19.5, shadow=0, fog=False), Card(SCB, 0, 15, 46, y=-9.5, shadow=0, fog=False)]
    for i in range(22):
        r = np.random.default_rng(730 + i); dt = t - T('chaar', 2) - i * .09
        if dt > 0: C.append(Card(BILLS[i % 4], r.uniform(-5, 5) + .6 * math.sin(dt * 3 + i), r.uniform(6, 14), 2.0, y=16 - dt * r.uniform(5, 8), yaw=1.2 * math.sin(dt * 2.4 + i), tilt=.5 * math.sin(dt * 3.1 + i), shadow=0, fog=False))
    hang(C, art.calendar('YEAR', '1989', seed=6), -2.0, 12, 2.4, 4.2, t, a + .1, ph=.5, swing=.45, L=16); hl(C, cam, t, '470 MILLION DOLLAR', T('chaar', 2), b + .3, .80, .82); return C
def sc_few(t, cam, a, b):                                # "kai peediton ke hisse mein bas kuch sau dollar aaye"
    C = [Card(PROT, 0, 34, 80, y=-26, shadow=0, blur=1.6, fog=False), Card(PROTFG, 1.5, 20, 52, y=-17.5, shadow=0, fog=False)]
    hang(C, BILLS[0], .4, 10, 3.0, 3.0, t, T('bas') - .2, ph=.4, swing=.6, L=16); hl(C, cam, t, 'KAI PEEDITON KE HISSE MEIN', T('kai'), T('bas') - .1, .80, .92); hl(C, cam, t, 'BAS KUCH SAU DOLLAR', T('bas'), b + .3, .80, .84, RED); return C
def sc_end(t, cam, a, b):                                # "aisi aur kahaniyon ke liye follow karo"
    C = [Card(SKYN, 0, 75, 130, y=-52, shadow=0, blur=1.0, fog=False)]; pop(C, T_FOLLOW, t, T('follow'), 40, 18, 46); C += [Card(FN, 0, 30, 58, y=-14.5, shadow=0, fog=False), Card(GN, -1, 15, 44, y=-9.5, shadow=0, fog=False)]
    C.append(Card(STAT, cam.x * .7 + 1.0, 12, 8.5, y=-6.0, shadow=0, fog=False))
    for i in range(16): r = np.random.default_rng(770 + i); C.append(Card(CANDLE, r.uniform(-5, 5), 7 + r.uniform(0, 3), .26 * (1 + .06 * math.sin(t * 11 + i)), y=-1.4 - r.uniform(0, .8), shadow=0, fog=False))
    hl(C, cam, t, 'AISI SACHCHI KAHANIYAN', T('aisi'), T('aise') - .05, .80, .88); hl(C, cam, t, 'AISE AUR FACTS', T('aise'), T('follow') - .05, .80, .70); hl(C, cam, t, 'FOLLOW KAREIN', T('follow'), DUR, .80, .70); return C


E = 1e-3
SCN = [(0, None, None), (S3.C1, None, 'zoom'), (S3.C2, None, 0.0), (S3.C3, None, pi / 2), (S3.C4, None, .62), (S3.C5, sc6, -.55), (T('ek', 3) - .12, sc_tank, 0.0), (T('us') - .15, sc_mic, 'zoom'), (T('tank', 3) - .1, sc_hot, pi / 2),
       (T('safety') - .12, sc_safety, .62), (T('jo') - .1, sc_cool, 'zoom'), (T('yeh', 2) - .1, sc_heavy, -.55), (T('log') - .1, sc_run, 0.0), (T('us', 2) - .1, sc_toll, pi / 2), (T('aur', 4) - .1, sc_5lakh, .62),
       (T('chaar') - .12, sc_arrest, -.55), (T('kuch', 3) - .12, sc_bail, 'zoom'), (T('do', 2) - .1, sc_florida, 0.0), (T('unnees', 3) - .1, sc_470, pi / 2), (T('kai') - .12, sc_few, .62), (T('aisi') - .1, sc_end, -.55)]
OLD = [S.scene1, S.scene2, S.scene3, S3.scene4, S3.scene5]; TR = .5
def idx(t): return max(i for i in range(len(SCN)) if t >= SCN[i][0])


def raw(t, f):
    i = idx(t); a = SCN[i][0]; b = SCN[i + 1][0] if i + 1 < len(SCN) else DUR
    if i < 5: cam = S3.cam_at(t); C = OLD[i](t, cam); WD.focus = 14 if i == 2 else 26 if i == 3 else 30
    else: cam = push(t, a, b, i); C = SCN[i][1](t, cam, a, b); typed(C, cam, t, WORDS, a - .2, b - .05); WD.focus = 30
    return WD.render(cam, C, f, t)


def render(f):
    t = min(f / FPS, DUR - .001); img = raw(t, f); dip = 0.0
    for tc, fn, kind in SCN[1:]:
        if kind == 'zoom':
            if abs(t - tc) < .3: img = zoom_blur(img, .5 * math.exp(-abs(t - tc) * 9), 12); dip = .6 * math.exp(-abs(t - tc) * 14)
        elif tc <= t < tc + TR: img = rip(img, raw(tc - 1 / FPS, f), seg(t, tc, tc + TR), kind, seed=int(tc * 7))
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(36):
        r = np.random.default_rng(100 + i); cv2.circle(lay, (int((r.uniform(0, W) + 30 * math.sin(t * .4 + i)) % W) // 2, int((r.uniform(0, H) - t * (14 + 6 * (i % 3))) % H) // 2), int(r.uniform(1, 4)), (1, .95, .85), -1, cv2.LINE_AA)
    img = img + cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2) * .22
    expo = 1.25 * smooth(seg(t, 0, .4)) * (1 - .95 * ein(seg(t, DUR - .35, DUR), 2)) * (1 - dip)
    return (post(img, f, tilt=0.6, expo=expo) * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); Rn = np.random.default_rng(4)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)
    for tc, fn, kind in SCN[1:]:
        if kind == 'zoom': add(film.whoosh(.7, 200, 2400, .55), tc - .4, .16)
        else: rp = film._filt(Rn.normal(0, 1, int(.55 * SR)), 1200, 7500); m = len(rp); add(rp * np.linspace(1, .15, m) * (.35 + .65 * (Rn.random(m // 60 + 1).repeat(60)[:m] > .35)), tc, .085, (-1) ** int(tc))
    def hiss(t0, d, g=.03): h = film._filt(Rn.normal(0, 1, int(d * SR)), 2500, 7000); add(h * np.minimum(1, np.arange(len(h)) / SR) * np.linspace(1, .2, len(h)), t0, g)
    hiss(T('zehreeli'), 3.6); hiss(T('gas', 2), 2.0, .04); hiss(T('yeh', 2), 7.5, .025); hiss(T('log'), 6, .025)
    HL = [T('unnees'), T('zehreeli'), T('neend'), T('company'), T('court'), T('saath'), T('yeh'), T('bhopal'), T('do'), T('aadhi'), T('pesticide'), T('paani'), T('chaalees'), T('methyl'), T('sabse'), T('garam'), T('gas', 2), T('band'), T('repair'), T('kamzor'), T('kuch'),
          T('cooling'), T('mahino'), T('hawa'), T('bastiyon'), T('poore'), T('aankhon'), T('usi'), T('teen'), T('aath', 2), T('paanch'), T('american'), T('warren'), T('giraftaar'), T('bail'), T('state'), T('kabhi', 2), T('do', 2), T('florida'), T('chaar', 2), T('bas'), T('follow')]
    for tl in HL: add(film.thump(82, 32, .6, .14), tl, .16); add(film.nburst(.25, 300, 3000, .04), tl, .045)
    for w in RAWW: add(film.nburst(.03, 2500, 7000, .008), w[1], .018)
    for i in range(10): add(film.nburst(.02, 3000, 8000, .006), T('saath') + i * .25, .05)
    m = int(5 * SR); t2 = np.arange(m) / SR; bell = lambda f0: sum(a * np.sin(2 * np.pi * f0 * k * t2) * np.exp(-t2 / d) for k, a, d in ((1, .5, 2.6), (2, .35, 1.8), (2.38, .2, 1.2), (.5, .3, 3.2)))
    for tb, f0, g in ((T('neend'), 147, .08), (T('aadhi') + .1, 196, .07), (T('sabse'), 131, .06), (T('poore'), 147, .06), (T('teen'), 147, .08), (T('aath', 2), 131, .08), (T('uski'), 131, .08), (T('bas'), 147, .07), (T('follow'), 196, .07)): add(bell(f0), tb, g)
    for i in range(3): add(film.thump(180, 90, .5, .08), T('court') + i * .22, .10)
    drip = lambda: film.thump(900, 400, .3, .05)
    for i in range(6): add(drip(), T('paani') + i * .22, .05, .3)
    jet = film._filt(Rn.normal(0, 1, int(2.6 * SR)), 80, 500); add(jet * np.minimum(1, np.arange(len(jet)) / (.8 * SR)) * np.linspace(1, .3, len(jet)), T('india') - .5, .05, -.3); add(jet * np.linspace(.3, 1, len(jet)) * np.linspace(1, 0, len(jet)), T('state'), .05, .3)
    add(film.thump(140, 60, .5, .12), T('giraftaar'), .12); add(film.thump(120, 50, .5, .2), T('bail') + .2, .10)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.3 * SR):] *= np.linspace(1, 0, int(.3 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):06.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (360, 640), interpolation=cv2.INTER_AREA)[..., ::-1])
    elif mode == 'render':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True); NF = round(DUR * FPS); nseg = math.ceil(NF / 300)
        a, b = (int(x) for x in sys.argv[3].split('-')) if len(sys.argv) > 3 else (0, nseg - 1)
        with Pool(4) as p:
            for s in range(a, b + 1):
                fn = f'{out}/seg_{s:02d}.mp4'
                if os.path.exists(fn): continue
                ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4'], stdin=subprocess.PIPE)
                for im in p.imap(render, range(s * 300, min(NF, (s + 1) * 300)), chunksize=4): ff.stdin.write(im.tobytes())
                ff.stdin.close(); ff.wait(); os.rename(fn + '.tmp.mp4', fn); print('seg', s, flush=True)
    else:
        out = sys.argv[2]; dst = sys.argv[3]; sfx = dst + '.sfx.wav'; soundtrack(sfx); lst = dst + '.txt'
        open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in sorted(glob.glob(f'{out}/seg_*.mp4'))))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', S.VOICE, '-i', sfx,
                        '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={DUR - .2}:d=0.2,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                        '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', dst], check=True)
        os.remove(sfx); os.remove(lst); print('done', dst)
