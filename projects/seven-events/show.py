"""7 Most Horrifying Events in History - full video. Cinematic 3D pop-up: every event is a set built back-to-front, shot from several sides,
with giants rising behind the set, things hanging from above, and a moving, lit background.
Usage: python3 show.py stills <dir> t1,t2,.. | render <outdir> [a-b] | mux <outdir> <out.mp4>"""
import sys, os, math, json, subprocess, glob, wave as wavmod, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, medieval as M, kit3d as K, world7 as V
from voxkit.pop3d import Cam3, Card, World, dust

_sp = importlib.util.spec_from_file_location('s2', os.path.join(HERE, 'sample2.py')); S2 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S2); S1 = S2.S1
VOICE = os.path.join(HERE, 'voice', 'full.mp3'); T = S2.T; PHD = os.path.join(HERE, 'photos', 'wm')
DUR = 85.55; pi = math.pi; BURNT = S1.BURNT; WHITE = S1.WHITE; LB = S1.LB; pin = S1.pin; chip = S1.chip; look = S2.look; up = S2.up
B = [0, 10.30, 14.42, 24.55, 37.08, 51.02, 62.75, 73.20, 81.15, DUR]                      # scene boundaries
IC = [S2.CUT1, S2.CUT2, 19.80, 30.90, 42.65, 47.95, 55.25, 58.90, 67.00, 76.90]           # cuts inside scenes
CUTS = sorted(B[1:-1] + IC)


def photo(key):
    for e in ('jpg', 'jpeg', 'png', 'JPG'):
        p = os.path.join(PHD, f'{key}.{e}')
        if os.path.exists(p): return p
    return None


# ------------------------------------------------------------------ helpers
def shot(t, t0, t1, p0, p1, tg, f=1150, tg1=None):
    k = smooth(seg(t, t0, t1)); g = tg if tg1 is None else [lerp(a, b, k) for a, b in zip(tg, tg1)]
    return look(lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k), lerp(p0[2], p1[2], k), g[0], g[1], g[2], f)


def giant(C, spr, x, z, w, t, t0, d=2.4, sway=.3, ph=0.0, blur=1.1, alpha=.88, yaw=0.0, fog=False):
    """A massive cut-out rising from behind the set, always slightly alive (sways, breathes, turns)."""
    k = eout(seg(t, t0, t0 + d), 2.5)
    if k < .03: return
    crop = spr[:max(8, int(spr.shape[0] * k))]
    C.append(Card(crop, x + sway * .6 * math.sin(t * .45 + ph), z, w * (1 + .012 * math.sin(t * .9 + ph)), yaw=yaw + .05 * math.sin(t * .38 + ph), sway=sway, ph=ph, shadow=0, blur=blur, alpha=alpha, fog=fog))


STRING = V.string()
def hang(C, spr, x, z, w, ybot, t, t0, ph=0.0, swing=.5, yaw=0.0, L=14.0, fog=False, wv=0.0, blur=None, alpha=1.0):
    """Something lowered from above on a string; it drops in, swings and settles."""
    if t < t0: return
    dt = t - t0; y = ybot + (1 - back(seg(dt, 0, .75), 1.2)) * 13
    a = swing * math.exp(-dt * .55) * math.sin(dt * 2.7 + ph) + .07 * math.sin(t * 1.1 + ph)          # pendulum angle
    hh = w * spr.shape[0] / spr.shape[1]; xx = x + a * 2.2; fix = pi / 2 - t * 1.3                        # ph that pins Card.sway to its full value
    C.append(Card(STRING, xx, z + .02, L * 8 / 700, y=y + hh - .05, sway=-a * 2.2, ph=fix, shadow=0, fog=fog, blur=blur, alpha=alpha))
    C.append(Card(spr, xx, z, w, y=y, yaw=yaw + .25 * a, sway=-a * 2.2 * hh / L, ph=fix, shadow=0, fog=fog, wv=wv, blur=blur, alpha=alpha))


def ppl(C, spr, x, z, hgt, t, i, fy, fall=None, tl=0.0, alpha=1.0, bob=.05, sh=.55):
    """A standing/walking paper person; fall = time at which it tips over."""
    tilt = tl or 0.0; yb = bob * abs(math.sin(t * 4.6 + i * 1.7))
    if fall is not None:
        kf = seg(t, fall, fall + .5); tilt = max(tilt, kf ** 2 * pi / 2 * .97); yb *= 1 - kf
    C.append(Card(spr, x, z, hgt * spr.shape[1] / spr.shape[0], y=yb, yaw=fy if tilt < .1 else 0, tilt=tilt, sway=.04 if tilt < .1 else 0, ph=i, shadow=sh, alpha=alpha))


_CAL = {}
def cal(top, big):
    if (top, big) not in _CAL: _CAL[(top, big)] = art.calendar(top, str(big), seed=len(_CAL) + 3)
    return _CAL[(top, big)]


def wf(txt): return min(.92, .17 + .046 * len(txt))
def caps(C, cam, t, L):
    """L: (text | sprite, colour, t0, t1, sy[, width, sx])"""
    for e in L:
        txt, col, t0, t1, sy = e[:5]; spr = LB(txt, col) if isinstance(txt, str) else txt
        chip(C, cam, t, spr, t0, t1, e[6] if len(e) > 6 else .5, sy, e[5] if len(e) > 5 else wf(txt))


def tint(spr, c): s = spr.copy(); s[..., :3] *= np.float32(c); return s
CLOUDS = [art3d.cloud(i) for i in range(4)]
def clouds(C, t, col, n=6, z=70, y=22, w=30, v=.9, alpha=.8):
    for i in range(n): C.append(Card(_CT(i % 4, col), -60 + (t * v + i * 23.7) % 120, z + (i % 3) * 9, w * (1 + .2 * (i % 2)), y=y + 4 * math.sin(i * 2.1), shadow=0, blur=2.2, alpha=alpha))
_CTc = {}
def _CT(i, col):
    if (i, col) not in _CTc: _CTc[(i, col)] = tint(CLOUDS[i], col)
    return _CTc[(i, col)]


def mk(ground, top, bot, fog, fog_d=60, dof=16, seed=1, tex=None):
    return World(tex if tex is not None else art3d.ground_tex(col=ground, seed=seed), art3d.sky(top, bot, seed + 20), fog=fog, fog_d=fog_d, focus=9.0, dof=dof)


def atmos(img, cam, t, col=(1, .85, .6), fall=-1.0, beam=(.10, .07, .04), n=40, amt=.35):
    """Drifting motes (fall<0 rise, >0 fall like ash/snow) and a slow-moving shaft of light."""
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(n):
        r = np.random.default_rng(100 + i); x = ((r.uniform(0, W) + 30 * math.sin(t * .4 + i) - cam.x * 60) % W) / 2; y = ((r.uniform(0, H) + fall * t * (14 + 6 * (i % 3))) % H) / 2
        cv2.circle(lay, (int(x), int(y)), int(r.uniform(1, 4)), col, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2)
    sh = .35 + .3 * math.sin(t * .33)
    bm = np.clip(1 - np.abs(np.linspace(-1, 1, W, dtype=np.float32)[None, :] + sh - .25 * np.linspace(0, 1, H, dtype=np.float32)[:, None]) * 1.6, 0, 1) ** 2
    return img + lay * amt + bm[..., None] * np.float32(beam)


