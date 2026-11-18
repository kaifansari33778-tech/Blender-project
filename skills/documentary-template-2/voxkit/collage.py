"""voxkit.collage - "Documentary Template 2": full-frame layered photo collage.
One photograph per phrase fills the frame, cut into depth layers (sky / subject / foreground) and shot with a slow push-in so the
layers slide; big words sit between the layers; narration is typed a few words at a time; key phrases pop in a highlight box;
scenes change with a zoom-through or by tearing the old frame in two."""
import math
import numpy as np, cv2
from .core import *
from . import art
from .cine import pin
YEL = np.float32([.93, .80, .16]); INKC = np.float32([.10, .09, .09]); CREAM = np.float32([.93, .90, .82])


def grade(img, tone=(1.0, .97, .90), sat=.12, gain=1.0, seed=0, con=1.15):
    """Print look: mostly monochrome in one tone, a little halftone and paper grain."""
    lum = img.mean(2, keepdims=True); g = img * sat + lum * np.float32(tone) * (1 - sat); g = np.clip((g - .5) * con + .5, 0, 1) * gain
    h, w = g.shape[:2]; return np.clip(g * (0.90 + 0.14 * fbm(h, w, 6, 3, seed))[..., None] * (1 - .10 * halftone(lum[..., 0], 3.0))[..., None], 0, 1)


def nonsky(img, top=.10, bot=.55, pf=.30):
    """Alpha of everything that is not sky. Rows above `top` are sky for sure, below `bot` subject for sure, below `pf` probably subject."""
    h, w = img.shape[:2]; k = 400 / w; sm = cv2.resize((img * 255).astype(np.uint8)[..., ::-1], (400, int(h * k))); m = np.full(sm.shape[:2], cv2.GC_PR_BGD, np.uint8)
    m[int(sm.shape[0] * pf):] = cv2.GC_PR_FGD; m[:int(sm.shape[0] * top)] = cv2.GC_BGD; m[int(sm.shape[0] * bot):] = cv2.GC_FGD
    cv2.grabCut(sm, m, None, np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_MASK)
    a = ((m == 1) | (m == 3)).astype(np.float32); return np.clip((cv2.GaussianBlur(cv2.resize(a, (w, h)), (0, 0), 2.0) - .45) * 6, 0, 1)


def subject(img, rect=(.14, .10, .72, .86)):
    """Alpha of the main subject inside a rectangle (fractions x, y, w, h)."""
    h, w = img.shape[:2]; k = 400 / w; sm = cv2.resize((img * 255).astype(np.uint8)[..., ::-1], (400, int(h * k))); hh, ww = sm.shape[:2]; m = np.zeros((hh, ww), np.uint8)
    cv2.grabCut(sm, m, (int(ww * rect[0]), int(hh * rect[1]), int(ww * rect[2]), int(hh * rect[3])), np.zeros((1, 65)), np.zeros((1, 65)), 5, cv2.GC_INIT_WITH_RECT)
    a = cv2.morphologyEx(((m == 1) | (m == 3)).astype(np.float32), cv2.MORPH_OPEN, np.ones((5, 5))); return np.clip((cv2.GaussianBlur(cv2.resize(a, (w, h)), (0, 0), 2.5) - .45) * 6, 0, 1)


def layer(img, a, rim=4):
    """RGBA layer with a thin paper-white cut edge."""
    s = np.dstack([img, a]).astype(np.float32)
    if rim:
        e = cv2.dilate(a, np.ones((rim * 2 + 1, rim * 2 + 1))) - a; s[..., :3] = s[..., :3] * (1 - e[..., None]) + CREAM * e[..., None]; s[..., 3] = np.maximum(a, np.clip(e * 2, 0, 1))
    return s


def band(img, y0, jag=18, seed=0, y1=1.0):
    """The lower part of a photo as a nearer layer with a torn top edge."""
    h, w = img.shape[:2]; sub = img[int(h * y0):int(h * y1)]; hh = sub.shape[0]; top = (jag * (1 + fbm(1, w, 40, 3, seed)[0] * 2 + .5 * np.sin(np.arange(w) / 37.0))).astype(np.float32)
    return layer(sub, np.clip((np.arange(hh)[:, None] - top[None, :]) / 3, 0, 1), 3)


def sky_plate(top, bot, seed=0, moon=False, w=1200, h=1500, stars=0):
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]; rgb = (np.float32(top) * (1 - g) + np.float32(bot) * g) * np.ones((1, w, 1), np.float32)
    rgb = rgb * (0.85 + 0.3 * fbm(h, w, 5, 4, seed))[..., None]; r = np.random.default_rng(seed)
    for i in range(stars): cv2.circle(rgb, (int(r.integers(w)), int(r.integers(int(h * .7)))), int(r.integers(1, 3)), tuple(float(v) for v in np.float32([1, .95, .85]) * r.uniform(.4, .9)), -1, cv2.LINE_AA)
    if moon: cv2.circle(rgb, (int(w * .68), int(h * .30)), 70, (.95, .93, .82), -1, cv2.LINE_AA); cv2.circle(rgb, (int(w * .70), int(h * .29)), 62, tuple(float(v) for v in np.float32(top) * 1.1), -1, cv2.LINE_AA)
    return np.dstack([np.clip(rgb, 0, 1), np.ones((h, w), np.float32)])


