"""El Chapo - full video (Documentary Template 1, Mexico grade), timed word-by-word to voice/full.mp3.
Usage: python3 show.py stills <dir> t1,t2  |  render <outdir> [a-b]  |  mux <outdir> <out.mp4>"""
import sys, os, math, json, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art
from voxkit.film import *
from voxkit import film

PH = os.path.join(HERE, 'photos'); P = lambda f: os.path.join(PH, f)
VOICE = P('../voice/full.mp3')
T = timeline(json.load(open(os.path.join(HERE, 'voice', 'words.json'))))
DUR = 118.4
WHITE = np.array([.95, .93, .86], np.float32); RED = art.RED; GLOW_RED = (0.95, 0.06, 0.04); BLUE = np.array([.15, .25, .65], np.float32)


def WM(key):
    f = sorted(glob.glob(os.path.join(PH, 'wm', key + '_0.*')))
    f = [x for x in f if not x.endswith('.svg') and cv2.imread(x, cv2.IMREAD_UNCHANGED) is not None]
    return f[0] if f else None


def _outlined(spr, px=9, col=(.05, .03, .03)):
    a = spr[..., 3]; o = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1)))
    out = np.zeros_like(spr); out[..., :3] = col; out[..., 3] = o; return art.paste(out, spr, 0, 0)


# ------------------------------------------------------------------ cast (real photos -> halftone cutouts / prints)
KATE = art.photo_cutout(P('kate.webp'), (20, 0, 440, 650), out_h=1000, fg_hint=[(230, 180, 70), (230, 450, 110)], bg_hint=[(20, 60, 18), (455, 60, 18), (450, 300, 12)])
BOSS = art.photo_cutout(P('boss_ai.webp'), (840, 380, 2000, 4600), out_h=1150, core=False,
                        fg_hint=[(1600, 820, 200), (1650, 1800, 380), (1450, 3500, 200), (1950, 3500, 200), (2550, 1350, 90), (1250, 950, 90)],
                        bg_hint=[(500, 600, 300), (2900, 700, 250), (2700, 300, 200), (3000, 2600, 300), (500, 3000, 300), (1720, 4350, 70), (2800, 4700, 200), (600, 4700, 200)])
BOOK = art.photo_cutout(P('wm/chapo_0.jpg'), (130, 60, 760, 1270), out_h=700, fg_hint=[(500, 520, 230)], bg_hint=[(60, 200, 50), (950, 200, 50), (80, 700, 40), (930, 700, 40)])
MARINE = art.photo_cutout(P('marine.webp'), (70, 0, 360, 711), out_h=900, core=False, fg_hint=[(230, 130, 50), (240, 420, 120)], bg_hint=[(20, 400, 20), (455, 300, 15), (60, 60, 30)])
OVIDIO = art.photo_cutout(P('ovidio.jpg'), (110, 20, 420, 947), out_h=900, fg_hint=[(310, 270, 110), (320, 750, 160)], bg_hint=[(30, 300, 30), (590, 300, 30), (40, 900, 30), (580, 900, 30)])
EMMA = art.photo_cutout(P('emma.webp'), (175, 20, 150, 295), out_h=800, core=False, fg_hint=[(246, 95, 26), (250, 230, 45)], bg_hint=[(150, 60, 18), (340, 60, 18), (130, 250, 25), (360, 250, 25)])
HORNS = _outlined(fit(cv2.copyMakeBorder(art.horns(col=np.array([.95, .10, .06], np.float32)), 14, 14, 14, 14, cv2.BORDER_CONSTANT, value=0), 440))
KH = fit(KATE, h=300); BH = fit(BOOK, h=260); BOSS_S = fit(BOSS, h=520)
PR_2014 = art.photo_print(P('chapo_2014_arrest.webp'), (0, 0, 474, 600), w=520, caption_h=60)
PR_SHOWER = art.photo_print(P('shower_hole.jpg'), (0, 0, 634, 380), w=560, caption_h=60)
PR_TUNNEL = art.photo_print(P('tunnel.jpg'), (0, 180, 1238, 1700), w=500, caption_h=60)
PR_PENN = art.photo_print(P('penn_handshake.webp'), (0, 0, 474, 316), w=620, caption_h=60)
PR_TANK = art.photo_print(P('chapo_2016_tanktop.webp'), (0, 0, 474, 681), w=520, caption_h=60)
PR_HANGAR = art.photo_print(P('chapo_2016_marines.jpg'), (0, 0, 962, 580), w=640, caption_h=60)
PR_FIRE = art.photo_print(P('burning_trailer.webp'), (0, 0, 474, 315), w=640, caption_h=60)
PR_FIRE2 = art.photo_print(P('burning_truck_aerial.webp'), (0, 0, 474, 315), w=560)
PR_EMMA = art.photo_print(P('emma.webp'), (60, 0, 380, 315), w=480, caption_h=60)
PENA = art.photo_print(WM('pena'), w=420, caption_h=50) if WM('pena') else None

