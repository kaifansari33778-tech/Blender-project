"""Bhopal 1984 - opening sample v2 (10.7 s): one full-frame layered photograph per phrase, slow push-in with parallax,
text between the layers, typed captions with a highlighted key phrase, zoom-through and torn-paper transitions.
Usage: python3 sample2.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, json, subprocess, glob, wave as wavmod
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, kit3d as K
from voxkit.pop3d import Cam3, Card, World
from voxkit.cine import look, pin, tint, hang, pi

VOICE = os.path.join(HERE, 'voice', 'full.mp3'); WORDS = json.load(open(os.path.join(HERE, 'voice', 'words.json'))); T = film.timeline(WORDS); PH = os.path.join(HERE, 'photos', 'wm')
DUR = 10.7; C1, C2 = T('ek') - .06, T('aur') - .02                                       # scene changes
YEL = np.float32([.93, .80, .16]); GASC = (.80, .88, .22); INKC = np.float32([.10, .09, .09]); CREAM = np.float32([.93, .90, .82])


def load(name): return cv2.imread(glob.glob(os.path.join(PH, name + '.*'))[0])[..., ::-1].astype(np.float32) / 255
def grade(img, tone=(1.0, .97, .90), sat=.12, gain=1.0, seed=0, con=1.15):
    lum = img.mean(2, keepdims=True); g = img * sat + lum * np.float32(tone) * (1 - sat); g = np.clip((g - .5) * con + .5, 0, 1) * gain
    h, w = g.shape[:2]; return np.clip(g * (0.90 + 0.14 * fbm(h, w, 6, 3, seed))[..., None] * (1 - .10 * halftone(lum[..., 0], 3.0))[..., None], 0, 1)


def nonsky(img, top=.10, bot=.55):
    """Alpha of everything that is not sky (GrabCut seeded: top rows = sky, lower part = subject)."""
    h, w = img.shape[:2]; k = 400 / w; sm = cv2.resize((img * 255).astype(np.uint8)[..., ::-1], (400, int(h * k))); m = np.full(sm.shape[:2], cv2.GC_PR_BGD, np.uint8)
    m[int(sm.shape[0] * .30):] = cv2.GC_PR_FGD; m[:int(sm.shape[0] * top)] = cv2.GC_BGD; m[int(sm.shape[0] * bot):] = cv2.GC_FGD
    cv2.grabCut(sm, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_MASK)
    a = ((m == 1) | (m == 3)).astype(np.float32); return np.clip((cv2.GaussianBlur(cv2.resize(a, (w, h)), (0, 0), 2.0) - .45) * 6, 0, 1)


def layer(img, a, rim=4):
    s = np.dstack([img, a]).astype(np.float32)
    if rim:
        e = cv2.dilate(a, np.ones((rim * 2 + 1, rim * 2 + 1))) - a; s[..., :3] = s[..., :3] * (1 - e[..., None]) + CREAM * e[..., None]; s[..., 3] = np.maximum(a, np.clip(e * 2, 0, 1))
    return s


def band(img, y0, jag=18, seed=0):
    """The lower part of a photo as a nearer layer with a torn top edge."""
    h, w = img.shape[:2]; sub = img[int(h * y0):]; hh = sub.shape[0]; top = (jag * (1 + fbm(1, w, 40, 3, seed)[0] * 2 + .5 * np.sin(np.arange(w) / 37.0))).astype(np.float32)
    a = np.clip((np.arange(hh)[:, None] - top[None, :]) / 3, 0, 1); return layer(sub, a, 3)


def sky_plate(top, bot, seed=0, moon=False, w=1200, h=1500):
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]; rgb = (np.float32(top) * (1 - g) + np.float32(bot) * g) * np.ones((1, w, 1), np.float32)
    rgb = rgb * (0.85 + 0.3 * fbm(h, w, 5, 4, seed))[..., None]
    if moon: cv2.circle(rgb, (int(w * .68), int(h * .30)), 70, (.95, .93, .82), -1, cv2.LINE_AA); cv2.circle(rgb, (int(w * .70), int(h * .29)), 62, tuple(float(v) for v in np.float32(top) * 1.1), -1, cv2.LINE_AA)
    return np.dstack([np.clip(rgb, 0, 1), np.ones((h, w), np.float32)])


def big_text(txt, col, size=420, seed=1): return text_sprite(txt, size, np.float32(col), pad=10, squeeze=.82, distress=.25, seed=seed)


def box(txt, bg=YEL, fg=INKC, size=150, seed=0):
    t = text_sprite(txt, size, np.float32(fg), pad=6, squeeze=.86, distress=.1, seed=seed); h, w = t.shape[:2]; px, py = int(size * .34), int(size * .2)
    rgb = paper(h + 2 * py, w + 2 * px, np.float32(bg), seed, .04, .12); s = rgba(rgb, torn(h + 2 * py, w + 2 * px, 4, 2, seed + 2)); art.paste(s, t, px, py); return s


# ------------------------------------------------------------------ plates
F = load('union_carbide_pesticide_factory_bhopal_i'); FA = nonsky(F, .06, .62); Fg = grade(F, (1.02, .98, .90), .0, 1.0, 1)
FACT = layer(Fg, FA); GRASS = band(grade(F, (1.0, .97, .88), .0, .8, 2), .66, seed=3)
S = load('slum_in_bhopal_town'); SA = nonsky(S, .41, .52); Sg = grade(S, (.62, .74, 1.0), .10, .62, 4, 1.25)
SLUM = layer(Sg, SA, 0); ROOFS = band(grade(S, (.55, .66, .95), .10, .50, 5, 1.25), .60, seed=6)
MS = load('memorial_statue_1985'); MA = nonsky(MS[:, 60:560], .05, .70) if False else None
def statue():
    img = MS; h, w = img.shape[:2]; k = 400 / w; sm = cv2.resize((img * 255).astype(np.uint8)[..., ::-1], (400, int(h * k))); m = np.full(sm.shape[:2], cv2.GC_PR_BGD, np.uint8); hh = sm.shape[0]
    m[int(hh * .02):int(hh * .55), 120:270] = cv2.GC_PR_FGD; m[int(hh * .18):int(hh * .50), 160:240] = cv2.GC_FGD; m[int(hh * .56):int(hh * .98), 80:330] = cv2.GC_FGD; m[:, :40] = cv2.GC_BGD; m[:int(hh * .5), 330:] = cv2.GC_BGD
    cv2.grabCut(sm, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_MASK); a = ((m == 1) | (m == 3)).astype(np.float32)
    a = np.clip((cv2.GaussianBlur(cv2.resize(a, (w, h)), (0, 0), 2.5) - .45) * 6, 0, 1); return layer(grade(img, (.95, .97, 1.0), 0, .95, 7, 1.2), a, 5)
STATUE = statue()
P = load('dow_chemical_banner_bhopal'); CROWD = band(grade(P, (1.0, .97, .9), .0, .55, 8), .30, seed=9)
SKY1 = sky_plate((.30, .29, .28), (.80, .76, .66), 1); SKY2 = sky_plate((.03, .04, .10), (.16, .20, .36), 2, moon=True); SKY3 = sky_plate((.16, .14, .13), (.42, .36, .30), 3)
T1984 = big_text('1984', (.86, .30, .12)); TRAAT = big_text('EK RAAT', (.90, .88, .80), 300, 2); COURT = tint(K.courthouse(), (.78, .76, .72))
PUFFS = [K.puff(i, col=GASC) for i in range(5)]; GAVEL = art.gavel()
exec(open(os.path.join(HERE, 'sample.py')).read().split('def dial')[0].split('def chair')[1].join(['def chair', '']) if False else '')
import importlib.util
def _from_sample(names):
    src = open(os.path.join(HERE, 'sample.py')).read(); out = {}
    for n in names:
        i = src.index(f'def {n}('); j = src.index('\n\n\n', i); exec(src[i:j], globals(), out)
    return out
_f = _from_sample(['chair', 'boss']); CHAIR = _f['chair'](); BOSS = _f['boss']()
WD = World(np.zeros((64, 64, 3), np.float32) + .04, np.zeros((H, W, 3), np.float32) + .04, fog=(.05, .05, .06), fog_d=1e6, focus=30, dof=12)


def cam_at(t):
    if t < C1: k = seg(t, 0, C1); e = k + .35 * ein(seg(t, C1 - .35, C1), 2); return look(lerp(-1.6, 1.2, k), lerp(4.4, 5.6, k), lerp(-2, 5, e) + 16 * ein(seg(t, C1 - .3, C1), 2), lerp(-1.6, 1.2, k) * .6, 6.5, 30)
    if t < C2: k = seg(t, C1, C2); return look(lerp(2.2, -1.8, smooth(k)), lerp(6.5, 4.6, k), lerp(-12, 4.5, eout(seg(t, C1, C1 + .55), 3) * .55 + k * .45), 0, 5.5, 30)
    k = seg(t, C2, DUR); return look(lerp(-2, 1.6, k), lerp(3.6, 5.2, k), lerp(-3, 4, k), 0, 6.5, 30)


def typed(C, cam, t, a, b, sy=.085):
    """The narration typed word by word in a small label; words a..b (indices into WORDS)."""
    ws = [w for w in WORDS[a:b] if w[1] <= t + .03]
    if not ws or t > WORDS[b - 1][2] + .7: return
    ws = ws[(len(ws) - 1) // 4 * 4:]                                                           # four words at a time, so the type stays large
    txt = ' '.join(w[0] for w in ws).replace('unnees sau chauraasi', '1984'); txt = txt[0].upper() + txt[1:]
    s = box(txt, CREAM, INKC, 96, 1); C.append(pin(s, cam, .5, sy, min(.92, s.shape[1] * .00072)))


def hl(C, cam, t, txt, t0, t1, sy, wfr, bg=YEL, rot=0):
    if t < t0 - .1 or t > t1: return
    k = back(seg(t, t0 - .1, t0 + .12), 2.2); C.append(pin(box(txt, bg), cam, .5, sy, wfr * k, alpha=min(1, k * 2)))


def scene1(t, cam):
    C = [Card(SKY1, 2 * math.sin(t * .2), 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]
    k = back(seg(t, T('unnees') - .1, T('unnees') + .35), 1.6)
    if k > 0: C.append(Card(T1984, 0, 46, 34 * k, y=17 + (1 - k) * -14, shadow=0, blur=.6, fog=False))
    C.append(Card(FACT, 0, 30, 58, y=-14.5, shadow=0, fog=False)); C.append(Card(GRASS, -1, 15, 44, y=-9.5, shadow=0, fog=False))
    for i in range(4): C.append(Card(PUFFS[i], -8 + i * 5 + .6 * t, 29.5, 9, y=13 + i % 2 * 2 + .3 * t, shadow=0, alpha=.0, fog=False))
    typed(C, cam, t, 0, 9); hl(C, cam, t, '1984 MEIN', T('unnees'), C1, .80, .52)
    return C


def scene2(t, cam):
    C = [Card(SKY2, 0, 75, 130, y=-52, shadow=0, blur=1.2, fog=False)]
    k = back(seg(t, C1 + .1, C1 + .5), 1.6) * (1 - smooth(seg(t, T('zehreeli') + .5, T('zehreeli') + 1.0)))
    if k > .02: C.append(Card(TRAAT, 0, 46, 40 * k, y=19, shadow=0, blur=.5, fog=False, alpha=min(1, k * 2)))
    C.append(Card(SLUM, 0, 30, 62, y=-17, shadow=0, fog=False))
    gk = seg(t, T('zehreeli') - .1, C2)
    for i in range(26):                                                                          # the gas creeps in between the layers, low to the ground
        r = np.random.default_rng(400 + i); z = r.uniform(9, 29); x = -34 + gk * r.uniform(28, 62) + 1.2 * math.sin(t * .7 + i)
        if gk > 0: C.append(Card(PUFFS[i % 5], x, z, r.uniform(9, 15), y=r.uniform(-12, -3) + .5 * math.sin(t + i), shadow=0, alpha=.26 * min(1, gk * 6), blur=None if z > 16 else 3.0, fog=False))
    C.append(Card(ROOFS, 1, 15, 46, y=-13.5, shadow=0, fog=False))
    k = eout(seg(t, T('hazaaron') - .15, T('hazaaron') + .9), 3)
    if k > 0: C.append(Card(STATUE, 1.5 + .15 * math.sin(t * .6), 8.0, 6.4, y=-1.4 - (1 - k) * 12, yaw=-.12 + .04 * math.sin(t * .5), shadow=0, fog=False))
    typed(C, cam, t, 9, 23); hl(C, cam, t, 'ZEHREELI GAS', T('zehreeli'), T('neend') - .05, .80, .66, np.float32(GASC)); hl(C, cam, t, 'NEEND MEIN HI', T('neend'), C2 + .3, .80, .66, YEL)
    return C


def scene3(t, cam):
    C = [Card(SKY3, 0, 75, 130, y=-55, shadow=0, blur=1.2, fog=False)]
    k = eout(seg(t, T('maalik') - .2, T('maalik') + 1.0), 3)
    if k > 0: C.append(Card(BOSS, .5 * math.sin(t * .5), 44, 30, y=-14 - (1 - k) * 30, shadow=0, blur=.8, fog=False, sway=.3))
    C.append(Card(COURT, 0, 30, 40, y=-9, shadow=0, fog=False)); C.append(Card(CHAIR, -.3, 12, 4.0, y=-3.6, shadow=0, fog=False, yaw=.12))
    hang(C, GAVEL, 3.4, 13, 4.4, 6.2, t, T('court') - .15, ph=1.1, swing=.5, L=16)
    C.append(Card(CROWD, 0, 6.5, 22, y=-11.2 + 1.6 * eout(seg(t, C2, C2 + .8), 3), shadow=0, fog=False, blur=3.5))
    typed(C, cam, t, 23, 32); hl(C, cam, t, 'COMPANY KA MAALIK', T('company'), T('kabhi') + .2, .80, .82); hl(C, cam, t, 'COURT TAK NAHI PAHUNCHA', T('court'), DUR, .80, .90)
    return C


def frame(t, f, sc):
    cam = cam_at(t) if sc is None else sc[1]; fn = scene1 if t < C1 else scene2 if t < C2 else scene3
    if sc: fn = sc[0]
    WD.focus = 30 if fn is not scene3 else 14
    return WD.render(cam, fn(t, cam), f, t)


def render(f):
    t = min(f / FPS, DUR - .001); img = frame(t, f, None)
    if abs(t - C1) < .3: img = zoom_blur(img, .5 * math.exp(-abs(t - C1) * 9), 12)
    if C2 - .02 <= t < C2 + .42:                                                              # torn-paper wipe: a jagged strip opens from the middle
        k = eio(seg(t, C2 - .02, C2 + .42), 2); old = frame(C2 - .03, f, (scene2, cam_at(C2 - .03))); yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
        jag = 34 * (2 * np.abs(((yy / 150) % 1) - .5) * 2 - 1); d = np.abs(xx - W / 2 + jag * np.sign(xx - W / 2)) - k * (W * .62)
        m = np.clip(d / 3, 0, 1)[..., None]; edge = np.clip(1 - np.abs(d - 9) / 9, 0, 1)[..., None]; img = img * (1 - m) + old * m; img = img * (1 - edge) + np.float32([.16, .14, .50]) * edge
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(36):
        r = np.random.default_rng(100 + i); cv2.circle(lay, (int((r.uniform(0, W) + 30 * math.sin(t * .4 + i)) % W) // 2, int((r.uniform(0, H) - t * (14 + 6 * (i % 3))) % H) // 2), int(r.uniform(1, 4)), (1, .95, .85), -1, cv2.LINE_AA)
    img = img + cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2) * .22
    expo = 1.25 * smooth(seg(t, 0, .4)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2)) * (1 - .6 * math.exp(-abs(t - C1) * 14))
    return (post(img, f, tilt=0.6, expo=expo) * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); Rn = np.random.default_rng(4)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)
    add(film.whoosh(.7, 200, 2400, .55), C1 - .4, .16); rip = film._filt(Rn.normal(0, 1, int(.45 * SR)), 1200, 7000); add(rip * np.linspace(1, .2, len(rip)) * (.5 + .5 * np.sign(np.sin(np.arange(len(rip)) / 90.0))), C2 - .02, .07)
    hiss = film._filt(Rn.normal(0, 1, int(3.6 * SR)), 2500, 7000); add(hiss * np.minimum(1, np.arange(len(hiss)) / SR) * np.linspace(1, .2, len(hiss)), T('zehreeli'), .03)
    for tl in (T('unnees'), T('zehreeli'), T('neend'), T('company'), T('court')): add(film.thump(82, 32, .6, .14), tl, .17); add(film.nburst(.25, 300, 3000, .04), tl, .05)
    for w in WORDS:
        if w[1] < DUR: add(film.nburst(.03, 2500, 7000, .008), w[1], .02)                                                      # typing ticks
    m = int(5 * SR); t2 = np.arange(m) / SR; bell = sum(a * np.sin(2 * np.pi * 147 * k * t2) * np.exp(-t2 / d) for k, a, d in ((1, .5, 2.6), (2, .35, 1.8), (2.38, .2, 1.2), (.5, .3, 3.2))); add(bell, T('neend'), .08)
    for i in range(3): add(film.thump(180, 90, .5, .08), T('court') + i * .22, .10)
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
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
