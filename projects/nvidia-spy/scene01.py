"""Scene 01 (the hook, 0.0-12.4s of the voice-over) - paper-diorama fake-oner.
Usage: python3 scene01.py out.mp4 [--half] [--stills t1,t2,... dir]"""
import sys, os, math, subprocess, wave
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art

DUR = 12.4
VOICE = os.path.join(HERE, 'voice', 'full.mp3'); V0 = 0.0

# ------------------------------------------------------------------ assets
EYE = art.eye_plate(); BAR = art.bar(); WOMAN = art.woman(); MAN = art.man()
PAGE = art.page(portrait=WOMAN)
T_BOT = art.tower(9, seed=3, torn_top=True); T_TOP = art.tower(4, seed=40, torn_bot=True)
RIDGE_A = art.ridge(2600, 620, 1, dark=0.82); RIDGE_B = art.ridge(2600, 620, 7, dark=0.62, amp=200)
CHIP = art.chip(); LABEL = art.label('$4.8 BILLION'); DIAL = art.dial(); HAND = art.hand(); CROWN = art.crown()
FAR = cv2.GaussianBlur(newsprint(1024, 1024, 77, PAPER, 0.30, cols=4), (0, 0), 5); FAR = rgba(FAR, np.ones((1024, 1024), np.float32))
CANYON = np.zeros((2048, 2048, 4), np.float32)
CANYON[:, :700] = art.wall(700, 2048, 5, 0.50, 'r'); CANYON[:, 1348:] = art.wall(700, 2048, 9, 0.44, 'l')
CANYON = cv2.GaussianBlur(CANYON, (0, 0), 2.2)
CAN_S = 3000 * par(1.2) / 2048

G = 2400                                   # zone B ground line
BX, CX, DX = 3000, 3000, 6000
T_SLAM, T_RIP, T_LAND, T_BAR2, T_STAMP, T_CHIP = 1.25, 2.46, 3.86, 5.02, 6.42, 7.72
BURSTS = [Burst(T_SLAM, 0, 0, 46, 1100, 1, 0.3, size=20, puff=1.5, spread=1.6),
          Burst(T_RIP, BX, 1100, 26, 700, 2, 0.5, size=15, puff=0.5),
          Burst(T_LAND, BX + 250, G - 40, 60, 1000, 3, 1.0, size=18, puff=1.5),
          Burst(T_STAMP, CX, 5330, 34, 900, 4, 0.5, cols=(PAPER, ORANGE, PAPER_LT), size=14, puff=0.9, spread=1.5),
          Burst(T_CHIP, CX, 5770, 40, 900, 5, 0.6, cols=(ORANGE, PAPER, PAPER_LT), size=14, puff=0.9)]

KEYS = [  # t, x, y, zoom, ease power into this key
    (1.60, 0, -148, 3.0, 1), (2.00, 0, 0, 1.0, 2.2), (2.06, 0, 0, 1.0, 1),
    (2.42, BX, 300, 1.28, 3), (2.58, BX + 10, 320, 1.3, 1), (3.86, BX + 230, G - 250, 1.12, 2),
    (4.40, BX + 235, G - 240, 1.22, 1), (4.78, CX, 4640, 1.0, 3), (5.95, CX, 4610, 1.07, 1),
    (6.36, CX, 5180, 0.98, 3), (9.05, CX, 5230, 1.07, 1), (9.42, DX, 5150, 0.96, 3), (11.0, DX, 5150, 1.06, 1), (12.4, DX, 5150, 30.0, -1)]


def cam_at(t):
    if t <= KEYS[0][0]: return Cam(*KEYS[0][1:4])
    for a, b in zip(KEYS, KEYS[1:]):
        if t <= b[0]:
            k = seg(t, a[0], b[0]); p = b[4]
            if p == -1:                                   # exponential dive
                k = k ** 1.6; return Cam(lerp(a[1], b[1], k), lerp(a[2], b[2], k), a[3] * (b[3] / a[3]) ** k)
            k = k if p == 1 else (eout(k, p) if a[0] < 2.0 else eio(k, p))
            return Cam(lerp(a[1], b[1], k), lerp(a[2], b[2], k), lerp(a[3], b[3], k))
    return Cam(*KEYS[-1][1:4])


