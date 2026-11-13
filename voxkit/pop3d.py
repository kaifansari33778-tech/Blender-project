"""voxkit.pop3d - a 3D pop-up paper diorama: upright paper cards in a perspective world with a ground plane,
cast shadows, depth-of-field, distance haze and a moving camera. Uses the same paper sprites as the 2D engine."""
import math
import numpy as np
import cv2
from .core import W, H, FPS, PAPER, PAPER_LT, INK, ORANGE, paper, fbm, rgba, torn, post, lerp, seg, cl, eout, eio, back, wave


class Cam3:
    def __init__(s, x=0.0, y=1.6, z=0.0, yaw=0.0, pitch=0.0, f=1500.0):
        s.x, s.y, s.z, s.yaw, s.pitch, s.f = x, y, z, yaw, pitch, f

    def to_cam(s, P):
        P = np.asarray(P, np.float64).reshape(-1, 3) - np.array([s.x, s.y, s.z])
        cy, sy = math.cos(s.yaw), math.sin(s.yaw)
        X = P[:, 0] * cy - P[:, 2] * sy; Z = P[:, 0] * sy + P[:, 2] * cy; Y = P[:, 1]
        cp, sp = math.cos(s.pitch), math.sin(s.pitch)
        Y2 = Y * cp - Z * sp; Z2 = Y * sp + Z * cp
        return np.stack([X, Y2, Z2], 1)

    def project(s, P):
        C = s.to_cam(P); Z = np.maximum(C[:, 2], 1e-6)
        return np.stack([W / 2 + s.f * C[:, 0] / Z, H / 2 - s.f * C[:, 1] / Z], 1), C[:, 2]


