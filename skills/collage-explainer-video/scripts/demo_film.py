"""Minimal working film: copy this file and replace the art, scenes, transitions and captions.
Needs no downloaded images (everything here is generated), so it doubles as an install check:
    python3 demo_film.py /tmp/work /tmp/work/frames 0 240 30      # one frame per second
    python3 demo_film.py /tmp/work /tmp/work/frames               # every frame (run ranges in parallel)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
from engine import place, obj, mk, pre, grade, pop, seg, ease, lerp, bg_pan, new

E.init(sys.argv[1])

# ---- art: build everything once at import time, graded for the scene it lives in ----
YEL = E.flat_bg((.82, .62, .09), seed=21)                       # evidence-desk yellow
PUR = E.flat_bg((.30, .08, .42), seed=9)                        # social-media purple
CARD = mk(grade(pre(E.msg_card()), (1, .95, .84), .5, bot=.86))  # the forwarded-message card
T_A = mk(grade(pre(E.tile('Al', '13', 'ALUMINIUM')), (1, .9, .6), .25), 26, .7)
T_B = mk(grade(pre(E.tile('Pb', '82', 'LEAD', light=False)), (1, .9, .6), .12, rim=(.9, .7, .2), rim_k=.5), 26, .7)
CROSS = E.cross(); TICK = E.tick()
BEAD = E.sphere(26, (.62, .66, .72))

# ---- scenes: fn(t) with ABSOLUTE film time, returns a canvas ----
def s_rumour(t):
    c = new(); bg_pan(c, PUR, 750, 1200, 1.0)
    for i, (t0, dx, dy, r) in enumerate(((1.6, -70, -150, -5), (1.3, 60, -75, 4), (0.3, 0, 0, -2))):
        p = pop(t, t0)                                           # overshoot entrance
        if p > 0:                                                # rx tilt on entry + ry idle wobble = the "3D" feel
            obj(c, CARD, 540 + dx, 1000 + dy + (1 - p) * 220, .96 * p, r + (1 - p) * 8, rx=(1 - p) * 55 + 6, ry=math.sin(t * 1.3 + i) * 7, depth=1.2 + i * .35)
    E.draw_on(c, CROSS, t, 2.6, 540, 1000, 3.0, depth=1.9)       # hand-drawn red cross, stroke by stroke
    return c
def s_tiles(t):
    c = new(); bg_pan(c, YEL, 750, 1200, 1.0)
    p = pop(t, 4.2)
    if p > 0: obj(c, T_A, 320, 1010, .95 * p, -5, rx=22, ry=math.sin(t * 1.1) * 6)
    shake = E.slam(c, t, 5.6, T_B, 770, 1030, 1.0, 4)            # slam with dust ring; returns camera shake
    if shake: c[:] = __import__('numpy').roll(c, int(shake), 0)
    for i in range(12):                                          # simple looping particles
        ph = (t * .4 + i / 12) % 1
        place(c, BEAD, 200 + i * 60, 1700 - ph * 600, .5, 0, math.sin(ph * math.pi), depth=1.4)
    return c

film = E.Film(
    dur=8.0,
    scenes=[(0.0, s_rumour), (4.0, s_tiles)],
    trans=[(3.8, 4.2, 4.0, 'h')],                                # whip pan centred on the scene change
    captions=[(0.3, 1.3, 'YOU HEARD', 'THE RUMOUR', E.PNK), (4.2, 5.6, 'THE REAL ISSUE', 'IS LEAD', E.RED)])
if __name__ == '__main__':
    film.main()