def stroke(fr, pts, k, col, width, depth=0):
    """Hand-drawn marker stroke revealed 0..k (world-space points)."""
    n = max(2, int(len(pts) * cl(k)))
    if k <= 0: return
    sp = np.int32([fr.w2s(x, y, depth) for x, y in pts[:n]])
    sh = fr.c.copy(); cv2.polylines(sh, [sp + np.int32([5, 8])], False, (0, 0, 0), max(1, int(width * fr.cam.z)), cv2.LINE_AA)
    fr.c = cv2.addWeighted(sh, 0.25, fr.c, 0.75, 0)
    cv2.polylines(fr.c, [sp], False, tuple(float(v) for v in col), max(1, int(width * fr.cam.z)), cv2.LINE_AA)


_r = np.random.default_rng(5)
SMILE = [(CX - 78 + 156 * i / 40 + _r.normal(0, 1.2), 4512 + 46 * math.sin(math.pi * i / 40) ** 0.9 - 18 * (abs(i - 20) / 20) ** 3 + _r.normal(0, 1.5)) for i in range(41)]
CIRC = [(CX + 330 * math.cos(a) * (1 + 0.03 * math.sin(3 * a)), 5770 + 300 * math.sin(a) * (1 + 0.04 * math.cos(2 * a)) + 6 * a) for a in np.linspace(-2.0, -2.0 + 2 * math.pi * 1.08, 90)]


def eye_frame(t):
    sx, sy = shake(t, T_SLAM, 26)
    fr = Frame(Cam(sx, sy, lerp(1.0, 1.10, t / 1.6) * lerp(1, 0.55, ein(seg(t, 1.58, 1.9), 2))), dof=0)
    fr.put(EYE, 0, 0, 0.8, shadow=0)
    k = seg(t, T_SLAM - 0.11, T_SLAM)
    if k > 0:
        y = lerp(-1500, 0, k * k); sq = 1 + 0.10 * math.exp(-(t - T_SLAM) * 16) * (t >= T_SLAM)
        fr.put(BAR, 0, y, 0.8, rot=-0.012, sx=sq, sy=2 - sq, shadow=0.75, sh_off=(10, 34))
    BURSTS[0].draw(fr, t)
    return fr.c


