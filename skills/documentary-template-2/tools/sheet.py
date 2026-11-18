#!/usr/bin/env python3
"""Contact sheet of images, numbered, so they can be LOOKED AT before use (photos) or checked after a stills run.

    python3 tools/sheet.py photos/wm sheet.jpg        # every image in a folder (prints index -> file name)
    python3 tools/sheet.py stills sheet.jpg 6         # 6 per row"""
import sys, glob, os, cv2, numpy as np
src, out = sys.argv[1:3]; per = int(sys.argv[3]) if len(sys.argv) > 3 else 8; S = 300
fs = sorted(f for e in ('jpg', 'jpeg', 'png') for f in glob.glob(os.path.join(src, '*.' + e))); tiles = []
for i, f in enumerate(fs):
    im = cv2.imread(f)
    if im is None: continue
    h, w = im.shape[:2]; k = S / max(h, w); im = cv2.resize(im, (max(1, int(w * k)), max(1, int(h * k)))); t = np.full((S + 26, S, 3), 40, np.uint8); t[:im.shape[0], :im.shape[1]] = im
    cv2.putText(t, f'{i} {os.path.basename(f)[:22]}', (4, S + 19), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 0), 1, cv2.LINE_AA); tiles.append(t); print(i, os.path.basename(f), f'{w}x{h}')
blank = np.full((S + 26, S, 3), 40, np.uint8); rows = [np.hstack(tiles[i:i + per] + [blank] * (per - len(tiles[i:i + per]))) for i in range(0, len(tiles), per)]
cv2.imwrite(out, np.vstack(rows)); print('wrote', out)
