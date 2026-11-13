"""El Chapo - opening test clip (Documentary Template 1, Mexico grade), timed to the real voice-over.
Usage: python3 sample.py stills <dir> t1,t2  |  render <outdir>  |  mux <outdir> <out.mp4>"""
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art
from voxkit.film import *
from voxkit import film

PH = os.path.join(HERE, 'photos')
VOICE = os.path.join(HERE, 'voice', 'full.mp3')
T = timeline(json.load(open(os.path.join(HERE, 'voice', 'words.json'))))
DUR = 17.0

# ------------------------------------------------------------------ cast
KATE = art.photo_cutout(os.path.join(PH, 'kate.webp'), (20, 0, 440, 650), out_h=1000, fg_hint=[(230, 180, 70), (230, 450, 110)], bg_hint=[(20, 60, 18), (455, 60, 18), (450, 300, 12)])
BOOK = art.photo_cutout(os.path.join(PH, 'wm', 'chapo_0.jpg'), (130, 60, 760, 1270), out_h=700, fg_hint=[(500, 520, 230)], bg_hint=[(60, 200, 50), (950, 200, 50), (80, 700, 40), (930, 700, 40)])
BOSS = art.photo_cutout(os.path.join(PH, 'penn_handshake.webp'), (262, 38, 200, 278), out_h=1000, core=False, fg_hint=[(352, 92, 26), (360, 200, 40), (340, 270, 30), (400, 260, 25)],
                        bg_hint=[(250, 40, 8), (465, 60, 8), (470, 200, 6), (290, 60, 12), (440, 55, 16), (300, 40, 10), (420, 40, 10), (455, 120, 8), (395, 45, 12), (380, 40, 8), (405, 70, 7), (275, 80, 8)])
def _outlined(spr, px=9, col=(.05, .03, .03)):
    a = spr[..., 3]; o = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1)))
    out = np.zeros_like(spr); out[..., :3] = col; out[..., 3] = o; return art.paste(out, spr, 0, 0)
HORNS = _outlined(fit(cv2.copyMakeBorder(art.horns(col=np.array([.95, .10, .06], np.float32)), 14, 14, 14, 14, cv2.BORDER_CONSTANT, value=0), 440))
KH = fit(KATE, h=300); BH = fit(BOOK, h=260)

# ------------------------------------------------------------------ props
FLAG = art.flag_mx(1000, 572); FLAG_S = fit(FLAG, 220); F_US = art.flag_us(1000, 530)
MTN_A = art.mountains(2600, 700, 3, np.array([.42, .26, .20], np.float32), .55, 7); MTN_B = art.mountains(2600, 700, 8, np.array([.24, .17, .28], np.float32), .45, 4)
BILLS = [art.bill(seed=i) for i in range(3)]; BUNDLE = art.cash_bundle(); BRICK = art.brick(); BAG = art.baggie()
BARS = art.jail_bars(820, 1200); BARS_L = BARS[:, :410].copy(); BARS_R = BARS[:, 410:].copy()
RAYS_R = art.rays(1800, 12, art.RED, 0.55); RAYS_B = art.rays(1800, 14, np.array([.15, .25, .65], np.float32), 0.45); RAYS_G = art.rays(1800, 14, art.MXG, 0.45)
WANTED = art.wanted(BOOK, 520, 720, 4); PIN = art.pin()
RED = art.RED; GLOW_RED = (0.95, 0.06, 0.04); WHITE = np.array([.95, .93, .86], np.float32)
LOOT = [BILLS[0], BRICK, BUNDLE, BAG, BILLS[1], BRICK, BILLS[2], BAG]          # money AND drugs falling


def scene_bg(rays, mtn=True, flag=True, fy=-640, fs=1.05):
    els = [BG(rays, -150)]
    if flag: els.append(E(FLAG, 0, fy, fs, r=-.02, d=.55, wv=20, wob=0, sh=.3))
    if mtn: els += [E(MTN_B, 0, 560, 1.0, d=.7, wob=0, sh=.2), E(MTN_A, 150, 760, 1.0, d=.35, wob=0, sh=.3)]
    return els


