"""Phrase-level timings for a voiceover, so captions and actions land on the words.

  python3 voice_timing.py voice.mp3 [--lang en] [--no-text]

Splits the audio at pauses (ffmpeg silencedetect) and transcribes each piece with Whisper, printing
    start   end   text
`--no-text` prints only the start/end of each spoken phrase (enough when you already have the script).
Whisper runs through sherpa-onnx; the model (about 1.9 GB) is fetched once from GitHub releases into ~/.cache.
Hugging Face is often blocked in sandboxes, GitHub releases usually is not.
"""
import sys, os, re, subprocess, tempfile
src = sys.argv[1]; lang = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'en'
wav = tempfile.mktemp(suffix='.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', wav], check=True)
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', wav, '-af', 'silencedetect=noise=-32dB:d=0.1', '-f', 'null', '-'], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', log)]; ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', log)]
import soundfile as sf
a, sr = sf.read(wav, dtype='float32'); dur = len(a) / sr
segs, t = [], 0.0
for s, e in zip(starts, ends + [dur] * (len(starts) - len(ends))):
    if s - t > 0.15: segs.append((t, s))
    t = e
if dur - t > 0.15: segs.append((t, dur))
if '--no-text' in sys.argv:
    for s, e in segs: print(f'{s:7.2f} {e:7.2f}')
    sys.exit()
import sherpa_onnx
d = os.path.expanduser('~/.cache/sherpa-onnx-whisper-medium')
if not os.path.exists(d + '/medium-encoder.int8.onnx'):
    os.makedirs(os.path.dirname(d), exist_ok=True)
    subprocess.run(f'cd {os.path.dirname(d)} && curl -sL https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-medium.tar.bz2 | tar xj', shell=True, check=True)
r = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d + '/medium-encoder.int8.onnx', decoder=d + '/medium-decoder.int8.onnx', tokens=d + '/medium-tokens.txt', language=lang, task='transcribe', num_threads=3)
for s, e in segs:
    st = r.create_stream(); st.accept_waveform(sr, a[int(max(0, s - .05) * sr):int((e + .05) * sr)]); r.decode_stream(st)
    print(f'{s:7.2f} {e:7.2f} {st.result.text.strip()}', flush=True)
