"""voxkit.film - Documentary Template 1 shot engine (elements, whip-pan camera, sound, CLI).
A project script builds `SHOTS` with the helpers here, then calls `run(SHOTS, DUR, VOICE, ...)`."""
import sys, os, math, glob, subprocess, wave as wavmod
import numpy as np, cv2
from multiprocessing import Pool
from .core import *
from . import art


def fit(spr, w=None, h=None):
    k = (w / spr.shape[1]) if w else (h / spr.shape[0])
    return cv2.resize(spr, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def L(txt, w, col=ORANGE): return fit(art.label(txt, 150, col=col, seed=len(txt)), w)
def ST(txt, w, col=None): return fit(art.stamp(txt, 120, art.RED if col is None else col, seed=len(txt)), w)


def timeline(words):
    """words: [[word, start, end], ...] -> T(word, n) lookup of the n-th occurrence's start time."""
    def T(w, n=1):
        k = 0
        for x, a, b in words:
            if x.split('(')[0] == w:
                k += 1
                if k == n: return a
        raise KeyError(f'{w} #{n}')
    return T


# ------------------------------------------------------------------ elements
class El:
    def __init__(self, **k): self.__dict__.update(k)


_n = [0]
def E(spr, x, y, s=1.0, r=0.0, d=0.0, t=None, a='pop', dur=None, wob=0.02, sh=0.5, wv=0, spin=0.0, out=None, blur=None, alpha=1.0, quiet=False, glow=None, tint=None, pulse=0.0):
    _n[0] += 1
    dur = dur or {'pop': .22, 'slam': .12, 'drop': .38, 'rise': .38, 'L': .34, 'R': .34, 'fade': .3, 'none': .1}[a]
    t0 = None if t is None else (t - dur if a == 'slam' else t - 0.12 if a in ('drop', 'rise', 'L', 'R') else t)
    return El(kind='el', spr=spr, x=x, y=y, s=s, r=r, d=d, t=t0, hit=t, a=a if t is not None else 'none', dur=dur, wob=wob, sh=sh, wv=wv, spin=spin, out=out, blur=blur, alpha=alpha,
              ph=_n[0] * 1.7, quiet=quiet, glow=None if glow is None else np.asarray(glow, np.float32), tint=tint, pulse=pulse)
def S(pts, t, dur=0.35, col=ORANGE, w=12, d=0.0, dash=False): return El(kind='stroke', pts=pts, t=t, dur=dur, col=np.asarray(col, np.float32), w=w, d=d, dash=dash)
def Fn(fn): return El(kind='fn', fn=fn)
def BG(rays, y=-200, spin=0.3): return E(rays, 0, y, 1.5, d=0.9, sh=0, spin=spin, wob=0, blur=2)
def grid(spr, pts, t0, step=0.07, s=1.0, d=-0.1, a='pop'): return [E(spr, x, y, s, r=0.15 * (-1) ** i, d=d, t=t0 + i * step, a=a) for i, (x, y) in enumerate(pts)]
def arc(x0, y0, x1, y1, bend=0.2, n=24): return [(lerp(x0, x1, i / n) - (y1 - y0) * bend * math.sin(math.pi * i / n), lerp(y0, y1, i / n) + (x1 - x0) * bend * math.sin(math.pi * i / n)) for i in range(n + 1)]
def circ(cx, cy, rx, ry, n=70): return [(cx + rx * math.cos(a) * (1 + .03 * math.sin(3 * a)), cy + ry * math.sin(a) + 4 * a) for a in np.linspace(-2.0, -2.0 + 6.9, n)]


def rain(sprs, t0, t1, n, seed, s=0.6, spread=560, speed=1.0):
    """Things falling and fluttering through the frame (cash, pages, bricks)."""
    def fn(fr, t, ox, oy):
        for i in range(n):
            r = np.random.default_rng(seed * 100 + i); ts = lerp(t0, t1, r.random()); dt = (t - ts) * speed
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


_GLOW = {}
def _glow_spr(spr, col):
    key = (id(spr), tuple(col))
    if key not in _GLOW:
        a = spr[..., 3]; P = 60
        a = cv2.copyMakeBorder(a, P, P, P, P, cv2.BORDER_CONSTANT, value=0)
        a = cv2.GaussianBlur(cv2.dilate(a, np.ones((15, 15), np.uint8)), (0, 0), 22)
        _GLOW[key] = rgba(np.broadcast_to(col, a.shape + (3,)).copy(), np.clip(a * 1.6, 0, 1))
    return _GLOW[key]


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
    if e.pulse: s *= 1 + e.pulse * math.sin(t * 6.0)
    r += e.wob * math.sin(t * 1.4 + e.ph) + e.spin * t
    if e.wob: y += 5 * math.sin(t * 1.1 + e.ph)
    spr = wave(e.spr, t + e.ph, e.wv) if e.wv else e.spr
    if e.glow is not None:
        fr.put(_glow_spr(e.spr, e.glow), ox + x, oy + y, s, r, e.d, al * (0.75 + 0.25 * math.sin(t * 4)), shadow=0, blur=0)
    fr.put(spr, ox + x, oy + y, s, r, e.d, al, shadow=e.sh, blur=e.blur, tint=e.tint)


def flashes(times, cols=None):
    """Light flashes (camera flash, police lights) at (t, x, y)."""
    def fn(fr, t, ox, oy):
        for i, (tf, x, y) in enumerate(times):
            k = math.exp(-max(0, t - tf) * 9) * (t >= tf)
            if k > 0.03:
                lay = np.zeros((H // 4, W // 4), np.float32); X, Y = fr.w2s(ox + x, oy + y); cv2.circle(lay, (int(X / 4), int(Y / 4)), int(90 * k + 20), 1.0, -1)
                lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 30), (W, H))[..., None] * k * 1.6
                col = np.ones(3, np.float32) if cols is None else np.asarray(cols[i % len(cols)], np.float32)
                fr.c = fr.c + lay * col * (1 - fr.c * 0.3)
    return Fn(fn)


def orbit(items, t0, cy=-40, R=600):
    def fn(fr, t, ox, oy):
        for i, (sp, sc) in enumerate(items):
            k = back(seg(t, t0 + i * 0.08, t0 + i * 0.08 + .22), 2.4)
            if k <= 0: continue
            a = i / len(items) * 2 * math.pi + t * 0.5; rr = (R + 60 * (i % 2))
            fr.put(sp, ox + math.cos(a) * rr * 0.82, oy + cy + math.sin(a) * rr * 1.25, sc * k, rot=math.sin(t * 2 + i) * .25, depth=(-0.25, 0.25)[i % 2], shadow=0.5)
    return Fn(fn)


_DIAL, _HAND = art.dial(), art.hand()
_SWCROWN = art.shape([[(.3, .1), (.7, .1), (.7, 1), (.3, 1)], [(.15, 0), (.85, 0), (.85, .35), (.15, .35)]], 150, 150, (.14, .12, .10), 5)
def stopwatch(t0, ticks=28, span=2.2):
    def fn(fr, t, ox, oy):
        k = back(seg(t, t0 - .1, t0 + .2), 2.2)
        fr.put(_SWCROWN, ox, oy - 40 - 470 * k, k, anchor=(0.5, 1), shadow=0.5)
        fr.put(_DIAL, ox, oy - 40, 1.06 * k, rot=lerp(-0.5, 0, k), shadow=0.6, sh_off=(18, 30))
        tk = np.floor(seg(t, t0 + .1, t0 + span) * ticks) / ticks
        fr.put(_HAND, ox, oy - 40, k, rot=tk * 2 * math.pi * 0.9, anchor=(0.5, 0.86), depth=-0.03, shadow=0.6, sh_off=(8, 14))
        cv2.circle(fr.c, tuple(int(v) for v in fr.w2s(ox, oy - 40)), max(2, int(26 * fr.cam.z * k)), tuple(float(v) for v in INK), -1, cv2.LINE_AA)
    return Fn(fn)


# ------------------------------------------------------------------ show
FAR = rgba(cv2.GaussianBlur(newsprint(1024, 1024, 77, PAPER, 0.30, cols=4), (0, 0), 5), np.ones((1024, 1024), np.float32))
_CAN = np.zeros((2048, 2048, 4), np.float32)
_CAN[:, :700] = art.wall(700, 2048, 5, 0.50, 'r'); _CAN[:, 1348:] = art.wall(700, 2048, 9, 0.44, 'l'); CANYON = cv2.GaussianBlur(_CAN, (0, 0), 2.2)


def default_bg(fr, t):
    fr.put(FAR, 0, 0, 2.6, depth=3.0, wrap=True, blur=0, shadow=0)
    fr.put(CANYON, 0, 0, 1.2, depth=1.2, wrap=True, shadow=0)


class Show:
    def __init__(self, shots, dur, voice, bg=default_bg, grade=None, whip=0.17, sfx_extra=None, sfx_gain=1.0, floaters_cols=None):
        self.shots, self.dur, self.voice, self.bg, self.grade, self.whip, self.sfx_extra, self.g = shots, dur, voice, bg, grade, whip, sfx_extra, sfx_gain
        self.fcols = floaters_cols or (PAPER, PAPER_LT, ORANGE, art.RED, PAPER)
        step = [(2700, 0), (0, 2900), (2700, 0), (0, -2900)]; x = y = 0
        for i, sh in enumerate(shots):
            sh['o'] = (x, y); dx, dy = step[i % 4]; x += dx; y += dy
            sh['t1'] = shots[i + 1]['t'] if i + 1 < len(shots) else dur
            if 'cam' not in sh: sh['cam'] = [(sh['t'], 0, 0, 1.0), (sh['t1'], 0, -24, 1.07)]
        self.impacts = [(e.hit, sh['o'][0] + e.x, sh['o'][1] + e.y) for sh in shots for e in sh['els'] if e.kind == 'el' and e.a == 'slam' and e.alpha > 0 and not e.quiet]
        self.bursts = [Burst(t_, x_, y_, 20, 800, i, 0.5, cols=(PAPER, PAPER_LT, ORANGE), size=13, puff=0.7, spread=1.4) for i, (t_, x_, y_) in enumerate(self.impacts)]

    def pose(self, i, t):
        sh = self.shots[i]; ks = sh['cam']; ox, oy = sh['o']
        if t <= ks[0][0]: _, x, y, z = ks[0]
        elif t >= ks[-1][0]: _, x, y, z = ks[-1]
        else:
            for a, b in zip(ks, ks[1:]):
                if t <= b[0]:
                    k = seg(t, a[0], b[0]); k = k if len(ks) == 2 else eio(k, 2)
                    x, y = lerp(a[1], b[1], k), lerp(a[2], b[2], k); z = a[3] * (b[3] / a[3]) ** k; break
        return ox + x, oy + y, z

    def shot_at(self, t):
        for i in range(len(self.shots) - 1, -1, -1):
            if t >= self.shots[i]['t']: return i
        return 0

    def cam_at(self, t):
        i = self.shot_at(t); sh = self.shots[i]; W_ = self.whip
        for j, b in ((i, sh['t']), (i + 1, sh['t1'])):
            if 0 < j < len(self.shots) and abs(t - b) < W_:
                A, B = self.pose(j - 1, b - W_), self.pose(j, b + W_); k = eio(seg(t, b - W_, b + W_), 3)
                return Cam(lerp(A[0], B[0], k), lerp(A[1], B[1], k), A[2] * (B[2] / A[2]) ** k * (1 - 0.10 * math.sin(math.pi * k)))
        return Cam(*self.pose(i, t))

    def floaters(self, fr, t, n=20):
        lay = np.zeros((H // 2, W // 2, 4), np.float32); c = fr.cam
        for i in range(n):
            r = np.random.default_rng(1000 + i); bx, by = r.uniform(0, 3000), r.uniform(0, 4200); sz = r.uniform(10, 34) * min(c.z, 2.2); col = self.fcols[i % len(self.fcols)]
            x = ((bx - c.x * 1.7 * c.z + 40 * math.sin(t * .7 + i)) % (W + 500) - 250) / 2; y = ((by - c.y * 1.7 * c.z + t * (25 + 12 * (i % 4))) % (H + 500) - 250) / 2
            a = r.uniform(0, 6.28) + t * r.uniform(-1.5, 1.5); cs, sn = math.cos(a), math.sin(a)
            pts = np.int32([(x + (px * cs - py * sn) * sz / 2, y + (px * sn + py * cs) * sz / 2) for px, py in ((-1, -.6), (1, -.7), (.8, .7), (-1, .5))])
            cv2.fillConvexPoly(lay, pts, (float(col[0]), float(col[1]), float(col[2]), 1.0), cv2.LINE_AA)
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 5), (W, H)); a = lay[..., 3:4] * 0.5
        fr.c = fr.c * (1 - a) + lay[..., :3] * 0.5 * 0.8

    def frame_at(self, t, cam):
        sx = sy = 0.0
        for t0, _, _ in self.impacts:
            if 0 <= t - t0 < 0.45: a, b = shake(t, t0, 15); sx += a; sy += b
        cam = Cam(cam.x + sx, cam.y + sy, cam.z)
        fr = Frame(cam, dof=4.2); self.bg(fr, t)
        i = self.shot_at(t); sh = self.shots[i]; idx = [i]
        if i > 0 and t - sh['t'] < self.whip + .05: idx.insert(0, i - 1)
        if i + 1 < len(self.shots) and sh['t1'] - t < self.whip + .05: idx.append(i + 1)
        for j in idx:
            ox, oy = self.shots[j]['o']
            for e in self.shots[j]['els']: draw_el(fr, e, t, ox, oy)
        for b in self.bursts:
            if 0 <= t - b.t0 < 1.6: b.draw(fr, t)
        self.floaters(fr, t)
        return fr.c

    def render(self, f):
        t = f / FPS; cam, prev = self.cam_at(t), self.cam_at(t - 1 / FPS)
        img = self.frame_at(t, cam)
        img = zoom_blur(img, (cam.z / prev.z - 1) * 1.5, 10)
        img = dir_blur(img, (cam.x - prev.x) * cam.z * 0.75, (cam.y - prev.y) * cam.z * 0.75)
        expo = 1.12 * smooth(seg(t, 0, 0.25)) * (1 - 0.95 * ein(seg(t, self.dur - 0.3, self.dur), 2))
        for t0, _, _ in self.impacts:
            if 0 <= t - t0 < 0.2: expo *= 1 + 0.25 * math.exp(-(t - t0) * 30)
        img = post(img, f, tilt=1.0, expo=expo)
        if self.grade: img = np.clip(self.grade(img, t), 0, 1)
        return (img * 255 + 0.5).astype(np.uint8)

    # -------------------------------------------------------------- sound (subtle)
    def soundtrack(self, path):
        g = self.g; n = int(self.dur * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
        def add(x, t_, gain=1.0, pan=0.0):
            i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]
            Lc[i:i + len(x)] += x * gain * (1 - max(0, pan)); Rc[i:i + len(x)] += x * gain * (1 + min(0, pan))
        tt = np.arange(len(Lc)) / SR
        add((np.sin(2 * np.pi * 43.6 * tt) + 0.5 * np.sin(2 * np.pi * 65.4 * tt + 1) + 0.25 * np.sin(2 * np.pi * 87.3 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, 0.05)
        for hb in np.arange(0.35, self.dur, 60 / 46): add(thump(58, 36, 0.4, 0.09), hb, 0.08); add(thump(52, 34, 0.4, 0.08), hb + 0.19, 0.05)
        for sh in self.shots:
            if sh['t'] > 0.2: add(whoosh(0.5, 250, 2400, 0.5), sh['t'] - 0.25, 0.16 * g, _a.uniform(-.5, .5))
            for e in sh['els']:
                pan = float(np.clip(getattr(e, 'x', 0) / 700, -.6, .6))
                if e.kind == 'stroke': add(scribble(max(0.15, e.dur)), e.t, 0.045 * g, pan)
                elif e.kind == 'el' and e.t is not None and not e.quiet:
                    if e.a == 'slam': add(thump(82, 32, 0.6, 0.14), e.hit, 0.30 * g); add(nburst(0.25, 300, 3000, 0.04), e.hit, 0.10 * g, pan)
                    elif e.a == 'pop': add(thump(170, 95, 0.12, 0.03), e.t, 0.06 * g, pan); add(nburst(0.07, 1500, 6000, 0.012), e.t + .05, 0.03 * g, pan)
                    else: add(whoosh(0.32, 500, 3500, 0.7), e.t - 0.05, 0.06 * g, pan); add(thump(120, 60, 0.2, 0.05), e.hit + .15, 0.07 * g, pan)
        if self.sfx_extra: self.sfx_extra(add)
        mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(0.2 * SR):] *= np.linspace(1, 0, int(0.2 * SR))[:, None]
        w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * 0.9 * 32767).astype(np.int16).tobytes()); w.close()


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
def gunshot(): n = int(0.5 * SR); return _filt(_a.normal(0, 1, n), 200, 6000) * _env(n, 0.0005, 0.04) + thump(120, 50, 0.4, 0.06)[:n] * 0.6


