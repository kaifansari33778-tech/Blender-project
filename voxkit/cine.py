"""voxkit.cine - cinematic helpers on top of pop3d: aimed cameras and crane shots, giants, hanging props, 2.5D photo reliefs, pinned captions, atmosphere."""
import math, os
import numpy as np, cv2
from .core import *
from . import art, art3d
from .pop3d import Cam3, Card, World, dust
pi = math.pi
BURNT = np.array([.80, .36, .10], np.float32); WHITE = np.array([.92, .88, .78], np.float32)


def look(x, y, z, tx, ty, tz, f=1150):
    return Cam3(x, y, z, yaw=math.atan2(tx - x, tz - z), pitch=math.atan2(ty - y, math.hypot(tx - x, tz - z)), f=f)


def path(t, keys, f=1150):
    """keys: [(time, (x,y,z), (tx,ty,tz))...] - smooth crane move through every key (Catmull-Rom)."""
    if t <= keys[0][0]: return look(*keys[0][1], *keys[0][2], f)
    if t >= keys[-1][0]: return look(*keys[-1][1], *keys[-1][2], f)
    i = max(j for j in range(len(keys) - 1) if t >= keys[j][0]); k = (t - keys[i][0]) / (keys[i + 1][0] - keys[i][0])
    P = [np.float64(keys[max(0, min(len(keys) - 1, j))][1] + keys[max(0, min(len(keys) - 1, j))][2]) for j in (i - 1, i, i + 1, i + 2)]
    v = 0.5 * ((2 * P[1]) + (-P[0] + P[2]) * k + (2 * P[0] - 5 * P[1] + 4 * P[2] - P[3]) * k * k + (-P[0] + 3 * P[1] - 3 * P[2] + P[3]) * k ** 3)
    return look(*v, f)


def up(t, t0, d=.5): return None if t < t0 else (1 - back(seg(t, t0, t0 + d), 1.4)) * pi / 2


def giant(C, spr, x, z, w, t, t0, d=2.4, sway=.3, ph=0.0, blur=1.1, alpha=.9, yaw=0.0, fog=False, y=0.0):
    k = eout(seg(t, t0, t0 + d), 2.5)
    if k < .03: return
    crop = spr[:max(8, int(spr.shape[0] * k))]
    C.append(Card(crop, x + sway * .6 * math.sin(t * .45 + ph), z, w * (1 + .012 * math.sin(t * .9 + ph)), y=y, yaw=yaw + .05 * math.sin(t * .38 + ph), sway=sway, ph=ph, shadow=0, blur=blur, alpha=alpha, fog=fog))


_STR = np.zeros((700, 8, 4), np.float32); _STR[..., :3] = .08; _STR[..., 3] = 1
def hang(C, spr, x, z, w, ybot, t, t0, ph=0.0, swing=.5, yaw=0.0, L=14.0, fog=False, wv=0.0, blur=None, alpha=1.0):
    if t < t0: return
    dt = t - t0; y = ybot + (1 - back(seg(dt, 0, .75), 1.2)) * 13
    a = swing * math.exp(-dt * .55) * math.sin(dt * 2.7 + ph) + .07 * math.sin(t * 1.1 + ph)
    hh = w * spr.shape[0] / spr.shape[1]; xx = x + a * 2.2; fix = pi / 2 - t * 1.3
    C.append(Card(_STR, xx, z + .02, L * 8 / 700, y=y + hh - .05, sway=-a * 2.2, ph=fix, shadow=0, fog=fog, blur=blur, alpha=alpha))
    C.append(Card(spr, xx, z, w, y=y, yaw=yaw + .25 * a, sway=-a * 2.2 * hh / L, ph=fix, shadow=0, fog=fog, wv=wv, blur=blur, alpha=alpha))


def ppl(C, spr, x, z, hgt, t, i, fy, fall=None, tl=0.0, alpha=1.0, bob=.05, sh=.55):
    tilt = tl or 0.0; yb = bob * abs(math.sin(t * 4.6 + i * 1.7))
    if fall is not None:
        kf = seg(t, fall, fall + .5); tilt = max(tilt, kf ** 2 * pi / 2 * .97); yb *= 1 - kf
    C.append(Card(spr, x, z, hgt * spr.shape[1] / spr.shape[0], y=yb, yaw=fy if tilt < .1 else 0, tilt=tilt, sway=.04 if tilt < .1 else 0, ph=i, shadow=sh, alpha=alpha))


# ---- screen-pinned captions
def pin(spr, cam, sx, sy, wf, alpha=1.0, d=3.2):
    ww = wf * W * d / cam.f; hh = ww * spr.shape[0] / spr.shape[1]
    X, Y = (sx - .5) * W * d / cam.f, (.5 - sy) * H * d / cam.f
    cp, sp = math.cos(cam.pitch), math.sin(cam.pitch); Y0 = Y - hh / 2; Yw = Y0 * cp + d * sp; Z1 = -Y0 * sp + d * cp
    cy, sn = math.cos(cam.yaw), math.sin(cam.yaw)
    return Card(spr, cam.x + X * cy + Z1 * sn, cam.z - X * sn + Z1 * cy, ww, y=cam.y + Yw, yaw=-cam.yaw, tilt=-cam.pitch, shadow=0, alpha=alpha, fog=False, blur=0)


def chip(C, cam, t, spr, t0, t1, sx, sy, wf):
    if t < t0 - .13 or (t1 is not None and t > t1 + .22): return
    k = seg(t, t0 - .13, t0); s = lerp(2.3, 1, k * k) * (1 - smooth(seg(t, t1, t1 + .22)) if t1 is not None else 1)
    if s > .02: C.append(pin(spr, cam, sx, sy, wf * s, alpha=min(1, k * 2.5)))


