"""Dark America - 3D pop-up diorama sample (first line: "In 1906, America put a human being in a zoo.").
Usage: python3 sample3d.py stills <dir> t1,t2 | render <out.mp4>"""
import sys, os, math, json, subprocess, wave as wavmod
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..'))
import numpy as np, cv2
from multiprocessing import Pool
from voxkit.core import *
from voxkit import art, art3d, film
from voxkit.pop3d import Cam3, Card, World, dust

VOICE = os.path.join(HERE, 'voice', 'full.mp3'); T = film.timeline(json.load(open(os.path.join(HERE, 'voice', 'words.json'))))
DUR = 5.0; T_ZOO = T('zoo'); T_HUMAN = T('human')
PH = os.path.join(HERE, 'photos')

# ------------------------------------------------------------------ paper pieces
OTA = art.photo_cutout(os.path.join(PH, 'wm', 'otabenga_0.jpg'), (150, 90, 740, 1100), out_h=1000, fg_hint=[(450, 400, 170), (520, 1000, 200)], bg_hint=[(40, 950, 110), (60, 700, 60), (80, 80, 60), (820, 80, 60), (850, 500, 40), (745, 470, 55), (760, 620, 45), (730, 340, 40)])
PEOPLE = [art3d.person(i) for i in range(12)]
TREES = [art3d.tree(i) for i in range(4)]; CLOUDS = [art3d.cloud(i) for i in range(4)]
HOUSE = art3d.facade(1600, 900); SIGN = art3d.sign('MONKEY HOUSE', 900); BARS = art3d.bars(1000, 700); BACK = art3d.wall(1000, 700); SIDE = art3d.bars(500, 700, 5, 3)
ROOF = art3d.wall(1000, 120, (.16, .14, .13), 4)
FLAG = art.flag_us(900, 480); POLE = art3d.pole()
Y06 = art.label('1906', 220, seed=4); HUMAN = art.label('A HUMAN BEING', 150, seed=13, col=np.array([.95, .93, .86], np.float32)); ZOO = art.label('IN A ZOO', 170, seed=8)
RAYS = art.rays(1800, 14, np.array([.98, .90, .70], np.float32), 0.35)
GROUND = art3d.ground_tex(); SKY = art3d.sky()
WORLD = World(GROUND, SKY, fog=(.88, .78, .60), fog_d=75, focus=8.0, dof=13)
rng = np.random.default_rng(4)
_pos = [(-1.6, -7.5), (1.9, -7.0), (-3.2, -5.8), (2.9, -5.5), (-1.5, -4.2), (1.6, -3.8), (-3.9, -3.0), (3.7, -2.6), (-2.3, -1.6), (2.4, -1.2), (-1.5, -0.2), (1.6, 0.3),
        (-3.3, 0.9), (3.2, 1.2), (-2.0, 2.0), (2.1, 2.3), (-4.4, 2.6), (4.3, 2.8), (-3.0, 3.4), (3.1, 3.6), (-1.9, 4.1), (2.0, 4.3), (-4.0, 4.6), (4.1, 4.9), (-2.7, 5.4), (2.8, 5.6),
        (-1.75, 5.9), (1.8, 6.1), (-3.6, 6.3), (3.7, 6.4), (-5.2, 5.2), (5.3, 5.6), (-5.6, 3.3), (5.6, 3.7)]
CROWD = [(x, z, int(rng.integers(12)), float(rng.uniform(1.62, 1.86)), float(rng.uniform(0, 6))) for x, z in _pos]


def popup(t, t0, d=0.5):
    """Pop-up-book hinge: lying flat (pi/2) -> upright (0) with a little overshoot."""
    return (1 - back(seg(t, t0, t0 + d), 1.4)) * math.pi / 2