# ------------------------------------------------------------------ CLI
_SHOW = [None]
def _render(f): return _SHOW[0].render(f)


def run(show, argv, voice_offset=0.0, voice_gain='loudnorm=I=-15:TP=-1.5'):
    _SHOW[0] = show; mode = argv[1]
    if mode == 'stills':
        for ts in argv[3].split(','):
            cv2.imwrite(f'{argv[2]}/f_{float(ts):06.2f}.jpg', cv2.resize(show.render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
    elif mode == 'render':
        out = argv[2]; os.makedirs(out, exist_ok=True); total = round(show.dur * FPS)
        lo, hi = (int(v) for v in argv[3].split('-')) if len(argv) > 3 else (0, 999)
        with Pool(4) as p:
            for s0 in range(0, total, 300):
                fn = f'{out}/seg{s0 // 300:02d}.mp4'
                if os.path.exists(fn) or not lo <= s0 // 300 <= hi: continue
                ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4'], stdin=subprocess.PIPE)
                for im in p.imap(_render, range(s0, min(total, s0 + 300)), chunksize=4): ff.stdin.write(im.tobytes())
                ff.stdin.close(); ff.wait(); os.rename(fn + '.tmp.mp4', fn); print('seg', s0 // 300, flush=True)
        print('RENDERED')
    elif mode == 'mux':
        out = argv[2]; sfx = out + '/sfx.wav'; show.soundtrack(sfx)
        open(out + '/list.txt', 'w').write(''.join(f"file '{os.path.abspath(f)}'\n" for f in sorted(glob.glob(out + '/seg*.mp4'))))
        if show.voice:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', out + '/list.txt', '-ss', str(voice_offset), '-i', show.voice, '-i', sfx,
                   '-filter_complex', f'[1:a]aresample=48000,{voice_gain},pan=stereo|c0=c0|c1=c0[v];[v][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]']
        else:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', out + '/list.txt', '-i', sfx, '-filter_complex', '[1:a]alimiter=limit=0.95[a]']
        subprocess.check_call(cmd + ['-map', '0:v', '-map', '[a]', '-t', str(show.dur), '-c:v', 'libx264', '-preset', 'medium', '-crf', '25', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', argv[3]])
        print('MUXED', argv[3])