def world_frame(t, cam):
    sx, sy = 0, 0
    for t0, amp in ((T_LAND, 30), (T_STAMP, 22), (T_CHIP, 26), (T_RIP, 10)):
        a, b = shake(t, t0, amp); sx += a; sy += b
    cam = Cam(cam.x + sx, cam.y + sy, cam.z)
    fr = Frame(cam, dof=4.2)
    fr.put(FAR, 0, 0, 2.6, depth=3.0, wrap=True, blur=0, shadow=0)
    fr.put(CANYON, 0, 0, CAN_S, depth=1.2, wrap=True, shadow=0)

    # ---- zone A: front page
    if cam.x < 1900:
        fr.put(PAGE, 0, 0, 1.0, rot=0.02)
        fr.put(BAR, 0, -148, 0.25, rot=-0.012, shadow=0.6, sh_off=(4, 9))

    # ---- zone B: the tower and the fall
    if 900 < cam.x and cam.y < 3600:
        fr.put(RIDGE_B, BX - 150, G - 330, 1.25, depth=0.7, anchor=(0.5, 0), shadow=0.3)
        fr.put(T_BOT, BX, G + 20, 1.0, anchor=(0.5, 1), depth=0.05)
        k = seg(t, T_RIP, T_RIP + 1.25)
        topy = G + 20 - T_BOT.shape[0] + 70
        fr.put(T_TOP, BX - 330 * k * k, topy + 1500 * k ** 2.2, 1.0, rot=-1.15 * k ** 1.3 - 0.05 * math.sin(seg(t, T_RIP - .25, T_RIP) * 9) * (t < T_RIP), anchor=(0.5, 1), depth=0.05)
        feet = topy - T_TOP.shape[0] + 14
        ms = 0.92; mh = MAN.shape[0] * ms
        if t < T_RIP:
            wob = 0.05 * math.sin(seg(t, T_RIP - .3, T_RIP) * 10)
            fr.put(MAN, BX, feet, ms, rot=wob, anchor=(0.5, 0.965))
        else:
            k = seg(t, T_RIP, T_LAND); kk = k ** 1.9
            bx = BX + 250 * eout(k, 1.6); by = lerp(feet - mh / 2, G - 95, kk) - 150 * math.sin(math.pi * min(1, k * 2.2)) * (k < 0.455)
            rot = 1.62 * eout(k, 1.3) + 0.6 * math.sin(k * 5) * (1 - k)
            if t > T_LAND: by += -26 * abs(math.sin((t - T_LAND) * 13)) * math.exp(-(t - T_LAND) * 7)
            fr.put(MAN, bx, by, ms, rot=rot)
        fr.put(RIDGE_A, BX, G - 60, 1.3, depth=-0.25, anchor=(0.5, 0), shadow=0.5, sh_off=(0, -18))
        BURSTS[1].draw(fr, t); BURSTS[2].draw(fr, t)

    # ---- zone C: her, the smile, the deal
    if 1200 < cam.x < 5200 and cam.y > 3300:
        fr.put(RIDGE_B, CX + 200, 4250, 1.3, depth=0.9, anchor=(0.5, 0), shadow=0.3)
        k = back(seg(t, 4.66, 5.0), 1.6)
        fr.put(WOMAN, CX, lerp(5750, 4560, k), 1.0, rot=lerp(-0.10, 0.0, k))
        kb = eout(seg(t, T_BAR2 - 0.1, T_BAR2), 2)
        if kb > 0: fr.put(BAR, lerp(CX - 1400, CX, kb), 4372, 0.37, rot=-0.01, sy=0.78, shadow=0.6, sh_off=(5, 12))
        stroke(fr, SMILE, eio(seg(t, 5.52, 5.88), 2), ORANGE * 1.05, 14)
        fr.put(RIDGE_A, CX, 4960, 1.45, depth=-0.12, anchor=(0.5, 0), shadow=0.55, sh_off=(0, -20), tint=0.92)
        k = seg(t, T_STAMP - 0.12, T_STAMP)
        if k > 0:
            fr.put(LABEL, CX, 5330, 0.84 * lerp(3.0, 1.0, k * k) * (1 + 0.06 * math.exp(-(t - T_STAMP) * 18) * (t >= T_STAMP)), rot=-0.055, depth=-0.14, alpha=min(1, k * 2.5), shadow=0.6, blur=0)
        k = seg(t, T_CHIP - 0.13, T_CHIP)
        if k > 0:
            fr.put(CHIP, CX, 5770, 0.95 * lerp(3.4, 1.0, k * k) * (1 + 0.07 * math.exp(-(t - T_CHIP) * 18) * (t >= T_CHIP)), rot=lerp(0.9, 0.09, k), depth=-0.14, alpha=min(1, k * 2.5), shadow=0.65, sh_off=(16, 26), blur=0)
        stroke(fr, CIRC, eio(seg(t, 8.06, 8.44), 2), INK * 0.8, 13, depth=-0.14)
        BURSTS[3].draw(fr, t); BURSTS[4].draw(fr, t)

    # ---- zone D: sixty seconds
    if cam.x > 4000:
        fr.put(RIDGE_B, DX - 200, 4500, 1.3, depth=0.9, anchor=(0.5, 0), shadow=0.3)
        fr.put(RIDGE_A, DX, 5900, 1.45, depth=-0.3, anchor=(0.5, 0), shadow=0.5, sh_off=(0, -20))
        k = back(seg(t, 9.25, 9.6), 2.2)
        press = 26 * math.exp(-max(0, t - 9.62) * 14) * (t >= 9.55)
        fr.put(CROWN, DX, 5150 - 470 * k + press, 1.0 * k, anchor=(0.5, 1), shadow=0.5)
        fr.put(DIAL, DX, 5150, 1.06 * k, rot=lerp(-0.5, 0, k), shadow=0.6, sh_off=(18, 30))
        ticks = np.floor(seg(t, 9.62, 11.6) * 26) / 26
        fr.put(HAND, DX, 5150, 1.0 * k, rot=ticks * 2 * math.pi * 0.86 + 0.03 * math.exp(-((t - 9.62) % (1.98 / 26)) * 60), anchor=(0.5, 0.86), depth=-0.03, shadow=0.6, sh_off=(8, 14))
        cv2.circle(fr.c, tuple(int(v) for v in fr.w2s(DX, 5150)), max(2, int(26 * cam.z * k)), tuple(float(v) for v in INK), -1, cv2.LINE_AA)
    return fr.c


