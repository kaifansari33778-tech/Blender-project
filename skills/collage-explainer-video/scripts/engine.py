"""2.5D cutout-collage engine: layers with perspective tilt, depth parallax, grading, captions, transitions, render loop.

Typical use (see demo_film.py):
    import engine as E
    E.init(workdir)                      # workdir holds cut/*.png and raw/*.jpg ; fonts come from the skill's assets/fonts
    POT = E.cut('pot', 600, amb=(1, .86, .5), s=.4, rim=(1, .78, .25))
    def s_intro(t): c = E.new(); E.bg_pan(c, BG, 750, 1200, 1.0); E.obj(c, POT, 540, 1000); return c
    film = E.Film(dur=20, scenes=[(0, s_intro)], trans=[], captions=[(0.2, 1.0, 'LINE ONE', 'PUNCH LINE', E.RED)])
    film.main()                          # python3 my_film.py <workdir> <frames_dir> [f0 f1 [step]]
All images are premultiplied float32 RGBA in 0..1. Screen is W x H = 1080 x 1920, 30 fps.
"""
import os, sys, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
A = '.'
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts')
PAD = 70
CAM = [0.0, 0.0]          # camera sway in px; place(..., depth=d) shifts a layer by CAM*d, backgrounds by CAM*0.3
def init(workdir, fonts=None):
    """set the asset directory (expects <workdir>/cut/*.png and <workdir>/raw/*.jpg)"""
    global A, FONT
    A = workdir
    if fonts: FONT = fonts
def anton(s): return ImageFont.truetype(f'{FONT}/Anton.ttf', s)
def caveat(s): return ImageFont.truetype(f'{FONT}/Caveat.ttf', s)
def inter(s, w=600):
    f = ImageFont.truetype(f'{FONT}/Inter.ttf', s)
    try: f.set_variation_by_axes([14, w])
    except Exception: pass
    return f
def new(): return np.zeros((H, W, 4), np.float32)
def pop(t, t0, d=.32, k=1.4):
    """0 -> overshoot -> 1 entrance curve starting at t0"""
    return back(seg(t, t0, t0 + d), k)
def pre(im):
    """PIL/np RGBA uint8 -> premultiplied float32"""
    a = np.asarray(im.convert('RGBA') if isinstance(im, Image.Image) else im).astype(np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    return a
def blur(img, r):
    return cv2.GaussianBlur(img, (0, 0), r) if r > 0.3 else img
def over(dst, src, op=1.0):
    if op <= 0: return
    a = src[..., 3:4] * op
    dst[..., :3] = dst[..., :3] * (1 - a) + src[..., :3] * op
    dst[..., 3:4] = dst[..., 3:4] * (1 - a) + a
def place(dst, img, cx, cy, s=1.0, rot=0.0, op=1.0, sx=None, add=False, anchor=(0.5, 0.5), rx=0.0, ry=0.0, depth=1.0):
    """draw img with its anchor at (cx,cy); rot = in-plane deg, rx/ry = 3D tilt deg with perspective; depth scales camera sway"""
    if op <= 0 or s <= 0: return
    cx += CAM[0] * depth; cy += CAM[1] * depth
    h, w = img.shape[:2]
    ax, ay = w * anchor[0], h * anchor[1]
    DW, DH = dst.shape[1], dst.shape[0]
    pts = np.array([[-ax, -ay, 0], [w - ax, -ay, 0], [w - ax, h - ay, 0], [-ax, h - ay, 0]], np.float32) * s
    if sx: pts[:, 0] *= sx
    a, b, g = math.radians(rx), math.radians(ry), math.radians(rot)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(g), -math.sin(g), 0], [math.sin(g), math.cos(g), 0], [0, 0, 1]])
    P = pts @ (Rz @ Ry @ Rx).T
    k = 2400.0 / (2400.0 + P[:, 2])
    q = np.stack([cx + P[:, 0] * k, cy + P[:, 1] * k], 1)
    x0, y0 = max(0, int(math.floor(q[:, 0].min())) - 1), max(0, int(math.floor(q[:, 1].min())) - 1)
    x1, y1 = min(DW, int(math.ceil(q[:, 0].max())) + 2), min(DH, int(math.ceil(q[:, 1].max())) + 2)
    if x1 <= x0 or y1 <= y0: return
    q = (q - (x0, y0)).astype(np.float32)
    Hm = cv2.getPerspectiveTransform(np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32), q)
    lay = cv2.warpPerspective(img, Hm, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA if s < 0.6 and not (rx or ry) else cv2.INTER_LINEAR)
    if (rx or ry) and not add: lay[..., :3] *= float(np.clip(1 + 0.35 * math.sin(b) - 0.25 * abs(math.sin(a)), .55, 1.3))
    sub = dst[y0:y1, x0:x1]
    if add: sub[..., :3] += lay[..., :3] * op
    else: over(sub, lay, op)
def grade(img, amb, s=0.35, rim=None, rim_r=7, rim_k=0.9, top=1.08, bot=0.82, under=None, sat=1.0):
    """match a cutout to its scene: ambient tint, top-to-bottom light falloff, coloured rim light, bounce glow from below"""
    o = img.copy(); a = o[..., 3:4]
    amb = np.array(amb, np.float32); amb = amb / amb.max()
    lum = (o[..., :3] @ np.array([.3, .59, .11], np.float32))[..., None]
    o[..., :3] = lum + (o[..., :3] - lum) * sat
    o[..., :3] *= (1 - s) + s * amb
    g = np.linspace(top, bot, o.shape[0], dtype=np.float32)[:, None, None]
    o[..., :3] *= g
    if rim is not None:
        e = a * np.clip(1 - blur(np.ascontiguousarray(a[..., 0]), rim_r)[..., None], 0, 1) * 2 * rim_k
        o[..., :3] += np.array(rim, np.float32) * e
    if under is not None:
        u = np.clip(np.linspace(-2.2, 1, o.shape[0], dtype=np.float32), 0, 1)[:, None, None] ** 2
        o[..., :3] += np.array(under, np.float32) * u * a * .5
    o[..., :3] = np.minimum(o[..., :3], a)
    return o