# ------------------------------------------------------------------ props
FLAG = art.flag_mx(1000, 572); FLAG_S = fit(FLAG, 220); F_US = art.flag_us(1000, 530)
MTN_A = art.mountains(2600, 700, 3, np.array([.42, .26, .20], np.float32), .55, 7); MTN_B = art.mountains(2600, 700, 8, np.array([.24, .17, .28], np.float32), .45, 4)
BILLS = [art.bill(seed=i) for i in range(3)]; BUNDLE = art.cash_bundle(); BRICK = art.brick(); BAG = art.baggie()
BARS = art.jail_bars(820, 1200); BARS_L = BARS[:, :410].copy(); BARS_R = BARS[:, 410:].copy(); BARS_S = fit(BARS, 560)
RAYS_R = art.rays(1800, 12, RED, 0.55); RAYS_B = art.rays(1800, 14, BLUE, 0.45); RAYS_G = art.rays(1800, 14, art.MXG, 0.45); RAYS_O = art.rays(1800, 16, ORANGE, 0.5)
WANTED = art.wanted(BOOK, 520, 720, 4); PIN = art.pin(); DOCS = [art.doc(seed=i) for i in range(3)]
TUB = art.bathtub(); HOUSE = art.house(); PRISON = art.prison(); BIKE = art.motorbike(); CLAP = art.clapper(); PLANE = art.plane(); MIRROR = art.mirror(); GAVEL = art.gavel()
HOLES = [art.bullet_hole(seed=i) for i in range(4)]; FLASH = art.muzzle(); MOON = art.moon(); SKY = art.skyline(1800, 700); PALM = art.palm(); PHONE = art.phone(240, 440)
HEART = art.heart(); HB_L, HB_R = art.heart_broken(); CLOCK = art.clock_face(4, 40); CROWN = art.crown(); CAR = fit(art.car(), 640)
BUBBLES = [art.bubble(360, 150), art.bubble(300, 130, (.30, .80, .40)), art.bubble(340, 150)]
TVK = art.tv(art.photo_print(P('kate.webp'), (0, 0, 474, 420), w=500, border=8))
LOOT = [BILLS[0], BRICK, BUNDLE, BAG, BILLS[1], BRICK, BILLS[2], BAG]
SEMAR = fit(art.sticker(WM('semar'), 500), 260) if WM('semar') else fit(art.seal('SEMAR', col=(.10, .18, .38)), 240)
DEA = fit(art.sticker(WM('dea'), 500), 240) if WM('dea') else fit(art.seal('DEA', col=(.12, .20, .45)), 230)


def scene_bg(rays, mtn=True, flag=True, fy=-640, fs=1.05):
    els = [BG(rays, -150)]
    if flag: els.append(E(FLAG, 0, fy, fs, r=-.02, d=.55, wv=20, wob=0, sh=.3))
    if mtn: els += [E(MTN_B, 0, 560, 1.0, d=.7, wob=0, sh=.2), E(MTN_A, 150, 760, 1.0, d=.35, wob=0, sh=.3)]
    return els


def route(pts, t0, spr, n=6, speed=0.5, s=0.5, once=False, rot_follow=False):
    def fn(fr, t, ox, oy):
        if t < t0: return
        for i in range(n):
            raw = (t - t0) * speed + i / n
            if (t - t0) * speed < i / n: continue
            if once and raw - i / n >= 1: continue
            u = (raw - i / n) % 1.0 if once else raw % 1.0
            j = u * (len(pts) - 1); a, b = pts[int(j)], pts[min(len(pts) - 1, int(j) + 1)]; f = j - int(j)
            r_ = math.atan2(b[1] - a[1], b[0] - a[0]) if rot_follow else 0.25 * math.sin(i + t * 3)
            fr.put(spr, ox + lerp(a[0], b[0], f), oy + lerp(a[1], b[1], f), s * min(1, u * 8) * min(1, (1 - u) * 8 if not once else 1), rot=r_, depth=-0.05, shadow=0.5)
    return Fn(fn)


def mover(spr, path, t0, t1, s=1.0, d=-.05, ease=3, rot=0.0, bob=0.0):
    """Move one sprite along a path between t0 and t1 (stays at the end)."""
    def fn(fr, t, ox, oy):
        if t < t0: return
        u = eio(seg(t, t0, t1), ease); j = u * (len(path) - 1); a, b = path[int(j)], path[min(len(path) - 1, int(j) + 1)]; f = j - int(j)
        fr.put(spr, ox + lerp(a[0], b[0], f), oy + lerp(a[1], b[1], f) + bob * math.sin(t * 25), s, rot=rot, depth=d, shadow=0.5)
    return Fn(mover_wrap(fn))
def mover_wrap(fn): return fn


def gunfire(t0, t1, n, seed, area=(-450, -650, 450, 650)):
    """Bullet holes punch through the paper and muzzle flashes pop between t0 and t1."""
    r = np.random.default_rng(seed); els = []
    for i in range(n):
        tt = lerp(t0, t1, i / max(1, n - 1)) + r.uniform(-.05, .05); x, y = r.uniform(area[0], area[2]), r.uniform(area[1], area[3])
        els.append(E(FLASH, x + r.uniform(-60, 60), y - 40, r.uniform(.5, .9), r=r.uniform(0, 6), d=-.2, t=tt - .02, a='none', out=tt + .06, sh=0, quiet=True))
        els.append(E(HOLES[i % 4], x, y, r.uniform(.6, 1.0), r=r.uniform(0, 6), d=-.2, t=tt, a='pop', dur=.06, sh=.2, wob=0, quiet=True))
    return els


def bigbars(t0, d=-.08, x=0, y=40, s=1.0): return E(BARS, x, y, s, d=d, t=t0, a='slam', wob=0, sh=.7)
def kh(t0, x, y, s=1.0, r=0.0): return E(KH, x, y, s, r=r, d=-.05, t=t0)


