"""voxkit.show3d - scene runner for the 3D pop-up diorama: items with entrance animations, keyframed camera,
push transitions between scenes, subtle auto sound, CLI (stills / render / mux)."""
import sys, os, math, glob, subprocess, wave as wavmod
import numpy as np, cv2
from multiprocessing import Pool
from .core import *
from . import art, film
from .pop3d import Cam3, Card, World

WHITE = np.array([.95, .93, .86], np.float32); DARK = np.array([.13, .12, .12], np.float32)


class It:
    def __init__(self, **k): self.__dict__.update(k)


_n = [0]
def I(spr, x, z, w, y=0.0, t=None, a='pop', dur=None, yaw=0.0, sway=0.0, wv=0.0, bob=0.0, sh=0.5, fog=True, blur=None, out=None, face=False, flat=False, alpha=1.0, quiet=False, shake=False, drift=(0, 0, 0)):
    _n[0] += 1
    dur = dur or {'pop': .45, 'drop': .4, 'slam': .13, 'grow': .25, 'fade': .3, 'none': .1}[a]
    t0 = None if t is None else (t - dur if a in ('slam', 'drop') else t)
    return It(spr=spr, x=x, y=y, z=z, w=w, t=t0, hit=t, a=a if t is not None else 'none', dur=dur, yaw=yaw, sway=sway, wv=wv, bob=bob, sh=sh, fog=fog, blur=blur, out=out, face=face, flat=flat, alpha=alpha,
              ph=_n[0] * 1.7, quiet=quiet, shake=shake, drift=drift, scr=None)


def _fit_label(spr, maxw=1400):
    return spr if spr.shape[1] <= maxw else cv2.resize(spr, None, fx=maxw / spr.shape[1], fy=maxw / spr.shape[1], interpolation=cv2.INTER_AREA)


_LC = {}
def Lb(txt, x, y, z, w, t, col=ORANGE, a='slam', out=None, shake=True, size=150, anchor=False):
    """A letterpress caption card. By default it is pinned to the screen (always readable, same size whatever the camera does)
    but still lives 4 m into the scene so near objects pass in front of it; anchor=True fixes it to a world position instead."""
    key = (txt, tuple(np.round(col, 3)), size)
    if key not in _LC: _LC[key] = _fit_label(art.label(txt, size, col=np.asarray(col, np.float32), seed=len(txt)))
    it = I(_LC[key], x, z, w, y=y, t=t, a=a, sh=0, fog=False, blur=0, out=out, face=True, shake=shake and a == 'slam')
    if not anchor:
        sy = .125 if y >= 5.5 else .215 if y >= 4.4 else .31 if y >= 2.6 else .5 if y >= 1.0 else .81
        it.scr = (0.5 + x * 0.085, sy, min(.92, w / 5.6))
    return it