def shadow_of(img, r=18, dark=0.55):
    a = blur(np.ascontiguousarray(img[..., 3]), r) * dark
    o = np.zeros_like(img); o[..., 3] = a
    return o
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def eout(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def back(x, k=1.7):
    x = min(1, max(0, x)); x -= 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2
def seg(t, a, b): return (t - a) / (b - a)
def lerp(a, b, x): return a + (b - a) * x
def noise_tex(w, h, scale, seed, amp=1.0):
    r = np.random.RandomState(seed)
    n = cv2.resize(r.rand(max(2, h // scale), max(2, w // scale)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    return (n - 0.5) * amp
def rrect(d, box, r, **k): d.rounded_rectangle(box, r, **k)
def text_sprite(txt, font, fill, pad=30):
    b = font.getbbox(txt); im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, font=font, fill=fill); return im
def bg_pan(dst, tex, cx, cy, z):
    th, tw = tex.shape[:2]
    M = np.array([[z, 0, W / 2 - cx * z + CAM[0] * .3], [0, z, H / 2 - cy * z + CAM[1] * .3]], np.float32)
    dst[:] = cv2.warpAffine(tex, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
def lens(c, mx, my, R, zoom=1.55):
    mx += CAM[0] * 2; my += CAM[1] * 2
    x0, y0, x1, y1 = int(mx - R), int(my - R), int(mx + R), int(my + R)
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: return
    M = np.array([[zoom, 0, R - mx * zoom], [0, zoom, R - my * zoom]], np.float32)
    patch = cv2.warpAffine(c, M, (2 * R, 2 * R), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    yy, xx = np.mgrid[-1:1:2 * R * 1j, -1:1:2 * R * 1j].astype(np.float32); rr = np.hypot(xx, yy)
    m = np.clip((1 - rr) * 30, 0, 1)[..., None]; patch[..., :3] *= (1.08 - .25 * rr[..., None] ** 3)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    sub = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
    c[Y0:Y1, X0:X1] = c[Y0:Y1, X0:X1] * (1 - m[sub]) + patch[sub] * m[sub]
def path(t, pts):
    for (t0, x0, y0), (t1, x1, y1) in zip(pts, pts[1:]):
        if t <= t1: k = ease(seg(t, t0, t1)); return lerp(x0, x1, k), lerp(y0, y1, k)
    return pts[-1][1], pts[-1][2]
def caption(l1, l2, c_top, c_bot):
    w, h = 1000, 330; im = Image.new('RGBA', (w, h)); pad = 50
    def line(txt, f, y, top, bot, glow):
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad, y), txt, font=f, fill=255)
        g = np.linspace(0, 1, h)[:, None, None]; bb = m.getbbox() or (0, 0, 1, 1)
        g = np.clip((np.arange(h) - bb[1]) / max(1, bb[3] - bb[1]), 0, 1)[:, None, None]
        col = (np.array(top) * (1 - g) + np.array(bot) * g) * np.ones((h, w, 1))
        gl = Image.new('RGBA', (w, h), glow + (0,)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(16)).point(lambda v: min(255, int(v * 1.5))))
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(5)))
        im.alpha_composite(gl); im.alpha_composite(sh, (0, 5))
        im.alpha_composite(Image.fromarray(np.dstack([col, np.asarray(m)[..., None]]).astype(np.uint8), 'RGBA'))
    o1 = Image.new('RGBA', (w, h));
    line(l1, anton(74), 40, (255, 255, 255), (238, 232, 220), (60, 40, 20)); a = im.copy()
    im = Image.new('RGBA', (w, h)); line(l2, anton(next(z for z in range(116, 60, -4) if anton(z).getlength(l2) <= 930)), 118, c_top, c_bot, tuple(int(v * .8) for v in c_bot)) if l2 else None
    return pre(a), pre(im)