# ------------------------------------------------------------------ the shots
tc = T('caught'); te = T('escaped')
SMUG = film.arc(0, 620, 0, -380, .45, 40)
TUB_PATH = [(160, -60), (120, 120), (40, 300), (-60, 460), (-260, 560), (-520, 620)]
BIKE_PATH = [(-700, 120), (700, 120)]
FLIGHT = film.arc(-650, 500, 600, -500, .25, 30)
TRAIL = [(-420, 640), (-300, 450), (-330, 260), (-150, 120), (-120, -80), (60, -200), (40, -380), (200, -480)]
CARP = [(-900, 380), (900, 380)]
NYF = film.arc(-650, 300, 650, -300, .2, 30)

S0 = [
 # 0  "Because of this woman,"
 dict(t=0.0, els=scene_bg(RAYS_R) + [rain(LOOT, 0.0, 1.3, 14, 3, .6),
      E(HORNS, 0, -530, 1.15, d=0, t=T('woman'), a='slam', glow=GLOW_RED, sh=.5), E(KATE, 0, 20, 1.0, t=0.03, a='pop', dur=.25, glow=GLOW_RED, breath=.012),
      E(L('THIS WOMAN', 640), 0, 660, r=-.05, d=-.1, t=T('woman') + .1, a='slam')], cam=[(0, 0, 60, 1.18), (1.5, 0, -20, 1.04)]),
 # 1  "the world's most wanted drug lord got caught."
 dict(t=T('the') - .1, els=scene_bg(RAYS_R, fy=-720) + [rain(LOOT, T('the'), tc + .8, 22, 4, .62),
      *[E(BRICK, x, y, .85, r=.05 * (-1) ** i, d=.15, t=T('drug') + i * .06, a='rise', wob=.01) for i, (x, y) in enumerate(((-420, 700), (-420, 570), (420, 700), (420, 570), (-400, 440), (400, 440)))],
      E(BOSS, 0, 60, 1.0, t=T('world\'s'), a='rise', glow=GLOW_RED, breath=.01),
      E(L('MOST WANTED', 660), 0, -720, r=-.04, d=-.1, t=T('wanted'), a='slam'),
      bigbars(tc, s=1.05), E(ST('CAUGHT', 640), 0, 620, r=-.12, d=-.15, t=tc + .15, a='slam', sh=0), flashes([(tc + .02, 0, 0)])],
      cam=[(1.4, 0, 60, 1.0), (3.6, 0, 20, 1.04), (4.6, 0, 0, 1.09)]),
 # 2  "Give me sixty seconds, and I'll show you how it happened."
 dict(t=T('give') - .12, els=scene_bg(RAYS_B, mtn=False) + [stopwatch(T('give')),
      orbit([(BUNDLE, .8), (BRICK, .7), (FLAG_S, 1), (BAG, .9), (BH, 1), (BRICK, .6), (KH, 1), (BUNDLE, .7)], T('sixty')),
      E(L('60 SECONDS', 620), 0, 650, r=-.04, d=-.1, t=T('sixty'), a='slam')], cam=[(4.6, 0, 0, .98), (7.0, 0, 0, 1.06), (8.0, 0, -40, 6.0)]),
 # 3  "Joaquin Guzman. El Chapo. Boss of the Sinaloa Cartel."
 dict(t=T('joaquin') - .12, els=scene_bg(RAYS_G) + [rain(LOOT, T('boss') - .3, T('cartel') + .6, 16, 7, .6),
      E(fit(WANTED, 380), -390, -250, r=-.15, d=.3, t=T('joaquin') + .2), E(PIN, -390, -470, .8, d=.3, t=T('joaquin') + .4, quiet=True), E(CROWN, 380, -380, .8, r=.2, d=.3, t=T('boss')),
      *[E(BUNDLE, x, y, .85, r=.05 * (-1) ** i, d=.15, t=T('boss') + i * .06, a='rise', wob=.01) for i, (x, y) in enumerate(((-420, 700), (-420, 600), (420, 700), (420, 600), (-400, 500), (400, 500)))],
      E(BOSS, 40, 30, 1.0, t=T('joaquin'), a='rise', glow=GLOW_RED, breath=.01),
      E(L('JOAQUÍN GUZMÁN', 760, WHITE), 0, -720, r=.03, d=-.12, t=T('joaquin') + .05, a='L', out=T('el') - .1),
      E(L('EL CHAPO', 560), 0, -720, r=-.05, d=-.1, t=T('el'), a='slam'), E(L('SINALOA CARTEL', 760), 0, 640, r=.03, d=-.1, t=T('sinaloa'), a='slam')],
      cam=[(8.0, 0, 60, 1.0), (13.0, 0, 0, 1.07)]),
 # 4  "He flooded America with cocaine, and he escaped prison twice."
 dict(t=T('he') - .12, els=[BG(RAYS_R, 0), E(F_US, 0, -650, 1.0, r=.02, d=.5, wv=18, wob=0, t=T('flooded'), a='drop'), E(FLAG, 0, 700, .95, r=-.02, d=.5, wv=18, wob=0),
      S(SMUG, T('flooded'), .7, RED, 14, dash=True), route(SMUG, T('flooded') + .2, BRICK, 7, .55, .8),
      E(L('COCAINE', 560), 0, -300, r=-.06, d=-.1, t=T('cocaine'), a='slam'), rain([BRICK, BAG, BRICK, BILLS[0]], T('america'), T('and', 2) + .6, 16, 11, .6),
      E(BOSS_S, 0, 80, 1.0, d=-.06, t=te - .45, a='rise', breath=.015, out=te + .35),
      'SPLIT', E(BARS_L, -205, 40, .9, d=-.1, t=te - .35, a='drop', wob=0), E(BARS_R, 205, 40, .9, d=-.1, t=te - .35, a='drop', wob=0),
      E(ST('ESCAPED 2X', 680), 0, 330, r=-.1, d=-.15, t=T('twice'), a='slam', sh=0)],
      cam=[(12.9, 0, -150, 1.0), (14.9, 0, -60, 1.03), (16.0, 0, 120, 1.05), (17.4, 0, 140, 1.08)]),
]

