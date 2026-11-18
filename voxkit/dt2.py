"""voxkit.dt2 - runner and scene helpers for "Documentary Template 2" (full-frame layered photo collage).

A video is a list of scenes. Each scene is ONE phrase of the narration and ONE full-frame image, written as a function
    def scene(t, cam, a, b) -> list[Card]        (a, b = the scene's start / end time in seconds)
The runner adds the typed narration caption, the camera push-in, the transitions, the grade, the sound and the CLI.
See starter/show.py in the skill for a complete working example."""
import sys, os, math, json, glob, subprocess, wave as wavmod
import numpy as np, cv2
from multiprocessing import Pool
from .core import *
from . import art, film, kit3d as K
from .pop3d import Card, World
from .cine import look, pin, tint, hang, pi
from .collage import *

RED = np.float32([.78, .16, .12]); BLUE = np.float32([.20, .50, .86]); GASC = np.float32([.80, .88, .22]); ORANGE2 = np.float32([.86, .30, .12])


# ------------------------------------------------------------------ photos -> plates
def load(path):
    """Read an image as float RGB 0..1."""
    im = cv2.imread(path)
    if im is None: raise FileNotFoundError(path)
    return im[..., ::-1].astype(np.float32) / 255
def opaque(img): return np.dstack([img, np.ones(img.shape[:2], np.float32)]).astype(np.float32)
def skyline_plate(img, tone=(1.02, .97, .88), gain=.95, sat=.06, seed=0, top=.10, bot=.55, pf=.30, band_y=.62, band_gain=.8, rim=4):
    """For a photo with sky above a subject: returns (subject layer with the sky cut away, the lower part as a nearer torn band)."""
    a = nonsky(img, top, bot, pf); return layer(grade(img, tone, sat, gain, seed), a, rim), band(grade(img, tone, sat, gain * band_gain, seed + 1), band_y, seed=seed + 2)
def pop_plate(img, rect=(.14, .10, .72, .86), tone=(1.02, .97, .88), gain=.95, sat=.08, seed=0, bg_gain=.58):
    """For a photo with no clear sky: returns (the whole photo as a dim blurred-able background, the main subject cut out to float in front)."""
    return opaque(grade(img, tone, 0, gain * bg_gain, seed)), layer(grade(img, tone, sat, gain, seed + 1), subject(img, rect), 5)


# ------------------------------------------------------------------ things that move inside a scene
def push(t, t0, t1, i, f=1150):
    """Default camera: slow push-in; drift direction and rise/fall alternate with the scene index i."""
    k = seg(t, t0, t1); sx = 1 if i % 2 else -1; sy = 1 if i % 3 else -1; e = eout(seg(t, t0, t0 + .5), 3) * .25 + k * .75
    return look(sx * lerp(-2.0, 1.6, k), 5.0 + sy * lerp(-1.3, 1.0, k), lerp(-4, 5, e), 0, 6, 30, f)
def pop(C, spr, t, t0, w, y, z=46, x=0.0, t1=1e9, blur=.5):
    """Big word (or any sprite) popping up between the layers at time t0, gone at t1."""
    k = back(seg(t, t0 - .1, t0 + .32), 1.6) * (1 - smooth(seg(t, t1, t1 + .3)))
    if k > .02: C.append(Card(spr, x, z, w * k, y=y, shadow=0, blur=blur, fog=False, alpha=min(1, k * 2)))
def rise(C, spr, t, t0, x, z, w, y, d=.9, **kw):
    """A cut-out rising into frame from below."""
    k = eout(seg(t, t0, t0 + d), 3)
    if k > 0: C.append(Card(spr, x + .12 * math.sin(t * .6), z, w, y=y - (1 - k) * (w * spr.shape[0] / spr.shape[1] + 6), shadow=0, fog=False, **kw))
_PUFF = {}
def gas(C, t, t0, t1, n=24, x0=-34, zr=(9, 29), yr=(-12, -3), a=.26, seed=400, spread=(28, 62), col=GASC):
    """Low cloud creeping in between the layers from one side (x0 < 0: from the left)."""
    key = tuple(np.float32(col))
    if key not in _PUFF: _PUFF[key] = [K.puff(i, col=tuple(float(v) for v in col)) for i in range(5)]
    gk = seg(t, t0, t1)
    for i in range(n):
        r = np.random.default_rng(seed + i); z = r.uniform(*zr); x = x0 + gk * r.uniform(*spread) * (1 if x0 < 0 else -1) + 1.2 * math.sin(t * .7 + i)
        if gk > 0: C.append(Card(_PUFF[key][i % 5], x, z, r.uniform(9, 15), y=r.uniform(*yr) + .5 * math.sin(t + i), shadow=0, alpha=a * min(1, gk * 6), blur=None if z > 16 else 3.0, fog=False))