def cam_at(t):
    k = eio(seg(t, 0.0, 4.4), 2)
    sh = math.exp(-max(0, t - T_ZOO) * 9) * (t >= T_ZOO) * 0.05
    return Cam3(lerp(0.9, 0.0, k) + sh * math.sin(t * 70), lerp(2.2, 1.75, k) + sh * math.cos(t * 83), lerp(-10.0, 1.3, k), yaw=lerp(-0.07, 0.0, k), pitch=lerp(-0.03, 0.115, k), f=1150)


def cards_at(t):
    C = []
    C.append(Card(RAYS, 0, 120, 190, y=-20, shadow=0, fog=False, blur=3))
    for i, (x, y, z, w) in enumerate(((-34, 22, 110, 30), (30, 30, 100, 26), (-8, 38, 120, 34), (48, 16, 115, 24))):
        C.append(Card(CLOUDS[i], x + t * 0.5, z, w, y=y, shadow=0, blur=1.5))
    C.append(Card(HOUSE, 0, 11.5, 20, tilt=popup(t, 0.05, .55)))
    for i, (x, z, w) in enumerate(((-8.5, 9.5, 6.0), (8.3, 9.0, 6.5), (-6.2, 5.0, 4.6), (6.4, 4.4, 5.0), (-11, 14, 8), (11.5, 15, 8))):
        C.append(Card(TREES[i % 4], x, z, w, tilt=popup(t, 0.12 + i * .05), sway=0.05, ph=i))
    C.append(Card(POLE, -5.0, 7.2, 0.28, tilt=popup(t, 0.3)))
    if t > 0.75: C.append(Card(FLAG, -3.55, 7.2, 2.9, y=4.9, wv=14, shadow=0, alpha=seg(t, .75, .95), ph=1))
    # the cage
    kc = popup(t, 0.25, .5)
    C.append(Card(BACK, 0, 10.0, 5.6, tilt=kc)); C.append(Card(SIDE, -2.8, 8.75, 2.5, yaw=math.pi / 2, tilt=0, alpha=seg(t, .55, .75))); C.append(Card(SIDE, 2.8, 8.75, 2.5, yaw=math.pi / 2, alpha=seg(t, .55, .75)))
    C.append(Card(OTA, 0, 8.9, 2.5, tilt=popup(t, 0.45, .5)))
    kb = seg(t, T_ZOO - 0.14, T_ZOO)                                           # bars slam down on "zoo"
    if kb > 0: C.append(Card(BARS, 0, 7.5, 5.6, y=lerp(9.0, 0.0, kb * kb), shadow=.5))
    C.append(Card(ROOF, 0, 7.5, 5.9, y=3.92, shadow=0, alpha=seg(t, .6, .8)))
    C.append(Card(SIGN, 0, 7.45, 3.6, y=4.45, shadow=0, tilt=-popup(t, 0.7, .4) * .9))
    # labels standing in the scene
    k1 = back(seg(t, T('nineteen') - .05, T('nineteen') + .25), 1.8)
    if k1 > 0: C.append(Card(Y06, -0.1, 7.3, 2.5 * k1, y=6.05 + 2 * (1 - k1), shadow=0, fog=False, blur=0))
    k2 = back(seg(t, T_HUMAN, T_HUMAN + .22), 1.8)
    if k2 > 0: C.append(Card(HUMAN, 0.75, 7.3, 4.0 * k2, y=5.2, shadow=0, fog=False, blur=0))
    k3 = seg(t, T_ZOO - .1, T_ZOO)
    if k3 > 0: C.append(Card(ZOO, 0, 7.2, 3.6 * lerp(2.4, 1, k3 * k3), y=0.12, shadow=0, fog=False, blur=0, alpha=min(1, k3 * 2)))
    # the crowd (seen from behind) - pops up row by row, then shuffles
    for i, (x, z, pi, hgt, ph) in enumerate(CROWD):
        w = hgt * PEOPLE[pi].shape[1] / PEOPLE[pi].shape[0]
        C.append(Card(PEOPLE[pi], x + 0.03 * math.sin(t * 1.7 + ph), z, w, y=0.02 * abs(math.sin(t * 2.2 + ph)), tilt=popup(t, 0.15 + (7.5 + z) * 0.045, .4), ph=ph))
    return C