def route(pts, t0, spr, n=6, speed=0.5, s=0.5):
    """Bricks travelling along a dashed smuggling route."""
    def fn(fr, t, ox, oy):
        if t < t0: return
        for i in range(n):
            u = ((t - t0) * speed + i / n) % 1.0
            if (t - t0) * speed < i / n: continue
            j = u * (len(pts) - 1); a, b = pts[int(j)], pts[min(len(pts) - 1, int(j) + 1)]; f = j - int(j)
            fr.put(spr, ox + lerp(a[0], b[0], f), oy + lerp(a[1], b[1], f), s * min(1, u * 8) * min(1, (1 - u) * 8), rot=0.25 * math.sin(i + t * 3), depth=-0.05, shadow=0.5)
    return Fn(fn)


tw = T('woman'); tc = T('caught'); te = T('escaped')
SMUG = film.arc(0, 620, 0, -380, .45, 40)
SHOTS = [
 # 0 - "Because of this woman," - she is the devil of the story
 dict(t=0.0, els=scene_bg(RAYS_R) + [rain(LOOT, 0.0, 1.3, 14, 3, .6),
      E(HORNS, 0, -530, 1.15, d=0, t=tw, a='slam', glow=GLOW_RED, sh=.5),
      E(KATE, 0, 20, 1.0, t=0.03, a='pop', dur=.25, glow=GLOW_RED, breath=.012),
      E(L('THIS WOMAN', 640), 0, 660, r=-.05, d=-.1, t=tw + .1, a='slam')],
      cam=[(0, 0, 60, 1.18), (1.5, 0, -20, 1.04)]),
 # 1 - "the world's most wanted drug lord got caught" - the boss, then the bars
 dict(t=T('the') - .1, els=scene_bg(RAYS_R, fy=-700) + [rain(LOOT, T('the'), tc + .8, 20, 4, .62),
      *[E(BRICK, x, y, .85, r=.05 * (-1) ** i, d=.15, t=T('drug') + i * .06, a='rise', wob=.01) for i, (x, y) in enumerate(((-420, 700), (-420, 570), (420, 700), (420, 570), (-400, 440), (400, 440)))],
      E(BOSS, 0, 40, 1.0, t=T('world\'s'), a='rise', glow=(.9, .05, .04), breath=.012),
      E(L('MOST WANTED', 660), 0, -700, r=-.04, d=-.1, t=T('wanted'), a='slam'),
      E(BARS, 0, 40, 1.0, d=-.08, t=tc, a='slam', wob=0, sh=.7),
      E(ST('CAUGHT', 640), 0, 600, r=-.12, d=-.15, t=tc + .15, a='slam', sh=0),
      flashes([(tc + .02, 0, 0)])],
      cam=[(1.4, 0, 60, 1.0), (3.6, 0, 20, 1.04), (4.6, 0, 0, 1.09)]),
 # 2 - "Give me sixty seconds, and I'll show you how it happened."
 dict(t=T('give') - .12, els=scene_bg(RAYS_B, mtn=False) + [stopwatch(T('give')),
      orbit([(BUNDLE, .8), (BRICK, .7), (FLAG_S, 1), (BAG, .9), (BH, 1), (BRICK, .6), (KH, 1), (BUNDLE, .7)], T('sixty')),
      E(L('60 SECONDS', 620), 0, 650, r=-.04, d=-.1, t=T('sixty'), a='slam')], cam=[(4.6, 0, 0, .98), (7.0, 0, 0, 1.06), (8.0, 0, -40, 6.0)]),
 # 3 - "Joaquin Guzman. El Chapo. Boss of the Sinaloa Cartel."
 dict(t=T('joaquin') - .12, els=scene_bg(RAYS_G) + [rain(LOOT, T('boss') - .3, T('cartel') + .6, 16, 7, .6),
      E(art.wanted(BOOK, 380, 520, 9), -400, -260, .8, r=-.15, d=.3, t=T('joaquin') + .2), E(PIN, -400, -440, .8, d=.3, t=T('joaquin') + .4, quiet=True),
      *[E(BUNDLE, x, y, .85, r=.05 * (-1) ** i, d=.15, t=T('boss') + i * .06, a='rise', wob=.01) for i, (x, y) in enumerate(((-420, 700), (-420, 600), (420, 700), (420, 600), (-400, 500), (400, 500)))],
      E(BOSS, 60, -20, 1.0, t=T('joaquin'), a='rise', glow=(.9, .05, .04), breath=.012),
      E(L('JOAQUÍN GUZMÁN', 760, WHITE), 0, -720, r=.03, d=-.12, t=T('joaquin') + .05, a='L', out=T('el') - .1),
      E(L('EL CHAPO', 560), 0, -720, r=-.05, d=-.1, t=T('el'), a='slam'),
      E(L('SINALOA CARTEL', 760), 0, 620, r=.03, d=-.1, t=T('sinaloa'), a='slam')],
      cam=[(8.0, 0, 60, 1.0), (13.0, 0, 0, 1.07)]),
 # 4 - "He flooded America with cocaine, and he escaped prison twice."
 dict(t=T('he') - .12, els=[BG(RAYS_R, 0), E(F_US, 0, -650, 1.0, r=.02, d=.5, wv=18, wob=0, t=T('flooded'), a='drop'), E(FLAG, 0, 700, .95, r=-.02, d=.5, wv=18, wob=0),
      S(SMUG, T('flooded'), .7, RED, 14, dash=True), route(SMUG, T('flooded') + .2, BRICK, 7, .55, .8),
      E(L('COCAINE', 560), 0, -300, r=-.06, d=-.1, t=T('cocaine'), a='slam'), rain([BRICK, BAG, BRICK, BILLS[0]], T('america'), T('and') + .6, 16, 11, .6),
      E(BOSS, 0, 60, .62, d=-.06, t=te - .45, a='rise', breath=.015, out=te + .35),
      E(BARS_L, -205, 40, .9, d=-.1, t=te - .35, a='drop', wob=0, out=None), E(BARS_R, 205, 40, .9, d=-.1, t=te - .35, a='drop', wob=0),
      Fn(lambda fr, t, ox, oy: None),
      E(ST('ESCAPED 2X', 680), 0, 330, r=-.1, d=-.15, t=T('twice'), a='slam', sh=0)],
      cam=[(12.9, 0, -150, 1.0), (14.9, 0, -60, 1.03), (16.0, 0, 120, 1.05), (17.0, 0, 140, 1.08)]),
]


