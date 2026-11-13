"""voxkit.core - 2.5D paper-diorama compositor: textures, cutouts, camera, motion blur, film post."""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
PAPER = np.array([226, 205, 168], np.float32) / 255
PAPER_LT = np.array([240, 228, 200], np.float32) / 255
ORANGE = np.array([206, 88, 12], np.float32) / 255
INK = np.array([34, 27, 22], np.float32) / 255
FONT_BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'


# ------------------------------------------------------------------ easing
def cl(x): return max(0.0, min(1.0, x))
def seg(t, a, b): return cl((t - a) / (b - a))
def smooth(x): x = cl(x); return x * x * (3 - 2 * x)
def eout(x, p=3): x = cl(x); return 1 - (1 - x) ** p
def ein(x, p=3): x = cl(x); return x ** p
def eio(x, p=3): x = cl(x); return 0.5 * (2 * x) ** p if x < 0.5 else 1 - 0.5 * (2 - 2 * x) ** p
def back(x, s=1.9): x = cl(x) - 1; return 1 + x * x * ((s + 1) * x + s)
def lerp(a, b, k): return a + (b - a) * k
def shake(t, t0, amp, dur=0.45, f=31):
    if t < t0 or t > t0 + dur: return 0.0, 0.0
    k = (1 - (t - t0) / dur) ** 2 * amp
    return k * math.sin((t - t0) * f * 2.1 + 1), k * math.cos((t - t0) * f * 1.7)


# ------------------------------------------------------------------ noise / textures
def fbm(h, w, base=8, octs=5, seed=0, fall=0.55):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octs):
        n = base * 2 ** o
        g = r.random((max(2, int(n * h / max(h, w)) + 2), max(2, int(n * w / max(h, w)) + 2))).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC); tot += amp; amp *= fall
    return out / tot


def paper(h, w, col=PAPER, seed=0, grain=0.05, blotch=0.14):
    r = np.random.default_rng(seed + 99)
    lum = 1 + (fbm(h, w, 4, 5, seed) - 0.5) * blotch * 2 + r.normal(0, grain, (h, w)).astype(np.float32)
    fib = np.zeros((h, w), np.float32)
    for _ in range(int(h * w / 9000)):
        x, y = r.integers(0, w), r.integers(0, h); a = r.random() * 6.28; L = r.integers(8, 34)
        cv2.line(fib, (int(x), int(y)), (int(x + math.cos(a) * L), int(y + math.sin(a) * L)), float(r.choice([-1, 1])) * 0.07, 1, cv2.LINE_AA)
    return np.clip((lum + fib)[..., None] * col[None, None, :], 0, 1).astype(np.float32)


def torn(h, w, rough=10, margin=6, seed=0, sides='tblr'):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    big = np.float32(1e6)
    d = np.minimum.reduce([yy if 't' in sides else yy + big, (h - 1 - yy) if 'b' in sides else yy + big,
                           xx if 'l' in sides else xx + big, (w - 1 - xx) if 'r' in sides else xx + big])
    n = fbm(h, w, 40, 3, seed, 0.6) * 0.7 + fbm(h, w, 6, 2, seed + 1) * 0.6
    return np.clip((d - margin - n * rough) / 1.5, 0, 1).astype(np.float32)


def halftone(gray, cell=6.0, ang=45, gain=1.0):
    """gray: 0..1 luminance -> ink coverage 0..1 (round dots, rotated screen)."""
    h, w = gray.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(ang)
    u = (xx * math.cos(a) + yy * math.sin(a)) / cell; v = (-xx * math.sin(a) + yy * math.cos(a)) / cell
    du = u - np.floor(u) - 0.5; dv = v - np.floor(v) - 0.5
    dist = np.sqrt(du * du + dv * dv)
    dark = np.clip((1 - gray) * gain, 0, 1)
    rad = 0.78 * np.sqrt(dark)
    return np.clip((rad - dist) * cell / 1.4 + 0.5, 0, 1).astype(np.float32)


def rgba(rgb, a):
    return np.dstack([rgb, a]).astype(np.float32)


