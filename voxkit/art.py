"""voxkit.art - procedurally drawn paper props and anonymous archival-style cutout figures."""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw
from .core import *


def _L(w, h, bg=0): return Image.new('L', (w, h), bg)
def _np(im): return np.asarray(im, np.float32) / 255
def _soft(a, s): return cv2.GaussianBlur(a, (0, 0), s)


def _light(g, m, seed=0, amt=0.22):
    """Fake photographic modelling: soft side light + grain inside mask."""
    h, w = g.shape
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    inner = _soft(m, max(h, w) * 0.03)
    g = g + amt * (0.35 - xx * 0.5) * 0.6 + (inner - 0.8) * 0.25
    g = g + (fbm(h, w, 40, 3, seed) - 0.5) * 0.10
    return np.clip(g, 0, 1)


def eye_plate(w=1500, h=2600):
    """Macro newsprint sheet (tall) with one halftone-printed eye in the middle."""
    e = _eye_gray(w, 1150)
    g = np.full((h, w), 0.62, np.float32) + (fbm(h, w, 3, 3, 14) - 0.5) * 0.18
    y0 = (h - 1150) // 2
    k = np.clip(np.minimum(np.arange(1150), 1149 - np.arange(1150)) / 220.0, 0, 1).astype(np.float32)[:, None]
    g[y0:y0 + 1150] = g[y0:y0 + 1150] * (1 - k) + e * k
    rgb = ink_on_paper(halftone(g, 15.0, 45, 1.05), col=PAPER, seed=2)
    return rgba(rgb, np.ones((h, w), np.float32))


def _eye_gray(w=1500, h=1150):
    g = np.full((h, w), 0.62, np.float32)
    g += (fbm(h, w, 3, 3, 4) - 0.5) * 0.18
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); cx, cy = w * 0.5, h * 0.55
    g -= 0.20 * np.exp(-(((xx - cx) / (w * .42)) ** 2 + ((yy - cy + h * .05) / (h * .30)) ** 2))   # socket shade
    im = Image.fromarray((g * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    ew, eh = w * 0.31, h * 0.135
    up = [(cx - ew + 2 * ew * i / 60, cy - eh * math.sin(math.pi * i / 60) ** 0.8 * (1.15 - 0.25 * i / 60)) for i in range(61)]
    lo = [(cx - ew + 2 * ew * i / 60, cy + eh * 0.62 * math.sin(math.pi * i / 60) ** 0.9) for i in range(61)]
    d.polygon(up + lo[::-1], fill=228)
    eye = Image.new('L', (w, h), 0); ImageDraw.Draw(eye).polygon(up + lo[::-1], fill=255)
    iris = Image.new('L', (w, h), 0); di = ImageDraw.Draw(iris); R = eh * 1.02
    di.ellipse([cx - R, cy - R * 1.05, cx + R, cy + R * .95], fill=255)
    ia = _np(iris) * _np(eye)
    g = _np(im)
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy + R * .05) ** 2) / R; th = np.arctan2(yy - cy, xx - cx)
    irisg = 0.34 + 0.10 * np.sin(th * 23) * np.clip(rr, 0, 1) + 0.12 * rr - 0.25 * (rr > 0.9)
    irisg = np.where(rr < 0.42, 0.03, irisg)
    g = g * (1 - ia) + irisg * ia
    g -= 0.30 * _soft(_np(eye), 4) * np.clip(1 - (yy - (cy - eh)) / (eh * 0.9), 0, 1) * (1 - ia * 0.3) * 0.6     # lid shadow
    im = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.ellipse([cx - R * .42, cy - R * .62, cx - R * .05, cy - R * .25], fill=250)                 # catchlight
    d.line(up, fill=14, width=int(h * 0.016)); d.line(lo, fill=70, width=int(h * 0.006))
    for i in range(4, 58, 2):                                                                      # lashes
        x, y = up[i]; k = (i - 30) / 30
        d.line([(x, y), (x + k * w * .03 - w * .004, y - h * (0.045 + 0.02 * (1 - abs(k))))], fill=18, width=int(h * .006))
    crease = [(x, y - eh * (0.55 + 0.25 * math.sin(math.pi * i / 60))) for i, (x, y) in enumerate(up)]
    d.line(crease, fill=95, width=int(h * 0.008))
    brow = [(cx - ew * 1.12 + 2.3 * ew * i / 40, cy - eh * 2.55 - eh * 0.75 * math.sin(math.pi * (i / 40) ** 0.8) + (i / 40) * eh * .3) for i in range(41)]
    for i in range(40):
        d.line([brow[i], brow[i + 1]], fill=22, width=int(h * (0.050 - 0.030 * i / 40)))
    return _soft(_np(im), 2.2)


