"""Synthesise a sound-effects track from an event list (no samples needed).

  python3 sfx.py events.json out.wav

events.json:
  {"dur": 113.3,
   "whoosh":   [1.95, 5.7, 11.75],            one per transition (use the scene-change times)
   "thud":     [[20.62, 0.9], [72.0, 1.0]],   [time, strength] for stamps, slams, drops
   "pop":      [2.45, 3.72, 3.95],            object entrances
   "scribble": [12.2, 26.1],                  drawn-on strokes (ticks, crosses, highlighter)
   "rewind":   [14.5],                        tape-rewind chirp
   "sizzle":   [[0.0, 2.0], [56.9, 3.1]],     [time, length] cooking beds
   "rumble":   [[29.9, 6.8]]}                 [time, length] furnace / machinery bed
Mix it UNDER the voice at about 0.4 gain (see SKILL.md); effects support the picture, they should never mask a word.
"""
import sys, json, wave
import numpy as np
ev = json.load(open(sys.argv[1])); SR, DUR = 44100, float(ev['dur'])
rng = np.random.RandomState(3); mix = np.zeros((int(SR * DUR) + SR, 2), np.float32)
def lpf(x, n): return np.convolve(x, np.ones(n, np.float32) / n, 'same') if n > 1 else x
def noise(n): return rng.randn(n).astype(np.float32)
def put(t, s, gain=1.0, pan=0.0):
    i = int(t * SR); n = min(len(s), len(mix) - i)
    if i < 0 or n <= 0: return
    mix[i:i + n, 0] += s[:n] * gain * (1 - max(0, pan)); mix[i:i + n, 1] += s[:n] * gain * (1 + min(0, pan))
def whoosh(d=.44, bright=10):
    n = int(SR * d); x = noise(n); m = np.linspace(0, 1, n) ** 1.5
    return ((lpf(x, bright * 3) * (1 - m) + lpf(x, max(1, bright // 2)) * m) * np.sin(np.linspace(0, np.pi, n)) ** 2 * 1.6).astype(np.float32)
def thud(d=.45, f0=95):
    n = int(SR * d); t = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(f0 * np.exp(-t * 9) + 38) / SR
    return (np.sin(ph) * np.exp(-t * 9) + lpf(noise(n), 6) * np.exp(-t * 60) * .6).astype(np.float32)
def pop(f=620, d=.09):
    t = np.arange(int(SR * d)) / SR; return (np.sin(2 * np.pi * (f + 900 * t) * t) * np.exp(-t * 45)).astype(np.float32)
def scribble(d=.28):
    n = int(SR * d); return (lpf(noise(n), 4) * np.sin(np.linspace(0, np.pi, n)) ** .5 * (.6 + .4 * np.sin(np.linspace(0, 40, n)))).astype(np.float32)
def rewind(d=.9):
    n = int(SR * d); t = np.arange(n) / SR; f = 300 + 1500 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 28 * t)))
    return ((tone * .5 + lpf(noise(n), 5) * .5) * np.sin(np.linspace(0, np.pi, n)) ** .7).astype(np.float32)
def bed(d, kind):
    n = int(SR * d); env = np.minimum(1, np.linspace(0, 6, n)) * np.minimum(1, np.linspace(6, 0, n))
    if kind == 'rumble': return lpf(noise(n), 60) * env
    x = noise(n); x = x - lpf(x, 8); crack = ((rng.rand(n) > .9993) * rng.rand(n) * 6).astype(np.float32)
    return ((x * .35 + lpf(crack, 3)) * env).astype(np.float32)
for i, t in enumerate(ev.get('whoosh', [])): put(t - .2, whoosh(.44, 8 + i % 5), .16, (-1) ** i * .25)
for t, g in ev.get('thud', []): put(t, thud(), .5 * g)
for i, t in enumerate(ev.get('pop', [])): put(t, pop(520 + (i * 97) % 380), .12, ((i * 37) % 7 - 3) / 6)
for t in ev.get('scribble', []): put(t, scribble(), .1)
for t in ev.get('rewind', []): put(t, rewind(), .16)
for t, d in ev.get('sizzle', []): put(t, bed(d, 'sizzle'), .07)
for t, d in ev.get('rumble', []): put(t, bed(d, 'rumble'), 1.1)
mix = np.tanh(mix * 1.2) * .8
w = wave.open(sys.argv[2], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix[:int(SR * DUR)], -1, 1) * 32767).astype(np.int16).tobytes()); w.close(); print('wrote', sys.argv[2])