def render(f):
    t = f / FPS
    cam, prev = cam_at(t), cam_at(t - 1 / FPS)
    if t < 1.9:
        img = eye_frame(t)
        if t > 1.6:
            k = smooth(seg(t, 1.64, 1.86)); img = img * (1 - k) + world_frame(t, cam) * k
        img = img * smooth(seg(t, 0.0, 0.3))
    else:
        img = world_frame(t, cam)
    zr = cam.z / prev.z - 1
    if t < 1.9 and t > 1.58: zr = min(zr, -0.10 * math.sin(math.pi * seg(t, 1.58, 1.95)))
    img = zoom_blur(img, zr * 1.5, 12)
    img = dir_blur(img, (cam.x - prev.x) * cam.z * 0.75, (cam.y - prev.y) * cam.z * 0.75)
    expo = 1.12 + 0.5 * math.exp(-abs(t - T_SLAM) * 30) * (t >= T_SLAM)
    expo *= 1 - 0.92 * ein(seg(t, DUR - 0.5, DUR), 2)
    img = post(img, f, tilt=1.0 if t > 1.9 else 0.5, expo=expo)
    return (img * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ sound design (all synthesized)
SR = 48000
_a = np.random.default_rng(21)


def _filt(x, lo=None, hi=None):
    X = np.fft.rfft(x); fq = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(fq)
    if lo: g *= 1 / (1 + (lo / np.maximum(fq, 1)) ** 4)
    if hi: g *= 1 / (1 + (fq / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def _env(n, a, d): t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-np.maximum(t - a, 0) / d)
def thump(f0=70, f1=34, dur=0.7, d=0.16):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t / 0.05)) / SR
    return np.sin(ph) * _env(n, 0.002, d)
def burst(dur=0.4, lo=300, hi=5000, d=0.07): n = int(dur * SR); return _filt(_a.normal(0, 1, n), lo, hi) * _env(n, 0.001, d)
def whoosh(dur=0.45, lo=250, hi=2600, peak=0.6):
    n = int(dur * SR); t = np.linspace(0, 1, n); e = np.exp(-((t - peak) / 0.22) ** 2)
    x = _a.normal(0, 1, n); a = _filt(x, lo, hi * 0.5); b = _filt(x, lo * 2, hi)
    return (a * (1 - t) + b * t) * e
def rip(dur=0.36):
    n = int(dur * SR); t = np.linspace(0, 1, n); x = _filt(_a.normal(0, 1, n), 900, 9000)
    gate = (np.repeat(_a.random(n // 90 + 1), 90)[:n] > 0.35) * 1.0
    return x * gate * np.sin(np.pi * t) ** 0.6
def scribble(dur=0.38):
    n = int(dur * SR); t = np.linspace(0, 1, n); x = _filt(_a.normal(0, 1, n), 1800, 7000)
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 21 * t * dur)) * np.sin(np.pi * t) ** 0.5
def tick(): n = int(0.05 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * 2300 * t) + 0.6 * np.sin(2 * np.pi * 4100 * t)) * np.exp(-t / 0.006) + burst(0.05, 2500, 9000, 0.004)[:n] * 0.5
def riser(dur, f0=40, f1=120):
    n = int(dur * SR); t = np.linspace(0, 1, n); ph = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * t ** 2) / SR
    return (np.sin(ph) * 0.6 + _filt(_a.normal(0, 1, n), 200, 3000) * 0.5 * t) * t ** 2.2


