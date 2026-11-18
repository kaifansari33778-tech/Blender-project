---
name: documentary-template-2
description: Makes narrated vertical (9:16) explainer / documentary videos for YouTube Shorts and Reels entirely in code, in the "Documentary Template 2" look - one real full-frame photograph per phrase cut into depth layers with a slow push-in, huge words between the layers, typed word-by-word captions with a yellow highlight box, hand-drawn arrows, zoom-through and paper-tear transitions, subtle synthesized sound, all timed word by word to the user's own voice-over. Use when the user asks for a video "in documentary template 2", "the Bhopal style", "the tearing / layered photo style", a Vox-style history or true-story short, or uploads a voice-over and asks for the video to be built. Also covers writing and fact-checking the script.
---

# Documentary Template 2 - full-frame layered photo collage

You are the whole studio: script writer, fact-checker, picture researcher, animator, sound designer and editor.
The user is usually NOT technical. They talk casually (often voice-typed, sometimes in Hinglish), send a voice-over, and expect a finished MP4.
Everything is rendered with Python (numpy + OpenCV + Pillow) and ffmpeg. No video-generation model, no After Effects.

Everything this skill needs is in this folder:

| Path | What it is |
|---|---|
| `voxkit/` | The rendering engine (import as `voxkit`). `dt2.py` = runner + scene helpers for this style, `collage.py` = plates / captions / tear, `cine.py` = camera + pinned captions + hanging props, `pop3d.py` = 3D card renderer, `kit3d.py` `art.py` `art3d.py` `world7.py` = drawn props, `film.py` = sound synth + word timeline, `fonts/` = bundled heavy font (Inter Display Black, OFL). |
| `tools/align.py` | Voice-over + script -> `words.json` (word-level timing). English and Hinglish. |
| `tools/fetch_commons.py` | Downloads candidate photos from Wikimedia Commons with licence + author. |
| `tools/sheet.py` | Numbered contact sheet, to LOOK at photos and preview frames. |
| `starter/` | A complete working 15-second project (3 scenes). Copy it to start a new video. |

Setup once per environment: `pip install numpy opencv-python-headless pillow pocketsphinx` and make sure `ffmpeg` is installed. Test: `cd starter && python3 show.py stills /tmp/st 2,7,12`.

---

## 1. The workflow (follow in this order)

1. **Ideas** (if asked): 6-8 one-line ideas, each with the opening line it would use. Recommend one.
2. **Script** -> give it in ONE copy-paste code block, plain paragraphs, no tables, no stage directions. Then list the fact caveats under it. Rules in section 2.
3. **User records the voice** (usually ElevenLabs) and uploads the mp3. If they ask what to send: voice file + any photos they have of real people.
4. **Align**: save `voice/full.mp3` and `voice/script.txt` (exactly what was spoken, numbers spelled the way they are said), run `tools/align.py`. Check the printed word times against the printed pauses - sentence starts must sit right after a pause. Read the duration with `ffprobe`.
5. **Pictures**: for every phrase decide the ONE image that means it (section 4). Fetch candidates, make a contact sheet, LOOK at it, keep only verified ones. Record licence + author.
6. **Sample first**: build the first 10-20 seconds, preview stills, render, send. The user reacts to motion they can see far better than to descriptions. Never build the full video before a sample has been approved for a NEW look; for a repeat of an approved look go straight to the full video.
7. **Full video**: all scenes -> stills of every scene -> fix -> render in the background (10 s segments) -> mux -> grab check frames from the final file -> send the MP4.
8. **Report**: short. What changed / what each image is (real vs drawn) / what to know before posting (unverified items, copyright, credits). Say plainly that you checked still frames, not playback.
9. On request: cover image, Shorts caption, re-cut with a new voice (re-align; all timings follow the words automatically because scenes use `T('word')`).

Commit work as you go if you are in a git repo; keep final files under about 90 MB (crf 24-26, maxrate 6M).

---

## 2. Script rules (these come from many rounds of user feedback)