def bar(w=1500, h=300, seed=0):
    a = torn(h, w, 5, 3, seed)
    rgb = paper(h, w, np.array([.055, .05, .045], np.float32), seed, 0.25, 0.3)
    return rgba(rgb, a)


def woman(w=760, h=920, smile=False):
    """Anonymous businesswoman bust (shoulder-length dark hair, dark blazer). Eyes are always under a censor bar."""
    S = 2; W2, H2 = w * S, h * S
    im = _L(W2, H2); d = ImageDraw.Draw(im); m = _L(W2, H2); dm = ImageDraw.Draw(m)
    cx = W2 * 0.5
    def both(fn, *a, fill): getattr(d, fn)(*a, fill=fill); getattr(dm, fn)(*a, fill=255)
    both('ellipse', [cx - W2 * .30, H2 * .045, cx + W2 * .30, H2 * .60], fill=30)                          # hair mass
    both('polygon', [(cx - W2 * .30, H2 * .30), (cx - W2 * .33, H2 * .66), (cx - W2 * .12, H2 * .70), (cx + W2 * .12, H2 * .70), (cx + W2 * .33, H2 * .66), (cx + W2 * .30, H2 * .30)], fill=30)
    both('polygon', [(cx - W2 * .47, H2), (cx - W2 * .44, H2 * .74), (cx - W2 * .16, H2 * .635), (cx + W2 * .16, H2 * .635), (cx + W2 * .44, H2 * .74), (cx + W2 * .47, H2)], fill=48)   # blazer
    d.polygon([(cx - W2 * .10, H2 * .62), (cx + W2 * .10, H2 * .62), (cx + W2 * .02, H2 * .93), (cx - W2 * .02, H2 * .93)], fill=215)   # blouse
    d.polygon([(cx - W2 * .075, H2 * .48), (cx + W2 * .075, H2 * .48), (cx + W2 * .085, H2 * .67), (cx, H2 * .735), (cx - W2 * .085, H2 * .67)], fill=168)  # neck
    d.polygon([(cx - W2 * .17, H2 * .635), (cx - W2 * .075, H2 * .655), (cx - W2 * .015, H2 * .95), (cx - W2 * .10, H2 * .83), (cx - W2 * .20, H2 * .80)], fill=26)   # lapels
    d.polygon([(cx + W2 * .17, H2 * .635), (cx + W2 * .075, H2 * .655), (cx + W2 * .015, H2 * .95), (cx + W2 * .10, H2 * .83), (cx + W2 * .20, H2 * .80)], fill=26)
    d.ellipse([cx - W2 * .178, H2 * .125, cx + W2 * .178, H2 * .555], fill=205)                            # face
    d.polygon([(cx - W2 * .19, H2 * .32), (cx - W2 * .20, H2 * .10), (cx + W2 * .06, H2 * .085), (cx + W2 * .005, H2 * .17), (cx - W2 * .12, H2 * .23)], fill=30)   # side-swept fringe
    d.polygon([(cx + W2 * .19, H2 * .34), (cx + W2 * .20, H2 * .10), (cx + W2 * .0, H2 * .09), (cx + W2 * .10, H2 * .18)], fill=30)
    d.polygon([(cx - W2 * .012, H2 * .33), (cx + W2 * .03, H2 * .405), (cx - W2 * .005, H2 * .41)], fill=172)   # nose shadow
    if smile:
        d.arc([cx - W2 * .085, H2 * .385, cx + W2 * .085, H2 * .475], 20, 160, fill=70, width=int(H2 * .012))
    else:
        pass
    d.ellipse([cx - W2 * .15, H2 * .43, cx - W2 * .06, H2 * .49], fill=188); d.ellipse([cx + W2 * .06, H2 * .43, cx + W2 * .15, H2 * .49], fill=188)
    g = cv2.resize(_soft(_np(im), 3.0), (w, h), interpolation=cv2.INTER_AREA); mk = cv2.resize(_np(m), (w, h), interpolation=cv2.INTER_AREA)
    return cutout(_light(g, mk, 3), mk, 5.0, 14, seed=31)


