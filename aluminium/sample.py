"""2.5D cutout-collage sample (first ~11.7 s). Usage: python3 sample.py <assets_dir> <out_frames_dir> [f0 f1]"""
import sys, os, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

A, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 11.7
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
def place(dst, img, cx, cy, s=1.0, rot=0.0, op=1.0, sx=None, add=False, anchor=(0.5, 0.5)):
    """draw img with its anchor at (cx,cy), uniform scale s, rotation deg"""
    if op <= 0 or s <= 0: return
    h, w = img.shape[:2]
    ax, ay = w * anchor[0], h * anchor[1]
    c, sn = math.cos(math.radians(rot)) * s, math.sin(math.radians(rot)) * s
    kx = (sx or 1.0)
    M = np.array([[c * kx, -sn, cx - (c * kx * ax - sn * ay)], [sn * kx, c, cy - (sn * kx * ax + c * ay)]], np.float32)
    lay = cv2.warpAffine(img, M, (dst.shape[1], dst.shape[0]), flags=cv2.INTER_AREA if s < 0.6 else cv2.INTER_LINEAR)
    if add: dst[..., :3] += lay[..., :3] * op
    else: over(dst, lay, op)
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
    im = Image.new('RGBA', (w, h)); line(l2, anton(116), 118, c_top, c_bot, tuple(int(v * .8) for v in c_bot)) if l2 else None
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
POT = pre(POT_P.resize((620, int(620 * POT_P.height / POT_P.width)), Image.LANCZOS)); POT_SH = shadow_of(cv2.copyMakeBorder(POT, 60, 60, 60, 60, cv2.BORDER_CONSTANT), 26, .7)
fl = np.asarray(Image.open(f'{A}/raw/flame.jpg').convert('RGB')).astype(np.float32) / 255
fl = cv2.resize(fl, (560, 430)); fl = np.clip(fl * 1.5 - 0.06, 0, 1); FLAME = np.dstack([fl, np.zeros(fl.shape[:2], np.float32)])
PLATE = pre(plate_img(PASTA_P)); PLATE_SH = shadow_of(cv2.copyMakeBorder(PLATE, 80, 80, 80, 80, cv2.BORDER_CONSTANT), 34, .75)
CARD_P = msg_card(); CARD = pre(CARD_P); CARD_SH = shadow_of(cv2.copyMakeBorder(CARD, 50, 50, 50, 50, cv2.BORDER_CONSTANT), 20, .5)
HAND_P = Image.open(f'{A}/cut/hand.png')
MIC = pre(Image.open(f'{A}/cut/mic1.png').resize((600, 849), Image.LANCZOS)); MIC_F = np.ascontiguousarray(MIC[:, ::-1]); MIC_B = blur(np.ascontiguousarray(MIC[:, ::-1]), 5); MIC_SH = shadow_of(cv2.copyMakeBorder(MIC, 0, 0, 0, 0, cv2.BORDER_CONSTANT), 22, .4)
ONAIR0, ONAIR1 = pre(on_air(False)), pre(on_air(True))
ART = [pre(article('HEALTH ALERT', 'ALUMINIUM POTS', '= CANCER?', True, POT_P)), pre(article('MUST READ', 'IS YOUR POT', 'POISONING YOU?')), pre(article('WARNING', 'THROW YOUR', 'POTS OUT TODAY!'))]
ART_SH = shadow_of(cv2.copyMakeBorder(ART[0], 50, 50, 50, 50, cv2.BORDER_CONSTANT), 24, .5)
VID_P = video_screen(POT_P); CHAT_P = chat_screen(CARD_P)
RIMS = [(240, 80, 150), (90, 220, 230), (250, 250, 250), (150, 110, 250), (250, 150, 60)]
PH_VID = [pre(phone(VID_P, r).resize((300, 615), Image.LANCZOS)) for r in RIMS]
PH_VID_BIG = pre(phone(VID_P, RIMS[0]))
PH_CHAT = pre(phone(CHAT_P, RIMS[1]).resize((300, 615), Image.LANCZOS))
PH_SH = shadow_of(cv2.copyMakeBorder(PH_VID[0], 40, 40, 40, 40, cv2.BORDER_CONSTANT), 16, .55)
BOK = [bokeh_sprite(r, c) for r, c in ((60, (255, 120, 220)), (90, (160, 120, 255)), (40, (255, 180, 240)), (120, (120, 80, 230)))]
BOKP = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.randrange(4), rnd.uniform(.3, 1), rnd.uniform(0, 6)) for _ in range(22)]
STEAM = pre(Image.fromarray((np.dstack([np.ones((300, 300, 3)) * 255, np.clip(1 - np.hypot(*np.mgrid[-1:1:300j, -1:1:300j]), 0, 1) ** 2 * 150])).astype(np.uint8), 'RGBA'))
CAPS = {k: caption(*v) for k, v in dict(
    cook=('COOKING IN', 'ALUMINIUM', (190, 215, 255), (90, 130, 255)),
    cancer=('CANCER?', 'OR A RUMOUR?', (255, 170, 215), (236, 70, 150)),
    pod=('YOU HEARD IT', 'ON PODCASTS', (255, 170, 225), (236, 80, 170)),
    art=('IN ARTICLES', 'AND VIDEOS', (255, 170, 225), (236, 80, 170)),
    claim=('ALUMINIUM COOKWARE', 'CAUSES CANCER', (255, 190, 190), (238, 60, 70))).items()}
