"""Post: captions (from the voice-over's own word timings), synthesized SFX bed, final 1080x1920 encode.
Usage: python3 post.py [--frames frames] [--out out/worst_jobs.mp4]"""
import json, os, sys, subprocess, wave, math, glob, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100; DUR = 89.25; FPS = 24
rng = np.random.default_rng(7)


# ------------------------------------------------------------------ captions
FIX = {'Purefinder.': 'Pure Finder.', 'Tosher': 'Tosher.', 'Boy': 'Boy.', 'Ratcatcher.': 'Rat Catcher.', 'Ratcatchers': 'Rat catchers', 'sixty': '60', 'dead': 'dead!"', 'Bring': '"Bring',
       'Number': 'Number', 'shouting,': 'shouting,'}


def captions(path):
    words = json.load(open(os.path.join(HERE, 'audio/words.json')))
    out = []
    for i, (w, t) in enumerate(words):
        if w == 'Tosher' and words[i + 1][0] != 'Toshers':
            pass
        w2 = FIX.get(w, w)
        if w == 'Tosher' and words[i + 1][0] != 'Toshers':
            w2 = w
        if w == 'Boy' and words[i - 1][0] != 'Whipping':
            w2 = w
        if w == 'dead' and words[i - 1][0] != 'your':
            w2 = w
        out.append((w2, t))
    chunks, cur = [], []
    for i, (w, t) in enumerate(out):
        cur.append((w, t))
        nxt = out[i + 1][1] if i + 1 < len(out) else DUR
        end_sent = w[-1] in '.!?,"' 
        chars = sum(len(x[0]) for x in cur) + len(cur) - 1
        gap = nxt - t > 0.75
        if len(cur) >= 3 or chars >= 15 or end_sent or gap or i + 1 == len(out):
            chunks.append((cur[0][1], min(nxt, t + 1.3), ' '.join(x[0] for x in cur)))
            cur = []
    def ts(x):
        h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
        return f'{h}:{m:02d}:{s:05.2f}'
    with open(path, 'w') as f:
        f.write('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n')
        f.write('[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n')
        f.write('Style: cap,Inter Black,78,&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,7,3,8,60,60,330,1\n')
        f.write('Style: num,Inter Black,92,&H0030D8FF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,8,3,8,60,60,322,1\n\n')
        f.write('[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
        for a, b, txt in chunks:
            style = 'num' if txt.startswith('Number') or txt.startswith('And Number') else 'cap'
            f.write(f'Dialogue: 0,{ts(a)},{ts(b)},{style},,0,0,0,,{{\\fad(60,40)\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}}{txt.upper()}\n')
    return chunks


# ------------------------------------------------------------------ sfx synthesis
def T(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))


def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (f / fc) ** 4 / (1 + (f / fc) ** 4), len(x))


def bp(x, lo, hi):
    return hp(lp(x, hi), lo)


def env(d, a, r, power=1.0):
    t = T(d)
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r) ** power


def reverb(x, decay=1.2, mix=0.35):
    n = int(decay * SR * 1.5)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (decay * SR / 3))
    ir = lp(ir, 3500)
    y = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    y /= (np.abs(y).max() + 1e-9) / (np.abs(x).max() + 1e-9)
    return x * (1 - mix) + y * mix


class Mix:
    def __init__(self):
        self.b = np.zeros(int(DUR * SR) + SR)

    def add(self, t, x, g=1.0):
        i = int(t * SR)
        if i < 0:
            x = x[-i:]; i = 0
        x = x[:len(self.b) - i]
        self.b[i:i + len(x)] += x * g

    def bed(self, t0, t1, x_fn, g=1.0, fade=0.25):
        d = t1 - t0
        x = x_fn(d)
        n = len(x); f = int(fade * SR)
        w = np.ones(n); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        self.add(t0, x * w, g)


