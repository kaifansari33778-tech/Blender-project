"""Synthesised sound effects track. Usage: python3 sfx.py out.wav"""
import sys, wave
import numpy as np
SR, DUR = 44100, 113.3
rng = np.random.RandomState(3)
mix = np.zeros((int(SR * DUR) + SR, 2), np.float32)
def lp(x, k):
    """one-pole low-pass, k in (0,1]: smaller = darker"""
    y = np.empty_like(x); a = 0.0
    for i in range(len(x)): a += k * (x[i] - a); y[i] = a
    return y
def lp_fast(x, n):
    return np.convolve(x, np.ones(n, np.float32) / n, 'same') if n > 1 else x
def put(t, s, gain=1.0, pan=0.0):
    i = int(t * SR); n = min(len(s), len(mix) - i)
    if n <= 0: return
    mix[i:i + n, 0] += s[:n] * gain * (1 - max(0, pan)); mix[i:i + n, 1] += s[:n] * gain * (1 + min(0, pan))
def whoosh(d=.42, bright=10):
    n = int(SR * d); x = rng.randn(n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    a = lp_fast(x, bright * 3); b = lp_fast(x, max(1, bright // 2)); m = np.linspace(0, 1, n) ** 1.5
    return ((a * (1 - m) + b * m) * env).astype(np.float32) * 1.6
def thud(d=.45, f0=95):
    n = int(SR * d); t = np.arange(n) / SR
    f = f0 * np.exp(-t * 9) + 38; ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 9)
    click = lp_fast(rng.randn(n).astype(np.float32), 6) * np.exp(-t * 60) * .6
    return (body + click).astype(np.float32)
def pop(f=620, d=.09):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (f + 900 * t) * t) * np.exp(-t * 45)).astype(np.float32)
def scribble(d=.28):
    n = int(SR * d); x = lp_fast(rng.randn(n).astype(np.float32), 4)
    env = (np.sin(np.linspace(0, np.pi, n)) ** .5) * (0.6 + 0.4 * np.sin(np.linspace(0, 40, n)))
    return (x * env).astype(np.float32)
def rewind(d=.9):
    n = int(SR * d); t = np.arange(n) / SR
    f = 300 + 1500 * (t / d) ** 2; tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * t)))
    return ((tone * .5 + lp_fast(rng.randn(n).astype(np.float32), 5) * .5) * np.sin(np.linspace(0, np.pi, n)) ** .7).astype(np.float32)
def sizzle(d):
    n = int(SR * d); x = rng.randn(n).astype(np.float32); x = x - lp_fast(x, 8)
    env = np.minimum(1, np.linspace(0, 6, n)) * np.minimum(1, np.linspace(6, 0, n)); crack = (rng.rand(n) > .9993) * rng.rand(n) * 6
    return ((x * .35 + lp_fast(crack.astype(np.float32), 3)) * env).astype(np.float32)

WHOOSH = [1.95, 5.7, 11.75, 13.3, 16.62, 21.9, 25.3, 29.62, 36.9, 40.1, 42.9, 47.3, 48.75, 53.5, 56.8, 60.1, 64.5, 67.3, 68.2, 69.4, 72.7, 74.3, 78.0, 80.7, 87.4,
          92.2, 94.0, 96.2, 99.9, 102.6, 104.5, 107.9, 108.6, 110.4]
THUD = [(1.25, .5), (20.62, .9), (72.0, 1.0), (95.05, .7), (101.0, .9), (109.66, 1.0), (15.45, .4)]
POP = [2.45, 3.72, 3.95, 5.2, 5.34, 5.46, 6.62, 7.4, 8.4, 17.05, 18.5, 22.4, 23.1, 24.05, 30.4, 34.8, 35.5, 41.0, 43.3, 44.2, 49.3, 51.5, 55.0, 55.13, 55.26, 55.39, 55.52,
       57.9, 58.45, 64.6, 64.75, 65.6, 66.65, 69.75, 75.9, 76.9, 79.4, 81.0, 85.0, 87.7, 88.8, 89.05, 89.3, 90.0, 90.35, 90.7, 97.75, 105.7, 110.55, 110.7, 110.85, 112.15, 112.41, 112.67]
SCRIB = [12.2, 26.1, 28.9, 29.05, 38.15, 38.35, 65.3, 65.95, 67.0, 67.65, 68.85]
for i, t in enumerate(WHOOSH): put(t - .2, whoosh(.44, 8 + i % 5), .16, (-1) ** i * .25)
for t, g in THUD: put(t, thud(), .5 * g)
for i, t in enumerate(POP): put(t, pop(520 + (i * 97) % 380), .12, ((i * 37) % 7 - 3) / 6)
for t in SCRIB: put(t, scribble(), .1)
put(14.5, rewind(.92), .16)
put(0.0, sizzle(2.0), .07); put(37.0, sizzle(3.0), .05); put(56.9, sizzle(3.1), .09); put(92.2, sizzle(1.8), .07)
put(29.9, lp_fast(rng.randn(int(SR * 6.8)).astype(np.float32), 60) * np.minimum(1, np.linspace(0, 4, int(SR * 6.8))) * np.minimum(1, np.linspace(4, 0, int(SR * 6.8))), 1.1)   # furnace rumble
mix = np.tanh(mix * 1.2) * .8
w = wave.open(sys.argv[1], 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix[:int(SR * DUR)], -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print('sfx written', sys.argv[1])