def man(w=380, h=640):
    """Anonymous executive, full body: silver hair, black leather jacket, dark trousers."""
    S = 3; W2, H2 = w * S, h * S
    im = _L(W2, H2); d = ImageDraw.Draw(im); m = _L(W2, H2); dm = ImageDraw.Draw(m)
    cx = W2 * .5
    def both(fn, *a, fill): getattr(d, fn)(*a, fill=fill); getattr(dm, fn)(*a, fill=255)
    both('polygon', [(cx - W2 * .17, H2 * .52), (cx - W2 * .20, H2 * .93), (cx - W2 * .04, H2 * .93), (cx, H2 * .60), (cx + W2 * .04, H2 * .93), (cx + W2 * .20, H2 * .93), (cx + W2 * .17, H2 * .52)], fill=40)   # trousers
    both('rounded_rectangle', [cx - W2 * .25, H2 * .915, cx - W2 * .03, H2 * .965], int(H2 * .02), fill=18)
    both('rounded_rectangle', [cx + W2 * .03, H2 * .915, cx + W2 * .25, H2 * .965], int(H2 * .02), fill=18)
    both('polygon', [(cx - W2 * .30, H2 * .225), (cx - W2 * .40, H2 * .52), (cx - W2 * .30, H2 * .55), (cx - W2 * .22, H2 * .34)], fill=24)    # arms
    both('polygon', [(cx + W2 * .30, H2 * .225), (cx + W2 * .40, H2 * .52), (cx + W2 * .30, H2 * .55), (cx + W2 * .22, H2 * .34)], fill=24)
    both('ellipse', [cx - W2 * .41, H2 * .50, cx - W2 * .29, H2 * .58], fill=170); both('ellipse', [cx + W2 * .29, H2 * .50, cx + W2 * .41, H2 * .58], fill=170)
    both('polygon', [(cx - W2 * .31, H2 * .225), (cx - W2 * .12, H2 * .185), (cx + W2 * .12, H2 * .185), (cx + W2 * .31, H2 * .225), (cx + W2 * .25, H2 * .56), (cx - W2 * .25, H2 * .56)], fill=22)   # jacket
    d.polygon([(cx - W2 * .07, H2 * .19), (cx + W2 * .07, H2 * .19), (cx + W2 * .03, H2 * .50), (cx - W2 * .03, H2 * .50)], fill=58)           # dark tee
    d.polygon([(cx - W2 * .13, H2 * .185), (cx - W2 * .05, H2 * .20), (cx - W2 * .02, H2 * .36), (cx - W2 * .15, H2 * .27)], fill=64)          # lapel sheen
    d.polygon([(cx + W2 * .13, H2 * .185), (cx + W2 * .05, H2 * .20), (cx + W2 * .02, H2 * .36), (cx + W2 * .15, H2 * .27)], fill=64)
    d.line([(cx - W2 * .27, H2 * .30), (cx - W2 * .24, H2 * .52)], fill=70, width=int(W2 * .012)); d.line([(cx + W2 * .27, H2 * .30), (cx + W2 * .24, H2 * .52)], fill=70, width=int(W2 * .012))
    both('rectangle', [cx - W2 * .055, H2 * .15, cx + W2 * .055, H2 * .20], fill=160)                                                          # neck
    both('ellipse', [cx - W2 * .125, H2 * .035, cx + W2 * .125, H2 * .175], fill=198)                                                         # head
    both('pieslice', [cx - W2 * .14, H2 * .018, cx + W2 * .14, H2 * .15], 180, 360, fill=226)                                                 # silver hair
    d.polygon([(cx - W2 * .14, H2 * .085), (cx - W2 * .125, H2 * .115), (cx - W2 * .10, H2 * .08)], fill=226); d.polygon([(cx + W2 * .14, H2 * .085), (cx + W2 * .125, H2 * .115), (cx + W2 * .10, H2 * .08)], fill=226)
    d.line([(cx - W2 * .04, H2 * .148), (cx + W2 * .04, H2 * .148)], fill=110, width=int(H2 * .005))
    g = cv2.resize(_soft(_np(im), 2.5), (w, h), interpolation=cv2.INTER_AREA); mk = cv2.resize(_np(m), (w, h), interpolation=cv2.INTER_AREA)
    spr = cutout(_light(g, mk, 8, 0.16), mk, 4.0, 10, seed=41)
    by, bh = int(h * .088), int(h * .03)                                                                                                     # baked censor bar
    x0, x1 = int(w * .345), int(w * .655)
    spr[by:by + bh, x0:x1, :3] = np.array([.05, .045, .04], np.float32); spr[by:by + bh, x0:x1, 3] = 1
    return spr