S1 = [
 # 5  "In 2014, marines cornered him in Culiacan."
 dict(t=T('in') - .1, els=scene_bg(RAYS_B, fy=-700) + [E(art.calendar('YEAR', '2014', seed=1), -330, -380, 1.0, r=-.08, d=-.05, t=T('twenty'), a='slam'),
      E(SEMAR, 360, -420, r=.1, t=T('marines')), *[E(MARINE, x, 260, .62, d=-.05 + .03 * i, t=T('marines') + .1 * i, a=('L' if x < 0 else 'R'), breath=.01) for i, x in enumerate((-420, 420, -240, 240))],
      E(BOSS_S, 0, 160, 1.0, d=-.02, t=T('cornered') - .1, a='rise', breath=.015), S(film.circ(0, 160, 200, 300), T('cornered'), .35, RED, 12),
      E(L('CULIACÁN', 520), 0, 680, r=-.04, d=-.1, t=T('culiacan'), a='slam')]),
 # 6  "He slipped out through a tunnel hidden under a bathtub,"
 dict(t=T('he', 3) - .12, els=[BG(RAYS_O, -200), E(HOUSE, 0, -330, 1.25, d=.3, wob=0), E(MTN_A, 0, 700, 1.0, d=.2, wob=0, sh=.3),
      E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 1600, 900, (.20, .14, .10), 9), 0, 560, 1.0, d=.1, wob=0, sh=0),
      S(TUB_PATH, T('slipped'), .9, ORANGE, 14, dash=True), mover(BOSS_S, [(160, -150)] + TUB_PATH, T('slipped') + .1, T('bathtub') + .6, .85),
      Fn(lambda fr, t, ox, oy: fr.put(TUB, ox + 160, oy - 40 - 140 * eout(seg(t, T('slipped') - .2, T('slipped') + .2), 3), 1.0, rot=-.35 * eout(seg(t, T('slipped') - .2, T('slipped') + .2), 3), shadow=0.5)),
      E(L('TUNNEL', 420), -250, -700, r=-.05, d=-.1, t=T('tunnel'), a='slam'), E(L('UNDER A BATHTUB', 720), 0, 860, r=.03, d=-.15, t=T('bathtub'), a='slam')]),
 # 7  "and was caught days later at a beach hotel in Mazatlan."
 dict(t=T('and', 3) - .12, els=[BG(RAYS_B, -200), E(art.shape([[(0, .5), (1, .4), (1, 1), (0, 1)]], 1600, 700, (.18, .38, .58), 11), 0, 720, 1.0, d=.4, wob=0, sh=0),
      E(art.building(380, 900, seed=4, dark=.6), 330, -120, 1.2, d=.3, wob=0), E(PALM, -400, 300, 1.3, d=.2), E(PALM, 470, 420, 1.1, d=.15),
      E(PR_2014, -60, -40, 1.0, r=-.04, d=-.05, t=T('caught', 2), a='slam'), E(ST('CAUGHT', 520), -60, 300, r=-.1, d=-.1, t=T('caught', 2) + .15, a='slam', sh=0),
      E(art.calendar('FEB', '22', seed=3), -330, -560, .9, r=-.08, d=-.1, t=T('days'), a='pop'), E(L('MAZATLÁN', 540), 0, 660, r=-.04, d=-.12, t=T('mazatlan'), a='slam'),
      E(L('BEACH HOTEL', 520, WHITE), 260, -620, r=.05, d=-.1, t=T('hotel'), a='pop')]),
 # 8  "Mexico locked him inside Altiplano, its most secure prison."
 dict(t=T('mexico') - .12, els=scene_bg(RAYS_B, mtn=False, fy=-720) + [E(PRISON, 0, 380, 1.1, d=.2, t=T('mexico'), a='rise', wob=0),
      E(BOOK, 0, -120, .95, t=T('locked') - .1, a='pop'), bigbars(T('locked'), y=-120, s=.75), E(L('ALTIPLANO', 600), 0, 200, r=-.04, d=-.1, t=T('altiplano'), a='slam'),
      E(ST('MAX SECURITY', 680), 0, 760, r=-.1, d=-.12, t=T('secure'), a='slam', sh=0)]),
 # 9  "Seventeen months later, he walked into his shower and vanished,"
 dict(t=T('seventeen') - .12, els=[BG(RAYS_O, -150), E(art.calendar('MONTHS', '17', seed=6), -320, -620, 1.0, r=-.08, d=-.05, t=T('seventeen'), a='slam'),
      E(PR_SHOWER, 0, 0, 1.0, r=.03, d=-.05, t=T('shower'), a='slam'), S(film.circ(-10, -40, 120, 120), T('shower') + .3, .35, RED, 12),
      E(BOSS_S, 330, -380, .8, d=-.05, t=T('walked'), a='R', out=T('vanished')), E(ST('VANISHED', 640), 0, 520, r=-.1, d=-.1, t=T('vanished'), a='slam', sh=0)]),
 # 10 "down a mile-long tunnel with a motorcycle on rails."
 dict(t=T('down') - .12, els=[BG(RAYS_O, -300), E(PR_TUNNEL, 230, -330, 1.0, r=.04, d=.2, t=T('down'), a='drop'),
      E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 1600, 380, (.22, .15, .10), 12), 0, 120, 1.0, d=.05, wob=0, sh=.4),
      S([(-800, 270), (800, 270)], T('down'), .6, (.6, .6, .62), 8), S([(-800, 300), (800, 300)], T('down') + .1, .6, (.6, .6, .62), 8),
      mover(BIKE, BIKE_PATH, T('motorcycle') - .4, T('rails') + 1.0, .9, ease=2, bob=1.5),
      E(L('1.5 KM TUNNEL', 700), -40, 560, r=-.04, d=-.1, t=T('mile'), a='slam'), E(L('MOTORCYCLE ON RAILS', 860, WHITE), 0, 760, r=.03, d=-.12, t=T('rails'), a='pop')]),
]