def finish_overlay():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.55 * np.clip((((xx - W / 2) / (W * .72)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2) - 0.35, 0, 1)
    v = v * (0.62 + 0.38 * np.clip(yy / 520, 0, 1) ** .8)
    mul = np.dstack([v, v, v])
    add = np.zeros((H, W, 3), np.float32)
    x0 = int(W * .622); add[:, x0 - 1:x0 + 1] += 0.07; mul[:, x0 + 2:x0 + 5] *= 0.93
    mul[:, x0 + 5:] *= 1.03
    for y in range(140, H, 215):
        cv2.circle(mul, (34, y), 9, (0.72, 0.72, 0.72), -1, cv2.LINE_AA)
    return mul, add

# ---------- cutouts, photos, generated art ----------
def padded(a, p=PAD): return cv2.copyMakeBorder(a, p, p, p, p, cv2.BORDER_CONSTANT)
def mk(a, sh_r=22, sh_d=.6):
    a = padded(a); return dict(i=a, s=shadow_of(a, sh_r, sh_d))
def cut(key, width, flip=False, **kw):
    im = Image.open(f'{A}/cut/{key}.png').convert('RGBA')
    im = im.resize((width, max(1, int(width * im.height / im.width))), Image.LANCZOS)
    a = pre(im)
    if flip: a = np.ascontiguousarray(a[:, ::-1])
    return mk(grade(a, **kw) if kw else a)
def obj(c, o, x, y, s=1.0, rot=0.0, op=1.0, lift=1.0, depth=1.0, rx=0.0, ry=0.0, sh=.8):
    if op <= 0 or s <= 0: return
    place(c, o['s'], x + 20 * lift * s, y + 28 * lift * s, s * (1 + .03 * lift), rot, sh * op / (1 + .35 * lift), depth=depth * .96, rx=rx, ry=ry)
    place(c, o['i'], x, y, s, rot, op, depth=depth, rx=rx, ry=ry)
def photo(key, w=1400, h=2490, tint=(1, 1, 1), s=0.0, bright=1.0, sat=1.0, contrast=1.0, blur_r=0, focus=(.5, .5), vig=.0):
    im = Image.open(f'{A}/raw/{key}.jpg').convert('RGB')
    k = max(w / im.width, h / im.height); im = im.resize((math.ceil(im.width * k), math.ceil(im.height * k)), Image.LANCZOS)
    x0 = int((im.width - w) * focus[0]); y0 = int((im.height - h) * focus[1]); im = im.crop((x0, y0, x0 + w, y0 + h))
    a = np.asarray(im).astype(np.float32) / 255
    lum = (a @ np.array([.3, .59, .11], np.float32))[..., None]
    a = lum + (a - lum) * sat; a = (a - .5) * contrast + .5
    t = np.array(tint, np.float32); a = a * ((1 - s) + s * t / t.max()) * bright
    if vig:
        yy, xx = np.mgrid[-1:1:h * 1j, -1:1:w * 1j].astype(np.float32); a *= (1 - vig * np.clip(xx * xx + yy * yy - .3, 0, 1))[..., None]
    a = np.clip(a, 0, 1)
    if blur_r: a = blur(a, blur_r)
    return np.dstack([a, np.ones((h, w), np.float32)]).astype(np.float32)
def flat_bg(rgb, seed=1, w=1500, h=2400, n=.10):
    c = np.ones((h, w, 3), np.float32) * np.array(rgb, np.float32)
    c += (noise_tex(w, h, 3, seed, .035) + noise_tex(w, h, 60, seed + 1, .025) + noise_tex(w, h, 500, seed + 2, n))[..., None]
    yy, xx = np.mgrid[-1:1:h * 1j, -1:1:w * 1j].astype(np.float32)
    c *= (1.12 - .32 * np.clip(xx * xx + yy * yy, 0, 1.4))[..., None]
    return np.dstack([np.clip(c, 0, 1), np.ones((h, w), np.float32)]).astype(np.float32)
def reveal(img, p, soft=40, vertical=False):
    """left-to-right (or top-down) wipe for drawn-on strokes"""
    n = img.shape[0] if vertical else img.shape[1]
    m = np.clip((p * (n + soft) - np.arange(n)) / soft, 0, 1).astype(np.float32)
    return img * (m[:, None, None] if vertical else m[None, :, None])
def sphere(r, base, hi=(1, 1, 1), glow=None):
    s = r * 2 + 8; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32) * (s / (2 * r))
    d = np.hypot(xx, yy); a = np.clip((1 - d) * r, 0, 1)
    sh = np.clip(1 - np.hypot(xx + .35, yy + .4) * .75, 0.12, 1)
    spec = np.exp(-(np.hypot(xx + .38, yy + .42) / .22) ** 2)
    rgb = np.array(base, np.float32) * sh[..., None] + np.array(hi, np.float32) * spec[..., None]
    rim = np.clip(d - .72, 0, 1)[..., None] * 1.2 * np.array(base, np.float32)
    o = np.dstack([np.clip(rgb + rim * .5, 0, 1), a]).astype(np.float32); o[..., :3] *= o[..., 3:4]
    return o
def glow_sprite(r, col):
    s = r * 2; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    g = np.clip(1 - np.hypot(xx, yy), 0, 1) ** 2
    return np.dstack([g[..., None] * np.array(col, np.float32), np.zeros((s, s), np.float32)]).astype(np.float32)
def stroke(pts, w=22, col=(214, 30, 40, 255), size=None, rough=True):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; size = size or (int(max(xs)) + 40, int(max(ys)) + 40)
    im = Image.new('RGBA', size); d = ImageDraw.Draw(im)
    d.line(pts, fill=col, width=w, joint='curve')
    for p in (pts[0], pts[-1]): d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)
    a = pre(im)
    if rough: a *= np.clip(noise_tex(size[0], size[1], 3, 77, 1.0) + 1.0, .55, 1)[..., None]
    return a
def cross(sz=260, w=26):
    a = stroke([(30, 30), (sz - 30, sz - 30)], w, size=(sz, sz)); b = stroke([(sz - 30, 30), (30, sz - 30)], w, size=(sz, sz))
    return a, b
def tick(sz=260, w=28):
    return stroke([(30, sz * .55), (sz * .4, sz - 40), (sz - 30, 40)], w, (40, 200, 90, 255), size=(sz, sz))
def highlight(wd=440, col=(70, 230, 110, 150)):
    im = Image.new('RGBA', (wd, 62)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 6, wd - 1, 56], 14, fill=col)
    return pre(im.filter(ImageFilter.GaussianBlur(1.5)))
