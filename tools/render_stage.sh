#!/bin/bash
# Render one stage at final quality, encode each shot to renders/<stage>_<firstframe>.mp4 and push.
# Usage: tools/render_stage.sh <stage> [WxH] [samples]
set -e
cd "$(dirname "$0")/.."
ST=$1; RES=${2:-720x1280}; SPP=${3:-8}
bash setup.sh
python3 render.py $ST frames/$ST --res $RES --samples $SPP 2>&1 | grep -E "^\[|Error|Traceback" 
mkdir -p renders
python3 - "$ST" <<'PY'
import os, sys, subprocess
st = sys.argv[1]
fr = sorted(int(f[:5]) for f in os.listdir(f'frames/{st}') if f.endswith('.jpg'))
runs, cur = [], [fr[0]]
for f in fr[1:]:
    if f == cur[-1] + 1: cur.append(f)
    else: runs.append(cur); cur = [f]
runs.append(cur)
for r in runs:
    out = f'renders/{st}_{r[0]:05d}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '24', '-start_number', str(r[0]), '-i', f'frames/{st}/%05d.jpg', '-frames:v', str(len(r)),
                    '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', out], check=True)
    print(out, len(r), 'frames')
PY
git add renders/${ST}_*.mp4
git commit -qm "Add rendered shots for the $ST stage"
BR=$(git rev-parse --abbrev-ref HEAD)
for i in 1 2 3 4 5 6; do
  git pull -q --rebase origin "$BR" && git push -q -u origin "$BR" && echo PUSHED && break
  sleep $((i * 5))
done