S2 = [
 # 11 "Then he made one mistake."
 dict(t=T('then') - .12, els=[BG(RAYS_R, -100, 1.0), E(BOSS, 0, 120, .9, t=T('then'), a='pop', breath=.012), E(L('ONE MISTAKE', 820), 0, -640, r=-.05, d=-.1, t=T('mistake'), a='slam'),
      E(HEART, 330, -280, 1.0, r=.2, d=-.1, t=T('mistake') + .2, pulse=.08)]),
 # 12 "He became obsessed with Kate del Castillo, the actress who played a drug queen on TV."
 dict(t=T('he', 6) - .12, els=scene_bg(RAYS_R, mtn=False, fy=-720) + [*[E(HEART, x, y, s, r=r, d=.2, t=T('obsessed') + i * .08, pulse=.06) for i, (x, y, s, r) in enumerate(((-420, -420, .6, -.2), (430, -380, .5, .2), (-380, 420, .5, .1), (420, 480, .7, -.1)))],
      E(HORNS, 0, -470, 1.0, d=0, t=T('kate'), a='slam', glow=GLOW_RED), E(KATE, 0, 60, .9, t=T('kate') - .05, a='rise', glow=GLOW_RED, breath=.012),
      E(L('KATE DEL CASTILLO', 860), 0, 560, r=-.03, d=-.1, t=T('kate'), a='slam'),
      E(TVK, 330, 120, .55, r=.08, d=-.12, t=T('actress'), a='R'), E(CROWN, 330, -60, .5, r=.1, d=-.13, t=T('queen')), E(L('"DRUG QUEEN"', 520, WHITE), 300, 300, r=.06, d=-.14, t=T('queen'), a='pop')],
      cam=[(42.1, 0, -80, 1.0), (47.4, 0, 40, 1.06)]),
 # 13 "He texted her. He wanted her to make a movie about his life."
 dict(t=T('he', 7) - .12, els=[BG(RAYS_R, -150), E(fit(BOSS, h=700), -250, 120, 1.0, t=T('he', 7), a='L', breath=.012), E(fit(KATE, h=620), 300, 160, 1.0, t=T('her', 1), a='R', breath=.012),
      E(PHONE, -60, -300, 1.0, r=-.1, d=-.05, t=T('texted'), a='pop'), *[E(BUBBLES[i], x, y, 1.0, r=r, d=-.08, t=T('texted') + .15 + i * .35, a='pop') for i, (x, y, r) in enumerate(((-30, -640, -.05), (250, -480, .05), (-120, -500, .03)))],
      E(CLAP, 250, 520, .8, r=.1, d=-.1, t=T('movie'), a='slam'), E(L('A MOVIE ABOUT HIS LIFE', 900), 0, 760, r=-.03, d=-.12, t=T('movie'), a='slam')]),
 # 14 "In October 2015, she flew into the Sinaloa mountains to meet him, and she brought Hollywood star Sean Penn."
 dict(t=T('in', 4) - .12, els=[BG(RAYS_B, -300), E(MTN_B, 0, 400, 1.2, d=.6, wob=0), E(MTN_A, 0, 650, 1.2, d=.3, wob=0), E(MOON, 380, -700, 1.0, d=.6),
      E(art.calendar('OCT', '2015', seed=7), -330, -640, 1.0, r=-.08, d=-.05, t=T('october'), a='slam'),
      S(FLIGHT, T('flew'), 1.0, WHITE, 8, dash=True), mover(PLANE, FLIGHT, T('flew'), T('mountains') + .6, .55),
      E(fit(KATE, h=380), -330, 100, 1.0, r=-.06, d=-.05, t=T('she', 1), a='pop'), E(fit(BOSS, h=420), 330, 60, 1.0, r=.06, d=-.05, t=T('meet'), a='pop'),
      E(PR_PENN, 0, 380, 1.0, r=-.03, d=-.1, t=T('sean'), a='slam'), E(L('SEAN PENN', 520), 0, 680, r=.04, d=-.12, t=T('penn'), a='slam'),
      E(L('SINALOA MOUNTAINS', 760, WHITE), 0, -420, r=.03, d=-.1, t=T('mountains'), a='pop', out=T('sean') - .2)],
      cam=[(51.4, 0, -150, 1.0), (55.5, 0, 0, 1.0), (58.6, 0, 150, 1.06)]),
 # 15 "Mexican officials say that trip helped put them on his trail."
 dict(t=T('mexican') - .12, els=scene_bg(RAYS_G, mtn=False) + [E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 1000, 1300, (.80, .72, .55), 13), 0, 80, 1.0, d=.3, wob=0),
      S(TRAIL, T('officials'), 1.6, RED, 12, dash=True), *[E(PIN, x, y, .9, d=-.05, t=T('officials') + i * .2, quiet=True) for i, (x, y) in enumerate(TRAIL[::2])],
      E(fit(BOSS, h=360), 200, -480, 1.0, d=-.05, t=T('trail') - .4, a='pop'), S(film.circ(200, -480, 170, 210), T('trail'), .35, RED, 14),
      E(fit(DOCS[0], 300), -360, -500, 1.0, r=-.15, d=-.03), E(ST('ON HIS TRAIL', 720), 0, 640, r=-.08, d=-.12, t=T('trail'), a='slam', sh=0)]),
]

