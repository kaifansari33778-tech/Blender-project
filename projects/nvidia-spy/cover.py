"""NVIDIA story cover (1080x1920). Usage: python3 cover.py [out.png]"""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('nv_show', os.path.join(HERE, 'show.py')); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
import numpy as np, cv2
from voxkit.core import *
from voxkit import art
E, L, ST, BG, fit = M.E, M.L, M.ST, M.BG, M.fit

A = fit(M.ABUST, h=930); J = fit(M.JSEAT, h=980)
els = [BG(M.RAYS_R, -150, 0), E(M.FLAG, 0, -380, 1.5, r=-.03, d=.5, wv=20, wob=0),
       E(M.DOCS[0], -430, -80, .8, r=-.2, d=.3, wob=0), E(M.DOCS[2], 430, 60, .8, r=.15, d=.3, wob=0), E(M.NVCARD, 350, -200, .85, r=.1, d=.15, wob=0),
       E(A, -165, 200, d=0, wob=0), E(J, 255, 170, d=0, wob=0),
       E(M.HEART, 40, -330, .85, r=.1, d=-.1, wob=0),
       *[E(M.BILLS[i % 3], x, y, .8, r=r, d=-.08, wob=0) for i, (x, y, r) in enumerate(((-420, 560, .4), (430, 600, -.35), (-340, 790, -.2), (360, 800, .3), (0, 820, .1)))],
       E(M.SCHIP, -460, 330, 1.3, r=.3, d=-.1, wob=0), E(M.SCHIP, 470, 400, 1.1, r=-.2, d=-.1, wob=0), E(M.NVS, 430, -470, .9, r=.2, d=-.05, wob=0),
       E(L('$470 BILLION', 1000), 0, -800, r=-.03, d=-.12, wob=0), E(L('FOR ONE RELATIONSHIP', 960), 0, -630, r=.02, d=-.12, wob=0),
       E(M.WHITE('THE NVIDIA SCANDAL', 840), 0, 800, r=-.02, d=-.15, wob=0)]
fr = Frame(Cam(0, 0, 1.0), dof=3.0)
fr.put(M.FAR, 0, 0, 2.6, depth=3.0, wrap=True, blur=0, shadow=0); fr.put(M.CANYON, 0, 0, 1.2, depth=1.2, wrap=True, shadow=0)
for e in els: M.draw_el(fr, e, 3.0, 0, 0)
img = np.clip(post(fr.c, 7, tilt=0.5, expo=1.12), 0, 1)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'cover.png')
cv2.imwrite(out, (img * 255 + .5).astype(np.uint8)[..., ::-1]); print('wrote', out)
