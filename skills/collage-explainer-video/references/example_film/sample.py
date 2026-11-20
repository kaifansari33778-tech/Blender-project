"""2.5D cutout-collage sample (first ~11.7 s). Usage: python3 sample.py <assets_dir> <out_frames_dir> [f0 f1]"""
import sys, os, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

A, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 21.9
FONT = os.path.join(A, 'fonts')
anton = lambda s: ImageFont.truetype(f'{FONT}/Anton.ttf', s)
def inter(s, w=600):
    f = ImageFont.truetype(f'{FONT}/Inter.ttf', s)
    try: f.set_variation_by_axes([14, w])
    except Exception: pass
    return f
rnd = random.Random(7)

# ---------- helpers ----------
def pre(im):
    """PIL/np RGBA uint8 -> premultiplied float32"""
    a = np.asarray(im.convert('RGBA') if isinstance(im, Image.Image) else im).astype(np.float32) / 255
    a[..., :3] *= a[..., 3:4]
    return a
def load(n): return pre(Image.open(f'{A}/cut/{n}.png'))
def blur(img, r):
    return cv2.GaussianBlur(img, (0, 0), r) if r > 0.3 else img
def over(dst, src, op=1.0):
    if op <= 0: return
    a = src[..., 3:4] * op
    dst[..., :3] = dst[..., :3] * (1 - a) + src[..., :3] * op
    dst[..., 3:4] = dst[..., 3:4] * (1 - a) + a
CAM = [0.0, 0.0]
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