_LB = {}
def LB(txt, col=BURNT):
    if (txt, tuple(col)) not in _LB: _LB[(txt, tuple(col))] = art.label(txt, 150, col=np.asarray(col, np.float32), seed=len(txt))
    return _LB[(txt, tuple(col))]
def wf(txt): return min(.92, .17 + .046 * len(txt))
def caps(C, cam, t, L):
    for e in L:
        txt, col, t0, t1, sy = e[:5]; spr = LB(txt, col) if isinstance(txt, str) else txt
        chip(C, cam, t, spr, t0, t1, e[6] if len(e) > 6 else .5, sy, e[5] if len(e) > 5 else wf(txt))
_CAL = {}
def cal(top, big):
    if (top, big) not in _CAL: _CAL[(top, big)] = art.calendar(top, str(big), seed=len(_CAL) + 3)
    return _CAL[(top, big)]


def tint(spr, c): s = spr.copy(); s[..., :3] *= np.float32(c); return s
def mk(ground, top, bot, fog, fog_d=60, dof=16, seed=1, tex=None):
    return World(tex if tex is not None else art3d.ground_tex(col=ground, seed=seed), art3d.sky(top, bot, seed + 20), fog=fog, fog_d=fog_d, focus=9.0, dof=dof)


def atmos(img, cam, t, col=(1, .85, .6), fall=-1.0, beam=(.10, .07, .04), n=40, amt=.35):
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for i in range(n):
        r = np.random.default_rng(100 + i); x = ((r.uniform(0, W) + 30 * math.sin(t * .4 + i) - cam.x * 60) % W) / 2; y = ((r.uniform(0, H) + fall * t * (14 + 6 * (i % 3)) + cam.y * 40) % H) / 2
        cv2.circle(lay, (int(x), int(y)), int(r.uniform(1, 4)), col, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(cv2.resize(lay, (W, H)), (0, 0), 2.2); sh = .35 + .3 * math.sin(t * .33)
    bm = np.clip(1 - np.abs(np.linspace(-1, 1, W, dtype=np.float32)[None, :] + sh - .25 * np.linspace(0, 1, H, dtype=np.float32)[:, None]) * 1.6, 0, 1) ** 2
    return img + lay * amt + bm[..., None] * np.float32(beam)


# ---- 2.5D photo reliefs: a print whose subject is cut out and floats in front of it, so it shifts with the camera
class Relief:
    def __init__(s, path, w=900, crop=None, border=26, sat=.75, seed=0, tone=(1.06, .96, .80), pop=True):
        img = cv2.imread(path)[..., ::-1].astype(np.float32) / 255
        if crop: x, y, cw, ch = crop; img = img[y:y + ch, x:x + cw]
        h = int(w * img.shape[0] / img.shape[1]); img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
        lum = img.mean(2, keepdims=True); img = np.clip((img * sat + lum * np.float32(tone) * (1 - sat)) * (0.92 + 0.10 * fbm(h, w, 8, 3, seed))[..., None], 0, 1)
        H_, W_ = h + 2 * border, w + 2 * border; rgb = paper(H_, W_, np.float32([.92, .88, .78]), seed, .04, .12); rgb[border:border + h, border:border + w] = img
        s.base = rgba(rgb, torn(H_, W_, 6, 2, seed + 3)); s.fg = None; s.aspect = H_ / W_
        s.back = rgba(np.zeros((H_, W_, 3), np.float32) + .05, torn(H_, W_, 6, 2, seed + 3))
        if pop:
            try:
                sm = cv2.resize((img * 255).astype(np.uint8)[..., ::-1], (300, int(300 * h / w))); m = np.zeros(sm.shape[:2], np.uint8); hh, ww = sm.shape[:2]
                cv2.grabCut(sm, m, (int(ww * .14), int(hh * .10), int(ww * .72), int(hh * .86)), np.zeros((1, 65)), np.zeros((1, 65)), 4, cv2.GC_INIT_WITH_RECT)
                mk_ = ((m == 1) | (m == 3)).astype(np.float32); fr = mk_.mean()
                if .10 < fr < .62:
                    mk_ = cv2.GaussianBlur(cv2.resize(cv2.morphologyEx(mk_, cv2.MORPH_OPEN, np.ones((5, 5))), (w, h)), (0, 0), 3); a = np.clip((mk_ - .4) * 5, 0, 1)
                    fg = np.zeros((H_, W_, 4), np.float32); fg[border:border + h, border:border + w, :3] = np.clip(img * 1.08, 0, 1); fg[border:border + h, border:border + w, 3] = a; s.fg = fg
            except cv2.error: pass

    def add(s, C, x, y, z, w, yaw=0.0, t=0.0, ph=0.0, alpha=1.0, fog=False, blur=None, drift=.12, tilt=0.0, depth=.5):
        yw = yaw + .10 * math.sin(t * .5 + ph); xx = x + drift * math.sin(t * .6 + ph); yy = y + drift * math.sin(t * .9 + ph); nx, nz = math.sin(yw), -math.cos(yw)
        C.append(Card(s.back, xx - nx * .12 + .10, z - nz * .12, w, y=yy - .10, yaw=yw, tilt=tilt, shadow=0, alpha=alpha * .55, fog=fog, blur=blur))
        C.append(Card(s.base, xx, z, w, y=yy, yaw=yw, tilt=tilt, shadow=0, alpha=alpha, fog=fog, blur=blur))
        if s.fg is not None:
            d = depth * w / 6; C.append(Card(s.fg, xx + nx * d, z + nz * d, w * 1.05, y=yy - w * s.aspect * .025, yaw=yw, tilt=tilt, shadow=0, alpha=alpha, fog=fog, blur=blur))