def page(w=900, h=1300, portrait=None):
    """Aged front page with a big censor-bar portrait."""
    rgb = newsprint(h, w, seed=5, cols=3)
    px, py, pw, ph = int(w * .13), int(h * .20), int(w * .74), int(h * .56)
    if portrait is not None:
        p = cv2.resize(portrait, (pw, int(pw * portrait.shape[0] / portrait.shape[1])), interpolation=cv2.INTER_AREA)[:ph]
        ph = p.shape[0]
        bgp = ink_on_paper(halftone(np.full((ph, pw), 0.55, np.float32) + (fbm(ph, pw, 3, 3, 9) - .5) * .2, 5.0), seed=6)
        a = p[..., 3:4]
        rgb[py:py + ph, px:px + pw] = bgp * (1 - a) + p[..., :3] * a
        cv2.rectangle(rgb, (px, py), (px + pw, py + ph), tuple(float(x) for x in INK), 5)
    return rgba(rgb, torn(h, w, 9, 4, 12))


def bundle(w=460, h=150, seed=0):
    """A tied stack of newspapers seen from the side."""
    rgb = paper(h, w, PAPER * 0.92, seed, 0.05, 0.15)
    r = np.random.default_rng(seed)
    for y in range(4, h, 5):
        c = float(r.uniform(.45, .8)); cv2.line(rgb, (0, y + int(r.integers(-1, 2))), (w, y + int(r.integers(-1, 2))), (c * .9, c * .8, c * .62), 1, cv2.LINE_AA)
    for x in (int(w * .28), int(w * .72)):
        cv2.rectangle(rgb, (x - 6, 0), (x + 6, h), tuple(float(v) for v in INK * 1.6), -1)
    return rgba(rgb, torn(h, w, 5, 2, seed + 4))