def ink_on_paper(ink, h=None, w=None, col=PAPER_LT, seed=0, inkcol=INK):
    h, w = ink.shape
    p = paper(h, w, col, seed, 0.035, 0.08)
    r = np.random.default_rng(seed)
    ink = ink * (0.86 + 0.14 * fbm(h, w, 30, 3, seed + 5))        # uneven letterpress coverage
    return p * (1 - ink[..., None]) + inkcol[None, None, :] * ink[..., None]


def cutout(gray, mask, cell=5.0, border=13, seed=0, gain=1.05):
    """Monochrome archival photo cutout: halftoned gray inside mask, rough white paper border."""
    h, w = gray.shape
    rgb = ink_on_paper(halftone(gray, cell, 45, gain), seed=seed)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (border * 2 + 1, border * 2 + 1))
    n = fbm(h, w, 50, 3, seed + 3)
    outer = cv2.dilate(mask, k)
    outer = np.clip((cv2.GaussianBlur(outer, (0, 0), 2.5) - 0.42 - (n - 0.5) * 0.35) * 9, 0, 1)
    white = paper(h, w, np.array([0.95, 0.92, 0.85], np.float32), seed + 7, 0.03, 0.06)
    m = cv2.GaussianBlur(mask, (0, 0), 0.8)[..., None]
    return rgba(rgb * m + white * (1 - m), outer)


