#!/bin/bash
# Join rendered frames with the voiceover (and optional sound effects) into the final MP4.
#   encode.sh <frames_dir> <voice.mp3> <duration_sec> <out.mp4> [sfx.wav] [sfx_gain=0.4]
# crf 24 with a 5 Mbit cap keeps a 2-minute 1080x1920 film around 70 MB; the film grain makes lower crf balloon.
set -e
F=$1; V=$2; D=$3; O=$4; S=$5; G=${6:-0.4}
FADE=$(python3 -c "print($D-0.4)")
if [ -n "$S" ]; then
  AF="[1:a]apad=whole_dur=$D[v];[2:a]volume=$G[s];[v][s]amix=inputs=2:normalize=0:duration=first,atrim=0:$D,afade=t=out:st=$FADE:d=0.4[a]"
  ffmpeg -v error -y -framerate 30 -i "$F/%05d.jpg" -i "$V" -i "$S" -filter_complex "$AF" -map 0:v -map "[a]" \
    -c:v libx264 -crf 24 -maxrate 5M -bufsize 10M -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -t "$D" -movflags +faststart "$O"
else
  ffmpeg -v error -y -framerate 30 -i "$F/%05d.jpg" -i "$V" -af "apad=whole_dur=$D,afade=t=out:st=$FADE:d=0.4" \
    -c:v libx264 -crf 24 -maxrate 5M -bufsize 10M -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -t "$D" -movflags +faststart "$O"
fi
ls -la "$O"