CAPT = [('cook', 0.15, 0.95, 2.0), ('cancer', 2.05, 3.5, 5.7), ('pod', 5.75, 6.35, 7.4), ('art', 7.42, 8.39, 9.5), ('claim', 9.57, 10.35, 99)]
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
QUAD = np.array([tl, tr, br, bl], np.float32); HAND = pre(hp); HSZ = hp.size
HOLE = (lab == k).astype(np.float32); HOLE = cv2.dilate(HOLE, np.ones((5, 5)))
print('hand', HSZ, QUAD.tolist(), flush=True)

# ---------- scenes ----------
def steam(dst, t, x, y, n=5, op=.35, sc=1.0):
    for i in range(n):
        ph = (t * .45 + i / n) % 1
        place(dst, STEAM, x + math.sin(t * 1.3 + i * 2.1) * 40 * sc + (i - n / 2) * 30 * sc, y - ph * 420 * sc, (0.6 + ph * 1.4) * sc, 0, op * math.sin(ph * math.pi))
def bg_pan(dst, tex, cx, cy, z):
    th, tw = tex.shape[:2]
    M = np.array([[z, 0, W / 2 - cx * z], [0, z, H / 2 - cy * z]], np.float32)
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
    place(c, PLATE_SH, cx + 10, cy + 60, z * .74, 0, .9); place(c, PLATE, cx, cy, z * .72, lerp(-2, 1, k))
    steam(c, t, cx, cy - 120, 4, .22)
    for i, (t0, dx, dy, r) in enumerate(((3.95, -70, -150, -5), (3.72, 60, -75, 4), (2.45, 0, 0, -2))):
        if t > t0:
            p = back(seg(t, t0, t0 + .3)); yy = 1420 + dy + (1 - p) * 220
            place(c, CARD_SH, cx + dx + 12, yy + 22, .98 * p, r, .8)
            place(c, CARD, cx + dx, yy, .96 * p * (1 + .01 * math.sin(t * 2 + i)), r + (1 - p) * 8)
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
            p = back(seg(t, t0, t0 + .28)); place(c, PH_SH, x + 14, y + 24, sc * p, r, .7); place(c, im, x, y + (1 - p) * 160, sc * p, r)
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
        place(c, MIC_B, lerp(1700, 860, a) - drift * 1.4, 640 - up * 1500, .95, lerp(40, 14, a) + math.sin(t * 1.7) * .6)
        mx, my, mr = lerp(-500, 300, b) - drift * 2.2, 1060 - up * 1900, lerp(-40, -9, b) + math.sin(t * 2.2) * .8
        place(c, MIC_SH, mx + 36, my + 44, 1.2, mr, .8)
        place(c, MIC, mx, my, 1.2, mr)
        p = back(seg(t, 6.2, 6.5)); lit = t > 6.62 and not (6.72 < t < 6.78)
        place(c, ONAIR1 if lit else ONAIR0, 700 - drift * 1.2, 1560 + (1 - p) * 500 + up * 900, 1.15, -3)
    # --- articles
    if t > 7.3:
        out = ease(seg(t, 8.3, 8.75))
        for i, (t0, x, y, r, sc) in enumerate(((7.5, 300, 1200, -9, .86), (7.6, 800, 1230, 7, .86), (7.38, 540, 1190, -2, 1.0))):
            p = back(seg(t, t0, t0 + .38), 1.0); yy = y + (1 - p) * 1500 + out * (1700 + i * 100)
            img = ART[(i + 1) % 3] if i < 2 else ART[0]
            place(c, ART_SH, x + 16, yy + 26, sc, r + out * 14, .8); place(c, img if i == 2 else blur(img, 0), x, yy, sc, r + (1 - p) * 10 + out * 14)
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
                place(c, PH_VID[j % 5], x, y + (1 - p) * 120, zz * depth * 1.7 * p, r + math.sin(t * 1.5 + j) * 1.2, min(1, depth))
        p = back(seg(t, 8.38, 8.8), 1.0)
        place(c, PH_SH, W / 2 + 20, 1010 + 40 + (1 - p) * 1700, 3.0 * zz, 0, .7)
        place(c, PH_VID_BIG, W / 2, 1010 + (1 - p) * 1700, 1.62 * zz, (1 - p) * 10 + math.sin(t * 1.7) * .8)
    return c
def frame(t):
    if t < 2.0: c = s_kitchen(t)
    elif t < 4.78: c = s_plate(t)
    elif t < 5.7: c = s_phone(t)
    else: c = s_studio(t)
    img = c[..., :3]
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
        if o1 > 0: place(cc, l1, 30, 96 + (1 - o1) * 14, 1, 0, o1, anchor=(0, 0))
        if o2 > 0: place(cc, l2, 30, 96 + (1 - o2) * 14, 1, 0, o2, anchor=(0, 0))
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
