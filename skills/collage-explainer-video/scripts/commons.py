"""Find, download and cut out free-licence photos from Wikimedia Commons.

  python3 commons.py search <workdir> "gas stove burner flame" "aluminium pot" ...
        -> <workdir>/cand/<query>.jpg (numbered contact sheet) + <query>.json (titles, sizes, licences)
  python3 commons.py fetch <workdir> pot=aluminium_pot:2:cut factory=aluminium_smelter:6:raw ...
        key=<query slug>:<index on the sheet>:<cut|raw>   cut -> background removed, saved to <workdir>/cut/key.png
                                                          raw -> full photo, saved to <workdir>/raw/key.jpg
  python3 commons.py sheet <workdir>      -> <workdir>/cut/_sheet.jpg : every cutout on magenta, to check the edges
  python3 commons.py credits <workdir>    -> prints a Markdown credits table for everything fetched

Run ONE search or fetch at a time: Commons rate-limits hard (HTTP 429) and parallel runs make it worse.
"""
import sys, os, json, re, subprocess, time, tempfile, urllib.parse
from PIL import Image, ImageDraw

UA = 'MediaResearchBot/1.0 (python-requests)'          # generic client name; a browser-like UA gets throttled harder
STEPS = (500, 960, 1280, 1920, 3840)                    # Commons only serves thumbnails at fixed widths; others return 400
def curl(url, tries=7):
    fd, tmp = tempfile.mkstemp(); os.close(fd)           # unique temp file: a shared one corrupts results if two runs overlap
    try:
        for a in range(tries):
            r = subprocess.run(['curl', '-s', '-L', '-m', '120', '-A', UA, '-w', '%{http_code}', '-o', tmp, url], capture_output=True, text=True)
            if r.stdout.strip() == '200': return open(tmp, 'rb').read()
            time.sleep(4 * (a + 1))
        return None
    finally:
        os.remove(tmp)
def api(**p):
    b = curl('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(action='query', format='json', **p)))
    return json.loads(b) if b else None
def slug(q): return re.sub(r'[^a-z0-9]+', '_', q.lower()).strip('_')[:50]

def search(work, queries, n=12):
    import io
    out = f'{work}/cand'; os.makedirs(out, exist_ok=True)
    for q in queries:
        time.sleep(2)
        d = api(generator='search', gsrnamespace=6, gsrsearch=q + ' filetype:bitmap', gsrlimit=n, prop='imageinfo', iiprop='url|size|extmetadata', iiurlwidth=320)
        pages = sorted((d or {}).get('query', {}).get('pages', {}).values(), key=lambda x: x.get('index', 0))
        tiles, meta = [], []
        for i, p in enumerate(pages):
            ii = p['imageinfo'][0]; b = curl(ii['thumburl'], 3)
            if not b: continue
            try: im = Image.open(io.BytesIO(b)).convert('RGB')
            except Exception: continue
            im.thumbnail((240, 240)); c = Image.new('RGB', (240, 260)); c.paste(im, (0, 20))
            ImageDraw.Draw(c).text((2, 2), f"{i}  {ii['width']}x{ii['height']}", fill='yellow'); tiles.append(c)
            em = ii.get('extmetadata', {})
            meta.append(dict(i=i, title=p['title'], url=ii['url'], w=ii['width'], h=ii['height'], lic=em.get('LicenseShortName', {}).get('value'),
                             artist=re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()[:200]))
        if not tiles: print(q, '-> nothing'); continue
        sh = Image.new('RGB', (1440, 30 + 260 * ((len(tiles) + 5) // 6)), (40, 0, 60)); ImageDraw.Draw(sh).text((6, 8), q, fill='white')
        for k, t in enumerate(tiles): sh.paste(t, ((k % 6) * 240, 30 + (k // 6) * 260))
        sh.save(f'{out}/{slug(q)}.jpg', quality=80); json.dump(meta, open(f'{out}/{slug(q)}.json', 'w'), indent=1)
        print(q, '->', len(tiles), f'{out}/{slug(q)}.jpg', flush=True)

def tight(o, thr=60):
    import numpy as np
    a = np.asarray(o)[..., 3]; ys, xs = np.where(a > thr)
    return o.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)) if len(xs) else o
def fetch(work, specs):
    os.makedirs(f'{work}/raw', exist_ok=True); os.makedirs(f'{work}/cut', exist_ok=True)
    credp = f'{work}/credits.json'; cred = json.load(open(credp)) if os.path.exists(credp) else {}
    todo = []
    for spec in specs:
        key, rest = spec.split('='); q, idx, mode = rest.split(':')[:3]
        m = [x for x in json.load(open(f'{work}/cand/{q}.json')) if x['i'] == int(idx)][0]
        out = f'{work}/raw/{key}.jpg'
        if not os.path.exists(out):
            width = max([w for w in STEPS if w <= min(1920, m['w'])] or [0])
            url = m['url']
            if width:
                d = api(titles=m['title'], prop='imageinfo', iiprop='url', iiurlwidth=width)
                if d: url = list(d['query']['pages'].values())[0]['imageinfo'][0].get('thumburl', url)
            b = curl(url)
            if not b: print(key, 'FAILED (rerun later)', flush=True); continue
            tmp = out + '.part'; open(tmp, 'wb').write(b); Image.open(tmp).convert('RGB').save(out, quality=94); os.remove(tmp)
            print(key, 'ok', m['title'], flush=True); time.sleep(1.5)
        cred[key] = dict(title=m['title'], license=m['lic'], artist=m['artist'], mode=mode); json.dump(cred, open(credp, 'w'), indent=1)
        if mode == 'cut' and not os.path.exists(f'{work}/cut/{key}.png'): todo.append(key)
    if todo:
        from rembg import remove, new_session          # model downloads once from GitHub releases
        ses = new_session('isnet-general-use')
        for k in todo:
            o = tight(remove(Image.open(f'{work}/raw/{k}.jpg').convert('RGB'), session=ses)); o.save(f'{work}/cut/{k}.png'); print('cut', k, o.size, flush=True)

def sheet(work):
    fs = sorted(f for f in os.listdir(f'{work}/cut') if f.endswith('.png')); tiles = []
    for f in fs:
        o = Image.open(f'{work}/cut/{f}').convert('RGBA'); t = Image.new('RGB', o.size, (200, 60, 160)); t.paste(o, (0, 0), o); t.thumbnail((300, 300))
        c = Image.new('RGB', (300, 320)); c.paste(t, (0, 20)); ImageDraw.Draw(c).text((4, 2), f'{f[:-4]} {o.size}', fill='yellow'); tiles.append(c)
    sh = Image.new('RGB', (1800, 320 * ((len(tiles) + 5) // 6)))
    for i, t in enumerate(tiles): sh.paste(t, ((i % 6) * 300, (i // 6) * 320))
    sh.save(f'{work}/cut/_sheet.jpg', quality=85); print(f'{work}/cut/_sheet.jpg')
def credits(work):
    c = json.load(open(f'{work}/credits.json'))
    print('| Used as | File | Author | License |\n|---|---|---|---|')
    for k, v in c.items():
        print(f"| {k} | [{v['title'][5:]}](https://commons.wikimedia.org/wiki/{v['title'].replace(' ', '_')}) | {(v['artist'] or 'see file page').replace('|', '/')} | {v['license']} |")

if __name__ == '__main__':
    cmd, work, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    dict(search=lambda: search(work, rest), fetch=lambda: fetch(work, rest), sheet=lambda: sheet(work), credits=lambda: credits(work))[cmd]()