_AR = {}
def arrow(k, flip=False, col=(.93, .80, .16)):
    """A hand-drawn curved arrow (pointing down-right; down-left when flipped) that draws itself as k goes 0..1."""
    q = (int(k * 12), flip, tuple(col))
    if q not in _AR:
        s = np.zeros((520, 620, 4), np.float32); r = np.random.default_rng(3); P = [(60 + 470 * u + 6 * r.normal(), 70 + 360 * u ** 2.2 + 30 * math.sin(u * 3.1) + 4 * r.normal()) for u in np.linspace(0, 1, 40)]
        n = max(2, int(len(P) * min(1, k / .8)))
        for off in ((0, 0), (3, 2)): cv2.polylines(s, [np.int32([(x + off[0], y + off[1]) for x, y in P[:n]])], False, tuple(col) + (1.0,), 13, cv2.LINE_AA)
        if k > .8:
            (x1, y1), (x0, y0) = P[-1], P[-4]; a = math.atan2(y1 - y0, x1 - x0); L = 95 * min(1, (k - .8) / .2)
            for da in (2.55, -2.55): cv2.line(s, (int(x1), int(y1)), (int(x1 + L * math.cos(a + da)), int(y1 + L * math.sin(a + da))), tuple(col) + (1.0,), 14, cv2.LINE_AA)
        _AR[q] = s[:, ::-1].copy() if flip else s
    return _AR[q]
def point(C, t, t0, t1, x, y, z, w, flip=False, col=(.93, .80, .16)):
    """Hand-drawn arrow whose tip lands on world point (x, y, z). Use sparingly: only where the viewer needs to be shown which thing is meant."""
    if t < t0 or t > t1: return
    k = seg(t, t0, t0 + .45); a = 1 - seg(t, t1 - .25, t1); tipx = (530 / 620 - .5) * w * (-1 if flip else 1)
    C.append(Card(arrow(k, flip, col), x - tipx + .05 * math.sin(t * 7), z, w, y=y - w * 520 / 620 * (1 - 430 / 520), shadow=0, fog=False, alpha=a, blur=0))