def tower(n=7, w=460, bh=150, seed=0, torn_top=False, torn_bot=False):
    h = n * (bh - 8) + 8
    out = np.zeros((h, w + 60, 4), np.float32); r = np.random.default_rng(seed)
    for i in range(n):
        b = bundle(w, bh, seed + i * 3); x = 30 + int(r.integers(-22, 22)); y = h - bh - i * (bh - 8)
        a = b[..., 3:4]; reg = out[y:y + bh, x:x + w]
        reg[..., :3] = reg[..., :3] * (1 - a) + b[..., :3] * a * (0.78 + 0.22 * (i % 2)); reg[..., 3:4] = np.maximum(reg[..., 3:4], a)
    if torn_top or torn_bot:
        hh, ww = out.shape[:2]; xs = np.arange(ww)
        zig = (np.abs(((xs / 38.0) % 2) - 1) * 46 + fbm(1, ww, 30, 2, seed)[0] * 30).astype(np.int32)
        yy = np.arange(hh)[:, None]
        if torn_top: out[..., 3] *= (yy > zig[None, :] + 4)
        if torn_bot: out[..., 3] *= (yy < hh - 60 + zig[None, :] - 30)
    return out


def ridge(w=2600, h=620, seed=0, col=PAPER, dark=0.8, amp=120):
    """Wide torn newsprint ground / ridge with a ragged top edge."""
    rgb = newsprint(h, w, seed, col, dark, cols=7)
    xs = np.arange(w, dtype=np.float32)
    top = (fbm(1, w, 5, 4, seed + 2)[0] * amp + fbm(1, w, 120, 2, seed + 3)[0] * 14)
    yy = np.arange(h, dtype=np.float32)[:, None]
    a = np.clip((yy - top[None, :]) / 1.5, 0, 1)
    edge = np.clip(1 - (yy - top[None, :]) / 9, 0, 1) * a
    rgb = rgb * (1 - edge[..., None] * 0.75) + np.array([.95, .92, .85], np.float32) * edge[..., None] * 0.75   # white torn lip
    return rgba(rgb, a.astype(np.float32))


