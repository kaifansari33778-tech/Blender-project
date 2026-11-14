"""7 Horrifying Events - opening sample v2: one medieval town set, shot from three sides, deep focus pulls, big moving figures.
Usage: python3 sample2.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, json, subprocess, wave as wavmod, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film, medieval as M
from voxkit.pop3d import Cam3, Card, World, dust

_sp = importlib.util.spec_from_file_location('s1', os.path.join(HERE, 'sample.py')); S1 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S1)
VOICE = os.path.join(HERE, 'voice', 'full.mp3'); T = film.timeline(json.load(open(os.path.join(HERE, 'voice', 'words.json'))))
DUR = 10.4; pi = math.pi; BURNT = S1.BURNT; WHITE = S1.WHITE; LB = S1.LB; pin = S1.pin; chip = S1.chip
CUT1, CUT2 = T('one') - .06, T('it') - .08                                     # the two camera cuts

# ------------------------------------------------------------------ set pieces
FOLK = [M.folk(k, i) for i, k in enumerate(('man', 'woman', 'man', 'monk', 'woman', 'man', 'child', 'man', 'woman', 'digger', 'man', 'child'))]
HOUSES = [M.house(i) for i in range(6)]; CHURCH = M.church(); WALL = M.wall(); CART = M.cart(); RAT = M.rat(); CROWS = [M.crow(up=True), M.crow(up=False)]
CROSSES = [M.cross(i) for i in range(3)]; WELL = M.well(); STALLS = [M.stall(0), M.stall(1)]; TORCH = M.torch(); SMOKES = [M.smoke(i) for i in range(3)]
HILLS = M.hills(seed=2); HILLS2 = M.hills(seed=5, col=(.34, .27, .24))
TRIUMPH = S1.TRIUMPH; TOURNAI = S1.TOURNAI; DANCE = S1.DANCE; CAL = S1.CAL
WORLD = World(art3d.ground_tex(col=(.42, .35, .28), seed=6), art3d.sky((.12, .10, .13), (.86, .52, .30), 12), fog=(.52, .36, .26), fog_d=55, focus=9.0, dof=17)

rng = np.random.default_rng(3)
TOWN = [(HILLS, 0, 95, 210, 0, 0, 2.2), (HILLS2, 30, 80, 170, 0, 0, 1.8), (WALL, 0, 62, 80, 0, 0, 1.5), (CHURCH, 3, 31, 14, 0, 0, .9)] + \
       [(HOUSES[i % 6], x, z, w, 0, yaw, .6 if z > 20 else None) for i, (x, z, w, yaw) in enumerate(((-15, 26, 7, 0), (-8.5, 25, 6.5, 0), (11, 26, 7, 0), (17, 25, 6.5, 0), (-12, 19, 6, .5), (12.5, 19, 6, -.5),
                                                                                                    (-10.5, 13, 5.6, .9), (10.8, 13, 5.6, -.9), (-9.5, 7, 5.2, 1.2), (9.8, 7, 5.2, -1.2), (-20, 20, 7, 0), (21, 21, 7, 0)))] + \
       [(WELL, .3, 15.5, 2.3, 0, 0, None), (STALLS[0], -4.6, 16.5, 3.0, 0, .25, None), (STALLS[1], 5.0, 17, 3.0, 0, -.25, None), (TORCH, -3.2, 11.5, .42, 0, 0, None), (TORCH, 3.4, 11.8, .42, 0, 0, None), (TORCH, -6.2, 18, .42, 0, 0, None), (TORCH, 6.6, 18.5, .42, 0, 0, None)]
WALKERS = [(int(rng.integers(12)), float(rng.uniform(-6, 5)), float(z), float(rng.choice([-1, 1]) * rng.uniform(.35, .8)), float(rng.uniform(1.6, 1.85))) for z in (8.6, 9.6, 10.4, 11.3, 12.2, 13.0, 13.9, 14.6, 16.2, 17.4, 18.3, 19.4)] + \
          [(0, -5.2, 2.6, 1.0, 1.8), (1, 2.4, 4.0, -.8, 1.7), (3, -1.6, 5.4, .55, 1.85), (4, 1.2, 6.6, -.5, 1.7), (6, -2.6, 4.6, .7, 1.2)]                                        # the last three pass close to the lens
CROWD = [(x + .3 * (j % 2) + float(rng.uniform(-.12, .12)), 10.2 + j * 1.05, int(rng.integers(12))) for j in range(6) for x in np.arange(-3.6, 3.61, .9)]
GRAVES = [(2.5 + i * 1.25 + .4 * (j % 2), 19 + j * 1.5) for j in range(6) for i in range(7)]


def look(x, y, z, tx, ty, tz, f=1150):
    return Cam3(x, y, z, yaw=math.atan2(tx - x, tz - z), pitch=math.atan2(ty - y, math.hypot(tx - x, tz - z)), f=f)


def cam_at(t):
    if t < CUT1:   k = smooth(seg(t, 0, CUT1)); return look(lerp(-6.5, -1.2, k), lerp(1.15, 1.55, k), lerp(-4.0, 2.2, k), 0, 2.4, 16)                    # low orbit into the square
    if t < CUT2:   k = smooth(seg(t, CUT1, CUT2)); return look(lerp(7.2, 4.2, k), lerp(3.3, 2.3, k), lerp(4.2, 7.0, k), -.3, 1.5, 12.8)                  # high from the right, sinking
    k = smooth(seg(t, CUT2, DUR)); return look(lerp(-7.5, -3.8, k), lerp(.95, 1.5, k), lerp(9.0, 13.0, k), 5.5, 3.4, 27)                               # low from the left, towards the churchyard


def focus_at(t):
    if t < CUT1: return lerp(5, 13, smooth(seg(t, 0, CUT1)))                                       # rack focus from the passers-by to the square
    if t < CUT2: return 10.0
    return lerp(6, 15, smooth(seg(t, CUT2, CUT2 + 2.5)))


def up(t, t0, d=.5): return None if t < t0 else (1 - back(seg(t, t0, t0 + d), 1.4)) * pi / 2


def cards(t, cam):
    C = []; A = C.append; fy = -cam.yaw * .8                                                        # figures turn most of the way toward the lens
    # ---- the town builds from the horizon towards the camera
    for spr, x, z, w, y, yaw, bl in TOWN:
        tl = up(t, max(0, (95 - z) * .0115 - .15))
        if tl is not None: A(Card(spr, x, z, w, y=y, yaw=yaw, tilt=tl, blur=bl, shadow=.4))
    for i, (x, z) in enumerate(((-14, 44), (9, 50), (22, 40), (-26, 52))):
        A(Card(SMOKES[i % 3], x + .6 * math.sin(t * .4 + i), z, 7, y=1.5 + (t * .5) % 3, shadow=0, blur=2.0, alpha=.8))
    for i in range(9):                                                                             # crows crossing the sky
        A(Card(CROWS[int(t * 5 + i) % 2], -20 + (t * 3.4 + i * 4.7) % 44, 28 + (i % 3) * 4, 1.5, y=11 + 2.2 * math.sin(i * 1.3) + .4 * math.sin(t * 3 + i), shadow=0, fog=False, blur=.6))
    # ---- shot 3 set dressing: Bruegel's Triumph of Death looms behind the church, the churchyard fills with crosses
    if t > CUT2 - .1:
        A(Card(TRIUMPH, 12, 46, 30, y=7 + .3 * math.sin(t * .5), yaw=-.25, shadow=0, blur=1.4, alpha=.9))
        A(Card(TOURNAI, -1.5 + .2 * math.sin(t * .6), 21.5, 4.6, y=3.6 + .15 * math.sin(t * .9), yaw=fy, shadow=0))
        A(Card(DANCE, 9.5 + .2 * math.sin(t * .5 + 1), 23, 3.4, y=5.2 + .15 * math.sin(t * .8 + 2), yaw=fy, shadow=0))
        for i, (x, z) in enumerate(GRAVES):
            tl = up(t, CUT2 + .15 + (27 - z) * .09 + (i % 7) * .03, .35)
            if tl is not None: A(Card(CROSSES[i % 3], x, z, .62, tilt=tl, shadow=.5))
        k = seg(t, CUT2, DUR); cx = lerp(-9.5, 2.5, k)                                               # the dead-cart rolls through the foreground
        A(Card(CART, cx, 17.6, 3.6, y=.04 * abs(math.sin(t * 9)), shadow=.6)); A(Card(FOLK[9], cx + 2.5, 17.4, 1.9 * FOLK[9].shape[1] / FOLK[9].shape[0], y=.05 * abs(math.sin(t * 5)), yaw=fy, sway=.05, ph=1))
        A(Card(FOLK[3], lerp(-4.5, -1.8, k), 17.6, 1.95 * FOLK[3].shape[1] / FOLK[3].shape[0], y=.04 * abs(math.sin(t * 4.4)), yaw=fy, sway=.04, ph=2))
        for i in range(3): A(Card(FOLK[9], 4.2 + i * 2.6, 20.2 + i * 1.6, 1.8 * FOLK[9].shape[1] / FOLK[9].shape[0], y=.1 * abs(math.sin(t * 3.2 + i)), yaw=fy, sway=.07, ph=i))
    # ---- walkers crossing the square (and three passing close to the lens)
    for i, (pi_, x0, z, vx, hgt) in enumerate(WALKERS):
        if t > CUT1: continue                                                            # the square empties into one crowd for shot 2
        tl = up(t, .55 + i * .04, .35)
        if tl is None: continue
        p = FOLK[pi_]; A(Card(p, x0 + vx * t, z, hgt * p.shape[1] / p.shape[0], y=.06 * abs(math.sin(t * 5.2 + i)), yaw=fy, tilt=tl, sway=.05, ph=i, shadow=.55))
    # ---- shot 2: everyone, then half of them fall
    if t > CUT1 - .05:
        th = T('half')
        for i, (x, z, pi_) in enumerate(CROWD):
            p = FOLK[pi_]; tilt = 0.0; yb = .03 * abs(math.sin(t * 3 + i)); a = 1.0
            if i % 2 == 1:
                kf = seg(t, th + (i % 9) * .045, th + .5 + (i % 9) * .045); tilt = kf ** 2 * pi / 2 * .97; yb *= (1 - kf)
            A(Card(p, x + .04 * math.sin(t * 1.3 + i), z, 1.75 * p.shape[1] / p.shape[0], y=yb, yaw=fy if tilt < .1 else 0, tilt=tilt, sway=.03 if tilt < .1 else 0, ph=i, shadow=.55))
        if t < CUT2:
            A(Card(S1.map_card(seg(t, T('disease'), T('europe') + .5)), -.3 + .1 * math.sin(t * .7), 19.5, 7.2, y=4.6 + .12 * math.sin(t * .9), yaw=-cam.yaw, shadow=0, fog=False))
            for i in range(14):                                                                     # rats
                r = np.random.default_rng(60 + i); x = r.uniform(-7, 5) + (t - CUT1) * r.uniform(1.6, 3.2) * (1 if i % 2 else -1); A(Card(RAT, x, r.uniform(7.2, 17), .5, yaw=0 if i % 2 else pi, shadow=.3))
    return C


def chips(C, cam, t):
    yrs = 1347 + min(4, int(seg(t, T('five') - .15, T('years') + .5) * 5))
    if T('five') - .28 < t < CUT1: chip(C, cam, t, CAL[yrs], T('five') - .15, CUT1 - .25, .5, .31, .26)
    chip(C, cam, t, LB('IN JUST 5 YEARS'), T('just'), CUT1 - .25, .5, .14, .78)
    chip(C, cam, t, LB('ONE DISEASE', WHITE), T('disease'), CUT2 - .25, .5, .12, .62); chip(C, cam, t, LB('UP TO HALF OF EUROPE'), T('half'), CUT2 - .25, .5, .86, .92)
    chip(C, cam, t, LB('THE BLACK DEATH'), T('black'), None, .5, .13, .86); chip(C, cam, t, CAL[1347], T('thirteen'), None, .5, .275, .24)


def extra(img, cam, t):
    for i in range(6): dust(img, cam, (-3 + i * 1.2, .2, 10.5 + (i % 3) * 1.6), t, T('half') + .42 + i * .07, col=(.40, .32, .25), n=12, seed=30 + i, speed=1.5)


def render(f):
    t = f / FPS; cam = cam_at(t); prev = cam_at(max(0, t - 1 / FPS)); WORLD.focus = focus_at(t)
    C = cards(t, cam); chips(C, cam, t)
    img = WORLD.render(cam, C, f, t, extra)
    img = S1.motes(img, cam, t)
    cutk = max(math.exp(-abs(t - CUT1) * 16), math.exp(-abs(t - CUT2) * 16))                        # cuts hide in a short speed-ramp blur
    same = not ((prev_t := t - 1 / FPS) < CUT1 <= t or prev_t < CUT2 <= t)
    if same:
        ox = (cam.yaw - prev.yaw) * cam.f
        if abs(ox) > 3: img = dir_blur(img, ox * .8, 0)
    if cutk > .08: img = zoom_blur(img, .22 * cutk, 10)
    expo = 1.32 * smooth(seg(t, 0, .5)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2)) * (1 + .25 * cutk)
    for th in (T('half'), T('black')):
        if 0 <= t - th < .25: expo *= 1 + .15 * math.exp(-(t - th) * 22)
    img = post(img, f, tilt=0.9, expo=expo)
    lum = img.mean(2, keepdims=True); img = np.clip(img * .80 + lum * np.float32([1.05, .95, .78]) * .20, 0, 1)
    return (img * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 41.2 * tt) + .5 * np.sin(2 * np.pi * 61.7 * tt + 1) + .3 * np.sin(2 * np.pi * 82.4 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, .06)
    for hb in np.arange(.4, DUR, 60 / 46): add(film.thump(56, 34, .4, .09), hb, .07); add(film.thump(50, 32, .4, .08), hb + .19, .045)
    for tw in (CUT1 - .3, CUT2 - .3): add(film.whoosh(.6, 200, 2400, .55), tw, .16)
    for i in range(22): add(film.nburst(.09, 900, 5000, .02), .05 + i * .045, .028, (-1) ** i * .5)                              # the town popping up
    m = int(5 * SR); t2 = np.arange(m) / SR
    bell = sum(a * np.sin(2 * np.pi * fq * t2) * np.exp(-t2 / d) for fq, a, d in ((196, .5, 2.6), (392, .35, 1.8), (466, .2, 1.2), (587, .16, .9), (784, .1, .6), (98, .3, 3.2)))
    add(bell, T('black'), .11); add(bell, T('thirteen'), .07)
    for i in range(18): add(film.nburst(.08, 900, 4500, .02), T('half') + .3 + (i % 9) * .045 + (i // 9) * .1, .03, (-1) ** i * .5)   # bodies falling
    for tl in (T('just'), T('disease'), T('half'), T('black'), T('thirteen')): add(film.thump(82, 32, .6, .14), tl, .2); add(film.nburst(.25, 300, 3000, .04), tl, .06)
    c = film._filt(np.random.default_rng(2).normal(0, 1, int(2.0 * SR)), 250, 1100); add(c * np.sin(np.pi * np.arange(len(c)) / len(c)), .4, .016)   # market murmur
    cw = int(.25 * SR); t3 = np.arange(cw) / SR; caw = np.sin(2 * np.pi * (900 - 500 * t3 / .25) * t3) * np.sin(np.pi * t3 / .25) * (.6 + .4 * np.sign(np.sin(2 * np.pi * 70 * t3)))
    for tc in (CUT2 + .5, CUT2 + .85, CUT2 + 2.4): add(caw, tc, .03, .4)
    r = film._filt(np.random.default_rng(5).normal(0, 1, int(4 * SR)), 60, 400) * (.5 + .5 * np.sin(2 * np.pi * 3 * np.arange(int(4 * SR)) / SR)); add(r, CUT2, .035, -.3)   # cart wheels
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.2 * SR):] *= np.linspace(1, 0, int(.2 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
    else:
        out = sys.argv[2]; sfx = out + '.sfx.wav'; soundtrack(sfx)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-t', '10.25', '-i', VOICE, '-i', sfx,
                               '-filter_complex', '[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st=10.1:d=0.15,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