def marker(col=(40, 190, 90)):
    w, h = 130, 620; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.polygon([(45, 0), (85, 0), (95, 70), (35, 70)], fill=col + (255,)); d.rounded_rectangle([25, 66, 105, 150], 10, fill=(30, 30, 30, 255))
    d.rounded_rectangle([18, 140, 112, h - 4], 22, fill=col + (255,)); d.rounded_rectangle([18, 140, 50, h - 4], 16, fill=tuple(min(255, v + 60) for v in col) + (255,))
    return im
def paper(kicker, title_lines, w=760, h=980, bar=None, kcol=(190, 40, 40), body=True):
    im = Image.new('RGBA', (w, h), (244, 239, 226, 255)); d = ImageDraw.Draw(im); y = 50
    if bar: d.rectangle([0, 0, w, 110], fill=bar + (255,)); d.text((44, 55), kicker, font=inter(34, 800), fill=(255, 255, 255), anchor='lm'); y = 150
    else: d.text((50, y), kicker, font=inter(28, 800), fill=kcol); y += 54
    for l in title_lines: d.text((50, y), l, font=inter(46, 800), fill=(26, 24, 22)); y += 62
    y += 26; d.line([50, y, w - 50, y], fill=(120, 116, 106), width=3); y += 30
    r = random.Random(len(kicker))
    while body and y < h - 60: d.rectangle([50, y, w - 50 - r.randint(0, 220), y + 10], fill=(150, 146, 136, 255)); y += 30
    return im
def pin():
    im = Image.new('RGBA', (90, 110)); d = ImageDraw.Draw(im)
    d.line([45, 60, 52, 104], fill=(120, 120, 120, 255), width=5); d.ellipse([12, 6, 78, 72], fill=(214, 30, 40, 255)); d.ellipse([26, 16, 48, 38], fill=(255, 130, 130, 255))
    return im
def tile(sym, num, name, light=True):
    w = 420; im = Image.new('RGBA', (w + 40, w + 60)); d = ImageDraw.Draw(im)
    base, top, ink = ((176, 170, 158), (226, 221, 208), (70, 68, 64)) if light else ((16, 16, 18), (48, 48, 52), (12, 12, 14))
    d.rounded_rectangle([0, 34, w + 39, w + 59], 26, fill=base + (255,)); d.rounded_rectangle([0, 0, w + 39, w + 20], 26, fill=top + (255,))
    d.rounded_rectangle([10, 10, w + 29, w + 10], 20, outline=tuple(min(255, v + 22) for v in top) + (255,), width=5)
    d.text((44, 30), num, font=inter(44, 700), fill=ink); d.text(((w + 40) / 2, 205), sym, font=inter(210, 800), fill=ink, anchor='mm')
    d.text(((w + 40) / 2, 372), name, font=inter(34, 700), fill=ink, anchor='mm')
    return im
def hang_tag(txt, col, w=170, h=250, fs=58):
    im = Image.new('RGBA', (w, h + 60)); d = ImageDraw.Draw(im)
    d.line([w / 2, 0, w / 2, 80], fill=(230, 220, 200, 255), width=4)
    d.polygon([(22, 110), (w / 2, 60), (w - 22, 110), (w - 14, h + 54), (14, h + 54)], fill=col + (255,))
    d.ellipse([w / 2 - 10, 82, w / 2 + 10, 102], fill=(20, 20, 20, 255))
    d.text((w / 2, 60 + (h + 60) / 2), txt, font=anton(fs), fill=(255, 255, 255, 255), anchor='mm')
    return im
def label_tag(txt, col=(232, 206, 150), ink=(60, 36, 20)):
    f = anton(64); wd = int(f.getlength(txt)) + 130; im = Image.new('RGBA', (wd, 120)); d = ImageDraw.Draw(im)
    d.polygon([(0, 60), (50, 6), (wd - 4, 6), (wd - 4, 114), (50, 114)], fill=col + (255,)); d.ellipse([30, 48, 54, 72], fill=(40, 30, 20, 255))
    d.text((80, 60), txt, font=f, fill=ink + (255,), anchor='lm')
    return im
def badge(l1, l2):
    im = Image.new('RGBA', (330, 300)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 329, 299], 26, fill=(22, 26, 40, 255), outline=(250, 200, 70, 255), width=8)
    d.text((165, 74), l1, font=anton(74), fill=(255, 255, 255), anchor='mm'); d.text((165, 196), l2, font=anton(150), fill=(250, 206, 70), anchor='mm')
    return im
def bubble(initials, col, user, text):
    f = inter(38, 700); wd = int(f.getlength(text)) + 190; im = Image.new('RGBA', (wd, 130)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, wd - 1, 129], 40, fill=(252, 252, 252, 255), outline=(210, 210, 215, 255), width=3)
    d.ellipse([20, 22, 106, 108], fill=col + (255,)); d.text((63, 65), initials, font=inter(36, 800), fill=(255, 255, 255), anchor='mm')
    d.text((130, 22), user, font=inter(24, 600), fill=(130, 130, 140)); d.text((130, 56), text, font=f, fill=(24, 24, 28))
    return im
def shelf_plank(w=1300):
    im = Image.new('RGBA', (w, 190)); d = ImageDraw.Draw(im)
    for x in (170, w - 210):
        d.polygon([(x, 50), (x + 34, 50), (x + 34, 186), (x, 120)], fill=(22, 18, 16, 255))
    a = np.asarray(im).astype(np.float32) / 255
    wood = np.ones((56, w, 3), np.float32) * np.array([.42, .24, .11]) + cv2.resize(np.random.RandomState(3).rand(56, 30).astype(np.float32), (w, 56))[..., None] * .16 - .08
    a[0:56, :, :3] = wood; a[0:56, :, 3] = 1; a[0:10, :, :3] *= 1.35; a[44:56, :, :3] *= .55
    a[..., :3] *= a[..., 3:4]
    return a