def chip(s=460):
    """Burnt-orange paper microchip - the through-line prop."""
    c = np.zeros((s, s, 4), np.float32)
    body = paper(s, s, ORANGE, 3, 0.06, 0.16)
    m = np.zeros((s, s), np.float32); p = int(s * .13)
    cv2.rectangle(m, (p, p), (s - p, s - p), 1, -1)
    m = m * torn(s, s, 3, p - 4, 6)
    pins = np.zeros((s, s), np.float32); n = 9; pw = int(s * .034)
    for i in range(n):
        x = int(p + (s - 2 * p) * (i + .5) / n)
        cv2.rectangle(pins, (x - pw // 2, int(p * .25)), (x + pw // 2, p + 4), 1, -1); cv2.rectangle(pins, (x - pw // 2, s - p - 4), (x + pw // 2, s - int(p * .25)), 1, -1)
        cv2.rectangle(pins, (int(p * .25), x - pw // 2), (p + 4, x + pw // 2), 1, -1); cv2.rectangle(pins, (s - p - 4, x - pw // 2), (s - int(p * .25), x + pw // 2), 1, -1)
    pcol = paper(s, s, np.array([.16, .13, .10], np.float32), 8, 0.08, 0.2)
    rgb = pcol * pins[..., None] * (1 - m[..., None]) + body * m[..., None]
    d0, d1 = int(s * .33), int(s * .67)
    die = paper(d1 - d0, d1 - d0, ORANGE * 0.62, 9, 0.07, 0.2)
    rgb[d0:d1, d0:d1] = die
    cv2.rectangle(rgb, (d0, d0), (d1, d1), tuple(float(v) for v in ORANGE * 0.4), 3)
    for i in range(5):                                                                                 # embossed traces
        y = int(d0 + (d1 - d0) * (i + .5) / 5)
        for xa, xb in ((p + 16, d0 - 8), (d1 + 8, s - p - 16)):
            cv2.line(rgb, (xa, y), (xb, y), tuple(float(v) for v in ORANGE * 0.72), 3, cv2.LINE_AA)
            cv2.line(rgb, (y, xa), (y, xb), tuple(float(v) for v in ORANGE * 0.72), 3, cv2.LINE_AA)
    cv2.circle(rgb, (p + 26, p + 26), 9, tuple(float(v) for v in ORANGE * 0.45), -1, cv2.LINE_AA)
    c[..., :3] = rgb; c[..., 3] = np.maximum(m, pins)
    return c


def label(txt, size=150, padx=70, pady=46, seed=0, col=ORANGE):
    """Torn burnt-orange paper strip carrying distressed letterpress type."""
    t = text_sprite(txt, size, INK, pad=8, squeeze=0.82, distress=0.3, seed=seed, tracking=4)
    th, tw = t.shape[:2]; h, w = th + pady * 2, tw + padx * 2
    rgb = paper(h, w, col, seed + 2, 0.06, 0.18)
    a = t[..., 3:4]
    rgb[pady:pady + th, padx:padx + tw] = rgb[pady:pady + th, padx:padx + tw] * (1 - a) + t[..., :3] * a
    return rgba(rgb, torn(h, w, 9, 4, seed + 5))


def dial(s=860):
    """Paper stopwatch face: ticks only, no numerals."""
    c = s // 2; yy, xx = np.mgrid[0:s, 0:s].astype(np.float32); rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    n = fbm(s, s, 60, 2, 3)
    a = np.clip((c - 10 - rr - n * 6) / 1.5, 0, 1)
    rgb = paper(s, s, PAPER_LT, 21, 0.04, 0.12)
    ring = ((rr > c * .88) & (rr < c * .93)).astype(np.float32)
    rgb = rgb * (1 - ring[..., None]) + INK * ring[..., None]
    for i in range(60):
        th = i / 60 * 2 * math.pi; big = i % 5 == 0
        r0, r1 = c * (.70 if big else .78), c * .85
        cv2.line(rgb, (int(c + math.sin(th) * r0), int(c - math.cos(th) * r0)), (int(c + math.sin(th) * r1), int(c - math.cos(th) * r1)), tuple(float(v) for v in INK), 9 if big else 3, cv2.LINE_AA)
    sub = ink_on_paper(halftone(np.clip(rr / (c * .6), 0, 1) * 0.5 + 0.45, 6.0), seed=4)
    k = (rr < c * .62)[..., None].astype(np.float32)
    rgb = rgb * (1 - k * 0.5) + sub * k * 0.5
    return rgba(rgb, a)


def crown(s=150):
    """Stopwatch crown/button (dark paper)."""
    rgb = paper(s, s, np.array([.14, .12, .10], np.float32), 5, 0.1, 0.2)
    m = np.zeros((s, s), np.float32); cv2.rectangle(m, (int(s * .3), int(s * .1)), (int(s * .7), s), 1, -1); cv2.rectangle(m, (int(s * .15), 0), (int(s * .85), int(s * .35)), 1, -1)
    return rgba(rgb, m * torn(s, s, 3, 1, 2))


def hand(w=70, h=400):
    rgb = paper(h, w, ORANGE, 14, 0.05, 0.12)
    m = np.zeros((h, w), np.float32)
    cv2.fillConvexPoly(m, np.int32([(w / 2, 0), (w * .82, h * .82), (w / 2, h), (w * .18, h * .82)]), 1.0, cv2.LINE_AA)
    return rgba(rgb, m)


def wall(w=700, h=2048, seed=0, dark=0.55, side='r'):
    """Vertically tileable canyon wall strip of layered newsprint, torn on one side."""
    rgb = newsprint(h, w, seed, PAPER, dark, cols=2)
    edge = (fbm(h, 1, 7, 4, seed + 1)[:, 0] * 260 + fbm(h, 1, 90, 2, seed + 2)[:, 0] * 26)
    k = np.linspace(0, 1, h); blend = np.clip((k - 0.9) / 0.1, 0, 1); edge = edge * (1 - blend) + edge[0] * blend     # tile seam
    xx = np.arange(w, dtype=np.float32)[None, :]
    a = np.clip(((w - 20 - edge[:, None]) - xx) / 1.5, 0, 1) if side == 'r' else np.clip((xx - 20 - edge[:, None]) / 1.5, 0, 1)
    return rgba(rgb, a.astype(np.float32))
