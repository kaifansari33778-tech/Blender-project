---
name: collage-explainer-video
description: Make vertical (9:16) "2.5D cutout collage" explainer videos for Reels, Shorts and TikTok - photoreal cutout images floating over colour-coded textured backgrounds, constant camera drift, perspective tilt, colour-graded cutouts, two-line glowing captions, object-driven transitions, synced to a voiceover, with sound effects. Use this skill whenever the user wants a short explainer, myth-busting, health or science video in this collage or motion-graphics style, asks to recreate or match a reference reel, gives a voiceover or script and wants a video made from it, or asks for "the same style as before", "more 3D", "better cutouts" or "colour grading" on such a video. Also use it to analyse a reference video frame by frame, to write the script and shot list, or to find and cut out images for one. It bundles a tested Python compositor, an image search and cutout tool, voice timing, and a sound-effects generator, so start here instead of writing a renderer from scratch.
---

# Collage explainer video

This skill produces a finished MP4: 1080x1920, 30 fps, voiceover plus sound effects, in the style of
fast educational reels built from cut-out photos. It was developed by recreating a real reference reel
and then producing a complete 113-second film; the full analysis of that reel is in
`references/reference-video-breakdown.md` and the full film code is in `references/example_film/`.

The renderer is a plain Python layer compositor (numpy + OpenCV + Pillow). It is not Blender and does not
need a GPU. Flat cutouts get their depth from perspective tilt, parallax, shadows and grading, which is
exactly how the reference style is made, and a frame renders in about half a second.

## What "the style" is

Read `references/style-guide.md` before designing scenes. The short version:

- Every object is a photoreal cutout on transparency. Backgrounds are flat textured colour walls or
  graded photos, and the background colour tells the viewer which chapter they are in.
- Nothing is ever still. The camera drifts, objects pop in with overshoot, tilt in perspective and keep
  swaying. A scene lasts 2 to 4 seconds.
- Each cutout is graded to its scene: ambient tint, darker towards the bottom, a rim light in the
  background's colour, and a soft offset shadow.
- Captions sit top-left in two lines: small white line, then a large gradient punch line on the key word.
  They summarise, they do not transcribe.
- Transitions are motivated by motion: whip pans, a zoom through an object, a match on a moving element.
- One paper-texture overlay (crease, punch holes, vignette, grain) sits on everything.

## Workflow

Work in a scratch directory (`WORK`) with `cut/`, `raw/`, `cand/` and a frames folder. Keep the film
script itself in the user's project.

### 1. Understand the brief
If there is a reference video, look at it before anything else:
`scripts/sheets.sh video ref.mp4 WORK/ref 2` gives timestamped contact sheets, and
`scripts/sheets.sh strip ref.mp4 out.jpg <sec>` gives 10 frames across one second, which is how you see what
a transition actually does. Transcribe its narration with `scripts/voice_timing.py` (`--lang hi` etc.).
Write down scene by scene: caption, picture, motion, transition.

If the user only has a topic, write the script first (about 150 words per minute), in short spoken
sentences, and get the voiceover from the user. You cannot generate the voice; ask for the audio file.

### 2. Time the voiceover
`python3 scripts/voice_timing.py voice.mp3` prints every spoken phrase with start and end times.
Everything downstream is keyed to these numbers: a scene starts in the pause before its sentence, the
second caption line appears on the punch word, and impacts (stamps, slams) land on the stressed word.
Never guess timings from the script text.

### 3. Plan the scenes
Make a table: start time, caption (two lines), background/colour, objects, motion, transition out.
Rules that made the difference:
- One idea per scene, shown with objects doing something (a stamp slams, a tag flips, beads fall away),
  not with text on screen.
- Assign each chapter a background colour and reuse it when the topic returns.
- Plan a transition for every scene change, and vary them.
- Include people where a process is described, but prefer back views, hands, masked or cropped figures.
  Do not put an identifiable private person's face in a health or opinion video.
- Adapt objects to the audience the user names (for example a generic pot instead of a regional one).

### 4. Source the images
`scripts/commons.py` searches Wikimedia Commons, downloads at a legal thumbnail size, removes backgrounds
and records licences. Read `references/sourcing-images.md` first; it lists which queries work, which
hosts are usually reachable from a sandbox, and the rate-limit traps.

```
python3 scripts/commons.py search WORK "aluminium frying pan" "kidney anatomical model" ...
# look at WORK/cand/<query>.jpg, pick by the yellow index number
python3 scripts/commons.py fetch WORK pan=aluminium_frying_pan:9:cut kidney=kidney_anatomical_model:0:cut factory=foundry:0:raw
python3 scripts/commons.py sheet WORK      # then LOOK at WORK/cut/_sheet.jpg
```
Always look at the cutout sheet. Background removal fails quietly: plates vanish from under food, hands
vanish from forks, a huge machine stays attached to the person you wanted. Fix by cropping the raw photo
before cutting, drawing the missing part, or using the photo as a framed card (`engine.framed`).
If no usable photo exists, draw the object with Pillow in the same flat-shaded look; documents, phones,
cards, tags, tiles and stamps are always drawn (the engine has them).