def smoke_sprite(col=(.12, .1, .09), a=.6):
    s = 360; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    g = np.clip(1 - np.hypot(xx, yy), 0, 1) ** 1.6 * np.clip(.6 + noise_tex(s, s, 40, 9, 1.2), 0, 1) * a
    return np.dstack([g[..., None] * np.array(col, np.float32), g]).astype(np.float32)
def dark_spot():
    s = 200; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    g = np.clip(1 - np.hypot(xx, yy) - noise_tex(s, s, 20, 4, .5), 0, 1) ** .8
    return np.dstack([g[..., None] * np.array([.12, .05, .06], np.float32), g * .92]).astype(np.float32)
def micro_surface(pitted):
    """thin oxide skin on metal: iridescent cells; pitted=True adds corroded holes"""
    s = 1600; r = np.random.RandomState(12); im = np.zeros((s, s, 3), np.float32)
    sub = cv2.Subdiv2D((0, 0, s, s)); pts = r.rand(260, 2) * (s - 2) + 1
    for p in pts: sub.insert((float(p[0]), float(p[1])))
    facets, _ = sub.getVoronoiFacetList([])
    pal = np.array([[.55, .62, .95], [.72, .55, .95], [.45, .85, .9], [.85, .7, .95], [.6, .75, 1.0], [.95, .75, .85]], np.float32)
    for i, f in enumerate(facets):
        c = pal[r.randint(len(pal))] * r.uniform(.55, 1.0)
        cv2.fillConvexPoly(im, f.astype(np.int32), tuple(float(v) for v in c)); cv2.polylines(im, [f.astype(np.int32)], True, (.18, .2, .32), 3, cv2.LINE_AA)
    im += noise_tex(s, s, 5, 3, .08)[..., None]
    pits = [(420, 520, 150), (980, 420, 120), (760, 980, 190), (1220, 1050, 130), (330, 1180, 110), (1150, 700, 90)]
    if pitted:
        for x, y, R in pits:
            m = np.zeros((s, s), np.float32); cv2.circle(m, (x, y), R, 1, -1); m = blur(m, 12)
            jag = np.clip((m + noise_tex(s, s, 18, x, .7)) * 3 - 1.2, 0, 1)
            rim = np.clip(blur(jag, 14) - jag * .9, 0, 1)
            im = im * (1 - jag[..., None]) + np.array([.07, .06, .08]) * jag[..., None] + rim[..., None] * np.array([.75, .78, .8])
    return np.dstack([np.clip(im, 0, 1), np.ones((s, s), np.float32)]).astype(np.float32), pits
def num_sprite(n): return pre(text_sprite(str(n), anton(300), (255, 255, 255, 255), 30))
def bone():
    s = 620; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    ang = np.arctan2(yy, xx); rr = np.hypot(xx, yy) / (0.86 + .05 * np.sin(ang * 3 + 1) + .03 * np.sin(ang * 7))
    a = np.clip((1 - rr) * 60, 0, 1)
    cell = (noise_tex(s, s, 14, 5, 1.0) + noise_tex(s, s, 30, 6, .8))
    holes = np.clip((cell - .05) * 9, 0, 1) * np.clip((.74 - rr) * 14, 0, 1)
    col = np.ones((s, s, 3), np.float32) * np.array([.93, .88, .76]); col *= (1 - .25 * np.clip(rr - .75, 0, 1) * 4)[..., None]
    col = col * (1 - holes[..., None]) + np.array([.42, .22, .12]) * holes[..., None] * (.7 + .3 * noise_tex(s, s, 4, 8, 1)[..., None])
    col *= (1.12 - .3 * (yy[..., None] + 1) / 2)
    o = np.dstack([np.clip(col, 0, 1), a]).astype(np.float32); o[..., :3] *= o[..., 3:4]
    return o, holes
def warn_tri(s):
    im = Image.new('RGBA', (s, s)); d = ImageDraw.Draw(im)
    d.polygon([(s / 2, 4), (s - 2, s - 6), (2, s - 6)], fill=(255, 205, 0), outline=(30, 30, 30), width=5)
    d.text((s / 2, s * 0.62), '!', font=anton(int(s * .55)), fill=(20, 20, 20), anchor='mm')
    return im
def msg_card():
    w, h = 900, 540; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, w - 1, h - 1], 34, fill=(250, 250, 248), outline=(215, 215, 210), width=3)
    d.text((70, 30), '↳ Forwarded many times', font=inter(30, 500), fill=(130, 130, 130))
    im.alpha_composite(warn_tri(120), (48, 100))
    d.text((185, 80), 'ALUMINIUM', font=anton(138), fill=(18, 18, 22))
    d.text((60, 232), '= CANCER!!', font=anton(138), fill=(226, 22, 30))
    d.text((60, 410), 'Throw out every aluminium pot TODAY!!', font=inter(31, 700), fill=(40, 40, 40))
    d.text((60, 452), 'Forward to all family groups', font=inter(31, 700), fill=(40, 40, 40))
    d.text((w - 40, h - 26), '9:41 pm ✓✓', font=inter(24, 500), fill=(90, 150, 200), anchor='rs')
    return im
