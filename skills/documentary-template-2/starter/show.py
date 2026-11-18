"""Documentary Template 2 - STARTER PROJECT (copy this folder, replace the photos, voice and scenes).

    python3 show.py stills stills 1.5,5,9,12,14     # preview frames (360x640) - always do this first and LOOK at them
    python3 show.py render out                      # full render in 10 s segments (resumable)
    python3 show.py mux out final.mp4               # join + voice + sound

This demo is the first 15 s of a Bhopal 1984 video: three scenes, one zoom-through and one paper tear."""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))      # the folder that contains voxkit/
import numpy as np
from voxkit.dt2 import *

WORDS = json.load(open(os.path.join(HERE, 'voice', 'words.json'))); T = film.timeline(WORDS)       # T('word') / T('word', 2) = start time of its n-th occurrence
DUR = 15.3; VOICE = os.path.join(HERE, 'voice', 'full.mp3')                                        # DUR = length of the voice-over (ffprobe)
P = lambda name: load(os.path.join(HERE, 'photos', name))

# ---------------------------------------------------------------- plates: built ONCE at import (GrabCut is slow), never inside a scene function
F = P('factory.jpg'); FACT, GRASS = skyline_plate(F, tone=(1.02, .98, .90), sat=0, top=.06, bot=.62, band_y=.66, seed=1)                 # day, sepia
S = P('slum.jpg');    SLUM, ROOFS = skyline_plate(S, tone=(.62, .74, 1.0), sat=.10, gain=.62, top=.41, bot=.52, band_y=.60, seed=4, rim=0)  # graded to night
V = P('vessel.jpg');  VBG, VFG = pop_plate(V, rect=(.02, .16, .70, .80), tone=(1.03, .97, .86), seed=11)                                   # no sky: subject pops out
SKY_DAY = sky_plate((.30, .29, .28), (.80, .76, .66), 1); SKY_NIGHT = sky_plate((.03, .04, .10), (.16, .20, .36), 2, moon=True, stars=140)
T_1984 = big_text('1984', (.86, .30, .12)); T_RAAT = big_text('EK RAAT', (.90, .88, .80), 300, 2); T_KAISE = big_text('KAISE?', (.90, .88, .80), 380, 4); STOPW = dial('60')


# ---------------------------------------------------------------- scenes: one phrase, one full-frame image each.  fn(t, cam, a, b) -> list of Cards
def sc_factory(t, cam, a, b):            # "Kya aap jaante hain ki 1984 mein"
    C = [Card(SKY_DAY, 2 * math.sin(t * .2), 75, 130, y=-60, shadow=0, blur=1.5, fog=False)]       # far: drawn sky
    pop(C, T_1984, t, T('unnees'), 34, 17, 46)                                                      # big word BETWEEN sky and subject
    C += [Card(FACT, 0, 30, 58, y=-14.5, shadow=0, fog=False),                                      # subject, sky cut away
          Card(GRASS, -1, 15, 44, y=-9.5, shadow=0, fog=False)]                                     # nearer band -> parallax
    point(C, t, T('unnees') + .5, b, 3.0, 9.0, 27, 9)                                               # ONE arrow, because "this factory" needs pointing at
    hl(C, cam, t, '1984 MEIN', T('unnees'), b, .80, .52); return C

def sc_night(t, cam, a, b):              # "ek raat, ek zehreeli gas ne hazaaron logon ko neend mein hi maar diya ..."
    C = [Card(SKY_NIGHT, 0, 75, 130, y=-52, shadow=0, blur=1.2, fog=False)]
    pop(C, T_RAAT, t, a + .2, 40, 19, 46, t1=T('zehreeli') + .5)
    C.append(Card(SLUM, 0, 30, 62, y=-17, shadow=0, fog=False))
    gas(C, t, T('zehreeli') - .1, b)                                                                # motion inside the scene, in the accent colour
    C.append(Card(ROOFS, 1, 15, 46, y=-13.5, shadow=0, fog=False))
    hl(C, cam, t, 'ZEHREELI GAS', T('zehreeli'), T('neend') - .05, .80, .66, GASC); hl(C, cam, t, 'NEEND MEIN HI', T('neend'), b + .3, .80, .66); return C

def sc_vessel(t, cam, a, b):             # "Mujhe sirf 60 second dijiye, main aapko batata hoon yeh kaise hua"
    C = [Card(VBG, 0, 34, 46, y=-25, shadow=0, blur=2.2, fog=False)]                                # whole photo, dim and soft
    pop(C, T_KAISE, t, T('yeh'), 20, 17, 31, blur=None)
    C.append(Card(VFG, 0, 26, 36, y=-19.5, shadow=0, fog=False))                                    # the subject floats in front of it
    hang(C, STOPW, .6, 11, 4.6 * (1 + .04 * math.sin(t * 12.5)), 2.6, t, T('saath') - .25, ph=.6, swing=.45, L=16)   # prop lowered on a string
    hl(C, cam, t, 'SIRF 60 SECOND', T('saath'), T('main'), .80, .72); hl(C, cam, t, 'YEH KAISE HUA?', T('yeh'), b + .3, .80, .72); return C


SCENES = [dict(t=0, fn=sc_factory),
          dict(t=T('ek') - .06, fn=sc_night, trans='zoom'),                 # zoom-through
          dict(t=T('mujhe') - .05, fn=sc_vessel, trans=pi / 2, focus=26)]   # paper tear, horizontal (0 = vertical, +-0.6 = diagonal)
NUMBERS = {('unnees', 'sau', 'chauraasi'): '1984', ('saath', 'second'): '60 second'}      # spoken words -> what the typed caption shows
HITS = [T('unnees'), T('zehreeli'), T('neend'), T('saath'), T('yeh')]                      # every highlight box / big word gets a soft thump

def sfx(add, film, T):                   # optional scene sounds; keep them quiet (gains about .02 - .10)
    import numpy as np
    h = film._filt(np.random.default_rng(1).normal(0, 1, int(3.6 * film.SR)), 2500, 7000); add(h * np.minimum(1, np.arange(len(h)) / film.SR) * np.linspace(1, .2, len(h)), T('zehreeli'), .03)   # gas hiss
    for i in range(10): add(film.nburst(.02, 3000, 8000, .006), T('saath') + i * .25, .05)                                                                                            # stopwatch ticks

if __name__ == '__main__':
    Show(HERE, SCENES, WORDS, DUR, voice=VOICE, number_words=NUMBERS, hits=HITS, sfx=sfx).cli()
