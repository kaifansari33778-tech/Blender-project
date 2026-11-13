"""NVIDIA spy story - full video (paper-diorama, 24 shots timed to the voice-over word timings).
Usage: python3 show.py render <outdir> [a-b]   |   python3 show.py stills <dir> t1,t2,...   |   python3 show.py mux <outdir> <out.mp4>"""
import sys, os, math, json, glob, subprocess, wave as wavmod
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art

VOICE = os.path.join(HERE, 'voice', 'full_v2.mp3'); DUR = 102.95
WORDS = json.load(open(os.path.join(HERE, 'voice', 'words_v2.json')))
PH = os.path.join(HERE, 'photos')


def T(w, n=1):
    k = 0
    for x, a, b in WORDS:
        if x.split('(')[0] == w:
            k += 1
            if k == n: return a
    raise KeyError(w)


def fit(spr, w=None, h=None):
    k = (w / spr.shape[1]) if w else (h / spr.shape[0])
    return cv2.resize(spr, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def WM(key):
    f = sorted(glob.glob(os.path.join(PH, 'wm', key + '_0.*')))
    f = [x for x in f if not x.endswith('.svg')] or f
    if f and f[0].endswith('.svg'):                                           # rasterise once
        png = f[0][:-4] + '.png'
        r = subprocess.run(['node', os.path.join(HERE, '..', '..', 'tools', 'svg2png.js'), f[0], png], capture_output=True)
        return png if os.path.exists(png) else None
    return f[0] if f and cv2.imread(f[0], cv2.IMREAD_UNCHANGED) is not None else None


def L(txt, w, col=ORANGE): return fit(art.label(txt, 150, col=col, seed=len(txt)), w)
def ST(txt, w, col=art.RED): return fit(art.stamp(txt, 120, col, seed=len(txt)), w)
def WHITE(txt, w): return L(txt, w, np.array([.95, .93, .86], np.float32))
def logo(key, w, fallback): return fit(art.sticker(WM(key), 600), w) if WM(key) else WHITE(fallback, w)
def sealspr(key, txt, w): return fit(art.sticker(WM(key), 500), w) if WM(key) else fit(art.seal(txt), w)
def printspr(key, w, fallback=None, **kw): return art.photo_print(WM(key), w=w, **kw) if WM(key) else fallback


# ------------------------------------------------------------------ assets
B = os.path.join(PH, 'user_bench.jpg'); CHAIR = [(120, 360, 50), (115, 450, 50), (110, 540, 50), (120, 640, 50), (150, 325, 35), (75, 700, 50)]
AP = os.path.join(PH, 'user_alice_portrait.jpg'); _abg = [(90, 150, 85), (60, 330, 60), (825, 110, 80), (860, 320, 55), (100, 560, 85), (55, 690, 45), (870, 600, 45), (880, 820, 40), (150, 905, 55), (55, 850, 40), (170, 40, 50), (760, 30, 40)]
ABUST = art.photo_cutout(AP, (150, 2, 660, 600), out_h=800, clip_y=600, fg_hint=[(460, 210, 90), (460, 480, 110)], bg_hint=_abg)
AFULL = art.photo_cutout(AP, (80, 2, 730, 933), out_h=900, fg_hint=[(460, 210, 90), (460, 640, 150), (230, 745, 25)], bg_hint=_abg)
JP = os.path.join(PH, 'user_jensen_portrait.jpg')
JSEAT = art.photo_cutout(JP, (80, 12, 550, 688), out_h=900, fg_hint=[(300, 150, 70), (350, 480, 150)], bg_hint=[(100, 120, 80), (120, 245, 40), (500, 110, 90), (480, 240, 45), (610, 200, 60), (40, 200, 40), (650, 40, 40), (40, 40, 40)])
PAIR = art.photo_print(B, (60, 180, 820, 900), w=560, caption_h=70)
EMBR = art.photo_print(os.path.join(PH, 'user_embrace.jpg'), (330, 340, 675, 1100), w=520, caption_h=70)
LJ = os.path.join(PH, 'user_lori_jensen.webp')
LORI = art.photo_cutout(LJ, (40, 65, 195, 330), out_h=700, clip_y=390, fg_hint=[(160, 150, 45), (140, 300, 60)], bg_hint=[(30, 80, 30), (250, 60, 20), (20, 250, 15)])
COUPLE = art.photo_cutout(LJ, (30, 20, 425, 623), out_h=900, fg_hint=[(160, 150, 45), (140, 400, 70), (280, 100, 50), (330, 350, 90), (320, 560, 60)], bg_hint=[(30, 40, 30), (450, 40, 20), (110, 30, 25), (460, 300, 10)])
XI = art.photo_cutout(os.path.join(PH, 'xi_0.jpg'), (20, 60, 790, 1094), out_h=800, fg_hint=[(410, 350, 170), (410, 900, 200), (150, 1030, 90), (690, 1030, 90)],
                      bg_hint=[(80, 150, 70), (740, 150, 70), (50, 480, 40), (775, 460, 35), (60, 650, 30), (770, 640, 25), (90, 300, 80)])
JHEAD = art.photo_cutout(JP, (185, 12, 220, 262), out_h=700, clip_y=268, cell=4.5, fg_hint=[(298, 150, 70)], bg_hint=[(110, 100, 45), (490, 100, 45), (298, 4, 6)])
JBUST = art.photo_cutout(JP, (80, 12, 550, 400), out_h=700, clip_y=400, fg_hint=[(300, 150, 70), (330, 340, 60)], bg_hint=[(100, 120, 80), (120, 245, 40), (500, 110, 90), (480, 240, 45), (610, 200, 60), (40, 200, 40), (650, 40, 40), (40, 40, 40)])
MAN = art.collage_man(JHEAD, 330); EXEC = art.man(300, 500)
BAR = art.bar(); CHIP = art.chip(); SCHIP = fit(CHIP, 150); BILLS = [art.bill(seed=i) for i in range(3)]
FLAG = art.flag(900, 600); F_US = art.flag_us(900, 480); F_TW = art.flag_tw(600, 400); F_MY = art.flag_my(700, 350)
NVCARD = fit(art.nv_card(), 470); NVS = fit(art.nv_sticker(), 240)
RAYS = art.rays(1800); RAYS_R = art.rays(1800, 12, art.RED, 0.55); RAYS_O = art.rays(1800, 16, ORANGE, 0.5); RAYS_G = art.rays(1800, 14, art.NVG, 0.4)
DOCS = [art.doc(seed=i) for i in range(4)]; TAPE = art.tape(); PIN = art.pin(); PIN_Y = art.pin(col=art.YEL)
BLDG = [art.building(240 + 40 * i, 800 + 170 * i, seed=i) for i in range(3)]
RIDGE_A = art.ridge(2600, 620, 1, dark=0.82); RIDGE_B = art.ridge(2600, 620, 7, dark=0.62, amp=200)
TOWER = art.tower(5, seed=3); T_TOP = art.tower(3, seed=40, torn_bot=True); T_LOW = art.tower(3, seed=3, torn_top=True)
DIAL = art.dial(); HAND = art.hand()
CROWN = art.crown(); HEART = art.heart(); GLASS = art.glass(); CAR = art.car(); CRATE = art.crate(); FOLDER = art.folder(); CAMERA = art.camera()
GLOBE = art.globe(); REEL = art.reel(); PHONE = art.phone()
FAR = cv2.GaussianBlur(newsprint(1024, 1024, 77, PAPER, 0.30, cols=4), (0, 0), 5); FAR = rgba(FAR, np.ones((1024, 1024), np.float32))
CANYON = np.zeros((2048, 2048, 4), np.float32)
CANYON[:, :700] = art.wall(700, 2048, 5, 0.50, 'r'); CANYON[:, 1348:] = art.wall(700, 2048, 9, 0.44, 'l'); CANYON = cv2.GaussianBlur(CANYON, (0, 0), 2.2)
SEAL_CIA = sealspr('cia', 'CIA', 250); SEAL_NSA = sealspr('nsa', 'NSA', 250); SEAL_FBI = sealspr('fbi', 'FBI', 250); SEAL_DOJ = sealspr('doj', 'DOJ', 230)
EMBLEM = sealspr('cn_emblem', 'MSS', 300) if not WM('mss') else fit(art.sticker(WM('mss'), 500), 300)
HSBC = logo('hsbc', 460, 'HSBC'); NYT = logo('nyt_logo', 800, 'THE NEW YORK TIMES'); MEGA = WHITE('MEGASPEED', 640)
P_CCTV = printspr('cctv_hq', 420, fit(BLDG[2], 300)); P_NVHQ = printspr('nvhq', 620, fit(BLDG[1], 300)); P_GPU = printspr('gpu', 380, fit(CHIP, 300))
P_TAIPEI = printspr('taipei', 760, fit(BLDG[2], 360)); P_NYTB = printspr('nyt_bldg', 420, fit(BLDG[2], 300)); P_CAP = printspr('capitol', 820, fit(BLDG[0], 400))
P_DC = printspr('datacenter', 460, fit(BLDG[1], 320)); P_STAGE = printspr('jensen_stage', 820, fit(NVCARD, 700)); P_PET = printspr('petronas', 330, fit(BLDG[2], 260))
NEWS = art.page(900, 1300)                                                 # front page that carries the pair photo
_p = fit(PAIR, 640)[:, :, :]; art.paste(NEWS, _p, 130, 270)


# ------------------------------------------------------------------ element system
class El:
    def __init__(self, **k): self.__dict__.update(k)


_n = [0]
def E(spr, x, y, s=1.0, r=0.0, d=0.0, t=None, a='pop', dur=None, wob=0.02, sh=0.5, wv=0, spin=0.0, out=None, blur=None, alpha=1.0, quiet=False):
    _n[0] += 1
    dur = dur or {'pop': .22, 'slam': .12, 'drop': .38, 'rise': .38, 'L': .34, 'R': .34, 'fade': .3, 'none': .1}[a]
    t0 = None if t is None else (t - dur if a == 'slam' else t - 0.12 if a in ('drop', 'rise', 'L', 'R') else t)
    return El(kind='el', spr=spr, x=x, y=y, s=s, r=r, d=d, t=t0, hit=t, a=a if t is not None else 'none', dur=dur, wob=wob, sh=sh, wv=wv, spin=spin, out=out, blur=blur, alpha=alpha, ph=_n[0] * 1.7, quiet=quiet)
def S(pts, t, dur=0.35, col=ORANGE, w=12, d=0.0, dash=False): return El(kind='stroke', pts=pts, t=t, dur=dur, col=np.asarray(col, np.float32), w=w, d=d, dash=dash)
def Fn(fn): return El(kind='fn', fn=fn)
def BG(rays, y=-200, spin=0.3): return E(rays, 0, y, 1.5, d=0.9, sh=0, spin=spin, wob=0, blur=2)
def grid(spr, pts, t0, step=0.07, s=1.0, d=-0.1, a='pop'): return [E(spr, x, y, s, r=0.15 * (-1) ** i, d=d, t=t0 + i * step, a=a) for i, (x, y) in enumerate(pts)]
def arc(x0, y0, x1, y1, bend=0.2, n=24): return [(lerp(x0, x1, i / n) - (y1 - y0) * bend * math.sin(math.pi * i / n), lerp(y0, y1, i / n) + (x1 - x0) * bend * math.sin(math.pi * i / n)) for i in range(n + 1)]
def circ(cx, cy, rx, ry, n=70): return [(cx + rx * math.cos(a) * (1 + .03 * math.sin(3 * a)), cy + ry * math.sin(a) + 4 * a) for a in np.linspace(-2.0, -2.0 + 6.9, n)]
def eyes(spr, x, y, s=1.0): return x + (0.47 - 0.5) * spr.shape[1] * s, y + (0.345 - 0.5) * spr.shape[0] * s


def rain(sprs, t0, t1, n, seed, s=0.6, spread=540):
    def fn(fr, t, ox, oy):
        for i in range(n):
            r = np.random.default_rng(seed * 100 + i); ts = lerp(t0, t1, r.random()); dt = t - ts
            if dt <= 0 or dt > 3.2: continue
            fr.put(sprs[i % len(sprs)], ox + r.uniform(-spread, spread) + 80 * math.sin(dt * 3.5 + i), oy - 1150 + 620 * dt + 260 * dt * dt, s * r.uniform(.8, 1.2), rot=r.uniform(0, 6) + math.sin(dt * 5 + i),
                   depth=(-0.35, 0.1, 0.35)[i % 3], sy=abs(math.cos(dt * 6 + i)) * .8 + .2, shadow=0.35)
    return Fn(fn)


def stroke(fr, pts, k, col, width, depth=0.0, dash=False):
    if k <= 0: return
    n = max(2, int(len(pts) * cl(k)))
    sp = np.int32([fr.w2s(x, y, depth) for x, y in pts[:n]]); wd = max(1, int(width * fr.cam.z))
    segs = [sp[i:i + 2] for i in range(0, n - 1, 2)] if dash else [sp]
    sh = fr.c.copy(); cv2.polylines(sh, [q + np.int32([5, 8]) for q in segs], False, (0, 0, 0), wd, cv2.LINE_AA)
    fr.c = cv2.addWeighted(sh, 0.25, fr.c, 0.75, 0)
    cv2.polylines(fr.c, segs, False, tuple(float(v) for v in col), wd, cv2.LINE_AA)


def draw_el(fr, e, t, ox, oy):
    if e.kind == 'fn': e.fn(fr, t, ox, oy); return
    if e.kind == 'stroke':
        stroke(fr, [(ox + x, oy + y) for x, y in e.pts], eio(seg(t, e.t, e.t + e.dur), 2), e.col, e.w, e.d, e.dash); return
    if e.t is not None and t < e.t: return
    k = 1.0 if e.t is None else seg(t, e.t, e.t + e.dur)
    x, y, s, r, al, a = e.x, e.y, e.s, e.r, e.alpha, e.a
    if a == 'pop': s *= back(k, 2.0)
    elif a == 'slam': s *= lerp(2.8, 1, k * k) * (1 + 0.06 * math.exp(-max(0, t - e.hit) * 18) * (k >= 1)); al *= min(1, k * 2.5); r += (1 - k) * 0.25
    elif a == 'drop': y -= 1700 * (1 - back(k, 1.3)); r += (1 - k) * .3
    elif a == 'rise': y += 1700 * (1 - back(k, 1.3))
    elif a == 'L': x -= 1400 * (1 - eout(k, 3)); r -= (1 - k) * .25
    elif a == 'R': x += 1400 * (1 - eout(k, 3)); r += (1 - k) * .25
    elif a == 'fade': al *= k
    if e.out is not None:
        ko = seg(t, e.out, e.out + .22)
        if ko >= 1: return
        s *= 1 - ko * ko
    if s <= 0.01: return
    r += e.wob * math.sin(t * 1.4 + e.ph) + e.spin * t
    if e.wob: y += 5 * math.sin(t * 1.1 + e.ph)
    fr.put(wave(e.spr, t + e.ph, e.wv) if e.wv else e.spr, ox + x, oy + y, s, r, e.d, al, shadow=e.sh, blur=e.blur)


# ------------------------------------------------------------------ custom bits
SWCROWN = art.shape([[(.3, .1), (.7, .1), (.7, 1), (.3, 1)], [(.15, 0), (.85, 0), (.85, .35), (.15, .35)]], 150, 150, (.14, .12, .10), 5)
def stopwatch(fr, t, ox, oy):
    t0 = T('give'); k = back(seg(t, t0 - .1, t0 + .2), 2.2)
    fr.put(SWCROWN, ox, oy - 40 - 470 * k, k, anchor=(0.5, 1), shadow=0.5)
    fr.put(DIAL, ox, oy - 40, 1.06 * k, rot=lerp(-0.5, 0, k), shadow=0.6, sh_off=(18, 30))
    ticks = np.floor(seg(t, t0 + .1, t0 + 2.3) * 28) / 28
    fr.put(HAND, ox, oy - 40, k, rot=ticks * 2 * math.pi * 0.9, anchor=(0.5, 0.86), depth=-0.03, shadow=0.6, sh_off=(8, 14))
    cv2.circle(fr.c, tuple(int(v) for v in fr.w2s(ox, oy - 40)), max(2, int(26 * fr.cam.z * k)), tuple(float(v) for v in INK), -1, cv2.LINE_AA)


def orbit(items, t0, cy=-40, R=600):
    def fn(fr, t, ox, oy):
        for i, (sp, sc) in enumerate(items):
            k = back(seg(t, t0 + i * 0.08, t0 + i * 0.08 + .22), 2.4)
            if k <= 0: continue
            a = i / len(items) * 2 * math.pi + t * 0.5; rr = (R + 60 * (i % 2))
            fr.put(sp, ox + math.cos(a) * rr * 0.82, oy + cy + math.sin(a) * rr * 1.25, sc * k, rot=math.sin(t * 2 + i) * .25, depth=(-0.25, 0.25)[i % 2], shadow=0.5)
    return Fn(fn)


def crates(path, t0, t1, n=6):
    def fn(fr, t, ox, oy):
        if t < t0: return
        for i in range(n):
            u = ((t - t0) * 0.42 + i / n) % 1.0
            if (t - t0) * 0.42 + i / n < i / n + 0.001 and i > (t - t0) * 6: continue
            j = u * (len(path) - 1); a, b = path[int(j)], path[min(len(path) - 1, int(j) + 1)]; f = j - int(j)
            fr.put(CRATE, ox + lerp(a[0], b[0], f), oy + lerp(a[1], b[1], f), 0.55 * min(1, u * 8) * min(1, (1 - u) * 8), rot=0.2 * math.sin(i + t * 3), depth=-0.05, shadow=0.5)
    return Fn(fn)


def closer(fr, t, ox, oy):
    t0, t1 = T('she', 5), T('closer') + 0.45
    k = eio(seg(t, t0, t1), 2); x = lerp(430, 215, k)
    fr.put(A_M, ox - x, oy - 40, 1, rot=-0.04 + 0.02 * math.sin(t * 2), shadow=0.6)
    fr.put(J_M, ox + x, oy - 60, 1, rot=0.04 + 0.02 * math.sin(t * 2 + 1), shadow=0.6)
A_M = fit(ABUST, h=700); J_M = fit(JBUST, h=700)


def drive(fr, t, ox, oy):
    t0 = T('they'); k = eout(seg(t, t0 - .1, t0 + .75), 3); x = lerp(-1300, 0, k) + 60 * seg(t, t0 + .75, t0 + 2.2); y = 330 + 5 * math.sin(t * 22)
    fr.put(A_C, ox + x - 62, oy + y - 138, 1, shadow=0); fr.put(J_C, ox + x + 150, oy + y - 142, 1, shadow=0)
    fr.put(CAR_L, ox + x, oy + y, 1, shadow=0.6, sh_off=(0, 26))
    for i in range(5):                                                       # speed lines
        yy = oy + y - 120 + i * 60; x0 = ox + x - 560 - 90 * ((t * 7 + i * .37) % 1)
        stroke(fr, [(x0, yy), (x0 - 170 - 30 * i, yy)], 1.0 * (k > 0.05), PAPER_LT, 6)
A_C = fit(ABUST, h=250); J_C = fit(JHEAD, h=230); CAR_L = fit(CAR, 980)


def waveform(fr, t, ox, oy):
    t0 = T('listening')
    if t < t0: return
    pts = [(-500 + i * 10, -330 + (120 * math.sin(i * .55 + t * 14) * math.sin(i * .09 + t * 3) + 40 * math.sin(i * 1.7 - t * 22)) * math.exp(-((i - 50) / 34) ** 2) * min(1, (t - t0) * 4)) for i in range(101)]
    stroke(fr, [(ox + x, oy + y) for x, y in pts], 1.0, ORANGE, 11)


def flashes(times):
    def fn(fr, t, ox, oy):
        for i, (tf, x, y) in enumerate(times):
            k = math.exp(-max(0, t - tf) * 9) * (t >= tf)
            if k > 0.03:
                lay = np.zeros((H // 4, W // 4), np.float32); X, Y = fr.w2s(ox + x, oy + y); cv2.circle(lay, (int(X / 4), int(Y / 4)), int(90 * k + 20), 1.0, -1)
                lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 30), (W, H))[..., None] * k * 1.6
                fr.c = fr.c + lay * (1 - fr.c * 0.3)
    return Fn(fn)


def fall(fr, t, ox, oy):
    """Tower with Jensen on top; rips on 'resigned', he falls out of frame bottom."""
    t0 = T('resigned'); base = 960; low_top = base - T_LOW.shape[0] + 60
    fr.put(T_LOW, ox, oy + base, 1, anchor=(0.5, 1), shadow=0.5)
    k = seg(t, t0, t0 + 1.2)
    fr.put(T_TOP, ox - 300 * k * k, oy + low_top + 1500 * k ** 2.2, 1, rot=-1.1 * k ** 1.3, anchor=(0.5, 1), shadow=0.5)
    feet = low_top - T_TOP.shape[0] + 14; ms = 1.1; mh = MAN.shape[0] * ms
    if t < t0:
        fr.put(MAN, ox, oy + feet, ms, rot=0.05 * math.sin(seg(t, t0 - .3, t0) * 10), anchor=(0.5, 0.965), shadow=0.55)
        fr.put(CROWN, ox + 8, oy + feet - mh + 10, 1.05, rot=-0.12, shadow=0.5)
    else:
        kk = seg(t, t0, t0 + 1.5)
        fr.put(MAN, ox + 260 * eout(kk, 1.6), oy + feet - mh / 2 - 170 * math.sin(math.pi * min(1, kk * 2.2)) * (kk < .455) + 1700 * kk ** 1.9, ms, rot=2.2 * eout(kk, 1.3), shadow=0.55)
        fr.put(CROWN, ox - 200 * kk, oy + feet - mh - 260 * math.sin(math.pi * min(1, kk * 1.6)) + 1500 * kk ** 2, 0.85, rot=-0.12 - 5 * kk, shadow=0.5)
    cr = [(120 + 260 * (i / 50) ** .6 + 50 * math.sin(i * .9) * (1 - i / 50), feet - 250 + 1500 * (i / 50) ** 1.4) for i in range(51)]
    stroke(fr, [(ox + x, oy + y) for x, y in cr], seg(t, t0, t0 + 1.1) ** .8, ORANGE, 15)


# ------------------------------------------------------------------ the shots
A1 = fit(ABUST, h=980); ex1 = eyes(A1, 0, -170)
J2 = fit(JSEAT, h=1020)
A4 = fit(AFULL, h=1080)
A5 = fit(ABUST, h=820); ex5 = eyes(A5, 0, 270)
X6 = fit(XI, h=900); A6 = fit(ABUST, h=430); J6 = fit(JHEAD, h=380); ex6 = eyes(A6, -260, 560)
J7 = fit(JBUST, h=900)
C8 = fit(COUPLE, h=1050)
A9 = fit(AFULL, h=800); J9 = fit(JSEAT, h=760)
A11 = fit(ABUST, h=420)
L16 = fit(LORI, h=760)
A17 = fit(ABUST, h=420)
J19 = fit(JBUST, h=780)
A23 = fit(ABUST, h=940); ex23 = eyes(A23, 0, -150); X23 = fit(XI, h=820)
tA = T('alice'); t = None
SHOTS = [
 # 0 - "This woman charged $470 billion for one relationship"
 dict(t=0.0, els=[BG(RAYS_R, -200), E(FLAG, 40, -560, 1.2, r=-0.03, d=0.5, wv=18, wob=0), E(DOCS[0], -400, -100, .8, r=-.2, d=.3), E(DOCS[1], 420, 60, .8, r=.15, d=.3),
      E(A1, 0, -170, t=0.02, a='pop', dur=.2), S(arc(430, -720, 250, -480, -.3), 0.25, .3, ORANGE, 14), S([(300, -420), (250, -480), (330, -500)], 0.5, .12, ORANGE, 14),
      *[E(BILLS[i % 3], x, y, .8, r=rr, d=-.05, t=T('hundred') + i * .09) for i, (x, y, rr) in enumerate(((-380, 380, .4), (390, 420, -.35), (-330, 590, -.2), (350, 610, .3), (-60, 640, .1)))],
      E(L('$470 BILLION', 940), 0, 480, r=-.05, d=-.1, t=T('four'), a='slam'), E(SCHIP, -440, 250, 1, r=.3, d=-.1, t=T('billion')), E(SCHIP, 450, 240, .9, r=-.2, d=-.1, t=T('billion') + .1),
      E(fit(PAIR, 400), -210, 800, r=-.09, d=-.12, t=T('one'), a='drop'), E(TAPE, -210, 570, .9, r=.1, d=-.12, t=T('one') + .3, a='fade', sh=.2), E(HEART, 230, 790, .9, r=.1, d=-.12, t=T('relationship'))],
      cam=[(0, 0, -120, 1.12), (1.0, 0, -100, 1.08), (1.3, 0, 60, 1.0), (3.5, 0, 80, 1.02), (3.9, 0, 200, 1.0), (5.3, 0, 220, 1.04)]),
 # 1 - "and the richest tech CEO on the planet actually paid it"
 dict(t=T('and'), els=[BG(RAYS, -300), E(GLOBE, 0, -420, 1.35, d=.6, spin=.25, wob=0, t=T('planet') - .9, a='rise'), E(BLDG[0], -420, 700, 1.3, d=.6), E(BLDG[2], 430, 760, 1.3, d=.6),
      E(NVCARD, -300, -640, r=-.08, d=.3, t=T('richest')), E(NVS, 380, -560, r=.2, d=.3, t=T('tech')), E(J2, 0, -30, t=T('the', 1), a='rise'), E(CROWN, -55, -590, 1.0, r=-.14, t=T('richest') + .12),
      *grid(SCHIP, [(-430, 250), (-400, 420), (430, 230), (410, 400)], T('tech'), .1), *[E(BILLS[i % 3], x, y, .75, r=rr, d=-.1, t=T('c') + i * .08) for i, (x, y, rr) in enumerate(((-360, 620, .3), (370, 640, -.3), (-150, 760, -.1), (160, 780, .2)))],
      rain(BILLS, T('actually'), T('paid') + .5, 16, 2), E(ST('PAID', 640), 0, 560, r=-.13, d=-.15, t=T('paid'), a='slam', sh=0)]),
 # 2 - "Give me sixty seconds"
 dict(t=T('give') - .12, els=[BG(RAYS_O, -40, .9), Fn(stopwatch), orbit([(NVS, .9), (SCHIP, 1.1), (fit(FLAG, 190), 1), (BILLS[0], .6), (fit(JHEAD, h=230), 1), (SCHIP, 1.0), (fit(ABUST, h=250), 1), (BILLS[2], .55)], T('sixty')),
      E(L('60 SECONDS', 620), 0, 650, r=-.04, d=-.1, t=T('sixty'), a='slam')], cam=[(9.5, 0, 0, 0.98), (11.2, 0, 0, 1.06), (12.55, 0, -40, 7.0)]),
 # 3 - "Her name is Alice Huang. A Chinese citizen"
 dict(t=T('her') - .1, els=[BG(RAYS_R, -100), E(FLAG, 250, -230, .68, r=.06, d=.4, wv=16, wob=0, t=T('chinese'), a='R'), E(DOCS[2], 300, 420, .9, r=.12, d=.2, t=T('citizen')), E(DOCS[0], 260, 560, .8, r=-.1, d=.2, t=T('citizen') + .12),
      E(A4, -170, 120, t=T('her'), a='L'), E(L('ALICE HUANG', 800), 40, -690, r=-.04, d=-.1, t=tA, a='slam'), S(arc(-250, -600, -230, -420, .3), tA + .3, .3, art.RED * .9, 6), E(PIN, -250, -600, .9, t=tA + .25),
      E(PIN_Y, 250, -400, .9, d=.4, t=T('chinese') + .3), E(SCHIP, 400, 780, 1, r=.3, d=-.1, t=T('citizen') + .2), E(fit(XI, h=300), 330, 130, r=.05, d=.3, t=T('citizen') + .05)]),
 # 4 - "who worked at state TV, HSBC, and one of China's biggest financial firms"
 dict(t=T('who') - .05, els=[BG(RAYS, 0), E(fit(ABUST, h=400), -300, -40, r=-.05, t=T('who')), E(PIN, -300, -230, .9, t=T('who') + .2),
      E(P_CCTV, 190, -560, r=.05, d=.1, t=T('state'), a='drop'), E(CAMERA, -300, -640, .9, r=-.2, t=T('t')), E(L('STATE TV', 430), -180, -400, r=-.06, d=-.1, t=T('t'), a='slam'), S(arc(-300, -230, 100, -520, -.2), T('state') + .2, .3, art.RED * .9, 6),
      E(HSBC, 200, 30, r=.04, d=-.05, t=T('h'), a='slam'), S(arc(-300, -230, 60, 20, .15), T('h') + .15, .3, art.RED * .9, 6), E(BILLS[0], 400, 170, .7, r=.4, t=T('s', 1)), E(BILLS[1], 60, 180, .7, r=-.3, t=T('b')),
      E(BLDG[0], -330, 960, 1.0, d=.3, t=T('china\'s') - .2, a='rise'), E(BLDG[2], -60, 1040, 1.0, d=.3, t=T('china\'s') - .1, a='rise'), E(BLDG[1], 230, 1000, 1.0, d=.3, t=T('china\'s'), a='rise'),
      S([(-480 + i * 24, 760 - i * 9 - 50 * math.sin(i * .6)) for i in range(40)], T('biggest'), .6, art.NVG * .9, 13), S(arc(-300, -230, -150, 480, .25), T('one', 2), .3, art.RED * .9, 6),
      *[E(BILLS[i % 3], x, y, .7, r=rr, d=-.1, t=T('financial') + i * .08) for i, (x, y, rr) in enumerate(((-400, 830, .3), (380, 800, -.3), (0, 880, .1)))], E(L('FINANCE', 430), 200, 640, r=.05, d=-.1, t=T('financial'), a='slam')]),
 # 5 - "But according to U.S. intelligence, she had a second job"
 dict(t=T('but') - .1, els=[BG(RAYS, -200), E(F_US, 0, -620, 1.15, r=.02, d=.4, wv=16, wob=0, t=T('according'), a='drop'), E(FOLDER, -10, -250, .9, r=-.05, d=.2, t=T('u', 1)), E(ST('CLASSIFIED', 420), 0, -230, r=-.14, d=.15, t=T('intelligence'), a='slam', sh=0),
      E(SEAL_CIA, -340, -330, r=-.1, t=T('u', 1)), E(SEAL_NSA, 340, -330, r=.1, t=T('s', 2)), E(DOCS[1], -420, 80, .7, r=-.2, d=.3, t=T('intelligence')), E(DOCS[3], 420, 100, .7, r=.2, d=.3, t=T('intelligence') + .1),
      E(A5, 0, 270, t=T('she', 2), a='rise'), E(fit(BAR, 400), ex5[0], ex5[1], r=-.02, d=-.03, t=T('second'), a='slam', sh=.6), E(L('SECOND JOB', 600), 0, 690, r=-.04, d=-.1, t=T('job'), a='slam')]),
 # 6 - "recruited by China's Ministry of State Security to get close to one man"
 dict(t=T('recruited') - .1, els=[BG(RAYS_R, -300), E(FLAG, 0, -500, 1.3, d=.5, wv=20, wob=0, t=T('recruited'), a='drop'), E(X6, 140, -330, t=T('by'), a='rise'), E(EMBLEM, -330, -560, r=-.08, d=-.05, t=T('ministry'), a='slam'),
      E(L('STATE SECURITY', 760), 0, 160, r=-.03, d=-.1, t=T('state', 2), a='slam'), E(A6, -260, 560, r=-.05, t=T('recruited') + .2), E(fit(BAR, 210), ex6[0], ex6[1], d=-.03, t=T('recruited') + .5, a='slam', sh=.5, quiet=True),
      S(arc(60, 60, -230, 380, .3), T('security'), .35, art.RED * .9, 6), E(PIN, 60, 60, .8, t=T('security')),
      S(arc(-90, 600, 150, 600, -.25), T('get'), .5, ORANGE, 10, dash=True), E(J6, 280, 580, r=.05, t=T('one', 3)), S(circ(280, 580, 190, 215), T('one', 3) + .1, .35, ORANGE, 12),
      S([(280, 330), (280, 830)], T('man'), .15, ORANGE, 8), S([(40, 580), (520, 580)], T('man') + .1, .15, ORANGE, 8)]),
 # 7 - "Jensen Huang. The guy who built NVIDIA into a $4.5 trillion AI empire"
 dict(t=T('jensen') - .12, els=[BG(RAYS_G, -250), E(P_NVHQ, -200, -650, r=-.05, d=.4, t=T('built'), a='drop'), E(P_GPU, 330, -640, r=.08, d=.3, t=T('nvidia')), E(J7, 0, -210, t=T('jensen'), a='slam'),
      E(L('JENSEN HUANG', 820), 0, 290, r=-.04, d=-.1, t=T('huang', 2), a='slam'), E(NVCARD, -330, -260, r=-.1, d=-.05, t=T('nvidia')), E(NVS, 400, -200, r=.2, d=-.05, t=T('nvidia') + .15),
      S([(-500 + i * 26, 760 - i * 6 - 40 * math.sin(i * .5) - max(0, i - 24) * 16) for i in range(40)], T('into'), .7, art.NVG * .9, 14), E(L('$4.5 TRILLION', 900), 0, 560, r=.03, d=-.12, t=T('four', 2), a='slam'),
      *grid(SCHIP, [(-450 + i * 150, 800 + 20 * (i % 2)) for i in range(7)], T('a', 4), .09), E(BILLS[0], -420, 420, .7, r=.3, t=T('trillion')), E(BILLS[1], 430, 430, .7, r=-.3, t=T('trillion') + .1)]),
 # 8 - "Married for thirty years."
 dict(t=T('married') - .15, els=[BG(RAYS, -100), E(C8, 0, -40, t=T('married'), a='drop'), E(TAPE, -200, -540, 1, r=-.5, t=T('married') + .35, a='fade', sh=.2), E(HEART, 340, -600, .9, r=.15, t=T('for', 2)),
      E(art.calendar('YEARS', '30'), -340, -620, 1, r=-.1, d=-.05, t=T('thirty'), a='slam'), E(DOCS[1], -430, 500, .8, r=-.2, d=.3), E(L('MARRIED', 520), 0, 640, r=-.04, d=-.1, t=T('years'), a='slam')]),
 # 9 - "The most powerful person in AI"
 dict(t=T('the', 4) - .12, els=[BG(RAYS_G, -300, .5), E(GLOBE, 0, -350, 1.3, d=.7, spin=.2, wob=0), E(BLDG[0], -430, 900, 1.4, d=.5), E(BLDG[2], 430, 960, 1.4, d=.5), E(TOWER, 0, 620, 1, t=T('the', 4), a='rise', wob=0),
      E(MAN, 0, -215, 1.22, t=T('most'), a='drop', wob=.01), E(CROWN, 8, -770, 1.2, r=-.12, t=T('powerful')), E(NVS, -360, -420, r=-.2, t=T('person')), E(NVS, 370, -300, .8, r=.2, t=T('person') + .1),
      E(L('MOST POWERFUL', 700), 0, 690, r=-.03, d=-.1, t=T('powerful'), a='slam'), *grid(SCHIP, [(-420, -100), (420, -40), (-400, 120), (400, 160)], T('in', 1), .08)]),
 # 10 - "She met him at an NVIDIA event in early 2024"
 dict(t=T('she', 3) - .12, els=[BG(RAYS, -200), E(P_STAGE, 0, -560, r=-.02, d=.3, t=T('nvidia', 2), a='drop'), E(NVCARD, -330, -250, .8, r=-.1, t=T('nvidia', 2) + .1), E(A9, -230, 420, t=T('she', 3), a='L'), E(J9, 240, 420, t=T('him'), a='R'),
      S(arc(-200, 60, 200, 60, -.25), T('met') + .3, .3, art.RED * .9, 6), E(PIN, -200, 60, .8, t=T('met') + .3), E(PIN, 200, 60, .8, t=T('met') + .5),
      E(art.calendar('EARLY', '2024', seed=3), 330, -230, 1, r=.08, d=-.1, t=T('twenty'), a='slam')]),
 # 11 - "Within months, she was pulling him into bars in Taipei for drinks with executives"
 dict(t=T('within') - .12, els=[BG(RAYS_O, -200), E(P_TAIPEI, 0, -560, r=.02, d=.4, t=T('within'), a='drop'), E(F_TW, -330, -230, .6, r=-.08, d=.2, wv=12, wob=0, t=T('taipei'), a='L'),
      E(L('TAIPEI', 460), 200, -180, r=.04, d=-.1, t=T('taipei'), a='slam'), E(fit(PAIR, 600), 0, 330, r=-.04, d=-.05, t=T('pulling'), a='slam'), E(TAPE, 0, -20, 1.1, r=.05, d=-.05, t=T('pulling') + .1, a='fade', sh=.2),
      E(GLASS, -410, 420, 1, r=.35, d=-.15, t=T('drinks')), E(GLASS, 410, 420, 1, r=-.35, d=-.15, t=T('drinks') + .12),
      *[E(EXEC, -330 + i * 330, 860, .6, d=-.2, t=T('executives') + i * .1, a='rise', wob=.01) for i in range(3)]]),
 # 12 - "Her company started buying $4.8 billion in NVIDIA chips"
 dict(t=T('her', 2) - .12, els=[BG(RAYS_O, 0), E(MEGA, 110, -690, r=-.03, t=T('company'), a='slam'), E(A11, -360, -480, r=-.06, t=T('her', 2)), E(DOCS[0], 400, -450, .7, r=.15, d=.3),
      E(L('$4.8 BILLION', 940), 0, -170, r=-.05, d=-.1, t=T('four', 4), a='slam'), *[E(BILLS[i % 3], x, y, .75, r=rr, d=-.05, t=T('billion', 2) + i * .08) for i, (x, y, rr) in enumerate(((-400, -10, .4), (400, 0, -.4), (-380, 90, -.2), (380, 110, .2)))],
      E(NVS, -400, 330, r=-.2, t=T('nvidia', 3)), E(fit(CHIP, 430), 0, 380, r=.08, d=-.12, t=T('chips'), a='slam'), S(circ(0, 380, 300, 290), T('chips') + .15, .35, INK * .8, 12, -.12),
      *grid(SCHIP, [(-450 + i * 150, 780 + 20 * (i % 2)) for i in range(7)] + [(380, 300), (420, 470), (-420, 560)], T('point', 2), .14)]),
 # 13 - "allegedly shipping them straight to banned Chinese companies through a fake data center in Malaysia"
 dict(t=T('and', 4) - .12, els=[BG(RAYS, 0), E(FLAG, 0, -700, .75, d=.4, wv=16, wob=0), E(BLDG[0], -300, -230, .75, d=.2), E(BLDG[2], 0, -200, .75, d=.2), E(BLDG[1], 290, -230, .75, d=.2),
      E(F_MY, -250, 700, .7, r=-.04, d=.3, wv=13, wob=0), E(P_PET, -330, 440, r=-.05, d=.2, t=T('malaysia') - .3, a='rise'), E(P_DC, 200, 560, r=.04, d=.1, t=T('data'), a='drop'),
      S(arc(150, 420, 40, -180, .35, 40), T('shipping'), .9, ORANGE, 12, dash=True), crates(arc(150, 420, 40, -180, .35, 40), T('shipping') + .2, 99),
      E(ST('ALLEGEDLY', 440, INK), -280, 120, r=-.1, d=-.1, t=T('allegedly') + .3, a='slam', sh=0), E(ST('BANNED', 620), 0, -420, r=-.1, d=-.1, t=T('banned'), a='slam', sh=0),
      E(ST('FAKE?', 380), 220, 560, r=-.15, d=-.1, t=T('fake') + .25, a='slam', sh=0), E(L('MALAYSIA', 460), -200, 690, r=.03, d=-.1, t=T('malaysia'), a='slam')],
      cam=[(54.3, 0, 120, 1.0), (55.3, 0, 100, 1.02), (56.3, 0, -230, 1.06), (57.9, 0, -240, 1.08), (58.5, 0, 330, 1.04), (60.4, 0, 350, 1.08)]),
 # 14 - "She kept getting closer"
 dict(t=T('she', 5) - .12, els=[BG(RAYS_R, -100, .5), E(FLAG, -330, -640, .5, r=-.1, d=.4, wv=14, wob=0), E(NVCARD, 330, -650, .8, r=.1, d=.4), Fn(closer), E(HEART, 0, -420, 1.0, t=T('closer'), a='pop'),
      S(arc(-330, 560, -60, 560, .0), T('kept'), .4, ORANGE, 14), S(arc(330, 560, 60, 560, .0), T('kept'), .4, ORANGE, 14), E(L('CLOSER', 460), 0, 690, r=-.04, d=-.1, t=T('closer'), a='slam')]),
 # 15 - "Cameras caught her kissing him on the cheek at a public dinner"
 dict(t=T('cameras') - .12, els=[BG(RAYS, -100), E(CAMERA, -390, -720, 1, r=-.2, t=T('cameras')), E(CAMERA, 390, -660, .9, r=.25, t=T('cameras') + .1), E(CAMERA, -380, 700, .9, r=.15, t=T('cameras') + .2),
      E(fit(EMBR, 700), 0, -30, r=-.03, d=-.05, t=T('caught'), a='slam'), E(TAPE, -250, -600, 1.1, r=-.5, d=-.05, t=T('caught') + .1, a='fade', sh=.2), E(TAPE, 250, -600, 1.1, r=.5, d=-.05, t=T('caught') + .1, a='fade', sh=.2),
      S([(-400, -480), (-400, -620), (-260, -620)], T('her', 3), .15, art.RED, 10), S([(400, -480), (400, -620), (260, -620)], T('her', 3), .15, art.RED, 10),
      S([(-400, 420), (-400, 560), (-260, 560)], T('kissing'), .15, art.RED, 10), S([(400, 420), (400, 560), (260, 560)], T('kissing'), .15, art.RED, 10), E(fit(art.pin(90), 60), 330, -700, t=T('kissing')),
      flashes([(T('cameras') + .15, -390, -720), (T('caught'), 390, -660), (T('kissing'), -380, 700), (T('cheek'), 390, -660), (T('public'), -390, -720)]), E(L('CAUGHT ON CAMERA', 800), 0, 690, r=-.03, d=-.1, t=T('cheek'), a='slam')]),
 # 16 - "They left in the same car"
 dict(t=T('they') - .15, els=[BG(RAYS_O, -300), E(P_TAIPEI, 0, -520, .9, r=-.03, d=.5), E(BLDG[0], -420, 200, 1.1, d=.4), E(BLDG[1], 400, 240, 1.1, d=.4), E(RIDGE_A, 0, 760, 1.2, d=-.1, wob=0), Fn(drive),
      E(L('SAME CAR', 520), 0, 690, r=-.04, d=-.15, t=T('same'), a='slam')]),
 # 17 - "His wife was in the same city"
 dict(t=T('his') - .12, els=[BG(RAYS, -200), E(P_TAIPEI, 200, -560, .8, r=.04, d=.4), E(F_TW, -360, -700, .45, r=-.1, d=.3, wv=10, wob=0), E(L16, -210, -100, t=T('wife'), a='L'), E(fit(EMBR, 380), 290, 330, r=.1, d=-.05, t=T('was', 2), a='R'),
      S(arc(-60, 100, 190, 180, -.3), T('in', 7), .4, ORANGE, 10, dash=True), E(PIN, -200, 420, 1, t=T('same', 2)), E(PIN, 290, 80, 1, d=-.05, t=T('same', 2) + .1), E(L('SAME CITY', 560), 0, 690, r=-.04, d=-.1, t=T('city'), a='slam')]),
 # 18 - "U.S. agencies had been listening to her calls for over a year"
 dict(t=T('u', 2) - .12, els=[BG(RAYS, -200), E(F_US, 0, -700, 1.0, d=.4, wv=14, wob=0, t=T('u', 2), a='drop'), E(SEAL_NSA, -330, -480, r=-.1, t=T('s', 3)), E(SEAL_FBI, 0, -520, t=T('agencies')), E(SEAL_CIA, 330, -480, r=.1, t=T('agencies') + .12),
      E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 700, 330, (.16, .14, .12), 3), 0, -60, r=-.01, t=T('listening') - .1, a='rise', wob=0), E(REEL, -180, -70, 1, spin=4, wob=0, t=T('listening')), E(REEL, 180, -70, 1, spin=4, wob=0, t=T('listening') + .08),
      Fn(waveform), E(PHONE, -40, 560, 1, r=-.08, t=T('calls')), E(A17, -330, 560, r=-.05, t=T('her', 4)), S(arc(-120, 500, -30, 200, .2), T('calls') + .15, .3, art.RED * .9, 6),
      E(art.calendar('OVER', '1 YEAR', seed=5), 300, 560, 1, r=.08, d=-.1, t=T('year'), a='slam')]),
 # 19 - "Then the New York Times dropped everything"
 dict(t=T('then') - .12, els=[BG(RAYS, 0), E(P_NYTB, -360, -640, r=-.06, d=.4), rain(DOCS, T('dropped') - .2, T('everything') + .6, 14, 5, .5), E(NYT, 0, -700, r=-.02, d=-.25, t=T('new'), a='slam'),
      E(NEWS, 0, 150, 1.0, r=.03, d=-.08, t=T('dropped'), a='slam'), E(fit(BAR, 280), -40, -70, d=-.1, t=T('everything'), a='slam', sh=.5, alpha=0.0), E(ST('EXCLUSIVE', 460), 150, 620, r=-.14, d=-.12, t=T('everything'), a='slam', sh=0)]),
 # 20 - "Jensen admitted the affair to his entire company"
 dict(t=T('jensen', 2) - .12, els=[BG(RAYS_G, -300), E(NVCARD, -340, -660, .8, r=-.1, d=.3), E(J19, 0, -380, t=T('jensen', 2), a='drop'), E(L('ADMITTED', 600), 0, 90, r=-.04, d=-.1, t=T('admitted'), a='slam'),
      E(HEART, 360, -600, .7, r=.2, t=T('affair')), S([(300, -700), (420, -500)], T('affair') + .2, .15, INK, 14), S([(420, -700), (300, -500)], T('affair') + .3, .15, INK, 14),
      *[E(DOCS[i % 4], -400 + (i % 5) * 200, 330 + (i // 5) * 60, .32, r=.2 * (-1) ** i, d=-.05, t=T('to', 6) + i * .05, a='drop') for i in range(10)],
      *[E(EXEC, -430 + (i % 6) * 172, 560 + (i // 6) * 250, .42, d=-.1 - .05 * (i // 6), t=T('entire') + i * .05, a='rise', wob=.01) for i in range(12)]]),
 # 21 - "NVIDIA's stock crashed - $470 billion gone in two days"
 dict(t=T("nvidia's") - .12, els=[BG(RAYS, -200), E(NVCARD, -300, -660, r=-.08, d=.2), E(fit(JHEAD, h=330), 330, -620, r=.08, d=.2),
      S([(-500 + i * 14, -80 - i * 9 - 40 * math.sin(i * .5)) for i in range(30)], T("nvidia's"), .4, art.NVG * .9, 14),
      S([(-80 + i * 11 + 30 * math.sin(i * .8), -350 + 22 * i + 6 * (i % 3)) for i in range(48)], T('crashed') - .15, .55, ORANGE, 18), S([(390, 620), (448, 706), (480, 600)], T('crashed') + .4, .1, ORANGE, 18),
      rain(BILLS, T('four', 5), T('days'), 22, 9), E(L('-$470 BILLION', 940), 0, 170, r=-.05, d=-.12, t=T('four', 5), a='slam'), E(ST('GONE', 460), 0, 400, r=-.12, d=-.14, t=T('gone'), a='slam', sh=0),
      E(art.calendar('DAY', '1', seed=7), -200, 700, .9, r=-.08, d=-.1, t=T('two'), a='slam'), E(art.calendar('DAY', '2', seed=8), 200, 700, .9, r=.08, d=-.1, t=T('days'), a='slam')]),
 # 22 - "Congress threatened a subpoena. The FBI opened a case."
 dict(t=T('congress') - .12, els=[BG(RAYS, -300), E(F_US, 0, -720, 1.0, d=.5, wv=14, wob=0), E(P_CAP, 0, -480, r=-.02, d=.2, t=T('congress'), a='rise'), E(DOCS[3], -230, 160, 1.0, r=-.08, d=-.05, t=T('subpoena'), a='slam'),
      E(L('SUBPOENA', 520), -150, 330, r=-.06, d=-.1, t=T('subpoena') + .25, a='slam'), E(fit(SEAL_FBI, 330), 290, 180, r=.08, d=-.05, t=T('f'), a='slam'), E(FOLDER, 150, 660, 1, r=.05, d=-.1, t=T('opened')),
      E(ST('CASE OPENED', 480), 150, 680, r=-.1, d=-.12, t=T('case'), a='slam', sh=0), E(fit(JHEAD, h=250), -330, 700, r=-.08, d=-.1, t=T('opened') + .1), E(PIN, -330, 560, .8, d=-.1, t=T('case'))]),
 # 23 - "And on November 12th, Jensen Huang resigned from the company he built from nothing"
 dict(t=T('and', 5) - .12, els=[BG(RAYS_G, -300, .4), E(P_NVHQ, 150, -640, r=.04, d=.5), E(BLDG[0], -450, 800, 1.3, d=.5), E(BLDG[2], 450, 860, 1.3, d=.5), E(art.calendar('NOV', '12', seed=9), -330, -620, 1.15, r=-.08, d=-.05, t=T('november'), a='slam'),
      E(NVCARD, 340, -250, .8, r=.1, d=.2, out=T('resigned') + .2), Fn(fall), rain(BILLS + [SCHIP], T('resigned'), T('nothing'), 14, 11),
      E(ST('RESIGNED', 880), 0, 60, r=-.1, d=-.2, t=T('resigned') + .25, a='slam', sh=0)], cam=[(90.8, 0, -60, 1.0), (93.0, 0, -80, 1.08), (93.6, 0, 60, 1.0), (95.9, 0, 120, 1.05)]),
 # 24 - "One woman. One mission. And the entire AI industry will never be the same."
 dict(t=T('one', 4) - .15, els=[BG(RAYS_R, -150, .4), E(FLAG, 0, -560, 1.25, d=.5, wv=20, wob=0, t=T('one', 5), a='drop'), E(X23, 230, -420, d=.2, t=T('mission'), a='rise'),
      *[x for i, (sp, x_, y_) in enumerate(((fit(JHEAD, h=330), -760, -900), (NVCARD, 760, -900), (SEAL_FBI, -820, -100), (fit(NYT, 420), 800, -60), (fit(CHIP, 300), -780, 700), (fit(P_CAP, 420), 780, 720), (fit(EMBR, 300), 0, 1250), (SEAL_CIA, -400, 1200), (BILLS[0], 420, 1220), (art.calendar('NOV', '12', seed=9), 0, -1300, ))) for x in
        (S(arc(0, -150, x_ * .8, y_ * .85, .12), T('and', 6) + i * .14, .3, art.RED * .9, 7), E(sp, x_, y_, 1, r=.1 * (-1) ** i, t=T('and', 6) + .15 + i * .14), E(PIN, x_ * .8, y_ * .85, .9, t=T('and', 6) + .3 + i * .14, quiet=True))],
      E(A23, 0, -150, t=T('one', 4), a='pop'), E(fit(BAR, 460), ex23[0], ex23[1], r=-.02, d=-.03, t=T('mission'), a='slam', sh=.6), E(L('ONE MISSION', 640), 0, 520, r=-.04, d=-.1, t=T('mission') + .35, a='slam')],
      cam=[(96.0, 0, -100, 1.08), (98.2, 0, -60, 1.02), (99.4, 0, 0, 0.56), (101.8, 0, 0, 0.6)]),
 # 25 - "Follow for more"
 dict(t=T('follow') - .12, els=[BG(RAYS_O, 0, 1.2), E(L('FOLLOW', 860), 0, -120, r=-.05, t=T('follow'), a='slam'), E(L('FOR MORE', 620), 0, 150, r=.03, t=T('more'), a='slam'), E(SCHIP, -380, 420, 1.3, r=.3, t=T('more')), E(NVS, 380, 420, r=-.2, t=T('more') + .08),
      E(fit(ABUST, h=330), -300, -560, r=-.08, t=T('follow')), E(fit(JHEAD, h=300), 300, -560, r=.08, t=T('follow') + .08)]),
]
STEP = [(2700, 0), (0, 2900), (2700, 0), (0, -2900)]
_x = _y = 0
for i, sh in enumerate(SHOTS):
    sh['o'] = (_x, _y); dx, dy = STEP[i % 4]; _x += dx; _y += dy
    sh['t1'] = SHOTS[i + 1]['t'] if i + 1 < len(SHOTS) else DUR
    if 'cam' not in sh: sh['cam'] = [(sh['t'], 0, 0, 1.0), (sh['t1'], 0, -24, 1.07)]
IMPACTS = [(e.hit, sh['o'][0] + e.x, sh['o'][1] + e.y) for sh in SHOTS for e in sh['els'] if e.kind == 'el' and e.a == 'slam' and e.alpha > 0 and not e.quiet]
BURSTS = [Burst(t_, x_, y_, 20, 800, i, 0.5, cols=(PAPER, PAPER_LT, ORANGE), size=13, puff=0.7, spread=1.4) for i, (t_, x_, y_) in enumerate(IMPACTS)]
WHIP = 0.17


def pose(i, t):
    sh = SHOTS[i]; ks = sh['cam']; ox, oy = sh['o']
    if t <= ks[0][0]: _, x, y, z = ks[0]
    elif t >= ks[-1][0]: _, x, y, z = ks[-1]
    else:
        for a, b in zip(ks, ks[1:]):
            if t <= b[0]:
                k = seg(t, a[0], b[0]); k = k if len(ks) == 2 else eio(k, 2)
                x, y = lerp(a[1], b[1], k), lerp(a[2], b[2], k); z = a[3] * (b[3] / a[3]) ** k; break
    return ox + x, oy + y, z


def shot_at(t):
    for i in range(len(SHOTS) - 1, -1, -1):
        if t >= SHOTS[i]['t']: return i
    return 0


def cam_at(t):
    i = shot_at(t); sh = SHOTS[i]
    for j, b in ((i, sh['t']), (i + 1, sh['t1'])):
        if 0 < j < len(SHOTS) and abs(t - b) < WHIP:
            A, Bp = pose(j - 1, b - WHIP), pose(j, b + WHIP); k = eio(seg(t, b - WHIP, b + WHIP), 3)
            return Cam(lerp(A[0], Bp[0], k), lerp(A[1], Bp[1], k), A[2] * (Bp[2] / A[2]) ** k * (1 - 0.10 * math.sin(math.pi * k)))
    return Cam(*pose(i, t))


def floaters(fr, t, n=20):
    lay = np.zeros((H // 2, W // 2, 4), np.float32); c = fr.cam
    for i in range(n):
        r = np.random.default_rng(1000 + i); bx, by = r.uniform(0, 3000), r.uniform(0, 4200); sz = r.uniform(10, 34) * min(c.z, 2.2); col = (PAPER, PAPER_LT, ORANGE, art.RED, PAPER)[i % 5]
        x = ((bx - c.x * 1.7 * c.z + 40 * math.sin(t * .7 + i)) % (W + 500) - 250) / 2; y = ((by - c.y * 1.7 * c.z + t * (25 + 12 * (i % 4))) % (H + 500) - 250) / 2
        a = r.uniform(0, 6.28) + t * r.uniform(-1.5, 1.5); cs, sn = math.cos(a), math.sin(a)
        pts = np.int32([(x + (px * cs - py * sn) * sz / 2, y + (px * sn + py * cs) * sz / 2) for px, py in ((-1, -.6), (1, -.7), (.8, .7), (-1, .5))])
        cv2.fillConvexPoly(lay, pts, (float(col[0]), float(col[1]), float(col[2]), 1.0), cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 5), (W, H)); a = lay[..., 3:4] * 0.5
    fr.c = fr.c * (1 - a) + lay[..., :3] * 0.5 * 0.8


def frame_at(t, cam):
    sx = sy = 0.0
    for t0, _, _ in IMPACTS:
        if 0 <= t - t0 < 0.45: a, b = shake(t, t0, 15); sx += a; sy += b
    cam = Cam(cam.x + sx, cam.y + sy, cam.z)
    fr = Frame(cam, dof=4.2)
    fr.put(FAR, 0, 0, 2.6, depth=3.0, wrap=True, blur=0, shadow=0)
    fr.put(CANYON, 0, 0, 1.2, depth=1.2, wrap=True, shadow=0)
    i = shot_at(t); sh = SHOTS[i]; idx = [i]
    if i > 0 and t - sh['t'] < WHIP + .05: idx.insert(0, i - 1)
    if i + 1 < len(SHOTS) and sh['t1'] - t < WHIP + .05: idx.append(i + 1)
    for j in idx:
        ox, oy = SHOTS[j]['o']
        for e in SHOTS[j]['els']: draw_el(fr, e, t, ox, oy)
    for b in BURSTS:
        if 0 <= t - b.t0 < 1.6: b.draw(fr, t)
    floaters(fr, t)
    return fr.c


def render(f):
    t = f / FPS; cam, prev = cam_at(t), cam_at(t - 1 / FPS)
    img = frame_at(t, cam)
    img = zoom_blur(img, (cam.z / prev.z - 1) * 1.5, 10)
    img = dir_blur(img, (cam.x - prev.x) * cam.z * 0.75, (cam.y - prev.y) * cam.z * 0.75)
    expo = 1.12 * smooth(seg(t, 0, 0.25)) * (1 - 0.95 * ein(seg(t, DUR - 0.3, DUR), 2))
    for t0, _, _ in IMPACTS:
        if 0 <= t - t0 < 0.2: expo *= 1 + 0.25 * math.exp(-(t - t0) * 30)
    return (post(img, f, tilt=1.0, expo=expo) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ sound (all synthesized from the same event list)
SR = 48000; _a = np.random.default_rng(21)
def _filt(x, lo=None, hi=None):
    X = np.fft.rfft(x); fq = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(fq)
    if lo: g *= 1 / (1 + (lo / np.maximum(fq, 1)) ** 4)
    if hi: g *= 1 / (1 + (fq / hi) ** 4)
    return np.fft.irfft(X * g, len(x))
def _env(n, a, d): tt = np.arange(n) / SR; return np.minimum(tt / a, 1) * np.exp(-np.maximum(tt - a, 0) / d)
def thump(f0=70, f1=34, dur=0.7, d=0.16):
    n = int(dur * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-tt / 0.05)) / SR) * _env(n, 0.002, d)
def nburst(dur=0.4, lo=300, hi=5000, d=0.07): n = int(dur * SR); return _filt(_a.normal(0, 1, n), lo, hi) * _env(n, 0.001, d)
def whoosh(dur=0.45, lo=250, hi=2600, peak=0.6):
    n = int(dur * SR); tt = np.linspace(0, 1, n); e = np.exp(-((tt - peak) / 0.22) ** 2); x = _a.normal(0, 1, n)
    return (_filt(x, lo, hi * 0.5) * (1 - tt) + _filt(x, lo * 2, hi) * tt) * e
def scribble(dur=0.38):
    n = int(dur * SR); tt = np.linspace(0, 1, n); return _filt(_a.normal(0, 1, n), 1800, 7000) * (0.6 + 0.4 * np.sin(2 * np.pi * 21 * tt * dur)) * np.sin(np.pi * tt) ** 0.5
def tick(): n = int(0.05 * SR); tt = np.arange(n) / SR; return (np.sin(2 * np.pi * 2300 * tt) + 0.6 * np.sin(2 * np.pi * 4100 * tt)) * np.exp(-tt / 0.006)
def riser(dur, f0=40, f1=120):
    n = int(dur * SR); tt = np.linspace(0, 1, n); return (np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * tt ** 2) / SR) * 0.6 + _filt(_a.normal(0, 1, n), 200, 3000) * 0.5 * tt) * tt ** 2.2


def soundtrack(path):
    n = int(DUR * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]
        Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 43.6 * tt) + 0.5 * np.sin(2 * np.pi * 65.4 * tt + 1) + 0.25 * np.sin(2 * np.pi * 87.3 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, 0.05)
    for hb in np.arange(0.35, DUR, 60 / 46): add(thump(58, 36, 0.4, 0.09), hb, 0.08); add(thump(52, 34, 0.4, 0.08), hb + 0.19, 0.05)
    for sh in SHOTS:
        if sh['t'] > 0.2: add(whoosh(0.5, 250, 2400, 0.5), sh['t'] - 0.25, 0.16, _a.uniform(-.5, .5))
        for e in sh['els']:
            pan = float(np.clip(getattr(e, 'x', 0) / 700, -.6, .6))
            if e.kind == 'stroke': add(scribble(max(0.15, e.dur)), e.t, 0.045, pan)
            elif e.kind == 'el' and e.t is not None and not e.quiet:
                if e.a == 'slam': add(thump(82, 32, 0.6, 0.14), e.hit, 0.30); add(nburst(0.25, 300, 3000, 0.04), e.hit, 0.10, pan)
                elif e.a == 'pop': add(thump(170, 95, 0.12, 0.03), e.t, 0.06, pan); add(nburst(0.07, 1500, 6000, 0.012), e.t + .05, 0.03, pan)
                else: add(whoosh(0.32, 500, 3500, 0.7), e.t - 0.05, 0.06, pan); add(thump(120, 60, 0.2, 0.05), e.hit + .15, 0.07, pan)
    for i in range(28): add(tick(), T('give') + .1 + i * 2.2 / 28, 0.06)
    for tr, d_ in ((T('dropped') - 1.0, 1.0), (T('resigned') - 1.1, 1.1), (T('four') - .9, .9), (T('four', 5) - 1.0, 1.0), (11.3, 1.3)): add(riser(d_), tr, 0.13)
    for i in range(5): add(nburst(0.1, 2500, 9000, 0.02), (T('cameras') + .15, T('caught'), T('kissing'), T('cheek'), T('public'))[i], 0.10)
    add(_filt(_a.normal(0, 1, int(1.6 * SR)), 80, 500) * _env(int(1.6 * SR), 0.2, 0.6), T('they'), 0.10)                      # car rumble
    hiss = _filt(_a.normal(0, 1, int(2.2 * SR)), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * np.arange(int(2.2 * SR)) / SR)); add(hiss * _env(len(hiss), 0.2, 1.2), T('listening'), 0.025)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(0.2 * SR):] *= np.linspace(1, 0, int(0.2 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * 0.9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):06.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
    elif mode == 'render':                                                   # video-only segments of 10 s each, resumable
        out = sys.argv[2]; os.makedirs(out, exist_ok=True); total = round(DUR * FPS)
        with Pool(4) as p:
            lo, hi = (int(v) for v in sys.argv[3].split('-')) if len(sys.argv) > 3 else (0, 99)
            for s0 in range(0, total, 300):
                fn = f'{out}/seg{s0 // 300:02d}.mp4'
                if os.path.exists(fn) or not lo <= s0 // 300 <= hi: continue
                ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4'], stdin=subprocess.PIPE)
                for im in p.imap(render, range(s0, min(total, s0 + 300)), chunksize=4): ff.stdin.write(im.tobytes())
                ff.stdin.close(); ff.wait(); os.rename(fn + '.tmp.mp4', fn); print('seg', s0 // 300, flush=True)
        print('RENDERED')
    elif mode == 'mux':
        out = sys.argv[2]; sfx = out + '/sfx.wav'; soundtrack(sfx)
        open(out + '/list.txt', 'w').write(''.join(f"file '{os.path.abspath(f)}'\n" for f in sorted(glob.glob(out + '/seg*.mp4'))))
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', out + '/list.txt', '-i', VOICE, '-i', sfx,
                               '-filter_complex', '[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,pan=stereo|c0=c0|c1=c0[v];[v][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', sys.argv[3]])
        print('MUXED', sys.argv[3])