class Card:
    """An upright paper card. (x, y, z) = centre of its bottom edge; w = width in metres; tilt 0 = upright, pi/2 = lying flat."""
    def __init__(s, spr, x, z, w, y=0.0, yaw=0.0, tilt=0.0, shadow=0.5, alpha=1.0, wv=0.0, fog=True, sway=0.0, ph=0.0, blur=None, tag=None):
        s.spr, s.x, s.y, s.z, s.w, s.yaw, s.tilt, s.shadow, s.alpha, s.wv, s.fog, s.sway, s.ph, s.blur, s.tag = spr, x, y, z, w, yaw, tilt, shadow, alpha, wv, fog, sway, ph, blur, tag
        s.h = w * spr.shape[0] / spr.shape[1]
        a = cv2.resize(spr[..., 3], (max(8, spr.shape[1] // 6), max(8, spr.shape[0] // 6)), interpolation=cv2.INTER_AREA); s._sh = a

    def corners(s):
        r = np.array([math.cos(s.yaw), 0, math.sin(s.yaw)]) * s.w / 2
        u = np.array([-math.sin(s.yaw) * math.sin(s.tilt) * 0, math.cos(s.tilt), math.sin(s.tilt)]) * s.h
        p = np.array([s.x, s.y, s.z])
        return np.array([p - r + u, p + r + u, p + r, p - r])          # TL, TR, BR, BL


def _warp_quad(spr, dst, premul=True):
    """Perspective-warp an RGBA (or single channel) sprite onto screen quad dst (TL,TR,BR,BL). Returns (layer, x0, y0) cropped to the screen."""
    x0, y0 = max(0, int(math.floor(dst[:, 0].min())) - 2), max(0, int(math.floor(dst[:, 1].min())) - 2)
    x1, y1 = min(W, int(math.ceil(dst[:, 0].max())) + 3), min(H, int(math.ceil(dst[:, 1].max())) + 3)
    if x1 - x0 < 2 or y1 - y0 < 2: return None, 0, 0
    h, w = spr.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, np.float32(dst - [x0, y0]))
    return cv2.warpPerspective(spr, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0), x0, y0


class World:
    def __init__(s, ground, sky, fog=(0.86, 0.78, 0.62), fog_d=70.0, light=(0.55, 0.75), tile=10.0, focus=9.0, dof=16.0):
        s.ground, s.sky, s.fog, s.fog_d, s.light, s.tile, s.focus, s.dof = ground, sky, np.asarray(fog, np.float32), fog_d, light, tile, focus, dof
        s._gp = ground.copy()

    def draw_ground(s, img, cam):
        n, F, Lt = 0.9, 160.0, 90.0
        cy, sy = math.cos(cam.yaw), math.sin(cam.yaw)
        loc = [(-Lt, F), (Lt, F), (Lt * 0.03, n), (-Lt * 0.03, n)]
        wp = np.array([[cam.x + lx * cy + lz * sy, 0, cam.z - lx * sy + lz * cy] for lx, lz in loc])
        sp, Z = cam.project(wp)
        if Z.min() < 0.05: return
        k = s.ground.shape[1] / s.tile
        tp = np.float32([[p[0] * k, -p[2] * k] for p in wp])
        Hm = cv2.getPerspectiveTransform(tp, np.float32(sp))
        g = cv2.warpPerspective(s.ground, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        m = np.zeros((H, W), np.float32); cv2.fillConvexPoly(m, np.int32(sp), 1.0, cv2.LINE_AA)
        hy = sp[0, 1]                                                        # horizon row: haze the far ground into the fog colour
        yy = np.arange(H, dtype=np.float32)[:, None]
        haze = np.clip(1 - (yy - hy) / (H * 0.16), 0, 1) ** 1.5
        g = g * (1 - haze[..., None]) + s.fog * haze[..., None]
        img[:] = img * (1 - m[..., None]) + g * m[..., None]

    def render(s, cam, cards, f=0, t=0.0, extra=None):
        img = s.sky.copy()
        s.draw_ground(img, cam)
        info = []
        for c in cards:
            if c.alpha <= 0.01: continue
            q = c.corners()
            if c.sway: q[:2, 0] += c.sway * math.sin(t * 1.3 + c.ph)
            sp, Z = cam.project(q)
            if Z.min() < 0.25: continue
            info.append((float(Z.mean()), c, sp, q))
        info.sort(key=lambda a: -(a[0] + (1000.0 if a[1].tilt > 1.4 else 0.0)))      # cards lying flat on the ground are drawn first
        # ---- cast shadows on the ground
        shl = np.zeros((H, W), np.float32)
        for zc, c, sp, q in info:
            if not c.shadow or c.y > 0.6 or zc > 60: continue
            hh = c.h * math.cos(c.tilt)
            off = np.array([s.light[0] * hh, 0, s.light[1] * hh])
            base_r, base_l = q[2].copy(), q[3].copy(); base_r[1] = base_l[1] = 0.01
            sq, Zs = cam.project(np.array([base_l + off, base_r + off, base_r, base_l]))
            if Zs.min() < 0.25: continue
            lay, x0, y0 = _warp_quad(c._sh, sq)
            if lay is None: continue
            reg = shl[y0:y0 + lay.shape[0], x0:x0 + lay.shape[1]]; np.maximum(reg, lay * c.shadow * c.alpha, out=reg)
        shl = cv2.GaussianBlur(shl, (0, 0), 7)
        img *= (1 - 0.75 * shl)[..., None]
        # ---- cards, far to near
        for zc, c, sp, q in info:
            spr = wave(c.spr, t + c.ph, c.wv) if c.wv else c.spr
            pm = spr.copy(); pm[..., :3] *= pm[..., 3:4]
            lay, x0, y0 = _warp_quad(pm, sp)
            if lay is None: continue
            sig = c.blur if c.blur is not None else s.dof * abs(1.0 / max(zc, 0.3) - 1.0 / s.focus)
            if sig > 0.7: lay = cv2.GaussianBlur(lay, (0, 0), min(sig, 30))
            a = lay[..., 3:4] * c.alpha; rgb = lay[..., :3] * c.alpha
            if c.fog:
                k = 1 - math.exp(-max(zc, 0) / s.fog_d)
                rgb = rgb * (1 - k) + s.fog * a * k
            reg = img[y0:y0 + lay.shape[0], x0:x0 + lay.shape[1]]
            reg[:] = reg * (1 - a) + rgb
        if extra: extra(img, cam, t)
        return img


def dust(img, cam, pts, t, t0, col=PAPER, n=40, seed=0, speed=3.0):
    """Paper scraps bursting from world point pts=(x,y,z) at t0."""
    dt = t - t0
    if dt < 0 or dt > 1.4: return
    r = np.random.default_rng(seed)
    v = r.normal(0, 1, (n, 3)) * [speed, speed * 0.7, speed * 0.5]; v[:, 1] = np.abs(v[:, 1]) + 1
    P = np.asarray(pts) + v * dt * (1 - 0.3 * dt) + np.array([0, -4.9 * dt * dt, 0])
    sp, Z = cam.project(P)
    for i in range(n):
        if Z[i] < 0.3 or P[i, 1] < 0: continue
        q = cam.f * 0.07 / Z[i] * r.uniform(.5, 1.2); a = r.uniform(0, 6.28) + dt * r.uniform(-9, 9); c_, s_ = math.cos(a), math.sin(a)
        pts2 = [(sp[i, 0] + (px * c_ - py * s_) * q, sp[i, 1] + (px * s_ + py * c_) * q) for px, py in ((-1, -.6), (1, -.7), (.8, .7), (-1, .5))]
        cv2.fillConvexPoly(img, np.int32(pts2), tuple(float(x) for x in np.asarray(col) * r.uniform(.7, 1.05)), cv2.LINE_AA)