def to_card(it, t, cam, t_end=None):
    if it.t is not None and t < it.t: return None
    k = 1.0 if it.t is None else seg(t, it.t, it.t + it.dur)
    tilt, y, w, al = 0.0, it.y, it.w, it.alpha
    if it.a == 'pop':
        if it.flat or it.face: w *= back(k, 1.8)
        else: tilt = (1 - back(k, 1.4)) * math.pi / 2
    elif it.a == 'drop': y += 16 * (1 - k) ** 2 - 0.35 * math.sin(math.pi * seg(t, it.hit, it.hit + .25)) * (t > it.hit) * 0
    elif it.a == 'slam': w *= lerp(2.4, 1, k * k); al *= min(1, k * 2.5)
    elif it.a == 'grow': w *= back(k, 1.8)
    elif it.a == 'fade': al *= k
    if it.out is not None and t > it.out:
        ko = seg(t, it.out, it.out + .25)
        if ko >= 1: return None
        if it.face or it.flat: w *= 1 - ko * ko
        else: tilt = max(tilt, ko * math.pi / 2)
    if w <= 0.01 or al <= 0.01: return None
    if it.flat: tilt = math.pi / 2
    if it.scr is not None:                                                    # screen-pinned caption -> world position on the camera ray
        d = 4.0; sx, sy, wf = it.scr; ww = wf * W * d / cam.f * (w / it.w); hh = ww * it.spr.shape[0] / it.spr.shape[1]
        X, Y, Zc = (sx - .5) * W * d / cam.f, (.5 - sy) * H * d / cam.f, d
        cp, sp = math.cos(cam.pitch), math.sin(cam.pitch); Y1 = Y * cp + Zc * sp; Z1 = -Y * sp + Zc * cp
        cy, sn = math.cos(cam.yaw), math.sin(cam.yaw)
        return Card(it.spr, cam.x + X * cy + Z1 * sn, cam.z - X * sn + Z1 * cy, ww, y=cam.y + Y1 - hh / 2, yaw=-cam.yaw, tilt=0, shadow=0, alpha=al, fog=False, blur=0)
    dt = t - (it.t or 0)
    if it.bob: y += it.bob * abs(math.sin(t * 2.2 + it.ph))
    return Card(it.spr, it.x + it.drift[0] * dt, it.z + it.drift[2] * dt, w, y=y + it.drift[1] * dt, yaw=(-cam.yaw if it.face else it.yaw), tilt=tilt, shadow=it.sh, alpha=al, wv=it.wv, fog=it.fog,
                sway=it.sway, ph=it.ph, blur=it.blur)


def fall(sprs, t0, t1, n, seed, box=(-6, 6, 2, 12), top=9.0, w=0.5, speed=3.0):
    """Things fluttering down through the 3D scene (stamps, papers, cash). Returns fn(t, cam) -> cards."""
    def fn(t, cam):
        out = []
        for i in range(n):
            r = np.random.default_rng(seed * 100 + i); ts = lerp(t0, t1, r.random()); dt = t - ts
            if dt <= 0: continue
            y = top - speed * dt * (0.7 + 0.6 * r.random())
            if y < 0.02: continue
            out.append(Card(sprs[i % len(sprs)], r.uniform(box[0], box[1]) + 0.4 * math.sin(dt * 2 + i), r.uniform(box[2], box[3]), w * r.uniform(.7, 1.3), y=y, yaw=dt * r.uniform(-4, 4) + i, shadow=0, ph=i))
        return out
    return fn


