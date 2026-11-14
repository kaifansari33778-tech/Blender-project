"""Dark America cover (1080x1920), 3D pop-up diorama style. Usage: python3 cover.py [out.png]"""
import sys, os, math, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from voxkit.core import *
from voxkit import art, art3d, kit3d as K
from voxkit.pop3d import Cam3, Card, World
sp = importlib.util.spec_from_file_location('test20', os.path.join(HERE, 'test20.py')); Q = importlib.util.module_from_spec(sp); sys.modules['test20'] = Q; sp.loader.exec_module(Q)
Z = Q.Z; pi = math.pi
cam = Cam3(0, 3.3, -5.2, yaw=0, pitch=.06, f=1150)
world = World(art3d.ground_tex(), art3d.sky((.10, .10, .24), (.96, .50, .30), 7), fog=(.70, .50, .44), fog_d=90, focus=8.0, dof=10)
C = []; A = C.append
A(Card(Z.BIGFLAG, 0, 60, 120, y=6, wv=22, shadow=0, blur=1.0, fog=False, alpha=.95, ph=2))
tows = [K.tower(k, col=c, lit=.45) for k, c in (('empire', (.26, .26, .34)), ('chrysler', (.30, .30, .38)), ('wtc', (.22, .28, .38)))] + [K.tower('block', w=320 + 40 * (i % 3), h=800 + 140 * (i % 4), col=(.24 + .03 * (i % 3), .24, .32), seed=i, lit=.4) for i in range(6)]
for i, (x, z, w) in enumerate([(0, 34, 9), (9, 35, 8), (-9.5, 36, 9)] + [(x, 40 + (j % 2) * 4, 9) for j, x in enumerate((-24, -16, -5, 5, 16, 24))]): A(Card(tows[i], x, z, w, shadow=.3))
A(Card(Z.HOUSE, 0, 12.0, 22)); A(Card(Z.INWALL, 0, 10.0, 5.6)); A(Card(Z.STRAW, 0, 7.55, 5.5, tilt=pi / 2, shadow=0))
A(Card(Z.SIDEWALL, -2.8, 8.75, 2.5, yaw=pi / 2, shadow=0)); A(Card(Z.SIDEWALL, 2.8, 8.75, 2.5, yaw=pi / 2, shadow=0)); A(Card(Z.BRANCH, -.3, 9.7, 5.0, y=2.2, shadow=0)); A(Card(Z.ROOF, 0, 7.5, 5.9, y=3.92, shadow=0))
A(Card(Z.ORANG, -1.75, 9.1, 1.6)); A(Card(Q.OTA, .3, 8.8, 2.9)); A(Card(Z.BARS, 0, 7.5, 5.6)); A(Card(Q.LOCK, 1.9, 7.42, .8, y=1.1, shadow=0, fog=False))
for i, (x, z, w) in enumerate(((-9.5, 10, 6), (9.6, 9.5, 6.5), (-8.5, 4.6, 5), (8.6, 4.2, 5))): A(Card(Q.TREES[i % 4], x, z, w))
for sx in (-1, 1): A(Card(Z.LAMP, sx * 4.2, 6.6, .62))
for i, (x, z) in enumerate(((-3.3, 5.6), (-2.2, 5.0), (2.3, 5.2), (3.4, 5.7), (-3.9, 4.4), (4.0, 4.5), (-2.9, 3.9), (3.0, 3.8))):
    p = Q.PEOPLE[(i * 5) % 12]; A(Card(p, x, z, 1.75 * p.shape[1] / p.shape[0]))
for spr, x, z, w, y in ((K.barrel(skull=True), -2.1, .9, 1.0, 0), (K.grave(), 2.15, .9, .95, 0), (K.bomb(), -1.05, .6, .45, 0), (K.syringe(), 1.05, .5, 1.2, .1), (K.vial(), -.25, .5, .34, 0), (art.gavel(), .3, .9, .9, 0)):
    A(Card(spr, x, z, w, y=y, fog=False, blur=0))
def lab(txt, sy, wf, col=ORANGE): A(Q.pin(art.label(txt, 150, col=np.asarray(col, np.float32), seed=len(txt)), cam, .5, sy, wf))
lab('THE DARK REALITY', .085, .94); lab('OF AMERICA', .175, .66); lab('9 TRUE STORIES', .935, .62, np.array([.95, .93, .86], np.float32))
img = world.render(cam, C, 7, 3.0)
img = post(img, 7, tilt=0.4, expo=1.1)
lum = img.mean(2, keepdims=True); img = np.clip((img * .82 + lum * .18) * np.float32([.96, .97, 1.08]), 0, 1)        # slightly cold and dark
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cover.png')
cv2.imwrite(out, (img * 255 + .5).astype(np.uint8)[..., ::-1]); print('wrote', out)