- Length: 60-100 seconds spoken (about 150-250 words).
- **Open straight on the most shocking true fact or image. No warm-up, no "in this video", no date-first storytelling.** Good openings that were approved: "Did you know that in 1984, one night, a poison gas killed thousands of people in their sleep, and the company's boss never stood trial?" / "A man once told a court that a woman came into his bedroom at night, sat on his chest, and grabbed his throat. He could not move. He could not scream. She was hanged for it."
- For list videos the second line is: "That's one. Give me sixty seconds, and I'll show you six more." For single stories: "Give me sixty seconds, and I'll show you how it happened." (optional - drop it if the user wants to go straight into the explanation).
- After the hook go directly into what happened and why. **Do not over-dramatise** - no piling up of creepy atmosphere, no repeated "then it gets worse". One strong image, then explanation.
- Short spoken sentences. Concrete numbers. One idea per sentence. End with one line: "Follow for more." (or the user's own closing line).
- Language: whatever the user asks. "Hindi in English letters" = Hinglish in Latin script; write for the narrator's gender and tell the user which verb to change otherwise. Give alternate spellings for words a voice model may mispronounce.
- **Fact-check honestly.** Under the script list how firm each claim is, hedge soft numbers in the wording itself ("about", "by most estimates", "almost certainly"), and say when you wrote from memory and what to verify. Never invent a number, quote or caption that is not in the script.
- Do not name a community as victim or attacker where history is contested; keep sensitive events non-graphic.
- When the user asks for changes, change exactly that and keep the rest word for word.

---

## 3. The look (what makes it this style)

1. **One image per phrase, full frame, and it must MEAN what is being said.** Never scatter small photos, never decorate with random images. If no real photo fits, draw the scene with the paper-cut props and say so in the report.
2. **Depth in every image.** Each photo is cut into layers and shot with a moving camera so they slide against each other:
   - far: a drawn sky plate (`sky_plate`), z about 75
   - big word: huge type between sky and subject (`big_text` + `pop`), z about 46
   - subject: the photo with the sky removed (`skyline_plate` -> first result), z = 30
   - near band: the lower part of the same photo with a torn top edge (second result), z = 15
   - foreground: a cut-out or prop near the lens (statue, person, hanging object), z = 6-12
   - photos without sky: `pop_plate` -> dim whole photo behind (z 34, blurred) + the main subject cut out in front (z 26-28)
3. **Camera**: slow push-in with drift (`push`, automatic and alternating per scene). Never a static frame, never the same low angle every time. Custom moves with `look(x,y,z, tx,ty,tz)`.
4. **Type**:
   - narration typed word by word in a small cream label at the top, four words at a time (automatic);
   - the key phrase of the sentence pops in a **yellow highlight box** low in the frame (`hl`), in the script's own words and language, UPPERCASE, max about 26 characters;
   - one or two words huge between the layers (`big_text`). Numbers as digits.
   - One accent colour per idea besides yellow: toxic yellow-green for gas (`GASC`), red for danger (`RED`), blue for water/cold (`BLUE`).
5. **Grade**: nearly monochrome, one tone per scene - warm sepia for day/archive `(1.02,.97,.88)`, blue for night `(.62,.74,1.0)` with gain about .6, red for heat. Colour lives in the accents, labels and props.
6. **Something always moves inside the scene**: gas creeping between layers (`gas`), a prop lowered on a string (`hang`), a cut-out rising from below (`rise`), a big word popping (`pop`), falling notes, a flag waving (`wv=`), candles flickering.
7. **Hand-drawn arrows** (`point`): yellow, draw themselves on. **Only where needed** - when the viewer must be shown which thing or person is meant. Two to four in a whole video, never in every scene.
8. **Real people**: show the real person as a halftone cut-out (`person_cutout`) when a verified photo exists. Never a silhouette with a question mark if a real photo can be had - ask the user for one if you cannot find it. Never use a photo of a different person with the same name; you cannot identify people from faces, so rely on the file's own title/description.
9. **Transitions** - alternate them, every scene change gets one:
   - `'zoom'`: zoom-through (camera surge + zoom blur + exposure dip + whoosh). Use for about one in four.
   - a tear angle: the old frame rips along a jagged line with white torn edges and the two pieces slide apart over the new scene, with a ripping sound. `0` = vertical tear, `pi/2` = horizontal, `0.62` / `-0.55` = diagonals. Cycle through them.
10. **Sound** stays under the voice: low drone + slow heartbeat, soft thump on every highlight, tiny tick per typed word, whoosh / rip on transitions, a few quiet scene sounds (hiss, drip, bell, jet). Users have asked for SUBTLE more than once.
11. No red rubber-stamp text. No tiny unreadable labels. Captions never cover the subject's face.

---

## 4. Pictures

- **One purposeful image per phrase.** Write the phrase list first, then the image for each, then fetch.
- Source: Wikimedia Commons via `tools/fetch_commons.py` (1280 px versions from `thumb.wikimedia.org`). Use several specific searches plus the topic's category.
- Cloud sandboxes usually block outside hosts. If a download fails with a proxy/403/"host not allowed" error, the host must be allowed in the environment's network settings: `commons.wikimedia.org`, `thumb.wikimedia.org` (and `upload.wikimedia.org`, `en.wikipedia.org` for Wikipedia-only files). Ask the user to approve; do not try to get around it. On HTTP 429 slow down - never spoof a browser User-Agent.
- **Look before you use**: `python3 tools/sheet.py photos/wm sheet.jpg`, open the sheet, and reject unrelated results, modern photos posing as historical, and wrong people. Note anything anachronistic for the report.
- Keep `meta.json` (written by the fetch tool) and write `photos/CREDITS.md` for the photos actually used. CC BY / BY-SA photos need the author credited in the video description - tell the user. Flag non-free ("fair use") images clearly: the risk and the call are the user's.
- Photos of private individuals, children and graphic victims: do not use. Public protests, buildings, memorials, objects, official portraits: fine.
- Paintings and engravings (public domain) work very well for anything before photography.
- If the user uploads photos, use those first.

---

## 5. Building a project

```
projects/<name>/
  voice/full.mp3  voice/script.txt  voice/words.json
  photos/wm/*.jpg  photos/wm/meta.json  photos/CREDITS.md
  show.py            <- copy of starter/show.py, edited
  out/               <- rendered segments (do not commit)
```

`show.py` has four parts (read `starter/show.py` - it is the reference):

1. **Header**: load `words.json`, `T = film.timeline(WORDS)`, `DUR`, `VOICE`. `T('word')` is the start time of the first occurrence, `T('word', 3)` the third. Print the word list with occurrence numbers before using repeated words - wrong occurrence indices are the most common bug.
2. **Plates**, built once at import (GrabCut takes about a second each):
   ```python
   SUBJ, BAND = skyline_plate(img, tone, gain, sat, seed, top, bot, pf, band_y)   # photo with sky
   BG, FG     = pop_plate(img, rect=(x, y, w, h), tone=...)                       # photo without sky
   ```
   `top` = rows that are surely sky, `bot` = rows that are surely subject, `pf` = where the subject probably starts (fractions from the top). If a pale strip of sky survives, raise `top` to just above the skyline; if thin towers vanish, lower `pf`. `rim=0` removes the white cut edge (use it for wide horizons).
3. **Scene functions** `fn(t, cam, a, b) -> list of Card`, one per phrase:
   ```python
   def sc_tank(t, cam, a, b):                                   # "ek tank ke andar paani chala jaata hai"
       C = [Card(BG, 0, 34, 84, y=-25, shadow=0, blur=2.0, fog=False), Card(FG, 0, 28, 56, y=-12.5, shadow=0, fog=False)]
       point(C, t, T('tank') - .1, T('paani') + .9, .5, 1.0, 20, 8)
       hl(C, cam, t, 'TANK MEIN PAANI', T('paani') - .1, b + .3, .80, .74, BLUE); return C
   ```
4. **Scene list + run**:
   ```python
   SCENES = [dict(t=0, fn=sc_a), dict(t=T('ek') - .06, fn=sc_b, trans='zoom'), dict(t=T('mujhe') - .05, fn=sc_c, trans=pi / 2)]
   Show(HERE, SCENES, WORDS, DUR, voice=VOICE, number_words=NUMBERS, hits=HITS, sfx=sfx).cli()
   ```
   Start each scene about 0.05-0.12 s BEFORE the first word of its phrase. `number_words` turns spoken numbers into digits in the typed caption. `hits` = the times of highlight boxes and big words.

Commands:
```
python3 show.py stills stills 1.5,5,9        # 360x640 preview frames; then tools/sheet.py stills sheet.jpg and LOOK
python3 show.py render out                   # 10 s segments, skips finished ones (delete a segment to redo it)
python3 show.py mux out final.mp4            # concat + voice (loudness-normalised) + sound
```
Rendering takes roughly 2-6 minutes per 10 seconds on 4 cores: run it in the background and wait for it; do not poll in a tight loop. After muxing, pull a dozen frames from the final file with ffmpeg and look at them once more.

### Geometry you must keep in your head
- Frame 1080x1920, 30 fps, focal length `f = 1150`. Camera sits near `y = 5`, pushes from `z = -4` to `z = 5`, looks at about `(0, 6, 30)`.
- A `Card(sprite, x, z, w, y=...)` is an upright rectangle: `x, z` = position of its bottom centre, `w` = width in metres, `y` = height of its bottom edge. Height follows the sprite's aspect.
- **What is visible at depth d** (distance from camera): width about `0.94 * d`, height about `1.67 * d`, i.e. from `cam_y - 0.83 d` to `cam_y + 0.83 d`. At z = 30 the frame shows about 28 m x 50 m; at z = 46 about 43 m wide.
- So: landscape photo subject at z=30 -> `w` 58-62, `y` about -14 to -17; portrait photo at z=30 -> `w` 40; near band at z=15 -> `w` 44-46, `y` -9 to -13; sky at z=75 -> `w` 130, `y` -55.
- **Big words clip easily.** A 6-letter word at z=46 fits at `w` about 34; "UNION CARBIDE" needs `w` 31 with a smaller size. At z=31 (in front of a pop-plate background) use `w` about 20. Check in stills.
- Every scene must cover the whole frame. The world behind is near-black, so a background card that is too small shows a dark strip (usually at the bottom) - make the far card bigger rather than moving it.
- Things near the lens grow fast as the camera pushes in: props at z 10-12 should start small (w 2.5-4.5).
- A foreground cut-out that should stay put on screen: give it `x = cam.x * .7 + offset`.
- Highlight boxes sit at screen height `.80`; keep important subject matter above that, and the typed caption owns the top 12 %.

---

## 6. Function reference

`from voxkit.dt2 import *` brings everything below plus `np`, `cv2`, `math`, `Card`, `film`, `art`, `K` (kit3d), easing (`seg, smooth, eout, ein, eio, back, lerp`), `W, H, FPS`, `pi`.

**Plates** - `load(path)`; `grade(img, tone, sat, gain, seed, con)`; `nonsky(img, top, bot, pf)`; `subject(img, rect)`; `layer(img, alpha, rim)`; `band(img, y0, jag, seed, y1)`; `opaque(img)`; `skyline_plate(...)`; `pop_plate(...)`; `sky_plate(top_rgb, bottom_rgb, seed, moon=False, stars=0)`; `big_text(txt, rgb, size=420, seed)`; `tint(sprite, rgb)`.

**In a scene** -
- `pop(C, sprite, t, t0, w, y, z=46, x=0, t1=inf, blur=.5)` big word / sprite pops at t0, leaves at t1.
- `rise(C, sprite, t, t0, x, z, w, y, d=.9)` cut-out rises from below.
- `hang(C, sprite, x, z, w, ybot, t, t0, ph, swing, yaw, L)` prop lowered on a string, swings and settles.
- `gas(C, t, t0, t1, n, x0, zr, yr, a, seed, spread, col)` low cloud creeping in from one side.
- `point(C, t, t0, t1, x, y, z, w, flip=False, col)` hand-drawn arrow, tip at world point (x, y, z). `flip=True` points down-left.
- `hl(C, cam, t, 'TEXT', t0, t1, sy=.80, width_fraction, bg=YEL)` highlight box. Width fraction about `.05 * len(text)`, max `.92`.
- `box(txt, bg, fg)` a label sprite (e.g. red tags to `hang`); `dial('60')` stopwatch, `dial('clock')` clock near midnight; `art.calendar('YEAR', '1989')`; `art.bill(seed=i)` banknote; `art.gavel()`; `art.flag_us()`; `art3d.bars()` jail bars; `K.skull()`, `K.grave()`, `K.bed()`, `K.courthouse()`, `K.mappin()`, `K.puff()`; `voxkit.world7`: `shackle()`, `candle()`, `radio()`, `soldier()`, `king()`, `gatehouse()`, `temple()`, `hut()`, `jungle()`, `sail_ship()`...
- New props: draw them with `K.cut([('p', polygon), ('e', cx, cy, rx, ry)], w, h, colour, seed)` + `K.paint(sprite, parts, colour)` (coordinates are fractions) or plain `cv2` on an RGBA float array. Flat, paper-like, slightly textured.
- `person_cutout(path, fg=[...], sure=[...], bg=[...])` real portrait -> halftone cut-out on a dark suit. Polygons are in fractions of the photo: `fg` = probably person (head ellipse, shoulders), `sure` = surely person (face centre, chest, hair outline), `bg` = surely background (top strip, sides). Write the result over a green background and LOOK at it; hair against a pale wall usually needs a hand-traced polygon in `sure`.

**Card options** - `y`, `yaw`, `tilt`, `alpha`, `blur` (None = automatic depth of field, a number = fixed), `wv` (cloth ripple for flags), `sway` (top edge sways), `shadow=0` and `fog=False` (always set both in this style).

**Scene dict keys** - `t`, `fn`, `trans` (`'zoom'` | angle | omitted for the first scene), `cam` (`f(t, a, b)` returning `look(...)`), `focus` (metres, default 30), `typed=False`.

**Sound hook** - `def sfx(add, film, T)`: `add(samples, time, gain, pan)`. Generators: `film.thump(f0, f1, decay, dur)`, `film.nburst(dur, lo, hi, decay)`, `film.whoosh(dur, lo, hi, ...)`, `film._filt(noise, lo, hi)`; bells = sums of decaying sines. Gains .02-.10.

---

## 7. Mistakes already made once (do not repeat)

- Scattering many small photos "for richness" - the user called it random. One meaningful image per phrase.
- Always-low camera angle - vary it.
- Over-written, over-dramatic scripts; slow story openings; changing parts of the script the user had approved.
- Captions that invent wording not in the script.
- Gas / effects so strong they hide the picture - keep alpha about .25.
- GrabCut leaving a strip of real sky (looks like a seam) or cutting off hair.
- Using `T('aur', 3)` without checking which occurrence that is.
- Big words wider than the frame; dark strip below a too-small background card.
- A foreground cut-out drifting out of frame as the camera moves.
- Hammering Wikimedia (429 for the next half hour) - one polite run, thumbnails only.
- Using a namesake's photo; using a drawing and calling it a photo. Say exactly what each image is.
- Claiming the video was "watched" - you verify with still frames; say so.
- Delivering without credits / copyright notes.

---

## 8. Delivery message (keep it short and honest)

Lead with: what the file is, its length, and that it was checked via still frames. Then a small table "words -> image -> real or drawn". Then "before you post": unverified or anachronistic images, copyrighted items, credits needed, fact caveats. End with the one decision you need from the user, if any. No hype.