def newsprint(h, w, seed=0, col=PAPER, dark=1.0, cols=3):
    """Aged newspaper sheet: headline bars, text columns as broken line strokes, halftone photo blocks. No letters."""
    r = np.random.default_rng(seed)
    ink = np.zeros((h, w), np.float32)
    m = int(w * 0.06); y = int(h * 0.04)
    cv2.rectangle(ink, (m, y), (w - m, y + int(h * 0.006)), 1, -1); y += int(h * 0.02)
    x = m
    while x < w - m - 30:                                  # masthead: heavy block "type"
        bw = int(r.integers(int(w * .03), int(w * .09)))
        cv2.rectangle(ink, (x, y), (min(x + bw, w - m), y + int(h * 0.045)), 0.95, -1); x += bw + int(w * .012)
    y += int(h * 0.06); cv2.rectangle(ink, (m, y), (w - m, y + int(h * 0.004)), 1, -1); y += int(h * 0.02)
    cw = (w - 2 * m) / cols; lh = max(5, int(h * 0.0085))
    for c in range(cols):
        x0 = int(m + c * cw + cw * 0.05); x1 = int(m + (c + 1) * cw - cw * 0.05); yy = y
        while yy < h - m:
            k = r.random()
            if k < 0.05 and yy < h - m - cw:              # halftone photo block
                bh = int(cw * r.uniform(.5, .9)); g = fbm(bh, x1 - x0, 3, 3, int(r.integers(1e6)))
                ink[yy:yy + bh, x0:x1] = np.maximum(ink[yy:yy + bh, x0:x1], halftone(g * 0.9, 4.0)[:h - yy]); yy += bh + lh * 2
            elif k < 0.12:                                 # sub headline
                cv2.rectangle(ink, (x0, yy), (int(x0 + (x1 - x0) * r.uniform(.5, .95)), yy + lh * 2), 0.9, -1); yy += lh * 4
            else:                                          # text line = broken strokes
                xx = x0; end = x1 if r.random() > 0.15 else int(x0 + (x1 - x0) * r.uniform(.3, .8))
                while xx < end:
                    ww = int(r.integers(lh, lh * 5))
                    cv2.rectangle(ink, (xx, yy), (min(xx + ww, end), yy + max(2, lh // 2)), float(r.uniform(.55, .85)), -1); xx += ww + max(2, lh // 2)
                yy += int(lh * 1.7)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.6)
    return ink_on_paper(ink * 0.85, col=col * dark, seed=seed)


def text_sprite(txt, size, col=INK, pad=20, squeeze=0.8, distress=0.5, seed=0, tracking=0):
    f = ImageFont.truetype(FONT_BLACK, size)
    l, t, r_, b = f.getbbox(txt)
    im = Image.new('L', (int(r_ - l + pad * 2 + tracking * len(txt)), b - t + pad * 2), 0)
    d = ImageDraw.Draw(im)
    if tracking:
        x = pad - l
        for ch in txt:
            d.text((x, pad - t), ch, 255, font=f); x += f.getlength(ch) + tracking
    else:
        d.text((pad - l, pad - t), txt, 255, font=f)
    a = np.asarray(im, np.float32) / 255
    a = cv2.resize(a, (int(a.shape[1] * squeeze), a.shape[0]), interpolation=cv2.INTER_AREA)
    h, w = a.shape
    n = fbm(h, w, 60, 3, seed, 0.7); n2 = fbm(h, w, 8, 2, seed + 1)
    a = a * np.clip(1.25 - distress * 1.6 * np.clip((n - 0.5) * 3 + (n2 - 0.45) * 2, 0, 1), 0, 1)
    return rgba(np.broadcast_to(col, (h, w, 3)), a.astype(np.float32))


_WG = {}
def wave(spr, t, amp=16.0, wl=300.0, speed=5.0, pin='l'):
    """Cloth ripple: displace + shade a sprite so it looks like a flag flowing in the wind."""
    h, w = spr.shape[:2]
    if (h, w) not in _WG: _WG[(h, w)] = np.mgrid[0:h, 0:w].astype(np.float32)
    yy, xx = _WG[(h, w)]
    k = (xx / w) ** 0.8 if pin == 'l' else np.float32(1.0)
    ph = xx / wl * 6.283 + yy / (wl * 3.1) * 6.283 - t * speed
    dy = amp * np.sin(ph) * k; dx = amp * 0.35 * np.cos(ph * 0.7 + 1) * k
    out = cv2.remap(spr, xx + dx, yy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    out[..., :3] *= (1 + 0.22 * np.cos(ph) * k)[..., None]
    return out


def with_alpha(spr, k):
    o = spr.copy(); o[..., 3] *= k; return o


# ------------------------------------------------------------------ compositor
class Cam:
    def __init__(s, x=0, y=0, z=1, r=0): s.x, s.y, s.z, s.r = x, y, z, r


def par(depth):
    return 1.0 / (1.0 + 0.32 * depth) if depth >= 0 else 1.0 - 0.45 * depth


class Frame:
    def __init__(s, cam, focus=0.0, dof=5.0):
        s.c = np.zeros((H, W, 3), np.float32); s.cam = cam; s.focus = focus; s.dof = dof

    def w2s(s, wx, wy, depth=0):
        c = s.cam; p = par(depth)
        dx, dy = (wx - c.x) * p * c.z, (wy - c.y) * p * c.z
        cr, sr = math.cos(-c.r), math.sin(-c.r)
        return W / 2 + dx * cr - dy * sr, H / 2 + dx * sr + dy * cr

    def M(s, spr, wx, wy, scale=1, rot=0, depth=0, anchor=(0.5, 0.5), sx=1, sy=1):
        h, w = spr.shape[:2]
        X, Y = s.w2s(wx, wy, depth)
        k = scale * s.cam.z * (par(depth) if depth < 0 else 1)
        a = rot - s.cam.r; ca, sa = math.cos(a), math.sin(a)
        ax, ay = anchor[0] * w, anchor[1] * h
        A = np.array([[ca * k * sx, -sa * k * sy], [sa * k * sx, ca * k * sy]], np.float32)
        tr = np.array([X, Y], np.float32) - A @ np.array([ax, ay], np.float32)
        return np.hstack([A, tr[:, None]]).astype(np.float32)

    def put(s, spr, wx, wy, scale=1, rot=0, depth=0, alpha=1.0, anchor=(0.5, 0.5), shadow=0.5, sh_off=(14, 22), sx=1, sy=1,
            blur=None, tint=None, wrap=False):
        if alpha <= 0.003: return
        M = s.M(spr, wx, wy, scale, rot, depth, anchor, sx, sy)
        if not wrap:                                       # cull offscreen
            h, w = spr.shape[:2]
            pts = (M[:, :2] @ np.array([[0, w, w, 0], [0, 0, h, h]], np.float32)) + M[:, 2:3]
            if pts[0].max() < -60 or pts[0].min() > W + 60 or pts[1].max() < -60 or pts[1].min() > H + 60: return
        sig = s.dof * abs(depth - s.focus) * math.sqrt(max(s.cam.z, .2)) if blur is None else blur
        z = s.cam.z
        if wrap:
            x0, y0, x1, y1 = 0, 0, W, H
        else:
            pad = int(3 * sig + (abs(sh_off[0]) + abs(sh_off[1]) + 30) * z * (1 if shadow else 0) + 4)
            x0, y0 = max(0, int(pts[0].min()) - pad), max(0, int(pts[1].min()) - pad)
            x1, y1 = min(W, int(pts[0].max()) + pad + 1), min(H, int(pts[1].max()) + pad + 1)
            if x1 - x0 < 2 or y1 - y0 < 2: return
            M = M.copy(); M[0, 2] -= x0; M[1, 2] -= y0
        pm = spr.copy(); pm[..., :3] *= pm[..., 3:4]
        det = abs(M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0])
        if det < 0.2 and not wrap:                              # heavy minification: prefilter to avoid shimmer
            pm = cv2.GaussianBlur(pm, (0, 0), min(6.0, 0.45 / math.sqrt(max(det, 1e-4))))
        lay = cv2.warpAffine(pm, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP if wrap else cv2.BORDER_CONSTANT, borderValue=0)
        if sig > 0.6: lay = cv2.GaussianBlur(lay, (0, 0), sig)
        reg = s.c[y0:y1, x0:x1]
        a = lay[..., 3:4] * alpha
        if shadow and not wrap:
            Ms = np.float32([[1, 0, sh_off[0] * z], [0, 1, sh_off[1] * z]])
            sh = cv2.warpAffine(lay[..., 3], Ms, (x1 - x0, y1 - y0))
            sh = cv2.GaussianBlur(sh, (0, 0), 9 * z + sig)
            reg *= (1 - shadow * alpha * sh)[..., None]
        rgb = lay[..., :3] * alpha
        if tint is not None: rgb = rgb * tint
        reg[:] = reg * (1 - a) + rgb

    def quad(s, pts, col, alpha=1.0):
        """Filled screen-space polygon (particles)."""
        ov = s.c.copy(); cv2.fillConvexPoly(ov, np.int32(pts), tuple(float(x) for x in col), cv2.LINE_AA)
        s.c = ov if alpha >= 1 else cv2.addWeighted(ov, alpha, s.c, 1 - alpha, 0)


class Burst:
    """Paper scraps + dust puff emitted at world point."""
    def __init__(s, t0, wx, wy, n=40, speed=900, seed=0, up=0.6, cols=(PAPER, PAPER_LT), size=16, grav=1700, puff=1.0, spread=1.0):
        r = np.random.default_rng(seed); s.t0 = t0; s.o = (wx, wy); s.grav = grav; s.puff = puff
        ang = r.uniform(0, 2 * math.pi, n); sp = r.uniform(.25, 1, n) * speed
        s.v = np.stack([np.cos(ang) * sp * spread, np.sin(ang) * sp - up * speed * r.uniform(.2, 1, n)], 1)
        s.sz = r.uniform(.4, 1, n) * size; s.rot = r.uniform(0, 6.28, n); s.w = r.uniform(-14, 14, n)
        s.col = [cols[i % len(cols)] * r.uniform(.7, 1.05) for i in range(n)]; s.life = r.uniform(.5, 1.3, n)
        s.pa = r.uniform(0, 6.28, 9); s.pr = r.uniform(.5, 1, 9)

    def draw(s, fr, t):
        dt = t - s.t0
        if dt < 0 or dt > 1.6: return
        z = fr.cam.z
        if s.puff and dt < 1.1:
            lay = np.zeros((H, W), np.float32)
            for a, rr in zip(s.pa, s.pr):
                d = 260 * rr * eout(dt / 0.9) * s.puff
                X, Y = fr.w2s(s.o[0] + math.cos(a) * d, s.o[1] + math.sin(a) * d * 0.45 - 40 * dt)
                cv2.circle(lay, (int(X), int(Y)), int((60 + 190 * eout(dt / 0.8)) * z * rr * s.puff), 1.0, -1)
            lay = cv2.GaussianBlur(cv2.resize(lay, (W // 4, H // 4)), (0, 0), 14 * z)
            lay = cv2.resize(lay, (W, H)) * 0.5 * (1 - dt / 1.1) ** 1.5
            fr.c = fr.c * (1 - lay[..., None]) + (PAPER * 0.95)[None, None, :] * lay[..., None]
        for i in range(len(s.sz)):
            if dt > s.life[i]: continue
            x = s.o[0] + s.v[i, 0] * dt * (1 - 0.3 * dt); y = s.o[1] + s.v[i, 1] * dt + 0.5 * s.grav * dt * dt
            X, Y = fr.w2s(x, y); a = s.rot[i] + s.w[i] * dt; q = s.sz[i] * z
            c, sn = math.cos(a), math.sin(a); fl = abs(math.cos(a * 1.7)) * .8 + .2
            pts = [(X + (px * c - py * fl * sn) * q, Y + (px * sn + py * fl * c) * q) for px, py in ((-1, -.7), (1, -.6), (.9, .7), (-1, .6))]
            fr.quad(pts, s.col[i], cl((s.life[i] - dt) * 5))


# ------------------------------------------------------------------ blur + film post
def dir_blur(img, vx, vy):
    L = math.hypot(vx, vy)
    if L < 3: return img
    L = int(min(L, 420)); a = math.atan2(vy, vx)
    if abs(math.sin(a)) < 0.05: return cv2.blur(img, (L | 1, 1))
    if abs(math.cos(a)) < 0.05: return cv2.blur(img, (1, L | 1))
    k = np.zeros((L | 1, L | 1), np.float32); c = L // 2
    cv2.line(k, (int(c - math.cos(a) * c), int(c - math.sin(a) * c)), (int(c + math.cos(a) * c), int(c + math.sin(a) * c)), 1.0, 1)
    return cv2.filter2D(img, -1, k / k.sum())


def zoom_blur(img, amt, n=10):
    if abs(amt) < 0.006: return img
    acc = np.zeros_like(img)
    for i in range(n):
        k = 1 + amt * (i / (n - 1) - 0.5)
        M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
        acc += cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return acc / n


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r2 = ((_xx - W / 2) / (W * 0.78)) ** 2 + ((_yy - H * 0.47) / (H * 0.62)) ** 2
_VIG = np.clip(1.12 - _r2 * 0.72, 0.25, 1.12)[..., None]
_TS = np.clip((np.abs(_yy - H * 0.5) / (H * 0.5) - 0.80) / 0.20, 0, 1)[..., None]
_WARM = np.array([1.08, 0.97, 0.80], np.float32)
_grng = np.random.default_rng(11)
_GRAIN = [cv2.resize(_grng.normal(0, 1, (H // 2 + 2, W // 2 + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None] for _ in range(6)]


def post(img, f, tilt=1.0, expo=1.0):
    if tilt > 0:
        b = cv2.GaussianBlur(img, (0, 0), 7)
        img = img * (1 - _TS * tilt) + b * (_TS * tilt)
    glow = cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4)), (0, 0), 12)
    img = img + cv2.resize(glow, (W, H)) * 0.10                       # tungsten bloom
    img = img * _VIG * _WARM * expo * (1 + 0.018 * math.sin(f * 1.9) + 0.012 * math.sin(f * 0.53))
    img = img / (1 + 0.12 * img) * 1.10                                # soft shoulder
    lum = img.mean(2, keepdims=True)
    img = img + _GRAIN[f % 6] * 0.035 * (0.35 + lum)
    if f % 7 == 3:                                                     # dust speck
        r = np.random.default_rng(f)
        for _ in range(int(r.integers(1, 4))):
            cv2.circle(img, (int(r.integers(0, W)), int(r.integers(0, H))), int(r.integers(1, 3)), (.05, .04, .03), -1, cv2.LINE_AA)
    return np.clip(img, 0, 1)
