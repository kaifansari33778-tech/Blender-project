#!/bin/bash
# Contact sheets for looking at video without playing it.
#   sheets.sh video <file.mp4> <outdir> [fps=2]      timestamped tiles of a reference or finished video (6x3 per sheet)
#   sheets.sh strip <file.mp4> <out.jpg> <start_sec> 10 frames at 10 fps from start_sec: use on every transition
#   sheets.sh frames <frames_dir> <out.jpg> [cols=8] tile preview frames rendered with a step (e.g. every 30th)
set -e
case "$1" in
  video) mkdir -p "$3"; ffmpeg -v error -i "$2" -vf "fps=${4:-2},scale=240:-2,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x3" "$3/s_%02d.jpg";;
  strip) ffmpeg -v error -y -ss "$4" -i "$2" -t 1.05 -frames:v 1 -update 1 -vf "fps=10,scale=180:-2,tile=10x1" "$3";;
  frames) n=$(ls "$2"/*.jpg | wc -l); c=${4:-8}; r=$(( (n + c - 1) / c ))
          ffmpeg -v error -y -pattern_type glob -i "$2/*.jpg" -frames:v 1 -update 1 -vf "scale=270:-2,tile=${c}x${r}" "$3";;
  *) sed -n 2,5p "$0";;
esac
