"""El Chapo - 10 s style sample (Documentary Template 1, Mexico grade). Timings are estimates until the voice-over arrives.
Usage: python3 sample.py stills <dir> t1,t2  |  render <outdir>  |  mux <outdir> <out.mp4>"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art
from voxkit.film import *
from voxkit import film

PH = os.path.join(HERE, 'photos')
DUR = 10.0
# estimated word starts (replace with forced alignment once the voice-over arrives)
T = {'because': 0.1, 'woman': 0.85, 'worlds': 1.3, 'wanted': 1.85, 'drug': 2.3, 'caught': 3.2, 'give': 4.2, 'sixty': 4.75, 'show': 5.6, 'happened': 6.4,
     'joaquin': 7.2, 'guzman': 7.75, 'chapo': 8.45, 'boss': 9.0, 'sinaloa': 9.35, 'cartel': 9.8}

# ------------------------------------------------------------------ assets
KATE = art.photo_cutout(os.path.join(PH, 'kate.webp'), (20, 0, 440, 650), out_h=1000, fg_hint=[(230, 180, 70), (230, 450, 110)], bg_hint=[(20, 60, 18), (455, 60, 18), (450, 300, 12)])
BOOK = art.photo_cutout(os.path.join(PH, 'wm', 'chapo_0.jpg'), (130, 60, 760, 1270), out_h=700, fg_hint=[(500, 520, 230)], bg_hint=[(60, 200, 50), (950, 200, 50), (80, 700, 40), (930, 700, 40)])
CHAPO = art.photo_cutout(os.path.join(PH, 'penn_handshake.webp'), (262, 38, 200, 278), out_h=980, core=False, fg_hint=[(352, 92, 26), (360, 200, 40), (340, 270, 30), (400, 260, 25)], bg_hint=[(250, 40, 8), (465, 60, 8), (470, 200, 6), (290, 60, 12), (440, 55, 16), (300, 40, 10), (420, 40, 10), (455, 120, 8), (395, 45, 12), (380, 40, 8), (405, 70, 7), (275, 80, 8)])
HORNS = fit(art.horns(), 400)
FLAG = art.flag_mx(1000, 572); FLAG_S = fit(FLAG, 200)
MTN_A = art.mountains(2600, 700, 3, np.array([.42, .26, .20], np.float32), .55, 7); MTN_B = art.mountains(2600, 700, 8, np.array([.24, .17, .28], np.float32), .45, 4)
BILLS = [art.bill(seed=i) for i in range(3)]; BUNDLE = art.cash_bundle(); BRICK = art.brick()
RAYS_R = art.rays(1800, 12, art.RED, 0.55); RAYS_B = art.rays(1800, 14, np.array([.15, .25, .65], np.float32), 0.45); RAYS_G = art.rays(1800, 14, art.MXG, 0.45)
WANTED = art.wanted(BOOK, 520, 720, 4)
DOCS = [art.doc(seed=i) for i in range(2)]; PIN = art.pin()
RED = art.RED; GLOW_RED = (0.95, 0.06, 0.04)
KH = fit(KATE, h=270); CH = fit(BOOK, h=260)
CASH = [BILLS[0], BILLS[1], BUNDLE, BILLS[2]]


def scene_bg(rays, mtn=True, flag=True, fy=-640):
    els = [BG(rays, -150)]
    if flag: els.append(E(FLAG, 0, fy, 1.05, r=-.02, d=.55, wv=20, wob=0, sh=.3))
    if mtn: els += [E(MTN_B, 0, 560, 1.0, d=.7, wob=0, sh=.2), E(MTN_A, 150, 760, 1.0, d=.35, wob=0, sh=.3)]
    return els


SHOTS = [
 # 0 - "Because of this woman, the world's most wanted drug lord got caught."
 dict(t=0.0, els=scene_bg(RAYS_R) + [rain(CASH, 0.0, 3.6, 26, 3, .62),
      E(KATE, 0, -60, 1.0, t=0.05, a='pop', dur=.25, glow=GLOW_RED),
      E(L('THIS WOMAN', 640), 0, -720, r=-.05, d=-.1, t=T['woman'], a='slam'),
      E(WANTED, 240, 520, .62, r=.1, d=-.15, t=T['wanted'], a='R'), E(PIN, 230, 290, .9, d=-.15, t=T['wanted'] + .3, quiet=True),
      S(film.arc(90, 430, -150, 250, .3), T['drug'], .35, RED, 9), S([(-120, 220), (-150, 250), (-115, 275)], T['drug'] + .3, .1, RED, 9),
      *[E(BUNDLE, x, y, .9, r=rr, d=-.1, t=T['worlds'] + i * .1) for i, (x, y, rr) in enumerate(((-400, 560, .3), (-330, 700, -.2), (-430, 820, .1)))],
      E(ST('CAUGHT', 480), 240, 560, r=-.2, d=-.2, t=T['caught'], a='slam', sh=0),
      flashes([(T['caught'] + .05, -420, -300), (T['caught'] + .25, 420, -300), (T['caught'] + .45, -420, -300), (T['caught'] + .65, 420, -300)], [(1., .15, .1), (.15, .3, 1.), (1., .15, .1), (.15, .3, 1.)])],
      cam=[(0, 0, -40, 1.12), (1.6, 0, 20, 1.0), (4.2, 0, 80, 1.04)]),
 # 1 - "Give me sixty seconds, and I'll show you how it happened."
 dict(t=T['give'] - .12, els=scene_bg(RAYS_B, mtn=False) + [stopwatch(T['give']),
      orbit([(BUNDLE, .8), (BRICK, .7), (FLAG_S, 1), (BILLS[0], .6), (CH, 1), (BRICK, .6), (KH, 1), (BUNDLE, .7)], T['sixty']),
      E(L('60 SECONDS', 620), 0, 650, r=-.04, d=-.1, t=T['sixty'], a='slam')], cam=[(4.1, 0, 0, .98), (6.0, 0, 0, 1.06), (7.15, 0, -40, 6.0)]),
 # 2 - "Joaquin Guzman. El Chapo. Boss of the Sinaloa Cartel."
 dict(t=T['joaquin'] - .12, els=scene_bg(RAYS_G) + [rain(CASH, T['boss'] - .3, T['cartel'] + .5, 14, 7, .6),
      *[E(BRICK, x, y, .9, r=.05 * (-1) ** i, d=.15, t=T['joaquin'] + .1 + i * .07, a='rise', wob=.01) for i, (x, y) in enumerate(((-400, 640), (-400, 500), (-400, 360), (400, 640), (400, 500), (400, 360), (-380, 220), (380, 220)))],
      E(CHAPO, 0, -20, 1.0, t=T['joaquin'], a='rise', glow=(.9, .05, .04)),
      E(HORNS, 0, -478, 0.95, d=-.02, t=T['chapo'], a='slam', glow=GLOW_RED, sh=.5),
      E(L('EL CHAPO', 560), 0, -720, r=-.05, d=-.1, t=T['chapo'], a='slam'), E(L('JOAQUÍN GUZMÁN', 760, np.array([.95, .93, .86], np.float32)), 0, -560, r=.03, d=-.12, t=T['joaquin'] + .05, a='L', out=T['chapo'] - .1),
      E(L('SINALOA CARTEL', 760), 0, 560, r=.03, d=-.1, t=T['sinaloa'], a='slam')],
      cam=[(7.1, 0, 60, 1.0), (10.0, 0, 0, 1.08)]),
]


def grade(img, t):
    """Mexico night grade: blue shadows, red highlights, alternating red/blue police light at the frame edges."""
    lum = img.mean(2, keepdims=True); sh = (1 - lum) ** 2; hi = lum ** 2
    img = img * (1 + sh * (np.array([.62, .78, 1.40], np.float32) - 1) * .55 + hi * (np.array([1.22, .90, .82], np.float32) - 1) * .45)
    ph = math.sin(t * 2 * math.pi * 1.2); k = 0.10 + 0.06 * abs(ph)
    img = img + _EDGE_L * (np.array([1., .1, .06], np.float32) * k * max(0, ph) * 1.6) + _EDGE_R * (np.array([.1, .25, 1.], np.float32) * k * max(0, -ph) * 1.6)
    img = img + _EDGE_L * np.array([.10, .01, .01], np.float32) + _EDGE_R * np.array([.01, .03, .12], np.float32)
    return img
_x = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
_EDGE_L = np.clip(1 - _x / 0.45, 0, 1) ** 2; _EDGE_R = np.clip((_x - 0.55) / 0.45, 0, 1) ** 2


def extra(add):
    for i in range(28): add(film.tick(), T['give'] + .1 + i * 2.2 / 28, 0.06)
    add(film.riser(1.0), T['caught'] - 1.0, 0.13)
    n = int(1.4 * film.SR); tt = np.arange(n) / film.SR                               # distant siren, very low
    add(np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 1.6 * tt)) / film.SR) * np.sin(np.pi * tt / 1.4) * 0.5, T['caught'] + .1, 0.035)
    for i in range(10): add(film.nburst(0.12, 1500, 6000, 0.03), 0.3 + i * .32, 0.02)  # cash flutter


SHOW = Show(SHOTS, DUR, None, grade=grade, sfx_extra=extra, floaters_cols=(PAPER, art.RED, np.array([.15, .3, .9], np.float32), art.MXG, PAPER_LT))
if __name__ == '__main__': run(SHOW, sys.argv)
