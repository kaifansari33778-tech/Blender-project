#!/usr/bin/env python3
"""Forced alignment: voice-over + the exact script -> words.json = [[word, start_sec, end_sec], ...]

    python3 tools/align.py voice/full.mp3 voice/script.txt voice/words.json

Works for English and for Hindi written in Latin letters (Hinglish): every word that is not in the English pronunciation
dictionary gets a rule-based pronunciation. Write numbers in the script as they are SPOKEN ("nineteen eighty four",
"unnees sau chauraasi") - digits cannot be aligned. Always check the result against the pauses (see the printed table):
sentence starts should land right after a silence. Needs: pip install pocketsphinx ; ffmpeg."""
import sys, json, wave, re, subprocess, tempfile, os
from pocketsphinx import Decoder
src, script, out = sys.argv[1:4]
wav = os.path.join(tempfile.mkdtemp(), 'a.wav'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', wav], check=True)
words = re.findall(r"[a-z']+", open(script).read().lower()); w = wave.open(wav); pcm = w.readframes(w.getnframes())
d = Decoder(samprate=16000, bestpath=False, beam=1e-80, wbeam=1e-60, pbeam=1e-80)
DI = [('aa', 'AA'), ('ee', 'IY'), ('oo', 'UW'), ('ai', 'EH'), ('au', 'AO'), ('ch', 'CH'), ('sh', 'SH'), ('th', 'T'), ('dh', 'D'), ('kh', 'K'), ('gh', 'G'), ('bh', 'B'), ('ph', 'F'), ('jh', 'JH'), ('ng', 'NG')]
MO = dict(a='AH', e='EY', i='IH', o='OW', u='UH', b='B', c='K', d='D', f='F', g='G', h='HH', j='JH', k='K', l='L', m='M', n='N', p='P', q='K', r='R', s='S', t='T', v='V', w='V', x='K S', y='Y', z='Z')
def g2p(s):
    s = s.replace("'", ''); o = []; i = 0
    while i < len(s):
        for a, b in DI:
            if s.startswith(a, i): o.append(b); i += 2; break
        else:
            c = s[i]; p = MO.get(c, 'AH')
            if i == len(s) - 1 and c == 'a': p = 'AA'
            if i == len(s) - 1 and c == 'i': p = 'IY'
            o.append(p); i += 1
    return ' '.join(o) or 'AH'
# optional overrides: a file next to the script named pronounce.txt with lines "word PH PH PH" (ARPAbet), for names the rules get wrong
ov = {}
pf = os.path.join(os.path.dirname(os.path.abspath(script)), 'pronounce.txt')
if os.path.exists(pf):
    for ln in open(pf):
        p = ln.split()
        if len(p) > 1: ov[p[0].lower()] = ' '.join(p[1:])
alias = {}
for wd in sorted(set(words)):
    if wd in ov: a = wd + 'qx'; d.add_word(a, ov[wd], True); alias[wd] = a
    elif not d.lookup_word(wd): d.add_word(wd, g2p(wd), True)
d.set_align_text(' '.join(alias.get(x, x) for x in words)); d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
res = [[re.sub('qx$', '', s.word.split('(')[0]), round(s.start_frame / 100, 2), round(s.end_frame / 100, 2)] for s in d.seg() if not s.word.startswith('<') and not s.word.startswith('[')]
json.dump(res, open(out, 'w')); print(len(words), 'words in script,', len(res), 'aligned')
for i in range(0, len(res), 12): print(' '.join(f"{a}@{b}" for a, b, c in res[i:i + 12]))
sil = subprocess.run(['ffmpeg', '-v', 'info', '-i', src, '-af', 'silencedetect=noise=-32dB:d=0.22', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('pauses (start-end):', ' '.join(f"{a}-{b}" for a, b in zip(re.findall(r'silence_start: ([0-9.]+)', sil), re.findall(r'silence_end: ([0-9.]+)', sil))))
