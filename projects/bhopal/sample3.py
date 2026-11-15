"""Bhopal 1984 - 21 s sample v3: sample2's opening plus three more scenes, every scene change a different transition (zoom-through and paper tears).
Usage: python3 sample3.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, json, subprocess, glob, wave as wavmod, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, film, kit3d as K
from voxkit.pop3d import Card, World
from voxkit.cine import look, pin, tint, hang, pi
from voxkit.collage import *

_sp = importlib.util.spec_from_file_location('s2', os.path.join(HERE, 'sample2.py')); S = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S)
T = S.T; WORDS = merge_words(S.WORDS, {('unnees', 'sau', 'chauraasi'): '1984', ('do', 'december'): '2 December', ('saath', 'second'): '60 second'}); load = S.load
DUR = 21.0; C1, C2 = S.C1, S.C2; C3 = T('mujhe') - .05; C4 = T('bhopal') - .12; C5 = T('aadhi') - .1
CUT = [(C1, 'zoom', 0), (C2, 'rip', 0.0), (C3, 'rip', pi / 2), (C4, 'rip', .62), (C5, 'rip', -.55)]; TR = .5

# ------------------------------------------------------------------ new plates
V = load('bhopal_plant_3'); VES = grade(V, (1.03, .97, .86), .10, .95, 11); VBG = np.dstack([grade(V, (1.0, .96, .86), .0, .55, 12), np.ones(V.shape[:2], np.float32)]); VFG = layer(VES, subject(V, (.02, .16, .70, .80)), 5)
M = load('taj_ul_masajid_and_its_reflection_bhopal'); MQ = layer(grade(M, (.80, .78, 1.0), .30, .80, 13, 1.2), nonsky(M, .02, .40, .05) * (np.arange(M.shape[0])[:, None] < M.shape[0] * .50), 3)
WATER = band(grade(M, (.70, .72, 1.0), .25, .62, 14, 1.2), .47, seed=15); SKY5 = sky_plate((.20, .16, .30), (.74, .52, .50), 5); SKY6 = sky_plate((.02, .03, .08), (.12, .15, .30), 6, moon=True, stars=160)
TBHOPAL = big_text('BHOPAL', (.93, .80, .16), 360, 3); TKAISE = big_text('KAISE?', (.90, .88, .80), 380, 4); FNIGHT = layer(grade(S.F, (.50, .60, .95), .0, .50, 16, 1.3), S.FA, 3); GNIGHT = band(grade(S.F, (.45, .55, .90), .0, .38, 17, 1.3), .66, seed=3)
_d = S._from_sample(['dial']); STOPW = _d['dial'](); CLOCK = _d['dial'](mode='clock'); CAL = art.calendar('DEC', '2', seed=4)
WD = S.WD


def cam_at(t):
    if t < C3: return S.cam_at(t)
    if t < C4: k = seg(t, C3, C4); return look(lerp(1.8, -1.4, k), lerp(7.5, 4.2, k), lerp(-3, 5, k), 0, lerp(8, 5, k), 30)          # crane down the vessel
    if t < C5: k = seg(t, C4, C5); return look(lerp(-2.2, 1.6, k), lerp(3.0, 6.0, k), lerp(-2, 5, k), 0, 6, 30)                     # rising over the lake
    k = seg(t, C5, DUR); return look(lerp(2.0, -1.0, k), lerp(6.0, 4.6, k), lerp(-3, 3.5, k), 0, 6.5, 30)


def scene4(t, cam):
    C = [Card(VBG, 0, 34, 46, y=-25, shadow=0, blur=2.2, fog=False)]
    k = back(seg(t, T('yeh') - .12, T('yeh') + .3), 1.6)
    if k > 0: C.append(Card(TKAISE, 0, 31, 30 * k, y=17, shadow=0, fog=False))
    C.append(Card(VFG, 0, 26, 36, y=-19.5, shadow=0, fog=False))
    hang(C, STOPW, .6, 11, 4.6 * (1 + .04 * math.sin(t * 12.5)), 2.6, t, T('saath') - .25, ph=.6, swing=.45, L=16)
    typed(C, cam, t, WORDS, C3, C4); hl(C, cam, t, 'SIRF 60 SECOND', T('saath'), T('main'), .80, .72); hl(C, cam, t, 'YEH KAISE HUA?', T('yeh'), C4 + .3, .80, .72)
    return C


def scene5(t, cam):
    C = [Card(SKY5, 2 * math.sin(t * .2), 75, 130, y=-55, shadow=0, blur=1.2, fog=False)]
    k = back(seg(t, T('bhopal') - .05, T('bhopal') + .4), 1.6)
    if k > 0: C.append(Card(TBHOPAL, 0, 29.6, 24 * k, y=17.5 - (1 - k) * 6, shadow=0, fog=False))
    C.append(Card(MQ, 0, 30, 40, y=-25.2, shadow=0, fog=False)); C.append(Card(WATER, .8, 16, 30, y=-17.5 + .12 * math.sin(t * 1.3), shadow=0, fog=False))
    hang(C, CAL, -1.6, 12, 2.6, 3.6, t, T('do') - .2, ph=1.2, swing=.5, L=16)
    typed(C, cam, t, WORDS, C4, C5); hl(C, cam, t, '2 DECEMBER 1984', T('do'), C5 + .3, .80, .78)
    return C


def scene6(t, cam):
    C = [Card(SKY6, 0, 75, 130, y=-52, shadow=0, blur=1.0, fog=False)]
    k = back(seg(t, C5 + .15, C5 + .6), 1.5)
    if k > 0: C.append(Card(CLOCK, -.5, 44, 22 * k, y=10 + .3 * math.sin(t), shadow=0, blur=.5, fog=False))
    C.append(Card(FNIGHT, 0, 30, 58, y=-14.5, shadow=0, fog=False)); C.append(Card(GNIGHT, -1, 15, 44, y=-9.5, shadow=0, fog=False))
    typed(C, cam, t, WORDS, C5, DUR + 1); hl(C, cam, t, 'AADHI RAAT SE PEHLE', T('aadhi') + .1, DUR, .80, .86)
    return C


def s1(t, cam):
    C = S.scene1(t, cam); return [c for c in C if c.z > 3.5]                                   # drop sample2's own captions (pinned at 3.2 m) ...
SCN = [(0, S.scene1), (C1, S.scene2), (C2, S.scene3), (C3, scene4), (C4, scene5), (C5, scene6)]
def scene_at(t): return [fn for t0, fn in SCN if t >= t0][-1]


def raw(t, f):
    fn = scene_at(t); cam = cam_at(t); WD.focus = 14 if fn is S.scene3 else 26 if fn is scene4 else 30
    return WD.render(cam, fn(t, cam), f, t)


def render(f):
    t = min(f / FPS, DUR - .001); img = raw(t, f); dip = 0.0
    for tc, kind, ang in CUT:
        if kind == 'zoom' and abs(t - tc) < .3: img = zoom_blur(img, .5 * math.exp(-abs(t - tc) * 9), 12); dip = .6 * math.exp(-abs(t - tc) * 14)
        if kind == 'rip' and tc <= t < tc + TR: img = rip(img, raw(tc - 1 / FPS, f), seg(t, tc, tc + TR), ang, seed=int(tc * 7))
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(36):
        r = np.random.default_rng(100 + i); cv2.circle(lay, (int((r.uniform(0, W) + 30 * math.sin(t * .4 + i)) % W) // 2, int((r.uniform(0, H) - t * (14 + 6 * (i % 3))) % H) // 2), int(r.uniform(1, 4)), (1, .95, .85), -1, cv2.LINE_AA)
    img = img + cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2) * .22
    expo = 1.25 * smooth(seg(t, 0, .4)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2)) * (1 - dip)
    return (post(img, f, tilt=0.6, expo=expo) * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + 6 * SR); Rc = np.zeros(n + 6 * SR); Rn = np.random.default_rng(4)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .06); add(film.thump(50, 32, .4, .08), hb + .19, .04)
    for tc, kind, ang in CUT:
        if kind == 'zoom': add(film.whoosh(.7, 200, 2400, .55), tc - .4, .16)
        else:                                                                                                                   # paper tearing
            rp = film._filt(Rn.normal(0, 1, int(.55 * SR)), 1200, 7500); m = len(rp); add(rp * np.linspace(1, .15, m) * (.35 + .65 * (Rn.random(m // 60 + 1).repeat(60)[:m] > .35)), tc, .085, (-1) ** int(tc))
    hiss = film._filt(Rn.normal(0, 1, int(3.6 * SR)), 2500, 7000); add(hiss * np.minimum(1, np.arange(len(hiss)) / SR) * np.linspace(1, .2, len(hiss)), T('zehreeli'), .03)
    for tl in (T('unnees'), T('zehreeli'), T('neend'), T('company'), T('court'), T('saath'), T('yeh'), T('bhopal'), T('do'), T('aadhi')): add(film.thump(82, 32, .6, .14), tl, .17); add(film.nburst(.25, 300, 3000, .04), tl, .05)
    for w in S.WORDS:
        if w[1] < DUR: add(film.nburst(.03, 2500, 7000, .008), w[1], .02)
    for i in range(10): add(film.nburst(.02, 3000, 8000, .006), T('saath') + i * .25, .05)                                         # stopwatch
    m = int(5 * SR); t2 = np.arange(m) / SR; bell = lambda f0: sum(a * np.sin(2 * np.pi * f0 * k * t2) * np.exp(-t2 / d) for k, a, d in ((1, .5, 2.6), (2, .35, 1.8), (2.38, .2, 1.2), (.5, .3, 3.2)))
    add(bell(147), T('neend'), .08); add(bell(196), T('aadhi') + .1, .08)
    for i in range(3): add(film.thump(180, 90, .5, .08), T('court') + i * .22, .10)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.3 * SR):] *= np.linspace(1, 0, int(.3 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (360, 640), interpolation=cv2.INTER_AREA)[..., ::-1])
    else:
        out = sys.argv[2]; sfx = out + '.sfx.wav'; soundtrack(sfx)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-t', str(DUR), '-i', VOICE if False else S.VOICE, '-i', sfx,
                               '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={DUR - .25}:d=0.25,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