def searchlight(img, cam, t, src, a0, sp_=.5, ph=0.0, col=(.30, .29, .24)):
    p, Z = cam.project(np.array([src], np.float32))
    if Z[0] < .5: return img
    a = a0 + .6 * math.sin(t * sp_ + ph); x, y = p[0]; Ln = 2600
    lay = np.zeros((H // 4, W // 4), np.float32)
    cv2.fillConvexPoly(lay, np.int32([(x / 4, y / 4), ((x + Ln * math.cos(a - .07)) / 4, (y + Ln * math.sin(a - .07)) / 4), ((x + Ln * math.cos(a + .07)) / 4, (y + Ln * math.sin(a + .07)) / 4)]), 1.0, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 5), (W, H))
    return img + lay[..., None] * np.float32(col)


# ------------------------------------------------------------------ sprites
DOC = tint(S1.DOCTOR, (.50, .46, .46)); DOCF = DOC[:, ::-1].copy()
NUMS = S1.NUMS; NUMD = {n: tint(NUMS[n], (.34, .34, .36)) for n in NUMS}
HILLS = [M.hills(seed=2), M.hills(seed=5, col=(.34, .27, .24))]
SHIP = V.sail_ship(); SHIPF = SHIP[:, ::-1].copy(); SHACKLE = V.shackle(); CAPT = [V.captive(i) for i in range(4)]; CAPTG = [tint(c, (.42, .40, .44)) for c in CAPT]
KING = V.king(); FLAG_BE = V.flag3([(.10, .10, .10), (.95, .80, .20), (.80, .15, .15)]); FLAG_JP = V.flag_disc((.95, .93, .88), (.75, .10, .15)); FLAG_RED = V.flag3([(.70, .10, .10)])
HUTS = [V.hut(i) for i in range(3)]; JUNGLE = [V.jungle(i) for i in range(5)]; GATE_CN = V.cn_gate(); CNH = [V.cn_house(i) for i in range(4)]; SOLDIER = V.soldier(); SOLDF = SOLDIER[:, ::-1].copy()
GATEH = V.gatehouse(); RAILS = V.rails(); FENCE = V.fence(); WTOWER = V.watchtower(); STAR = V.star_badge(); COATS = [V.coat_person(i, k) for i, k in enumerate(('man', 'woman', 'child', 'man', 'woman', 'man', 'child', 'woman'))]
TEMPLE = V.temple(); CADRES = [V.cadre(i) for i in range(3)]; CADREG = tint(V.cadre(0), (.8, .8, .85)); FARM = [V.farmer(i) for i in range(6)]; RADIO = V.radio(); ARC = V.wave_arc(); CANDLE = V.candle()
PALACE = K.courthouse(); AFRICA = K.africa(); GAVEL = art.gavel(); SKYLINE = art3d.skyline_old(seed=3); LAMP = art3d.lamp(); SMOKES = S2.SMOKES; CROWS = S2.CROWS
GENTS = [K.fig(c, (.14, .13, .13), i % 2, 'fedora', seed=500 + i, long=i % 3 == 0) for i, c in enumerate(((.16, .16, .20), (.24, .20, .18), (.12, .14, .16), (.30, .26, .22), (.18, .16, .16), (.22, .22, .26)))]
VILL = [K.fig(c, (.30, .24, .20), 4 + i % 2, None, skirt=i % 2 == 1, seed=520 + i) for i, c in enumerate(((.70, .56, .36), (.62, .30, .22), (.46, .50, .36), (.76, .66, .46), (.52, .36, .30), (.36, .44, .52)))]
CNP = [K.fig(c, (.16, .16, .17), 1 + i % 2, 'hair' if i % 2 else None, long=True, seed=540 + i) for i, c in enumerate(((.22, .24, .30), (.32, .28, .26), (.18, .22, .22), (.36, .34, .36), (.26, .20, .20), (.20, .26, .32)))]
RWP = [K.fig(c, (.24, .20, .18), 4 + i % 2, None, skirt=i % 2 == 0, seed=560 + i) for i, c in enumerate(((.78, .34, .20), (.30, .46, .56), (.84, .70, .30), (.44, .56, .34), (.66, .30, .44), (.86, .84, .78)))]
GHILL = [M.hills(seed=11 + i, col=c) for i, c in enumerate(((.30, .40, .30), (.26, .36, .24), (.22, .32, .20)))]


def _leopold():
    p = photo('leopold')
    if not p: return None
    return S1.aged(p, w=900, border=34, sat=.25, seed=21)
LEOPOLD = _leopold()
PRINTS = {k: (S1.aged(photo(k), w=900, sat=.3, seed=30 + i) if photo(k) else None) for i, k in enumerate(('brookes', 'birkenau', 'polpot', 'tribunal', 'kigali', 'tuolsleng', 'nanjinggate'))}


def _wavestrip(seed, w=2400, h=150):
    xs = np.arange(w); top = h * (.42 + .22 * np.sin(xs / w * 2 * pi * 9 + seed) + .08 * np.sin(xs / w * 2 * pi * 23 + seed * 2))
    yy = np.arange(h)[:, None]; m = (yy > top[None, :]).astype(np.float32); rgb = paper(h, w, np.float32([.13, .24, .32]) * (1 + .1 * (seed % 3)), seed, .05, .15)
    rgb[(yy > top[None, :]) & (yy < top[None, :] + 12)] = (.74, .82, .84); return rgba(rgb, cv2.GaussianBlur(m, (0, 0), 1))
WAVES = [_wavestrip(i) for i in range(3)]


def _routemap(w=1300, h=900):
    rgb = paper(h, w, np.float32([.30, .44, .52]), 61, .05, .15)
    am = np.int32([(0, 0), (.30, 0), (.26, .16), (.34, .34), (.24, .46), (.33, .58), (.44, .70), (.36, .98), (.30, 1), (.24, .74), (.12, .50), (0, .40)]) if False else None
    for pts, col in (([(0, 0), (.30, 0), (.27, .18), (.20, .28), (.26, .40), (.22, .48), (.34, .60), (.44, .72), (.38, 1), (.26, 1), (.22, .74), (.10, .52), (0, .44)], (.78, .68, .46)),
                     ([(.66, .26), (.80, .22), (1, .24), (1, 1), (.84, 1), (.80, .80), (.82, .62), (.70, .54), (.62, .40)], (.80, .58, .26))):
        cv2.fillPoly(rgb, [np.int32([(x * w, y * h) for x, y in pts])], col, cv2.LINE_AA)
    for (x0, y0), (x1, y1), bow in (((.68, .48), (.30, .34), -.10), ((.70, .56), (.36, .64), .10), ((.74, .64), (.40, .84), .14), ((.67, .44), (.24, .22), -.16)):
        for i in range(22):
            k = i / 21; x = lerp(x0, x1, k); y = lerp(y0, y1, k) + bow * math.sin(k * pi)
            cv2.circle(rgb, (int(x * w), int(y * h)), 7 if i < 21 else 14, (.80, .22, .12), -1, cv2.LINE_AA)
    rgb *= (0.9 + 0.2 * fbm(h, w, 12, 3, 62))[..., None]
    for txt, x, y in (('AFRICA', .76, .40), ('THE AMERICAS', .02, .08), ('ATLANTIC', .40, .46)):
        ts = text_sprite(txt, 54, np.float32([.12, .10, .08]), pad=4, distress=.2, seed=5); art.paste(rgb4 := rgba(rgb, np.ones((h, w), np.float32)), ts, int(x * w), int(y * h)); rgb = rgb4[..., :3]
    return rgba(np.clip(rgb, 0, 1), torn(h, w, 7, 2, 63))
ROUTE = _routemap(); PLANK = art3d.wall(w=1000, h=340, col=(.34, .24, .16), seed=5)


def _stopwatch(s=520):
    c = np.zeros((int(s * 1.2), s, 4), np.float32); cy = int(s * .68)
    cv2.rectangle(c, (s // 2 - 28, int(s * .04)), (s // 2 + 28, int(s * .22)), (.75, .60, .25, 1), -1); cv2.circle(c, (s // 2, cy), int(s * .47), (.75, .60, .25, 1), -1, cv2.LINE_AA)
    cv2.circle(c, (s // 2, cy), int(s * .40), (.93, .89, .78, 1), -1, cv2.LINE_AA)
    for i in range(12): a = i * pi / 6; cv2.line(c, (int(s / 2 + s * .33 * math.sin(a)), int(cy - s * .33 * math.cos(a))), (int(s / 2 + s * .38 * math.sin(a)), int(cy - s * .38 * math.cos(a))), (.1, .08, .07, 1), 6, cv2.LINE_AA)
    ts = text_sprite('60', 190, np.float32([.12, .10, .08]), pad=4, distress=.2, seed=2); k = s * .42 / ts.shape[1]; ts = cv2.resize(ts, None, fx=k, fy=k); art.paste(c, ts, (s - ts.shape[1]) // 2, cy - ts.shape[0] // 2); return c
STOPW = _stopwatch()


def _vine(seed, w=260, h=1400):
    s = np.zeros((h, w, 4), np.float32); r = np.random.default_rng(seed); pts = [(w / 2 + 40 * math.sin(y / 130 + seed), y) for y in range(0, h, 20)]
    cv2.polylines(s, [np.int32(pts)], False, (.10, .20, .10, 1), 9, cv2.LINE_AA)
    for x, y in pts[2::2]:
        a = r.uniform(-1, 1); cv2.ellipse(s, (int(x + 46 * np.sign(a)), int(y)), (46, 20), float(a * 40), 0, 360, tuple(float(v) for v in np.float32([.14, .34, .16]) * r.uniform(.7, 1.2)) + (1.0,), -1, cv2.LINE_AA)
    return s
VINES = [_vine(i) for i in range(3)]


def _lantern(w=200, h=300):
    s = K.cut([('e', .5, .55, .42, .36), ('p', [(.36, .12), (.64, .12), (.64, .24), (.36, .24)]), ('p', [(.36, .86), (.64, .86), (.64, .94), (.36, .94)])], w, h, (.78, .16, .12), 71, 3)
    K.paint(s, [('p', [(.36, .12), (.64, .12), (.64, .24), (.36, .24)]), ('p', [(.36, .86), (.64, .86), (.64, .94), (.36, .94)])], (.86, .68, .24)); K.paint(s, [('e', .5, .55, .16, .2)], (.98, .70, .30)); return s
LANTERN = _lantern()
rng = np.random.default_rng(7)
CANDLES = [(float(rng.uniform(-9, 9)), float(rng.uniform(5, 24)), float(rng.uniform(.5, .8))) for _ in range(80)]


def candles(C, t, t0, rate=30.0, x0=0.0):
    for i, (x, z, hgt) in enumerate(sorted(CANDLES, key=lambda c: c[1])):
        if t < t0 + i / rate: break
        fl = 1 + .06 * math.sin(t * 11 + i * 2.3) + .04 * math.sin(t * 17 + i)
        C.append(Card(CANDLE, x + x0, z, hgt * 90 / 260 * fl, shadow=.3, fog=False))


# ------------------------------------------------------------------ 1. the Black Death (the approved town, plus the giant doctors)
def cam1(t): return S2.cam_at(t)
def sc1(t, cam):
    C = S2.cards(t, cam)
    if t < S2.CUT1 + .05:
        giant(C, DOC, -15, 72, 20, t, .75, 2.2, ph=0); giant(C, DOCF, 18, 68, 17, t, 1.15, 2.2, ph=2)
    elif t < S2.CUT2:
        giant(C, DOC, -30, 44, 15, t, S2.CUT1 + .1, 2.4, ph=1); giant(C, DOCF, -8, 52, 17, t, S2.CUT1 + .7, 2.4, ph=3)
    else:
        giant(C, DOCF, 38, 54, 18, t, S2.CUT2 + .2, 2.4, ph=0); giant(C, DOC, -13, 62, 20, t, S2.CUT2 + .9, 2.4, ph=2)
    S2.chips(C, cam, t)
    return dict(world=S2.WORLD, C=C, focus=S2.focus_at(t), tint=(1.05, .95, .78), mix=.20, expo=1.32, extra=S2.extra, flick=.04)


# ------------------------------------------------------------------ 2. "That's one ... six more"
W2 = mk((.20, .17, .16), (.05, .05, .07), (.40, .22, .15), (.22, .15, .13), 42, 14, 2)
def cam2(t): return shot(t, B[1], B[2], (-3.2, 1.2, -3.5), (2.4, 2.0, -.6), (0, 3.6, 10))
def sc2(t, cam):
    C = [Card(HILLS[0], 0, 95, 210, blur=2.2), Card(HILLS[1], 20, 75, 170, blur=1.8)]
    giant(C, DOC, -9, 52, 20, t, B[1] - 3, ph=0); giant(C, DOCF, 12, 58, 18, t, B[1] - 3, ph=2)
    for i in range(5): C.append(Card(SMOKES[i % 3], -20 + i * 10 + .8 * math.sin(t * .4 + i), 36 + (i % 2) * 6, 7, y=1 + (t * .6 + i) % 3, shadow=0, blur=2.0, alpha=.7))
    six = T('six')
    for n in range(1, 8):
        lit = n == 1 or t > six + (n - 2) * .075
        hang(C, NUMS[n] if lit else NUMD[n], (n - 4) * 1.55, 9.5 + .45 * abs(n - 4), 1.25, 3.0 + .5 * (n % 2) + (.35 if lit and n > 1 else 0) * math.exp(-(t - six) * 3), t, B[1] + .02 + n * .06, ph=n * 1.3, swing=.35)
    hang(C, STOPW, 0, 6.4, 1.5, 1.2, t, T('sixty') - .15, ph=.5, swing=.5)
    caps(C, cam, t, [("THAT'S ONE", BURNT, T("that's"), T('give') - .15, .14), ('GIVE ME 60 SECONDS', WHITE, T('give'), T('six') - .2, .14), ('SIX MORE', BURNT, six, None, .14)])
    return dict(world=W2, C=C, focus=lerp(7, 10, smooth(seg(t, B[1], B[2]))), tint=(1.05, .95, .80), mix=.2, expo=1.3, flick=.03)


# ------------------------------------------------------------------ 3. the Atlantic slave trade
W3 = mk(None, (.13, .12, .20), (.86, .50, .30), (.48, .36, .36), 75, 16, 3, tex=np.clip(K.water_tex(seed=3) * np.float32([.55, .62, .70]), 0, 1))
SHIPS = [(-7, 15, 7, .45), (6, 25, 8, .35), (-15, 37, 9, .3), (15, 47, 10, .25), (-2, 60, 10, .2), (26, 70, 10, .2), (-30, 66, 10, .2)]
DECK = [(-5.2 + i * .8 + .2 * (i % 2), 8.2 + (i % 3) * .9) for i in range(14)]
def cam3(t):
    if t < IC[2]: return shot(t, B[2], IC[2], (-5.5, 1.1, -7), (-1.0, 1.9, -1.5), (0, 4.0, 26))
    return shot(t, IC[2], B[3], (8.5, 5.2, -2), (5.0, 3.4, 2.2), (-1.5, 3.2, 14))
def sc3(t, cam):
    C = [Card(tint(HILLS[0], (.5, .55, .6)) if False else HILLS[0], -60, 110, 150, blur=2.4)]; fy = -cam.yaw * .8; A = t < IC[2]
    clouds(C, t, (.95, .62, .50), z=95, y=26, w=40)
    for i in range(12): C.append(Card(WAVES[i % 3], 3 * math.sin(t * .5 + i * 1.7), 5 + i * 5.5, 70, y=-3.3 + .22 * math.sin(t * 1.5 + i * 1.1), shadow=0, wv=5))
    for i, (x, z, w, v) in enumerate(SHIPS):
        tl = up(t, B[2] + (70 - z) * .012, .5)
        if tl is not None: C.append(Card(SHIP if i % 2 else SHIPF, x + (t - B[2]) * v * (1 if i % 2 else -1), z, w, y=.1 + .22 * math.sin(t * 1.5 + i * 2), tilt=tl, sway=.25, ph=i, shadow=.4))
    for i in range(3): giant(C, CAPTG[i], -17 + i * 17, 92 + (i % 2) * 5, 15, t, T('twelve') - .3 + i * .35, 2.6, ph=i * 2, sway=.35, blur=1.6)
    for i, x in enumerate((-3.4, 3.6, -.2)): hang(C, SHACKLE, x, 9 + i * 2.5, 1.5, 3.6 - i * .5, t, T('captive') - .2 + i * .12, ph=i * 2, swing=.6)
    if PRINTS['brookes'] is not None and A: hang(C, PRINTS['brookes'], 0, 15, 6.5, 5.2, t, T('ships') - .1, ph=1, swing=.3)
    if not A:
        hang(C, ROUTE, -2.5, 20, 11, 4.8, t, IC[2] + .05, ph=.8, swing=.28, yaw=-cam.yaw * .6)
        C.append(Card(PLANK, -.2, 7.4, 13, y=.06, tilt=pi / 2 * .999, shadow=0))
        for i, (x, z) in enumerate(DECK): ppl(C, CAPT[i % 4], x, z, 1.75, t, i, fy, fall=T('died') + .05 * (i % 4) if i % 7 == 3 else None, bob=.02)
    yr = (1500, 1600, 1700, 1800)[min(3, int(seg(t, T('three'), T('ships')) * 4))]
    caps(C, cam, t, [('MORE THAN 300 YEARS', WHITE, T('more', 2), T('ships') + .5, .14), (cal('YEAR', f'{yr}s'), None, T('three'), T('ships') + .5, .29, .26),
                     ('12.5 MILLION', BURNT, T('twelve'), IC[2] - .2, .14), ('CAPTIVE AFRICANS', WHITE, T('captive'), IC[2] - .2, .215, .62),
                     ('ACROSS THE ATLANTIC', WHITE, T('across'), T('about', 2) - .1, .14), ('1.8 MILLION DIED', BURNT, T('one', 3), None, .14), ('ON THE CROSSING', WHITE, T('died') + .35, None, .215, .6)])
    return dict(world=W3, C=C, focus=lerp(9, 22, smooth(seg(t, B[2], B[2] + 3))) if A else 11, tint=(.92, .96, 1.06), mix=.22, expo=1.3, atm=dict(col=(1, .8, .6), beam=(.10, .06, .04)))


# ------------------------------------------------------------------ 4. the Congo Free State
W4a = mk((.38, .36, .35), (.20, .24, .32), (.82, .72, .58), (.60, .56, .50), 60, 16, 4)
W4b = mk((.34, .30, .18), (.16, .28, .24), (.88, .78, .50), (.52, .56, .40), 50, 16, 5)
TREES = [(float(rng.uniform(-34, 34)), float(z), float(rng.uniform(7, 11)), int(rng.integers(5))) for z in (50, 46, 42, 38, 34, 30, 27) for _ in range(5)]
VPOS = [(float(rng.uniform(-6, 6)), 5.5 + i * .65, int(rng.integers(6)), float(rng.choice([-1, 1]) * rng.uniform(.1, .3))) for i in range(22)]
def cam4(t):
    if t < IC[3]: return shot(t, B[3], IC[3], (5.5, 1.2, -3), (1.0, 2.0, 3.5), (0, 6.0, 30))
    return shot(t, IC[3], B[4], (-6.5, 1.3, -1), (-2.0, 2.6, 4.0), (1.5, 4.2, 24))
def sc4(t, cam):
    C = []; fy = -cam.yaw * .8
    if t < IC[3]:
        C += [Card(SKYLINE, 0, 90, 200, blur=2.2), Card(SKYLINE[:, ::-1], 40, 70, 150, blur=1.6)]; clouds(C, t, (.9, .88, .86), z=80, y=26)
        for spr, x, z, w, t0 in ((PALACE, 0, 30, 30, .1), (PALACE, -34, 38, 26, .0), (PALACE, 34, 38, 26, .05)):
            tl = up(t, B[3] + t0, .5)
            if tl is not None: C.append(Card(spr, x, z, w, tilt=tl, shadow=.4, blur=.8 if abs(x) > 1 else None))
        for i, x in enumerate((-11, 11, -5.5, 5.5)):
            hang(C, FLAG_BE, x, 26 - (i // 2) * 6, 4.2, 6.5 - (i // 2) * 1.5, t, B[3] + .35 + i * .1, ph=i * 1.4, swing=.3, wv=14, fog=True)
        for i in range(8): C.append(Card(LAMP, (-1) ** i * 6.5, 6 + (i // 2) * 5.5, .8, shadow=.4))
        if LEOPOLD is not None: giant(C, LEOPOLD, 0, 58, 46, t, T('king') - .25, 2.4, ph=1, blur=.9, sway=.4)
        C.append(Card(KING, 0, 20, 2.3, tilt=up(t, T('king') - .1, .45) or 0, yaw=fy, sway=.03, shadow=.6)) if t > T('king') - .1 else None
        for i in range(12):
            r = np.random.default_rng(80 + i); z = 5 + i * 1.2; ppl(C, GENTS[i % 6], r.uniform(-6, 6) + (t - B[3]) * r.uniform(.3, .7) * (1 if i % 2 else -1), z, 1.8, t, i, fy, tl=up(t, B[3] + .3 + i * .04, .35))
        hang(C, AFRICA, 2.6, 12, 4.4, 3.4, t, T('country') - .1, ph=.6, swing=.45, yaw=-cam.yaw * .7)
        caps(C, cam, t, [(cal('YEAR', 1885), None, T('eighteen'), T('king') - .2, .27, .26), ('A KING IN BRUSSELS', WHITE, T('king'), T('personal') - .15, .14),
                         ('HIS PERSONAL PROPERTY', BURNT, T('personal'), None, .14)])
        return dict(world=W4a, C=C, focus=lerp(6, 18, smooth(seg(t, B[3], B[3] + 2.5))), tint=(1.0, .97, .90), mix=.2, expo=1.28, atm=dict(col=(1, .9, .7)))
    C += [Card(GHILL[0], 0, 100, 220, blur=2.2), Card(GHILL[2], -30, 75, 170, blur=1.6)]; clouds(C, t, (.95, .9, .75), z=85, y=26)
    if LEOPOLD is not None: giant(C, LEOPOLD, 6, 72, 54, t, IC[3] - 3, ph=1, blur=1.6, sway=.4, alpha=.92)
    for i, (x, z, hh, k) in enumerate(TREES):
        tl = up(t, IC[3] + (52 - z) * .02, .45)
        if tl is not None and abs(x) > 3 + (z < 30) * 4: C.append(Card(JUNGLE[k], x, z, hh * 700 / 1100, tilt=tl, sway=.25, ph=i, shadow=.4))
    for i, (x, z) in enumerate(((-8, 22), (8.5, 21), (-11, 16), (11.5, 15), (-3, 25), (4, 26))):
        tl = up(t, IC[3] + .5 + i * .06, .4)
        if tl is not None: C.append(Card(HUTS[i % 3], x, z, 4.4, tilt=tl, shadow=.5))
    for i in range(4): C.append(Card(SMOKES[i % 3], (-8, 8.5, -3, 4)[i] + .5 * math.sin(t * .5 + i), (22, 21, 25, 26)[i] + .3, 2.4, y=3.6 + (t * .5 + i) % 2, shadow=0, alpha=.6))
    for i, (x, z, pi_, v) in enumerate(VPOS):
        ppl(C, VILL[pi_], x + v * (t - IC[3]), z, 1.75, t, i, fy, fall=T('ten') + .06 * (i % 8) if i % 2 else None, tl=up(t, IC[3] + .7 + i * .03, .35))
    for i, x in enumerate((-3.2, 3.4, -1.0)): C.append(Card(VINES[i], cam.x + x * .5 + 1.2 * math.sin(cam.yaw), cam.z + 2.4 + i * .5, .9, y=cam.y + .5 - i * .2, sway=.12, ph=i * 2, shadow=0, fog=False))
    caps(C, cam, t, [('THE CONGO', BURNT, T('congo'), T('he') - .1, .14), ('HE NEVER VISITED IT', WHITE, T('he'), T('by') - .1, .14),
                     ('MOST-CITED ESTIMATE', WHITE, T('most'), None, .215, .62), ('10 MILLION DEAD', BURNT, T('ten'), None, .14)])
    return dict(world=W4b, C=C, focus=lerp(5, 12, smooth(seg(t, IC[3], IC[3] + 2.5))), tint=(1.02, 1.0, .82), mix=.2, expo=1.28, atm=dict(col=(1, .95, .6), beam=(.10, .09, .04)),
                extra=lambda img, c, tt: [dust(img, c, (-3 + i * 1.5, .2, 10 + i), tt, T('ten') + .45 + i * .08, col=(.36, .30, .2), n=10, seed=40 + i, speed=1.5) for i in range(5)])


# ------------------------------------------------------------------ 5. Nanjing
W5 = mk((.38, .36, .35), (.12, .13, .17), (.66, .58, .54), (.46, .42, .42), 55, 16, 6)
W5c = mk((.16, .14, .14), (.04, .04, .06), (.30, .18, .14), (.16, .11, .10), 40, 14, 7)
NJH = [(-15, 27, 7, 0), (-8.5, 26, 6.5, 0), (10, 27, 7, 0), (17, 26, 6.5, 0), (-12, 20, 6, .5), (12.5, 20, 6, -.5), (-10.5, 14, 5.6, .9), (10.8, 14, 5.6, -.9), (-9.5, 8, 5.2, 1.2), (9.8, 8, 5.2, -1.2), (-22, 22, 7, 0), (23, 22, 7, 0)]
NJP = [(float(rng.uniform(-4.5, 4.5)), 5.5 + i * .6, int(rng.integers(6)), float(rng.choice([-1, 1]) * rng.uniform(.15, .5))) for i in range(24)]
def cam5(t):
    if t < IC[4]: return shot(t, B[4], IC[4], (-5.0, 1.2, -4), (-.8, 1.9, 2.5), (0, 5.0, 34))
    if t < IC[5]: return shot(t, IC[4], IC[5], (7.5, 3.6, 3.5), (4.4, 2.5, 6.2), (-.6, 2.4, 13.5))
    return shot(t, IC[5], B[5], (-2.0, .9, -1.5), (1.0, 2.2, 1.5), (0, 1.6, 14))
def sc5(t, cam):
    C = []; fy = -cam.yaw * .8
    if t >= IC[5]:                                                                                    # the memorial candles
        C += [Card(tint(HILLS[0], (.5, .5, .55)), 0, 95, 210, blur=2.2), Card(tint(GATE_CN, (.34, .32, .34)), 0, 40, 48, blur=1.4)]
        candles(C, t, IC[5] + .05, 45)
        for i, x in enumerate((-4.5, -1.5, 1.5, 4.5)): hang(C, LANTERN, x, 12 + (i % 2) * 2, 1.0, 4.4 + (i % 2) * .6, t, IC[5] + .1 + i * .12, ph=i * 1.9, swing=.5)
        caps(C, cam, t, [("CHINA'S OFFICIAL FIGURE", WHITE, T("china's"), None, .215, .7), ('300,000', BURNT, T('three', 2), None, .13, .6)])
        return dict(world=W5c, C=C, focus=9, tint=(1.08, .95, .78), mix=.2, expo=1.35, flick=.05, atm=dict(col=(1, .7, .4), beam=(.08, .04, .02)))
    C += [Card(tint(HILLS[0], (.7, .7, .8)), 0, 100, 210, blur=2.2), Card(tint(HILLS[1], (.7, .7, .8)), 30, 82, 170, blur=1.8)]; clouds(C, t, (.6, .6, .64), z=85, y=26, alpha=.7)
    tl = up(t, B[4] + .12, .55)
    if tl is not None: C.append(Card(GATE_CN, 0, 40, 52, tilt=tl, shadow=.4, blur=.7))
    for i, (x, z, w, yaw) in enumerate(NJH):
        tl = up(t, B[4] + (45 - z) * .02, .45)
        if tl is not None: C.append(Card(CNH[i % 4], x, z, w, yaw=yaw, tilt=tl, shadow=.45))
    for i, (x, z, w) in enumerate(((-19, 64, 24), (0, 70, 28), (19, 62, 24), (-40, 72, 22), (40, 74, 22))): giant(C, SOLDIER if i % 2 else SOLDF, x, z, w, t, T('japanese') - .3 + i * .22, 2.2, ph=i * 1.7, blur=1.5, sway=.3)
    for i in range(6): C.append(Card(SMOKES[i % 3], -30 + i * 12 + .8 * math.sin(t * .4 + i), 46 + (i % 2) * 6, 8, y=2 + (t * .6 + i * .7) % 4, shadow=0, blur=2.0, alpha=.75 * seg(t, T('capture'), T('capture') + 1.5)))
    hang(C, FLAG_JP, -4.6, 22, 5.0, 6.4, t, T('japanese') - .1, ph=.4, swing=.35, wv=14, fog=True); hang(C, FLAG_JP, 5.2, 28, 5.0, 7.4, t, T('troops') - .1, ph=2, swing=.35, wv=14, fog=True)
    for i, x in enumerate((-6.5, 6.5, -6.2, 6.2)): hang(C, LANTERN, x, 9 + (i // 2) * 6, .8, 3.6, t, B[4] + .5 + i * .1, ph=i * 1.9, swing=.5, fog=True)
    fallt = T('two') if t >= IC[4] else None
    for i, (x, z, pi_, v) in enumerate(NJP):
        A = t < IC[4]; xx = x + v * (t - B[4]) if A else x * .9
        ppl(C, CNP[pi_], xx, z, 1.75, t, i, fy, fall=(fallt + .05 * (i % 12)) if (fallt and i % 3) else None, tl=up(t, B[4] + .5 + i * .03, .35), bob=.05 if A else .02)
    if t >= IC[4]:
        hang(C, GAVEL, 1.2, 10.5, 3.4, 4.2, t, T('tokyo') - .15, ph=1.1, swing=.45, yaw=-cam.yaw * .7)
        if PRINTS['tribunal'] is not None: hang(C, PRINTS['tribunal'], -3.5, 17, 6.5, 4.6, t, T('tribunal') - .1, ph=2.2, swing=.3, yaw=-cam.yaw * .7)
    caps(C, cam, t, [(cal('DEC', 1937), None, T('december'), T('japanese') - .2, .27, .26), ('JAPANESE TROOPS', WHITE, T('japanese'), T('nanjing') - .15, .14), ('NANJING', BURNT, T('nanjing'), IC[4] - .2, .14, .6),
                     ('TOKYO TRIBUNAL', WHITE, T('tokyo'), T('over', 1) - .1, .14), ('200,000+ DEAD', BURNT, T('two'), None, .14), ('IN SIX WEEKS', WHITE, T('six', 2), None, .215, .52)])
    return dict(world=W5, C=C, focus=lerp(6, 16, smooth(seg(t, B[4], B[4] + 2.5))) if t < IC[4] else 10, tint=(.95, .97, 1.04), mix=.3, expo=1.3, atm=dict(col=(.9, .9, 1), fall=1.0, beam=(.06, .06, .07)),
                extra=lambda img, c, tt: [dust(img, c, (-3 + i * 1.5, .2, 10 + i), tt, T('two') + .45 + i * .08, col=(.34, .32, .32), n=10, seed=50 + i, speed=1.5) for i in range(5)])


# ------------------------------------------------------------------ 6. the Holocaust
W6 = mk((.46, .46, .48), (.07, .08, .10), (.50, .48, .48), (.40, .40, .42), 48, 16, 8)
ROWS = [(-4.2 + c * .78 + .25 * (r % 2), 9.5 + r * 1.25, (r * 11 + c) % 8) for r in range(5) for c in range(11)]
FADE = np.random.default_rng(9).permutation(len(ROWS))
def cam6(t):
    if t < IC[6]: return shot(t, B[5], IC[6], (.3, .9, -3), (.9, 1.5, 4.5), (0, 6.5, 54))
    if t < IC[7]: return shot(t, IC[6], IC[7], (-7.5, 2.4, 5.5), (-5.0, 1.9, 8.0), (.5, 2.0, 13.5))
    return shot(t, IC[7], B[6], (-6.0, 8.5, 6), (-1.2, 2.0, 22), (0, 7.0, 54))
def sc6(t, cam):
    C = [Card(tint(HILLS[0], (.5, .52, .58)), 0, 110, 230, blur=2.2)]; fy = -cam.yaw * .8
    for i in range(7): C.append(Card(RAILS, 0, max(cam.z + .6, -6) + i * 10.25 - ((max(cam.z + .6, -6)) % 10.25) + 0, 3.0, tilt=pi / 2 * .999, shadow=0))
    if PRINTS['birkenau'] is not None: giant(C, PRINTS['birkenau'], 0, 78, 70, t, B[5] - 3, blur=1.8, alpha=.85)
    tl = up(t, B[5] + .1, .55)
    if tl is not None: C.append(Card(GATEH, 0, 54, 56, tilt=tl, shadow=.4))
    for i in range(7): C.append(Card(SMOKES[i % 3], -27 + i * 9 + 1.2 * math.sin(t * .35 + i), 62 + (i % 2) * 6, 9, y=4 + (t * .7 + i * .9) % 5, shadow=0, blur=2.2, alpha=.7))
    for i in range(14):
        z = 5 + (i // 2) * 7; tl = up(t, B[5] + (54 - z) * .012, .4)
        if tl is not None: C.append(Card(FENCE, (-1) ** i * 6.2, z + 3.5, 7.0, yaw=pi / 2, tilt=0, shadow=.3, alpha=1 - tl / (pi / 2)))
    for i, (x, z) in enumerate(((-10, 18), (10, 22), (-10, 40), (10, 44))):
        tl = up(t, B[5] + .25 + i * .08, .5)
        if tl is not None: C.append(Card(WTOWER, x, z, 4.2, tilt=tl, shadow=.5))
    if IC[6] <= t < IC[7]:
        for i, (x, z, k) in enumerate(ROWS):
            a = 1 - seg(t, T('men') + FADE[i] / len(ROWS) * 1.7, T('men') + FADE[i] / len(ROWS) * 1.7 + .35)
            if a > .02: ppl(C, COATS[k], x, z, 1.25 if k in (2, 6) else 1.78, t, i, fy, bob=.012, alpha=a)
        for i, x in enumerate((-3.6, -1.6, .4, 2.4, 4.2)): hang(C, STAR, x - 1.5, 7.2 + (i % 2) * 1.3, .85, 3.3 + (i % 3) * .35, t, T('jewish') - .2 + i * .09, ph=i * 1.7, swing=.5)
    yr = 1941 + min(4, int(seg(t, T('to') - .1, T('five', 3) + .2) * 5))
    caps(C, cam, t, [(cal('YEAR', yr), None, T('nineteen', 2), T('nazi') - .2, .27, .26), ('NAZI GERMANY', WHITE, T('nazi'), IC[6] - .2, .14), ('AND ITS COLLABORATORS', WHITE, T('collaborators'), IC[6] - .2, .215, .62),
                     ('6 MILLION', BURNT, T('six', 3), IC[7] - .2, .13, .66), ('JEWISH MEN, WOMEN AND CHILDREN', WHITE, T('jewish'), IC[7] - .2, .215, .86),
                     ('ABOUT 1 MILLION', BURNT, T('one', 5), T('auschwitz') - .15, .14), ('IN A SINGLE PLACE', WHITE, T('single'), T('auschwitz') - .15, .215, .6), ('AUSCHWITZ', BURNT, T('auschwitz'), None, .14, .7)])
    return dict(world=W6, C=C, focus=lerp(5, 20, smooth(seg(t, B[5], B[5] + 3))) if t < IC[6] else (11 if t < IC[7] else 30), tint=(.94, .97, 1.05), mix=.55, expo=1.3, atm=dict(col=(.85, .85, .9), fall=1.3, beam=(.03, .03, .04), n=70),
                lights=[((-10, 9.5, 18), .9, .5, 0), ((10, 9.5, 22), 2.2, .42, 2), ((10, 9.5, 44), 2.0, .6, 4)])


# ------------------------------------------------------------------ 7. Cambodia
W7 = mk((.36, .40, .22), (.26, .12, .12), (.94, .60, .28), (.62, .40, .26), 60, 16, 9)
PALMS = [(float(rng.uniform(-36, 36)), float(z), float(rng.uniform(7, 11)), int(rng.integers(5))) for z in (52, 46, 40, 34, 28) for _ in range(5)]
GRID = [(-3.6 + c * 1.45 + .3 * (r % 2), 8.5 + r * 1.5) for r in range(4) for c in range(6)]
def cam7(t):
    if t < IC[8]: return shot(t, B[6], IC[8], (-5.5, 1.2, -4), (-1.2, 2.0, 2.0), (0, 6.0, 40))
    return shot(t, IC[8], B[7], (7.2, 4.6, 1.5), (3.6, 2.6, 4.5), (0, 1.8, 12.5))
def sc7(t, cam):
    C = [Card(tint(HILLS[0], (.6, .45, .45)), 0, 110, 230, blur=2.2)]; fy = -cam.yaw * .8; A = t < IC[8]
    clouds(C, t, (1, .6, .4), z=95, y=28, w=36)
    gs = PRINTS['polpot'] if PRINTS['polpot'] is not None else CADREG
    giant(C, gs, 3, 84, 30 if gs is not CADREG else 17, t, T('khmer') - .3, 2.4, ph=1, blur=1.5, sway=.4)
    tl = up(t, B[6] + .1, .55)
    if tl is not None: C.append(Card(TEMPLE, 0, 62, 62, tilt=tl, shadow=.3, blur=1.0))
    for i, (x, z, hh, k) in enumerate(PALMS):
        tl = up(t, B[6] + (56 - z) * .02, .45)
        if tl is not None and abs(x) > 5: C.append(Card(JUNGLE[k], x, z, hh * 700 / 1100, tilt=tl, sway=.3, ph=i, shadow=.4))
    for i, (x, z) in enumerate(((-9, 22), (9.5, 21), (-12, 15), (12, 14))):
        tl = up(t, B[6] + .5 + i * .06, .4)
        if tl is not None: C.append(Card(HUTS[i % 3], x, z, 4.2, tilt=tl, shadow=.5))
    for i, x in enumerate((-6.5, -2.2, 2.2, 6.5)): hang(C, FLAG_RED, x, 18 + (i % 2) * 5, 3.4, 6.2 + (i % 2), t, T('takes') - .15 + i * .1, ph=i * 1.4, swing=.35, wv=14, fog=True)
    if A:
        for i in range(14): r = np.random.default_rng(90 + i); ppl(C, FARM[i % 6], r.uniform(-6, 6), 4.5 + i * .9, 1.7, t, i, fy, tl=up(t, B[6] + .4 + i * .04, .35), bob=.09)
        for i in range(7): ppl(C, CADRES[i % 3], -13 + (t - T('khmer')) * 2.6 - i * 1.3, 11.5, 1.95, t, i * 2, fy, bob=.07) if t > T('khmer') - .2 else None
    else:
        for i, (x, z) in enumerate(GRID): ppl(C, FARM[i % 6], x, z, 1.75, t, i, fy, fall=T('die', 2) - .1 + .05 * (i % 6) if i % 4 == 1 else None, bob=.02)
        for i in range(4): ppl(C, CADRES[i % 3], -6.5 + i * 4.4, 15.5, 2.1, t, i, fy, bob=.01)
    yr = 1975 + min(4, int(seg(t, T('under') - .1, T('years', 3) + .35) * 5))
    caps(C, cam, t, [(cal('YEAR', 1975), None, T('nineteen', 3), T('khmer') - .2, .27, .26), ('KHMER ROUGE', BURNT, T('khmer'), IC[8] - .2, .14), ('TAKES OVER CAMBODIA', WHITE, T('takes'), IC[8] - .2, .215, .64),
                     ('UNDER 4 YEARS', WHITE, T('under'), T('between') + .3, .14), (cal('YEAR', yr), None, T('under'), T('between') + .3, .29, .26),
                     ('1.5 – 2 MILLION DEAD', BURNT, T('one', 6), None, .14), ('A QUARTER OF THE COUNTRY', WHITE, T('quarter') - .2, None, .215, .78)])
    return dict(world=W7, C=C, focus=lerp(6, 16, smooth(seg(t, B[6], B[6] + 2.5))) if A else 10, tint=(1.08, .94, .80), mix=.25, expo=1.28, atm=dict(col=(1, .7, .4), beam=(.12, .06, .03)),
                extra=lambda img, c, tt: [dust(img, c, GRID[i * 4 + 1] [0:1] + (.2, GRID[i * 4 + 1][1]), tt, T('die', 2) + .35, col=(.4, .36, .2), n=8, seed=60 + i, speed=1.4) for i in range(6)])


# ------------------------------------------------------------------ 8. Rwanda
W8 = mk((.50, .32, .22), (.20, .28, .40), (.92, .74, .48), (.62, .56, .46), 65, 16, 10)
RTREES = [(float(rng.uniform(-36, 36)), float(z), float(rng.uniform(6, 9)), int(rng.integers(5))) for z in (48, 42, 36, 30, 25) for _ in range(4)]
RPOS = [(float(rng.uniform(-5.5, 5.5)), 5.5 + i * .6, int(rng.integers(6)), float(rng.choice([-1, 1]) * rng.uniform(.1, .4))) for i in range(25)]
def cam8(t):
    if t < IC[9]: return shot(t, B[7], IC[9], (5.5, 1.2, -4), (1.2, 2.2, 2.0), (0, 6.0, 40))
    return shot(t, IC[9], B[8], (-7.0, 4.0, 1.5), (-3.6, 2.4, 5.0), (.4, 1.8, 13))
def sc8(t, cam):
    C = []; fy = -cam.yaw * .8; A = t < IC[9]
    for i, (z, w, x) in enumerate(((115, 240, 0), (88, 190, -30), (66, 150, 25))):
        tl = up(t, B[7] + i * .12, .5)
        if tl is not None: C.append(Card(GHILL[i], x + 1.5 * math.sin(t * .2 + i), z, w, tilt=tl, blur=2.2 - i * .5, shadow=0))
    clouds(C, t, (1, .9, .8), z=100, y=30, w=36)
    giant(C, RADIO, 0, 80, 62, t, T('rwanda') + .15, 2.2, ph=.5, blur=1.3, sway=.35)
    for i in range(3):
        k = ((t * .7 + i / 3) % 1); a = (1 - k) * seg(t, T('rwanda') + 1.6, T('rwanda') + 2.4)
        if a > .03: C.append(Card(ARC, 0, 79.5 - i * .1, 40 + 60 * k, y=22 - 30 * k, shadow=0, alpha=a * .8, blur=1.5, fog=False))
    for i, (x, z, hh, k) in enumerate(RTREES):
        tl = up(t, B[7] + (52 - z) * .02, .45)
        if tl is not None and abs(x) > 5: C.append(Card(JUNGLE[k], x, z, hh * 700 / 1100, tilt=tl, sway=.25, ph=i, shadow=.4))
    for i, (x, z) in enumerate(((-9, 24), (9.5, 23), (-12, 17), (12, 16), (-4, 28), (5, 29), (-18, 30), (19, 31))):
        tl = up(t, B[7] + .5 + i * .05, .4)
        if tl is not None: C.append(Card(HUTS[i % 3], x, z, 4.2, tilt=tl, shadow=.5))
    for i, (x, z, pi_, v) in enumerate(RPOS):
        ppl(C, RWP[pi_], x + (v * (t - B[7]) if A else v * (IC[9] - B[7])), z, 1.75, t, i, fy, fall=T('eight', 2) + .07 * (i % 14) if i % 4 else None, tl=up(t, B[7] + .5 + i * .03, .35), bob=.05 if A else .02)
    day = 1 + int(99 * seg(t, T('about', 5), T('days') + .3))
    caps(C, cam, t, [('RWANDA', BURNT, T('rwanda'), T('about', 5) - .15, .14, .6), (cal('YEAR', 1994), None, T('nineteen', 4), T('about', 5) - .15, .27, .26),
                     ('ABOUT 100 DAYS', WHITE, T('about', 5), IC[9] + .35, .14), (cal('DAY', day), None, T('about', 5), IC[9] + .35, .29, .26),
                     ('UP TO 800,000 KILLED', BURNT, T('eight', 2), None, .14), ('MOST OF THEM TUTSI', WHITE, T('most', 2), None, .215, .64)])
    return dict(world=W8, C=C, focus=lerp(6, 16, smooth(seg(t, B[7], B[7] + 2.5))) if A else 10, tint=(1.06, .97, .84), mix=.2, expo=1.28, atm=dict(col=(1, .85, .6), beam=(.11, .07, .04)),
                extra=lambda img, c, tt: [dust(img, c, (-3 + i * 1.5, .2, 9 + i), tt, T('eight', 2) + .5 + i * .12, col=(.5, .34, .24), n=10, seed=70 + i, speed=1.5) for i in range(5)])


# ------------------------------------------------------------------ 9. outro
W9 = mk((.15, .13, .13), (.03, .03, .05), (.34, .19, .13), (.15, .10, .09), 42, 14, 11)
def cam9(t): return shot(t, B[8], DUR, (2.5, 1.0, -1.0), (-1.2, 2.9, -4.0), (0, 2.8, 12))
def sc9(t, cam):
    C = [Card(tint(HILLS[0], (.5, .5, .55)), 0, 95, 210, blur=2.2)]
    candles(C, t, B[8] - 3, 60)
    for n in range(1, 8): hang(C, NUMS[n], (n - 4) * 1.6, 11 + .45 * abs(n - 4), 1.3 * (1 + (.12 * math.exp(-(t - T('recent')) * 2.5) if n == 7 and t > T('recent') else 0)), 3.6 + .5 * (n % 2), t, B[8] + .02 + n * .05, ph=n * 1.3, swing=.3)
    caps(C, cam, t, [('THE MOST RECENT', WHITE, T('most', 3), T('just', 2) - .1, .14), ('JUST OVER 30 YEARS AGO', BURNT, T('just', 2), T('follow') - .15, .14), ('FOLLOW FOR MORE', BURNT, T('follow'), None, .14)])
    return dict(world=W9, C=C, focus=10, tint=(1.08, .95, .78), mix=.2, expo=1.35, flick=.05, atm=dict(col=(1, .7, .4), beam=(.08, .04, .02)))


SCENES = [(cam1, sc1), (cam2, sc2), (cam3, sc3), (cam4, sc4), (cam5, sc5), (cam6, sc6), (cam7, sc7), (cam8, sc8), (cam9, sc9)]
def scene_of(t): return max(i for i in range(9) if t >= B[i])


def render(f):
    t = min(f / FPS, DUR - .001); i = scene_of(t); cf, sf = SCENES[i]; cam = cf(t); pt = max(B[i], t - 1 / FPS); prev = cf(pt)
    S = sf(t, cam); wd = S['world']; wd.focus = S['focus']
    img = wd.render(cam, S['C'], f, t, S.get('extra'))
    for src, a0, spd, ph in S.get('lights', ()): img = searchlight(img, cam, t, src, a0, spd, ph)
    img = S1.motes(img, cam, t) if i == 0 else atmos(img, cam, t, **S.get('atm', {}))
    cutk = max(math.exp(-abs(t - c) * 16) for c in CUTS)
    if not any(pt < c <= t for c in CUTS):
        ox = (cam.yaw - prev.yaw) * cam.f
        if abs(ox) > 3: img = dir_blur(img, ox * .8, 0)
    if cutk > .08: img = zoom_blur(img, .22 * cutk, 10)
    fl = S.get('flick', .015); expo = S['expo'] * smooth(seg(t, 0, .5)) * (1 - .95 * ein(seg(t, DUR - .35, DUR), 2)) * (1 + .25 * cutk) * (1 + fl * math.sin(t * 11.3) + fl * .7 * math.sin(t * 17.9 + 1) + .03 * math.sin(t * .9))
    img = post(img, f, tilt=0.9, expo=expo)
    lum = img.mean(2, keepdims=True); m = S['mix']; img = np.clip(img * (1 - m) + lum * np.float32(S['tint']) * m, 0, 1)
    return (img * 255 + .5).astype(np.uint8)


# ------------------------------------------------------------------ sound (kept low under the voice)
def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); R = np.random.default_rng(4)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    def noise(d, lo, hi): return film._filt(R.normal(0, 1, int(d * SR)), lo, hi)
    def env(x, a=.5, r=.5): m = len(x); e = np.minimum(1, np.minimum(np.arange(m) / (a * SR), (m - np.arange(m)) / (r * SR))); return x * e
    def bell(f0, d=5.0): t2 = np.arange(int(d * SR)) / SR; return sum(a * np.sin(2 * np.pi * f0 * m * t2) * np.exp(-t2 / dc) for m, a, dc in ((1, .5, 2.6), (2, .35, 1.8), (2.38, .2, 1.2), (3, .16, .9), (4, .1, .6), (.5, .3, 3.2)))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .055)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)
    for c in CUTS: add(film.whoosh(.6, 200, 2400, .55), c - .3, .15)
    for b in B[:-1] + IC[2:]:
        for i in range(16): add(film.nburst(.09, 900, 5000, .02), b + .08 + i * .05, .024, (-1) ** i * .5)                        # sets popping up
    caps_t = [T('just'), T('disease'), T('half'), T('black'), T('thirteen'), T("that's"), T('give'), T('six'), T('twelve'), T('captive'), T('one', 3), T('king'), T('personal'), T('congo'), T('ten'),
              T('japanese'), T('nanjing'), T('two'), T('three', 2), T('nazi'), T('six', 3), T('one', 5), T('auschwitz'), T('khmer'), T('one', 6), T('quarter'), T('rwanda'), T('eight', 2), T('most', 2), T('just', 2), T('follow')]
    for tl in caps_t: add(film.thump(82, 32, .6, .14), tl, .17); add(film.nburst(.25, 300, 3000, .04), tl, .05)
    for tf in (T('half'), T('died'), T('ten'), T('two'), T('die', 2), T('eight', 2)):
        for i in range(14): add(film.nburst(.08, 900, 4500, .02), tf + .3 + i * .05, .028, (-1) ** i * .5)                           # paper figures falling
    for tb, f0, g in ((T('black'), 196, .10), (T('thirteen'), 196, .06), (T('one', 2), 262, .05), (T('died'), 165, .07), (T('ten'), 147, .07), (T('three', 2), 196, .08), (T('auschwitz'), 131, .09),
                      (T('quarter'), 110, .07), (T('eight', 2), 147, .07), (T('just', 2), 196, .09), (T('follow'), 262, .06)): add(bell(f0), tb, g)
    add(env(noise(B[3] - B[2], 120, 900) * (.6 + .4 * np.sin(2 * np.pi * .22 * np.arange(int((B[3] - B[2]) * SR)) / SR))), B[2], .05)      # sea
    for tc in np.arange(B[2] + 1, B[3], 2.3): add(env(noise(.5, 180, 420), .1, .3) * np.sin(2 * np.pi * 7 * np.arange(int(.5 * SR)) / SR), tc, .05, .4)   # hull creak
    for td in np.arange(IC[3], B[4], .52): add(film.thump(70, 40, .5, .2), td, .09); add(film.thump(95, 50, .4, .12), td + .26, .05)   # distant drums
    add(env(noise(B[5] - B[4], 200, 700), 1, 1), B[4], .03); add(env(noise(B[6] - B[5], 150, 600), 1, 1), B[5], .04)                 # wind
    for i in range(3): add(film.thump(180, 90, .5, .08), T('tribunal') + i * .22, .12)                                              # gavel
    for tr in np.arange(B[5] + .2, IC[6], .42): add(film.thump(60, 45, .5, .07), tr, .07); add(film.thump(60, 45, .5, .07), tr + .11, .05)   # rails
    add(bell(73, 6), B[6] + .1, .10)                                                                                                # gong
    st = noise(IC[9] - B[7], 1500, 6000) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 3.1 * np.arange(int((IC[9] - B[7]) * SR)) / SR + 1))); add(env(st, .3, .3), B[7], .012)   # radio static
    cw = int(.25 * SR); t3 = np.arange(cw) / SR; caw = np.sin(2 * np.pi * (900 - 500 * t3 / .25) * t3) * np.sin(np.pi * t3 / .25) * (.6 + .4 * np.sign(np.sin(2 * np.pi * 70 * t3)))
    for tc in (S2.CUT2 + .5, S2.CUT2 + .85, S2.CUT2 + 2.4, B[4] + 1.2, B[4] + 1.6): add(caw, tc, .028, .4)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.3 * SR):] *= np.linspace(1, 0, int(.3 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (360, 640), interpolation=cv2.INTER_AREA)[..., ::-1])
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
    elif mode == 'mux':
        out = sys.argv[2]; dst = sys.argv[3]; sfx = dst + '.sfx.wav'; soundtrack(sfx); lst = dst + '.txt'
        open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in sorted(glob.glob(f'{out}/seg_*.mp4'))))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', VOICE, '-i', sfx,
                        '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={DUR - .2}:d=0.2,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                        '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', dst], check=True)
        os.remove(sfx); os.remove(lst); print('done', dst)