class Show3:
    def __init__(self, scenes, dur, voice, f=1150.0, tr=0.13, sfx_extra=None):
        self.sc, self.dur, self.voice, self.f, self.tr, self.sfx_extra = scenes, dur, voice, f, tr, sfx_extra
        for i, s in enumerate(scenes):
            s['t1'] = scenes[i + 1]['t'] if i + 1 < len(scenes) else dur
            s.setdefault('fns', []); s.setdefault('extra', None)
            s['hits'] = [it.hit for it in s['items'] if it.shake and it.hit is not None]

    def cam(self, s, t):
        ks = s['cam']
        if t <= ks[0][0]: v = ks[0][1:]
        elif t >= ks[-1][0]: v = ks[-1][1:]
        else:
            for a, b in zip(ks, ks[1:]):
                if t <= b[0]:
                    k = eio(seg(t, a[0], b[0]), 2); v = [lerp(p, q, k) for p, q in zip(a[1:], b[1:])]; break
        sx = sy = 0.0
        for th in s['hits']:
            if 0 <= t - th < 0.4: e = (1 - (t - th) / 0.4) ** 2 * 0.045; sx += e * math.sin((t - th) * 70); sy += e * math.cos((t - th) * 83)
        return Cam3(v[0] + sx, v[1] + sy, v[2], yaw=v[3], pitch=v[4], f=self.f)

    def scene_img(self, i, t, f):
        s = self.sc[i]; cam = self.cam(s, t); cards = []
        for it in s['items']:
            c = to_card(it, t, cam)
            if c is not None: cards.append(c)
        for fn in s['fns']: cards += fn(t, cam)
        return s['world'].render(cam, cards, f, t, s['extra'])

    def idx(self, t):
        for i in range(len(self.sc) - 1, -1, -1):
            if t >= self.sc[i]['t']: return i
        return 0

    def render(self, f):
        t = f / FPS; i = self.idx(t); s = self.sc[i]; tr = self.tr
        img = None
        for j, b in ((i, s['t']), (i + 1, s['t1'])):
            if 0 < j < len(self.sc) and abs(t - b) < tr:
                A = self.scene_img(j - 1, t, f); B = self.scene_img(j, t, f); k = eio(seg(t, b - tr, b + tr), 3); d = 1 if j % 2 else -1
                sh = int(k * W); img = np.empty_like(A)
                if d > 0: img[:, :W - sh] = A[:, sh:]; img[:, W - sh:] = B[:, :sh]
                else: img[:, sh:] = A[:, :W - sh]; img[:, :sh] = B[:, W - sh:]
                img = dir_blur(img, 260 * math.sin(math.pi * k), 0)
                break
        if img is None: img = self.scene_img(i, t, f)
        expo = 1.08 * smooth(seg(t, 0, .25)) * (1 - .95 * ein(seg(t, self.dur - .3, self.dur), 2))
        for th in s['hits']:
            if 0 <= t - th < 0.2: expo *= 1 + 0.2 * math.exp(-(t - th) * 30)
        g = s.get('grade')
        img = post(img, f, tilt=0.6, expo=expo)
        if g: img = np.clip(g(img, t), 0, 1)
        return (img * 255 + .5).astype(np.uint8)

    def soundtrack(self, path):
        SR = film.SR; n = int(self.dur * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
        def add(x, t_, g=1.0, pan=0.0):
            i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
        tt = np.arange(len(Lc)) / SR
        add((np.sin(2 * np.pi * 43.6 * tt) + .5 * np.sin(2 * np.pi * 65.4 * tt + 1) + .25 * np.sin(2 * np.pi * 87.3 * tt)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, 0.05)
        for hb in np.arange(0.35, self.dur, 60 / 46): add(film.thump(58, 36, .4, .09), hb, 0.07); add(film.thump(52, 34, .4, .08), hb + .19, 0.045)
        for s in self.sc:
            if s['t'] > 0.2: add(film.whoosh(.5, 250, 2400, .5), s['t'] - .25, 0.15)
            for it in s['items']:
                if it.t is None or it.quiet: continue
                pan = float(np.clip(it.x / 6, -.6, .6))
                if it.a == 'slam': add(film.thump(82, 32, .6, .14), it.hit, 0.26); add(film.nburst(.25, 300, 3000, .04), it.hit, 0.08, pan)
                elif it.a == 'drop': add(film.whoosh(.3, 400, 3000, .7), it.t, 0.05, pan); add(film.thump(100, 45, .4, .1), it.hit, 0.16, pan)
                elif it.a in ('pop', 'grow'): add(film.nburst(.09, 900, 5000, .02), it.t + .05, 0.028, pan)
        if self.sfx_extra: self.sfx_extra(add)
        mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.2 * SR):] *= np.linspace(1, 0, int(.2 * SR))[:, None]
        w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


_S = [None]
def _r(f): return _S[0].render(f)


def run(show, argv):
    _S[0] = show; mode = argv[1]
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
                ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4'], stdin=subprocess.PIPE)
                for im in p.imap(_r, range(s0, min(total, s0 + 300)), chunksize=4): ff.stdin.write(im.tobytes())
                ff.stdin.close(); ff.wait(); os.rename(fn + '.tmp.mp4', fn); print('seg', s0 // 300, flush=True)
        print('RENDERED')
    elif mode == 'mux':
        out = argv[2]; sfx = out + '/sfx.wav'; show.soundtrack(sfx)
        open(out + '/list.txt', 'w').write(''.join(f"file '{os.path.abspath(f)}'\n" for f in sorted(glob.glob(out + '/seg*.mp4'))))
        subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', out + '/list.txt', '-i', show.voice, '-i', sfx,
                               '-filter_complex', '[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,pan=stereo|c0=c0|c1=c0[v];[v][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(show.dur), '-c:v', 'libx264', '-preset', 'medium', '-crf', '26', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', argv[3]])
        print('MUXED', argv[3])