S3 = [
 # 16 "January 8th, 2016. Four forty in the morning."
 dict(t=T('january') - .12, els=[BG(RAYS_B, -100, .2), E(MOON, 330, -640, 1.2, d=.5), E(SKY, 0, 620, 1.0, d=.4, wob=0),
      E(art.calendar('JAN', '8', seed=8), -300, -380, 1.1, r=-.08, d=-.05, t=T('january'), a='slam'), E(L('2016', 360), -300, -60, r=.05, d=-.08, t=T('sixteen'), a='slam'),
      E(CLOCK, 230, 120, 1.0, d=-.05, t=T('four'), a='pop'), E(L('4:40 AM', 520), 230, 460, r=-.04, d=-.1, t=T('forty'), a='slam')]),
 # 17 "Mexican marines storm a safe house in Los Mochis."
 dict(t=T('mexican', 2) - .12, els=[BG(RAYS_B, -200), E(SKY, 0, 300, 1.0, d=.6, wob=0), E(HOUSE, 0, -80, 1.25, d=.2, t=T('safe'), a='rise', wob=0),
      *[E(MARINE, x, 420, .7, d=-.05 - .02 * i, t=T('marines', 2) + .08 * i, a=('L' if x < 0 else 'R'), breath=.01) for i, x in enumerate((-430, 430, -230, 230, 0))],
      E(SEMAR, -380, -620, r=-.1, t=T('marines', 2)), E(L('LOS MOCHIS', 620), 0, -620, r=.04, d=-.1, t=T('mochis'), a='slam'),
      flashes([(T('storm'), -300, 100), (T('storm') + .2, 300, 0)], [(1, .9, .7)]), E(ST('RAID', 400), 0, -320, r=-.1, d=-.1, t=T('storm'), a='slam', sh=0)]),
 # 18 "His gunmen fight back with assault rifles and a rocket launcher. Five of them are killed. One marine is wounded."
 dict(t=T('his', 4) - .12, els=[BG(RAYS_R, 0, .8), E(fit(PR_FIRE2, 700), 0, -420, 1.0, r=-.03, d=.3, wob=0), E(HOUSE, 0, 180, 1.0, d=.2, wob=0),
      *gunfire(T('fight'), T('launcher') + .3, 14, 5), E(L('ASSAULT RIFLES', 700), 0, -720, r=-.04, d=-.1, t=T('assault'), a='slam'),
      E(ST('ROCKET LAUNCHER', 820), 0, -120, r=.06, d=-.15, t=T('rocket'), a='slam', sh=0), flashes([(T('launcher'), 0, -100)], [(1, .6, .3)]),
      E(L('5 GUNMEN KILLED', 760), 0, 480, r=-.04, d=-.12, t=T('five'), a='slam'), E(L('1 MARINE WOUNDED', 760, WHITE), 0, 700, r=.03, d=-.12, t=T('marine'), a='slam'),
      *gunfire(T('five') - .3, T('wounded'), 6, 9)]),
 # 19 "Chapo runs again, through a secret door behind a mirror and into the city sewers."
 dict(t=T('chapo', 2) - .12, els=[BG(RAYS_O, -200), Fn(lambda fr, t, ox, oy: fr.put(MIRROR, ox - 120, oy - 200, 1.3, sx=max(0.08, 1 - eout(seg(t, T('door'), T('door') + .4), 3) * .92), shadow=0.5)),
      E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 330, 560, (.05, .04, .04), 14), -120, -200, 1.0, d=.02, wob=0, sh=0, t=T('secret') - .3, a='fade'),
      E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 1600, 420, (.18, .20, .16), 15), 0, 520, 1.0, d=.05, wob=0, sh=.3),
      S([(-120, -100), (-120, 400), (700, 520)], T('door'), .8, ORANGE, 14, dash=True), mover(BOSS_S, [(-120, -100), (-120, 420), (900, 520)], T('mirror'), T('sewers') + .7, .5),
      E(L('SECRET DOOR', 600), 160, -640, r=.04, d=-.1, t=T('secret'), a='slam'), E(L('CITY SEWERS', 600, WHITE), 0, 820, r=-.03, d=-.12, t=T('sewers'), a='slam')]),
 # 20 "He steals a car. Marines stop him on the highway."
 dict(t=T('he', 9) - .12, els=[BG(RAYS_B, -300), E(SKY, 0, 120, 1.0, d=.5, wob=0), E(art.shape([[(0, 0), (1, 0), (1, 1), (0, 1)]], 2000, 300, (.16, .15, .15), 16), 0, 520, 1.0, d=.1, wob=0, sh=0),
      S([(-900, 520), (900, 520)], T('steals'), .5, (.95, .85, .3), 10, dash=True),
      mover(CAR, [(-1000, 400), (0, 400)], T('steals') - .1, T('stop'), 1.0, ease=2, bob=2),
      *[E(MARINE, x, 300, .55, d=-.1, t=T('marines', 3) + .1 * i, a='R', breath=.01) for i, x in enumerate((330, 470))],
      E(PR_TANK, 0, -330, 1.0, r=-.04, d=-.12, t=T('stop'), a='slam'), E(ST('CAPTURED', 600), 0, 80, r=-.12, d=-.15, t=T('highway'), a='slam', sh=0),
      flashes([(T('stop'), -300, 380), (T('stop') + .25, 300, 380)], [(1, .2, .1), (.2, .3, 1)])]),
 # 21 "Mexico's president posts: Mission accomplished. We have him."
 dict(t=T("mexico's") - .12, els=scene_bg(RAYS_G, mtn=False) + ([E(PENA, -280, -300, 1.0, r=-.06, d=-.02, t=T('president'), a='L')] if PENA is not None else []) + [
      E(fit(PHONE, 360), 230, -40, 1.0, r=.06, d=-.05, t=T('posts'), a='pop'), E(fit(BUBBLES[0], 420), 200, -260, 1.0, r=.03, d=-.08, t=T('posts') + .2, a='pop'),
      E(L('"MISSION ACCOMPLISHED"', 900), 0, 300, r=-.04, d=-.1, t=T('mission'), a='slam'), E(L('"WE HAVE HIM"', 620, WHITE), 0, 520, r=.04, d=-.12, t=T('we'), a='slam'),
      rain([fit(FLAG, 160), BILLS[0], fit(FLAG, 140)], T('mission'), T('have') + .4, 10, 13, .9)]),
 # 22 "A year later, Chapo is flown to New York."
 dict(t=T('a', 13) - .12 if False else T('year') - .3, els=[BG(RAYS_B, -200), E(F_US, 0, -680, .95, d=.5, wv=18, wob=0), E(SKY, 0, 650, 1.0, d=.3, wob=0),
      E(art.calendar('JAN', '2017', seed=9), -330, -330, .9, r=-.08, d=-.05, t=T('year'), a='slam'),
      E(PR_HANGAR, 60, 60, 1.0, r=.03, d=-.05, t=T('chapo', 3), a='slam'), S(NYF, T('flown'), .9, WHITE, 8, dash=True), mover(PLANE, NYF, T('flown'), T('york') + .7, .55),
      E(L('NEW YORK', 520), 0, 460, r=-.04, d=-.1, t=T('new'), a='slam')]),
]