def article(kick, l1, l2, red2=True, thumb=None):
    w, h = 760, 1080; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(240, 236, 226))
    d.text((60, 56), kick, font=inter(30, 800), fill=(200, 30, 40)); d.line([60, 104, w - 60, 104], fill=(200, 30, 40), width=4)
    d.text((60, 126), l1, font=anton(104), fill=(34, 26, 46))
    d.text((60, 250), l2, font=anton(104), fill=(196, 26, 50) if red2 else (34, 26, 46))
    y = 400
    if thumb is not None:
        d.rectangle([60, y, w - 60, y + 330], fill=(128, 110, 120))
        t = thumb.copy(); t.thumbnail((440, 280)); im.alpha_composite(t, ((w - t.width) // 2, y + 165 - t.height // 2)); y += 370
    rr = random.Random(len(l1))
    while y < h - 60:
        d.rectangle([60, y, w - 60 - rr.randint(0, 200), y + 12], fill=(120, 116, 110)); y += 34
    return im
def phone(screen, rim=(240, 80, 150)):
    sw, sh = screen.size; m = 22; w, h = sw + 2 * m, sh + 2 * m
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, w - 1, h - 1], 70, fill=rim + (255,)); rrect(d, [5, 5, w - 6, h - 6], 66, fill=(12, 12, 16, 255))
    mask = Image.new('L', (sw, sh), 0); rrect(ImageDraw.Draw(mask), [0, 0, sw - 1, sh - 1], 50, fill=255)
    im.paste(screen, (m, m), mask); rrect(d, [w // 2 - 60, m + 14, w // 2 + 60, m + 44], 15, fill=(8, 8, 10, 255))
    return im
def on_air(lit):
    w, h = 520, 230; im = Image.new('RGBA', (w + 120, h + 120)); d = ImageDraw.Draw(im)
    if lit:
        g = Image.new('RGBA', im.size); rrect(ImageDraw.Draw(g), [40, 40, w + 80, h + 80], 30, fill=(255, 30, 30, 200)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(34)))
    rrect(d, [60, 60, w + 60, h + 60], 18, fill=(40, 10, 14, 255), outline=(20, 20, 22, 255), width=10)
    if lit: rrect(d, [76, 76, w + 44, h + 44], 10, fill=(232, 22, 28, 255))
    d.text((60 + w / 2, 60 + h / 2 - 6), 'ON AIR', font=anton(150), fill=(255, 255, 255) if lit else (96, 26, 30), anchor='mm')
    return im
def bokeh_sprite(r, col):
    s = r * 2 + 40; im = Image.new('RGBA', (s, s)); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, s - 20, s - 20], fill=col + (70,), outline=col + (130,), width=4)
    return pre(im.filter(ImageFilter.GaussianBlur(5)))
def tag_img():
    w, h = 230, 430; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.line([w / 2, 0, w / 2, 90], fill=(190, 40, 40, 255), width=5)
    d.polygon([(40, 120), (w / 2, 66), (w - 40, 120), (w - 30, h - 6), (30, h - 6)], fill=(244, 240, 230, 255))
    d.polygon([(40, 120), (w / 2, 66), (w - 40, 120), (w - 37, 190), (37, 190)], fill=(206, 32, 40, 255))
    d.ellipse([w / 2 - 11, 88, w / 2 + 11, 110], fill=(60, 20, 20, 255))
    d.text((w / 2, 156), 'EVIDENCE', font=anton(40), fill=(255, 255, 255, 255), anchor='mm')
    for yy in (240, 285, 330): d.line([56, yy, w - 56, yy], fill=(180, 176, 168, 255), width=3)
    return im
def magnifier():
    w, h = 760, 900; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im); cx = cy = 250; R = 205
    hd = Image.new('RGBA', (w, h)); hdd = ImageDraw.Draw(hd)
    hdd.rounded_rectangle([cx - 30, cy + R - 6, cx + 30, cy + R + 60], 8, fill=(190, 160, 80, 255))
    hdd.rounded_rectangle([cx - 38, cy + R + 50, cx + 38, cy + R + 400], 30, fill=(96, 48, 22, 255))
    hdd.rounded_rectangle([cx - 38, cy + R + 50, cx - 12, cy + R + 400], 12, fill=(128, 70, 34, 255))
    im.alpha_composite(hd.rotate(-42, center=(cx, cy), resample=Image.BICUBIC))
    d = ImageDraw.Draw(im)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 118, 50, 255), width=30)
    d.ellipse([cx - R + 4, cy - R + 4, cx + R - 4, cy + R - 4], outline=(232, 204, 120, 255), width=9)
    g = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(g)
    gd.ellipse([cx - R + 28, cy - R + 28, cx + R - 28, cy + R - 28], fill=(255, 255, 255, 26))
    gd.arc([cx - R + 50, cy - R + 50, cx + R - 50, cy + R - 50], 200, 262, fill=(255, 255, 255, 190), width=16)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(4)))
    return im, (cx / w, cy / h), R - 28
def bag_img():
    w, h = 600, 760; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 30, w - 10, h - 10], 14, fill=(255, 255, 255, 44), outline=(255, 255, 255, 150), width=5)
    r = random.Random(2)
    for _ in range(9):
        x = r.randint(20, w - 60); y = r.randint(120, h - 160); d.line([x, y, x + r.randint(-50, 50), y + r.randint(80, 200)], fill=(255, 255, 255, r.randint(40, 110)), width=r.randint(3, 9))
    im = im.filter(ImageFilter.GaussianBlur(2.2)); d = ImageDraw.Draw(im)
    d.rectangle([10, 30, w - 10, 52], fill=(226, 30, 40, 255)); d.rectangle([10, 60, w - 10, 66], fill=(255, 255, 255, 120))
    d.rounded_rectangle([130, 300, w - 130, 470], 6, fill=(236, 230, 204, 245))
    return im
