"""voxkit.art3d - paper cut-outs for the 3D pop-up diorama: period crowd figures, trees, buildings, clouds, ground and sky."""
import math
import numpy as np
import cv2
from .core import *
from . import art


def _rim(rgb, m, px=5, col=(.93, .90, .82)):
    """Paper-cut look: a light torn rim around the shape."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    outer = cv2.dilate(m, k); n = fbm(m.shape[0], m.shape[1], 40, 2, 3)
    outer = np.clip((cv2.GaussianBlur(outer, (0, 0), 1.5) - 0.4 - (n - .5) * .3) * 8, 0, 1)
    out = np.zeros(m.shape + (3,), np.float32) + np.float32(col)
    out = out * (1 - m[..., None]) + rgb * m[..., None]
    return rgba(out, outer)


def person(seed=0, kind=None, w=300, h=720):
    """1900s onlooker seen from behind: coat / long skirt and a hat, cut from dark paper."""
    r = np.random.default_rng(seed); kind = kind or ('man', 'woman', 'man', 'child')[seed % 4]
    m = np.zeros((h, w), np.float32); cx = w / 2
    def poly(pts): cv2.fillPoly(m, [np.int32([(cx + x * w, y * h) for x, y in pts])], 1.0, cv2.LINE_AA)
    top = 0.30 if kind == 'child' else 0.08
    sc = (1 - top) / 0.92
    Y = lambda v: top + (v - 0.08) * sc
    head_y, head_r = Y(0.17), 0.105 * w * (1.15 if kind == 'child' else 1)
    cv2.circle(m, (int(cx), int(head_y * h)), int(head_r), 1.0, -1, cv2.LINE_AA)
    poly([(-.06, Y(.2)), (.06, Y(.2)), (.07, Y(.27)), (-.07, Y(.27))])                                             # neck
    if kind == 'woman':
        poly([(-.25, Y(.27)), (.25, Y(.27)), (.2, Y(.48)), (-.2, Y(.48))])                                         # jacket
        poly([(-.2, Y(.46)), (.2, Y(.46)), (.42, 1), (-.42, 1)])                                                   # long skirt
        poly([(-.25, Y(.27)), (-.36, Y(.52)), (-.27, Y(.54)), (-.18, Y(.34))]); poly([(.25, Y(.27)), (.36, Y(.52)), (.27, Y(.54)), (.18, Y(.34))])
        cv2.ellipse(m, (int(cx), int((head_y - 0.035) * h)), (int(w * .30), int(h * .028)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)   # wide hat
        cv2.ellipse(m, (int(cx), int((head_y - 0.06) * h)), (int(w * .14), int(h * .04)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    else:
        poly([(-.27, Y(.27)), (.27, Y(.27)), (.25, Y(.62)), (-.25, Y(.62))])                                       # coat
        poly([(-.27, Y(.27)), (-.37, Y(.58)), (-.28, Y(.6)), (-.2, Y(.36))]); poly([(.27, Y(.27)), (.37, Y(.58)), (.28, Y(.6)), (.2, Y(.36))])
        poly([(-.22, Y(.6)), (-.03, Y(.6)), (-.05, 1), (-.2, 1)]); poly([(.22, Y(.6)), (.03, Y(.6)), (.05, 1), (.2, 1)])       # legs
        hat = seed % 3
        if hat == 0:                                                                                                # bowler
            cv2.ellipse(m, (int(cx), int((head_y - 0.045) * h)), (int(w * .17), int(h * .014)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
            cv2.ellipse(m, (int(cx), int((head_y - 0.05) * h)), (int(w * .115), int(h * .05)), 0, 180, 360, 1.0, -1, cv2.LINE_AA)
        elif hat == 1:                                                                                              # top hat
            cv2.ellipse(m, (int(cx), int((head_y - 0.045) * h)), (int(w * .18), int(h * .013)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
            poly([(-.1, head_y - .05), (.1, head_y - .05), (.105, head_y - .13), (-.105, head_y - .13)])
        else:                                                                                                       # flat cap
            cv2.ellipse(m, (int(cx), int((head_y - 0.04) * h)), (int(w * .14), int(h * .03)), 0, 180, 360, 1.0, -1, cv2.LINE_AA)
    cols = [(.16, .13, .11), (.20, .15, .12), (.12, .14, .19), (.24, .12, .10), (.14, .17, .13), (.27, .21, .15)]
    rgb = paper(h, w, np.float32(cols[int(r.integers(len(cols)))]), seed, 0.08, 0.25)
    rgb *= np.linspace(1.25, 0.8, h, dtype=np.float32)[:, None, None]
    return _rim(np.clip(rgb, 0, 1), m, 4)


def tree(seed=0, w=520, h=820):
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.float32); rgb = np.zeros((h, w, 3), np.float32)
    trunk = paper(h, w, np.float32([.30, .21, .14]), seed, .06, .2); leaf = paper(h, w, np.float32([.22, .33, .20]) * r.uniform(.8, 1.15), seed + 1, .07, .25)
    tm = np.zeros((h, w), np.float32); cv2.fillPoly(tm, [np.int32([(w * .45, h), (w * .47, h * .4), (w * .53, h * .4), (w * .56, h)])], 1.0, cv2.LINE_AA)
    lm = np.zeros((h, w), np.float32)
    for i in range(9):
        cv2.circle(lm, (int(w * r.uniform(.25, .75)), int(h * r.uniform(.14, .46))), int(w * r.uniform(.16, .25)), 1.0, -1, cv2.LINE_AA)
    rgb = trunk * tm[..., None]; rgb = rgb * (1 - lm[..., None]) + leaf * lm[..., None]
    return _rim(rgb, np.maximum(tm, lm), 5)


def facade(w=1600, h=900, sign=None, seed=0):
    """Brick zoo house with arched openings and a cornice."""
    rgb = paper(h, w, np.float32([.52, .30, .22]), seed, .05, .18)
    for y in range(0, h, 26):
        cv2.line(rgb, (0, y), (w, y), (.36, .2, .15), 2)
        for x in range((y // 26 % 2) * 30, w, 60): cv2.line(rgb, (x, y), (x, y + 26), (.36, .2, .15), 2)
    m = np.ones((h, w), np.float32)
    cv2.rectangle(rgb, (0, 0), (w, int(h * .12)), (.80, .74, .62), -1); cv2.rectangle(rgb, (0, int(h * .12)), (w, int(h * .15)), (.3, .22, .16), -1)
    for i in range(5):
        cx = int(w * (.1 + i * .2)); aw, at, ab = int(w * .065), int(h * .32), h
        cv2.rectangle(rgb, (cx - aw, at), (cx + aw, ab), (.07, .06, .06), -1); cv2.ellipse(rgb, (cx, at), (aw, aw), 0, 180, 360, (.07, .06, .06), -1, cv2.LINE_AA)
        cv2.ellipse(rgb, (cx, at), (aw + 12, aw + 12), 0, 180, 360, (.82, .76, .64), 10, cv2.LINE_AA)
    if sign is not None:
        k = (w * .5) / sign.shape[1]; sgn = cv2.resize(sign, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        art.paste(rgba(rgb, m), sgn, 0, 0)
    return rgba(rgb, torn(h, w, 5, 1, seed + 2, sides='tlr'))


def cloud(seed=0, w=900, h=360):
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.float32)
    for i in range(8): cv2.ellipse(m, (int(w * r.uniform(.2, .8)), int(h * r.uniform(.4, .7))), (int(w * r.uniform(.12, .22)), int(h * r.uniform(.18, .32))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    cv2.rectangle(m, (int(w * .12), int(h * .62)), (int(w * .88), int(h * .8)), 1.0, -1)
    return _rim(paper(h, w, np.float32([.93, .89, .80]), seed, .03, .08), m, 3, (.98, .96, .9))


def ground_tex(s=1024, col=(.70, .60, .44), seed=0):
    """Tileable paving of paper slabs."""
    rgb = paper(s, s, np.float32(col), seed, .05, .12)
    n = 8; st = s // n
    for i in range(n + 1):
        cv2.line(rgb, (0, i * st), (s, i * st), tuple(float(v) for v in np.float32(col) * .62), 4)
        for j in range(n):
            x = j * st + (st // 2 if i % 2 else 0); cv2.line(rgb, (x, i * st), (x, i * st + st), tuple(float(v) for v in np.float32(col) * .62), 4)
    r = np.random.default_rng(seed)
    for i in range(n):
        for j in range(n):
            if r.random() < .3: rgb[i * st + 4:(i + 1) * st - 2, j * st + 4:(j + 1) * st - 2] *= r.uniform(.86, 1.08)
    return np.clip(rgb, 0, 1)


def sky(top=(.36, .50, .58), bot=(.93, .80, .58), seed=0):
    k = np.linspace(0, 1, H, dtype=np.float32)[:, None, None] ** 0.8
    img = np.float32(top) * (1 - k) + np.float32(bot) * k
    img = img * (0.94 + 0.12 * fbm(H, W, 6, 4, seed))[..., None]
    ht = 1 - 0.10 * halftone(np.broadcast_to(np.linspace(.9, .35, H, dtype=np.float32)[:, None], (H, W)).copy(), 9.0)
    return np.clip(img * ht[..., None], 0, 1).astype(np.float32)


def sign(txt, w=900, col=(.16, .13, .11), tcol=(.93, .88, .74), seed=0):
    t = text_sprite(txt, 150, np.float32(tcol), pad=10, squeeze=.84, distress=.2, seed=seed, tracking=6)
    th, tw = t.shape[:2]; px, py = 50, 30; h_, w_ = th + py * 2, tw + px * 2
    rgb = paper(h_, w_, np.float32(col), seed, .05, .15); a = t[..., 3:4]
    rgb[py:py + th, px:px + tw] = rgb[py:py + th, px:px + tw] * (1 - a) + t[..., :3] * a
    cv2.rectangle(rgb, (10, 10), (w_ - 11, h_ - 11), tuple(float(v) for v in tcol), 5)
    out = rgba(rgb, torn(h_, w_, 4, 1, seed + 1)); k = w / w_
    return cv2.resize(out, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)


def pole(w=60, h=1400):
    m = np.zeros((h, w), np.float32); cv2.rectangle(m, (w // 2 - 9, 30), (w // 2 + 9, h), 1.0, -1); cv2.circle(m, (w // 2, 26), 22, 1.0, -1, cv2.LINE_AA)
    return rgba(paper(h, w, np.float32([.80, .74, .62]), 5, .04, .1), m)


def bars(w=1000, h=700, n=11, seed=0):
    """Cage front: vertical iron bars with top and bottom rails (transparent between)."""
    rgb = paper(h, w, np.float32([.13, .13, .15]), seed, .06, .2); a = np.zeros((h, w), np.float32); bw = int(w / n * .2)
    for i in range(n + 1):
        cx = int(i * (w - bw) / n + bw / 2); cv2.rectangle(a, (cx - bw // 2, 0), (cx + bw // 2, h), 1.0, -1)
        hl = np.linspace(0, 1, bw, dtype=np.float32); rgb[:, cx - bw // 2:cx - bw // 2 + bw] *= (0.7 + 0.9 * np.exp(-((hl - .3) / .2) ** 2))[None, :, None]
    for y0, y1 in ((0, int(h * .05)), (int(h * .93), h)):
        cv2.rectangle(a, (0, y0), (w, y1), 1.0, -1); cv2.rectangle(rgb, (0, y0), (w, y1), (.2, .2, .23), -1)
    return rgba(np.clip(rgb, 0, 1), a)


def wall(w=1000, h=700, col=(.24, .20, .17), seed=0):
    rgb = paper(h, w, np.float32(col), seed, .06, .25) * np.linspace(.7, 1.1, h, dtype=np.float32)[:, None, None]
    return rgba(np.clip(rgb, 0, 1), np.ones((h, w), np.float32))
