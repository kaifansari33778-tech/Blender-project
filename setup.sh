#!/bin/bash
# Installs Blender (as a Python module) and fetches the CC0 MakeHuman-derived character data.
set -e
pip install -q bpy numpy 2>&1 | tail -1 || true
A=${WJ_ASSETS:-$HOME/.cache/wj_assets}
mkdir -p "$A"
fetch() {  # name url commit
  if [ ! -d "$A/$1/.git" ]; then
    git init -q "$A/$1" && git -C "$A/$1" remote add origin "$2"
    git -C "$A/$1" fetch -q --depth 1 origin "$3" && git -C "$A/$1" checkout -q FETCH_HEAD
  fi
}
fetch mpfb2 https://github.com/makehumancommunity/mpfb2.git 6ff1eb358f6c1959ced77e79e6dd2406d9a71f49
fetch vrm-avatar-maker https://github.com/ffunch/vrm-avatar-maker.git 5950f3cf34e21261d3eac65bb391b0bd077c839a
python3 -c "import bpy; print('bpy', bpy.app.version_string)"
