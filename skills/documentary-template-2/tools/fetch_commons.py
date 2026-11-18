#!/usr/bin/env python3
"""Download candidate photos from Wikimedia Commons (1280 px versions) with licence + author recorded in meta.json.

    python3 tools/fetch_commons.py photos/wm --search "Union Carbide Bhopal plant" "Bhopal memorial statue" --cat "Bhopal disaster"

Hosts needed (allow them in the environment's network settings if blocked): commons.wikimedia.org, thumb.wikimedia.org
(optional: en.wikipedia.org + upload.wikimedia.org for a portrait that only exists on Wikipedia - those are usually non-free).
Be polite: one run at a time, honest User-Agent, never spoof a browser. On HTTP 429 the script waits and retries.
ALWAYS look at what was downloaded (tools/sheet.py) before using it: search results include unrelated files and
people who merely share a name."""
import json, os, sys, time, re, urllib.request, urllib.parse, argparse
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--search', nargs='*', default=[]); ap.add_argument('--cat', nargs='*', default=[]); ap.add_argument('--width', type=int, default=1280); ap.add_argument('--per', type=int, default=5)
A = ap.parse_args(); UA = "voxkit-video-tool/1.0 (educational history video)"; API = "https://commons.wikimedia.org/w/api.php?"; os.makedirs(A.out, exist_ok=True)
def get(url, tries=5):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90).read()
        except Exception as e: print('  retry', getattr(e, 'code', e), flush=True); time.sleep(20 * (i + 1) if getattr(e, 'code', 0) == 429 else 5)
    return None
mp = os.path.join(A.out, 'meta.json'); meta = json.load(open(mp)) if os.path.exists(mp) else {}
def pages(params):
    raw = get(API + urllib.parse.urlencode(dict(action='query', format='json', prop='imageinfo', iiprop='mime|size|url|extmetadata', iiurlwidth=A.width, iiextmetadatafilter='LicenseShortName|Artist|ImageDescription', **params))); time.sleep(3)
    return sorted(json.loads(raw).get('query', {}).get('pages', {}).values(), key=lambda p: p.get('index', 0)) if raw else []
todo = []
for c in A.cat: todo += pages(dict(generator='categorymembers', gcmtitle='Category:' + c, gcmtype='file', gcmlimit=60))
for q in A.search: todo += pages(dict(generator='search', gsrnamespace=6, gsrsearch=q, gsrlimit=A.per))
seen = set(v[0] for v in meta.values()); print('candidates', len(todo), flush=True)
for p in todo:
    if 'imageinfo' not in p or p['title'] in seen: continue
    seen.add(p['title']); ii = p['imageinfo'][0]
    if ii.get('mime') not in ('image/jpeg', 'image/png') or ii.get('size', 0) < 30e3 or 'thumburl' not in ii: continue
    data = get(ii['thumburl'], 3); time.sleep(1.5)
    if not data or data[:1] == b'<': continue
    key = re.sub(r'[^a-z0-9]+', '_', p['title'][5:].rsplit('.', 1)[0].lower()).strip('_')[:60]; ext = 'png' if data[:4] == b'\x89PNG' else 'jpg'; n = 1
    while os.path.exists(os.path.join(A.out, f'{key}.{ext}')): n += 1; key = key[:57] + f'_{n}'
    open(os.path.join(A.out, f'{key}.{ext}'), 'wb').write(data); em = ii.get('extmetadata', {}); cl = lambda k: re.sub('<[^>]+>', '', em.get(k, {}).get('value', ''))[:160]
    meta[f'{key}.{ext}'] = [p['title'], cl('LicenseShortName'), cl('Artist'), cl('ImageDescription')]; json.dump(meta, open(mp, 'w'), indent=1); print(key, len(data), '|', cl('LicenseShortName'), flush=True)
print('DONE')