def big_text(txt, col, size=420, seed=1): return text_sprite(txt, size, np.float32(col), pad=10, squeeze=.82, distress=.25, seed=seed)
_BX = {}
def box(txt, bg=YEL, fg=INKC, size=150, seed=0):
    key = (txt, tuple(np.float32(bg)), size)
    if key not in _BX:
        t = text_sprite(txt, size, np.float32(fg), pad=6, squeeze=.86, distress=.1, seed=seed); h, w = t.shape[:2]; px, py = int(size * .34), int(size * .2)
        s = rgba(paper(h + 2 * py, w + 2 * px, np.float32(bg), seed, .04, .12), torn(h + 2 * py, w + 2 * px, 4, 2, seed + 2)); art.paste(s, t, px, py); _BX[key] = s
    return _BX[key]


def merge_words(words, groups):
    """Join runs of spoken words into one caption token, e.g. {('unnees','sau','chauraasi'): '1984'}."""
    out = []; i = 0
    while i < len(words):
        for g, rep in groups.items():
            if tuple(w[0] for w in words[i:i + len(g)]) == g: out.append([rep, words[i][1], words[i + len(g) - 1][2]]); i += len(g); break
        else: out.append(list(words[i])); i += 1
    return out


def typed(C, cam, t, words, t0, t1, sy=.085, n=4):
    """Narration typed word by word in a small cream label, n words at a time; uses the words spoken in [t0, t1)."""
    seg_ = [w for w in words if t0 - .01 <= w[1] < t1]; ws = [w for w in seg_ if w[1] <= t + .03]
    if not ws or t > seg_[-1][2] + .7: return
    ws = ws[(len(ws) - 1) // n * n:]; txt = ' '.join(w[0] for w in ws); txt = txt[0].upper() + txt[1:]
    s = box(txt, CREAM, INKC, 96, 1); C.append(pin(s, cam, .5, sy, min(.92, s.shape[1] * .00072)))


def hl(C, cam, t, txt, t0, t1, sy=.80, wfr=.7, bg=YEL):
    """A key phrase popping in inside a highlight box."""
    if t < t0 - .1 or t > t1: return
    k = back(seg(t, t0 - .1, t0 + .12), 2.2); C.append(pin(box(txt, bg), cam, .5, sy, wfr * k, alpha=min(1, k * 2)))


def rip(new, old, k, ang=0.0, seed=0, gap=1.0):
    """Tear the old frame in two along a jagged line (ang: 0 = vertical tear, pi/2 = horizontal, else diagonal); the halves slide apart over the new frame."""
    k = eio(k, 2.2); nx, ny = math.cos(ang), math.sin(ang); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); u = -(xx - W / 2) * ny + (yy - H / 2) * nx
    jag = 30 * (4 * np.abs(((u / 170 + seed * .37) % 1) - .5) - 1) + 22 * np.sin(u / 47.0 + seed) + 10 * np.sin(u / 13.0 + seed * 2)
    d = (xx - W / 2) * nx + (yy - H / 2) * ny + jag; ext = (abs(nx) * W + abs(ny) * H) * .56 * gap; out = new.copy()
    sh = np.zeros((H, W), np.float32); pieces = []
    for sgn in (-1, 1):
        m = np.clip(sgn * d / 2 + .5, 0, 1); rim = np.clip(1 - np.abs(sgn * d - 9) / 9, 0, 1) * m                      # paper-white torn edge
        pc = old * (1 - rim[..., None]) + CREAM * (0.96 + .04 * np.sin(u / 5.0))[..., None] * rim[..., None]
        M = np.float32([[1, 0, sgn * nx * k * ext], [0, 1, sgn * ny * k * ext]]); rot = sgn * k * .035
        if rot: R = cv2.getRotationMatrix2D((W / 2, H / 2), math.degrees(rot), 1.0); R[:, 2] += M[:, 2]; M = R.astype(np.float32)
        pcw = cv2.warpAffine(pc, M, (W, H), flags=cv2.INTER_LINEAR); mw = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR); pieces.append((pcw, mw)); sh = np.maximum(sh, mw)
    out *= (1 - .55 * np.clip(cv2.GaussianBlur(sh, (0, 0), 26) * 1.3 - sh * 0, 0, 1) * (1 - sh))[..., None]                # shadow the pieces cast on the new scene
    for pcw, mw in pieces: out = out * (1 - mw[..., None]) + pcw * mw[..., None]
    return out