If the user can supply or generate images, that beats search. Ask once, early, and carry on with search
meanwhile.

### 5. Build the film
Copy `scripts/demo_film.py` and grow it. `scripts/engine.py` provides everything; its docstrings are the
API. The pieces you will use constantly:

- `cut(key, width, amb=, s=, rim=, ...)` loads a cutout, grades it and builds its shadow.
  `photo(key, tint=, s=, vig=, blur_r=)` loads a background photo, cover-cropped and graded.
  `flat_bg(rgb)` makes a textured colour wall.
- `obj(c, o, x, y, s, rot, rx=, ry=, depth=, lift=)` draws a cutout with its shadow. `rx`/`ry` are the
  perspective tilt. `depth` scales the camera sway (far 0.5, normal 1, near 2). `lift` separates the shadow.
- `pop(t, t0)` is the overshoot entrance curve. `slam`, `draw_on`, `reveal`, `steam`, `lens`, `Grp` cover
  impacts, drawn strokes, puffs, a real magnifier, and zooming a group of layers about a point.
- `Film(dur, scenes, trans, captions)` runs scene dispatch, transitions, captions, motion blur, the
  finishing overlay and a resumable render loop.

`references/scene-recipes.md` has copy-ready patterns for the recurring shots (document with highlighter,
bead grid, zoom chain, shelf with flipping tags, phone in hand with replaced screen, stamp, pile-up).

Build art once at import time, never inside a scene function. Scene functions take absolute film time.

### 6. Preview before every full render
A full render is minutes; a preview is seconds, so iterate on previews:
```
python3 my_film.py WORK WORK/pv 0 3400 36      # one frame every 1.2 s
scripts/sheets.sh frames WORK/pv WORK/pv.jpg   # then LOOK at it
```
Check each scene for: object too small, object hidden under the caption block (top 330 px, left 950 px),
layers overlapping by accident, empty frame for more than half a second, cutout not sitting on anything.
Fix and re-preview only the affected frame ranges. The first preview always shows several of these.

### 7. Render, add sound, encode
```
for r in "0 850" "850 1700" "1700 2550" "2550 3400"; do python3 my_film.py WORK WORK/frames $r & done; wait
python3 scripts/sfx.py events.json WORK/sfx.wav
scripts/encode.sh WORK/frames voice.mp3 113.3 out/film.mp4 WORK/sfx.wav
```
Rendering is resumable, so a crashed worker only costs its missing frames. Count the frames before
encoding. Put a whoosh on every transition, a thud on every impact, a pop on entrances, and keep the
effects at about 0.4 gain so they never cover a word.

Then make contact sheets of the finished MP4 and look at them once more.

### 8. Hand over honestly
Send the MP4 and say plainly:
- what you could not check (you cannot hear the mix or watch motion at speed; you checked stills),
- which shots are weak and why,
- that drawn documents are illustrations of what the narration says, not the real documents,
- whether factual claims in the script were verified,
- that the photos need attribution, with the credits table from `commons.py credits`.

## Start small when the look is new
For a new topic or a new user, deliver the first 10 seconds, then 20, then the whole film. Feedback on a
10-second sample ("more 3D", "match the grading") is cheap to apply; the same feedback on a finished
two-minute film costs a full rebuild.

## Things that went wrong, so they do not go wrong again
- Averaging only two sub-frames gives double images, not motion blur. Use three (`Film` does).
- Warping every layer onto a full-size canvas made rendering ten times slower. `place` warps into the
  layer's bounding box only; keep it that way.
- Two image downloads running at once silently swapped files. Run one `commons.py` at a time.
- Workers started together must not write the same derived file at import. Create derived assets before
  launching parallel renders, or guard with an existence check.
- Strong `rx`/`ry` (over about 30 degrees) on a photo cutout stretches it into a bell shape. Tumble
  objects mostly with in-plane rotation and keep tilt under 25 degrees.
- A zoom that scales a document also scales it under the caption. Aim the zoom target lower on screen.
- Film grain makes H.264 files huge at low crf. `encode.sh` uses crf 24 with a bitrate cap.
- Background processes die at the tool timeout. Long renders must be resumable and launched in the background.

## Files
- `scripts/engine.py` compositor and all drawing helpers
- `scripts/demo_film.py` minimal working film; the template
- `scripts/commons.py` image search, download, cutout, credits
- `scripts/voice_timing.py` phrase timings from the voiceover
- `scripts/sfx.py` sound-effects synthesiser
- `scripts/sheets.sh`, `scripts/encode.sh` contact sheets and final encode
- `references/style-guide.md` the look, in detail (read before designing)
- `references/scene-recipes.md` code patterns for recurring shots
- `references/sourcing-images.md` finding and cutting images
- `references/reference-video-breakdown.md` frame-by-frame analysis of the reel this style comes from
- `references/example_film/` the complete 113-second film (32 scenes) as worked code
- `assets/fonts/` Anton (captions), Inter (UI and documents), Caveat (handwriting), all open licence

Setup: `pip install numpy opencv-python-headless pillow rembg onnxruntime sherpa-onnx soundfile` and ffmpeg.