def dial(mode='60', s=600):
    """Stopwatch showing a number (mode = the text, e.g. '60') or a clock a few minutes before midnight (mode='clock')."""
    c = np.zeros((int(s * 1.2), s, 4), np.float32); cy = int(s * .68)
    cv2.rectangle(c, (s // 2 - 28, int(s * .04)), (s // 2 + 28, int(s * .22)), (.75, .60, .25, 1), -1); cv2.circle(c, (s // 2, cy), int(s * .47), (.75, .60, .25, 1), -1, cv2.LINE_AA); cv2.circle(c, (s // 2, cy), int(s * .40), (.93, .89, .78, 1), -1, cv2.LINE_AA)
    for i in range(12): a = i * pi / 6; cv2.line(c, (int(s / 2 + s * .33 * math.sin(a)), int(cy - s * .33 * math.cos(a))), (int(s / 2 + s * .38 * math.sin(a)), int(cy - s * .38 * math.cos(a))), (.1, .08, .07, 1), 7, cv2.LINE_AA)
    if mode == 'clock':
        for a, L, th in ((2 * pi * 11.9 / 12, .2, 14), (2 * pi * 54 / 60, .31, 9)): cv2.line(c, (s // 2, cy), (int(s / 2 + s * L * math.sin(a)), int(cy - s * L * math.cos(a))), (.1, .08, .07, 1), th, cv2.LINE_AA)
        cv2.circle(c, (s // 2, cy), 14, (.7, .15, .1, 1), -1, cv2.LINE_AA)
    else:
        ts = text_sprite(mode, 190, np.float32([.12, .10, .08]), pad=4, distress=.2, seed=2); k = s * .42 / ts.shape[1]; ts = cv2.resize(ts, None, fx=k, fy=k); art.paste(c, ts, (s - ts.shape[1]) // 2, cy - ts.shape[0] // 2)
    return c
def person_cutout(path, fg=(), bg=(), sure=(), tone=(1.04, .98, .90), w=700, h=1500, suit=(.085, .09, .10), up=3):
    """A real portrait as a halftone cut-out continued into a plain dark suit, for 'show the real person'.
    fg / sure / bg: lists of polygons (fractions of the photo) marking probably-person, surely-person and surely-background areas for GrabCut."""
    im = cv2.imread(path); im = cv2.resize(im, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC); H_, W_ = im.shape[:2]; m = np.full((H_, W_), cv2.GC_PR_BGD, np.uint8)
    P = lambda poly: np.int32([(x * W_, y * H_) for x, y in poly])
    for poly in fg: cv2.fillPoly(m, [P(poly)], cv2.GC_PR_FGD)
    for poly in sure: cv2.fillPoly(m, [P(poly)], cv2.GC_FGD)
    for poly in bg: cv2.fillPoly(m, [P(poly)], cv2.GC_BGD)
    cv2.grabCut(im, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK); a = ((m == 1) | (m == 3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a); a = (lab == 1 + np.argmax(st[1:, 4])).astype(np.float32); a = cv2.GaussianBlur(cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((15, 15))), (0, 0), 2.5)
    c = np.dstack([im[..., ::-1].astype(np.float32) / 255, a]); k = w / W_; c = cv2.resize(c, (w, int(H_ * k)), interpolation=cv2.INTER_CUBIC); bh = c.shape[0]; lum = c[..., :3].mean(2)
    c[..., :3] = np.clip((lum[..., None] * np.float32(tone) - .5) * 1.2 + .5, 0, 1) * (1 - .16 * halftone(lum, 4.0))[..., None]
    s = np.zeros((h, w, 4), np.float32); cv2.fillPoly(s, [np.int32([(w * .12, bh - 60), (w * .99, bh - 120), (w, h), (w * .06, h)])], tuple(suit) + (1.0,), cv2.LINE_AA)
    al = c[..., 3:4]; s[:bh] = s[:bh] * (1 - al) + c * al; s[..., :3] *= (0.93 + 0.1 * fbm(h, w, 8, 3, 5))[..., None]
    e = cv2.dilate(s[..., 3], np.ones((13, 13))) - s[..., 3]; s[..., :3] = s[..., :3] * (1 - e[..., None]) + CREAM * e[..., None]; s[..., 3] = np.maximum(s[..., 3], np.clip(e * 2, 0, 1)); return s


# ------------------------------------------------------------------ the show
_SHOW = None
def _render(f): return _SHOW.render(f)


class Show:
    """scenes: list of dicts {'t': start seconds, 'fn': scene function, 'trans': None | 'zoom' | tear angle in radians,
                              optional 'cam': f(t, a, b) -> Cam3, 'focus': metres, 'typed': False to hide the typed caption}
    words: [[word, start, end], ...] from forced alignment; number_words: {('nineteen','eighty','four'): '1984'} so captions show digits.
    hits: times of highlight boxes / big words (a soft thump each). sfx: optional f(add, film, T) to add scene sounds."""
    def __init__(s, here, scenes, words, dur, voice=None, number_words=None, hits=(), sfx=None, expo=1.25, caption_words=4, tear=.5):
        s.here, s.scenes, s.raw_words, s.dur, s.voice, s.hits, s.sfx, s.expo, s.n, s.TR = here, scenes, words, dur, voice, list(hits), sfx, expo, caption_words, tear
        s.words = merge_words(words, number_words or {}); s.T = film.timeline(words)
        s.world = World(np.zeros((64, 64, 3), np.float32) + .04, np.zeros((H, W, 3), np.float32) + .04, fog=(.05, .05, .06), fog_d=1e6, focus=30, dof=12)

    def idx(s, t): return max(i for i in range(len(s.scenes)) if t >= s.scenes[i]['t'])
    def span(s, i): return s.scenes[i]['t'], (s.scenes[i + 1]['t'] if i + 1 < len(s.scenes) else s.dur)

    def raw(s, t, f):
        i = s.idx(t); a, b = s.span(i); sc = s.scenes[i]; cam = sc['cam'](t, a, b) if 'cam' in sc else push(t, a, b, i)
        C = sc['fn'](t, cam, a, b)
        if sc.get('typed', True): typed(C, cam, t, s.words, a - .2, b - .05, n=s.n)
        s.world.focus = sc.get('focus', 30); return s.world.render(cam, C, f, t)

    def render(s, f):
        t = min(f / FPS, s.dur - .001); img = s.raw(t, f); dip = 0.0
        for sc in s.scenes[1:]:
            tc, kind = sc['t'], sc.get('trans', 0.0)
            if kind == 'zoom':
                if abs(t - tc) < .3: img = zoom_blur(img, .5 * math.exp(-abs(t - tc) * 9), 12); dip = .6 * math.exp(-abs(t - tc) * 14)
            elif kind is not None and tc <= t < tc + s.TR: img = rip(img, s.raw(tc - 1 / FPS, f), seg(t, tc, tc + s.TR), kind, seed=int(tc * 7))
        lay = np.zeros((H // 2, W // 2, 3), np.float32)                                                                        # drifting dust
        for i in range(36):
            r = np.random.default_rng(100 + i); cv2.circle(lay, (int((r.uniform(0, W) + 30 * math.sin(t * .4 + i)) % W) // 2, int((r.uniform(0, H) - t * (14 + 6 * (i % 3))) % H) // 2), int(r.uniform(1, 4)), (1, .95, .85), -1, cv2.LINE_AA)
        img = img + cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2) * .22
        expo = s.expo * smooth(seg(t, 0, .4)) * (1 - .95 * ein(seg(t, s.dur - .35, s.dur), 2)) * (1 - dip)
        return (post(img, f, tilt=0.6, expo=expo) * 255 + .5).astype(np.uint8)

    def soundtrack(s, path):
        SR = film.SR; n = int(s.dur * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); Rn = np.random.default_rng(4)
        def add(x, t_, g=1.0, pan=0.0):
            i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
        tt = np.arange(len(Lc)) / SR
        add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)      # drone
        for hb in np.arange(.4, s.dur, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)                                    # heartbeat
        for sc in s.scenes[1:]:
            tc, kind = sc['t'], sc.get('trans', 0.0)
            if kind == 'zoom': add(film.whoosh(.7, 200, 2400, .55), tc - .4, .16)
            elif kind is not None: rp = film._filt(Rn.normal(0, 1, int(.55 * SR)), 1200, 7500); m = len(rp); add(rp * np.linspace(1, .15, m) * (.35 + .65 * (Rn.random(m // 60 + 1).repeat(60)[:m] > .35)), tc, .085, (-1) ** int(tc))   # paper tearing
        for tl in s.hits: add(film.thump(82, 32, .6, .14), tl, .16); add(film.nburst(.25, 300, 3000, .04), tl, .045)
        for w in s.raw_words: add(film.nburst(.03, 2500, 7000, .008), w[1], .018)                                                                                              # typing ticks
        if s.sfx: s.sfx(add, film, s.T)
        mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.3 * SR):] *= np.linspace(1, 0, int(.3 * SR))[:, None]
        w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()

    def cli(s, argv=None):
        """stills <dir> t1,t2,..   |   render <outdir> [a-b]   (10 s segments, resumable)   |   mux <outdir> <out.mp4> [crf]"""
        global _SHOW; _SHOW = s; argv = argv or sys.argv; mode = argv[1]
        if mode == 'stills':
            os.makedirs(argv[2], exist_ok=True)
            for ts in argv[3].split(','): cv2.imwrite(f'{argv[2]}/f_{float(ts):06.2f}.jpg', cv2.resize(s.render(round(float(ts) * FPS)), (360, 640), interpolation=cv2.INTER_AREA)[..., ::-1])
        elif mode == 'render':
            out = argv[2]; os.makedirs(out, exist_ok=True); NF = round(s.dur * FPS); nseg = math.ceil(NF / 300); a, b = (int(x) for x in argv[3].split('-')) if len(argv) > 3 else (0, nseg - 1)
            with Pool(min(4, os.cpu_count() or 2)) as p:
                for k in range(a, b + 1):
                    fn = f'{out}/seg_{k:02d}.mp4'
                    if os.path.exists(fn): continue
                    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4'], stdin=subprocess.PIPE)
                    for im in p.imap(_render, range(k * 300, min(NF, (k + 1) * 300)), chunksize=4): ff.stdin.write(im.tobytes())
                    ff.stdin.close(); ff.wait(); os.rename(fn + '.tmp.mp4', fn); print('seg', k, flush=True)
        elif mode == 'mux':
            out, dst = argv[2], argv[3]; crf = argv[4] if len(argv) > 4 else '24'; sfx = dst + '.sfx.wav'; s.soundtrack(sfx); lst = dst + '.txt'
            open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in sorted(glob.glob(f'{out}/seg_*.mp4'))))
            cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst]
            if s.voice and os.path.exists(s.voice):
                cmd += ['-i', s.voice, '-i', sfx, '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={s.dur - .2}:d=0.2,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]', '-map', '0:v', '-map', '[a]']
            else: cmd += ['-i', sfx, '-map', '0:v', '-map', '1:a']
            subprocess.run(cmd + ['-t', str(s.dur), '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', dst], check=True)
            os.remove(sfx); os.remove(lst); print('done', dst)
        else: print(Show.cli.__doc__)
