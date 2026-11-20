"""Full film. Usage: python3 film.py <assets_dir> <out_frames_dir> [f0 f1 [step]]"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import sample as B
from sample import *
from film_art import *

DUR = B.DUR = 113.3
new = lambda: np.zeros((H, W, 4), np.float32)
sin = math.sin
def pop(t, t0, d=.32, k=1.4): return back(seg(t, t0, t0 + d), k)
class Grp:
    """group zoom: point F at zoom 1 maps to C, everything scales by Z about it"""
    def __init__(s, F, C, Z): s.F, s.C, s.Z = F, C, Z
    def __call__(s, x, y): return s.C[0] + (x - s.F[0]) * s.Z, s.C[1] + (y - s.F[1]) * s.Z
def framed(key, w=620, h=620, focus=(.5, .5), border=26, bottom=26):
    t = photo(key, w, h, focus=focus)
    im = Image.new('RGBA', (w + 2 * border, h + border + bottom), (246, 243, 234, 255))
    im.paste(Image.fromarray((t[..., :3] * 255).astype(np.uint8)), (border, border))
    return mk(pre(im))
def spots(c, t, pts, x, y, s=1.0):
    for dx, dy, sz, t0 in pts:
        g = ease(seg(t, t0, t0 + 1.1))
        if g > 0: place(c, SPOT, x + dx * s, y + dy * s, sz * g * s, t0 * 40, .9 * g, depth=1.4)

print('film art', flush=True)
YEL = B.YEL
MAR = flat_bg((.36, .05, .11), 31); GRN = flat_bg((.07, .38, .26), 41, n=.12); REDL = flat_bg((.55, .05, .04), 51)
TEAL = flat_bg((.05, .14, .2), 61)
DOC = mk(grade(pre(iarc_doc()), (1, .92, .7), .3, bot=.9)); HL = highlight(); MARK = mk(pre(marker()), 12, .5)
AGENCY = mk(grade(pre(agency_card()), (1, .93, .75), .25))
SCI = framed('sci', 620, 560, (.5, .4))
POTS = cut('pot', 560, amb=(1, .86, .5), s=.42, rim=(1, .78, .25), rim_k=.5, bot=.74)
CR1, CR2 = cross(); TICK = tick()
FACT = photo('factory', tint=(1, .55, .25), s=.35, contrast=1.15, vig=.5, focus=(.25, .5)); FACT_B = FACT.copy(); FACT_B[..., :3] = blur(FACT[..., :3], 16) * .75
WORK = cut('workers', 500, amb=(1, .6, .3), s=.5, rim=(1, .5, .12), rim_r=12, rim_k=1.0, top=1.0, bot=.55)
WORK_F = dict(i=np.ascontiguousarray(WORK['i'][:, ::-1]), s=np.ascontiguousarray(WORK['s'][:, ::-1]))
LUNG = cut('lungs', 600, amb=(1, .7, .5), s=.35, rim=(1, .55, .2), rim_k=.7, bot=.8)
_bl = Image.open(f'{A}/cut/bladder.png').convert('RGBA'); _ba = np.asarray(_bl).copy(); _ba[..., 3] = (np.clip((_ba[..., 3].astype(np.float32) / 255 - .6) * 3.5, 0, 1) * 255).astype(np.uint8); Image.fromarray(_ba).save(f'{A}/cut/bladder_c.png')
BLAD = cut('bladder_c', 420, amb=(1, .7, .5), s=.35, rim=(1, .55, .2), rim_k=.7, bot=.8)
SPOT = dark_spot(); DSMOKE = smoke_sprite(); DUST = smoke_sprite((.95, .9, .78), .8)
SPARK = glow_sprite(14, (1.0, .6, .15))
_fg = photo('factory', 900, 640, tint=(1, .55, .25), s=.35, focus=(.3, .4)); _yy, _xx = np.mgrid[-1:1:640j, -1:1:900j].astype(np.float32)
_fg[..., 3] = np.clip((1 - np.hypot(_xx, _yy)) * 3, 0, 1); _fg[..., :3] *= _fg[..., 3:4]; FGHOST = _fg
_pl = Image.new('RGBA', (940, 940)); _d = ImageDraw.Draw(_pl); _d.ellipse([0, 0, 939, 939], fill=(232, 230, 224, 255)); _d.ellipse([14, 14, 925, 925], fill=(250, 249, 245, 255))
_d.ellipse([120, 120, 819, 819], fill=(236, 234, 228, 255)); _d.ellipse([130, 134, 809, 813], fill=(246, 245, 240, 255))
_f = Image.open(f'{A}/cut/plate2.png').convert('RGBA'); _f = _f.resize((640, int(640 * _f.height / _f.width)), Image.LANCZOS); _pl.alpha_composite(_f, (150, 470 - _f.height // 2))
PLATE2 = mk(grade(pre(_pl), (1, .8, .75), .3, rim=(.6, .12, .2), rim_k=.5, top=1.05, bot=.85, sat=1.1), 30, .7)
TEA = cut('tea', 520, amb=(1, .8, .75), s=.3, rim=(.6, .12, .2), rim_k=.5)
FORK = cut('forkhand', 1000, amb=(1, .75, .75), s=.35, rim=(.7, .15, .25), rim_k=.6, bot=.7)
BEAD = sphere(26, (.62, .66, .72)); LBEAD = sphere(30, (.16, .17, .2), (.55, .58, .65)); GLOW = glow_sprite(90, (1.0, .95, .7)); RGLOW = glow_sprite(120, (1.0, .15, .1))
BADGE = mk(pre(badge('UNDER', '1%')))
rb = random.Random(5)
BP = [(rb.uniform(0, 6.28), rb.uniform(0, 1) ** .5 * 330, rb.uniform(0, 6)) for _ in range(100)]
GRID = [(540 - 4.5 * 78 + (i % 10) * 78, 1080 - 4.5 * 78 + (i // 10) * 78) for i in range(100)]; GI = 34
VILLI = photo('villi', tint=(1, .35, .4), s=.45, bright=.8, vig=.5)
VESSEL = photo('vessel', tint=(1, .4, .45), s=.3, vig=.4, focus=(.2, .5))
KID = cut('kidney', 640, amb=(1, .7, .7), s=.25, rim=(.7, .15, .25), rim_k=.6, bot=.85)
KID_W = cut('kidney', 640, amb=(.6, .5, .45), s=.9, sat=.25, top=.7, bot=.45)
GLOM = cut('glom', 520, amb=(1, .8, .8), s=.2)
_b, _holes = bone(); _bt = cv2.resize(photo('bonetex', 1500, 1500, focus=(0, .5))[..., :3], (620, 620), interpolation=cv2.INTER_AREA)
_b[..., :3] = (_bt * 1.05 * np.linspace(1.1, .8, 620, dtype=np.float32)[:, None, None]) * _b[..., 3:4]
_ring = np.clip(_b[..., 3] - blur(np.ascontiguousarray(_b[..., 3]), 26), 0, 1)[..., None]; _b[..., :3] = _b[..., :3] * (1 - _ring * 1.6).clip(0, 1) + np.array([.93, .88, .76], np.float32) * (_ring * 1.6).clip(0, 1) * _b[..., 3:4]
BONE = mk(grade(_b, (1, .8, .8), .25, rim=(.7, .15, .25), rim_k=.5))
rbn = random.Random(8); BSPK = [(rbn.uniform(-200, 200), rbn.uniform(-200, 200), rbn.uniform(52.2, 53.3)) for _ in range(70)]; BSPK = [p for p in BSPK if math.hypot(p[0], p[1]) < 210]
PLANK = shelf_plank()
SHELF_POTS = [cut('pot', 430, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.75), cut('moka', 250, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.75),
              cut('pcooker', 400, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.75), cut('kettle', 330, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.75),
              cut('castpot', 470, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.72), cut('redpot', 400, amb=(.8, 1, .85), s=.35, rim=(.25, .5, .38), bot=.75)]
TAG_SAFE = pre(hang_tag('SAFE', (40, 160, 80))); TAG_Q = pre(hang_tag('?', (210, 30, 40), fs=120)); TAG_WARN = pre(hang_tag('WARNING', (210, 30, 40), w=210, fs=46))
SAUCE = photo('sauce', tint=(1, .35, .25), s=.3, contrast=1.15, sat=1.25, vig=.45); SAUCE_D = SAUCE.copy(); SAUCE_D[..., :3] *= np.array([.6, .5, .5], np.float32)
TOM = cut('tomato', 620, amb=(1, .8, .7), s=.2, rim=(1, .5, .3), rim_k=.4); LEM = cut('lemon', 620, amb=(1, .85, .7), s=.2, rim=(1, .6, .3), rim_k=.4)
TAM = cut('tamarind', 520, amb=(1, .9, .6), s=.25)
SURF0, _ = micro_surface(False); SURF1, PITS = micro_surface(True)
PAN_B = cut('pan_bare', 520, amb=(1, .88, .55), s=.35, rim=(1, .78, .25), rim_k=.4); PAN_C = cut('pan_coat', 520, amb=(1, .88, .55), s=.35, rim=(1, .78, .25), rim_k=.4)
FRIDGE = photo('fridge', tint=(.5, .7, 1), s=.6, blur_r=5, bright=.85, vig=.4)
POT_F = cut('pot', 620, amb=(.6, .8, 1), s=.5, rim=(.5, .75, 1), rim_k=.6, bot=.7); GBOX = cut('glassbox', 560, amb=(.7, .85, 1), s=.4, rim=(.6, .8, 1), rim_k=.6)
T_AL = mk(grade(pre(tile('Al', '13', 'ALUMINIUM')), (1, .9, .6), .25), 26, .7); T_PB = mk(grade(pre(tile('Pb', '82', 'LEAD', False)), (1, .9, .6), .12, rim=(.9, .7, .2), rim_k=.5), 26, .7)
SCRAP = photo('scrapyard', tint=(1, .5, .3), s=.45, contrast=1.15, vig=.5, bright=.9)
MELT = photo('melt', tint=(1, .55, .3), s=.3, contrast=1.15, vig=.5); MELT_B = MELT.copy(); MELT_B[..., :3] = blur(MELT[..., :3], 12) * .7
ENG = framed('engine', 600, 450); PCB = cut('pcb', 600, amb=(1, .7, .4), s=.35, rim=(1, .5, .15), rim_k=.8)
LB_CAR = mk(pre(label_tag('OLD CAR PARTS'))); LB_EL = mk(pre(label_tag('OLD ELECTRONICS'))); LB_IN = mk(pre(label_tag('INDIA', (214, 30, 40), (255, 255, 255))))
POUR = photo('pour', tint=(1, .6, .35), s=.25, contrast=1.1, vig=.5)
CAST = cut('castpot', 760, amb=(1, .7, .45), s=.35, rim=(1, .5, .15), rim_k=.7, bot=.7)
CAST_Y = cut('castpot', 520, amb=(1, .86, .5), s=.4, rim=(1, .78, .25), rim_k=.5, bot=.72)
STUDY = mk(grade(pre(paper('RESEARCH  ·  2025', ['Lead exposure from', 'aluminium cooking pots:', 'pots from 25 countries tested'])), (1, .92, .7), .3)); PIN = pre(pin())
NOTICE = mk(grade(pre(paper('U.S. FDA  ·  PUBLIC WARNING', ['Certain imported aluminium', 'cookware may leach lead', 'into food'], bar=(20, 48, 110), h=760)), (1, .92, .7), .3))
PILE = [cut(k, w, amb=(1, .86, .5), s=.42, rim=(1, .78, .25), rim_k=.4, bot=.72) for k, w in (('pot', 250), ('castpot', 260), ('pcooker', 230), ('kettle', 200), ('redpot', 230), ('moka', 150))]
rp = random.Random(4); PILEP = []
for row, n in enumerate((7, 6, 6, 5, 4, 2)):
    for j in range(n): PILEP.append((540 + (j - (n - 1) / 2) * 150 + rp.uniform(-18, 18), 1580 - row * 105 + rp.uniform(-10, 10), rp.randrange(6), rp.uniform(-8, 8)))
NUMS = [num_sprite(n) for n in range(26)]; LB_CTRY = pre(text_sprite('COUNTRIES', anton(80), (255, 255, 255, 255)))
BIN = cut('bin', 620, amb=(.5, .6, 1), s=.5, rim=(.4, .5, .9), rim_k=.5, bot=.7); CAST_N = cut('castpot', 420, amb=(.5, .6, 1), s=.55, rim=(.4, .5, .9), rim_k=.5)
CITY2 = photo('city', 1400, 2490, tint=(.6, .6, 1), s=.3, bright=.8, vig=.5, focus=(.5, .6))
CHAT0 = pre(chat_screen(Image.new('RGBA', (10, 10))).resize((W, int(W * 1080 / 520)), Image.LANCZOS)); CHAT1 = pre(chat_screen(CARD_P).resize((W, int(W * 1080 / 520)), Image.LANCZOS))
WARN = mk(pre(warn_tri(260)))
B.SKY = photo('city', 1300, 2300, tint=(.75, .6, 1), s=.35, bright=.9, contrast=1.1, focus=(.5, .5)); B.CITY = np.zeros((4, 4, 4), np.float32)
BUBS = [mk(pre(bubble(*a)), 14, .4) for a in (('MK', (180, 60, 140), '@maria_k', 'Aluminium, always!'), ('JS', (60, 110, 200), '@james.s', 'Stainless steel for me'), ('AL', (230, 130, 40), '@ana_l', "Grandma's cast iron"))]
OUT_V = [cut('pot', 460, amb=(.8, 1, .85), s=.3, rim=(.25, .5, .38), bot=.72), cut('pan_coat', 480, amb=(.8, 1, .85), s=.3, rim=(.25, .5, .38), bot=.75), cut('castpot', 500, amb=(.8, 1, .85), s=.3, rim=(.25, .5, .38), bot=.72)]

# ---------- scenes ----------
def s_list(t):
    c = new(); k = ease(seg(t, 21.9, 29.6)); bg_pan(c, YEL, 750, 1200 + 20 * k, 1.0)
    zk = ease(seg(t, 25.0, 25.65)); Z = lerp(1, 1.7, zk); dsc, dx, dy = .9, 540, 1150
    rowy = dy + (ROW0 + ROW_AL * ROWH + ROWH / 2 - DOC_H / 2) * dsc; rowx = dx + (280 - DOC_W / 2) * dsc
    G = Grp((rowx, rowy), (lerp(rowx, 470, zk), lerp(rowy, 1240, zk)), Z)
    p = pop(t, 22.35, .45, 1.0)
    if p > 0: x, y = G(790, 520); obj(c, SCI, x + (1 - p) * 800, y, .62 * Z, 6, 1 - zk, rx=(1 - p) * 40, ry=-14 + sin(t * 1.3) * 4, depth=.8)
    p = pop(t, 23.0, .5, .9)
    if p > 0:
        x, y = G(dx, dy); obj(c, DOC, x, y - (1 - p) * 2000, dsc * Z, lerp(-9, -1.5, p), rx=(1 - p) * 50, depth=1.0)
        hp = ease(seg(t, 26.0, 26.9))
        if hp > 0:
            hx, hy = G(dx + (48 - DOC_W / 2) * dsc, rowy + 2)
            place(c, reveal(HL, hp), hx, hy, dsc * Z, -1.5, anchor=(0, .5))
        mp = ease(seg(t, 25.7, 26.0)) * (1 - ease(seg(t, 27.1, 27.5)))
        if mp > 0:
            hx, hy = G(dx + (48 - DOC_W / 2) * dsc, rowy + 2)
            obj(c, MARK, hx + hp * HL.shape[1] * dsc * Z + 110, hy + 200 + (1 - mp) * 1200, 1.1, 30, depth=1.8, lift=2)
    p = pop(t, 24.0, .4)
    if p > 0: x, y = G(420, 470); obj(c, AGENCY, x, y - (1 - p) * 900, .8 * Z, -5 + (1 - p) * 12, 1 - zk, rx=(1 - p) * 40, ry=10, depth=1.3, lift=1.6)
    p = pop(t, 28.45, .35)
    if p > 0:
        obj(c, POTS, 690, 1500 + (1 - p) * 800, 1.25, 4, depth=1.6, lift=1.8)
        place(c, reveal(CR1, ease(seg(t, 28.88, 29.03))), 690, 1500, 2.0, depth=1.6); place(c, reveal(CR2, ease(seg(t, 29.03, 29.18))), 690, 1500, 2.0, depth=1.6)
    return c
def s_factory(t):
    c = new(); k = ease(seg(t, 29.6, 36.9)); rack = ease(seg(t, 34.5, 34.95))
    bg_pan(c, FACT, 700 + 40 * k, 1245 - 30 * k, lerp(.84, .99, k))
    if rack > 0: c2 = new(); bg_pan(c2, FACT_B, 700 + 40 * k, 1245 - 30 * k, lerp(.84, .99, k)); c[:] = c * (1 - rack) + c2 * rack
    c[..., :3] *= 1 + .05 * sin(t * 23) + .03 * sin(t * 37)
    r = random.Random(1)
    for i in range(46):
        x0, sp, off, vx = r.uniform(80, 1000), r.uniform(.35, .8), r.random(), r.uniform(-260, 260)
        ph = (t * sp + off) % 1
        place(c, SPARK, x0 + vx * ph, 1250 - ph * 900 + 520 * ph * ph, r.uniform(.4, 1.1), 0, (1 - ph) * (1 - rack * .6), add=True, depth=1.5)
    for i in range(8):
        ph = (t * .2 + i / 8) % 1
        place(c, DSMOKE, 160 + i * 120 + sin(t + i * 2) * 60, 1700 - ph * 1500, 1.6 + ph * 3, i * 40, .75 * sin(ph * math.pi), depth=.7)
    p = pop(t, 30.3, .6, .8)
    if p > 0 and rack < 1:
        obj(c, WORK_F, 800, 1330 + (1 - p) * 1400 + rack * 1500, .78, depth=1.5, lift=0, sh=0)
        obj(c, WORK, 330, 1270 + (1 - p) * 1100 + rack * 1500, 1.0, depth=2.0, lift=0, sh=0)
    p = pop(t, 34.75, .4)
    if p > 0:
        obj(c, LUNG, 360, 1120 + (1 - p) * 1200, 1.0, -3, ry=sin(t * 1.2) * 7, depth=1.5)
        spots(c, t, [(-70, -40, .9, 35.2), (90, 60, 1.1, 35.5), (60, -150, .7, 35.9), (-110, 130, .8, 36.2)], 360, 1120)
    p = pop(t, 35.45, .4)
    if p > 0:
        obj(c, BLAD, 780, 1430 + (1 - p) * 1000, 1.45, 4, ry=-sin(t * 1.3) * 7, depth=1.7)
        spots(c, t, [(-20, 10, 1.0, 35.9), (90, -70, .7, 36.2)], 780, 1430)
    return c
def s_kitchen2(t):
    c = new(); k = ease(seg(t, 36.9, 40.1)); z = lerp(1.26, 1.36, k); cx, cy = 750, 1340
    bg_pan(c, KIT, cx, cy, z); P = lambda x, y: (W / 2 + (x - cx) * z, H / 2 + (y - cy) * z)
    fx, fy = P(750, 1632); px, py = P(750, 1610)
    place(c, FLAME, fx, fy - 6 * z, z * .78 * (1 + .05 * sin(t * 31)), add=True)
    place(c, POT_SH, px, py + 8 * z, z, 0, .8, anchor=(.5, .9)); place(c, POT, px, py, z, anchor=(.5, .97))
    steam(c, t, px, py - POT.shape[0] * z * .95, 5, .32, z * .8)
    g = ease(seg(t, 37.5, 37.95)) * (1 - ease(seg(t, 39.0, 39.5)))
    if g > 0:
        place(c, FGHOST, 540, 520 - (1 - g) * 60, 1.05, 0, g * .9, depth=.5)
        place(c, reveal(CR1, ease(seg(t, 38.1, 38.3))), 540, 520, 2.1, 0, g); place(c, reveal(CR2, ease(seg(t, 38.3, 38.5))), 540, 520, 2.1, 0, g)
    return c
def bead_pos(i, t):
    a, r, ph = BP[i]; return 540 + math.cos(a) * r, 1040 + math.sin(a) * r * .92 - 14 - 10 * sin(t * 2.2 + ph)
def s_food(t):
    c = new(); bg_pan(c, MAR, 750, 1200, 1.0); gk = ease(seg(t, 42.6, 43.3))
    obj(c, PLATE2, 540, 1040 + gk * 1500, 1.0, (t - 40) * 2.5, depth=.85)
    obj(c, TEA, 850 + gk * 600, 500, .62, 6, depth=.7)
    p = pop(t, 40.45, .5, 1.0)
    if p > 0: obj(c, FORK, 930 + (1 - p) * 700 + gk * 900, 1560 + (1 - p) * 300, .95, -14 + sin(t * 1.5) * 2, depth=1.9, lift=2.2)
    if gk > 0:
        for i in range(11):
            a = 540 - 5 * 78 + i * 78; b = 1080 - 5 * 78 + i * 78
            cv2.line(c, (int(a), int(1080 - 5 * 78)), (int(a), int(1080 + 5 * 78)), (.95 * gk, .8 * gk, .5 * gk, gk), 2); cv2.line(c, (int(540 - 5 * 78), int(b)), (int(540 + 5 * 78), int(b)), (.95 * gk, .8 * gk, .5 * gk, gk), 2)
    hot = ease(seg(t, 44.15, 44.5))
    for i in range(100):
        ap = pop(t, 41.0 + i * .013, .25)
        if ap <= 0: continue
        x0, y0 = bead_pos(i, t); g2 = ease(seg(t, 42.6 + i * .004, 43.15 + i * .004)); x, y = lerp(x0, GRID[i][0], g2), lerp(y0, GRID[i][1], g2) - sin(g2 * math.pi) * 120
        if i == GI and hot > 0: place(c, GLOW, x, y, 1 + .25 * sin(t * 6), 0, hot, add=True)
        place(c, BEAD, x, y, .62 * ap * (1 + .5 * hot * (i == GI)), 0, 1 if i == GI else 1 - .5 * hot, depth=1.2)
    p = pop(t, 43.3, .3)
    if p > 0: obj(c, BADGE, 850, 540, .85 * p, 7, ry=-16 + sin(t * 1.4) * 5, depth=1.6)
    return c
def s_gut(t):
    c = new(); k = ease(seg(t, 45.6, 47.3)); bg_pan(c, VILLI, 700, 1245 + 40 * k, lerp(.86, 1.0, k))
    for i in range(100):
        x, y = GRID[i]
        if i == GI:
            place(c, GLOW, x, y, 1.1 + .25 * sin(t * 6), add=True); place(c, BEAD, x, y, .95, depth=1.2); continue
        dt = t - (45.72 + (i % 10) * .03 + (9 - i // 10) * .05)
        if dt > 0: y += 2600 * dt * dt; x += sin(i) * 90 * dt
        if y < H + 60: place(c, BEAD, x, y, .62, 0, .5, depth=1.2)
    return c
def s_vessel(t):
    c = new(); k = seg(t, 47.3, 48.75); bg_pan(c, VESSEL, 560 + 300 * k, 1245, 1.0)
    x, y = lerp(180, 900, ease(k)), 960 + sin(t * 5) * 30
    place(c, GLOW, x, y, 1.3, add=True); place(c, BEAD, x, y, 1.2, depth=1.5)
    return c
def s_kidney(t):
    c = new(); bg_pan(c, MAR, 750, 1200, 1.0); p = pop(t, 48.7, .4, .8)
    obj(c, KID, 480, 900, lerp(1.5, 1.08, p), -4 + sin(t) * 1.5, depth=1.0)
    k = ease(seg(t, 48.8, 49.35)); x, y = lerp(-80, 500, k), lerp(700, 900, k) - sin(k * math.pi) * 120
    f = ease(seg(t, 49.55, 50.25))
    if f > 0: x, y = 500 + f * 60, 900 + f * 1100
    place(c, GLOW, x, y, 1.0, 0, 1 - f * .6, add=True); place(c, BEAD, x, y, .85, depth=1.4)
    p = pop(t, 49.3, .35)
    if p > 0:
        cv2.circle(c, (int(820 + CAM[0] * 1.5), int(1400 + CAM[1] * 1.5)), int(250 * p), (.98, .92, .88, 1), -1, cv2.LINE_AA)
        obj(c, GLOM, 820, 1400, .78 * p, sin(t * 1.5) * 3, depth=1.5, sh=0)
        cv2.circle(c, (int(820 + CAM[0] * 1.5), int(1400 + CAM[1] * 1.5)), int(250 * p), (.95, .75, .3, 1), 10, cv2.LINE_AA)
    return c
def s_weak(t):
    c = new(); bg_pan(c, MAR, 750, 1200, 1.0); m = ease(seg(t, 51.3, 51.9)); w = ease(seg(t, 50.55, 51.5))
    x, y = lerp(480, 330, m), lerp(900, 880, m)
    obj(c, KID, x, y, 1.08 * lerp(1, .8, m), -4, depth=1.0); obj(c, KID_W, x, y, 1.08 * lerp(1, .8, m), -4, w, depth=1.0, sh=0)
    p = pop(t, 51.5, .45, 1.0)
    if p > 0:
        bx, by = 730 + (1 - p) * 800, 1340
        obj(c, BONE, bx, by, 1.0, (1 - p) * 40 + sin(t * .9) * 2, depth=1.4)
        for dx, dy, t0 in BSPK:
            a = pop(t, t0, .2)
            if a > 0: place(c, BEAD, bx + dx, by + dy, .3 * a, 0, 1, depth=1.4); place(c, GLOW, bx + dx, by + dy, .18 * (1 + sin(t * 9 + dx)), add=True, op=.5, depth=1.4)
    return c
def shelves(c, t, G, tags=True, flip_t=55.0, only=None):
    items = [(0, 260, 0), (1, 560, 0), (2, 860, 0), (3, 240, 1), (4, 560, 1), (5, 880, 1)]
    for row, y in ((0, 830), (1, 1430)):
        x, yy = G(540, y); place(c, PLANK, x, yy, G.Z, anchor=(.5, 0), depth=.9)
    for j, (i, x, row) in enumerate(items):
        o = SHELF_POTS[i]; y = (830, 1430)[row]; hh = (o['i'].shape[0] - 2 * PAD) / 2
        X, Y = G(x, y - hh + 8); obj(c, o, X, Y, G.Z, 0, depth=1.0 + row * .25, lift=.6)
        if tags:
            fp = seg(t, flip_t + j * .13, flip_t + j * .13 + .35); sw = sin(t * 2.2 + j * 1.3) * 5
            tg, ry = (TAG_SAFE, min(1, max(0, fp)) * 2 * 90) if fp < .5 else (TAG_Q, (1 - min(1, fp)) * 2 * 90)
            tx, ty = G(x + 70, y - hh * .9); place(c, tg, tx, ty, .95 * G.Z, sw, anchor=(.5, 0), ry=ry, depth=1.3 + row * .25)
def s_shelf(t):
    c = new(); k = ease(seg(t, 53.5, 56.8)); bg_pan(c, GRN, 750 + 60 * k, 1200, 1.0)
    shelves(c, t, Grp((540, 1100), (540 + lerp(50, -50, k), 1100), lerp(.96, 1.04, k)))
    return c
def splash(c, t, t0, x, y, col=(1, .8, .7)):
    q = seg(t, t0, t0 + .5)
    if 0 < q < 1: cv2.ellipse(c, (int(x), int(y)), (int(60 + 260 * q), int(24 + 100 * q)), 0, 0, 360, tuple(v * (1 - q) for v in col) + (1 - q,), max(1, int(14 * (1 - q))), cv2.LINE_AA)
def s_sour(t):
    c = new(); k = ease(seg(t, 56.8, 60.1)); bg_pan(c, SAUCE, 700, 1245, lerp(.86, 1.02, k)); c[..., :3] *= 1 + .04 * sin(t * 9)
    for o, t0, x, y, s in ((TOM, 57.75, 400, 880, 1.15), (LEM, 58.3, 690, 1330, 1.05)):
        q = seg(t, t0, t0 + .4)
        if q > 0:
            e = min(1, q) ** 2; sink = ease(seg(t, t0 + .9, t0 + 2.4))
            obj(c, o, x, lerp(-400, y, e) + sink * 60, lerp(1.4, s, e), (1 - e) * 60 + sin(t * 1.2 + x) * 3, 1, depth=1.3, lift=2 * (1 - e) + .4)
            splash(c, t, t0 + .38, x, y + 90)
    r = random.Random(3)
    for i in range(60):
        t0 = 58.95 + r.random() * .5; x, y = r.uniform(120, 960), r.uniform(600, 1500); q = seg(t, t0, t0 + .35)
        if 0 < q: yy = lerp(-100, y, min(1, q) ** 2); s = int(7 + r.random() * 6); cv2.rectangle(c, (int(x), int(yy)), (int(x) + s, int(yy) + s), (1, 1, 1, 1) if q < 1.6 else (.9, .8, .8, .6), -1)
    return c
def proj(dx, dy, s, rx, cx, cy):
    a = math.radians(rx); y3, z3 = dy * s * math.cos(a), dy * s * math.sin(a); k = 2400 / (2400 + z3)
    return cx + dx * s * k, cy + y3 * k
def s_skin(t):
    c = new(); k = ease(seg(t, 60.1, 64.5)); bg_pan(c, REDL, 750, 900, 1.0)
    m = ease(seg(t, 60.75, 61.9)); surf = SURF0 * (1 - m) + SURF1 * m if 0 < m < 1 else (SURF1 if m >= 1 else SURF0)
    s, rx, cx, cy = lerp(1.55, 1.8, k), 60, 540, 1380
    place(c, surf, cx, cy, s, lerp(-4, 3, k), rx=rx, depth=1.0)
    hz = np.clip((np.arange(H, dtype=np.float32) - 560) / 420, 0, 1)[:, None, None]; c[..., :3] = c[..., :3] * hz + np.array([.5, .05, .05], np.float32) * (1 - hz) * (c[..., 3:4] > 0) + c[..., :3] * 0
    r = random.Random(9)
    for i in range(30):
        ph = (t * r.uniform(.15, .4) + r.random()) % 1; place(c, GLOW, r.uniform(0, W), 1000 - ph * 1000, r.uniform(.08, .2), 0, .25 * sin(ph * math.pi), add=True, depth=.5)
    if t > 62.0:
        for j, (px, py, R) in enumerate(PITS):
            X, Y = proj(px - 800, py - 800, s, rx, cx, cy)
            for n in range(7):
                ph = ((t - 62.0) * (.35 + .05 * n) + n / 7 + j * .13) % 1
                if t - 62.0 < ph / (.35 + .05 * n): continue
                place(c, BEAD, X + sin(t * 2 + n + j) * 30 + (n - 3) * 18, Y - ph * 1000, .6 + .5 * (1 - ph), 0, sin(ph * math.pi) ** .5, depth=1.2)
    return c
def s_pans(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0)
    p = pop(t, 64.55, .35); obj(c, PAN_B, 560 - (1 - p) * 1100, 800, 1.75, -4 + (1 - p) * 30, depth=1.0)
    p2 = pop(t, 64.7, .35)
    if p2 > 0: obj(c, PAN_C, 560 + (1 - p2) * 1100, 1440, 1.75, 3 - (1 - p2) * 30, depth=1.0)
    place(c, reveal(TICK, ease(seg(t, 65.25, 65.6))), 430, 1440, 1.9, depth=1.2)
    for o, t0, x, y, s in ((TOM, 65.5, 330, 760, .5), (TAM, 66.55, 500, 860, .6)):
        q = seg(t, t0, t0 + .3)
        if q > 0:
            e = min(1, q) ** 2; obj(c, o, x, lerp(-300, y, e), lerp(1.2, s, e), (1 - e) * 50, depth=1.3, lift=3 * (1 - e) + .5)
            place(c, reveal(CR1, ease(seg(t, t0 + .42, t0 + .56))), x, y, 1.2, depth=1.4); place(c, reveal(CR2, ease(seg(t, t0 + .56, t0 + .7))), x, y, 1.2, depth=1.4)
    return c
def s_fridge(t):
    c = new(); k = ease(seg(t, 67.3, 69.4)); bg_pan(c, FRIDGE, 700, 1245, lerp(.84, .92, k))
    o = ease(seg(t, 68.0, 68.5)); i = pop(t, 68.35, .45, 1.0)
    obj(c, POT_F, 540 - o * 1200, 1050, 1.1, -o * 20, depth=1.5)
    place(c, reveal(CR1, ease(seg(t, 67.62, 67.8))), 540 - o * 1200, 1050, 2.0, depth=1.5); place(c, reveal(CR2, ease(seg(t, 67.8, 67.98))), 540 - o * 1200, 1050, 2.0, depth=1.5)
    if i > 0:
        obj(c, GBOX, 540 + (1 - i) * 1200, 1080, 1.15, (1 - i) * 14, depth=1.5); place(c, reveal(TICK, ease(seg(t, 68.8, 69.1))), 540, 1080, 1.8, depth=1.6)
    return c
def slam(c, t, hit, o, x, y, s=1.0, rot=0):
    q = seg(t, hit - .14, hit)
    if q <= 0: return 0
    e = min(1, q) ** 2
    obj(c, o, x, lerp(y - 1500, y, e), lerp(1.9, s, e) * s, rot + (1 - e) * 16, depth=1.5, lift=6 * (1 - e) + .5, rx=(1 - e) * 30)
    d = seg(t, hit, hit + .7)
    if 0 < d < 1:
        for i in range(10):
            a = i / 10 * 6.283; place(c, DUST, x + math.cos(a) * (150 + 330 * d) * s, y + 110 * s + math.sin(a) * (60 + 110 * d), (.5 + 1.4 * d) * s, i * 36, (1 - d) * .8, depth=1.5)
    return max(0, 1 - (t - hit) / .3) * 18 * sin((t - hit) * 85) if t > hit else 0
def s_lead(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0); p = pop(t, 69.7, .35)
    if p > 0: obj(c, T_AL, 320, 1010 + (1 - p) * 300, .95 * p, -5, rx=22, ry=sin(t * 1.1) * 6, depth=1.0, lift=1.2)
    sh = slam(c, t, 72.0, T_PB, 770, 1030, 1.0, 4)
    if sh: c[:] = np.roll(c, int(sh), 0)
    return c
def s_scrap(t):
    c = new(); k = ease(seg(t, 72.7, 74.4)); bg_pan(c, SCRAP, 700 + 50 * k, 1245 - 60 * k, lerp(.84, 1.0, k))
    for i in range(5):
        ph = (t * .15 + i / 5) % 1; place(c, DSMOKE, 200 + i * 180, 1400 - ph * 1200, 2 + ph * 3, i * 50, .4 * sin(ph * math.pi), depth=.6)
    return c
def s_melt(t):
    c = new(); k = ease(seg(t, 74.2, 78.0)); par = ease(seg(t, 75.75, 76.1))
    bg_pan(c, MELT, 700, 1245 + 40 * k, lerp(.84, 1.02, k))
    if par > 0: c2 = new(); bg_pan(c2, MELT_B, 700, 1245 + 40 * k, lerp(.84, 1.02, k)); c[:] = c * (1 - par) + c2 * par
    c[..., :3] *= 1 + .05 * sin(t * 21)
    for i in range(6):
        ph = (t * .22 + i / 6) % 1; place(c, DSMOKE, 300 + i * 100 + sin(t + i) * 50, 1100 - ph * 1000, 1.5 + ph * 3, i * 50, .5 * sin(ph * math.pi), depth=.7)
    drop = ease(seg(t, 77.55, 77.95))
    for o, lb, t0, x, y, rr, lx in ((ENG, LB_CAR, 75.88, 400, 820, -8, 520), (PCB, LB_EL, 76.85, 680, 1380, 7, 560)):
        p = pop(t, t0, .4)
        if p > 0:
            yy = y + drop * 1600
            obj(c, o, x + (1 - p) * (-900 if x < 540 else 900), yy, 1.0 * lerp(1, .5, drop), rr + (1 - p) * 60 + drop * 90, rx=(1 - p) * 50, ry=sin(t * 1.3 + x) * 10, depth=1.7, lift=2)
            lp = pop(t, t0 + .25, .3)
            if lp > 0: obj(c, lb, lx, yy + 330, .95 * lp, -4, 1 - drop, depth=2.0, lift=1.2, ry=8)
    return c
def s_pour(t):
    c = new(); k = ease(seg(t, 78.0, 80.7)); bg_pan(c, POUR, 700 + 30 * k, 1245, lerp(.84, 1.0, k)); c[..., :3] *= 1 + .04 * sin(t * 19)
    p = pop(t, 79.35, .4)
    if p > 0:
        x, y = 540, 1330 + (1 - p) * 900; obj(c, CAST, x, y, 1.25, 0, depth=1.7, lift=1.5)
        for i, (dx, dy) in enumerate(((-220, 50), (-70, 150), (110, 80), (250, 0), (10, -30), (-290, -70), (190, 190))):
            a = pop(t, 79.6 + i * .09, .25)
            if a > 0:
                place(c, RGLOW, x + dx, y + dy, .55 + .12 * sin(t * 7 + i), 0, .6 * a, add=True, depth=1.7); place(c, LBEAD, x + dx, y + dy, 1.1 * a, depth=1.7)
    return c
def s_study(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0); ind = ease(seg(t, 84.8, 85.2))
    p = pop(t, 80.9, .45, 1.0)
    if p > 0:
        obj(c, STUDY, 770 + (1 - p) * 700, 660, .6, 5 + (1 - p) * 20, rx=(1 - p) * 40 + 4, ry=-12 + sin(t * 1.1) * 4, depth=.8, lift=1.5)
        place(c, PIN, 770 + (1 - p) * 700, 380, .9, depth=.85)
    n = int(round(25 * ease(seg(t, 81.9, 83.9)))); a = pop(t, 81.7, .3)
    if a > 0:
        place(c, NUMS[n], 250, 560, 1.0 * a, -3, depth=1.2); place(c, LB_CTRY, 250, 760, .9 * a, -3, depth=1.2)
    for i, (x, y, kind, rr) in enumerate(PILEP):
        q = seg(t, 81.6 + i * .065, 81.6 + i * .065 + .3)
        if q <= 0: continue
        e = min(1, q) ** 2; b = max(0, 1 - (q - 1) * 2.5) * abs(sin((q - 1) * 9)) * 26 if q > 1 else 0
        star = (i == 2)
        obj(c, PILE[kind], x, lerp(-200, y, e) - b, 1.0, rr + (1 - e) * 40, 1, depth=1.0 + (5 - i // 6) * .06, lift=.5) if not (star and ind > 0) else None
    if ind > 0:
        c[..., :3] *= lerp(1, .62, ind)
        x, y = lerp(PILEP[2][0], 540, ind), lerp(PILEP[2][1], 1300, ind)
        place(c, RGLOW, x, y, 5 + .5 * sin(t * 5), 0, .5 * ind, add=True, depth=1.8)
        obj(c, CAST_Y, x, y, lerp(.5, 1.25, ind), 0, depth=1.8, lift=2)
        lp = pop(t, 85.0, .3)
        if lp > 0: obj(c, LB_IN, x + 40, y + 300, 1.2 * lp, -6, depth=2.0, ry=10)
    return c
def s_fda(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0); p = pop(t, 87.6, .5, .9)
    obj(c, NOTICE, 540 + (1 - p) * 1200, 690, .95, -3 + (1 - p) * 14, rx=(1 - p) * 30 + 5, ry=(1 - p) * 40 + sin(t * 1.1) * 5, depth=.9, lift=1.6)
    for i, (x, y, s, fl) in enumerate(((250, 1400, 1.0, 1), (830, 1400, 1.0, -1), (540, 1540, 1.3, 1))):
        a = pop(t, 88.7 + i * .25, .35)
        if a > 0:
            obj(c, CAST_Y, x, y + (1 - a) * 700, s, 0, depth=1.3 + i * .2, lift=1)
            tg = pop(t, 90.0 + i * .35, .25)
            if tg > 0:
                sw = 18 * math.exp(-(t - 90.0 - i * .35) * 1.3) * sin((t - 90 - i * .35) * 8) + 3 * sin(t * 2 + i)
                place(c, TAG_WARN, x + 150 * s, y - 150 * s, .9 * tg, sw, anchor=(.5, 0), ry=sw * 1.5, depth=1.6 + i * .2)
    return c
def s_leach(t):
    c = new(); k = ease(seg(t, 92.2, 94.0)); bg_pan(c, SAUCE_D, 700, 1245, lerp(1.1, .9, k))
    r = random.Random(6)
    for i in range(40):
        sp, off, x = r.uniform(.3, .7), r.random(), r.uniform(60, 1020); ph = (t * sp + off) % 1
        place(c, RGLOW, x, 1900 - ph * 2000, .35, 0, .35 * sin(ph * math.pi), add=True, depth=1.2)
        place(c, LBEAD, x + sin(t * 2 + i) * 30, 1900 - ph * 2000, r.uniform(.5, 1.3), 0, sin(ph * math.pi) ** .5, depth=1.2)
    return c
def s_bin(t):
    c = new(); k = ease(seg(t, 94.0, 96.2)); bg_pan(c, CITY2, 700, 1100, lerp(.84, .9, k)); c[..., :3] = blur(c[..., :3], 6) * .7
    cv2.rectangle(c, (0, 1560), (W, H), (.05, .05, .09, 1), -1)
    q = seg(t, 94.45, 95.05); bx, by = 540, 1380; sh = max(0, 1 - (t - 95.05) / .35) * 14 * sin((t - 95.05) * 70) if t > 95.05 else 0
    if 0 < q < 1: e = q * q; obj(c, CAST_N, lerp(820, bx, q), lerp(-300, by - 300, e), lerp(1.2, .8, q), q * 250, depth=1.4, sh=0)
    obj(c, BIN, bx + sh, by, 1.0, sh * .15, depth=1.5)
    d = seg(t, 95.05, 95.8)
    if 0 < d < 1:
        for i in range(6): place(c, DUST, bx + (i - 2.5) * 60, by - 380 - d * 200, .8 + d * 1.5, i * 60, (1 - d) * .6, depth=1.5)
    return c
def s_next(t):
    c = new(); bg_pan(c, PUR, 750, 1200, 1.0); bokeh(c, t)
    p = pop(t, 96.25, .5, .9); qw = QUAD[1, 0] - QUAD[0, 0]; s = 560 / qw; qc = QUAD.mean(0)
    tx, ty = 560 + CAM[0], 1040 + (1 - p) * 1500 + CAM[1]; rot = -4 + sin(t * 1.6) * 1.2 + (1 - p) * 14
    cr, sr = math.cos(math.radians(rot)) * s, math.sin(math.radians(rot)) * s
    M = np.array([[cr, -sr, tx - (cr * qc[0] - sr * qc[1])], [sr, cr, ty - (sr * qc[0] + cr * qc[1])]], np.float32)
    quad = (M[:, :2] @ QUAD.T).T + M[:, 2]
    m = pop(t, 97.75, .3, 1.0); src = CHAT0 * (1 - m) + CHAT1 * m if 0 < m < 1 else (CHAT1 if m >= 1 else CHAT0)
    sh, sw = src.shape[:2]
    scr = cv2.warpPerspective(src, cv2.getPerspectiveTransform(np.array([[0, 0], [sw, 0], [sw, sh], [0, sh]], np.float32), quad.astype(np.float32)), (W, H), flags=cv2.INTER_AREA)
    hole = cv2.warpAffine(HOLE, M, (W, H)); scr *= hole[..., None]; lay = cv2.warpAffine(HAND, M, (W, H))
    shd = np.zeros_like(lay); shd[..., 3] = blur(np.ascontiguousarray(np.maximum(lay[..., 3], hole)), 24) * .6
    over(c, np.roll(shd, (30, 18), (0, 1))); over(c, scr); over(c, lay)
    return c
def s_remember(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0); hit = 101.0; p = pop(t, 99.95, .4, 1.0)
    sh = max(0, 1 - (t - hit) / .3) * 16 * sin((t - hit) * 80) if t > hit else 0
    bx, by = 540, 1080 + (1 - p) * 1300 + sh
    place(c, BAG_SH, bx + 22, by + 30, 1.3, -3, .5); place(c, BAG, bx, by, 1.3, -3, rx=(1 - p) * 40 + 5, ry=sin(t * 1.2) * 5, depth=1.2)
    if t > hit: place(c, INK, bx, by + 6, .8 * (1 + .3 * max(0, 1 - (t - hit) / .1)), -11, depth=1.2)
    q = seg(t, hit - .3, hit)
    if q > 0 and t < hit + .5:
        if q < 1: e = q * q; place(c, STAMP_B, lerp(980, bx + 10, e), lerp(500, by + 60, e), lerp(2.2, 1.25, e), lerp(25, -11, e), anchor=(.5, .95), depth=2)
        else: u = ease(seg(t, hit + .08, hit + .5)); place(c, STAMP_B if u > .3 else STAMP, bx + 10 + u * 600, by + 60 - u * 800, 1.25 + u, -11 + u * 30, 1 - u * .6, anchor=(.5, .95), depth=2)
    return c
def s_danger(t):
    c = new(); k = ease(seg(t, 102.6, 107.9)); bg_pan(c, GRN, 750 + 40 * k, 1200, 1.0)
    z = ease(seg(t, 103.4, 105.6)); G = Grp((560, 1320), (lerp(700, 540, k), lerp(1320, 1100, z)), lerp(.98, 1.85, z))
    shelves(c, t, G, tags=False)
    d = ease(seg(t, 105.6, 106.0))
    if d > 0:
        yy, xx = np.mgrid[-1:1:H * 1j, -1:1:W * 1j].astype(np.float32)
        c[..., :3] += (np.clip(xx * xx + yy * yy - .25, 0, 1) * (.45 + .15 * sin(t * 7)) * d)[..., None] * np.array([.9, .05, .05], np.float32)
        x, y = G(560, 1320); place(c, RGLOW, x, y - 150, 6, 0, .35 * d, add=True)
        obj(c, WARN, x + 10, y - 560, 1.0 * pop(t, 105.7, .3), sin(t * 3) * 4, depth=1.8)
    return c
def s_notal(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0); o = ease(seg(t, 108.3, 108.9))
    obj(c, T_AL, 540 - o * 1100, 1010, 1.0, -4 - o * 40, rx=20, ry=o * 40, depth=1.0)
    sh = slam(c, t, 109.66, T_PB, 540, 1020, 1.1, 3)
    if sh: c[:] = np.roll(c, int(sh), 0)
    return c
def s_outro(t):
    c = new(); k = ease(seg(t, 110.4, 113.3)); bg_pan(c, GRN, 750 - 30 * k, 1200, 1.0)
    place(c, PLANK, 540, 1560, 1.0, anchor=(.5, 0), depth=.9)
    for i, (o, x) in enumerate(zip(OUT_V, (250, 840, 545))):
        p = pop(t, 110.5 + i * .15, .35); hh = (o['i'].shape[0] - 2 * PAD) / 2 * 1.15
        if p > 0: obj(c, o, x, 1568 - hh + (1 - p) * 700 + (i == 2) * 6, 1.15, 0, depth=1.0 + i * .3, lift=.6)
    for i, (o, x, y) in enumerate(zip(BUBS, (500, 580, 520), (560, 740, 920))):
        p = pop(t, 112.15 + i * .26, .3)
        if p > 0: obj(c, o, x, y + (1 - p) * 60, 1.25 * p, (-2, 2, -1)[i], rx=(1 - p) * 40, ry=sin(t * 1.4 + i) * 6, depth=1.6 + i * .2, lift=1.4)
    return c

SCENES = [(21.9, s_list), (29.62, s_factory), (36.9, s_kitchen2), (40.1, s_food), (45.6, s_gut), (47.3, s_vessel), (48.75, s_kidney), (50.3, s_weak),
          (53.5, s_shelf), (56.8, s_sour), (60.1, s_skin), (64.5, s_pans), (67.3, s_fridge), (69.4, s_lead), (72.7, s_scrap), (74.3, s_melt),
          (78.0, s_pour), (80.7, s_study), (87.4, s_fda), (92.2, s_leach), (94.0, s_bin), (96.2, s_next), (99.9, s_remember), (102.6, s_danger),
          (107.9, s_notal), (110.4, s_outro)]
def scene(t):
    if t < 21.9: return B.scene(t)
    CAM[0], CAM[1] = sin(t * .8) * 24, math.cos(t * .63) * 13
    fn = [f for t0, f in SCENES if t >= t0][-1]
    return fn(t)[..., :3]
def zoom_img(img, z, cx=W / 2, cy=H / 2):
    M = np.array([[z, 0, cx - cx * z], [0, z, cy - cy * z]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
TRANS = [(21.72, 22.1, 21.9, 'v'), (29.3, 29.95, 29.62, 'zoom'), (36.65, 37.15, 36.9, 'smoke'), (39.93, 40.3, 40.1, 'h'), (47.08, 47.52, 47.3, 'zoom'),
         (48.55, 48.95, 48.75, 'zoom'), (53.32, 53.7, 53.5, 'h'), (56.6, 57.0, 56.8, 'zoom'), (59.88, 60.32, 60.1, 'zoom'), (64.32, 64.7, 64.5, 'v'),
         (67.12, 67.48, 67.3, 'h'), (69.22, 69.58, 69.4, 'h'), (72.52, 72.9, 72.7, 'v'), (74.05, 74.55, 74.3, 'fade'), (77.8, 78.2, 78.0, 'zoom'),
         (80.52, 80.9, 80.7, 'v'), (87.22, 87.58, 87.4, 'h'), (91.98, 92.42, 92.2, 'zoom'), (93.82, 94.18, 94.0, 'h'), (96.02, 96.4, 96.2, 'v'),
         (99.72, 100.08, 99.9, 'h'), (102.42, 102.8, 102.6, 'v'), (107.72, 108.08, 107.9, 'h'), (110.22, 110.58, 110.4, 'v')]
def frame(t):
    img = scene(t)
    if t < 21.5:
        f = 1 - abs(seg(t, 1.78, 2.22) * 2 - 1)
        if f > 0: img = img + (np.array([.95, .97, .93]) - img) * min(1, f * 1.6)
        B_scene = B.scene
        for a, b, cut_, v in ((5.52, 5.9, 5.7, False), (11.58, 11.95, 11.75, True), (16.44, 16.82, 16.62, False)):
            img = B.whip(img, t, a, b, cut_, v)
    for t0, t1, tc, kind in TRANS:
        p = seg(t, t0, t1)
        if not 0 < p < 1: continue
        if kind == 'smoke':
            f = 1 - abs(p * 2 - 1); img = img + (np.array([.3, .28, .25]) - img) * min(1, f * 1.5); continue
        a = scene(min(t, tc - .001)) if t >= tc else img; b = scene(max(t, tc)) if t < tc else img
        if kind in 'hv':
            L = H if kind == 'v' else W; off = int(ease(p) * L); kk = int(1 + 300 * sin(p * math.pi))
            img = cv2.blur(np.concatenate([a, b], 0)[off:off + H], (1, kk)) if kind == 'v' else cv2.blur(np.concatenate([a, b], 1)[:, off:off + W], (kk, 1))
        elif kind == 'zoom':
            za = 1 + 6 * p * p; a2 = (zoom_img(a, za) + zoom_img(a, za * 1.12) + zoom_img(a, za * 1.25)) / 3
            zb = lerp(1.7, 1.0, eout(p)); b2 = (zoom_img(b, zb) + zoom_img(b, zb * (1 + .12 * (1 - p)))) / 2
            m = ease(seg(p, .3, .7)); img = a2 * (1 - m) + b2 * m
        else:
            m = ease(p); r = 1 + 30 * sin(p * math.pi); img = blur(a, r) * (1 - m) + blur(b, r) * m
    img = img.copy(); cc = np.zeros((H, W, 4), np.float32)
    for key, t1, t2, tend in CAPT:
        if t < t1 or t > tend: continue
        l1, l2 = CAPS[key]; fo = 1 - ease(seg(t, tend - .12, tend))
        o1, o2 = ease(seg(t, t1, t1 + .14)) * fo, ease(seg(t, t2, t2 + .14)) * fo
        if o1 > 0: place(cc, l1, 30, 96 + (1 - o1) * 14, 1, 0, o1, anchor=(0, 0), depth=0)
        if o2 > 0: place(cc, l2, 30, 96 + (1 - o2) * 14, 1, 0, o2, anchor=(0, 0), depth=0)
    return img * (1 - cc[..., 3:4]) + cc[..., :3]

RED, BLU, PNK, YLW, TEA_, ORG = ((255, 195, 185), (238, 60, 66)), ((200, 220, 255), (90, 130, 255)), ((255, 170, 225), (236, 80, 170)), ((255, 240, 170), (250, 190, 40)), ((190, 255, 240), (60, 205, 190)), ((255, 220, 170), (250, 140, 40))
NEWCAPS = [(22.3, 25.2, "HERE'S THE SURPRISE", "IT'S ON WHO'S CANCER LIST", RED), (28.43, 28.88, 'BUT NOT', 'THE POT', RED), (29.86, 30.5, 'NOT THE POT', 'THE FACTORY', ORG),
           (32.12, 33.19, 'WORKERS BREATHED', 'FURNACE FUMES', YLW), (34.7, 35.3, 'AND DEVELOPED', 'LUNG & BLADDER CANCER', YLW), (37.07, 38.15, 'YOUR POT', 'NO FURNACE, NO FUMES', BLU),
           (40.29, 41.4, "A DAY'S FOOD", 'HAS ALUMINIUM', TEA_), (42.8, 44.23, 'LESS THAN 1%', 'REACHES YOUR BLOOD', RED), (45.75, 46.37, 'THE REST', 'LEAVES YOUR BODY', TEA_),
           (47.46, 48.87, 'WHAT GETS IN', 'KIDNEYS FILTER IT', TEA_), (50.52, 52.37, 'WEAK KIDNEYS', 'IT CAN BUILD UP', RED), (53.77, 55.3, 'BUT NOT EVERY POT', 'IS SAFE', RED),
           (57.06, 57.8, 'FIRST', 'SOUR + SALTY FOOD', BLU), (59.34, 60.19, 'EATS AWAY', 'THE THIN SKIN', TEA_), (62.14, 63.0, 'ALUMINIUM', 'SEEPS INTO FOOD', TEA_),
           (64.79, 65.5, 'UNCOATED POT', 'NO TOMATO, NO TAMARIND', RED), (67.4, 68.3, "DON'T COOK IN IT", "DON'T STORE IN IT", BLU), (69.65, 71.99, '2. THE BIGGER ONE', 'LEAD', RED),
           (72.85, 73.9, 'CHEAP POTS', 'CAST FROM SCRAP', ORG), (75.86, 76.85, 'OLD CAR PARTS', 'OLD ELECTRONICS', ORG), (78.19, 79.5, "THE SCRAP'S LEAD", 'STAYS IN THE POT', TEA_),
           (80.97, 82.9, 'A 2025 STUDY', '25 COUNTRIES', RED), (84.86, 85.9, 'AMONG THE MOST LEAD', 'INDIA', RED), (87.6, 89.0, 'THE US FDA', 'WARNED', RED),
           (92.37, 92.9, 'LEAD', 'LEACHES INTO FOOD', TEA_), (94.14, 95.11, 'THE ADVICE', 'THROW THEM AWAY', RED), (96.72, 97.8, 'NEXT TIME', 'SOMEONE SAYS...', PNK),
           (100.02, 100.89, 'REMEMBER', 'NO SOLID PROOF', RED), (102.75, 105.71, 'A SCRAP-CAST POT?', 'THE REAL DANGER', RED), (108.22, 109.62, 'NOT ALUMINIUM', "IT'S LEAD", RED),
           (110.66, 112.17, 'WHAT DO YOU COOK IN?', 'TELL US IN THE COMMENTS', PNK)]
CAPT = [(k, a, b, 21.85 if k == 'proof' else e) for k, a, b, e in B.CAPT]
for i, (a, b, l1, l2, col) in enumerate(NEWCAPS):
    CAPS[f'n{i}'] = caption(l1, l2, *col); CAPT.append((f'n{i}', a, b, NEWCAPS[i + 1][0] - .03 if i + 1 < len(NEWCAPS) else 999))
def render(i, out):
    acc = sum(frame(max(0, (i + s) / FPS)) for s in (0.0, 0.16, 0.32)) / 3
    acc = acc * MUL + ADD
    g = np.random.RandomState(i).randn(H // 2, W // 2).astype(np.float32) * .022
    acc += cv2.resize(g, (W, H))[..., None]
    if i > DUR * FPS - 12: acc *= max(0, (DUR * FPS - i) / 12)
    cv2.imwrite(f'{out}/{i:05d}.jpg', cv2.cvtColor((np.clip(acc, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    f0, f1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, int(DUR * FPS))
    step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    for i in range(f0, f1, step):
        if not os.path.exists(f'{OUT}/{i:05d}.jpg'): render(i, OUT)
    print('done', f0, f1, flush=True)