def step(kind='stone'):
    d = 0.16
    if kind == 'stone':
        x = bp(noise(d), 90, 1800) * env(d, 0.002, 0.03) + 0.6 * np.sin(2 * np.pi * 70 * T(d)) * env(d, 0.002, 0.04)
    elif kind == 'grass':
        x = bp(noise(d), 600, 5000) * env(d, 0.01, 0.05) * 0.6
    elif kind == 'water':
        d = 0.5
        x = bp(noise(d), 300, 3500) * env(d, 0.03, 0.14) + 0.5 * bp(noise(d), 100, 600) * env(d, 0.01, 0.1)
    else:
        x = bp(noise(d), 80, 900) * env(d, 0.003, 0.04)
    return x / np.abs(x).max()


def whip():
    d = 0.9
    t = T(d)
    whoosh = bp(noise(d), 500, 5000) * np.exp(-((t - 0.2) / 0.07) ** 2) * 0.35
    crack = hp(noise(d), 1500) * np.where(t > 0.24, np.exp(-(t - 0.24) / 0.018), 0) * (t > 0.24)
    thud = np.sin(2 * np.pi * 140 * t) * np.where(t > 0.24, np.exp(-(t - 0.24) / 0.05), 0) * 0.6
    return reverb(whoosh + crack * 1.3 + thud, 1.6, 0.3)       # crack at +0.24 s


def coin():
    d = 0.5; t = T(d)
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((4100, 1), (6300, 0.7), (8900, 0.5), (11200, 0.3))) * np.exp(-t / 0.08)
    x += 0.3 * hp(noise(d), 5000) * np.exp(-t / 0.006)
    return x / np.abs(x).max()


def bell():
    d = 1.4; t = T(d)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / r) for f, a, r in ((910, 1, 0.5), (1830, 0.6, 0.35), (2740, 0.45, 0.25), (3980, 0.3, 0.15), (5420, 0.2, 0.1)))
    x += 0.4 * hp(noise(d), 3000) * np.exp(-t / 0.004)
    return x / np.abs(x).max()


def squeak(n=3, base=3600):
    out = np.zeros(int(0.12 * n * SR) + SR // 10)
    for i in range(n):
        d = 0.07; t = T(d)
        f = base * (1 + 0.25 * np.sin(np.pi * t / d)) * (1 + 0.1 * rng.standard_normal())
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
        j = int(i * 0.11 * SR); out[j:j + len(x)] += x
    return out


def thud(f=70, r=0.12):
    d = 0.6; t = T(d)
    x = np.sin(2 * np.pi * f * t * (1 + 0.5 * np.exp(-t / 0.03))) * np.exp(-t / r) + 0.4 * bp(noise(d), 100, 1200) * np.exp(-t / 0.04)
    return x / np.abs(x).max()


def dig():
    d = 1.1; t = T(d)
    scrape = bp(noise(d), 700, 4500) * np.exp(-((t - 0.14) / 0.09) ** 2)
    chunk = thud(90, 0.06)[:len(t)] if len(thud(90, 0.06)) >= len(t) else np.pad(thud(90, 0.06), (0, len(t) - len(thud(90, 0.06))))
    toss = bp(noise(d), 400, 2500) * np.exp(-((t - 0.85) / 0.1) ** 2) * 0.5
    return scrape + 0.6 * chunk + toss


def gasp():
    d = 0.9; t = T(d)
    x = bp(noise(d), 500, 3200) * np.exp(-((t - 0.22) / 0.14) ** 2)
    x *= 1 + 0.3 * np.sin(2 * np.pi * 7 * t)
    return x


def wind(d, lo=120, hi=700, rate=0.25):
    t = T(d)
    m = 0.55 + 0.45 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)) * np.sin(2 * np.pi * rate * 0.37 * t + 1)
    return bp(noise(d), lo, hi) * m


def crowd(d):
    t = T(d)
    x = bp(noise(d), 250, 1600)
    m = np.clip(lp(noise(d), 4), -3, 3)
    m = (m - m.min()) / (m.max() - m.min() + 1e-9)
    return x * (0.5 + 0.5 * m)


