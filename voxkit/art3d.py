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


# ------------------------------------------------------------------ zoo life
def _blob(w, h, parts, col, seed=0, rim=4, shade=True):
    """parts: list of ('e', cx, cy, rx, ry) ellipses or ('p', [(x,y)...]) polygons in 0..1 units -> rimmed paper cut-out."""
    m = np.zeros((h, w), np.float32)
    for p in parts:
        if p[0] == 'e': cv2.ellipse(m, (int(p[1] * w), int(p[2] * h)), (int(p[3] * w), int(p[4] * h)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        else: cv2.fillPoly(m, [np.int32([(x * w, y * h) for x, y in p[1]])], 1.0, cv2.LINE_AA)
    rgb = paper(h, w, np.float32(col), seed, .07, .25)
    if shade: rgb = rgb * np.linspace(1.2, .8, h, dtype=np.float32)[:, None, None]
    return _rim(np.clip(rgb, 0, 1), m, rim), m


def orangutan(w=520, h=560):
    spr, m = _blob(w, h, [('e', .5, .62, .26, .30), ('e', .5, .25, .17, .17), ('p', [(.3, .45), (.08, .78), (.02, .98), (.16, .98), (.22, .8), (.38, .6)]), ('p', [(.7, .45), (.92, .78), (.98, .98), (.84, .98), (.78, .8), (.62, .6)]),
                           ('e', .34, .92, .12, .07), ('e', .66, .92, .12, .07)], (.62, .30, .12), 31)
    face = np.zeros((h, w), np.float32); cv2.ellipse(face, (int(w * .5), int(h * .27)), (int(w * .10), int(h * .11)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    spr[..., :3] = spr[..., :3] * (1 - face[..., None]) + np.float32([.30, .20, .14]) * face[..., None]
    for ex in (.46, .54): cv2.circle(spr, (int(w * ex), int(h * .245)), 5, (.05, .04, .04, 1), -1, cv2.LINE_AA)
    cv2.ellipse(spr, (int(w * .5), int(h * .31)), (int(w * .045), int(h * .02)), 0, 0, 180, (.12, .08, .06, 1), 3, cv2.LINE_AA)
    return spr


def monkey(seed=0, w=300, h=420):
    spr, m = _blob(w, h, [('e', .5, .55, .2, .24), ('e', .5, .22, .16, .15), ('e', .34, .2, .06, .06), ('e', .66, .2, .06, .06), ('p', [(.36, .42), (.14, .1), (.2, .06), (.44, .36)]), ('p', [(.64, .42), (.86, .1), (.8, .06), (.56, .36)]),
                           ('p', [(.4, .72), (.3, .98), (.42, .98), (.48, .76)]), ('p', [(.6, .72), (.7, .98), (.58, .98), (.52, .76)]), ('p', [(.62, .7), (.9, .78), (.96, .55), (.9, .55), (.86, .7), (.64, .64)])], ((.30, .22, .15), (.36, .26, .16), (.24, .20, .17))[seed % 3], 40 + seed)
    face = np.zeros((h, w), np.float32); cv2.ellipse(face, (int(w * .5), int(h * .24)), (int(w * .09), int(h * .085)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    spr[..., :3] = spr[..., :3] * (1 - face[..., None]) + np.float32([.78, .62, .46]) * face[..., None]
    for ex in (.465, .535): cv2.circle(spr, (int(w * ex), int(h * .225)), 4, (.05, .04, .04, 1), -1, cv2.LINE_AA)
    return spr


def parrot(w=200, h=360):
    spr, m = _blob(w, h, [('e', .5, .4, .2, .22), ('e', .5, .17, .15, .1), ('p', [(.38, .55), (.62, .55), (.56, 1), (.44, 1)])], (.80, .16, .12), 50, 3)
    cv2.fillPoly(spr, [np.int32([(w * .62, h * .15), (w * .82, h * .2), (w * .62, h * .24)])], (.95, .80, .2, 1), cv2.LINE_AA)
    cv2.circle(spr, (int(w * .54), int(h * .15)), 5, (.05, .05, .05, 1), -1, cv2.LINE_AA)
    wing = np.zeros((h, w), np.float32); cv2.ellipse(wing, (int(w * .44), int(h * .45)), (int(w * .1), int(h * .16)), 15, 0, 360, 1.0, -1, cv2.LINE_AA)
    spr[..., :3] = spr[..., :3] * (1 - wing[..., None]) + np.float32([.15, .35, .62]) * wing[..., None]
    return spr


def lamp(w=160, h=900):
    spr, m = _blob(w, h, [('p', [(.44, .16), (.56, .16), (.6, 1), (.4, 1)]), ('p', [(.3, .97), (.7, .97), (.74, 1), (.26, 1)]), ('p', [(.2, .16), (.8, .16), (.7, .12), (.3, .12)])], (.12, .13, .14), 60, 3, False)
    g = np.zeros((h, w), np.float32); cv2.ellipse(g, (w // 2, int(h * .07)), (int(w * .26), int(h * .055)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    spr[..., :3] = spr[..., :3] * (1 - g[..., None]) + np.float32([1., .93, .68]) * g[..., None]; spr[..., 3] = np.maximum(spr[..., 3], g)
    return spr


def bench(w=520, h=260):
    spr, m = _blob(w, h, [('p', [(0, .1), (1, .1), (1, .22), (0, .22)]), ('p', [(0, .3), (1, .3), (1, .42), (0, .42)]), ('p', [(0, .55), (1, .55), (1, .66), (0, .66)]),
                          ('p', [(.06, .1), (.12, .1), (.12, 1), (.06, 1)]), ('p', [(.88, .1), (.94, .1), (.94, 1), (.88, 1)])], (.20, .30, .22), 61, 3)
    return spr


def gate(txt='ZOOLOGICAL PARK', w=1600, h=900):
    """Entrance arch: two stone pillars and an iron sign arch (open in the middle)."""
    m = np.zeros((h, w), np.float32); rgb = paper(h, w, np.float32([.60, .55, .46]), 62, .05, .15)
    for x0, x1 in ((0, .12), (.88, 1)):
        cv2.rectangle(m, (int(w * x0), int(h * .2)), (int(w * x1), h), 1.0, -1); cv2.rectangle(m, (int(w * (x0 - .01)), int(h * .16)), (int(w * (x1 + .01)), int(h * .22)), 1.0, -1)
        cv2.circle(m, (int(w * (x0 + x1) / 2), int(h * .12)), int(w * .035), 1.0, -1, cv2.LINE_AA)
    iron = np.zeros((h, w), np.float32)
    cv2.ellipse(iron, (w // 2, int(h * .42)), (int(w * .4), int(h * .34)), 0, 180, 360, 1.0, 26, cv2.LINE_AA); cv2.ellipse(iron, (w // 2, int(h * .42)), (int(w * .4), int(h * .2)), 0, 180, 360, 1.0, 14, cv2.LINE_AA)
    t = text_sprite(txt, 110, np.float32([.10, .10, .11]), pad=4, squeeze=.9, distress=.1, seed=2, tracking=10)
    k = (w * .56) / t.shape[1]; t = cv2.resize(t, None, fx=k, fy=k, interpolation=cv2.INTER_AREA); th, tw = t.shape[:2]; tx, ty = (w - tw) // 2, int(h * .19) - th // 2
    rgb = rgb * (1 - iron[..., None]) + np.float32([.10, .10, .11]) * iron[..., None]; m = np.maximum(m, iron)
    plate = np.zeros((h, w), np.float32); cv2.rectangle(plate, (tx - 20, ty - 10), (tx + tw + 20, ty + th + 10), 1.0, -1)
    rgb = rgb * (1 - plate[..., None]) + np.float32([.90, .84, .68]) * plate[..., None]; m = np.maximum(m, plate)
    a = t[..., 3:4]; rgb[ty:ty + th, tx:tx + tw] = rgb[ty:ty + th, tx:tx + tw] * (1 - a) + t[..., :3] * a
    return _rim(rgb, m, 3)


def balloon(col=(.82, .14, .12), w=140, h=520):
    spr, m = _blob(w, h, [('e', .5, .16, .36, .15), ('p', [(.46, .3), (.54, .3), (.5, .34)])], col, 63, 3)
    cv2.line(spr, (w // 2, int(h * .33)), (int(w * .45), h - 2), (.2, .18, .15, 1), 3, cv2.LINE_AA)
    return spr


def parasol(col=(.90, .86, .74), w=360, h=420):
    spr, m = _blob(w, h, [('p', [(.02, .3)] + [(.5 + .48 * math.cos(a), .3 - .26 * math.sin(a)) for a in np.linspace(math.pi, 0, 20)] + [(.98, .3)])], col, 64, 3)
    cv2.line(spr, (w // 2, int(h * .3)), (w // 2, h - 2), (.25, .2, .15, 1), 5, cv2.LINE_AA)
    return spr


def camera_tripod(w=300, h=560):
    spr, m = _blob(w, h, [('p', [(.3, .08), (.75, .08), (.75, .32), (.3, .32)]), ('p', [(.75, .14), (.92, .1), (.92, .3), (.75, .26)]), ('p', [(.48, .32), (.54, .32), (.2, 1), (.14, 1)]), ('p', [(.5, .32), (.56, .32), (.56, 1), (.5, 1)]),
                          ('p', [(.52, .32), (.58, .32), (.9, 1), (.84, 1)])], (.20, .14, .10), 65, 3, False)
    return spr


def bird(w=120, h=60):
    m = np.zeros((h, w), np.float32); cv2.polylines(m, [np.int32([(4, h * .3), (w * .3, h * .7), (w * .5, h * .35), (w * .7, h * .7), (w - 4, h * .3)])], False, 1.0, 9, cv2.LINE_AA)
    return rgba(np.full((h, w, 3), .08, np.float32), m)


def stone_wall(w=1000, h=700, seed=0):
    """Lit cage interior: pale plaster wall with stone courses, a barred window and a painted dado."""
    rgb = paper(h, w, np.float32([.74, .66, .52]), seed, .05, .15)
    for y in range(0, h, 70):
        cv2.line(rgb, (0, y), (w, y), (.56, .49, .38), 3)
        for x in range((y // 70 % 2) * 80, w, 160): cv2.line(rgb, (x, y), (x, y + 70), (.56, .49, .38), 3)
    rgb[int(h * .72):] *= np.float32([.70, .78, .66])
    wx0, wx1, wy0, wy1 = int(w * .68), int(w * .88), int(h * .12), int(h * .42)
    rgb[wy0:wy1, wx0:wx1] = np.float32([.80, .88, .92])
    for x in np.linspace(wx0, wx1, 5): cv2.line(rgb, (int(x), wy0), (int(x), wy1), (.15, .15, .17), 6)
    cv2.rectangle(rgb, (wx0, wy0), (wx1, wy1), (.3, .26, .2), 8)
    rgb *= (0.9 + 0.2 * np.exp(-((np.linspace(-1, 1, w, dtype=np.float32)[None, :, None]) ** 2) * 2))
    return rgba(np.clip(rgb, 0, 1), np.ones((h, w), np.float32))


def straw(w=1000, h=500, seed=0):
    rgb = paper(h, w, np.float32([.80, .68, .36]), seed, .08, .2); r = np.random.default_rng(seed)
    for i in range(500):
        x, y = int(r.integers(w)), int(r.integers(h)); a = r.uniform(0, 3.14); L = int(r.integers(20, 60))
        cv2.line(rgb, (x, y), (int(x + math.cos(a) * L), int(y + math.sin(a) * L)), tuple(float(v) for v in np.float32([.92, .80, .45]) * r.uniform(.6, 1.1)), 2, cv2.LINE_AA)
    return rgba(np.clip(rgb, 0, 1), torn(h, w, 12, 4, seed + 1))


def branch(w=900, h=500):
    spr, m = _blob(w, h, [('p', [(0, .5), (.5, .42), (1, .3), (1, .38), (.5, .52), (0, .6)]), ('p', [(.3, .47), (.42, .1), (.48, .12), (.38, .5)]), ('p', [(.6, .42), (.72, .85), (.78, .84), (.68, .4)])], (.34, .24, .15), 66, 3, False)
    return spr


def skyline_old(w=2400, h=700, seed=0):
    """Hazy 1900s city: low blocks, church spires, chimneys, a water tower."""
    r = np.random.default_rng(seed); m = np.zeros((h, w), np.float32); x = 0
    while x < w:
        bw = int(r.integers(70, 190)); bh = int(r.uniform(.2, .7) * h); cv2.rectangle(m, (x, h - bh), (x + bw, h), 1.0, -1); k = r.random()
        if k < .18: cv2.fillPoly(m, [np.int32([(x + bw * .3, h - bh), (x + bw * .5, h - bh - 190), (x + bw * .7, h - bh)])], 1.0)
        elif k < .4: cv2.rectangle(m, (x + bw // 3, h - bh - 60), (x + bw // 3 + 18, h - bh), 1.0, -1)
        elif k < .5: cv2.rectangle(m, (x + bw // 2 - 26, h - bh - 70), (x + bw // 2 + 26, h - bh - 24), 1.0, -1); cv2.line(m, (x + bw // 2, h - bh - 24), (x + bw // 2, h - bh), 1.0, 8)
        x += bw + int(r.integers(0, 14))
    return rgba(paper(h, w, np.float32([.42, .40, .44]), seed, .05, .15), m)