# ---------- generated art ----------
def kitchen(hob=True):
    w, h = 1500, 2500
    wall = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    wall[:] = np.array([0.07, 0.36, 0.25]) * (1.15 - 0.5 * yy[..., None])
    wall += (noise_tex(w, h, 3, 1, .05) + noise_tex(w, h, 40, 2, .09) + noise_tex(w, h, 220, 3, .10))[..., None]
    im = Image.fromarray((np.clip(wall, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    y0 = 1050
    d.rectangle([0, y0, w, y0 + 26], fill=(150, 96, 40)); d.rectangle([0, y0 + 26, w, y0 + 34], fill=(60, 36, 14))
    d.rectangle([0, y0 + 34, w, y0 + 330], fill=(176, 160, 132))
    for x in range(-40, w, 150): d.line([x, y0 + 34, x, y0 + 330], fill=(120, 108, 88), width=4)
    d.line([0, y0 + 180, w, y0 + 180], fill=(120, 108, 88), width=4)
    d.rectangle([0, y0 + 330, w, h], fill=(26, 20, 14))
    a = np.asarray(im).astype(np.float32) / 255
    a[y0 + 330:] += np.clip(noise_tex(w, h - y0 - 330, 2, 5, .5), 0, 1)[..., None] * np.array([.25, .18, .08])
    a[y0 + 34:y0 + 330] += noise_tex(w, 296, 30, 6, .08)[..., None]
    # hob
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if not hob: return np.dstack([np.asarray(im).astype(np.float32) / 255, np.ones((h, w), np.float32)])
    d.polygon([(240, 1560), (1260, 1560), (1340, 1720), (160, 1720)], fill=(16, 16, 18))
    d.rectangle([160, 1720, 1340, 1820], fill=(150, 146, 136)); d.rectangle([160, 1720, 1340, 1730], fill=(215, 212, 204))
    d.ellipse([700, 1738, 770, 1808], fill=(24, 24, 24)); d.rectangle([730, 1742, 740, 1774], fill=(120, 120, 120))
    d.ellipse([560, 1590, 940, 1690], fill=(8, 8, 8)); d.ellipse([650, 1612, 850, 1668], fill=(34, 34, 36))
    for dx, dy in ((-250, -38), (250, -38), (-290, 46), (290, 46)):
        d.line([750, 1632, 750 + dx, 1640 + dy], fill=(40, 40, 42), width=20)
    o = np.dstack([np.asarray(im).astype(np.float32) / 255, np.ones((h, w), np.float32)])
    return o
def purple():
    w, h = 1500, 2400
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); yy /= h; xx /= w
    c = np.stack([0.30 + 0.35 * xx * (1 - yy), 0.05 + 0.06 * yy, 0.50 - 0.18 * yy + 0.1 * xx], -1)
    c += noise_tex(w, h, 300, 9, .12)[..., None] + noise_tex(w, h, 3, 10, .03)[..., None]
    return np.dstack([np.clip(c, 0, 1), np.ones((h, w), np.float32)]).astype(np.float32)
def bokeh_sprite(r, col):
    s = r * 2 + 40; im = Image.new('RGBA', (s, s)); d = ImageDraw.Draw(im)
    d.ellipse([20, 20, s - 20, s - 20], fill=col + (70,), outline=col + (130,), width=4)
    return pre(im.filter(ImageFilter.GaussianBlur(5)))
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
def video_screen(pot):
    w, h = 520, 1080; im = Image.new('RGBA', (w, h), (18, 10, 30, 255)); d = ImageDraw.Draw(im)
    g = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(g); gd.ellipse([40, 380, 480, 820], fill=(255, 190, 90, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
    t = pot.copy(); t.thumbnail((400, 300)); im.alpha_composite(t, ((w - t.width) // 2, 470))
    d.rectangle([70, 190, 450, 380], fill=(225, 20, 30))
    d.text((260, 240), 'ALUMINIUM', font=anton(78), fill=(255, 255, 255), anchor='mm')
    d.text((260, 326), '= CANCER?!', font=anton(78), fill=(255, 228, 60), anchor='mm')
    d.ellipse([220, 560, 300, 640], fill=(255, 255, 255, 190)); d.polygon([(248, 578), (248, 622), (284, 600)], fill=(30, 20, 40))
    for i, y in enumerate((760, 840, 920)):
        d.ellipse([440, y, 490, y + 50], outline=(255, 255, 255), width=5)
    d.text((40, 1000), '▶ 1,349,568 views', font=inter(30, 700), fill=(255, 255, 255))
    d.text((36, 36), '9:41', font=inter(26, 700), fill=(255, 255, 255))
    return im
def chat_screen(card):
    w, h = 520, 1080; im = Image.new('RGBA', (w, h), (36, 14, 78, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 150], fill=(88, 30, 150)); d.ellipse([30, 62, 100, 132], fill=(210, 60, 120))
    d.text((120, 66), 'Family Group', font=inter(34, 800), fill=(255, 255, 255)); d.text((120, 108), 'Mum, Dad, Aunt, +9', font=inter(22, 500), fill=(210, 200, 230))
    c = card.copy(); c.thumbnail((470, 400)); im.alpha_composite(c, (24, 230))
    rrect(d, [24, 980, 420, 1050], 34, fill=(60, 34, 110)); d.ellipse([440, 980, 510, 1050], fill=(40, 190, 170))
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
def plate_img(pasta):
    w, h = 1300, 820; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.ellipse([10, 150, w - 10, h - 20], fill=(206, 204, 198)); d.ellipse([10, 130, w - 10, h - 40], fill=(246, 245, 240))
    d.ellipse([150, 215, w - 150, h - 130], fill=(226, 224, 218)); d.ellipse([160, 228, w - 160, h - 128], fill=(240, 239, 234))
    p = pasta.resize((960, int(960 * pasta.height / pasta.width)), Image.LANCZOS); im.alpha_composite(p, (170, 70))
    return im
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

print('building art', flush=True)
POT_P = Image.open(f'{A}/cut/pot.png'); PASTA_P = Image.open(f'{A}/cut/plate.png')
KIT, KIT2, PUR = kitchen(), kitchen(False), purple()
POT = pre(POT_P.resize((620, int(620 * POT_P.height / POT_P.width)), Image.LANCZOS)); POT_SH = shadow_of(cv2.copyMakeBorder(POT, 60, 60, 60, 60, cv2.BORDER_CONSTANT), 26, .7); POT_RAW = POT
POT = grade(POT_RAW, (.78, 1.0, .82), .38, rim=(.25, .5, .38), under=(.25, .55, 1.0), bot=.7)
fl = np.asarray(Image.open(f'{A}/raw/flame.jpg').convert('RGB')).astype(np.float32) / 255
fl = cv2.resize(fl, (560, 430)); fl = np.clip(fl * 1.5 - 0.06, 0, 1); FLAME = np.dstack([fl, np.zeros(fl.shape[:2], np.float32)])
PLATE = grade(pre(plate_img(PASTA_P)), (1.0, .93, .74), .45, rim=(.2, .42, .3), top=1.1, bot=.72, sat=1.12); PLATE_SH = shadow_of(cv2.copyMakeBorder(PLATE, 80, 80, 80, 80, cv2.BORDER_CONSTANT), 34, .75)
CARD_P = msg_card(); CARD = grade(pre(CARD_P), (1.0, .95, .84), .5, top=1.0, bot=.86); CARD_SH = shadow_of(cv2.copyMakeBorder(CARD, 50, 50, 50, 50, cv2.BORDER_CONSTANT), 20, .5)
HAND_P = Image.open(f'{A}/cut/hand.png')
MIC = grade(pre(Image.open(f'{A}/cut/mic1.png').resize((600, 849), Image.LANCZOS)), (.95, .55, 1.0), .6, rim=(.95, .25, .8), rim_r=9, rim_k=1.1, bot=.7, sat=.7); MIC_F = np.ascontiguousarray(MIC[:, ::-1]); MIC_B = blur(np.ascontiguousarray(MIC[:, ::-1]), 5); MIC_SH = shadow_of(cv2.copyMakeBorder(MIC, 0, 0, 0, 0, cv2.BORDER_CONSTANT), 22, .4)
ONAIR0, ONAIR1 = pre(on_air(False)), pre(on_air(True))
ART = [grade(pre(x), (1.0, .82, 1.0), .45, rim=(.8, .3, .7), rim_r=5, rim_k=.5, bot=.78) for x in (article('HEALTH ALERT', 'ALUMINIUM POTS', '= CANCER?', True, POT_P), article('MUST READ', 'IS YOUR POT', 'POISONING YOU?'), article('WARNING', 'THROW YOUR', 'POTS OUT TODAY!'))]
ART_SH = shadow_of(cv2.copyMakeBorder(ART[0], 50, 50, 50, 50, cv2.BORDER_CONSTANT), 24, .5)
VID_P = video_screen(POT_P); CHAT_P = chat_screen(CARD_P)
RIMS = [(240, 80, 150), (90, 220, 230), (250, 250, 250), (150, 110, 250), (250, 150, 60)]
PH_VID = [pre(phone(VID_P, r).resize((300, 615), Image.LANCZOS)) for r in RIMS]
PH_VID_BIG = pre(phone(VID_P, RIMS[0]))
PH_CHAT = pre(phone(CHAT_P, RIMS[1]).resize((300, 615), Image.LANCZOS))
PH_FAR = [blur(x, 2.2) * np.array([.62, .5, .8, 1], np.float32) for x in PH_VID]
PH_SH = shadow_of(cv2.copyMakeBorder(PH_VID[0], 40, 40, 40, 40, cv2.BORDER_CONSTANT), 16, .55)
BOK = [bokeh_sprite(r, c) for r, c in ((60, (255, 120, 220)), (90, (160, 120, 255)), (40, (255, 180, 240)), (120, (120, 80, 230)))]
BOKP = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.randrange(4), rnd.uniform(.3, 1), rnd.uniform(0, 6)) for _ in range(22)]
STEAM = pre(Image.fromarray((np.dstack([np.ones((300, 300, 3)) * 255, np.clip(1 - np.hypot(*np.mgrid[-1:1:300j, -1:1:300j]), 0, 1) ** 2 * 150])).astype(np.uint8), 'RGBA'))
CAPS = {k: caption(*v) for k, v in dict(
    cook=('COOKING IN', 'ALUMINIUM', (190, 215, 255), (90, 130, 255)),
    cancer=('CANCER?', 'OR A RUMOUR?', (255, 170, 215), (236, 70, 150)),
    pod=('YOU HEARD IT', 'ON PODCASTS', (255, 170, 225), (236, 80, 170)),
    art=('IN ARTICLES', 'AND VIDEOS', (255, 170, 225), (236, 80, 170)),
    claim=('ALUMINIUM COOKWARE', 'CAUSES CANCER', (255, 190, 190), (238, 60, 70)),
    throw=('SO THROW', 'IT OUT?', (255, 190, 180), (240, 70, 70)),
    simple=("BUT IT'S", 'NOT THAT SIMPLE', (200, 220, 255), (90, 130, 255)),
    proof=('SO FAR', 'NO SOLID PROOF', (255, 205, 195), (236, 62, 62))).items()}
CAPT = [('cook', 0.15, 0.95, 2.0), ('cancer', 2.05, 3.5, 5.7), ('pod', 5.75, 6.35, 7.4), ('art', 7.42, 8.39, 9.5), ('claim', 9.57, 10.35, 11.75), ('throw', 12.1, 12.85, 14.5), ('simple', 14.52, 15.28, 16.65), ('proof', 16.78, 18.45, 99)]
MUL, ADD = finish_overlay()
# phone-in-hand: rotate so the phone is upright, find the transparent screen hole
hp = HAND_P.rotate(15.6, expand=True, resample=Image.BICUBIC); hp = hp.crop(hp.getbbox())
ha = np.asarray(hp)[..., 3]
ff = (ha < 40).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(ff)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
k = max((i for i in range(1, n) if i not in border), key=lambda i: st[i, cv2.CC_STAT_AREA])
cnt = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][0]
box = cv2.boxPoints(cv2.minAreaRect(cnt)); box = box[np.argsort(box[:, 1])]
tl, tr = sorted(box[:2], key=lambda p: p[0]); bl, br = sorted(box[2:], key=lambda p: p[0])
QUAD = np.array([tl, tr, br, bl], np.float32); HAND = grade(pre(hp), (1.0, .62, .95), .5, rim=(1.0, .3, .85), rim_r=14, rim_k=.8, top=1.05, bot=.6); HSZ = hp.size
HOLE = (lab == k).astype(np.float32); HOLE = cv2.dilate(HOLE, np.ones((5, 5)))
print('hand', HSZ, QUAD.tolist(), flush=True)

# ---------- scenes ----------
def steam(dst, t, x, y, n=5, op=.35, sc=1.0):
    for i in range(n):
        ph = (t * .45 + i / n) % 1
        place(dst, STEAM, x + math.sin(t * 1.3 + i * 2.1) * 40 * sc + (i - n / 2) * 30 * sc, y - ph * 420 * sc, (0.6 + ph * 1.4) * sc, 0, op * math.sin(ph * math.pi))
def bg_pan(dst, tex, cx, cy, z):
    th, tw = tex.shape[:2]
    M = np.array([[z, 0, W / 2 - cx * z + CAM[0] * .3], [0, z, H / 2 - cy * z + CAM[1] * .3]], np.float32)
    dst[:] = cv2.warpAffine(tex, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
def s_kitchen(t):
    c = np.zeros((H, W, 4), np.float32)
    z = lerp(1.25, 1.62, ease(seg(t, 0, 2.3))); cx, cy = 750, lerp(1500, 1560, ease(seg(t, 0, 2.3)))
    bg_pan(c, KIT, cx, cy, z)
    P = lambda x, y, d=1.0: (W / 2 + (x - cx) * z * d, H / 2 + (y - cy) * z * d)
    fx, fy = P(750, 1632)
    flick = 1 + 0.05 * math.sin(t * 31) + 0.03 * math.sin(t * 47)
    place(c, FLAME, fx, fy - 6 * z, z * .78 * flick, 0, min(1, t / .25), add=True)
    if t > 0.85:
        d = back(seg(t, 0.85, 1.3), 1.2); drop = (1 - d) * -900
        px, py = P(750, 1610, 1.04)
        place(c, POT_SH, px, py + 8 * z, z * (1.0 + (1 - d) * .4), 0, .8 * ease(seg(t, .85, 1.25)), anchor=(.5, .9))
        place(c, POT, px, py + drop, z, (1 - d) * -5, 1, anchor=(.5, .97))
        sw = seg(t, 1.35, 1.9)   # light sweep across metal
        if 0 < sw < 1:
            g = np.zeros_like(POT); xs = np.arange(POT.shape[1])[None, :] - np.arange(POT.shape[0])[:, None] * .4
            band = np.exp(-((xs - lerp(-100, POT.shape[1] + 300, sw)) / 50) ** 2) * POT[..., 3]
            g[..., :3] = band[..., None] * .5
            place(c, g, px, py, z, 0, 1, add=True, anchor=(.5, .97))
        if t > 1.3: steam(c, t, px, py - POT.shape[0] * z * .95, 5, .3 * ease(seg(t, 1.3, 1.8)), z * .8)
    return c
def s_plate(t):
    c = np.zeros((H, W, 4), np.float32)
    k = ease(seg(t, 2.0, 4.8)); z = lerp(1.05, 1.2, k)
    bg_pan(c, KIT2, 750, lerp(1230, 1260, k), z * 1.5)
    c[..., :3] *= lerp(.8, .6, k)
    cx, cy = W / 2, 1010
    place(c, PLATE_SH, cx + 10, cy + 60, z * .74, 0, .9, depth=.75); place(c, PLATE, cx, cy, z * .72, lerp(-2, 1, k), depth=.8)
    steam(c, t, cx, cy - 120, 4, .22)
    for i, (t0, dx, dy, r) in enumerate(((3.95, -70, -150, -5), (3.72, 60, -75, 4), (2.45, 0, 0, -2))):
        if t > t0:
            p = back(seg(t, t0, t0 + .3)); yy = 1420 + dy + (1 - p) * 220
            wob = math.sin(t * 1.3 + i * 1.7) * 7
            place(c, CARD_SH, cx + dx + 14 + i * 6, yy + 24 + i * 8, .98 * p, r, .8, depth=1.1 + i * .25)
            place(c, CARD, cx + dx, yy, .96 * p, r + (1 - p) * 8, rx=(1 - p) * 55 + 6, ry=wob, depth=1.2 + i * .35)
    return c
def bokeh(c, t, op=1.0):
    for x, y, i, s, ph in BOKP:
        place(c, BOK[i], (x + t * 14 * s) % (W + 300) - 150, y + math.sin(t * .6 + ph) * 30, s, 0, op * (.5 + .4 * math.sin(t * 1.4 + ph)), add=True)
def s_phone(t):
    c = np.zeros((H, W, 4), np.float32)
    bg_pan(c, PUR, 750, 1200, 1.0); bokeh(c, t)
    k = eout(seg(t, 4.78, 5.35))
    # hand+phone scale: at k=0 the screen quad fills the frame
    qw = QUAD[1, 0] - QUAD[0, 0]; s0 = W / qw * 1.05; s1 = 500 / qw
    s = s0 * (s1 / s0) ** k
    qc = QUAD.mean(0); tx, ty = lerp(W / 2, 560, k), lerp(H / 2, 1000, k)
    rot = lerp(0, -4, k) + math.sin(t * 2) * .6
    cr, sr = math.cos(math.radians(rot)) * s, math.sin(math.radians(rot)) * s
    M = np.array([[cr, -sr, tx - (cr * qc[0] - sr * qc[1])], [sr, cr, ty - (sr * qc[0] + cr * qc[1])]], np.float32)
    quad = (M[:, :2] @ QUAD.T).T + M[:, 2]
    extra = [(5.2, 180, 520, -9, .82, PH_CHAT), (5.34, 900, 620, 8, .9, PH_VID[1]), (5.46, 930, 1500, 12, .7, PH_CHAT)]
    for t0, x, y, r, sc, im in extra:
        if t > t0:
            p = back(seg(t, t0, t0 + .28)); place(c, PH_SH, x + 14, y + 24, sc * p, r, .7, depth=.6); place(c, im, x, y + (1 - p) * 160, sc * p, r, rx=(1 - p) * 40, ry=(18 if x > 540 else -18) + math.sin(t * 2 + x) * 5, depth=.6)
    src = s_plate(min(t, 4.78) + (t - 4.78) * .3 if t > 4.78 else t)
    Hm = cv2.getPerspectiveTransform(np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32), quad.astype(np.float32))
    scr = cv2.warpPerspective(src, Hm, (W, H), flags=cv2.INTER_AREA)
    hole = cv2.warpAffine(HOLE, M, (W, H))
    scr *= hole[..., None]
    lay = cv2.warpAffine(HAND, M, (W, H), flags=cv2.INTER_LINEAR)
    sh = np.zeros_like(lay); sh[..., 3] = blur(np.ascontiguousarray(np.maximum(lay[..., 3], hole)), 24) * .6 * k
    over(c, np.roll(sh, (30, 18), (0, 1))); over(c, scr); over(c, lay)
    return c
def s_studio(t):
    c = np.zeros((H, W, 4), np.float32)
    drift = (t - 5.7) * 22
    bg_pan(c, PUR, 760 + drift, 1150, 1.05); c[..., 0] *= 1.15; bokeh(c, t, .5)
    # --- podcast
    up = eout(seg(t, 7.3, 7.7))            # mics leave upward
    if up < 1:
        a = eout(seg(t, 5.72, 6.2)); b = eout(seg(t, 5.85, 6.35))
        place(c, MIC_B, lerp(1700, 860, a) - drift * 1.4, 640 - up * 1500, .95, lerp(40, 14, a) + math.sin(t * 1.7) * .6, depth=.5)
        mx, my, mr = lerp(-500, 300, b) - drift * 2.2, 1060 - up * 1900, lerp(-40, -9, b) + math.sin(t * 2.2) * .8
        place(c, MIC_SH, mx + 36, my + 44, 1.2, mr, .8)
        place(c, MIC, mx, my, 1.2, mr, depth=1.8)
        p = back(seg(t, 6.2, 6.5)); lit = t > 6.62 and not (6.72 < t < 6.78)
        place(c, ONAIR1 if lit else ONAIR0, 700 - drift * 1.2, 1560 + (1 - p) * 500 + up * 900, 1.15, -3, ry=-22 + math.sin(t * 1.2) * 4, rx=6, depth=1.5)
    # --- articles
    if t > 7.3:
        out = ease(seg(t, 8.3, 8.75))
        for i, (t0, x, y, r, sc) in enumerate(((7.5, 300, 1200, -9, .86), (7.6, 800, 1230, 7, .86), (7.38, 540, 1190, -2, 1.0))):
            p = back(seg(t, t0, t0 + .38), 1.0); yy = y + (1 - p) * 1500 + out * (1700 + i * 100)
            img = ART[(i + 1) % 3] if i < 2 else ART[0]
            place(c, ART_SH, x + 22, yy + 34, sc, r + out * 14, .8, depth=.8 + i * .3); place(c, img, x, yy, sc, r + (1 - p) * 10 + out * 14, rx=(1 - p) * 45 + 8, ry=(-20, 20, 0)[i] + math.sin(t * 1.4 + i) * 5, depth=.9 + i * .4)
    # --- videos
    if t > 8.3:
        wall = eout(seg(t, 9.0, 9.9)); zz = lerp(1.0, 0.56, wall) * lerp(1, 1.1, ease(seg(t, 9.6, DUR)))
        if wall > 0:
            rr = random.Random(3); cells = [(cxn, r) for r in range(-3, 4) for cxn in range(-3, 4) if (cxn, r) != (0, 0)]
            rr.shuffle(cells)
            for j, (gx, gy) in enumerate(cells):
                t0 = 9.0 + j * .016; p = back(seg(t, t0, t0 + .3))
                if p <= 0: continue
                depth = 0.75 + rr.random() * .35; ox, oy, r = rr.uniform(-40, 40), rr.uniform(-60, 60) + (gx % 2) * 150, rr.uniform(-9, 9)
                x = W / 2 + (gx * 330 + ox) * zz * depth * 1.75; y = 1010 + (gy * 640 + oy) * zz * depth * 1.75
                place(c, (PH_FAR if depth < .9 else PH_VID)[j % 5], x, y + (1 - p) * 120, zz * depth * 1.7 * p, r + math.sin(t * 1.5 + j) * 1.2, 1, rx=rr.uniform(-14, 14) + (1 - p) * 50, ry=rr.uniform(-28, 28) + math.sin(t * 1.1 + j) * 6, depth=(depth - .6) * 3)
        p = back(seg(t, 8.38, 8.8), 1.0)
        place(c, PH_SH, W / 2 + 30, 1010 + 50 + (1 - p) * 1700, 3.0 * zz, 0, .8, depth=1.6)
        place(c, PH_VID_BIG, W / 2, 1010 + (1 - p) * 1700, 1.62 * zz, (1 - p) * 10 + math.sin(t * 1.7) * .8, rx=(1 - p) * 30 + 4, ry=math.sin(t * 1.15) * 11, depth=2.0)
    return c
# ---------- art for the throw / rewind / evidence-desk scenes ----------
def night_sky():
    w, h = 1300, 2300
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top, mid, hor = np.array([.07, .06, .19]), np.array([.30, .15, .36]), np.array([1.0, .52, .16])
    c = np.where(y < .55, top + (mid - top) * (y / .55), mid + (hor - mid) * np.clip((y - .55) / .27, 0, 1) ** 1.6) * np.ones((h, w, 1), np.float32)
    cl = cv2.resize(np.random.RandomState(4).rand(46, 9).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    cl = np.clip(cl - .52, 0, 1)[..., None] * 2.2
    c = c * (1 - cl * .55) + np.array([.42, .26, .46]) * cl * .35
    st = np.random.RandomState(5)
    for _ in range(140):
        x, yy = st.randint(0, w), st.randint(0, int(h * .5)); c[yy:yy + 2, x:x + 2] += st.rand() * .6
    return np.dstack([np.clip(c, 0, 1), np.ones((h, w), np.float32)]).astype(np.float32)
def city():
    w, h = 1700, 760; im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im); r = random.Random(11)
    for layer, col, base in ((0, (52, 30, 62), 300), (1, (22, 14, 34), 430)):
        x = -20
        while x < w:
            bw = r.randint(70, 190); bh = r.randint(120, 420 - layer * 120)
            d.rectangle([x, h - base - bh + 300, x + bw, h], fill=col + (255,))
            for wy in range(h - base - bh + 320, h - 20, 34):
                for wx in range(x + 12, x + bw - 14, 26):
                    if r.random() < .28: d.rectangle([wx, wy, wx + 10, wy + 14], fill=(255, r.randint(170, 220), 90, 255))
            x += bw + r.randint(-10, 30)
    a = pre(im); gl = blur(a, 9); a[..., :3] = np.minimum(a[..., :3] + gl[..., :3] * .5, a[..., 3:4])
    return a
def night_wall():
    k = (np.clip(KIT2[..., :3] * np.array([.42, .46, .62], np.float32), 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(k).convert('RGBA'); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 450, 380, 1050, 1000; wood, dk = (118, 74, 30, 255), (60, 36, 14, 255)
    d.rectangle([x0 - 40, y0 - 40, x1 + 40, y1 + 40], fill=wood); d.rectangle([x0 - 40, y1 + 20, x1 + 40, y1 + 62], fill=(140, 90, 38, 255))
    for sx, a, b in ((-1, x0 - 40, x0 - 190), (1, x1 + 40, x1 + 190)):
        d.polygon([(a, y0 - 40), (b, y0 - 90), (b, y1 + 90), (a, y1 + 40)], fill=(96, 60, 24, 255))
        m = (a + b) // 2; d.line([m, y0 - 50, m, y1 + 50], fill=dk, width=6)
        for yy in range(y0, y1, 120): d.line([a, yy, b, yy - 14 * sx * sx], fill=dk, width=4)
    d.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 0))
    a = pre(im)
    glow = np.zeros(a.shape[:2], np.float32); glow[y0:y1, x0:x1] = 1; glow = blur(glow, 60) * (1 - (a[..., 3] < .5))
    a[..., :3] += glow[..., None] * np.array([.30, .16, .10]) * a[..., 3:4]
    return a
def yellow():
    w, h = 1500, 2400
    c = np.ones((h, w, 3), np.float32) * np.array([.82, .62, .09])
    c += (noise_tex(w, h, 3, 21, .04) + noise_tex(w, h, 60, 22, .025) + noise_tex(w, h, 500, 23, .10))[..., None]
    return np.dstack([np.clip(c, 0, 1), np.ones((h, w), np.float32)]).astype(np.float32)
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
def text_sprite(txt, font, fill, pad=30):
    b = font.getbbox(txt); im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, font=font, fill=fill); return im
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

SKY, CITY, WALL, YEL = night_sky(), city(), night_wall(), yellow()
POT_N = grade(POT_RAW, (.5, .45, 1.0), .7, rim=(1.0, .5, .15), rim_r=12, rim_k=.9, top=.8, bot=.95, under=(1.0, .45, .1), sat=.7)
POT_IN = grade(POT_RAW, (.6, .7, 1.0), .55, rim=(.25, .3, .5), top=.95, bot=.6, sat=.8)
_pd = POT_P.resize((820, int(820 * POT_P.height / POT_P.width)), Image.LANCZOS)
POT_D = grade(pre(_pd), (1.0, .86, .5), .42, rim=(1.0, .78, .25), rim_r=10, rim_k=.6, top=1.1, bot=.72, under=(.9, .6, .05))
POT_D_SH = shadow_of(cv2.copyMakeBorder(POT_D, 80, 80, 80, 80, cv2.BORDER_CONSTANT), 30, .6)
TAG = grade(pre(tag_img()), (1.0, .9, .6), .35, bot=.85)
_m, MAG_ANCH, MAG_R = magnifier(); MAG = grade(pre(_m), (1.0, .88, .55), .3, rim=(1.0, .8, .3), rim_k=.4); MAG_SH = shadow_of(MAG, 16, .4)
BAG = pre(bag_img()); BAG_SH = shadow_of(BAG, 22, .9)
PROOF_TXT = pre(text_sprite('PROOF', ImageFont.truetype(f'{FONT}/Caveat.ttf', 150), (40, 36, 30, 255)))
INK = ink_img(); STAMP = grade(pre(stamp_tool()), (1.0, .85, .55), .3, rim=(1.0, .8, .3), rim_k=.5); STAMP_B = blur(STAMP, 7)

def throw_fwd(u):
    c = np.zeros((H, W, 4), np.float32)
    a = ease(seg(u, 11.75, 13.1)); zb = ease(seg(u, 13.05, 13.55))
    z = lerp(1.0, 1.22, a) * (1 + 7 * zb * zb)
    out = ease(seg(u, 13.3, 14.5))
    place(c, SKY, W / 2, H / 2 + lerp(-380, -120, out), 1.38 + .1 * out, depth=.15)
    place(c, CITY, W / 2, lerp(1290, 1840, out), lerp(.62, 1.12, out), anchor=(.5, 1), depth=.5)
    l = ease(seg(u, 12.5, 13.15)); wx, wy = 540, 760
    def pot():
        if u < 13.15:
            sq = math.sin(min(1, max(0, seg(u, 12.3, 12.5))) * math.pi) * .06
            px, py = lerp(540, 562, l), lerp(1245, 760, l) - math.sin(l * math.pi) * 250
            ps, pr = lerp(1.0, .30, l), l * 300
            X, Y = wx + (px - wx) * z, wy + (py - wy) * z
            if l < .35: place(c, POT_SH, X, wy + (1440 - wy) * z, z * (1 + l), 0, .8 * (1 - l / .35), anchor=(.5, .9))
            place(c, POT_IN if l < .6 else POT_N, X, Y, ps * z * (1 + sq), pr, 1, sx=1 - sq * 2, rx=l * 14, ry=l * 10)
        else:
            f = seg(u, 13.15, 14.5); e = eout(f)
            px, py = lerp(566, 640, e), lerp(760, 900, f) - math.sin(f * math.pi) * 170
            place(c, POT_N, px, py, lerp(.39, 1.12, e), 300 + f * 300, 1, rx=14 + math.sin(f * 5) * 16, ry=10 + math.sin(f * 3.1) * 18, depth=1.6)
    behind = u >= 12.95
    if behind: pot()
    wop = 1 - ease(seg(u, 13.38, 13.55))
    if wop > 0: place(c, WALL, wx, wy, .8 * z, 0, wop, anchor=(750 / 1500, 690 / 2500), depth=1.0 + zb)
    if not behind: pot()
    return c
def s_throw(t):
    if t < 14.5: return throw_fwd(t)[..., :3]
    if t < 15.42:
        img = throw_fwd(lerp(14.5, 12.28, ease(seg(t, 14.5, 15.42))))[..., :3]
        # rewind look: streaks + torn scan bands
        img = img * .8 + cv2.blur(img, (71, 1)) * .28
        r = np.random.RandomState(int(t * 30))
        for _ in range(5):
            y = r.randint(0, H - 90); hh = r.randint(14, 80)
            img[y:y + hh] = np.roll(img[y:y + hh], r.randint(-46, 46), 1) * 1.12
        return img
    k = seg(t, 15.42, 16.7); c = throw_fwd(12.28 - .3 * ease(k))
    bump = math.sin(min(1, k * 4) * math.pi) * (1 - min(1, k * 4))
    return c[..., :3] * (1 + bump * .15)
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
def s_desk(t):
    c = np.zeros((H, W, 4), np.float32); hit = 20.62
    k = ease(seg(t, 16.6, 21.9)); z = lerp(1.0, 1.07, k)
    bg_pan(c, YEL, 750, 1200 + k * 30, 1.0)
    sh = max(0, 1 - (t - hit) / .3) * 16 * math.sin((t - hit) * 80) if t > hit else 0
    e = back(seg(t, 16.66, 17.1), .9); px, py = lerp(1500, 540, e), 900 + sh
    place(c, POT_D_SH, px + 6, py + 16, 1.0 * z, 0, .9, anchor=(.5, .9), depth=.85)
    place(c, POT_D, px, py, z, lerp(8, 0, e), anchor=(.5, .97), depth=1.0)
    sw = seg(t, 17.2, 18.0)
    if 0 < sw < 1:
        g = np.zeros_like(POT_D); xs = np.arange(POT_D.shape[1])[None, :] - np.arange(POT_D.shape[0])[:, None] * .4
        g[..., :3] = (np.exp(-((xs - lerp(-100, POT_D.shape[1] + 300, sw)) / 60) ** 2) * POT_D[..., 3])[..., None] * .45
        place(c, g, px, py, z, 0, 1, add=True, anchor=(.5, .97))
    ta = ease(seg(t, 17.0, 17.15))
    if ta > 0:
        swing = 16 * math.exp(-(t - 17.0) * 1.1) * math.sin((t - 17.0) * 7) + 2.5 * math.sin(t * 1.7)
        place(c, TAG, px + 372 * z, py - 418 * z, 1.05 * z, swing, ta, anchor=(.5, 0), ry=swing * 1.5 + 8, depth=1.3)
    bp = back(seg(t, 18.4, 18.9), 1.0); bx, by = 400, 1440 + (1 - bp) * 1000 + sh
    if bp > 0:
        place(c, BAG_SH, bx + 18, by + 26, 1, -4, .5, depth=1.25)
        place(c, BAG, bx, by, 1, -4, rx=(1 - bp) * 50 + 5, ry=math.sin(t * 1.2) * 5, depth=1.3)
        place(c, PROOF_TXT, bx - 2, by + 2, .82, -4, bp * (1 - ease(seg(t, 19.45, 20.2))), depth=1.3)
        if t > hit:
            place(c, INK, bx, by + 4, .62 * (1 + .3 * max(0, 1 - (t - hit) / .1)), -11, 1, depth=1.3)
    mx, my = path(t, [(17.25, 1350, 380), (17.95, 300, 640), (19.1, 800, 700), (19.75, 850, 1420)])
    mr = lerp(-18, 6, ease(seg(t, 17.25, 19.75))) + math.sin(t * 2.3) * 1.5
    if t > 17.25:
        lens(c, mx, my, int(MAG_R * 1.0))
        place(c, MAG_SH, mx + 34, my + 46, 1, mr, .8, anchor=MAG_ANCH, depth=1.9)
        place(c, MAG, mx, my, 1, mr, anchor=MAG_ANCH, depth=2.0)
    q = seg(t, hit - .3, hit)
    if q > 0 and t < hit + .5:
        if q < 1:
            e2 = q * q; place(c, STAMP_B, lerp(900, bx + 10, e2), lerp(700, by + 50, e2), lerp(1.9, 1.0, e2), lerp(25, -11, e2), 1, anchor=(.5, .95), depth=2.2)
        else:
            u2 = ease(seg(t, hit + .08, hit + .5))
            place(c, STAMP if u2 < .3 else STAMP_B, bx + 10 + u2 * 500, by + 50 - u2 * 700, 1 + u2 * .9, -11 + u2 * 30, 1 - u2 * .6, anchor=(.5, .95), depth=2.2)
    return c
def scene(t):
    CAM[0], CAM[1] = math.sin(t * .8) * 24, math.cos(t * .63) * 13
    if t < 2.0: return s_kitchen(t)[..., :3]
    if t < 4.78: return s_plate(t)[..., :3]
    if t < 5.7: return s_phone(t)[..., :3]
    if t < 11.75: return s_studio(t)[..., :3]
    if t < 16.62: return s_throw(t)
    return s_desk(t)[..., :3]
def whip(img, t, t0, t1, tcut, vertical=False):
    wq = seg(t, t0, t1)
    if not 0 < wq < 1: return img
    a = scene(min(t, tcut - .001)) if t >= tcut else img
    b = scene(max(t, tcut)) if t < tcut else img
    L = H if vertical else W
    off = int(ease(wq) * L); k = int(1 + 300 * math.sin(wq * math.pi))
    if vertical: return cv2.blur(np.concatenate([a, b], 0)[off:off + H], (1, k))
    return cv2.blur(np.concatenate([a, b], 1)[:, off:off + W], (k, 1))
def frame(t):
    img = scene(t)
    img = whip(img, t, 11.58, 11.95, 11.75, True)
    img = whip(img, t, 16.44, 16.82, 16.62)
    # steam flash stove -> plate
    f = 1 - abs(seg(t, 1.78, 2.22) * 2 - 1)
    if f > 0: img = img + (np.array([.95, .97, .93]) - img) * min(1, f * 1.6)
    # whip phone -> studio
    wq = seg(t, 5.52, 5.9)
    if 0 < wq < 1:
        a = (s_phone(min(t, 5.699))[..., :3] if t >= 5.7 else img); b = (s_studio(max(t, 5.7))[..., :3] if t < 5.7 else img)
        off = int(ease(wq) * W); st = np.concatenate([a, b], 1)[:, off:off + W]
        img = cv2.blur(st, (int(1 + 260 * math.sin(wq * math.pi)), 1))
    img = img.copy()
    cc = np.zeros((H, W, 4), np.float32)
    for key, t1, t2, tend in CAPT:
        l1, l2 = CAPS[key]; fo = 1 - ease(seg(t, tend - .12, tend))
        o1, o2 = ease(seg(t, t1, t1 + .14)) * fo, ease(seg(t, t2, t2 + .14)) * fo
        if o1 > 0: place(cc, l1, 30, 96 + (1 - o1) * 14, 1, 0, o1, anchor=(0, 0), depth=0)
        if o2 > 0: place(cc, l2, 30, 96 + (1 - o2) * 14, 1, 0, o2, anchor=(0, 0), depth=0)
    img = img * (1 - cc[..., 3:4]) + cc[..., :3]
    return img
def render(i):
    acc = sum(frame(max(0, (i + s) / FPS)) for s in (0.0, 0.16, 0.32)) / 3
    acc = acc * MUL + ADD
    g = np.random.RandomState(i).randn(H // 2, W // 2).astype(np.float32) * .022
    acc += cv2.resize(g, (W, H))[..., None]
    if i > DUR * FPS - 9: acc *= max(0, (DUR * FPS - i) / 9)
    cv2.imwrite(f'{OUT}/{i:05d}.jpg', cv2.cvtColor((np.clip(acc, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    f0, f1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, int(DUR * FPS))
    step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    for i in range(f0, f1, step):
        if not os.path.exists(f'{OUT}/{i:05d}.jpg'): render(i)
    print('done', f0, f1, flush=True)