def birds(d):
    x = np.zeros(int(d * SR))
    k = 0.0
    while k < d - 0.4:
        k += rng.uniform(0.25, 0.9)
        n = rng.integers(2, 5); f0 = rng.uniform(2600, 4800)
        for i in range(n):
            dd = 0.06; t = T(dd)
            f = f0 * (1 + 0.2 * np.sin(np.pi * t / dd * rng.choice([1, 2])))
            c = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dd) ** 2 * rng.uniform(0.3, 1)
            j = int((k + i * 0.085) * SR)
            if j + len(c) < len(x):
                x[j:j + len(c)] += c
    return x * 0.5 + wind(d, 200, 900) * 0.35


def drips(d):
    x = np.zeros(int(d * SR)); k = 0.0
    while k < d - 0.5:
        k += rng.uniform(0.35, 1.1)
        dd = 0.09; t = T(dd); f = rng.uniform(900, 2200)
        c = np.sin(2 * np.pi * f * t * (1 + 2.5 * t)) * np.exp(-t / 0.02)
        j = int(k * SR)
        if j + len(c) < len(x):
            x[j:j + len(c)] += c * rng.uniform(0.3, 1)
    return reverb(x, 2.2, 0.6) + lp(noise(d), 90)[:len(x)] * 3.0


def crickets(d):
    t = T(d)
    c = np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 31 * t) > 0.2) * (np.sin(2 * np.pi * 1.7 * t) > -0.2)
    return c * 0.12 + wind(d, 100, 500, 0.15) * 0.8


def rumble(d):
    t = T(d)
    x = lp(noise(d), 160) * 4 + bp(noise(d), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.2 * t)) * 0.35
    creak = np.sin(2 * np.pi * (620 + 90 * np.sin(2 * np.pi * 0.9 * t)) * t) * np.clip(np.sin(2 * np.pi * 0.9 * t), 0, 1) ** 6 * 0.12
    return x + creak


