"""7 Horrifying Events - 12 s style sample (diorama-doc look in 3D: aged archival prints floating in a dark paper void,
FPV camera with speed ramps). Timings are estimates until the voice-over arrives.
Usage: python3 sample.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, subprocess, wave as wavmod
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Cam3, Card, World, dust

PH = os.path.join(HERE, 'photos', 'wm'); DUR = 12.5; pi = math.pi
# estimated word starts (re-timed to the real voice-over later)
T = {'did': .05, 'five': 1.25, 'years': 1.5, 'one': 1.9, 'disease': 2.15, 'killed': 2.7, 'half': 3.35, 'everyone': 3.8, 'europe': 4.35,
     'it': 5.2, 'black': 6.0, 'death': 6.35, 'thirteen': 7.55, 'forty': 8.1, 'thats': 9.0, 'one2': 9.3, 'give': 9.9, 'sixty': 10.3, 'six': 11.45, 'more': 11.8}
BURNT = np.array([.80, .36, .10], np.float32)


# ------------------------------------------------------------------ aged archival prints (colour kept, but aged towards sepia)
def aged(path, crop=None, w=900, border=26, sat=.45, seed=0):
    img = cv2.imread(path)[..., ::-1].astype(np.float32) / 255
    if crop: x, y, cw, ch = crop; img = img[y:y + ch, x:x + cw]
    h = int(w * img.shape[0] / img.shape[1]); img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    lum = img.mean(2, keepdims=True); sep = lum * np.float32([1.08, .92, .70])
    img = img * sat + sep * (1 - sat)
    img = img * (0.86 + 0.14 * (1 - halftone(lum[..., 0], 4.0) * .35))[..., None] * (0.9 + 0.12 * fbm(h, w, 8, 3, seed))[..., None]
    H_, W_ = h + 2 * border, w + 2 * border
    rgb = paper(H_, W_, np.float32([.90, .84, .70]), seed, .04, .12); rgb[border:border + h, border:border + w] = np.clip(img, 0, 1)
    return rgba(rgb, torn(H_, W_, 6, 2, seed + 3))


TRIUMPH = aged(os.path.join(PH, 'triumph.jpg'), w=1100, seed=1)
TOURNAI = aged(os.path.join(PH, 'tournai.jpg'), (40, 40, 721, 402), w=800, seed=2)
DANCE = aged(os.path.join(PH, 'dance.jpg'), w=620, sat=.2, seed=3)
MAPIMG = cv2.imread(os.path.join(PH, 'plaguemap.png'))[..., ::-1].astype(np.float32)[:740] / 255           # crop the legend off
DOCTOR = art.photo_cutout(os.path.join(PH, 'schnabel.png'), (150, 28, 290, 628), out_h=1100, clip_y=652, cell=3.5, core=False,
                          fg_hint=[(265, 90, 22), (222, 100, 8), (270, 250, 55), (270, 460, 70), (300, 600, 40)], bg_hint=[(115, 48, 24), (170, 46, 14), (420, 48, 24), (470, 46, 18), (176, 140, 10), (395, 140, 22), (190, 185, 12), (420, 260, 25), (165, 260, 10), (415, 600, 26), (425, 560, 20)])
CAL = {y: art.calendar('YEAR', str(y), seed=y) for y in range(1347, 1352)}
PEOPLE = [art3d.person(i) for i in range(12)]
for p in PEOPLE: p[..., :3] = p[..., :3].mean(2, keepdims=True) * np.float32([1.12, .98, .80])                 # sepia paper people
BELLTOWER = K.cut([('p', [(.3, .3), (.7, .3), (.72, 1), (.28, 1)]), ('p', [(.25, .3), (.5, 0), (.75, .3)])], 400, 1300, (.30, .24, .20), 5)
HOUSES = [K.cut([('p', [(0, .45), (.5, 0), (1, .45), (1, 1), (0, 1)])] + ([('p', [(.6, .1), (.7, .1), (.7, .3), (.6, .3)])] if i % 2 else []), 420, 520 + 90 * i, (.26, .21, .17), 30 + i) for i in range(6)]


def numcard(n, s=420):
    rgb = paper(s, int(s * .8), np.float32([.16, .13, .11]), n, .06, .2); t = text_sprite(str(n), 300, BURNT, pad=4, squeeze=.9, distress=.3, seed=n)
    k = min(s * .7 / t.shape[0], s * .6 / t.shape[1]); t = cv2.resize(t, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    c = rgba(rgb, torn(s, int(s * .8), 5, 2, n)); art.paste(c, t, int((c.shape[1] - t.shape[1]) / 2), int((s - t.shape[0]) / 2)); return c
NUMS = {n: numcard(n) for n in range(1, 8)}
_LB = {}
def LB(txt, col=BURNT):
    if (txt, tuple(col)) not in _LB: _LB[(txt, tuple(col))] = art.label(txt, 150, col=np.asarray(col, np.float32), seed=len(txt))
    return _LB[(txt, tuple(col))]
WHITE = np.array([.92, .88, .78], np.float32)

_MC = {}
def map_card(k):
    """The real spread map, revealed outward from Sicily (where it landed in 1347) as k goes 0..1."""
    q = int(k * 30)
    if q not in _MC:
        h, w = MAPIMG.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt((xx - w * .50) ** 2 + (yy - h * .78) ** 2) / (w * 1.05)
        rev = np.clip((q / 30 - r) * 12, 0, 1)[..., None]
        lum = MAPIMG.mean(2, keepdims=True); base = lum * np.float32([.86, .76, .60]) * .55
        img = base * (1 - rev) + MAPIMG * rev
        B = 24; out = np.zeros((h + 2 * B, w + 2 * B, 4), np.float32); out[..., :3] = paper(h + 2 * B, w + 2 * B, np.float32([.88, .82, .68]), 9, .04, .1); out[B:B + h, B:B + w, :3] = img
        out[..., 3] = torn(h + 2 * B, w + 2 * B, 6, 2, 11); _MC[q] = out
    return _MC[q]


# ------------------------------------------------------------------ world: dark paper void with tungsten haze
WORLD = World(art3d.ground_tex(col=(.46, .38, .30), seed=4), art3d.sky((.10, .08, .07), (.66, .48, .32), 9), fog=(.42, .32, .24), fog_d=45, focus=5.0, dof=10)
rng = np.random.default_rng(7)
CROWD = [(x + .25 * (j % 2), 15.6 + j * 1.25) for j in range(4) for x in np.arange(-3.3, 3.31, .95)]
CROWD_P = [int(rng.integers(12)) for _ in CROWD]

# camera keys: (t, x, y, z, yaw, pitch) - glides inside each beat, speed-ramps between them
KEYS = [(0.0, .0, 1.5, -6.5, .05, .02), (1.7, -.1, 1.3, -.4, .02, .03), (2.15, .2, 2.5, 12.0, 0, .10), (4.8, .1, 2.6, 13.4, 0, .11),
        (5.35, -.4, 1.7, 26.2, -.05, .04), (8.8, -.3, 1.65, 27.6, -.03, .04), (9.35, 0, 3.6, 23.6, 0, -.02), (12.5, 0, 3.4, 25.2, 0, -.01)]
def cam_at(t):
    for a, b in zip(KEYS, KEYS[1:]):
        if t <= b[0]:
            k = seg(t, a[0], b[0]); fast = b[0] - a[0] < .7; k = eio(k, 3) if fast else smooth(k)
            v = [lerp(p, q, k) for p, q in zip(a[1:], b[1:])]; return Cam3(*v[:3], yaw=v[3], pitch=v[4], f=1150)
    return Cam3(*KEYS[-1][1:4], yaw=KEYS[-1][4], pitch=KEYS[-1][5], f=1150)


def pin(spr, cam, sx, sy, wf, alpha=1.0, d=3.2):
    ww = wf * W * d / cam.f; hh = ww * spr.shape[0] / spr.shape[1]
    X, Y = (sx - .5) * W * d / cam.f, (.5 - sy) * H * d / cam.f
    cp, sp = math.cos(cam.pitch), math.sin(cam.pitch); Y1 = Y * cp + d * sp; Z1 = -Y * sp + d * cp
    cy, sn = math.cos(cam.yaw), math.sin(cam.yaw)
    return Card(spr, cam.x + X * cy + Z1 * sn, cam.z - X * sn + Z1 * cy, ww, y=cam.y + Y1 - hh / 2, yaw=-cam.yaw, shadow=0, alpha=alpha, fog=False, blur=0)


def chip(C, cam, t, spr, t0, t1, sx, sy, wf):
    if t < t0 - .13 or (t1 is not None and t > t1 + .22): return
    k = seg(t, t0 - .13, t0); s = lerp(2.3, 1, k * k) * (1 - smooth(seg(t, t1, t1 + .22)) if t1 is not None else lerp(2.3, 1, k * k))
    if s > .02: C.append(pin(spr, cam, sx, sy, wf * s, alpha=min(1, k * 2.5)))


def floatc(spr, x, y, z, w, t, ph, amp=.12, yaw=0.0, t0=None, pop=.4):
    """A card hanging in the air, drifting and slowly turning; flips up into view at t0."""
    if t0 is not None and t < t0: return None
    k = 1 if t0 is None else back(seg(t, t0, t0 + pop), 1.5)
    return Card(spr, x + .15 * math.sin(t * .6 + ph), z, w * k, y=y + amp * math.sin(t * .9 + ph), yaw=yaw + .10 * math.sin(t * .5 + ph), shadow=0)


def cards(t, cam):
    C = []; A = lambda c: C.append(c) if c is not None else None
    # ---- the ruined medieval town on the horizon, a bell tower
    for i, (x, z, w) in enumerate(((-10, 44, 4), (-6.5, 47, 4.5), (-3.2, 45, 3.6), (4.8, 46, 4.4), (8.2, 44, 3.8), (11.5, 47, 4.6))): A(Card(HOUSES[i], x, z, w, shadow=.2))
    A(Card(BELLTOWER, 1.8, 47, 3.0, shadow=.2))
    # ---- beat A: "in just five years" - The Triumph of Death hangs in the dark, calendar years flip past it
    A(floatc(TRIUMPH, 0, .9, 3.6, 5.6, t, 0, .08))
    yrs = 1347 + min(4, int(seg(t, T['five'] - .1, T['years'] + .6) * 5)) if t > T['five'] - .1 else None
    if yrs and t < 2.3: A(floatc(CAL[yrs], 2.15, 2.3, 2.6, 1.1, t, 1, .05, -.3))
    # ---- beat B: "one disease killed up to half of everyone in Europe" - the real spread map over a crowd; half of them fall
    A(floatc(map_card(seg(t, T['disease'], T['europe'] + .4)), 0, 3.35, 19.6, 4.0, t, 2, .06, 0, t0=1.95))
    for i, ((x, z), pi_) in enumerate(zip(CROWD, CROWD_P)):
        p = PEOPLE[pi_]; tl = (1 - back(seg(t, 2.0 + (z - 15.6) * .06 + (i % 7) * .02, 2.4 + (z - 15.6) * .06 + (i % 7) * .02), 1.4)) * pi / 2
        if i % 2 == 1:                                                                                                    # every second person falls on "half"
            tf = seg(t, T['half'] + (i % 7) * .05, T['half'] + .45 + (i % 7) * .05); tl = max(tl, (tf ** 2) * pi / 2 * .98)
        C.append(Card(p, x, z, 1.7 * p.shape[1] / p.shape[0], tilt=tl, shadow=.5))
    # ---- beat C: "the Black Death ... 1347" - the plague doctor stands among the dead; the burial and the dance of death float either side
    A(floatc(TOURNAI, -2.1, 1.55, 31.8, 2.7, t, 3, .1, .45, t0=5.1))
    A(floatc(DANCE, 2.0, 1.45, 31.6, 1.9, t, 4, .1, -.45, t0=5.25))
    kd = (1 - back(seg(t, 5.15, 5.6), 1.4)) * pi / 2
    C.append(Card(DOCTOR, 0, 30.6, 1.0, tilt=kd, shadow=.6))
    # ---- beat D: "That's one... six more" - the card 1 lands, then 2-7 fly into a row behind it
    for n in range(2, 8):
        t0 = T['six'] - .55 + (n - 2) * .09
        if t > t0:
            k = eout(seg(t, t0, t0 + .45), 3); x = (n - 4.5) * .92
            C.append(Card(NUMS[n], lerp(x * 3, x * .62, k), 30.4, .62, y=lerp(6, 3.1, k) + .05 * math.sin(t * 2 + n), yaw=(1 - k) * 2.5, shadow=0, fog=False))
    # ---- captions
    chip(C, cam, t, LB('IN JUST 5 YEARS'), T['five'], 1.95, .5, .14, .74)
    chip(C, cam, t, LB('ONE DISEASE', WHITE), T['disease'], 4.85, .5, .13, .62); chip(C, cam, t, LB('UP TO HALF OF EUROPE'), T['half'], 4.85, .5, .84, .9)
    chip(C, cam, t, LB('THE BLACK DEATH'), T['black'], 8.85, .5, .14, .84); chip(C, cam, t, CAL[1347], T['thirteen'], 8.85, .17, .30, .2)
    chip(C, cam, t, NUMS[1], T['one2'], None, .5, .30, .22); chip(C, cam, t, LB('60 SECONDS', WHITE), T['sixty'], None, .5, .82, .6)
    chip(C, cam, t, LB('6 MORE'), T['six'], None, .5, .135, .46)
    return C


def extra(img, cam, t):
    for i in range(4):
        dust(img, cam, ((i % 2 - .5) * 2.5, .2, 16.2 + i * 1.1), t, T['half'] + .38 + i * .1, col=(.36, .30, .24), n=14, seed=20 + i, speed=1.6)


_gr = np.random.default_rng(3)
def motes(img, cam, t):
    """Dust drifting in the light beams, near the lens."""
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(40):
        r = np.random.default_rng(100 + i); x = ((r.uniform(0, W) + 30 * math.sin(t * .4 + i) - cam.x * 60) % W) / 2; y = ((r.uniform(0, H) - t * (14 + 6 * (i % 3))) % H) / 2
        cv2.circle(lay, (int(x), int(y)), int(r.uniform(1, 4)), (1, .85, .6), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2)
    beam = np.clip(1 - np.abs(np.linspace(-1, 1, W, dtype=np.float32)[None, :] + .35 - .25 * np.linspace(0, 1, H, dtype=np.float32)[:, None]) * 1.6, 0, 1) ** 2
    return img + lay * .35 + beam[..., None] * np.float32([.10, .07, .04])


def render(f):
    t = f / FPS; cam = cam_at(t); prev = cam_at(t - 1 / FPS)
    def ex(img, c, tt): extra(img, c, tt)
    img = WORLD.render(cam, cards(t, cam), f, t, ex)
    img = motes(img, cam, t)
    dz = math.hypot(cam.z - prev.z, cam.y - prev.y)
    if dz > .02: img = zoom_blur(img, min(.32, dz * .55), 12)
    ox = (cam.x - prev.x) * 900
    if abs(ox) > 3: img = dir_blur(img, ox, 0)
    expo = 1.22 * smooth(seg(t, 0, .55)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2))
    for th in (T['half'], T['black'], T['one2']):
        if 0 <= t - th < .25: expo *= 1 + .18 * math.exp(-(t - th) * 22)
    img = post(img, f, tilt=0.8, expo=expo)
    lum = img.mean(2, keepdims=True); img = np.clip(img * .78 + lum * np.float32([1.05, .95, .78]) * .22, 0, 1)        # aged sepia grade
    return (img * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .08); add(film.thump(50, 32, .4, .08), hb + .19, .05)
    for tw in (1.75, 4.9, 8.95): add(film.whoosh(.7, 200, 2400, .55), tw, .16)
    m = int(5 * SR); t2 = np.arange(m) / SR                                                                                   # church bell
    bell = sum(a * np.sin(2 * np.pi * f * t2) * np.exp(-t2 / d) for f, a, d in ((196, .5, 2.6), (392, .35, 1.8), (466, .2, 1.2), (587, .16, .9), (784, .1, .6), (98, .3, 3.2)))
    add(bell, T['black'], .12); add(bell, T['thirteen'] + .2, .06)
    for i in range(14): add(film.nburst(.08, 900, 4500, .02), T['half'] + (i % 7) * .05 + .3 + (i // 7) * .08, .03, (-1) ** i * .5)
    for tl in (T['five'], T['disease'], T['half'], T['black'], T['thirteen'], T['one2'], T['sixty'], T['six']): add(film.thump(82, 32, .6, .14), tl, .2); add(film.nburst(.25, 300, 3000, .04), tl, .06)
    for i in range(6): add(film.whoosh(.3, 500, 4000, .7), T['six'] - .55 + i * .09, .05, (i - 2.5) / 4)
    for i in range(int((DUR - T['give']) * 4)): add(film.tick(), T['give'] + .1 + i * .25, .04)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.2 * SR):] *= np.linspace(1, 0, int(.2 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
    else:
        out = sys.argv[2]; sfx = out + '.sfx.wav'; soundtrack(sfx)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', sfx, '-map', '0:v', '-map', '1:a',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
