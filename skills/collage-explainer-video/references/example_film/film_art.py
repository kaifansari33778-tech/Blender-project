"""Generated art + asset loading for the full film (imported by film.py)."""
import os, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sample as B
from sample import (A, W, H, FONT, anton, inter, pre, blur, shadow_of, grade, noise_tex, text_sprite, place, over, lerp, ease)

caveat = lambda s: ImageFont.truetype(f'{FONT}/Caveat.ttf', s)
PAD = 70
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

# ---------- documents ----------
ROWS = [('Acetaldehyde (from alcoholic beverages)', '1'), ('Aflatoxins', '1'), ('Alcoholic beverages', '1'), ('Aluminium production', '1'),
        ('Arsenic and inorganic arsenic compounds', '1'), ('Asbestos (all forms)', '1'), ('Benzene', '1'), ('Coal, indoor emissions', '1'),
        ('Diesel engine exhaust', '1'), ('Formaldehyde', '1'), ('Outdoor air pollution', '1'), ('Processed meat', '1'),
        ('Solar radiation', '1'), ('Tobacco smoking', '1'), ('Wood dust', '1')]
DOC_W, DOC_H, ROW0, ROWH = 940, 1320, 300, 62
def iarc_doc():
    im = Image.new('RGBA', (DOC_W, DOC_H), (243, 238, 224, 255)); d = ImageDraw.Draw(im)
    d.text((60, 60), 'Agents classified by the', font=inter(34, 500), fill=(60, 56, 50))
    d.text((60, 104), 'IARC Monographs', font=inter(58, 800), fill=(28, 26, 24))
    d.text((60, 186), 'Group 1  —  carcinogenic to humans', font=inter(30, 600), fill=(150, 40, 40))
    d.line([60, 250, DOC_W - 60, 250], fill=(40, 40, 40), width=4)
    d.text((60, 258), 'Agent', font=inter(24, 700), fill=(90, 90, 90)); d.text((DOC_W - 60, 258), 'Group', font=inter(24, 700), fill=(90, 90, 90), anchor='ra')
    for i, (n, g) in enumerate(ROWS):
        y = ROW0 + i * ROWH
        d.text((60, y + 12), n, font=inter(33, 500), fill=(34, 32, 30)); d.text((DOC_W - 80, y + 12), g, font=inter(33, 700), fill=(34, 32, 30), anchor='ra')
        d.line([60, y + ROWH - 2, DOC_W - 60, y + ROWH - 2], fill=(200, 194, 180), width=2)
    return im
ROW_AL = 3
def highlight(wd=440, col=(70, 230, 110, 150)):
    im = Image.new('RGBA', (wd, 62)); d = ImageDraw.Draw(im); d.rounded_rectangle([0, 6, wd - 1, 56], 14, fill=col)
    return pre(im.filter(ImageFilter.GaussianBlur(1.5)))
def marker(col=(40, 190, 90)):
    w, h = 130, 620; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.polygon([(45, 0), (85, 0), (95, 70), (35, 70)], fill=col + (255,)); d.rounded_rectangle([25, 66, 105, 150], 10, fill=(30, 30, 30, 255))
    d.rounded_rectangle([18, 140, 112, h - 4], 22, fill=col + (255,)); d.rounded_rectangle([18, 140, 50, h - 4], 16, fill=tuple(min(255, v + 60) for v in col) + (255,))
    return im
def agency_card():
    w, h = 760, 250; im = Image.new('RGBA', (w, h), (250, 250, 246, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 22, h], fill=(0, 130, 150, 255))
    d.text((60, 44), 'International Agency for', font=inter(38, 600), fill=(0, 110, 130)); d.text((60, 92), 'Research on Cancer', font=inter(52, 800), fill=(0, 96, 116))
    d.text((60, 172), "The World Health Organization's cancer agency", font=inter(28, 500), fill=(90, 90, 90))
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
def smoke_sprite(col=(.12, .1, .09), a=.6):
    s = 360; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    g = np.clip(1 - np.hypot(xx, yy), 0, 1) ** 1.6 * np.clip(.6 + noise_tex(s, s, 40, 9, 1.2), 0, 1) * a
    return np.dstack([g[..., None] * np.array(col, np.float32), g]).astype(np.float32)
def dark_spot():
    s = 200; yy, xx = np.mgrid[-1:1:s * 1j, -1:1:s * 1j].astype(np.float32)
    g = np.clip(1 - np.hypot(xx, yy) - noise_tex(s, s, 20, 4, .5), 0, 1) ** .8
    return np.dstack([g[..., None] * np.array([.12, .05, .06], np.float32), g * .92]).astype(np.float32)
def num_sprite(n): return pre(text_sprite(str(n), anton(300), (255, 255, 255, 255), 30))