def extra(img, cam, t):
    dust(img, cam, (0, 0.2, 7.4), t, T_ZOO, n=46, seed=3, speed=3.2)


def render(f):
    t = f / FPS; cam = cam_at(t)
    img = WORLD.render(cam, cards_at(t), f, t, extra)
    expo = 1.08 * smooth(seg(t, 0, .25)) * (1 - .95 * ein(seg(t, DUR - .3, DUR), 2)) * (1 + .3 * math.exp(-max(0, t - T_ZOO) * 25) * (t >= T_ZOO))
    return (post(img, f, tilt=0.6, expo=expo) * 255 + .5).astype(np.uint8)


def soundtrack(path):
    SR = film.SR; n = int(DUR * SR); Lc = np.zeros(n + SR); Rc = np.zeros(n + SR)
    def add(x, t_, g=1.0, pan=0.0):
        i = max(0, int(t_ * SR)); x = x[:len(Lc) - i]; Lc[i:i + len(x)] += x * g * (1 - max(0, pan)); Rc[i:i + len(x)] += x * g * (1 + min(0, pan))
    tt = np.arange(len(Lc)) / SR
    add((np.sin(2 * np.pi * 43.6 * tt) + .5 * np.sin(2 * np.pi * 65.4 * tt + 1)) * (.6 + .4 * np.sin(2 * np.pi * tt / 8 - 1.2)), 0, 0.05)
    for i in range(14): add(film.nburst(0.09, 900, 5000, 0.02), 0.08 + i * 0.07, 0.035, (-1) ** i * .5)        # pop-up paper flutter
    add(film.whoosh(1.2, 200, 1800, .5), 0.0, 0.07); add(film.thump(170, 95, .12, .03), T('nineteen'), 0.06); add(film.thump(170, 95, .12, .03), T_HUMAN, 0.06)
    add(film.riser(.9), T_ZOO - .9, 0.11); add(film.thump(60, 30, 1.0, .3), T_ZOO, 0.3)
    m = int(.5 * SR); t2 = np.arange(m) / SR; add(np.sin(2 * np.pi * 410 * t2) * np.exp(-t2 / .12) * .5 + np.sin(2 * np.pi * 1210 * t2) * np.exp(-t2 / .07) * .3, T_ZOO, 0.10)
    crowd = film._filt(np.random.default_rng(2).normal(0, 1, n), 250, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * np.arange(n) / SR)); add(crowd, 0, 0.012)
    mix = np.stack([Lc, Rc], 1)[:n]; mix[-int(.2 * SR):] *= np.linspace(1, 0, int(.2 * SR))[:, None]
    w = wavmod.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.tanh(mix * 1.1) * .9 * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[3].split(','):
            cv2.imwrite(f'{sys.argv[2]}/f_{float(ts):05.2f}.jpg', cv2.resize(render(round(float(ts) * FPS)), (540, 960), interpolation=cv2.INTER_AREA)[..., ::-1])
    else:
        out = sys.argv[2]; sfx = out + '.sfx.wav'; soundtrack(sfx)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-t', '4.42', '-i', VOICE, '-i', sfx,
                               '-filter_complex', '[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5,afade=t=out:st=4.3:d=0.12,pan=stereo|c0=c0|c1=c0,apad[v];[v][2:a]amix=inputs=2:duration=shortest:normalize=0,alimiter=limit=0.95[a]',
                               '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with Pool(4) as p:
            for im in p.imap(render, range(round(DUR * FPS)), chunksize=4): ff.stdin.write(im.tobytes())
        ff.stdin.close(); ff.wait(); os.remove(sfx); print('done', out)