def ink_img():
    t = text_sprite('NO PROOF', anton(150), (204, 26, 38, 255), 44); d = ImageDraw.Draw(t)
    d.rounded_rectangle([10, 10, t.width - 10, t.height - 10], 14, outline=(204, 26, 38, 255), width=14)
    a = pre(t); n = np.clip(noise_tex(t.width, t.height, 3, 31, 1.4) + .95, .25, 1)[..., None]
    return a * n
def stamp_tool():
    w, h = 460, 620; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.ellipse([130, 0, 330, 200], fill=(176, 112, 52, 255)); d.ellipse([160, 20, 250, 110], fill=(214, 156, 90, 255))
    d.polygon([(190, 170), (270, 170), (300, 420), (160, 420)], fill=(150, 92, 40, 255))
    d.rounded_rectangle([40, 410, 420, 540], 16, fill=(120, 70, 30, 255)); d.rounded_rectangle([40, 410, 420, 450], 16, fill=(170, 108, 50, 255))
    d.rectangle([56, 540, 404, 590], fill=(150, 24, 30, 255))
    return im

# ---------- scene helpers ----------
class Grp:
    """group zoom: point F at zoom 1 maps to C, everything scales by Z about it"""
    def __init__(s, F, C, Z): s.F, s.C, s.Z = F, C, Z
    def __call__(s, x, y): return s.C[0] + (x - s.F[0]) * s.Z, s.C[1] + (y - s.F[1]) * s.Z
def framed(key, w=620, h=620, focus=(.5, .5), border=26, bottom=26):
    t = photo(key, w, h, focus=focus)
    im = Image.new('RGBA', (w + 2 * border, h + border + bottom), (246, 243, 234, 255))
    im.paste(Image.fromarray((t[..., :3] * 255).astype(np.uint8)), (border, border))
    return mk(pre(im))