# prison bars split open on "escaped": slide the two halves apart
_bl, _br = SHOTS[4]['els'][8], SHOTS[4]['els'][9]
def _bars_split(fr, t, ox, oy):
    k = eout(seg(t, te, te + .45), 3)
    _bl.x = -205 - 520 * k; _bl.r = -0.35 * k; _br.x = 205 + 520 * k; _br.r = 0.35 * k
SHOTS[4]['els'][10] = Fn(_bars_split)
SHOTS[4]['els'][7], SHOTS[4]['els'][10] = SHOTS[4]['els'][10], SHOTS[4]['els'][7]   # update positions before drawing the bars


def grade(img, t):
    """Mexico night grade: cool blue shadows, warm red highlights (no edge lights)."""
    lum = img.mean(2, keepdims=True); sh = (1 - lum) ** 2; hi = lum ** 2
    return img * (1 + sh * (np.array([.62, .78, 1.40], np.float32) - 1) * .5 + hi * (np.array([1.22, .90, .82], np.float32) - 1) * .4)


def extra(add):
    for i in range(28): add(film.tick(), T('give') + .1 + i * 2.2 / 28, 0.06)
    add(film.riser(1.0), tc - 1.0, 0.13)
    add(film.thump(60, 30, 1.0, .3), tc, 0.25); add(film.nburst(0.4, 1500, 8000, 0.08), tc + .01, 0.08)        # cell-door clang
    n = int(.5 * film.SR); tt = np.arange(n) / film.SR; add(np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / .12) * .5 + np.sin(2 * np.pi * 1210 * tt) * np.exp(-tt / .07) * .3, tc, 0.08)
    add(np.sin(2 * np.pi * 410 * tt) * np.exp(-tt / .12) * .5, te, 0.06); add(film.whoosh(.45, 300, 3000, .4), te, 0.12)
    for i in range(14): add(film.nburst(0.12, 1500, 6000, 0.03), 0.3 + i * .3, 0.02)


SHOW = Show(SHOTS, DUR, VOICE, grade=grade, sfx_extra=extra, floaters_cols=(PAPER, art.RED, np.array([.15, .3, .9], np.float32), art.MXG, PAPER_LT, WHITE))
if __name__ == '__main__': run(SHOW, sys.argv)