def build_sfx(path):
    m = Mix()
    # ambience beds, cut with the picture
    beds = [(0, 5.2, lambda d: reverb(wind(d, 80, 300, 0.1), 2.0, 0.5), 0.5), (5.2, 6.7, lambda d: wind(d), 0.5), (6.7, 8.2, drips, 0.5), (8.2, 9.6, crowd, 0.45),
            (9.6, 11.0, lambda d: wind(d) + rumble(d) * 0.6, 0.45), (11.0, 13.1, lambda d: wind(d, 150, 600), 0.35), (13.1, 20.3, lambda d: wind(d) + crowd(d) * 0.12, 0.5),
            (20.3, 23.2, lambda d: wind(d, 150, 600), 0.45), (23.2, 33.7, birds, 0.5), (33.7, 43.9, drips, 0.6), (43.9, 54.6, crowd, 0.5),
            (54.6, 62.0, crickets, 0.55), (62.0, 65.1, birds, 0.35), (65.1, 72.9, lambda d: wind(d, 100, 600, 0.3), 0.6), (72.9, 75.5, lambda d: wind(d, 80, 500, 0.3), 0.6),
            (75.5, 84.4, lambda d: reverb(wind(d, 80, 300, 0.1), 2.0, 0.5), 0.5), (84.4, 86.2, lambda d: wind(d, 150, 600), 0.4), (86.2, 88.3, drips, 0.6), (88.3, DUR, lambda d: wind(d) + crowd(d) * 0.12, 0.5)]
    for a, b, fn, g in beds:
        m.bed(a - 0.05, b + 0.05, fn, g * 0.5)

    def steps(t0, t1, period, kind, g=0.5):
        t = t0
        while t < t1:
            m.add(t, step(kind), g * rng.uniform(0.7, 1)); t += period * rng.uniform(0.94, 1.06)
    # whip (crack lands 0.24 s into the sample)
    for h, g in ((2.12, 1.0), (4.6, 0.45), (81.85, 1.0), (83.15, 1.0)):
        m.add(h - 0.24, whip(), g)
    steps(5.2, 6.7, 0.52, 'stone'); steps(13.1, 18.0, 0.52, 'stone'); m.add(19.95, thud(160, 0.03), 0.3)
    for t in (11.72, 12.02, 12.32, 22.6, 33.45, 40.4, 84.9, 85.3):
        m.add(t, coin(), 0.55)
    steps(6.7, 8.2, 0.55, 'water', 0.6); steps(23.2, 25.6, 0.55, 'grass', 0.5); steps(25.7, 28.2, 0.62, 'water', 0.7); m.add(28.5, step('water'), 0.6); m.add(32.2, thud(300, 0.02), 0.2)
    steps(33.7, 38.6, 0.55, 'water', 0.7); m.add(39.0, step('water'), 0.5); m.add(39.5, step('water'), 0.4); m.add(42.0, reverb(step('water'), 2.5, 0.6), 0.5)
    steps(43.9, 46.2, 0.5, 'stone', 0.4)
    for t in (46.4, 46.9, 47.3):
        m.add(t, squeak(3), 0.3)
    m.add(47.55, squeak(5, 4200), 0.45); m.add(48.9, squeak(2), 0.25); m.add(50.3, squeak(3), 0.3); m.add(50.9, gasp(), 0.9); m.add(53.1, squeak(6, 4600), 0.6); m.add(53.3, gasp(), 0.6)
    for k in range(5):
        t = 54.2 + 1.3 * k
        if 54.6 <= t < 57.0:
            m.add(t, dig(), 0.8)
    for k in range(3):
        m.add(56.75 + 1.3 * k, dig(), 0.9)
    steps(59.6, 62.0, 0.5, 'grass', 0.6)
    m.bed(9.6, 11.0, rumble, 0.35); m.bed(65.1, 70.3, rumble, 0.4); steps(65.1, 70.3, 0.56, 'dirt', 0.4)
    t = 70.45
    while t < 72.85:
        m.add(t, bell(), 0.5); t += 1 / 2.6 * 1.0
    m.add(74.85, thud(60, 0.14), 1.0); m.add(74.9, bp(noise(0.5), 300, 2000) * env(0.5, 0.01, 0.1), 0.4)
    for t in (78.72, 78.8, 78.9):
        m.add(t, reverb(thud(110, 0.05), 1.5, 0.35), 0.7)
    x = m.b[:int(DUR * SR)]
    x = np.tanh(x * 0.9)
    x = x / (np.abs(x).max() + 1e-9) * 0.7
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def main():
    args = sys.argv[1:]
    frames = args[args.index('--frames') + 1] if '--frames' in args else os.path.join(HERE, 'frames')
    out = args[args.index('--out') + 1] if '--out' in args else os.path.join(HERE, 'out/worst_jobs.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    work = os.path.join(os.path.dirname(out), 'work'); os.makedirs(work, exist_ok=True)
    ass = os.path.join(work, 'captions.ass'); sfx = os.path.join(work, 'sfx.wav')
    ch = captions(ass); build_sfx(sfx)
    print(len(ch), 'caption chunks')
    seq = os.path.join(work, 'seq'); shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq)
    have = {}
    for f in glob.glob(os.path.join(frames, '*', '*.jpg')):
        have[int(os.path.basename(f)[:5])] = f
    total = int(round(DUR * FPS)); last = None; missing = 0
    for i in range(total):
        src = have.get(i)
        if src is None:
            missing += 1; src = last
        if src is None:
            src = have[min(have)]
        last = src
        os.symlink(src, os.path.join(seq, f'{i:05d}.jpg'))
    print('frames', len(have), 'missing', missing)
    vo = os.path.join(HERE, 'audio/worst_jobs.mp3')
    # voice loud and forward; SFX bed sits ~20 dB under it
    fc = (f"[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.6:5:5:0.0,ass='{ass}',format=yuv420p[v];"
          "[1:a]loudnorm=I=-13:TP=-1.0:LRA=9,aresample=48000[vo];[2:a]volume=-17dB,aresample=48000[fx];[vo][fx]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.97[a]")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(seq, '%05d.jpg'), '-i', vo, '-i', sfx, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
           '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-t', str(DUR), '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
