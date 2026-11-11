"""Shot driver: each stage builds one set + cast and returns [(t0, t1, update)] in film seconds."""
import bpy, sys, os, time, importlib, math
from mathutils import Vector
from . import stage as st
from .anim import noise

FPS = 24
STAGES = ['palace', 'london', 'pond', 'sewer', 'market', 'graveyard', 'plague']


def handheld(cam, t, amt=1.0, seed=0.0):
    """tiny organic camera drift so nothing ever feels locked off"""
    cam.rotation_euler.rotate_axis('X', noise(t, seed + 1, 1.3) * 0.0035 * amt)
    cam.rotation_euler.rotate_axis('Y', noise(t, seed + 2, 1.1) * 0.0035 * amt)
    cam.rotation_euler.rotate_axis('Z', noise(t, seed + 3, 0.9) * 0.002 * amt)


def shoot(cam, t, pos, tgt, lens=50, fstop=None, focus=None, shake=1.0, roll=0.0, seed=0.0):
    st.look(cam, pos, tgt, lens, roll=roll, fstop=fstop, focus=focus)
    handheld(cam, t, shake, seed)


def render_stage(name, out, res=(720, 1280), samples=12, only=None, every=1, frames=None):
    scene, cam = st.new_scene(res, samples)
    mod = importlib.import_module('wj.stages.' + name)
    t0 = time.time()
    shots = mod.build(scene, cam)
    print(f'[{name}] built in {time.time() - t0:.1f}s, {len(shots)} shots', flush=True)
    os.makedirs(out, exist_ok=True)
    for i, (a, b, fn) in enumerate(shots):
        fa, fb = round(a * FPS), round(b * FPS)
        for f in range(fa, fb):
            if frames is not None and f not in frames:
                continue
            if frames is None and (f - fa) % every:
                continue
            if only is not None and i not in only:
                continue
            path = os.path.join(out, f'{f:05d}.jpg')
            if os.path.exists(path):
                continue
            t = f / FPS
            fn(t)
            scene.frame_set(f)
            scene.render.filepath = path
            t1 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'[{name}] shot {i} frame {f} {time.time() - t1:.1f}s', flush=True)