def soundtrack(path):
    n = int(DUR * SR); L = np.zeros(n + SR); R = np.zeros(n + SR)
    def add(x, t, g=1.0, pan=0.0):
        i = int(t * SR); x = x[:len(L) - i]
        L[i:i + len(x)] += x * g * (1 - max(0, pan)); R[i:i + len(x)] += x * g * (1 + min(0, pan))
    t = np.arange(len(L)) / SR
    drone = (np.sin(2 * np.pi * 43.6 * t) + 0.5 * np.sin(2 * np.pi * 65.4 * t + 1) + 0.25 * np.sin(2 * np.pi * 87.3 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 8 - 1.2))
    add(drone, 0, 0.055)
    for hb in np.arange(0.35, DUR, 60 / 46):                                 # heartbeat pulse
        add(thump(58, 36, 0.4, 0.09), hb, 0.16); add(thump(52, 34, 0.4, 0.08), hb + 0.19, 0.10)
    add(riser(1.2), T_SLAM - 1.2, 0.30)
    add(thump(85, 30, 1.0, 0.24), T_SLAM, 0.95); add(burst(0.5, 150, 3500, 0.10), T_SLAM, 0.5); add(burst(0.9, 2000, 9000, 0.25), T_SLAM + 0.02, 0.10)
    add(whoosh(0.5, 200, 2200, 0.5), 1.55, 0.36); add(whoosh(0.5, 300, 3200, 0.55), 2.0, 0.40, -0.5)
    add(rip(0.36), T_RIP - 0.03, 0.34); add(thump(120, 60, 0.3, 0.05), T_RIP, 0.3)
    nf = int(1.3 * SR); tf = np.linspace(0, 1, nf)
    add(np.sin(2 * np.pi * np.cumsum(900 - 560 * tf ** 1.5) / SR) * np.sin(np.pi * tf) ** 1.5 * 0.5 + whoosh(1.3, 200, 1500, 0.7)[:nf], T_RIP + 0.08, 0.13)
    add(thump(70, 32, 0.9, 0.2), T_LAND, 0.85); add(burst(0.45, 200, 2500, 0.09), T_LAND, 0.45); add(rip(0.25), T_LAND + 0.05, 0.12)
    add(whoosh(0.5, 250, 2800, 0.5), 4.35, 0.40)
    add(whoosh(0.3, 600, 5000, 0.6), 4.66, 0.18); add(thump(150, 90, 0.15, 0.03), 4.93, 0.25)
    add(thump(110, 55, 0.3, 0.05), T_BAR2, 0.5); add(burst(0.12, 800, 5000, 0.02), T_BAR2, 0.3)
    add(scribble(0.38), 5.5, 0.20)
    add(whoosh(0.42, 250, 2400, 0.5), 5.95, 0.28)
    add(thump(78, 30, 0.9, 0.2), T_STAMP, 0.95); add(burst(0.3, 300, 4000, 0.05), T_STAMP, 0.5)
    add(whoosh(0.2, 500, 4000, 0.8), T_CHIP - 0.2, 0.2); add(thump(95, 40, 0.7, 0.15), T_CHIP, 0.85); add(burst(0.2, 1500, 8000, 0.03), T_CHIP, 0.4)
    add(np.sin(2 * np.pi * 3100 * t[:4800]) * np.exp(-t[:4800] / 0.02), T_CHIP, 0.10)
    add(scribble(0.4), 8.05, 0.20)
    add(whoosh(0.5, 300, 3200, 0.5), 9.02, 0.40, 0.5); add(thump(140, 80, 0.2, 0.04), 9.58, 0.3)
    for i in range(26): add(tick(), 9.62 + i * 1.98 / 26, 0.16 + 0.004 * i)
    add(riser(1.45, 45, 240), 10.95, 0.55); add(whoosh(1.2, 150, 4000, 0.85), 11.2, 0.5)
    mix = np.stack([L, R], 1)[:n]
    mix[-int(0.06 * SR):] *= np.linspace(1, 0, int(0.06 * SR))[:, None]
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.tanh(mix * 1.1) * 0.9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    out = sys.argv[1]
    if '--stills' in sys.argv:
        i = sys.argv.index('--stills'); d = sys.argv[i + 2]
        for ts in sys.argv[i + 1].split(','):
            cv2.imwrite(f'{d}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
        sys.exit()
    half = '--half' in sys.argv
    sfx = out + '.sfx.wav'; soundtrack(sfx)
    size = (W // 2, H // 2) if half else (W, H)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{size[0]}x{size[1]}', '-r', str(FPS), '-i', '-',
                           '-ss', str(V0), '-t', str(DUR), '-i', VOICE, '-i', sfx,
                           '-filter_complex', f'[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st={DUR - 0.15}:d=0.15,pan=stereo|c0=c0|c1=c0[v];[v][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]',
                           '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for i, im in enumerate(p.imap(render, range(round(DUR * FPS)), chunksize=4)):
            ff.stdin.write((cv2.resize(im, size, interpolation=cv2.INTER_AREA) if half else im).tobytes())
            if i % 60 == 0: print('frame', i, flush=True)
    ff.stdin.close(); ff.wait(); os.remove(sfx)
    print('done', out)