def zoom_img(img, z, cx=W / 2, cy=H / 2):
    M = np.array([[z, 0, cx - cx * z], [0, z, cy - cy * z]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
def proj(dx, dy, s, rx, cx, cy):
    a = math.radians(rx); y3, z3 = dy * s * math.cos(a), dy * s * math.sin(a); k = 2400 / (2400 + z3)
    return cx + dx * s * k, cy + y3 * k

# ---------- ready-made soft sprites (built lazily) ----------
_SPR = {}
def spr(name):
    """'steam' (white puff), 'smoke' (dark), 'dust' (pale), 'spark' (orange glow, additive)"""
    if name not in _SPR:
        if name == 'steam':
            g = np.clip(1 - np.hypot(*np.mgrid[-1:1:300j, -1:1:300j]), 0, 1) ** 2 * .6
            _SPR[name] = np.dstack([g, g, g, g]).astype(np.float32)
        elif name == 'smoke': _SPR[name] = smoke_sprite()
        elif name == 'dust': _SPR[name] = smoke_sprite((.95, .9, .78), .8)
        elif name == 'spark': _SPR[name] = glow_sprite(14, (1.0, .6, .15))
    return _SPR[name]
def steam(c, t, x, y, n=5, op=.35, sc=1.0, kind='steam'):
    """looping rising puffs above a point"""
    for i in range(n):
        ph = (t * .45 + i / n) % 1
        place(c, spr(kind), x + math.sin(t * 1.3 + i * 2.1) * 40 * sc + (i - n / 2) * 30 * sc, y - ph * 420 * sc, (0.6 + ph * 1.4) * sc, 0, op * math.sin(ph * math.pi))
def slam(c, t, hit, o, x, y, s=1.0, rot=0):
    """object drops from above and lands at time `hit` with a dust ring; returns a shake offset (px) to roll the canvas by"""
    q = seg(t, hit - .14, hit)
    if q <= 0: return 0
    e = min(1, q) ** 2
    obj(c, o, x, lerp(y - 1500, y, e), lerp(1.9, 1.0, e) * s, rot + (1 - e) * 16, depth=1.5, lift=6 * (1 - e) + .5, rx=(1 - e) * 30)
    d = seg(t, hit, hit + .7)
    if 0 < d < 1:
        for i in range(10):
            a = i / 10 * 6.283
            place(c, spr('dust'), x + math.cos(a) * (150 + 330 * d) * s, y + 110 * s + math.sin(a) * (60 + 110 * d), (.5 + 1.4 * d) * s, i * 36, (1 - d) * .8, depth=1.5)
    return max(0, 1 - (t - hit) / .3) * 18 * math.sin((t - hit) * 85) if t > hit else 0
def splash(c, t, t0, x, y, col=(1, .8, .7)):
    q = seg(t, t0, t0 + .5)
    if 0 < q < 1: cv2.ellipse(c, (int(x), int(y)), (int(60 + 260 * q), int(24 + 100 * q)), 0, 0, 360, tuple(v * (1 - q) for v in col) + (1 - q,), max(1, int(14 * (1 - q))), cv2.LINE_AA)
def draw_on(c, strokes, t, t0, x, y, s=1.0, each=.16, depth=1.0):
    """reveal a list of stroke images one after another (cross() returns two strokes, tick() one)"""
    for i, st in enumerate(strokes if isinstance(strokes, (list, tuple)) else [strokes]):
        place(c, reveal(st, ease(seg(t, t0 + i * each, t0 + (i + 1) * each))), x, y, s, depth=depth)

# caption palettes: (top colour, bottom colour) of the big second line
RED, BLU, PNK = ((255, 195, 185), (238, 60, 66)), ((200, 220, 255), (90, 130, 255)), ((255, 170, 225), (236, 80, 170))
YLW, TEAL, ORG = ((255, 240, 170), (250, 190, 40)), ((190, 255, 240), (60, 205, 190)), ((255, 220, 170), (250, 140, 40))

class Film:
    """scenes:   [(start_time, fn)]            fn(t) -> HxWx4 (or HxWx3) float canvas
    trans:    [(t0, t1, tcut, kind)]        kind: 'h' / 'v' whip pan, 'zoom' punch-through, 'fade' blur dissolve,
                                            'flash' (white) or 'smoke' (grey) cover; tcut must equal a scene start
    captions: [(t_line1, t_line2, 'LINE ONE', 'PUNCH LINE', palette)]   each stays until the next one starts
    """
    def __init__(self, dur, scenes, trans=(), captions=(), sway=(24, 13), subframes=(0.0, 0.16, 0.32), grain=.022):
        self.dur, self.scenes, self.trans, self.sway, self.sub, self.grain = dur, sorted(scenes, key=lambda s: s[0]), list(trans), sway, subframes, grain
        self.mul, self.add = finish_overlay()
        self.caps = []
        for i, (a, b, l1, l2, col) in enumerate(captions):
            end = captions[i + 1][0] - .03 if i + 1 < len(captions) else 1e9
            self.caps.append((a, b, end, caption(l1, l2, *col)))
    def scene(self, t):
        CAM[0], CAM[1] = math.sin(t * .8) * self.sway[0], math.cos(t * .63) * self.sway[1]
        fn = [f for t0, f in self.scenes if t >= t0][-1] if t >= self.scenes[0][0] else self.scenes[0][1]
        return fn(t)[..., :3]
    def frame(self, t):
        img = self.scene(t)
        for t0, t1, tc, kind in self.trans:
            p = seg(t, t0, t1)
            if not 0 < p < 1: continue
            if kind in ('flash', 'smoke'):
                col = np.array([.95, .97, .93] if kind == 'flash' else [.3, .28, .25], np.float32)
                img = img + (col - img) * min(1, (1 - abs(p * 2 - 1)) * 1.6); continue
            a = self.scene(min(t, tc - .001)) if t >= tc else img
            b = self.scene(max(t, tc)) if t < tc else img
            if kind in ('h', 'v'):
                L = H if kind == 'v' else W; off = int(ease(p) * L); k = int(1 + 300 * math.sin(p * math.pi))
                img = cv2.blur(np.concatenate([a, b], 0)[off:off + H], (1, k)) if kind == 'v' else cv2.blur(np.concatenate([a, b], 1)[:, off:off + W], (k, 1))
            elif kind == 'zoom':
                za = 1 + 6 * p * p; a2 = (zoom_img(a, za) + zoom_img(a, za * 1.12) + zoom_img(a, za * 1.25)) / 3
                zb = lerp(1.7, 1.0, eout(p)); b2 = (zoom_img(b, zb) + zoom_img(b, zb * (1 + .12 * (1 - p)))) / 2
                m = ease(seg(p, .3, .7)); img = a2 * (1 - m) + b2 * m
            else:
                m = ease(p); r = 1 + 30 * math.sin(p * math.pi); img = blur(a, r) * (1 - m) + blur(b, r) * m
        img = img.copy(); cc = np.zeros((H, W, 4), np.float32)
        for t1, t2, tend, (l1, l2) in self.caps:
            if t < t1 or t > tend: continue
            fo = 1 - ease(seg(t, tend - .12, tend))
            o1, o2 = ease(seg(t, t1, t1 + .14)) * fo, ease(seg(t, t2, t2 + .14)) * fo
            if o1 > 0: place(cc, l1, 30, 96 + (1 - o1) * 14, 1, 0, o1, anchor=(0, 0), depth=0)
            if o2 > 0: place(cc, l2, 30, 96 + (1 - o2) * 14, 1, 0, o2, anchor=(0, 0), depth=0)
        return img * (1 - cc[..., 3:4]) + cc[..., :3]
    def render(self, i, out):
        acc = sum(self.frame(max(0, (i + s) / FPS)) for s in self.sub) / len(self.sub)   # sub-frame average = motion blur
        acc = acc * self.mul + self.add
        acc += cv2.resize(np.random.RandomState(i).randn(H // 2, W // 2).astype(np.float32) * self.grain, (W, H))[..., None]
        n = self.dur * FPS
        if i > n - 12: acc *= max(0, (n - i) / 12)
        cv2.imwrite(f'{out}/{i:05d}.jpg', cv2.cvtColor((np.clip(acc, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    def main(self, argv=None):
        """<workdir> <frames_dir> [f0 f1 [step]] : resumable (skips frames that exist), so run several ranges in parallel"""
        argv = argv or sys.argv
        out = argv[2]; os.makedirs(out, exist_ok=True)
        f0, f1 = (int(argv[3]), int(argv[4])) if len(argv) > 4 else (0, int(self.dur * FPS))
        step = int(argv[5]) if len(argv) > 5 else 1
        for i in range(f0, f1, step):
            if not os.path.exists(f'{out}/{i:05d}.jpg'): self.render(i, out)
        print('done', f0, f1, flush=True)
