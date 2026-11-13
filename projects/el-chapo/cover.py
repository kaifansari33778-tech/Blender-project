"""El Chapo cover (1080x1920). Usage: python3 cover.py [out.png]"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('chapo_show', os.path.join(HERE, 'show.py')); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
import numpy as np, cv2
from voxkit.core import *
from voxkit.film import E, L, ST, fit

els = M.scene_bg(M.RAYS_R, mtn=True, flag=True, fy=-520, fs=1.25) + [
    E(M.WANTED, 400, -60, .5, r=.14, d=-.05, wob=0), E(M.PIN, 400, -250, .8, d=-.05, wob=0),
    E(M.BOSS, -255, 300, .86, d=-.02, glow=M.GLOW_RED, wob=0), E(M.BARS, -255, 300, .86, d=-.04, wob=0, sh=.7),
    E(M.HORNS, 175, -400, 1.15, d=0, glow=M.GLOW_RED, wob=0, sh=.5), E(M.KATE, 175, 140, .96, d=0, glow=M.GLOW_RED, wob=0),
    *[E(M.BUNDLE, x, y, .95, r=r, d=-.1, wob=0) for x, y, r in ((-380, 740, .25), (-120, 800, -.1), (330, 760, .2), (440, 640, -.3))],
    *[E(M.BRICK, x, y, .85, r=r, d=-.12, wob=0) for x, y, r in ((-470, 620, -.2), (180, 830, .15), (-250, 840, .1))],
    E(M.BAG, 60, 700, 1.2, r=.3, d=-.12, wob=0), E(M.BILLS[0], 470, 520, .8, r=.5, d=-.1, wob=0), E(M.BILLS[1], -480, 120, .7, r=-.5, d=-.1, wob=0),
    E(ST('CAUGHT', 560), -270, 600, r=-.18, d=-.2, sh=0, wob=0),
    E(L('HOW EL CHAPO', 1000), 0, -800, r=-.03, d=-.12, wob=0), E(L('GOT CAUGHT', 860), 0, -640, r=.02, d=-.12, wob=0),
    E(L('BECAUSE OF THIS WOMAN', 900, M.WHITE), 0, 800, r=-.02, d=-.15, wob=0)]
fr = Frame(Cam(0, 0, 1.0), dof=3.0); M.default_bg(fr, 3.0)
for e in els: M.draw_el(fr, e, 3.0, 0, 0)
img = np.clip(M.grade(post(fr.c, 7, tilt=0.5, expo=1.12), 3.0), 0, 1)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cover.png')
cv2.imwrite(out, (img * 255 + .5).astype(np.uint8)[..., ::-1]); print('wrote', out)