S4 = [
 # 23 "Convicted on ten counts. Life in prison plus thirty years, and twelve point six billion dollars to hand over."
 dict(t=T('convicted') - .12, els=[BG(RAYS_R, -150), E(DEA, 380, -660, r=.1, t=T('convicted')), E(fit(BOOK, h=560), 0, -300, 1.0, t=T('convicted'), a='pop'), E(GAVEL, -330, -560, .8, r=-.3, t=T('convicted') + .1, a='slam'),
      E(ST('GUILTY', 520), 0, -60, r=-.12, d=-.1, t=T('ten'), a='slam', sh=0), E(L('10 COUNTS', 460, WHITE), 300, -100, r=.05, d=-.1, t=T('counts'), a='pop'),
      bigbars(T('life', 2), y=-300, s=.6), E(L('LIFE + 30 YEARS', 820), 0, 200, r=-.04, d=-.1, t=T('plus'), a='slam'),
      E(L('$12.6 BILLION', 820), 0, 480, r=.04, d=-.12, t=T('twelve'), a='slam'), rain([BUNDLE, BILLS[0], BILLS[1], BUNDLE], T('billion') - .2, T('over') + .5, 22, 17, .7)]),
 # 24 "His wife Emma was later jailed in the U.S. too."
 dict(t=T('his', 5) - .12, els=[BG(RAYS_R, -150), E(fit(PR_EMMA, 300), 330, -560, 1.0, r=.1, d=.2), E(fit(EMMA, h=900), 0, 40, 1.0, t=T('wife'), a='rise', breath=.012),
      E(L('EMMA CORONEL', 640), 0, -640, r=-.04, d=-.1, t=T('emma'), a='slam'), E(L('HIS WIFE', 380, WHITE), -300, -470, r=.05, d=-.12, t=T('wife'), a='pop'),
      bigbars(T('jailed'), y=60, s=.9), E(ST('JAILED', 480), 0, 600, r=-.1, d=-.15, t=T('jailed') + .15, a='slam', sh=0)]),
 # 25 "And when soldiers grabbed his son in Culiacan in 2019, cartel gunmen took over the entire city, until the army let him go."
 dict(t=T('soldiers') - .3, els=[BG(RAYS_R, -100, .9), E(PR_FIRE, 0, -480, 1.0, r=-.03, d=.25, t=T('cartel', 2), a='drop'), E(fit(PR_FIRE2, 420), -330, 620, 1.0, r=.06, d=.2, t=T('took'), a='rise'),
      E(fit(OVIDIO, h=700), 120, 100, 1.0, t=T('soldiers'), a='rise', breath=.012), E(L('HIS SON', 400, WHITE), 280, -260, r=.06, d=-.1, t=T('son'), a='pop'),
      E(L('CULIACÁN 2019', 640), 0, -700, r=-.04, d=-.1, t=T('culiacan', 2), a='slam', out=T('cartel', 2) - .2),
      *gunfire(T('gunmen', 2), T('city') + .4, 10, 21), E(L('CITY TAKEN OVER', 720), 0, 520, r=-.03, d=-.12, t=T('took'), a='slam'),
      E(ST('LET GO', 520), 120, 120, r=-.12, d=-.15, t=T('let'), a='slam', sh=0)]),
 # 26 "The man who beat two prisons and an army was undone by a crush."
 dict(t=T('the', 15) - .12 if False else T('man') - .15, els=[BG(RAYS_R, -100, .6), E(BOSS, -170, 120, .8, d=0, t=T('man'), a='pop', breath=.012), bigbars(T('beat'), x=-170, y=120, s=.8),
      E(HORNS, 330, -500, .6, d=-.05, t=T('crush') - .1, a='slam', glow=GLOW_RED), E(fit(KATE, h=520), 330, -230, 1.0, d=-.05, t=T('undone'), a='R', glow=GLOW_RED, breath=.012),
      E(L('2 PRISONS', 420, WHITE), -330, -660, r=-.05, d=-.1, t=T('prisons'), a='pop'), E(L('1 ARMY', 340, WHITE), -330, -500, r=.05, d=-.1, t=T('army', 2), a='pop'),
      'HEART', E(HB_L, 330, 330, 1.0, d=-.1, t=T('crush') - .2, a='pop'), E(HB_R, 330, 330, 1.0, d=-.1, t=T('crush') - .2, a='pop'),
      E(L('UNDONE BY A CRUSH', 860), 0, 700, r=-.03, d=-.12, t=T('crush'), a='slam')]),
 # 27 "Follow for more."
 dict(t=T('follow') - .12, els=[BG(RAYS_O, 0, 1.2), E(L('FOLLOW', 860), 0, -120, r=-.05, t=T('follow'), a='slam'), E(L('FOR MORE', 620), 0, 150, r=.03, t=T('more'), a='slam'),
      E(fit(KATE, h=330), -300, -580, r=-.08, t=T('follow')), E(fit(BOOK, h=300), 300, -580, r=.08, t=T('follow') + .08), rain(LOOT, T('follow'), DUR, 12, 31, .6)]),
]
SHOTS = S0 + S1 + S2 + S3 + S4


# ------------------------------------------------------------------ special bits that animate existing elements
def _split_hook(els, t0, l, r, dist=520, rot=.35):
    def fn(fr, t, ox, oy):
        k = eout(seg(t, t0, t0 + .45), 3); l.x = l.x0 - dist * k; l.r = -rot * k; r.x = r.x0 + dist * k; r.r = rot * k
    l.x0, r.x0 = l.x, r.x; i = els.index('SPLIT' if 'SPLIT' in els else 'HEART'); els[i] = Fn(fn)


e4 = SHOTS[4]['els']; i = e4.index('SPLIT'); _split_hook(e4, te, e4[i + 1], e4[i + 2])
e26 = SHOTS[26]['els']; i = e26.index('HEART'); _split_hook(e26, T('crush') + .15, e26[i + 1], e26[i + 2], 90, .5)


def grade(img, t):
    lum = img.mean(2, keepdims=True); sh = (1 - lum) ** 2; hi = lum ** 2
    return img * (1 + sh * (np.array([.62, .78, 1.40], np.float32) - 1) * .5 + hi * (np.array([1.22, .90, .82], np.float32) - 1) * .4)


def extra(add):
    tick, riser, thump, nburst, whoosh, SR = film.tick, film.riser, film.thump, film.nburst, film.whoosh, film.SR
    for i in range(28): add(tick(), T('give') + .1 + i * 2.2 / 28, 0.06)
    n = int(.5 * SR); tt = np.arange(n) / SR; clang = np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / .12) * .5 + np.sin(2 * np.pi * 1210 * tt) * np.exp(-tt / .07) * .3
    for tb in (tc, T('locked'), T('life', 2), T('jailed'), T('beat')): add(clang, tb, 0.08); add(thump(60, 30, 1.0, .3), tb, 0.2)
    for tr in (tc, T('caught', 2), T('stop'), T('mission')): add(riser(.9), tr - .9, 0.11)
    for sh in SHOTS:                                                                  # quiet gunshots for every bullet hole
        for e in sh['els']:
            if getattr(e, 'spr', None) is not None and any(e.spr is h for h in HOLES): add(film.gunshot(), e.t, 0.05, float(np.clip(e.x / 700, -.6, .6)))
    add(thump(50, 25, 1.4, .5), T('rocket'), 0.3); add(nburst(1.2, 80, 2000, .4), T('launcher'), 0.12)
    m = int(2.5 * SR); tt = np.arange(m) / SR; add(np.sin(2 * np.pi * np.cumsum(110 + 25 * np.sin(2 * np.pi * 9 * tt)) / SR) * .4 * np.minimum(1, tt) * np.exp(-tt / 2), T('motorcycle'), 0.05)
    add(film._filt(np.random.default_rng(3).normal(0, 1, int(2 * SR)), 80, 600) * np.exp(-np.arange(int(2 * SR)) / SR / 1.2), T('steals'), 0.06)   # car
    add(film._filt(np.random.default_rng(4).normal(0, 1, int(2.2 * SR)), 300, 2500) * np.sin(np.pi * np.arange(int(2.2 * SR)) / int(2.2 * SR)), T('flew'), 0.05)  # plane
    n2 = int(1.4 * SR); tt = np.arange(n2) / SR; siren = np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 1.6 * tt)) / SR) * np.sin(np.pi * tt / 1.4) * 0.5
    for ts in (tc + .1, T('stop') + .1): add(siren, ts, 0.03)


SHOW = Show(SHOTS, DUR, VOICE, grade=grade, sfx_extra=extra, floaters_cols=(PAPER, RED, np.array([.15, .3, .9], np.float32), art.MXG, PAPER_LT, WHITE))
if __name__ == '__main__': run(SHOW, sys.argv)
